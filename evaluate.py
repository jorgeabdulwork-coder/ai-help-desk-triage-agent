#!/usr/bin/env python3
"""Score the classifier on the held-out evaluation set.

Examples:
    python evaluate.py --label baseline              # all 200 eval tickets (~20 min locally)
    python evaluate.py --label baseline --resume     # continue a run that was interrupted
    python evaluate.py --label test --limit 20       # quick partial run
    python evaluate.py --rescore reports/baseline_predictions.csv   # rebuild the report, no model calls

Outputs, in reports/:
    <label>_predictions.csv   every ticket with correct and predicted labels
    <label>_report.md         readable report with all the metrics
    runs.csv                  one line per run, for comparing prompt versions and models
"""

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from triage import metrics
from triage.classifier import PROMPT_VERSION, Classifier
from triage.config import load_config
from triage.records import PREDICTION_FIELDS, to_row
from triage.taxonomy import PRIORITIES

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
RUN_FIELDS = ["date", "label", "model", "prompt_version", "tickets", "subcategory_acc",
              "priority_acc", "fully_correct", "invalid_rate", "over_prioritized",
              "under_prioritized", "avg_latency_s"]


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(x):
    return f"{x * 100:.1f}%"


def run_model(tickets, pred_path, resume):
    """Classify tickets, writing each result as it finishes so progress is never lost."""
    done = {r["ticket_id"] for r in read_csv(pred_path)} if resume and pred_path.exists() else set()
    todo = [t for t in tickets if t["ticket_id"] not in done]
    if done:
        print(f"Resuming: {len(done)} already done, {len(todo)} to go.")

    config = load_config()
    classifier = Classifier(config)
    print(f"Model: {config.model}   Prompt: {PROMPT_VERSION}   Tickets: {len(todo)}\n")

    pred_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if done else "w"
    with open(pred_path, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PREDICTION_FIELDS)
        if not done:
            writer.writeheader()
        for i, ticket in enumerate(todo, 1):
            try:
                result = classifier.classify(ticket)
            except Exception as exc:
                if "Connection" in type(exc).__name__:
                    sys.exit(f"\nCould not reach the model at {config.base_url}. Is Ollama running? "
                             f"Progress is saved; rerun with --resume.")
                raise
            writer.writerow(to_row(ticket, result))
            f.flush()
            mark = "ok" if (result.subcategory == ticket["subcategory"]
                            and result.priority == ticket["priority"]) else "MISS"
            print(f"\r[{i}/{len(todo)}] {ticket['ticket_id']} {mark:<4}", end="", flush=True)
    print("\n")
    return config.model


def build_report(label, model, rows):
    s = metrics.summary(rows)
    lines = [
        f"# Evaluation report: {label}",
        "",
        f"Model: `{model}`, prompt version `{PROMPT_VERSION}`, {s['tickets']} held-out tickets, "
        f"run {datetime.now():%Y-%m-%d %H:%M}.",
        "",
        "## Summary",
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| Category accuracy | {pct(s['category_acc'])} |",
        f"| Subcategory accuracy | {pct(s['subcategory_acc'])} |",
        f"| Priority accuracy | {pct(s['priority_acc'])} |",
        f"| Fully correct (subcategory and priority) | {pct(s['fully_correct'])} |",
        f"| Invalid answers | {pct(s['invalid_rate'])} |",
        f"| Priority set too high | {s['over_prioritized']} tickets |",
        f"| Priority set too low | {s['under_prioritized']} tickets |",
        f"| Raises rejected by the code | {s['raises_rejected']} tickets |",
        f"| Average time per ticket | {s['avg_latency_s']:.1f}s |",
        "",
        "Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.",
        "",
        "## Accuracy by ticket difficulty",
        "",
        "| Tickets with | Count | Subcategory | Priority |",
        "|---|---|---|---|",
    ]
    lines += [f"| {tag} | {n} | {pct(a)} | {pct(b)} |" for tag, (n, a, b) in metrics.by_tag(rows).items()]

    lines += ["", "## Priority: correct (rows) vs. predicted (columns)", "",
              "| | " + " | ".join(PRIORITIES + ["(invalid)"]) + " |",
              "|---" * (len(PRIORITIES) + 2) + "|"]
    for true, preds in metrics.priority_matrix(rows).items():
        lines.append(f"| **{true}** | " + " | ".join(str(v) for v in preds.values()) + " |")

    lines += ["", "## Most common subcategory mix-ups", ""]
    confusions = metrics.top_confusions(rows)
    if confusions:
        lines += ["| Correct | Predicted | Count |", "|---|---|---|"]
        lines += [f"| {t} | {p} | {c} |" for (t, p), c in confusions]
    else:
        lines.append("None.")

    lines += ["", "## Accuracy by subcategory", "",
              "| Subcategory | Count | Subcategory | Priority |", "|---|---|---|---|"]
    lines += [f"| {sub} | {n} | {pct(a)} | {pct(b)} |" for sub, (n, a, b) in metrics.by_subcategory(rows).items()]

    misses = [r for r in rows if not (metrics.sub_ok(r) and metrics.pri_ok(r))]
    lines += ["", f"## Examples of misses (first 10 of {len(misses)})", ""]
    for r in misses[:10]:
        lines += [
            f"**{r['ticket_id']}** ({r['tags'] or 'clean'}): {r['subject']}. {r['description']}",
            f"- Correct: {r['true_subcategory']} / {r['true_priority']}. "
            f"Predicted: {r['pred_subcategory'] or '(invalid)'} / {r['pred_priority'] or '(invalid)'}",
            f"- Model's reason: {r['reason'] or r['error']}",
            *([f"- Raise rule: {r['raise_rule']}, evidence: \"{r.get('evidence', '')}\", "
               f"check: {r.get('raise_check') or 'n/a'}"] if r.get("raise_rule") not in (None, "", "none") else []),
            "",
        ]
    return "\n".join(lines), s


def log_run(label, model, s):
    path = REPORTS / "runs.csv"
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RUN_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow({
            "date": f"{datetime.now():%Y-%m-%d %H:%M}", "label": label, "model": model,
            "prompt_version": PROMPT_VERSION, "tickets": s["tickets"],
            **{k: round(s[k], 3) for k in ("subcategory_acc", "priority_acc", "fully_correct", "invalid_rate")},
            "over_prioritized": s["over_prioritized"], "under_prioritized": s["under_prioritized"],
            "avg_latency_s": round(s["avg_latency_s"], 2),
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", default="run", help="name for this run, e.g. baseline or prompt-v2")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "tickets_eval.csv")
    parser.add_argument("--limit", type=int, help="only use the first N tickets")
    parser.add_argument("--resume", action="store_true", help="continue an interrupted run with the same label")
    parser.add_argument("--rescore", type=Path, help="existing predictions CSV to re-score without calling the model")
    args = parser.parse_args()

    if args.rescore:
        rows, model, label = read_csv(args.rescore), "(rescored)", args.rescore.stem.replace("_predictions", "")
    else:
        tickets = read_csv(args.input)[: args.limit]
        pred_path = REPORTS / f"{args.label}_predictions.csv"
        model = run_model(tickets, pred_path, args.resume)
        rows, label = read_csv(pred_path), args.label

    report, s = build_report(label, model, rows)
    report_path = REPORTS / f"{label}_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    if not args.rescore:
        log_run(label, model, s)

    print(f"Subcategory: {pct(s['subcategory_acc'])}   Priority: {pct(s['priority_acc'])}   "
          f"Fully correct: {pct(s['fully_correct'])}   Invalid: {pct(s['invalid_rate'])}")
    print(f"Priority too high: {s['over_prioritized']}   too low: {s['under_prioritized']}")
    print(f"\nFull report: {report_path}")


if __name__ == "__main__":
    main()
