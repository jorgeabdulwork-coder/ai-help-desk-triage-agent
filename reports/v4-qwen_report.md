# Evaluation report: v4-qwen

Model: `qwen2.5:7b`, prompt version `v4`, 200 held-out tickets, run 2026-09-29 13:48.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 99.5% |
| Subcategory accuracy | 98.5% |
| Priority accuracy | 98.5% |
| Fully correct (subcategory and priority) | 98.0% |
| Invalid answers | 0.0% |
| Priority set too high | 2 tickets |
| Priority set too low | 1 tickets |
| Raises rejected by the code | 22 tickets |
| Average time per ticket | 17.7s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 99.2% | 100.0% |
| escalated | 17 | 100.0% | 94.1% |
| lowercase | 30 | 100.0% | 100.0% |
| multi_issue | 10 | 90.0% | 90.0% |
| typos | 15 | 100.0% | 100.0% |
| vague_subject | 16 | 93.8% | 93.8% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 31 | 1 | 0 | 0 | 0 |
| **Medium** | 0 | 120 | 1 | 0 | 0 |
| **High** | 0 | 0 | 35 | 0 | 0 |
| **Urgent** | 0 | 0 | 1 | 11 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Peripherals | Computer | 1 |
| Receipt Printer | Register Down | 1 |
| Shared Mailbox | Access Request | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 5 | 100.0% | 100.0% |
| Account Locked | 14 | 100.0% | 100.0% |
| Application Error | 9 | 100.0% | 100.0% |
| Card Reader | 11 | 100.0% | 90.9% |
| Computer | 24 | 100.0% | 100.0% |
| Desk Phone | 8 | 100.0% | 100.0% |
| Install Request | 7 | 100.0% | 100.0% |
| Internet Outage | 8 | 100.0% | 100.0% |
| Outlook | 13 | 100.0% | 100.0% |
| Password Reset | 32 | 100.0% | 100.0% |
| Peripherals | 3 | 66.7% | 66.7% |
| Printer/Scanner | 11 | 100.0% | 100.0% |
| Receipt Printer | 6 | 83.3% | 83.3% |
| Register Down | 15 | 100.0% | 100.0% |
| Shared Mailbox | 6 | 83.3% | 100.0% |
| Teams | 11 | 100.0% | 100.0% |
| VPN | 4 | 100.0% | 100.0% |
| Wi-Fi | 13 | 100.0% | 100.0% |

## Examples of misses (first 10 of 4)

**INC-10158** (escalated): Card reader not working. The card reader on register 4 isn't reading chip cards. Tap works sometimes. This is affecting all the registers.
- Correct: Card Reader / Urgent. Predicted: Card Reader / High
- Model's reason: Chip card reading issues on one register and the ticket states it is affecting all the registers.
- Raise rule: several_people, evidence: "affecting all the registers", check: rejected: quote doesn't fit the rule

**INC-11600** (vague_subject): IT problem. My keyboard stopped working right after lunch.
- Correct: Peripherals / Low. Predicted: Computer / Medium
- Model's reason: One keyboard stopped working; no one else is affected.

**INC-12547** (multi_issue): Receipt printer jammed. The receipt printer keeps jamming and beeping. Also, the POS on register 2 keeps restarting by itself in the middle of transactions.
- Correct: Receipt Printer / Medium. Predicted: Register Down / High
- Model's reason: The first problem is a receipt printer jam; the second is a POS issue, but only one register is affected.

**INC-12900** (clean): Shared mailbox access. I need access to the donations inbox for my new role.
- Correct: Shared Mailbox / Low. Predicted: Access Request / Low
- Model's reason: Access to a shared mailbox is requested for a new hire.
