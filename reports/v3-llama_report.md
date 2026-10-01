# Evaluation report: v3-llama

Model: `llama3.2:3b`, prompt version `v3`, 200 held-out tickets, run 2026-09-29 11:28.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 99.5% |
| Subcategory accuracy | 94.5% |
| Priority accuracy | 70.5% |
| Fully correct (subcategory and priority) | 69.5% |
| Invalid answers | 0.0% |
| Priority set too high | 58 tickets |
| Priority set too low | 1 tickets |
| Raises rejected (evidence not in ticket) | 2 tickets |
| Average time per ticket | 7.0s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 96.0% | 72.6% |
| escalated | 17 | 88.2% | 82.4% |
| lowercase | 30 | 93.3% | 66.7% |
| multi_issue | 10 | 100.0% | 70.0% |
| typos | 15 | 93.3% | 66.7% |
| vague_subject | 16 | 87.5% | 50.0% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 20 | 12 | 0 | 0 | 0 |
| **Medium** | 0 | 85 | 32 | 4 | 0 |
| **High** | 0 | 1 | 24 | 10 | 0 |
| **Urgent** | 0 | 0 | 0 | 12 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Wi-Fi | Internet Outage | 6 |
| Account Locked | Password Reset | 4 |
| Shared Mailbox | Access Request | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 5 | 100.0% | 20.0% |
| Account Locked | 14 | 71.4% | 35.7% |
| Application Error | 9 | 100.0% | 100.0% |
| Card Reader | 11 | 100.0% | 63.6% |
| Computer | 24 | 100.0% | 91.7% |
| Desk Phone | 8 | 100.0% | 87.5% |
| Install Request | 7 | 100.0% | 85.7% |
| Internet Outage | 8 | 100.0% | 100.0% |
| Outlook | 13 | 100.0% | 53.8% |
| Password Reset | 32 | 100.0% | 65.6% |
| Peripherals | 3 | 100.0% | 100.0% |
| Printer/Scanner | 11 | 100.0% | 100.0% |
| Receipt Printer | 6 | 100.0% | 100.0% |
| Register Down | 15 | 100.0% | 73.3% |
| Shared Mailbox | 6 | 83.3% | 33.3% |
| Teams | 11 | 100.0% | 72.7% |
| VPN | 4 | 100.0% | 75.0% |
| Wi-Fi | 13 | 53.8% | 30.8% |

## Examples of misses (first 10 of 61)

**INC-10073** (clean): Account locked out. My account got locked about an hour ago after I typed my password wrong a few times.
- Correct: Account Locked / Medium. Predicted: Password Reset / High
- Model's reason: The person says their account was locked out after multiple incorrect password attempts.
- Raise rule: several_people, evidence: "My account got locked about an hour ago", accepted: True

**INC-10114** (clean): Access denied on shared drive. When I try to open the Store Reports folder it says access denied. My manager said I should have it.
- Correct: Access Request / Low. Predicted: Access Request / Medium
- Model's reason: Access denied on a shared folder is a folder access problem.
- Raise rule: several_people, evidence: "When I try to open the Store Reports folder it says access denied", accepted: True

**INC-10204** (clean): Payment terminal declining everything. Every card is getting declined on register #1 this morning, even cards that work at the other registers.
- Correct: Card Reader / High. Predicted: Card Reader / Urgent
- Model's reason: The payment terminal is declining all card payments; this is a card reader problem.
- Raise rule: customers_waiting, evidence: "Every card is getting declined on register #1 this morning", accepted: True

**INC-10299** (typos;lowercase): Can't connect to wifi. my dekstop won't connect to the wi-fi on and off all week.
- Correct: Wi-Fi / Medium. Predicted: Internet Outage / Urgent
- Model's reason: One device with wireless connectivity issues; the ticket says it's been on and off all week.
- Raise rule: several_people, evidence: "my desk won't connect to the wi-fi on and off all week", accepted: False

**INC-10387** (lowercase): Account locked again. i keep getting locked out even after it gets unlocked. it happened again on and off all week.
- Correct: Account Locked / Medium. Predicted: Account Locked / High
- Model's reason: The account keeps getting locked out, and the person says it's happening repeatedly.
- Raise rule: several_people, evidence: "i keep getting locked out even after it gets unlocked", accepted: True

**INC-10436** (clean): Teams won't sign in. Teams shows error 0x80070005 when I try to sign in.
- Correct: Teams / Low. Predicted: Teams / Medium
- Model's reason: Teams sign-in error; the error code is mentioned.
- Raise rule: several_people, evidence: "Teams shows error 0x80070005 when I try to sign in", accepted: True

**INC-10496** (clean): Account locked again. I keep getting locked out even after it gets unlocked. It happened again since we opened.
- Correct: Account Locked / Medium. Predicted: Account Locked / High
- Model's reason: The account is locked again, and the person says it gets unlocked but still happens.
- Raise rule: several_people, evidence: "I keep getting locked out even after it gets unlocked", accepted: True

**INC-10542** (vague_subject): urgent!!. I keep getting locked out even after it gets unlocked. It happened again this morning.
- Correct: Account Locked / Medium. Predicted: Account Locked / High
- Model's reason: The person says they keep getting locked out, but 'urgent' is not a raise rule.
- Raise rule: several_people, evidence: "I keep getting locked out even after it gets unlocked", accepted: True

**INC-10625** (lowercase): Password expired. my password expired since we opened and now i can't sign in to anything. can someone reset it?
- Correct: Password Reset / Medium. Predicted: Password Reset / High
- Model's reason: A forgotten password is a password reset problem.
- Raise rule: several_people, evidence: "my password expired since we opened", accepted: True

**INC-10643** (clean): Keep getting locked out. I keep getting locked out even after it gets unlocked. It happened again on and off all week.
- Correct: Account Locked / Medium. Predicted: Password Reset / High
- Model's reason: The person is getting locked out repeatedly, but the ticket doesn't say the account is locked out.
- Raise rule: several_people, evidence: "I keep getting locked out even after it gets unlocked", accepted: True
