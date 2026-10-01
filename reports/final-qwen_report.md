# Evaluation report: final-qwen

Model: `qwen2.5:7b`, prompt version `v4`, 200 held-out tickets, run 2026-09-29 14:28.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 100.0% |
| Subcategory accuracy | 99.5% |
| Priority accuracy | 97.0% |
| Fully correct (subcategory and priority) | 97.0% |
| Invalid answers | 0.0% |
| Priority set too high | 1 tickets |
| Priority set too low | 5 tickets |
| Raises rejected by the code | 21 tickets |
| Average time per ticket | 11.8s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 100.0% | 100.0% |
| escalated | 19 | 100.0% | 73.7% |
| lowercase | 32 | 96.9% | 96.9% |
| multi_issue | 12 | 100.0% | 100.0% |
| typos | 13 | 100.0% | 100.0% |
| vague_subject | 16 | 100.0% | 100.0% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 32 | 1 | 0 | 0 | 0 |
| **Medium** | 0 | 117 | 0 | 0 | 0 |
| **High** | 0 | 3 | 38 | 0 | 0 |
| **Urgent** | 0 | 0 | 2 | 7 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Peripherals | Computer | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 8 | 100.0% | 100.0% |
| Account Locked | 11 | 100.0% | 100.0% |
| Application Error | 15 | 100.0% | 100.0% |
| Card Reader | 12 | 100.0% | 83.3% |
| Computer | 14 | 100.0% | 100.0% |
| Desk Phone | 6 | 100.0% | 100.0% |
| Install Request | 12 | 100.0% | 100.0% |
| Internet Outage | 4 | 100.0% | 100.0% |
| Outlook | 18 | 100.0% | 100.0% |
| Password Reset | 30 | 100.0% | 100.0% |
| Peripherals | 4 | 75.0% | 75.0% |
| Printer/Scanner | 11 | 100.0% | 100.0% |
| Receipt Printer | 13 | 100.0% | 76.9% |
| Register Down | 20 | 100.0% | 100.0% |
| Shared Mailbox | 4 | 100.0% | 100.0% |
| Teams | 5 | 100.0% | 100.0% |
| VPN | 4 | 100.0% | 100.0% |
| Wi-Fi | 9 | 100.0% | 100.0% |

## Examples of misses (first 10 of 6)

**INC-90009** (escalated): Blank receipts. Receipts are coming out blank on register 2. We can only use one register right now.
- Correct: Receipt Printer / High. Predicted: Receipt Printer / Medium
- Model's reason: Blank receipts are a printer issue, and only one register is affected.

**INC-90023** (escalated): Blank receipts. Receipts are coming out blank on the front register. This is affecting all the registers.
- Correct: Receipt Printer / High. Predicted: Receipt Printer / Medium
- Model's reason: Blank receipts on all registers indicate a widespread issue.
- Raise rule: several_people, evidence: "affecting all the registers", check: rejected: quote doesn't fit the rule

**INC-90026** (lowercase): Replacement mouse. my mouse is broken, can i get a replacement?
- Correct: Peripherals / Low. Predicted: Computer / Medium
- Model's reason: Request for a replacement mouse; no raise rule applies.

**INC-90106** (escalated): Blank receipts. Receipts are coming out blank on the front register. This is affecting all the registers.
- Correct: Receipt Printer / High. Predicted: Receipt Printer / Medium
- Model's reason: Blank receipts on all registers indicate a widespread issue.
- Raise rule: several_people, evidence: "affecting all the registers", check: rejected: quote doesn't fit the rule

**INC-90107** (escalated): Payment terminal declining everything. Every card is getting declined on register 2 about an hour ago, even cards that work at the other registers. We have a line of customers waiting.
- Correct: Card Reader / Urgent. Predicted: Card Reader / High
- Model's reason: Card payments are failing on one register, and customers are waiting in line.
- Raise rule: customers_waiting, evidence: "customers are waiting", check: rejected: quote not in ticket

**INC-90191** (escalated): Card reader not connected. The payment terminal on register #1 says 'device not connected'. We have a line of customers waiting.
- Correct: Card Reader / Urgent. Predicted: Card Reader / High
- Model's reason: Card reader issues and customers are waiting, indicating a significant impact.
- Raise rule: customers_waiting, evidence: "customers are waiting", check: rejected: quote not in ticket
