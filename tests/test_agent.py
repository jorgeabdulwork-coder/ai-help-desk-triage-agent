"""Tests for Phase 4: KB search, reply checks, the judge, and the full agent.

Uses a fake client, so no model is needed. Its fake embeddings are simple
word-count vectors: texts sharing words come out similar, which is enough
to test the search logic.
"""

import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from triage.agent import TriageAgent
from triage.config import LLMConfig
from triage.judge import ReplyJudge
from triage.kb import KnowledgeBase, cosine
from triage.reply import ReplyDrafter, check_reply, tidy

KB = {a["id"]: a for a in json.load(open(Path(__file__).resolve().parent.parent / "data" / "kb_articles.json"))}

CONFIG = LLMConfig(base_url="http://fake", api_key="x", model="fake", schema_mode="json_schema",
                   temperature=0, timeout=5, embed_model="fake-embed")
TICKET = {"ticket_id": "T1", "requester": "Maria Garcia", "role": "Accountant", "location": "Admin Office",
          "subject": "Copier not working",
          "description": "The office copier has print jobs stuck in the queue and scan to email fails."}
CLASSIFICATION = {"reason": "Office printer queue.", "category": "Hardware", "subcategory": "Printer/Scanner",
                  "raise_rule": "none", "evidence": ""}
GOOD_REPLY = ("Hi Maria,\n\nSorry the printer is giving you trouble. Please try:\n"
              "1. Check the printer screen for jams or low toner\n2. Turn the printer off and on\n"
              "3. Cancel stuck jobs and print again\n\nIf that doesn't work, IT will re-add the printer "
              "on your computer.\n\nIT Help Desk")


def fake_vector(text, dims=256):
    text = re.sub(r"^search_(query|document): ", "", text)
    vec = [0.0] * dims
    for word in re.findall(r"[a-z]+", text.lower()):
        vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % dims] += 1
    return vec


class FakeClient:
    """Answers like each part of the agent would, based on the system prompt it receives."""

    def __init__(self, classification=CLASSIFICATION, reply=GOOD_REPLY, grade=None):
        self.classification, self.reply = classification, reply
        self.grade = grade or {"grounded": True, "invented_quote": "", "steps_fit": True,
                               "addresses_issue": True, "tone_ok": True, "note": "none"}
        self.embed_calls = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._chat))
        self.embeddings = SimpleNamespace(create=self._embed)

    def _chat(self, **kwargs):
        system = kwargs["messages"][0]["content"]
        if "You review draft replies" in system:  # checked first: the judge's prompt quotes the reply rules
            content = json.dumps(self.grade)
        elif "triage assistant" in system:
            content = json.dumps(self.classification)
        else:
            content = self.reply
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

    def _embed(self, model, input):
        self.embed_calls += 1
        return SimpleNamespace(data=[SimpleNamespace(embedding=fake_vector(t)) for t in input])


class KBTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name) / "emb.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_cosine(self):
        self.assertAlmostEqual(cosine([1, 0], [1, 0]), 1.0)
        self.assertAlmostEqual(cosine([1, 0], [0, 1]), 0.0)

    def test_search_finds_the_matching_article(self):
        kb = KnowledgeBase(CONFIG, FakeClient(), cache_path=self.cache)
        top = kb.search("Card reader declining chip cards, payment terminal not connected")[0][0]
        self.assertEqual(top["id"], "KB-202")

    def test_article_embeddings_are_cached(self):
        client = FakeClient()
        KnowledgeBase(CONFIG, client, cache_path=self.cache).search("printer")
        first = client.embed_calls  # articles + the query
        KnowledgeBase(CONFIG, client, cache_path=self.cache).search("printer")
        self.assertEqual(client.embed_calls - first, 1)  # only the query this time

    def test_changed_article_is_embedded_again(self):
        client = FakeClient()
        KnowledgeBase(CONFIG, client, cache_path=self.cache).search("printer")
        kb = KnowledgeBase(CONFIG, client, cache_path=self.cache)
        kb.articles[0] = dict(kb.articles[0], title="A brand new title")
        before = client.embed_calls
        kb.search("printer")
        self.assertEqual(client.embed_calls - before, 2)  # the changed article + the query

    def test_suggestion_uses_classification_and_flags_disagreement(self):
        kb = KnowledgeBase(CONFIG, FakeClient(), cache_path=self.cache)
        agree = kb.suggest(TICKET, "Printer/Scanner")
        self.assertEqual(agree.primary["id"], "KB-401")
        self.assertFalse(agree.needs_review)
        disagree = kb.suggest(TICKET, "Teams")
        self.assertEqual(disagree.primary["id"], "KB-302")
        self.assertTrue(disagree.needs_review)
        self.assertIn("Printer/Scanner", disagree.review_note)


class ReplyCheckTests(unittest.TestCase):
    def test_good_reply_passes(self):
        self.assertEqual(check_reply(GOOD_REPLY, TICKET, KB["KB-401"]), [])

    def test_password_request_is_caught(self):
        bad = GOOD_REPLY.replace("Please try:", "Please reply with your current password so we can check.")
        self.assertIn("asks for a password", check_reply(bad, TICKET, KB["KB-401"]))

    def test_mentioning_a_password_reset_is_fine(self):
        ok = GOOD_REPLY.replace("Please try:", "IT will reset your password after confirming your identity.")
        self.assertEqual(check_reply(ok, TICKET, KB["KB-401"]), [])

    def test_invented_phone_number_is_caught(self):
        bad = GOOD_REPLY.replace("IT Help Desk", "Call us at 941-555-0123.\nIT Help Desk")
        self.assertIn("contains a link or phone number not in the KB", check_reply(bad, TICKET, KB["KB-401"]))

    def test_missing_greeting_and_signoff(self):
        problems = check_reply("Please restart the printer.", TICKET)
        self.assertIn("does not greet the requester by first name", problems)
        self.assertIn("does not end with 'IT Help Desk' on its own line", problems)

    def test_internal_labels_are_caught(self):
        bad = GOOD_REPLY.replace("If that doesn't work, IT will", "For IT, we will")
        self.assertIn("uses internal labels like 'For IT'", check_reply(bad, TICKET, KB["KB-401"]))

    def test_signoff_on_same_line_is_caught(self):
        bad = GOOD_REPLY.replace("\n\nIT Help Desk", " Thanks, IT Help Desk")
        self.assertIn("does not end with 'IT Help Desk' on its own line", check_reply(bad, TICKET, KB["KB-401"]))

    def test_real_llama_mistakes_are_caught(self):
        """Patterns from the r2 Llama evaluation."""
        outlook = dict(TICKET, subject="Outlook won't start", description="Outlook won't open on my desktop.")
        cases = [
            ("We'll repair your Office profile. If that doesn't help, we'll re-add the printer for you.",
             "mentions printer"),
            ("Outlook shows a blank screen, which is likely due to a corrupted Office profile.", "guesses at a cause"),
            ("I'll follow the steps outlined in KB-301.", "mentions a KB article number"),
            ("This is causing an Urgent outage for you.", "mentions a priority level"),
        ]
        for sentence, expected in cases:
            reply = f"Hi Maria,\n\n{sentence}\n\nIT Help Desk"
            problems = check_reply(reply, outlook, KB["KB-301"])
            self.assertTrue(any(p.startswith(expected) for p in problems), (sentence, problems))

    def test_acknowledging_urgency_in_plain_words_is_fine(self):
        reply = ("Hi Maria,\n\nWe know this is affecting your work and we are already working on it.\n\n"
                 "IT Help Desk")
        self.assertEqual(check_reply(reply, TICKET, KB["KB-401"]), [])

    def test_tidy_removes_extra_blank_lines(self):
        self.assertEqual(tidy('"Hi Maria,   \n\n\n\nText.\n\n\n\nIT Help Desk"'),
                         "Hi Maria,\n\nText.\n\nIT Help Desk")

    def test_reply_model_setting_is_used(self):
        client = FakeClient()
        calls = []
        original = client.chat.completions.create
        client.chat.completions.create = lambda **k: calls.append(k["model"]) or original(**k)
        config = LLMConfig(**{**CONFIG.__dict__, "reply_model": "big-writer"})
        ReplyDrafter(config, client).draft(TICKET, SimpleNamespace(subcategory="Printer/Scanner", priority="Medium"),
                                          KB["KB-401"])
        self.assertEqual(calls, ["big-writer"])

    def test_writer_never_sees_kb_number(self):
        messages = ReplyDrafter(CONFIG, FakeClient()).build_messages(
            TICKET, SimpleNamespace(subcategory="Printer/Scanner", priority="Medium"), KB["KB-401"])
        self.assertNotIn("KB-401", messages[1]["content"])

    def test_drafter_labels_it_steps(self):
        from triage.kb import KnowledgeBase
        article = KnowledgeBase(CONFIG, FakeClient(), cache_path=Path(tempfile.gettempdir()) / "x.json").by_subcategory["Account Locked"]
        messages = ReplyDrafter(CONFIG, FakeClient()).build_messages(
            dict(TICKET, subject="Locked", description="Account locked"),
            SimpleNamespace(subcategory="Account Locked", priority="Medium"), article)
        text = messages[1]["content"]
        self.assertIn("What IT does (describe as what we will do):\n- Confirm identity and unlock the account", text)


class JudgeTests(unittest.TestCase):
    KB401 = {"id": "KB-401", "title": "Office printer or scanner problems", "summary": "",
             "user_steps": ["Printing: turn the printer off and on"], "it_steps": []}

    def grade_with(self, **overrides):
        grade = {"grounded": False, "invented_quote": "", "steps_fit": True,
                 "addresses_issue": True, "tone_ok": True, "note": "x", **overrides}
        return ReplyJudge(CONFIG, FakeClient(grade=grade)).judge(TICKET, self.KB401, GOOD_REPLY)

    def test_judge_flag_confirmed_when_quote_is_not_in_kb(self):
        g = self.grade_with(invented_quote="Call the vendor hotline for a new toner cartridge.")
        self.assertTrue(g["judge_check"].startswith("confirmed"))

    def test_judge_flag_marked_false_alarm_when_quote_is_in_kb(self):
        g = self.grade_with(invented_quote="Turn the printer off and on again.")
        self.assertTrue(g["judge_check"].startswith("likely false alarm"))

    def test_judge_flag_without_quote(self):
        self.assertEqual(self.grade_with()["judge_check"], "no quote given")

    def test_valid_grade(self):
        grade = ReplyJudge(CONFIG, FakeClient()).judge(TICKET, {"id": "KB-401", "title": "t"}, GOOD_REPLY)
        self.assertIs(grade["grounded"], True)

    def test_invalid_grade_is_marked(self):
        client = FakeClient()
        client._chat = lambda **k: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))])
        client.chat = SimpleNamespace(completions=SimpleNamespace(create=client._chat))
        grade = ReplyJudge(CONFIG, client).judge(TICKET, {"id": "KB-401", "title": "t"}, GOOD_REPLY)
        self.assertIsNone(grade["grounded"])


class SerializeTests(unittest.TestCase):
    def test_result_becomes_plain_json(self):
        from triage.serialize import result_to_dict
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            kb = KnowledgeBase(CONFIG, client, cache_path=Path(tmp) / "emb.json")
            ticket = dict(TICKET, subcategory="Printer/Scanner", priority="Medium")
            data = result_to_dict(ticket, TriageAgent(CONFIG, client=client, kb=kb).run(ticket), CONFIG)
        json.dumps(data)  # must be serializable for the web pages
        self.assertEqual(data["triage"]["priority"], "Medium")
        self.assertEqual(data["kb"]["primary"]["id"], "KB-401")
        self.assertEqual(data["expected"], {"subcategory": "Printer/Scanner", "priority": "Medium"})


class AgentTests(unittest.TestCase):
    def test_full_pipeline(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            kb = KnowledgeBase(CONFIG, client, cache_path=Path(tmp) / "emb.json")
            result = TriageAgent(CONFIG, client=client, kb=kb).run(TICKET)
        self.assertEqual((result.triage.subcategory, result.triage.priority), ("Printer/Scanner", "Medium"))
        self.assertEqual(result.kb.primary["id"], "KB-401")
        self.assertTrue(result.reply.startswith("Hi Maria"))
        self.assertFalse(result.needs_review)

    def test_bad_reply_marks_ticket_for_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient(reply="Just restart it.")
            kb = KnowledgeBase(CONFIG, client, cache_path=Path(tmp) / "emb.json")
            result = TriageAgent(CONFIG, client=client, kb=kb).run(TICKET)
        self.assertTrue(result.needs_review)


if __name__ == "__main__":
    unittest.main()
