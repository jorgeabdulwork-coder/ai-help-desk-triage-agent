# Evaluation report: baseline

Model: `llama3.2:3b`, prompt version `v2`, 200 held-out tickets, run 2026-09-29 10:46.

## Summary

| Metric | Result |
|---|---|
| Category accuracy | 97.0% |
| Subcategory accuracy | 95.0% |
| Priority accuracy | 85.0% |
| Fully correct (subcategory and priority) | 83.0% |
| Invalid answers | 0.0% |
| Priority set too high | 24 tickets |
| Priority set too low | 6 tickets |
| Average time per ticket | 6.1s |

Setting priority too low is the more costly mistake in a help desk, since an urgent issue waits in the queue.

## Accuracy by ticket difficulty

| Tickets with | Count | Subcategory | Priority |
|---|---|---|---|
| (clean) | 124 | 94.4% | 87.9% |
| escalated | 17 | 94.1% | 76.5% |
| lowercase | 30 | 100.0% | 86.7% |
| multi_issue | 10 | 90.0% | 70.0% |
| typos | 15 | 93.3% | 86.7% |
| vague_subject | 16 | 87.5% | 68.8% |

## Priority: correct (rows) vs. predicted (columns)

| | Low | Medium | High | Urgent | (invalid) |
|---|---|---|---|---|---|
| **Low** | 28 | 4 | 0 | 0 | 0 |
| **Medium** | 3 | 110 | 5 | 3 | 0 |
| **High** | 0 | 3 | 20 | 12 | 0 |
| **Urgent** | 0 | 0 | 0 | 12 | 0 |

## Most common subcategory mix-ups

| Correct | Predicted | Count |
|---|---|---|
| Peripherals | Computer | 2 |
| Desk Phone | Password Reset | 2 |
| VPN | Access Request | 2 |
| Printer/Scanner | Peripherals | 1 |
| Receipt Printer | Register Down | 1 |
| Outlook | Application Error | 1 |
| Printer/Scanner | Receipt Printer | 1 |

## Accuracy by subcategory

| Subcategory | Count | Subcategory | Priority |
|---|---|---|---|
| Access Request | 5 | 100.0% | 100.0% |
| Account Locked | 14 | 100.0% | 92.9% |
| Application Error | 9 | 100.0% | 88.9% |
| Card Reader | 11 | 100.0% | 63.6% |
| Computer | 24 | 100.0% | 100.0% |
| Desk Phone | 8 | 75.0% | 100.0% |
| Install Request | 7 | 100.0% | 85.7% |
| Internet Outage | 8 | 100.0% | 100.0% |
| Outlook | 13 | 92.3% | 76.9% |
| Password Reset | 32 | 100.0% | 100.0% |
| Peripherals | 3 | 33.3% | 33.3% |
| Printer/Scanner | 11 | 81.8% | 81.8% |
| Receipt Printer | 6 | 83.3% | 83.3% |
| Register Down | 15 | 100.0% | 53.3% |
| Shared Mailbox | 6 | 100.0% | 83.3% |
| Teams | 11 | 100.0% | 100.0% |
| VPN | 4 | 50.0% | 25.0% |
| Wi-Fi | 13 | 100.0% | 69.2% |

## Examples of misses (first 10 of 34)

**INC-10204** (clean): Payment terminal declining everything. Every card is getting declined on register #1 this morning, even cards that work at the other registers.
- Correct: Card Reader / High. Predicted: Card Reader / Urgent
- Model's reason: Declined card payments are Card Reader (default High); the problem is on a specific register, which raises it one level.

**INC-10388** (clean): VPN keeps disconnecting. The VPN disconnects every 10 minutes.
- Correct: VPN / Medium. Predicted: VPN / Urgent
- Model's reason: The VPN keeps disconnecting, which is an Internet Outage (default Urgent); the 10-minute interval raises it one level.

**INC-10516** (clean): Second screen not working. My second monitor isn't detected when I plug into the docking station.
- Correct: Peripherals / Low. Predicted: Computer / Medium
- Model's reason: One computer with a non-detecting second monitor is Computer (default Medium); no raise rule applies.

**INC-10539** (clean): Voicemail not working. I forgot my voicemail PIN.
- Correct: Desk Phone / Medium. Predicted: Password Reset / Medium
- Model's reason: Forgot PIN is Password Reset (default Medium); no lockout message is mentioned.

**INC-10542** (vague_subject): urgent!!. I keep getting locked out even after it gets unlocked. It happened again this morning.
- Correct: Account Locked / Medium. Predicted: Account Locked / High
- Model's reason: Repeated lockouts without a clear reason to raise the priority

**INC-10586** (clean): The front register is down. The front register froze since yesterday and won't respond. We restarted it and it's stuck on the loading screen.
- Correct: Register Down / High. Predicted: Register Down / Urgent
- Model's reason: The register itself is frozen, so Register Down (default High); the whole store being affected raises it one level to Urgent.

**INC-10896** (vague_subject): Please call me. The Wi-Fi keeps dropping every few minutes.
- Correct: Wi-Fi / Medium. Predicted: Wi-Fi / Urgent
- Model's reason: Spotty wireless is Wi-Fi (default Medium); the whole site being affected raises it one level to Urgent.

**INC-10935** (clean): Register #1 is down. Register #1 froze since yesterday and won't respond. We restarted it and it's stuck on the loading screen.
- Correct: Register Down / High. Predicted: Register Down / Urgent
- Model's reason: The register itself is frozen, so Register Down (default High); the whole store being affected raises it one level to Urgent.

**INC-10996** (escalated;typos): Adobe Acrobat not working. dAobe Acrobat freezes every time I try to save. Several of us are having the same problem.
- Correct: Application Error / High. Predicted: Application Error / Medium
- Model's reason: One app freezing is Application Error (default Medium); several people having the same problem raises it one level.

**INC-11034** (escalated): Wi-Fi in back room. The handheld scanners keep losing Wi-Fi in the back room. I can't do any work until this is fixed.
- Correct: Wi-Fi / High. Predicted: Wi-Fi / Urgent
- Model's reason: One device losing Wi-Fi is Wi-Fi (default Medium); the whole back room being affected raises it one level to Urgent.
