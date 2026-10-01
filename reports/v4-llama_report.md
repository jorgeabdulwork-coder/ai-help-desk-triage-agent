# Evaluation report: v4-llama

Model: `llama3.2:3b`, prompt version `v4`, 200 held-out tickets, run 2026-09-29 12:48.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 99.5% |
| Subcategory accuracy | 95.5% |
| Priority accuracy | 96.0% |
| Fully correct (subcategory and priority) | 94.5% |
| Invalid answers | 0.0% |
| Priority set too high | 5 tickets |
| Priority set too low | 3 tickets |
| Raises rejected by the code | 66 tickets |
| Average time per ticket | 7.0s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 96.0% | 97.6% |
| escalated | 17 | 88.2% | 76.5% |
| lowercase | 30 | 96.7% | 100.0% |
| multi_issue | 10 | 100.0% | 100.0% |
| typos | 15 | 100.0% | 100.0% |
| vague_subject | 16 | 93.8% | 93.8% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 32 | 0 | 0 | 0 | 0 |
| **Medium** | 1 | 117 | 0 | 3 | 0 |
| **High** | 0 | 0 | 33 | 2 | 0 |
| **Urgent** | 0 | 0 | 2 | 10 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Wi-Fi | Internet Outage | 5 |
| Account Locked | Password Reset | 2 |
| Application Error | Install Request | 1 |
| Printer/Scanner | Receipt Printer | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 5 | 100.0% | 100.0% |
| Account Locked | 14 | 85.7% | 100.0% |
| Application Error | 9 | 88.9% | 88.9% |
| Card Reader | 11 | 100.0% | 81.8% |
| Computer | 24 | 100.0% | 100.0% |
| Desk Phone | 8 | 100.0% | 100.0% |
| Install Request | 7 | 100.0% | 100.0% |
| Internet Outage | 8 | 100.0% | 100.0% |
| Outlook | 13 | 100.0% | 100.0% |
| Password Reset | 32 | 100.0% | 100.0% |
| Peripherals | 3 | 100.0% | 100.0% |
| Printer/Scanner | 11 | 90.9% | 100.0% |
| Receipt Printer | 6 | 100.0% | 100.0% |
| Register Down | 15 | 100.0% | 100.0% |
| Shared Mailbox | 6 | 100.0% | 100.0% |
| Teams | 11 | 100.0% | 100.0% |
| VPN | 4 | 100.0% | 100.0% |
| Wi-Fi | 13 | 61.5% | 61.5% |

## Examples of misses (first 10 of 11)

**INC-10896** (vague_subject): Please call me. The Wi-Fi keeps dropping every few minutes.
- Correct: Wi-Fi / Medium. Predicted: Internet Outage / Urgent
- Model's reason: The person says they can't get online.
- Raise rule: several_people, evidence: "The Wi-Fi keeps dropping every few minutes", check: accepted

**INC-11026** (clean): The timekeeping app not working. When I open the timekeeping app I get 'something went wrong, try again later'.
- Correct: Application Error / Medium. Predicted: Install Request / Low
- Model's reason: One app is not working; the person says 'something went wrong', which is not a raise rule.

**INC-11279** (clean): Locked out of my computer. My account got locked right after lunch after I typed my password wrong a few times.
- Correct: Account Locked / Medium. Predicted: Password Reset / Medium
- Model's reason: Windows reports a locked-out account; the person says they typed their password wrong.
- Raise rule: several_people, evidence: "My account got locked right after lunch", check: rejected: quote doesn't fit the rule

**INC-11745** (escalated): Wi-Fi disconnecting. The Wi-Fi keeps dropping every few minutes. Several of us are having the same problem.
- Correct: Wi-Fi / High. Predicted: Internet Outage / Urgent
- Model's reason: The problem is Wi-Fi, and several people are affected.
- Raise rule: several_people, evidence: "Several of us are having the same problem", check: accepted

**INC-11869** (clean): Wi-Fi disconnecting. The Wi-Fi keeps dropping every few minutes.
- Correct: Wi-Fi / Medium. Predicted: Internet Outage / Urgent
- Model's reason: The Wi-Fi is dropping; no mention of the whole site or customers waiting.

**INC-12076** (clean): Can't connect to wifi. My work PC won't connect to the Wi-Fi since we opened.
- Correct: Wi-Fi / Medium. Predicted: Internet Outage / Urgent
- Model's reason: No connection to the whole site's internet; the ticket says the person can't connect.
- Raise rule: several_people, evidence: "My work PC won't connect to the Wi-Fi", check: rejected: quote doesn't fit the rule

**INC-12108** (lowercase): Locked out of my computer. my account got locked right after lunch after i typed my password wrong a few times.
- Correct: Account Locked / Medium. Predicted: Password Reset / Medium
- Model's reason: Windows reports a locked-out account; the person says they typed their password wrong.

**INC-12270** (clean): Can't print. The label printer isn't printing anything, jobs just sit in the queue.
- Correct: Printer/Scanner / Medium. Predicted: Receipt Printer / Medium
- Model's reason: The label printer is not working, and the person is a retail associate.
- Raise rule: customers_waiting, evidence: "jobs just sit in the queue", check: rejected: quote doesn't fit the rule

**INC-12305** (escalated): Payment terminal declining everything. Every card is getting declined on register 2 after the update last night, even cards that work at the other registers. We can only use one register right now.
- Correct: Card Reader / Urgent. Predicted: Card Reader / High
- Model's reason: The payment terminal is failing; the ticket says it's a problem with the card reader.
- Raise rule: customers_waiting, evidence: "customers are waiting", check: rejected: quote not in ticket

**INC-12560** (escalated): Wi-Fi disconnecting. The Wi-Fi keeps dropping every few minutes. This is happening to everyone in the office.
- Correct: Wi-Fi / High. Predicted: Internet Outage / Urgent
- Model's reason: The whole office is affected by the Wi-Fi issue.
- Raise rule: several_people, evidence: "This is happening to everyone in the office", check: accepted
