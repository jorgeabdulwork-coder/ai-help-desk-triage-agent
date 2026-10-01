"""An AI 'judge' that grades drafted replies during evaluation.

Rule-based checks catch clear problems (a password request, a phone number).
Some qualities need judgment: did the reply stick to the KB article, do the
chosen steps fit this problem, does it address the issue? A second model call
grades those.

Judge v2 (after the first agent evaluation, where most "not grounded" grades
were false alarms):
    - the judge sees the reply rules, so required phrases aren't flagged
    - it must quote the exact sentence it thinks is invented
    - the code checks that quote against the KB article; a quote whose content
      is in the article is marked as a likely false alarm

Limitation: a judge using the same model that wrote the reply may be lenient
or biased. Setting LLM_JUDGE_MODEL to a different model helps.
"""

from __future__ import annotations

import json
import re

from .reply import REPLY_RULES, format_article

JUDGE_VERSION = "j3"

JUDGE_RULES = f"""\
You review draft replies written by an IT help desk assistant. Be strict but accurate.

The assistant was given these rules, so anything they require is allowed:
{REPLY_RULES}

Grade the reply and answer with JSON only:
- grounded: false only if the reply contains a fix, step, link, phone number, or timing promise that is NOT in the KB article and NOT required by the rules above.
- invented_quote: if grounded is false, copy the exact sentence from the reply that is not supported. Otherwise "".
- steps_fit: true if every step in the reply makes sense for this specific problem (true if the reply has no steps and none would fit).
- addresses_issue: the reply responds to the problem the ticket describes.
- tone_ok: polite, clear, and suitable for a non-technical employee.
- note: one plain sentence describing the most important problem, or "none". Do not use field names."""

SCHEMA = {
    "type": "object",
    "properties": {
        "grounded": {"type": "boolean"},
        "invented_quote": {"type": "string"},
        "steps_fit": {"type": "boolean"},
        "addresses_issue": {"type": "boolean"},
        "tone_ok": {"type": "boolean"},
        "note": {"type": "string"},
    },
    "required": ["grounded", "invented_quote", "steps_fit", "addresses_issue", "tone_ok", "note"],
    "additionalProperties": False,
}
FIELDS = ("grounded", "invented_quote", "steps_fit", "addresses_issue", "tone_ok", "note")

STOPWORDS = set("""a an the and or but if to of on in at for with your you we our it is are be
this that then than so as from by will can may please try again have has had not
issue issues problem problems persist persists continue continues still help fix fixed work works
working doesnt dont isnt cant need needed make sure also just any""".split())


def _content_words(text: str) -> list:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower().replace("'", "")) if w not in STOPWORDS]


def quote_found_in_kb(quote: str, article: dict, threshold: float = 0.75) -> bool:
    """True if most of the quote's meaningful words appear in the KB article,
    suggesting the judge flagged content that actually came from the article."""
    words = _content_words(quote)
    if not words:
        return False
    source = " ".join([article.get("title", ""), article.get("summary", "")]
                      + article.get("user_steps", []) + article.get("it_steps", []))
    available = set(_content_words(source))
    # Allow simple word forms: "restart" matches "restarting", "printers" matches "printer".
    hits = sum(1 for w in words if any(a.startswith(w[:5]) for a in available if len(w) >= 5) or w in available)
    return hits / len(words) >= threshold


class ReplyJudge:
    def __init__(self, config, client):
        self.config = config
        self.client = client

    def judge(self, ticket: dict, article: dict, reply: str) -> dict:
        content = (f"TICKET\nSubject: {ticket['subject']}\nDescription: {ticket['description']}\n\n"
                   f"{format_article(article)}\n\nDRAFT REPLY\n{reply}")
        kwargs = {"model": self.config.judge_model or self.config.model, "temperature": 0,
                  "messages": [{"role": "system", "content": JUDGE_RULES},
                               {"role": "user", "content": content}]}
        if self.config.schema_mode == "json_schema":
            kwargs["response_format"] = {"type": "json_schema",
                                         "json_schema": {"name": "reply_grade", "schema": SCHEMA, "strict": True}}
        elif self.config.schema_mode == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        raw = self.client.chat.completions.create(**kwargs).choices[0].message.content or ""
        try:
            data = json.loads(raw.strip().strip("`").removeprefix("json").strip())
            grade = {k: data[k] for k in FIELDS}
        except (json.JSONDecodeError, KeyError, TypeError):
            grade = {k: None for k in FIELDS}
            grade["note"] = "judge gave an invalid answer"

        # Verify the judge's claim, the same way the classifier's evidence is verified.
        grade["judge_check"] = ""
        if grade["grounded"] is False:
            quote = grade.get("invented_quote") or ""
            if not quote.strip():
                grade["judge_check"] = "no quote given"
            elif quote_found_in_kb(quote, article):
                grade["judge_check"] = "likely false alarm: quoted text is in the KB article"
            else:
                grade["judge_check"] = "confirmed: quoted text not in the KB article"
        return grade
