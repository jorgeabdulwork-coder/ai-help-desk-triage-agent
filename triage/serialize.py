"""Turns an agent result into plain data (JSON) for the web pages."""

from __future__ import annotations


def result_to_dict(ticket: dict, result, config) -> dict:
    t, kb = result.triage, result.kb
    data = {
        "ticket": {k: ticket.get(k, "") for k in ("ticket_id", "requester", "role", "location", "subject", "description")},
        "triage": {
            "ok": t.ok, "error": t.error, "category": t.category, "subcategory": t.subcategory,
            "priority": t.priority, "default_priority": t.default_priority, "raise_rule": t.raise_rule,
            "evidence": t.evidence, "raise_check": t.raise_check, "reason": t.reason,
        },
        "kb": None,
        "reply": result.reply,
        "reply_problems": result.reply_problems,
        "needs_review": result.needs_review,
        "latency_s": result.latency_s,
        "models": {"classifier": config.model, "reply": config.reply_model or config.model,
                   "embeddings": config.embed_model},
        "expected": ({"subcategory": ticket["subcategory"], "priority": ticket["priority"]}
                     if ticket.get("subcategory") else None),
    }
    if kb:
        data["kb"] = {
            "primary": {"id": kb.primary["id"], "title": kb.primary["title"]},
            "related": [{"id": a["id"], "title": a["title"], "score": s} for a, s in kb.related],
            "needs_review": kb.needs_review, "review_note": kb.review_note,
        }
    return data
