# Agent evaluation: agent-qwen

Model `qwen2.5:7b`, embeddings `nomic-embed-text`, prompt `v4`, 30 evaluation tickets, run 2026-09-29 15:10.

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
| Grounded in the KB article (no invented fixes) | 80.0% |
| Addresses the ticket's problem | 100.0% |
| Tone suitable for an employee | 100.0% |
| Judge answers that were invalid | 0 |

The judge is an AI and can be wrong or lenient, especially when it is the same model that wrote the reply. Read the sample replies below to check its grading.

Average time per ticket (classify, search, and draft): 29.5s

## Replies with problems

**INC-12572**: Password reset needed. My passowrd expired right after lunch and now I can't sign in to anything. Can someone reset it?
- Issues: judge: Adds step 2 for the employee, which is not in the KB article.

```
Hi Linda,

Your password has expired, and we need to reset it for you.

1. Ensure Caps Lock is off and type your current password correctly.
2. Try your new password on a network-connected computer if you changed it recently.

For IT: We will verify your identity and reset your password, requiring a change at your next sign-in.

Thank you for your patience.

IT Help Desk
```

**INC-11559**: Password reset needed. My password expired this morning and now I can't sign in to anything. Can someone reset it?
- Issues: judge: Adds a step for the employee to try their new password on a network-connected computer, which is not in the KB article.

```
Hi Elena,

Your password has expired, and we need to reset it for you. Please make sure Caps Lock is off and try typing your current password. If you recently changed it, try the new password on a network-connected computer.

For IT, we will verify your identity and reset your password, requiring a change at your next sign-in.

Thank you for your patience.

IT Help Desk
```

**INC-12314**: VPN connected but no access. The VPN connects but I can't get to the shared drive.
- Issues: judge: Adds steps not in KB article and promises IT check.

```
Hi Maria,

The issue you're experiencing with the shared drive access after connecting to the VPN has been noted. Here are a few steps to try:

1. Ensure your home internet is working properly.
2. Update the VPN client on your device.
3. Sign in again and approve any MFA prompts on your phone.

For IT, we will check your VPN account to ensure everything is configured correctly.

Thank you for your patience. IT Help Desk
```

**INC-10489**: Internet down. The internet is down for everyone here about an hour ago. Nothing will load.
- Issues: judge: Adds timing promise 'IT is already working on it' not in KB.

```
Hi Ana,

The internet is down for everyone, and we understand this is urgent. IT is already working on it.

For the employee:
1. Check the lights on the modem and firewall.
2. Restart the modem, then the firewall, then the switch, in that order.

IT will contact the internet provider to resolve the issue.

Thank you for your patience.
IT Help Desk
```

**INC-11757**: Not getting emails. i haven't received any emails after the update last night. people say they sent me stuff.
- Issues: judge: Adds step to contact IT for profile repair, which is not in the KB article.

```
Hi Sofia,

I've noted you're not receiving emails. Here are a few steps to try:

1. Close Outlook completely and open it again.
2. Check the bottom bar for 'Disconnected' or 'Working offline'.
3. Restart your computer.

If issues persist, IT will repair your Office profile.

Thanks,
IT Help Desk
```

**INC-10375**: Forgot my password. I forgot my password and can't log into my computer. I tried on and off all week and it keeps saying the password is incorrect.
- Issues: judge: Adds step 2 which is not in the KB article.

```
Hi Linda,

I understand you're having trouble logging in. Here are a few steps to try:

1. Ensure Caps Lock is off.
2. Try your new password on a network-connected computer.

For IT, we will verify your identity and reset your password.

Thank you,
IT Help Desk
```

## Sample replies

**INC-11393** (Outlook, Medium, KB-301): Outlook won't start. Outlook won't open on my desktop. It just shows a blank white screen.

```
Hi Elena,

Outlook is showing a blank white screen. Here are some steps to try:

1. Close Outlook completely and open it again.
2. Check the bottom bar for 'Disconnected' or 'Working offline'.
3. Restart your computer.

For IT, we will repair your Office profile if mail still doesn't sync.

Thank you for your patience. IT Help Desk
```

**INC-10695** (Wi-Fi, Medium, KB-501): Please call me. My laptop won't connect to the Wi-Fi on and off all week.

```
Hi Priya,

Your laptop's Wi-Fi issue is noted. Here are some steps to try:
1. Forget the Wi-Fi network and join it again.
2. Ensure you are on the correct work network.
3. Check if other devices nearby have the same problem.

For IT, we will check the access point if multiple devices are affected.

IT Help Desk
```

**INC-11681** (Printer/Scanner, Medium, KB-401): Issue. The copier by the break room isn't printing anything, jobs just sit in the queue.

```
Hi Fatima,

The copier isn't printing anything, and jobs are just sitting in the queue. Please try the following:

1. Check the printer screen for any jams or low toner.
2. Turn the printer off and on.
3. Cancel any stuck jobs and print again.

For IT, we will re-add the printer on your computer if the issue persists.

Thank you for your cooperation.

IT Help Desk
```

**INC-10284** (Receipt Printer, Medium, KB-203): Receipt printer not printing. The receipt printer on lane 3 stopped printing since we opened. Paper is loaded.

```
Hi Jamal,

The receipt printer on lane 3 isn't printing. Here are some steps to try:

1. Ensure the paper roll is loaded with the shiny side facing the print head.
2. Open the cover and clear any jammed paper.
3. Turn the printer off and on.
4. IT will confirm the printer shows as connected in POS settings.

Thanks for your help with these steps. If the issue persists, please submit a separate ticket.

IT Help Desk
```

**INC-10405** (Password Reset, Medium, KB-101): Password reset needed. need a password reset please. i changed it last week and now it doesn't work.

```
Hi Keisha,

I've noted your request for a password reset. Please try the following:

1. Ensure Caps Lock is off and type your current password correctly.
2. Try logging in using your new password on a network-connected computer.

For IT, we will verify your identity and reset your password, requiring a change at your next sign-in.

Thank you,
IT Help Desk
```
