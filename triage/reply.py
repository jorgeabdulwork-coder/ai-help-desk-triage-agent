"""Drafts the first reply to the requester, grounded in one KB article.

The AI may only use the steps in that article, so it cannot invent fixes.
check_reply() then runs fast rule-based safety checks on every draft.
"""

from __future__ import annotations

import re

# Bump this whenever the reply rules change, so agent evaluation runs can be compared.
REPLY_VERSION = "r3"

# r3 note: r2 included an example sentence ("we'll re-add the printer for you"), and the
# small model pasted it into unrelated replies. Rules now describe the format without
# example sentences that could be copied.
REPLY_RULES = """\
You write the first reply from the IT Help Desk to an employee who submitted a ticket.

Rules:
- First line: "Hi <first name>," then a blank line.
- One short sentence acknowledging the problem in plain words. Do not guess what caused it.
- Choose ONLY the employee steps from the KB article that fit this specific problem. Some articles cover several situations; skip steps meant for a different situation. Introduce them with "Please try:" and list them as numbered steps for the employee to do (at most 4). If no employee step fits, leave this part out.
- Then one sentence saying what IT will do next, using the KB article's IT steps that fit this problem, written with "we will" or "we'll".
- Use only the KB article's content. Do not add other fixes, devices, links, phone numbers, or promises about timing.
- Never ask for their password.
- Never mention KB article numbers, category names, or priority levels.
- If the priority is High or Urgent, say that we know this is affecting their work and we are already working on it.
- Only if the ticket describes a second, unrelated problem, ask them to submit a separate ticket for it. Otherwise never mention separate tickets.
- Keep it under 120 words. Plain text only: no headings, no bold, no labels such as "For IT".
- End with a blank line and then "IT Help Desk" alone on the last line."""


def first_name(ticket: dict) -> str:
    return (ticket.get("requester") or "there").split()[0]


def format_article(article: dict) -> str:
    lines = [f"KB article: {article['title']}", "Things the employee can try:"]
    lines += [f"- {s}" for s in article.get("user_steps", [])] or ["- (none)"]
    lines += ["What IT does (describe as what we will do):"] + [f"- {s}" for s in article.get("it_steps", [])]
    return "\n".join(lines)


class ReplyDrafter:
    def __init__(self, config, client):
        self.config = config
        self.client = client

    def build_messages(self, ticket: dict, triage, article: dict) -> list:
        request = (
            f"Requester: {ticket.get('requester', 'Unknown')} ({ticket['role']}, {ticket['location']})\n"
            f"Subject: {ticket['subject']}\n"
            f"Description: {ticket['description']}\n"
            f"Internal notes, never mention in the reply: classified as {triage.subcategory}, "
            f"priority {triage.priority}\n\n"
            f"{format_article(article)}\n\n"
            "Write the reply."
        )
        return [{"role": "system", "content": REPLY_RULES}, {"role": "user", "content": request}]

    def draft(self, ticket: dict, triage, article: dict) -> str:
        response = self.client.chat.completions.create(
            model=self.config.reply_model or self.config.model,
            messages=self.build_messages(ticket, triage, article), temperature=self.config.temperature)
        return tidy(response.choices[0].message.content or "")


def tidy(text: str) -> str:
    """Remove stray quotes, trailing spaces, and runs of blank lines (a small-model habit)."""
    text = text.strip().strip('"').strip()
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text)


# ---------- rule-based safety checks ----------

ASKS_FOR_PASSWORD = re.compile(
    r"\b(send|give|tell|share|provide|reply with|confirm|what is|what's)\b[^.?!\n]{0,25}\b(your )?(current |old )?password\b",
    re.I)
INTERNAL_LABELS = re.compile(r"\b(for it|for the employee|steps for|what it does)\b\s*[:,]", re.I)
KB_NUMBER = re.compile(r"\bKB-?\s?\d{2,}\b", re.I)
PRIORITY_TALK = re.compile(r"\bpriority\b|\b(an?|is|as) (Urgent|High|Medium|Low)\b")
GUESSED_CAUSE = re.compile(r"\b(due to|caused by|because of)\b", re.I)
# Devices and systems a reply might mention. If one appears in the reply but in neither
# the ticket nor the KB article, the reply has probably borrowed text from elsewhere.
THINGS = ["printer", "copier", "scanner", "register", "card reader", "receipt", "monitor",
          "keyboard", "mouse", "headset", "docking station", "modem", "firewall", "router",
          "vpn", "teams", "outlook", "voicemail", "wi-fi", "wifi"]
LINK_OR_PHONE = re.compile(r"https?://|www\.|\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b|\bext\.?\s*\d+", re.I)


def unrelated_things(reply: str, ticket: dict, article: dict = None) -> list:
    """Devices or systems the reply mentions that the ticket and KB article never do."""
    source = f"{ticket.get('subject', '')} {ticket.get('description', '')}"
    if article:
        source += " " + " ".join([article.get("title", ""), article.get("summary", "")]
                                 + article.get("user_steps", []) + article.get("it_steps", []))
    found = lambda thing, text: re.search(rf"\b{re.escape(thing)}s?\b", text, re.I)
    return [t for t in THINGS if found(t, reply) and not found(t, source)]


def check_reply(reply: str, ticket: dict, article: dict = None, max_words: int = 150) -> list:
    """Return a list of problems found. An empty list means every check passed."""
    problems = []
    extra = unrelated_things(reply, ticket, article)
    if extra:
        problems.append(f"mentions {', '.join(extra)}, which the ticket and KB article don't")
    if first_name(ticket).lower() not in reply[:60].lower():
        problems.append("does not greet the requester by first name")
    if len(reply.split()) > max_words:
        problems.append(f"longer than {max_words} words")
    if ASKS_FOR_PASSWORD.search(reply):
        problems.append("asks for a password")
    if LINK_OR_PHONE.search(reply):
        problems.append("contains a link or phone number not in the KB")
    if KB_NUMBER.search(reply):
        problems.append("mentions a KB article number")
    if PRIORITY_TALK.search(reply):
        problems.append("mentions a priority level")
    if GUESSED_CAUSE.search(reply):
        problems.append("guesses at a cause")
    if INTERNAL_LABELS.search(reply):
        problems.append("uses internal labels like 'For IT'")
    lines = [line.strip() for line in reply.strip().splitlines() if line.strip()]
    if not lines or lines[-1].lower() != "it help desk":
        problems.append("does not end with 'IT Help Desk' on its own line")
    return problems
