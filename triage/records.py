"""Shared format for prediction files, used by classify.py and evaluate.py."""

PREDICTION_FIELDS = [
    "ticket_id", "subject", "description", "tags",
    "true_category", "true_subcategory", "true_priority",
    "pred_category", "pred_subcategory", "pred_priority",
    "default_priority", "raise_rule", "evidence", "raise_check", "reason", "attempts", "error", "latency_s",
]


def to_row(ticket: dict, result) -> dict:
    return {
        "ticket_id": ticket["ticket_id"], "subject": ticket["subject"],
        "description": ticket["description"], "tags": ticket["tags"],
        "true_category": ticket["category"], "true_subcategory": ticket["subcategory"],
        "true_priority": ticket["priority"],
        "pred_category": result.category or "", "pred_subcategory": result.subcategory or "",
        "pred_priority": result.priority or "", "default_priority": result.default_priority,
        "raise_rule": result.raise_rule, "evidence": result.evidence,
        "raise_check": result.raise_check, "reason": result.reason,
        "attempts": result.attempts, "error": result.error, "latency_s": result.latency_s,
    }
