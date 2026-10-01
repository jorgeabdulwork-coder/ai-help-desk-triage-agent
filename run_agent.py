#!/usr/bin/env python3
"""Run the full agent on one ticket: classify, suggest a KB article, draft a reply.

Examples:
    python run_agent.py INC-10204
    python run_agent.py --subject "Printer jammed" --description "The office printer says paper jam."
    python run_agent.py --subject "Help" --description "No one can log in" --requester "Ana Lopez" --location "Store 004"
"""

import argparse
import csv
import sys
import textwrap
from pathlib import Path

from triage.agent import TriageAgent
from triage.config import load_config

ROOT = Path(__file__).resolve().parent


def find_ticket(ticket_id):
    for path in sorted((ROOT / "data").glob("tickets_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            for t in csv.DictReader(f):
                if t["ticket_id"] == ticket_id:
                    return t
    sys.exit(f"Ticket {ticket_id} not found in data/tickets_*.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ticket_id", nargs="?", help="a ticket ID from the data files")
    parser.add_argument("--subject")
    parser.add_argument("--description")
    parser.add_argument("--requester", default="Sam Rivera")
    parser.add_argument("--role", default="Retail Associate")
    parser.add_argument("--location", default="Store 001")
    args = parser.parse_args()

    if args.ticket_id:
        ticket = find_ticket(args.ticket_id)
    elif args.subject and args.description:
        ticket = {"ticket_id": "CUSTOM", "subject": args.subject, "description": args.description,
                  "requester": args.requester, "role": args.role, "location": args.location}
    else:
        parser.error("give a ticket ID, or both --subject and --description")

    config = load_config()
    try:
        result = TriageAgent(config).run(ticket)
    except Exception as exc:
        if "Connection" in type(exc).__name__:
            sys.exit(f"Could not reach the model at {config.base_url}. Is Ollama running?")
        if "not found" in str(exc).lower():
            sys.exit(f"{exc}\n\nA model may not be downloaded yet. Try: ollama pull {config.embed_model}")
        raise

    t = result.triage
    print(f"TICKET {ticket['ticket_id']}  from {ticket['requester']} ({ticket['role']}, {ticket['location']})")
    print(f"  {ticket['subject']}: {ticket['description']}\n")
    if not t.ok:
        sys.exit(f"The classifier gave an invalid answer: {t.error}")

    print("CLASSIFICATION")
    print(f"  {t.category} > {t.subcategory}, priority {t.priority}")
    raised = f", raised from {t.default_priority} ({t.raise_rule}: \"{t.evidence}\")" if t.raised else ""
    print(f"  default priority {t.default_priority}{raised}")
    print(f"  reason: {t.reason}\n")

    kb = result.kb
    print("KB ARTICLES")
    print(f"  Use:     {kb.primary['id']}  {kb.primary['title']}")
    for article, score in kb.related:
        print(f"  Related: {article['id']}  {article['title']}  (similarity {score})")
    print()

    print("DRAFT REPLY (for the agent to review before sending)")
    print(textwrap.indent(result.reply, "  | ", lambda line: True))
    print()

    if result.needs_review:
        print("NEEDS REVIEW")
        if kb.needs_review:
            print(f"  - {kb.review_note}")
        for problem in result.reply_problems:
            print(f"  - Reply {problem}")
    else:
        print("All checks passed.")
    if "priority" in ticket:
        ok = t.subcategory == ticket["subcategory"] and t.priority == ticket["priority"]
        print(f"\n(Correct answer: {ticket['subcategory']} / {ticket['priority']}, KB {ticket['kb_article']}: "
              f"{'match' if ok and kb.primary['id'] == ticket['kb_article'] else 'MISMATCH'})")
    print(f"Time: {result.latency_s}s")


if __name__ == "__main__":
    main()
