#!/usr/bin/env python3
"""Run the triage classifier on a sample of tickets and compare with the correct labels.

Examples:
    python classify.py --dry-run                   # show the exact prompt, no model call
    python classify.py --limit 10                  # 10 random practice tickets
    python classify.py --limit 50 --out results/run1.csv
    python classify.py --explain INC-10204          # every step of the decision for one ticket
"""

import argparse
import csv
import random
import sys
from pathlib import Path

from triage.classifier import Classifier
from triage.config import load_config
from triage.records import PREDICTION_FIELDS, to_row

ROOT = Path(__file__).resolve().parent

def explain(ticket_id, classifier):
    """Walk through how one ticket is classified and how its priority is decided."""
    ticket = None
    for path in sorted((ROOT / "data").glob("tickets_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            ticket = next((t for t in csv.DictReader(f) if t["ticket_id"] == ticket_id), None)
        if ticket:
            break
    if not ticket:
        sys.exit(f"Ticket {ticket_id} not found in data/tickets_*.csv")

    print(f"TICKET {ticket_id}  ({ticket['role']}, {ticket['location']})")
    print(f"  Subject:     {ticket['subject']}")
    print(f"  Description: {ticket['description']}\n")

    r = classifier.classify(ticket)
    if not r.ok:
        sys.exit(f"The AI gave an invalid answer after {r.attempts} tries: {r.error}")

    print("STEP 1  The AI reads the ticket and answers (it does not choose a priority):")
    print(f"  subcategory: {r.subcategory}")
    print(f"  raise_rule:  {r.raise_rule}")
    print(f"  evidence:    \"{r.evidence}\"")
    print(f"  reason:      {r.reason}\n")

    print("STEP 2  The code looks up the default priority in kb_articles.json:")
    print(f"  {r.subcategory} -> {r.default_priority}\n")

    print("STEP 3  The code checks the raise:")
    if r.raise_rule == "none":
        print("  No raise rule claimed, so the default priority stands.\n")
    else:
        from triage.classifier import evidence_fits_rule, evidence_in_ticket
        found = evidence_in_ticket(r.evidence, ticket)
        print(f"  Check 1, is the quote really in the ticket?   {'yes' if found else 'NO'}")
        if found:
            fits = evidence_fits_rule(r.evidence, r.raise_rule)
            print(f"  Check 2, does the quote fit '{r.raise_rule}'?   {'yes' if fits else 'NO'}")
        print(f"  Result: {r.raise_check}\n")

    verdict = "correct" if r.priority == ticket["priority"] else f"WRONG, expected {ticket['priority']}"
    print(f"STEP 4  Final priority: {r.priority}   ({verdict})")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "tickets_train.csv")
    parser.add_argument("--limit", type=int, default=10, help="how many tickets to classify")
    parser.add_argument("--seed", type=int, default=1, help="which random sample to take")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "predictions.csv")
    parser.add_argument("--dry-run", action="store_true", help="print the prompt for one ticket and stop")
    parser.add_argument("--explain", metavar="TICKET_ID", help="show every step of the decision for one ticket")
    args = parser.parse_args()

    if "eval" in args.input.name:
        print("Heads up: this is the held-out evaluation set. Use evaluate.py for scored runs on it.\n")

    with open(args.input, newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))
    sample = random.Random(args.seed).sample(tickets, min(args.limit, len(tickets)))

    config = load_config()
    classifier = Classifier(config)

    if args.explain:
        explain(args.explain, classifier)
        return

    if args.dry_run:
        for message in classifier.build_messages(sample[0]):
            print(f"----- {message['role'].upper()} -----\n{message['content']}\n")
        return

    print(f"Model: {config.model} at {config.base_url}\n")
    rows, sub_hits, pri_hits, failures, total_time = [], 0, 0, 0, 0.0

    for i, ticket in enumerate(sample, 1):
        try:
            result = classifier.classify(ticket)
        except Exception as exc:  # connection problems stop the run with a clear hint
            if "Connection" in type(exc).__name__:
                sys.exit(f"Could not reach the model at {config.base_url}. "
                         "Is Ollama running? Open the Ollama app, or run: ollama serve")
            raise

        sub_ok = result.subcategory == ticket["subcategory"]
        pri_ok = result.priority == ticket["priority"]
        sub_hits += sub_ok
        pri_hits += pri_ok
        failures += not result.ok
        total_time += result.latency_s

        mark = "OK " if sub_ok and pri_ok else "XX "
        print(f"{mark}[{i}/{len(sample)}] {ticket['ticket_id']}  "
              f"expected {ticket['subcategory']} / {ticket['priority']}  "
              f"got {result.subcategory} / {result.priority}  ({result.latency_s}s)")
        if not (sub_ok and pri_ok) and result.reason:
            print(f"      model's reason: {result.reason}")
        if result.error:
            print(f"      invalid answer: {result.error}")

        rows.append(to_row(ticket, result))

    n = len(sample)
    print(f"\nSubcategory correct: {sub_hits}/{n}   Priority correct: {pri_hits}/{n}   "
          f"Invalid answers: {failures}   Avg time: {total_time / n:.1f}s per ticket")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved predictions to {args.out}")


if __name__ == "__main__":
    main()
