"""Tests for the classifier logic, using a fake model so no LLM is needed.

Run with:  python -m unittest discover tests
"""

import json
import unittest
from types import SimpleNamespace

from triage.classifier import (EXAMPLES, Classifier, decide_priority, evidence_fits_rule,
                               evidence_in_ticket)
from triage.config import LLMConfig

CONFIG = LLMConfig(base_url="http://fake", api_key="x", model="fake",
                   schema_mode="json_schema", temperature=0, timeout=5)
TICKET = {"subject": "Printer not working", "description": "Jobs stuck in the queue.",
          "role": "Accountant", "location": "Admin Office"}
GOOD = {"reason": "Printer queue problem.", "category": "Hardware",
        "subcategory": "Printer/Scanner", "raise_rule": "none", "evidence": ""}


class FakeClient:
    """Mimics openai.OpenAI: returns the queued replies in order and records each request."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.requests.append(kwargs)
        content = self.replies.pop(0)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def make(replies):
    client = FakeClient(replies)
    return Classifier(CONFIG, client=client), client


class ClassifierTests(unittest.TestCase):
    def test_valid_answer_gets_default_priority(self):
        clf, _ = make([json.dumps(GOOD)])
        r = clf.classify(TICKET)
        self.assertTrue(r.ok)
        self.assertEqual((r.subcategory, r.priority, r.raised, r.attempts), ("Printer/Scanner", "Medium", False, 1))

    def test_raise_with_real_evidence(self):
        ticket = dict(TICKET, description="Jobs stuck in the queue. Several of us are having the same problem.")
        answer = dict(GOOD, raise_rule="several_people", evidence="Several of us are having the same problem")
        clf, _ = make([json.dumps(answer)])
        r = clf.classify(ticket)
        self.assertTrue(r.raised)
        self.assertEqual(r.priority, "High")

    def test_raise_with_invented_evidence_is_rejected(self):
        answer = dict(GOOD, raise_rule="several_people", evidence="the whole office is affected")
        clf, _ = make([json.dumps(answer)])
        r = clf.classify(TICKET)
        self.assertFalse(r.raised)
        self.assertEqual(r.priority, "Medium")

    def test_raise_rule_without_evidence_is_rejected(self):
        clf, _ = make([json.dumps(dict(GOOD, raise_rule="cannot_work", evidence=""))])
        self.assertEqual(clf.classify(TICKET).priority, "Medium")

    def test_code_fence_is_stripped(self):
        clf, _ = make(["```json\n" + json.dumps(GOOD) + "\n```"])
        self.assertTrue(clf.classify(TICKET).ok)

    def test_mismatched_category_triggers_retry_with_feedback(self):
        bad = dict(GOOD, category="Software")
        clf, client = make([json.dumps(bad), json.dumps(GOOD)])
        r = clf.classify(TICKET)
        self.assertTrue(r.ok)
        self.assertEqual(r.attempts, 2)
        self.assertIn("belongs to 'Hardware'", client.requests[1]["messages"][-1]["content"])

    def test_invented_values_are_rejected(self):
        clf, _ = make([json.dumps(dict(GOOD, subcategory="Toaster", raise_rule="vip_user"))] * 2)
        r = clf.classify(TICKET)
        self.assertFalse(r.ok)
        self.assertIn("'Toaster' is not a valid subcategory", r.error)
        self.assertIn("'vip_user' is not a valid raise_rule", r.error)

    def test_broken_json_then_recovers(self):
        clf, _ = make(["Sure! Here is the answer", json.dumps(GOOD)])
        r = clf.classify(TICKET)
        self.assertTrue(r.ok)
        self.assertEqual(r.attempts, 2)

    def test_correct_labels_never_sent_to_model(self):
        ticket = dict(TICKET, category="Hardware", subcategory="Printer/Scanner", priority="Medium")
        clf, client = make([json.dumps(GOOD)])
        clf.classify(ticket)
        sent = client.requests[0]["messages"][-1]["content"]
        self.assertNotIn("Printer/Scanner", sent)
        self.assertNotIn("Medium", sent)

    def test_schema_has_no_priority_field(self):
        clf, client = make([json.dumps(GOOD)])
        clf.classify(TICKET)
        props = client.requests[0]["response_format"]["json_schema"]["schema"]["properties"]
        self.assertNotIn("priority", props)
        self.assertIn("raise_rule", props)

    def test_every_example_is_valid_and_its_evidence_is_real(self):
        clf, _ = make([])
        for ticket, answer in EXAMPLES:
            data, problem = clf.validate(json.dumps(answer))
            self.assertIsNotNone(data, problem)
            if answer["raise_rule"] != "none":
                self.assertTrue(evidence_in_ticket(answer["evidence"], ticket), answer["evidence"])
                self.assertTrue(evidence_fits_rule(answer["evidence"], answer["raise_rule"]), answer["evidence"])


class PriorityRuleTests(unittest.TestCase):
    def test_raise_one_level_and_cap_at_urgent(self):
        t = {"subject": "", "description": "Several of us are having the same problem."}
        ev = "Several of us are having the same problem"
        self.assertEqual(decide_priority("Low", "several_people", ev, t), ("Medium", "accepted"))
        self.assertEqual(decide_priority("Urgent", "several_people", ev, t), ("Urgent", "accepted"))
        self.assertEqual(decide_priority("High", "none", "", t), ("High", ""))

    def test_evidence_tolerates_typos_and_case(self):
        ticket = {"subject": "Help", "description": "sevreal of us are having the same porblem."}
        self.assertTrue(evidence_in_ticket("Several of us are having the same problem", ticket))
        self.assertTrue(evidence_fits_rule("sevreal of us are having the same porblem", "several_people"))

    def test_evidence_rejects_one_word_quotes(self):
        self.assertFalse(evidence_in_ticket("everyone", {"subject": "", "description": "everyone is down"}))

    def test_real_escalation_phrases_fit_their_rules(self):
        cases = [
            ("This is happening to everyone in the office", "several_people"),
            ("No one in our office has received email", "several_people"),
            ("We have a line of customers waiting", "customers_waiting"),
            ("This is affecting all the registers", "customers_waiting"),
            ("We can only use one register right now", "customers_waiting"),
            ("I can't do any work until this is fixed", "cannot_work"),
            ("I cant get anything done today", "cannot_work"),
        ]
        for quote, rule in cases:
            self.assertTrue(evidence_fits_rule(quote, rule), quote)

    def test_bad_quotes_from_the_v3_reports_are_rejected(self):
        """Real sentences the AI used as fake proof in the v3 evaluation runs."""
        cases = [
            ("My account got locked about an hour ago", "several_people"),
            ("Teams shows error 0x80070005 when I try to sign in", "several_people"),
            ("I keep getting locked out even after it gets unlocked", "several_people"),
            ("people say they sent me stuff", "several_people"),
            ("callers get a busy signal", "customers_waiting"),
            ("Every card is getting declined on register #1 this morning, even cards that work at "
             "the other registers", "customers_waiting"),
            ("front register is down", "customers_waiting"),
        ]
        for quote, rule in cases:
            self.assertFalse(evidence_fits_rule(quote, rule), quote)

    def test_rejection_reason_is_reported(self):
        t = {"subject": "", "description": "My account got locked about an hour ago."}
        self.assertEqual(decide_priority("Medium", "several_people", "the whole office is down", t),
                         ("Medium", "rejected: quote not in ticket"))
        self.assertEqual(decide_priority("Medium", "several_people", "My account got locked about an hour ago", t),
                         ("Medium", "rejected: quote doesn't fit the rule"))


if __name__ == "__main__":
    unittest.main()
