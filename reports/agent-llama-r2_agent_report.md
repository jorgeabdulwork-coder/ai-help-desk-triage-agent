# Agent evaluation: agent-llama-r2

Model `llama3.2:3b`, embeddings `nomic-embed-text`, judge `qwen2.5:7b`. Classifier prompt `v4`, reply rules `r2`, judge `j2`. 60 evaluation tickets, run 2026-10-01 08:56.

## KB suggestions

| Metric | Result |
|---|---|
| Suggested article is correct | 95.0% |
| KB search alone: correct article ranked first | 95.0% |
| KB search alone: correct article in the top 3 | 96.7% |

The suggested article comes from the classifier's subcategory. The search works independently from the ticket text, so it acts as a second opinion.

## Needs-review flag

| Metric | Result |
|---|---|
| Tickets flagged for review | 6 of 60 |
| Classifier mistakes caught by the flag | 3 of 3 |
| Flagged although classification and reply were fine | 3 |

## Reply safety checks (rule-based)

| Metric | Result |
|---|---|
| Replies passing every check | 100.0% |

## AI judge grades

| Metric | Result |
|---|---|
| Grounded in the KB article, as graded by the judge | 26.7% |
| Judge's 'not grounded' flags confirmed by the code | 28 of 44 |
| Judge flags that look like false alarms (quoted text is in the KB) | 16 of 44 |
| Grounded, after removing likely false alarms | 53.3% |
| Steps fit the specific problem | 50.0% |
| Addresses the ticket's problem | 95.0% |
| Tone suitable for an employee | 91.7% |
| Judge answers that were invalid | 0 |

When the judge says a reply isn't grounded, it must quote the sentence. The code then checks that quote against the KB article, the same way the classifier's evidence is checked. The judge is still an AI and can be wrong, so read the replies below to verify it.

Average time per ticket (classify, search, and draft): 16.2s

## Replies with problems

**INC-11393**: Outlook won't start. Outlook won't open on my desktop. It just shows a blank white screen.
- Issues: judge: invented_quote | quoted: "If that doesn't help, we'll re-add the printer for you." (confirmed: quoted text not in the KB article)

```
Hi Elena,



I've received your request for assistance with Outlook not starting on your desktop. The issue you're experiencing, where Outlook shows a blank white screen, is likely due to a corrupted Office profile.



We will try to repair the Office profile to see if that resolves the issue. If that doesn't help, we'll re-add the printer for you.



IT Help Desk
```

**INC-10695**: Please call me. My laptop won't connect to the Wi-Fi on and off all week.
- Issues: judge: Invented quote | quoted: "If that doesn't help, we'll re-add the printer for you." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem

```
Hi Priya,

Your laptop's Wi-Fi connection is intermittent and not connecting at all.

We will try to resolve the issue by checking the access point if several devices are affected.

1. Forget the Wi-Fi network and join it again.
2. Make sure you are on the correct work network.

If that doesn't help, we'll re-add the printer for you.

IT Help Desk
```

**INC-12572**: Password reset needed. My passowrd expired right after lunch and now I can't sign in to anything. Can someone reset it?
- Issues: judge: invented_quote | quoted: "Since you recently changed your password, I recommend trying to sign in with the new password on a work computer connected to the network to update the change." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem

```
Hi Linda,



I've acknowledged your password reset request. Since you recently changed your password, I recommend trying to sign in with the new password on a work computer connected to the network to update the change.



If that doesn't help, we'll verify your identity by calling back the number on file or confirming with a manager.



IT Help Desk
```

**INC-10405**: Password reset needed. need a password reset please. i changed it last week and now it doesn't work.
- Issues: judge: invented steps | quoted: "1. Check that Caps Lock is off.
2. Sign in with the new password on a work computer connected to the network so the change takes effect." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Keisha,

We'll verify your identity by calling back the number on file and then reset your password and require a change at next sign-in.

1. Check that Caps Lock is off.
2. Sign in with the new password on a work computer connected to the network so the change takes effect.

IT Help Desk
```

**INC-10496**: Account locked again. I keep getting locked out even after it gets unlocked. It happened again since we opened.
- Issues: judge: Invented quote | quoted: "If that doesn't help, we'll re-add the password for you." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem

```
Hi Robert,

I've received your request for assistance with your account being locked out. It seems that you're experiencing recurring issues with your account being locked out, even after it gets unlocked.

To help resolve this issue, I'll follow the steps outlined in KB-102. Here's what we'll do:

1. Wait 15 minutes before trying again.
2. Sign out of email on your phone and other devices that may have an old password saved.

If that doesn't help, we'll re-add the password for you.

IT Help Desk
```

**INC-11559**: Password reset needed. My password expired this morning and now I can't sign in to anything. Can someone reset it?
- Issues: judge: invented_quote | quoted: "To resolve the issue, please try checking that Caps Lock is off and signing in with your new password on a work computer connected to the network." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Elena, 

I've acknowledged your password reset request. To resolve the issue, please try checking that Caps Lock is off and signing in with your new password on a work computer connected to the network. If that doesn't help, we'll verify your identity and reset your password.

1. Check that Caps Lock is off.
2. Sign in with your new password on a work computer connected to the network.

IT Help Desk
```

**INC-12314**: VPN connected but no access. The VPN connects but I can't get to the shared drive.
- Issues: judge: Adding a printer when the issue is with a shared drive. | quoted: "If that doesn't help, we'll re-add the printer for you." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem | judge: doesn't address the problem

```
Hi Maria,

I've received your request for assistance with the VPN connection not allowing access to the shared drive. It seems that the VPN is connecting, but you're experiencing issues accessing the shared drive.

We'll check the VPN account to see if it's the cause of the problem.

If that doesn't help, we'll re-add the printer for you.

IT Help Desk
```

**INC-12076**: Can't connect to wifi. My work PC won't connect to the Wi-Fi since we opened.
- Issues: judge: invented_quote | quoted: "Your work PC is unable to connect to the Wi-Fi since we opened, which is causing an Urgent internet outage." (confirmed: quoted text not in the KB article)

```
Hi Priya,

Your work PC is unable to connect to the Wi-Fi since we opened, which is causing an Urgent internet outage.

We will try the steps from KB-502: Site-wide internet outage. We will check the lights on the modem and firewall, restart the modem, then the firewall, then the switch, in that order.

If that doesn't help, we'll contact the internet provider to investigate the issue.

IT Help Desk
```

**INC-11026**: The timekeeping app not working. When I open the timekeeping app I get 'something went wrong, try again later'.
- Issues: judge: invented_quote | quoted: "To resolve this issue, you can try submitting the Software Request form and asking your manager to approve it." (likely false alarm: quoted text is in the KB article) | judge: steps don't fit this problem

```
Hi Brian,

The timekeeping app is not working due to an error message.

To resolve this issue, you can try submitting the Software Request form and asking your manager to approve it. We will install the software after approval.

IT Help Desk
```

**INC-10454**: Nothing can connect. none of the computers can connect. the modem lights are orange.
- Issues: judge: invented_quote | quoted: "We will try restarting the modem, then the firewall, then the switch, in that order, to see if that resolves the issue." (confirmed: quoted text not in the KB article) | judge: steps don't fit this problem

```
Hi Marcus,

The modem lights are orange, indicating a connection issue.

We will try restarting the modem, then the firewall, then the switch, in that order, to see if that resolves the issue.

If that doesn't help, we'll contact the internet provider to investigate the cause of the outage.

IT Help Desk
```

## Sample replies

**INC-11681** (Printer/Scanner, Medium, KB-401): Issue. The copier by the break room isn't printing anything, jobs just sit in the queue.

```
Hi Fatima, 

The copier by the break room isn't printing anything, jobs just sit in the queue.

We will try printing: turn the printer off and on, and printing: cancel stuck jobs and print again. If that doesn't help, we'll re-add the printer on the computer if jobs stay stuck.

IT Help Desk
```

**INC-10284** (Receipt Printer, Medium, KB-203): Receipt printer not printing. The receipt printer on lane 3 stopped printing since we opened. Paper is loaded.

```
Hi Jamal,



The receipt printer on lane 3 is not printing due to the paper being loaded incorrectly.



We will check that the printer shows as connected in POS settings.



We will confirm the printer settings in POS settings.



IT Help Desk
```

**INC-12212** (Account Locked, Medium, KB-102): Says my account is locked. It says my account has been olcked and to contact the administrator.

```
Hi Kevin,

Your account has been locked due to an incorrect password attempt.

We will follow the steps from KB-102 to resolve the issue. We will confirm your identity and unlock the account. We will also investigate the device that keeps sending the old password.

IT Help Desk
```

**INC-10369** (Register Down, High, KB-201): POS error. register 2 shows a blank white screen when we try to sign in.

```
Hi Miguel,

The register is showing a blank white screen when trying to sign in, which is a critical issue for your store.

We will try to restart the register and the cash drawer, check that the network cable is firmly plugged in, and use another register if one is available.

If that doesn't help, we'll escalate to the POS team.

IT Help Desk
```

**INC-10204** (Card Reader, High, KB-202): Payment terminal declining everything. Every card is getting declined on register #1 this morning, even cards that work at the other registers.

```
Hi Tom,

The payment terminal on register #1 is declining every card transaction, even those that work on other registers.

We will try unplugging the card reader cable and plugging it back in, restarting the payment app, and running a test transaction to see if that resolves the issue.

If those steps don't help, we'll contact the payment processor if the backup reader also fails.

IT Help Desk
```
