# Agent evaluation: agent-qwen-r2

Model `qwen2.5:7b`, embeddings `nomic-embed-text`, judge `qwen2.5:7b`. Classifier prompt `v4`, reply rules `r2`, judge `j2`. 30 evaluation tickets, run 2026-09-29 15:46.

## KB suggestions

| Metric | Result |
|---|---|
| Suggested article is correct | 100.0% |
| KB search alone: correct article ranked first | 100.0% |
| KB search alone: correct article in the top 3 | 100.0% |

The suggested article comes from the classifier's subcategory. The search works independently from the ticket text, so it acts as a second opinion.

## Needs-review flag

| Metric | Result |
|---|---|
| Tickets flagged for review | 0 of 30 |
| Classifier mistakes caught by the flag | 0 of 0 |
| Flagged although classification and reply were fine | 0 |

## Reply safety checks (rule-based)

| Metric | Result |
|---|---|
| Replies passing every check | 100.0% |

## AI judge grades

| Metric | Result |
|---|---|
| Grounded in the KB article, as graded by the judge | 53.3% |
| Judge's 'not grounded' flags confirmed by the code | 7 of 14 |
| Judge flags that look like false alarms (quoted text is in the KB) | 7 of 14 |
| Grounded, after removing likely false alarms | 76.7% |
| Steps fit the specific problem | 70.0% |
| Addresses the ticket's problem | 93.3% |
| Tone suitable for an employee | 93.3% |
| Judge answers that were invalid | 0 |

When the judge says a reply isn't grounded, it must quote the sentence. The code then checks that quote against the KB article, the same way the classifier's evidence is checked. The judge is still an AI and can be wrong, so read the replies below to verify it.

Average time per ticket (classify, search, and draft): 26.9s

## Replies with problems

**INC-10695**: Please call me. My laptop won't connect to the Wi-Fi on and off all week.
- Issues: quoted: "Ensure you are on the correct work network." (confirmed: quoted text not in the KB article)

```
Hi Priya,

Your laptop has been having Wi-Fi connection issues.

1. Forget the Wi-Fi network and join it again.
2. Ensure you are on the correct work network.

If that doesn't help, we'll check the access point.

IT Help Desk
```

**INC-12212**: Says my account is locked. It says my account has been olcked and to contact the administrator.
- Issues: judge: We'll also check the device that keeps sending the old password. | quoted: "We'll also check the device that keeps sending the old password." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Kevin,

Your account has been locked out.

1. Wait 15 minutes before trying again.
2. Sign out of email on your phone and other devices that may have an old password saved.

If that doesn't help, we'll confirm your identity and unlock the account. We'll also check the device that keeps sending the old password.

IT Help Desk
```

**INC-11559**: Password reset needed. My password expired this morning and now I can't sign in to anything. Can someone reset it?
- Issues: judge: steps don't fit this problem

```
Hi Elena,

We will verify your identity and reset your password. You will need to change it at your next sign-in.

IT Help Desk
```

**INC-12314**: VPN connected but no access. The VPN connects but I can't get to the shared drive.
- Issues: judge: Invented quotes and steps do not fit the specific problem. | quoted: "Update the VPN client and sign in again to approve the MFA prompt on your phone." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem | judge: doesn't address the problem

```
Hi Maria,

Make sure your home internet works first. Update the VPN client and sign in again to approve the MFA prompt on your phone.

If that doesn't help, we'll check the VPN account.

IT Help Desk
```

**INC-12076**: Can't connect to wifi. My work PC won't connect to the Wi-Fi since we opened.
- Issues: quoted: "Ensure you are on the correct work network." (confirmed: quoted text not in the KB article)

```
Hi Priya,

We're sorry to hear you're having trouble connecting to the Wi-Fi.

1. Forget the Wi-Fi network and join it again.
2. Ensure you are on the correct work network.

If that doesn't help, we'll check the access point.

IT Help Desk
```

**INC-10204**: Payment terminal declining everything. Every card is getting declined on register #1 this morning, even cards that work at the other registers.
- Issues: judge: invented_quote | quoted: "Please try the following steps:" (confirmed: quoted text not in the KB article)

```
Hi Tom,

Every card is getting declined on register #1. Please try the following steps:

1. Unplug the card reader cable and plug it back in.
2. Restart the payment app.
3. Run a test transaction.

If that doesn't help, we'll contact the payment processor.

IT Help Desk
```

**INC-10454**: Nothing can connect. none of the computers can connect. the modem lights are orange.
- Issues: judge: Contacting the internet provider if the connection remains down. | quoted: "Contacting the internet provider if the connection remains down." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Marcus,

Nothing can connect, and the modem lights are orange.

If the lights don't resolve, we'll restart the modem, then the firewall, then the switch, in that order.

Contacting the internet provider if the connection remains down.

IT Help Desk
```

**INC-11787**: New password not working. Need a password reset please. I changed it last week and now it doesn't work.
- Issues: judge: sign in with the new one on a work computer connected to the network so the change takes effect | quoted: "sign in with the new one on a work computer connected to the network so the change takes effect" (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Michael,

If you recently changed your password, try signing in on a work computer connected to the network. If that doesn't help, we'll verify your identity and reset your password.

IT Help Desk
```

**INC-12266**: POS not working. The POS on lane 3 keeps restarting by itself in the middle of transactions.
- Issues: judge: Adding an unrelated printer step and suggesting adding a printer when the issue is with the POS. | quoted: "If that doesn't help, we'll re-add the printer for you." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem | judge: doesn't address the problem

```
Hi Omar,

The POS on your lane keeps restarting during transactions.

If that doesn't help, we'll re-add the printer for you.

If it still won't boot, we'll escalate to the POS team.

IT Help Desk
```

**INC-11757**: Not getting emails. i haven't received any emails after the update last night. people say they sent me stuff.
- Issues: judge: The steps suggested do not fit the specific problem of not receiving emails, as the KB article suggests steps for Outlook not opening or syncing, not for email delivery issues. | quoted: "Try closing Outlook completely and opening it again." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem

```
Hi Sofia,

We're sorry to hear you're not receiving emails. Try closing Outlook completely and opening it again. If that doesn't help, restart your computer.

If mail still doesn't sync, we'll repair your Office profile.

IT Help Desk
```

## Sample replies

**INC-11393** (Outlook, Medium, KB-301): Outlook won't start. Outlook won't open on my desktop. It just shows a blank white screen.

```
Hi Elena,

Outlook is showing a blank white screen.

1. Close Outlook completely and open it again.
2. Check the bottom bar for 'Disconnected' or 'Working offline'.
3. Restart your computer.

If that doesn't help, we'll repair the Office profile.

IT Help Desk
```

**INC-11681** (Printer/Scanner, Medium, KB-401): Issue. The copier by the break room isn't printing anything, jobs just sit in the queue.

```
Hi Fatima,

Printing jobs are sitting in the queue. Try turning the printer off and on, and cancel any stuck jobs and print again.

If that doesn't help, we'll re-add the printer on the computer for you.

IT Help Desk
```

**INC-12572** (Password Reset, Medium, KB-101): Password reset needed. My passowrd expired right after lunch and now I can't sign in to anything. Can someone reset it?

```
Hi Linda,

We will verify your identity by calling back the number on file or confirming with a manager. Then, we will reset your password and require a change at your next sign-in.

IT Help Desk
```

**INC-10284** (Receipt Printer, Medium, KB-203): Receipt printer not printing. The receipt printer on lane 3 stopped printing since we opened. Paper is loaded.

```
Hi Jamal,

The receipt printer on lane 3 isn't printing. Please check that the paper roll is loaded with the shiny side facing the print head and turn the printer off and on.

If that doesn't help, we'll confirm the printer shows as connected in POS settings.

IT Help Desk
```

**INC-10405** (Password Reset, Medium, KB-101): Password reset needed. need a password reset please. i changed it last week and now it doesn't work.

```
Hi Keisha,

If you recently changed your password, try signing in on a work computer connected to the network.

If that doesn't help, we'll verify your identity and reset your password.

IT Help Desk
```
