"""Ticket classifier: the AI reads the ticket, the code applies the priority rules.

Flow for one ticket:
    1. Build messages: instructions + worked examples + the ticket
    2. The AI returns JSON: subcategory, whether a raise rule applies, and a quote as evidence
    3. Validate the answer against the real list of categories (retry once if invalid)
    4. The code sets the priority: the subcategory's default, plus one level only if
       the quoted evidence really appears in the ticket AND actually fits the rule

Why split the work (prompt v3): in v2 the AI sometimes invented escalations
("the whole store is affected") and sometimes reasoned correctly but wrote the
wrong priority. Fixed business rules are now plain code; the AI only does the
part that needs language understanding.
"""

from __future__ import annotations

import difflib
import json
import re
import time
from dataclasses import dataclass
from typing import Optional

from .config import LLMConfig
from .taxonomy import PRIORITIES, Taxonomy

# Bump this whenever the prompt, examples, or priority logic change.
PROMPT_VERSION = "v4"

RAISE_RULES = {
    "none": "no raise rule applies",
    "several_people": "the ticket says several people, the whole office, or everyone at the site is affected",
    "customers_waiting": "the ticket says customers are waiting or all registers are affected",
    "cannot_work": "the person says they cannot do any work at all",
}

RAISE_GUIDE = """\
Decide whether one of these raise rules applies. It applies ONLY if the ticket text says so directly:
- several_people: several people, the whole office, or everyone at the site is affected
- customers_waiting: customers are waiting, or all registers are affected
- cannot_work: the person says they cannot do any work at all
- none: anything else

Do not assume impact the ticket doesn't state. One register, one device, or one person is not "the whole store".
These are never raise rules: how long the problem has lasted, how many times the person tried,
words like "urgent" or "ASAP", the ticket coming from a store, error codes, or a second problem.

If a rule applies, copy the exact words from the ticket that prove it into "evidence".
The evidence must itself say who is affected, for example "several of us", "customers are waiting",
or "I can't do any work". A sentence that only describes the problem is not evidence.
If no rule applies, use "none" and leave "evidence" empty."""

DISTINCTIONS = """\
- Password Reset: a forgotten, expired, or not-accepted Windows or account password. Account Locked: only when the ticket says the account is locked or locked out.
- Desk Phone: anything about desk phones, dial tone, ringing, or voicemail, including a forgotten voicemail PIN.
- Access Request: access to a shared drive or folder, "access denied" on a folder, or access for a new hire. Shared Mailbox: only when a shared mailbox or inbox is named.
- Outlook: the person's own email not arriving, Outlook not opening, or repeated password prompts in Outlook.
- Teams: anything that happens in Teams, including calls, meetings, audio, and errors signing in to Teams. It is never Outlook.
- Card Reader: card payments, declines, chip or tap problems, or the payment terminal, even if a register is named. Register Down: the register itself is frozen, restarting, or won't let anyone sign in.
- Receipt Printer: receipt printers at registers. Printer/Scanner: office printers, label printers, copiers, and scanners.
- Wi-Fi: wireless problems on some devices. Internet Outage: nothing at the whole site can get online. VPN: connecting to work from home or remotely.
- Computer: the whole computer is slow, won't start, or crashes. Peripherals: mouse, keyboard, monitors, headsets, and docking stations. Application Error: one app crashes, freezes, or shows an error."""

# Hand-written examples. Each reason points to specific evidence in that ticket.
EXAMPLES = [
    (
        {"subject": "Help!!", "description": "Chip and tap both failing on lane 2, customers are lining up.",
         "role": "Cashier", "location": "Store 021"},
        {"reason": "Failing card payments point to the card reader, and the ticket says customers are lining up.",
         "category": "Point of Sale", "subcategory": "Card Reader",
         "raise_rule": "customers_waiting", "evidence": "customers are lining up"},
    ),
    (
        {"subject": "Register 3 frozen", "description": "Register 3 is stuck on a black screen since we opened.",
         "role": "Assistant Manager", "location": "Store 015"},
        {"reason": "One register is frozen; nothing says other registers or customers are affected.",
         "category": "Point of Sale", "subcategory": "Register Down",
         "raise_rule": "none", "evidence": ""},
    ),
    (
        {"subject": "ASAP", "description": "Please install Visio on my laptop so I can finish the floor plan.",
         "role": "Director", "location": "Admin Office"},
        {"reason": "A request to install Visio; 'ASAP' is not a raise rule.",
         "category": "Software", "subcategory": "Install Request",
         "raise_rule": "none", "evidence": ""},
    ),
    (
        {"subject": "Can't log in", "description": "Windows says this account has been locked out. Tried three times this morning.",
         "role": "Store Manager", "location": "Store 007"},
        {"reason": "Windows reports a locked-out account; three tries is not a raise rule.",
         "category": "Access & Accounts", "subcategory": "Account Locked",
         "raise_rule": "none", "evidence": ""},
    ),
    (
        {"subject": "Permission error", "description": "Getting 'you don't have permission' on the Payroll folder.",
         "role": "Accountant", "location": "Admin Office"},
        {"reason": "No permission on a shared folder is a folder access problem, not a mailbox problem.",
         "category": "Access & Accounts", "subcategory": "Access Request",
         "raise_rule": "none", "evidence": ""},
    ),
    (
        {"subject": "Email down?", "description": "No one in our office has received email since 9am.",
         "role": "HR Generalist", "location": "Admin Office"},
        {"reason": "Mail is not arriving, and the ticket says no one in the office is receiving it.",
         "category": "Email & Collaboration", "subcategory": "Outlook",
         "raise_rule": "several_people", "evidence": "No one in our office has received email"},
    ),
    (
        {"subject": "wifi", "description": "wifi on my laptop has been flaky for two weeks, restarted it a bunch of times",
         "role": "Career Coach", "location": "Training Center"},
        {"reason": "One laptop with unreliable wireless; two weeks and many restarts are not raise rules.",
         "category": "Network", "subcategory": "Wi-Fi",
         "raise_rule": "none", "evidence": ""},
    ),
    (
        {"subject": "Excel", "description": "Excel closes every time I open the budget file, I can't get anything done today.",
         "role": "Program Coordinator", "location": "Admin Office"},
        {"reason": "One app keeps closing, and the person says they can't get anything done.",
         "category": "Software", "subcategory": "Application Error",
         "raise_rule": "cannot_work", "evidence": "I can't get anything done today"},
    ),
    (
        {"subject": "Teams echo", "description": "People hear an echo when I talk in Teams. Also the label printer is out of labels.",
         "role": "Logistics Lead", "location": "Warehouse"},
        {"reason": "The first problem is Teams audio; the second problem is ignored.",
         "category": "Email & Collaboration", "subcategory": "Teams",
         "raise_rule": "none", "evidence": ""},
    ),
]


def format_ticket(ticket: dict) -> str:
    """Only the fields a real agent would see. The correct labels are never sent."""
    return (
        f"Subject: {ticket['subject']}\n"
        f"Description: {ticket['description']}\n"
        f"Requester role: {ticket['role']}\n"
        f"Location: {ticket['location']}"
    )


# For each raise rule, the quote must contain at least one of these phrases.
# This stops a real sentence being used as fake proof, like quoting
# "My account got locked an hour ago" as evidence that several people are affected.
RULE_SIGNALS = {
    "several_people": [
        "several", "everyone", "everybody", "no one", "nobody", "none of us", "all of us",
        "many of us", "multiple", "whole office", "whole store", "whole site", "whole team",
        "entire", "coworkers", "others",
    ],
    "customers_waiting": [
        "customer", "shoppers", "line of", "lining up", "lined up", "all the registers",
        "all registers", "every register", "only use one register", "only one register",
    ],
    "cannot_work": [
        "cant do any work", "cannot do any work", "cant work", "cannot work", "unable to work",
        "cant get anything done", "cannot get anything done", "cant do anything",
        "cannot do anything", "cant do my job", "cannot do my job",
    ],
}


def _words(text: str) -> list:
    """Lowercase words with apostrophes removed, so "can't" and "cant" match."""
    return re.findall(r"[a-z0-9]+", text.lower().replace("'", "").replace("\u2019", ""))


def _same_word(a: str, b: str) -> bool:
    """Equal, or close enough to count as a typo ("sevreal" and "several")."""
    return a == b or (len(b) >= 4 and difflib.SequenceMatcher(None, a, b).ratio() >= 0.75)


def evidence_in_ticket(evidence: str, ticket: dict) -> bool:
    """Check 1: the quote really comes from the ticket.

    Every word of the quote must appear in the subject or description, allowing for
    capitalization, punctuation, and small typos. Invented facts like "the whole store
    is affected" are rejected when the ticket never says them.
    """
    quoted = _words(evidence)
    if len(quoted) < 2:
        return False
    available = set(_words(ticket["subject"] + " " + ticket["description"]))
    return all(any(_same_word(w, a) for a in available) for w in quoted)


def evidence_fits_rule(evidence: str, rule: str) -> bool:
    """Check 2: the quote actually says what the rule requires."""
    words = _words(evidence)
    for phrase in RULE_SIGNALS.get(rule, []):
        target = _words(phrase)
        for i in range(len(words) - len(target) + 1):
            if all(_same_word(words[i + j], target[j]) for j in range(len(target))):
                return True
    return False


def raise_one_level(priority: str) -> str:
    return PRIORITIES[min(PRIORITIES.index(priority) + 1, len(PRIORITIES) - 1)]


def decide_priority(default: str, rule: str, evidence: str, ticket: dict):
    """The priority rules in plain code. Returns (priority, what happened to the raise)."""
    if rule == "none":
        return default, ""
    if not evidence_in_ticket(evidence, ticket):
        return default, "rejected: quote not in ticket"
    if not evidence_fits_rule(evidence, rule):
        return default, "rejected: quote doesn't fit the rule"
    return raise_one_level(default), "accepted"


@dataclass
class TriageResult:
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[str] = None
    raise_rule: str = ""
    evidence: str = ""
    default_priority: str = ""
    raise_check: str = ""  # "", "accepted", or "rejected: <why>"
    reason: str = ""
    attempts: int = 0
    error: str = ""
    latency_s: float = 0.0

    @property
    def ok(self) -> bool:
        return not self.error

    @property
    def raised(self) -> bool:
        return self.raise_check == "accepted"


class Classifier:
    def __init__(self, config: LLMConfig, taxonomy: Optional[Taxonomy] = None,
                 client=None, max_attempts: int = 2):
        self.config = config
        self.tax = taxonomy or Taxonomy()
        self.max_attempts = max_attempts
        self._client = client
        missing = [s for s, p in self.tax.default_priority.items() if p not in PRIORITIES]
        if missing:
            raise ValueError(f"No valid default_priority in kb_articles.json for: {', '.join(missing)}. "
                             "Regenerate the data with data/generate_tickets.py.")

    @property
    def client(self):
        # Imported lazily so --dry-run and the tests work without the package installed.
        if self._client is None:
            from openai import OpenAI

            self._client = OpenAI(base_url=self.config.base_url, api_key=self.config.api_key,
                                  timeout=self.config.timeout)
        return self._client

    # ---------- prompt ----------

    def schema(self) -> dict:
        # "reason" first so the model explains before committing to labels.
        # There is no "priority" field: the code calculates it.
        return {
            "type": "object",
            "properties": {
                "reason": {"type": "string"},
                "category": {"type": "string", "enum": self.tax.categories},
                "subcategory": {"type": "string", "enum": self.tax.subcategories},
                "raise_rule": {"type": "string", "enum": list(RAISE_RULES)},
                "evidence": {"type": "string"},
            },
            "required": ["reason", "category", "subcategory", "raise_rule", "evidence"],
            "additionalProperties": False,
        }

    def system_prompt(self) -> str:
        options = "\n".join(
            f"- {cat}: {', '.join(subs)}" for cat, subs in self.tax.by_category().items()
        )
        return (
            "You are an IT help desk triage assistant for a multi-site retail nonprofit "
            "with thrift stores, donation centers, and offices.\n\n"
            "Classify the ticket into exactly one category and one of its subcategories:\n"
            f"{options}\n\n"
            f"How to tell similar subcategories apart:\n{DISTINCTIONS}\n\n"
            "If a ticket describes more than one problem, classify only the first problem described.\n\n"
            f"{RAISE_GUIDE}\n\n"
            'Reply with JSON only, in this shape: {"reason": "<one sentence>", "category": "...", '
            '"subcategory": "...", "raise_rule": "none | several_people | customers_waiting | cannot_work", '
            '"evidence": "<exact words from the ticket, or empty>"}'
        )

    def build_messages(self, ticket: dict) -> list:
        messages = [{"role": "system", "content": self.system_prompt()}]
        for example_ticket, answer in EXAMPLES:
            messages.append({"role": "user", "content": format_ticket(example_ticket)})
            messages.append({"role": "assistant", "content": json.dumps(answer)})
        messages.append({"role": "user", "content": format_ticket(ticket)})
        return messages

    # ---------- model call ----------

    def _call(self, messages: list) -> str:
        kwargs = {"model": self.config.model, "messages": messages,
                  "temperature": self.config.temperature}
        mode = self.config.schema_mode
        if mode == "json_schema":
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "ticket_triage", "schema": self.schema(), "strict": True},
            }
        elif mode == "json_object":
            kwargs["response_format"] = {"type": "json_object"}
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    # ---------- validation ----------

    def validate(self, raw: str):
        """Return (data, "") if the answer is usable, otherwise (None, explanation)."""
        text = raw.strip()
        if text.startswith("```"):  # some models wrap JSON in a code fence
            text = text.strip("`").removeprefix("json").strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return None, "The response was not valid JSON."
        if not isinstance(data, dict):
            return None, "The response must be a JSON object."

        cat, sub, rule = data.get("category"), data.get("subcategory"), data.get("raise_rule")
        errors = []
        if cat not in self.tax.categories:
            errors.append(f"'{cat}' is not a valid category.")
        if sub not in self.tax.parent:
            errors.append(f"'{sub}' is not a valid subcategory.")
        elif cat in self.tax.categories and self.tax.parent[sub] != cat:
            errors.append(f"'{sub}' belongs to '{self.tax.parent[sub]}', not '{cat}'.")
        if rule not in RAISE_RULES:
            errors.append(f"'{rule}' is not a valid raise_rule. Use one of: {', '.join(RAISE_RULES)}.")
        return (None, " ".join(errors)) if errors else (data, "")

    # ---------- main entry point ----------

    def classify(self, ticket: dict) -> TriageResult:
        messages = self.build_messages(ticket)
        result = TriageResult()
        start = time.perf_counter()

        for attempt in range(1, self.max_attempts + 1):
            result.attempts = attempt
            raw = self._call(messages)
            data, problem = self.validate(raw)
            if data:
                sub = data["subcategory"]
                result.category = data["category"]
                result.subcategory = sub
                result.raise_rule = data["raise_rule"]
                result.evidence = str(data.get("evidence", ""))
                result.reason = str(data.get("reason", ""))
                result.default_priority = self.tax.default_priority[sub]
                result.priority, result.raise_check = decide_priority(
                    result.default_priority, result.raise_rule, result.evidence, ticket)
                result.error = ""
                break
            # Show the model its mistake and ask for a corrected answer.
            result.error = problem
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"That answer was invalid: {problem} Reply again with corrected JSON only."},
            ]

        result.latency_s = round(time.perf_counter() - start, 2)
        return result
