"""Knowledge base search: finds the KB articles most similar in meaning to a ticket.

How it works:
    1. Each KB article is turned into an embedding: a list of numbers that
       represents its meaning. Texts with similar meaning get similar numbers.
    2. The ticket is turned into an embedding the same way.
    3. Cosine similarity measures how close the ticket is to each article
       (1.0 = same direction, 0 = unrelated). The closest articles win.

Article embeddings are cached in data/kb_embeddings.json, so they are only
computed again when an article's text or the embedding model changes.

The suggestion combines two signals: the article for the classifier's
subcategory, and the top search result. When they disagree, the ticket is
flagged for a human to double-check the classification.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .taxonomy import DATA_DIR


def cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def ticket_text(ticket: dict) -> str:
    return f"{ticket['subject']}. {ticket['description']}"


def article_text(article: dict) -> str:
    steps = " ".join(article.get("user_steps", []) + article.get("it_steps", []))
    return f"{article['subcategory']}: {article['title']}. {article['summary']} {steps}"


@dataclass
class KBSuggestion:
    primary: Optional[dict]                      # the article to use for the reply
    related: list = field(default_factory=list)  # other close matches, as (article, score)
    search_top: Optional[dict] = None            # best match from search alone
    needs_review: bool = False
    review_note: str = ""


class KnowledgeBase:
    def __init__(self, config, client, path: Path = DATA_DIR / "kb_articles.json",
                 cache_path: Path = DATA_DIR / "kb_embeddings.json"):
        self.config = config
        self.client = client
        self.cache_path = Path(cache_path)
        self.articles = json.loads(Path(path).read_text(encoding="utf-8"))
        self.by_subcategory = {a["subcategory"]: a for a in self.articles}
        self._vectors = None

    # ---------- embeddings ----------

    def _prefix(self, kind: str) -> str:
        # nomic-embed-text is trained with these task prefixes and works better with them.
        if "nomic" in self.config.embed_model:
            return "search_query: " if kind == "query" else "search_document: "
        return ""

    def _embed(self, texts: list, kind: str) -> list:
        response = self.client.embeddings.create(
            model=self.config.embed_model, input=[self._prefix(kind) + t for t in texts])
        return [item.embedding for item in response.data]

    def _index(self) -> dict:
        """Article id -> vector, reusing cached vectors whose text hasn't changed."""
        if self._vectors is not None:
            return self._vectors
        cache = {}
        if self.cache_path.exists():
            saved = json.loads(self.cache_path.read_text(encoding="utf-8"))
            if saved.get("model") == self.config.embed_model:
                cache = saved.get("items", {})

        texts = {a["id"]: article_text(a) for a in self.articles}
        hashes = {i: hashlib.sha256(t.encode()).hexdigest()[:16] for i, t in texts.items()}
        stale = [i for i in texts if cache.get(i, {}).get("hash") != hashes[i]]
        if stale:
            for i, vec in zip(stale, self._embed([texts[i] for i in stale], "document")):
                cache[i] = {"hash": hashes[i], "vector": vec}
            self.cache_path.write_text(json.dumps({"model": self.config.embed_model, "items": cache}),
                                       encoding="utf-8")
        self._vectors = {i: cache[i]["vector"] for i in texts}
        return self._vectors

    # ---------- search ----------

    def search(self, text: str, k: int = 3) -> list:
        """The k articles closest in meaning to the text, as (article, score), best first."""
        vectors = self._index()
        query = self._embed([text], "query")[0]
        scored = [(a, cosine(query, vectors[a["id"]])) for a in self.articles]
        return sorted(scored, key=lambda pair: pair[1], reverse=True)[:k]

    def suggest(self, ticket: dict, subcategory: Optional[str], k: int = 3) -> KBSuggestion:
        results = self.search(ticket_text(ticket), k=k)
        search_top = results[0][0]
        primary = self.by_subcategory.get(subcategory) or search_top
        related = [(a, round(s, 3)) for a, s in results if a["id"] != primary["id"]][: k - 1]

        suggestion = KBSuggestion(primary=primary, related=related, search_top=search_top)
        if search_top["id"] != primary["id"]:
            suggestion.needs_review = True
            suggestion.review_note = (f"Classified as {primary['subcategory']}, but the KB search "
                                      f"matched {search_top['subcategory']} more closely.")
        return suggestion
