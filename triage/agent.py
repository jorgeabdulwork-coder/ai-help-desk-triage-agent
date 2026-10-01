"""The full agent: classify the ticket, suggest a KB article, draft a reply.

    ticket -> Classifier -> KnowledgeBase.suggest -> ReplyDrafter -> check_reply
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

from .classifier import Classifier, TriageResult
from .config import LLMConfig, make_client
from .kb import KBSuggestion, KnowledgeBase
from .reply import ReplyDrafter, check_reply


@dataclass
class AgentResult:
    triage: TriageResult
    kb: Optional[KBSuggestion] = None
    reply: str = ""
    reply_problems: list = field(default_factory=list)
    latency_s: float = 0.0

    @property
    def needs_review(self) -> bool:
        return bool((self.kb and self.kb.needs_review) or self.reply_problems or not self.triage.ok)


class TriageAgent:
    def __init__(self, config: LLMConfig, client=None, kb: Optional[KnowledgeBase] = None):
        client = client or make_client(config)
        self.classifier = Classifier(config, client=client)
        self.kb = kb or KnowledgeBase(config, client)
        self.drafter = ReplyDrafter(config, client)

    def run(self, ticket: dict) -> AgentResult:
        start = time.perf_counter()
        triage = self.classifier.classify(ticket)
        result = AgentResult(triage=triage)
        if triage.ok:
            result.kb = self.kb.suggest(ticket, triage.subcategory)
            result.reply = self.drafter.draft(ticket, triage, result.kb.primary)
            result.reply_problems = check_reply(result.reply, ticket, result.kb.primary)
        result.latency_s = round(time.perf_counter() - start, 2)
        return result
