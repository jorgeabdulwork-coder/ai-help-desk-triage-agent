"""Tests for the scoring functions, using small hand-made prediction rows."""

import unittest

from triage import metrics


def row(true_sub, true_pri, pred_sub, pred_pri, tags="", error="", cat="Hardware"):
    return {"true_category": cat, "true_subcategory": true_sub, "true_priority": true_pri,
            "pred_category": cat if pred_sub else "", "pred_subcategory": pred_sub,
            "pred_priority": pred_pri, "tags": tags, "error": error, "latency_s": "2"}


ROWS = [
    row("Computer", "Medium", "Computer", "Medium"),                          # fully correct
    row("Computer", "Medium", "Peripherals", "Medium", tags="vague_subject"),  # wrong subcategory
    row("Computer", "Medium", "Computer", "High", tags="typos;lowercase"),     # priority too high
    row("Computer", "High", "Computer", "Low", tags="escalated"),              # priority too low
    row("Computer", "Medium", "", "", error="not valid JSON"),                 # invalid answer
]


class MetricsTests(unittest.TestCase):
    def test_summary(self):
        s = metrics.summary(ROWS)
        self.assertEqual(s["tickets"], 5)
        self.assertAlmostEqual(s["subcategory_acc"], 3 / 5)
        self.assertAlmostEqual(s["priority_acc"], 2 / 5)
        self.assertAlmostEqual(s["fully_correct"], 1 / 5)
        self.assertAlmostEqual(s["invalid_rate"], 1 / 5)
        self.assertEqual((s["over_prioritized"], s["under_prioritized"]), (1, 1))

    def test_ticket_with_two_tags_counts_in_both_groups(self):
        groups = metrics.by_tag(ROWS)
        self.assertEqual(groups["typos"][0], 1)
        self.assertEqual(groups["lowercase"][0], 1)
        self.assertEqual(groups["(clean)"][0], 2)

    def test_confusions_include_invalid(self):
        pairs = dict(metrics.top_confusions(ROWS))
        self.assertEqual(pairs[("Computer", "Peripherals")], 1)
        self.assertEqual(pairs[("Computer", "(invalid)")], 1)

    def test_priority_matrix(self):
        m = metrics.priority_matrix(ROWS)
        self.assertEqual(m["High"]["Low"], 1)
        self.assertEqual(m["Medium"]["(invalid)"], 1)


if __name__ == "__main__":
    unittest.main()
