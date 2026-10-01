#!/usr/bin/env python3
"""Build the showcase page (docs/index.html) from real agent output.

Runs the agent on a set of hand-picked tickets, then writes one self-contained
HTML file that GitHub Pages can host. Recruiters can browse it without
installing anything.

    python build_showcase.py --author "Your Name" --repo-url https://github.com/you/ai-help-desk-triage-agent
    python build_showcase.py --from-json docs/showcase.json    # rebuild the page without calling the models

Tip: run it with LLM_MODEL=llama3.2:3b and LLM_REPLY_MODEL=qwen2.5:7b in .env,
so the scanner example shows the review flag catching a misclassification.
"""

import argparse
import csv
import html
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB, DOCS = ROOT / "web", ROOT / "docs"

HERO_ID = "INC-10349"
EXAMPLES = [  # (ticket id, what it shows)
    ("INC-10118", "Customers waiting at the register"),
    ("INC-10349", "Vague subject, impact buried at the end"),
    ("INC-10029", "Repeated lockouts, but only one person"),
    ("INC-10026", "Expired password, unhelpful subject"),
    ("INC-10091", "Two problems in one ticket"),
    ("INC-10110", "Whole site offline"),
    ("INC-10165", "Low priority by default"),
    ("CUSTOM", "A ticket worded unlike the training data"),
]
CUSTOM = {"CUSTOM": {"ticket_id": "CUSTOM", "subject": "Scanner broken",
                          "description": "Scan to email stopped working on the copier.",
                          "requester": "Sam Rivera", "role": "Retail Associate", "location": "Store 001"}}

JOURNEY = [
    {"version": "v1", "model": "Llama 3.2 3B", "fully_correct": 59.0,
     "note": "First prompt. Strong at naming the problem, but it raised priority for invented reasons, such as a store being involved."},
    {"version": "v2", "model": "Llama 3.2 3B", "fully_correct": 83.0,
     "note": "A normal priority for each problem type, like an SLA matrix, and explicit rules for when to raise it."},
    {"version": "v3", "model": "Llama 3.2 3B", "fully_correct": 69.5,
     "note": "The AI now quotes evidence and code sets the priority. The small model quoted irrelevant sentences as proof, so it got worse."},
    {"version": "v3", "model": "Qwen 2.5 7B", "fully_correct": 89.0,
     "note": "The same design on a larger model gave the best result so far, with no ticket set too low."},
    {"version": "v4", "model": "Llama 3.2 3B", "fully_correct": 94.5,
     "note": "Code also checks that the quote shows wider impact. The small model recovers, at about half the time per ticket."},
    {"version": "v4", "model": "Qwen 2.5 7B", "fully_correct": 98.0,
     "note": "Best score on the evaluation set used for tuning."},
    {"version": "Final", "model": "Qwen 2.5 7B, unseen tickets", "fully_correct": 97.0, "final": True,
     "note": "A fresh set generated after tuning ended. Close to 98%, so the rules generalized rather than memorizing tickets."},
]
LESSONS = [
    {"title": "Let code apply the rules",
     "text": "The AI reads the ticket; plain code applies the priority matrix. Splitting the work took fully correct answers from 59% to 97%."},
    {"title": "Make the AI show its evidence",
     "text": "A priority raise needs a quote from the ticket that the code can verify, which stopped the AI from inventing impact like \"the whole store is down.\""},
    {"title": "Check the checker",
     "text": "An AI judge graded the drafted replies, but most of its \"invented content\" flags were wrong. Verifying its quotes moved measured accuracy from 63% to about 97%."},
    {"title": "The knowledge base sets the ceiling",
     "text": "Replies are only as good as the articles behind them. Labeling steps by situation worked better than any prompt instruction."},
]


def find_tickets(ids):
    found = dict(CUSTOM)
    for path in sorted((ROOT / "data").glob("tickets_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            for t in csv.DictReader(f):
                if t["ticket_id"] in ids:
                    found[t["ticket_id"]] = t
    missing = [i for i in ids if i not in found]
    if missing:
        sys.exit(f"Tickets not found: {', '.join(missing)}. Run python data/generate_tickets.py first.")
    return found


def run_agent():
    from triage.agent import TriageAgent
    from triage.config import load_config
    from triage.serialize import result_to_dict

    config = load_config()
    agent = TriageAgent(config)
    tickets = find_tickets({i for i, _ in EXAMPLES} | {HERO_ID})
    results = {}
    for n, tid in enumerate(sorted(tickets), 1):
        print(f"[{n}/{len(tickets)}] {tid}", flush=True)
        results[tid] = result_to_dict(tickets[tid], agent.run(tickets[tid]), config)
    return {
        "hero": results[HERO_ID],
        "examples": [{"caption": cap, "result": results[tid]} for tid, cap in EXAMPLES],
        "models": sorted({config.model, config.reply_model or config.model, config.embed_model}),
    }


def build(data, author, repo_url):
    data = {**data, "journey": JOURNEY, "lessons": LESSONS}
    page = (WEB / "showcase_template.html").read_text(encoding="utf-8")
    script_safe = json.dumps(data).replace("</", "<\\/")
    repo = f'<a href="{html.escape(repo_url)}">Code on GitHub</a>' if repo_url else ""
    by = f"Built by {html.escape(author)}. " if author else ""
    for marker, value in {
        "/*STYLE*/": (WEB / "style.css").read_text(encoding="utf-8"),
        "/*RENDER*/": (WEB / "render.js").read_text(encoding="utf-8"),
        "/*DATA*/": script_safe,
        "/*REPO_LINK*/": repo,
        "/*AUTHOR*/": by,
        "/*MODELS*/": html.escape(", ".join(data["models"])),
        "/*DATE*/": date.today().strftime("%B %d, %Y").replace(" 0", " "),
    }.items():
        page = page.replace(marker, value)
    DOCS.mkdir(exist_ok=True)
    (DOCS / "index.html").write_text(page, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--author", default="", help="your name, shown in the footer")
    parser.add_argument("--repo-url", default="", help="link to the GitHub repository")
    parser.add_argument("--from-json", type=Path, help="rebuild from saved results instead of running the agent")
    args = parser.parse_args()

    if args.from_json:
        data = json.loads(args.from_json.read_text(encoding="utf-8"))
    else:
        try:
            data = run_agent()
        except Exception as exc:
            if "Connection" in type(exc).__name__:
                sys.exit("Can't reach Ollama. Open the Ollama app and try again.")
            raise
        DOCS.mkdir(exist_ok=True)
        (DOCS / "showcase.json").write_text(json.dumps(data, indent=1), encoding="utf-8")
    build(data, args.author, args.repo_url)
    print(f"Wrote {DOCS / 'index.html'}. Open it in a browser to check it.")


if __name__ == "__main__":
    main()
