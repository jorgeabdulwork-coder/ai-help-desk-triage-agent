"""The list of valid categories, subcategories, and priorities.

Loaded from the KB articles file so there is a single source of truth:
adding a KB article for a new subcategory automatically makes it a valid label.
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRIORITIES = ["Low", "Medium", "High", "Urgent"]


class Taxonomy:
    def __init__(self, kb_path: Path = DATA_DIR / "kb_articles.json"):
        articles = json.loads(Path(kb_path).read_text(encoding="utf-8"))
        self.parent = {a["subcategory"]: a["category"] for a in articles}
        # Normal priority for each subcategory, like an SLA matrix.
        self.default_priority = {a["subcategory"]: a.get("default_priority") for a in articles}
        self.categories = list(dict.fromkeys(a["category"] for a in articles))
        self.subcategories = list(self.parent)

    def by_category(self) -> dict:
        grouped = {}
        for sub, cat in self.parent.items():
            grouped.setdefault(cat, []).append(sub)
        return grouped
