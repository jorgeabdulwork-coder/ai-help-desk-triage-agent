#!/usr/bin/env python3
"""Evaluate the full agent (Phase 4): KB suggestions and drafted replies.

Runs the agent on a random sample of evaluation tickets, then measures:
    - KB suggestion accuracy, and how well the meaning-based search does on its own
    - whether the "needs review" flag catches the classifier's mistakes
    - rule-based safety checks on every reply
    - an AI judge's grades: grounded in the KB article, addresses the issue, tone

Examples:
    python evaluate_agent.py --label agent-qwen                 # 30 tickets
    python evaluate_agent.py --label agent-qwen --limit 60
    python evaluate_agent.py --label agent-qwen --no-judge      # faster, skips the AI judge
"""

import argparse
import csv
import random
import sys
from datetime import datetime
from pathlib import Path

from triage.agent import TriageAgent
from triage.classifier import PROMPT_VERSION
from triage.config import load_config, make_client
from triage.judge import JUDGE_VERSION, ReplyJudge
from triage.kb import ticket_text
from triage.reply import REPLY_VERSION

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
FIELDS = ["ticket_id", "subject", "description", "true_subcategory", "pred_subcategory",
          "true_priority", "pred_priority", "true_kb", "kb_used", "search_top1", "search_top3",
          "needs_review", "reply", "reply_problems", "grounded", "invented_quote", "judge_check",
          "steps_fit", "addresses_issue", "tone_ok", "judge_note", "latency_s"]


def pct(n, d):
    return f"{100 * n / d:.1f}%" if d else "n/a"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", default="agent")
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "tickets_eval.csv")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    with open(args.input, newline="", encoding="utf-8") as f:
        tickets = list(csv.DictReader(f))
    sample = random.Random(args.seed).sample(tickets, min(args.limit, len(tickets)))

    config = load_config()
    client = make_client(config)
    agent = TriageAgent(config, client=client)
    judge = None if args.no_judge else ReplyJudge(config, client)
    print(f"Classifier: {config.model}   Replies: {config.reply_model or config.model}   "
          f"Embeddings: {config.embed_model}   "
          f"Judge: {'off' if not judge else (config.judge_model or config.model)}   Tickets: {len(sample)}\n")

    REPORTS.mkdir(exist_ok=True)
    rows = []
    for i, t in enumerate(sample, 1):
        try:
            result = agent.run(t)
            search = agent.kb.search(ticket_text(t), k=3)
        except Exception as exc:
            if "Connection" in type(exc).__name__:
                sys.exit(f"\nCould not reach the model at {config.base_url}. Is Ollama running?")
            if "not found" in str(exc).lower():
                sys.exit(f"\n{exc}\nA model may not be downloaded. Try: ollama pull {config.embed_model}")
            raise
        tr, kb = result.triage, result.kb
        grade = judge.judge(t, kb.primary, result.reply) if (judge and kb) else {}
        rows.append({
            "ticket_id": t["ticket_id"], "subject": t["subject"], "description": t["description"],
            "true_subcategory": t["subcategory"], "pred_subcategory": tr.subcategory or "",
            "true_priority": t["priority"], "pred_priority": tr.priority or "",
            "true_kb": t["kb_article"], "kb_used": kb.primary["id"] if kb else "",
            "search_top1": search[0][0]["id"], "search_top3": ";".join(a["id"] for a, _ in search),
            "needs_review": result.needs_review, "reply": result.reply,
            "reply_problems": "; ".join(result.reply_problems),
            "grounded": grade.get("grounded", ""), "invented_quote": grade.get("invented_quote", ""),
            "judge_check": grade.get("judge_check", ""), "steps_fit": grade.get("steps_fit", ""),
            "addresses_issue": grade.get("addresses_issue", ""),
            "tone_ok": grade.get("tone_ok", ""), "judge_note": grade.get("note", ""),
            "latency_s": result.latency_s,
        })
        print(f"\r[{i}/{len(sample)}] {t['ticket_id']}", end="", flush=True)
    print("\n")

    with open(REPORTS / f"{args.label}_agent_predictions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    report = build_report(args.label, config, rows, judged=bool(judge))
    path = REPORTS / f"{args.label}_agent_report.md"
    path.write_text(report, encoding="utf-8")
    print(report.split("## Replies with problems")[0])
    print(f"Full report: {path}")


def build_report(label, config, rows, judged):
    n = len(rows)
    count = lambda test: sum(1 for r in rows if test(r))
    kb_ok = count(lambda r: r["kb_used"] == r["true_kb"])
    top1 = count(lambda r: r["search_top1"] == r["true_kb"])
    top3 = count(lambda r: r["true_kb"] in r["search_top3"].split(";"))
    class_wrong = [r for r in rows if r["pred_subcategory"] != r["true_subcategory"]]
    caught = sum(1 for r in class_wrong if r["needs_review"])
    flagged = count(lambda r: r["needs_review"])
    false_alarms = count(lambda r: r["needs_review"] and r["pred_subcategory"] == r["true_subcategory"]
                         and not r["reply_problems"])
    clean_replies = count(lambda r: r["reply"] and not r["reply_problems"])
    problem_counts = {}
    for r in rows:
        for p in filter(None, r["reply_problems"].split("; ")):
            problem_counts[p] = problem_counts.get(p, 0) + 1
    avg_time = sum(float(r["latency_s"]) for r in rows) / n if n else 0

    lines = [
        f"# Agent evaluation: {label}", "",
        f"Classifier model `{config.model}`, reply model `{config.reply_model or config.model}`, "
        f"embeddings `{config.embed_model}`, judge `{config.judge_model or config.model}`. "
        f"Classifier prompt `{PROMPT_VERSION}`, reply rules `{REPLY_VERSION}`, judge `{JUDGE_VERSION}`. "
        f"{n} evaluation tickets, run {datetime.now():%Y-%m-%d %H:%M}.", "",
        "## KB suggestions", "",
        "| Metric | Result |", "|---|---|",
        f"| Suggested article is correct | {pct(kb_ok, n)} |",
        f"| KB search alone: correct article ranked first | {pct(top1, n)} |",
        f"| KB search alone: correct article in the top 3 | {pct(top3, n)} |", "",
        "The suggested article comes from the classifier's subcategory. The search works independently "
        "from the ticket text, so it acts as a second opinion.", "",
        "## Needs-review flag", "",
        "| Metric | Result |", "|---|---|",
        f"| Tickets flagged for review | {flagged} of {n} |",
        f"| Classifier mistakes caught by the flag | {caught} of {len(class_wrong)} |",
        f"| Flagged although classification and reply were fine | {false_alarms} |", "",
        "## Reply safety checks (rule-based)", "",
        "| Metric | Result |", "|---|---|",
        f"| Replies passing every check | {pct(clean_replies, n)} |",
    ]
    lines += [f"| Problem: reply {p} | {c} |" for p, c in sorted(problem_counts.items())]
    if judged:
        graded = [r for r in rows if r["grounded"] in (True, False)]
        g = len(graded)
        flagged = [r for r in graded if r["grounded"] is False]
        false_alarms_j = sum(1 for r in flagged if r["judge_check"].startswith("likely false alarm"))
        confirmed = sum(1 for r in flagged if r["judge_check"].startswith("confirmed"))
        share = lambda key: pct(sum(r[key] is True for r in graded), g)
        lines += ["", "## AI judge grades", "", "| Metric | Result |", "|---|---|",
                  f"| Grounded in the KB article, as graded by the judge | {share('grounded')} |",
                  f"| Judge's 'not grounded' flags confirmed by the code | {confirmed} of {len(flagged)} |",
                  f"| Judge flags that look like false alarms (quoted text is in the KB) | {false_alarms_j} of {len(flagged)} |",
                  f"| Grounded, after removing likely false alarms | {pct(g - len(flagged) + false_alarms_j, g)} |",
                  f"| Steps fit the specific problem | {share('steps_fit')} |",
                  f"| Addresses the ticket's problem | {share('addresses_issue')} |",
                  f"| Tone suitable for an employee | {share('tone_ok')} |",
                  f"| Judge answers that were invalid | {n - g} |", "",
                  "When the judge says a reply isn't grounded, it must quote the sentence. The code then checks "
                  "that quote against the KB article, the same way the classifier's evidence is checked. "
                  "The judge is still an AI and can be wrong, so read the replies below to verify it."]
    lines += ["", f"Average time per ticket (classify, search, and draft): {avg_time:.1f}s", ""]

    bad = [r for r in rows if r["reply_problems"] or r["addresses_issue"] is False or r["steps_fit"] is False
           or (r["grounded"] is False and not r["judge_check"].startswith("likely false alarm"))]
    lines += ["## Replies with problems", ""]
    if not bad:
        lines.append("None.")
    for r in bad[:10]:
        judge_bits = [f"judge: {r['judge_note']}" if r["judge_note"] and r["judge_note"] != "none" else "",
                      f"quoted: \"{r['invented_quote']}\" ({r['judge_check']})" if r["invented_quote"] else ""]
        judge_bits += ["judge: steps don't fit this problem" if r["steps_fit"] is False else "",
                       "judge: doesn't address the problem" if r["addresses_issue"] is False else ""]
        issues = [x for x in [r["reply_problems"], *judge_bits] if x]
        lines += [f"**{r['ticket_id']}**: {r['subject']}. {r['description']}",
                  f"- Issues: {' | '.join(issues)}", "", "```", r["reply"], "```", ""]

    lines += ["## Sample replies", ""]
    for r in [r for r in rows if r not in bad][:5]:
        lines += [f"**{r['ticket_id']}** ({r['pred_subcategory']}, {r['pred_priority']}, {r['kb_used']}): "
                  f"{r['subject']}. {r['description']}", "", "```", r["reply"], "```", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
