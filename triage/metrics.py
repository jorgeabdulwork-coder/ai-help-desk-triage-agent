"""Scoring functions. Each takes prediction rows (dicts from a predictions CSV)."""

from collections import Counter, defaultdict

from .taxonomy import PRIORITIES

RANK = {p: i for i, p in enumerate(PRIORITIES)}


def _share(rows, test):
    return sum(1 for r in rows if test(r)) / len(rows) if rows else 0.0


def sub_ok(r):
    return r["pred_subcategory"] == r["true_subcategory"]


def pri_ok(r):
    return r["pred_priority"] == r["true_priority"]


def summary(rows) -> dict:
    """Headline numbers for one run."""
    over = sum(1 for r in rows if r["pred_priority"] in RANK and RANK[r["pred_priority"]] > RANK[r["true_priority"]])
    under = sum(1 for r in rows if r["pred_priority"] in RANK and RANK[r["pred_priority"]] < RANK[r["true_priority"]])
    return {
        "tickets": len(rows),
        "category_acc": _share(rows, lambda r: r["pred_category"] == r["true_category"]),
        "subcategory_acc": _share(rows, sub_ok),
        "priority_acc": _share(rows, pri_ok),
        "fully_correct": _share(rows, lambda r: sub_ok(r) and pri_ok(r)),
        "invalid_rate": _share(rows, lambda r: bool(r["error"])),
        "over_prioritized": over,
        "under_prioritized": under,
        # Raises the AI claimed but the code rejected (evidence missing or not fitting the rule).
        "raises_rejected": sum(1 for r in rows if str(r.get("raise_check", "")).startswith("rejected")),
        "avg_latency_s": sum(float(r["latency_s"] or 0) for r in rows) / len(rows) if rows else 0.0,
    }


def _grouped(rows, key_fn):
    groups = defaultdict(list)
    for r in rows:
        for key in key_fn(r):
            groups[key].append(r)
    return {k: (len(g), _share(g, sub_ok), _share(g, pri_ok)) for k, g in sorted(groups.items())}


def by_tag(rows) -> dict:
    """Accuracy on clean tickets vs. each kind of noise. A ticket can have several tags."""
    return _grouped(rows, lambda r: [t for t in r["tags"].split(";") if t] or ["(clean)"])


def by_subcategory(rows) -> dict:
    return _grouped(rows, lambda r: [r["true_subcategory"]])


def top_confusions(rows, k: int = 10) -> list:
    """Most common (correct subcategory, predicted subcategory) mix-ups."""
    pairs = Counter((r["true_subcategory"], r["pred_subcategory"] or "(invalid)")
                    for r in rows if not sub_ok(r))
    return pairs.most_common(k)


def priority_matrix(rows) -> dict:
    """matrix[correct][predicted] = count."""
    matrix = {t: {p: 0 for p in PRIORITIES + ["(invalid)"]} for t in PRIORITIES}
    for r in rows:
        matrix[r["true_priority"]][r["pred_priority"] if r["pred_priority"] in RANK else "(invalid)"] += 1
    return matrix
