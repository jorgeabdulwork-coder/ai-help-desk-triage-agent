# Evaluation report: v3-qwen

Model: `qwen2.5:7b`, prompt version `v3`, 200 held-out tickets, run 2026-09-29 12:08.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 100.0% |
| Subcategory accuracy | 95.5% |
| Priority accuracy | 89.0% |
| Fully correct (subcategory and priority) | 89.0% |
| Invalid answers | 0.0% |
| Priority set too high | 22 tickets |
| Priority set too low | 0 tickets |
| Raises rejected (evidence not in ticket) | 3 tickets |
| Average time per ticket | 11.4s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 96.8% | 91.1% |
| escalated | 17 | 100.0% | 100.0% |
| lowercase | 30 | 90.0% | 80.0% |
| multi_issue | 10 | 90.0% | 90.0% |
| typos | 15 | 100.0% | 93.3% |
| vague_subject | 16 | 93.8% | 81.2% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 24 | 8 | 0 | 0 | 0 |
| **Medium** | 0 | 110 | 11 | 0 | 0 |
| **High** | 0 | 0 | 32 | 3 | 0 |
| **Urgent** | 0 | 0 | 0 | 12 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Teams | Outlook | 7 |
| Peripherals | Computer | 1 |
| Receipt Printer | Register Down | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 5 | 100.0% | 100.0% |
| Account Locked | 14 | 100.0% | 92.9% |
| Application Error | 9 | 100.0% | 100.0% |
| Card Reader | 11 | 100.0% | 81.8% |
| Computer | 24 | 100.0% | 100.0% |
| Desk Phone | 8 | 100.0% | 50.0% |
| Install Request | 7 | 100.0% | 100.0% |
| Internet Outage | 8 | 100.0% | 100.0% |
| Outlook | 13 | 100.0% | 76.9% |
| Password Reset | 32 | 100.0% | 96.9% |
| Peripherals | 3 | 66.7% | 66.7% |
| Printer/Scanner | 11 | 100.0% | 100.0% |
| Receipt Printer | 6 | 83.3% | 83.3% |
| Register Down | 15 | 100.0% | 93.3% |
| Shared Mailbox | 6 | 100.0% | 100.0% |
| Teams | 11 | 36.4% | 36.4% |
| VPN | 4 | 100.0% | 75.0% |
| Wi-Fi | 13 | 100.0% | 100.0% |

## Examples of misses (first 10 of 22)

**INC-10004** (clean): Phone not ringing. The main phone isn't ringing, callers get a busy signal.
- Correct: Desk Phone / Medium. Predicted: Desk Phone / High
- Model's reason: The main phone isn't ringing, and callers get a busy signal.
- Raise rule: customers_waiting, evidence: "callers get a busy signal", accepted: True

**INC-10146** (lowercase): Teams meeting won't load. i can't join teams meetings from my work pc, it just spins.
- Correct: Teams / Low. Predicted: Outlook / Medium
- Model's reason: Cannot join Teams meetings from one PC.

**INC-10151** (clean): Callers get busy signal. The main phone isn't ringing, callers get a busy signal.
- Correct: Desk Phone / Medium. Predicted: Desk Phone / High
- Model's reason: The main phone is not ringing and callers get a busy signal.
- Raise rule: customers_waiting, evidence: "callers get a busy signal", accepted: True

**INC-10204** (clean): Payment terminal declining everything. Every card is getting declined on register #1 this morning, even cards that work at the other registers.
- Correct: Card Reader / High. Predicted: Card Reader / Urgent
- Model's reason: All cards are being declined on one register, affecting multiple cards.
- Raise rule: customers_waiting, evidence: "Every card is getting declined on register #1 this morning, even cards that work at the other registers", accepted: True

**INC-10436** (clean): Teams won't sign in. Teams shows error 0x80070005 when I try to sign in.
- Correct: Teams / Low. Predicted: Outlook / Medium
- Model's reason: Error 0x80070005 in Teams is a sign-in issue.

**INC-10496** (clean): Account locked again. I keep getting locked out even after it gets unlocked. It happened again since we opened.
- Correct: Account Locked / Medium. Predicted: Account Locked / High
- Model's reason: The account keeps getting locked out, and the ticket mentions it happening again.
- Raise rule: several_people, evidence: "I keep getting locked out even after it gets unlocked. It happened again since we opened", accepted: True

**INC-11600** (vague_subject): IT problem. My keyboard stopped working right after lunch.
- Correct: Peripherals / Low. Predicted: Computer / Medium
- Model's reason: One keyboard stopped working; no mention of other devices or people.

**INC-11694** (typos): The front register is down. The front register froze this morning and won't respond. We retsarted it and it's stuck on the loading screen.
- Correct: Register Down / High. Predicted: Register Down / Urgent
- Model's reason: The front register is frozen and stuck on a loading screen.
- Raise rule: customers_waiting, evidence: "front register is down", accepted: True

**INC-11757** (lowercase): Not getting emails. i haven't received any emails after the update last night. people say they sent me stuff.
- Correct: Outlook / Medium. Predicted: Outlook / High
- Model's reason: No emails received after an update, and the ticket says people sent stuff to the requester.
- Raise rule: several_people, evidence: "people say they sent me stuff", accepted: True

**INC-11783** (lowercase): Teams sign-in error. teams shows a 'not responding' message when i try to sign in.
- Correct: Teams / Low. Predicted: Outlook / Medium
- Model's reason: Teams not responding during sign-in is a Teams issue.
