#!/usr/bin/env python3
"""
Synthetic help desk ticket generator.

Creates realistic but fake IT tickets for a multi-site retail nonprofit
(thrift stores, donation centers, offices). Each ticket is labeled with
category, subcategory, priority, and the KB article that resolves it.

No real organizational data is used anywhere in this file.

Usage:
    python generate_tickets.py                          # 3,000 tickets, seed 42
    python generate_tickets.py --count 5000 --seed 7 --eval-size 300
    python generate_tickets.py --test-set fresh --seed 2026 --count 200   # extra unseen test file
"""

import argparse
import csv
import json
import random
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

PRIORITIES = ["Low", "Medium", "High", "Urgent"]

LOCATIONS = (
    [f"Store {n:03d}" for n in range(1, 31)]
    + [f"Donation Center {c}" for c in "ABCDEF"]
    + ["Admin Office", "Training Center", "Warehouse"]
)

ROLES_BY_SITE = {
    "Store": ["Cashier", "Retail Associate", "Assistant Manager", "Store Manager"],
    "Donation Center": ["Donation Attendant", "Processor", "Center Lead"],
    "Admin Office": ["Accountant", "HR Generalist", "Program Coordinator", "Director"],
    "Training Center": ["Instructor", "Career Coach", "Program Coordinator"],
    "Warehouse": ["Warehouse Associate", "Logistics Lead", "Driver"],
}

FIRST_NAMES = [
    "Maria", "James", "Aisha", "Carlos", "Linda", "Tyrone", "Mei", "Robert",
    "Fatima", "Kevin", "Rosa", "Daniel", "Priya", "Marcus", "Ana", "Brian",
    "Yolanda", "Luis", "Grace", "Andre", "Sofia", "Michael", "Keisha", "Tom",
    "Elena", "Jamal", "Hannah", "Miguel", "Denise", "Omar",
]
LAST_NAMES = [
    "Garcia", "Johnson", "Nguyen", "Smith", "Rodriguez", "Williams", "Patel",
    "Brown", "Martinez", "Davis", "Lopez", "Wilson", "Kim", "Anderson",
    "Hernandez", "Thomas", "Jackson", "Perez", "White", "Rivera", "Harris",
    "Clark", "Lewis", "Torres", "Walker", "Ramirez", "Young", "Allen", "Scott",
    "Green",
]

# Values substituted into {placeholders} in subjects and bodies.
SLOTS = {
    "register": ["register 2", "register #1", "the front register", "lane 3", "register 4"],
    "when": [
        "this morning", "since yesterday", "about an hour ago",
        "after the update last night", "since we opened",
        "on and off all week", "right after lunch",
    ],
    "app": ["Excel", "Adobe Acrobat", "Chrome", "the timekeeping app", "Zoom", "the scheduling app"],
    "device": ["laptop", "desktop", "work PC", "computer"],
    "printer": [
        "the back office printer", "the label printer",
        "the copier by the break room", "the printer in the manager's office",
    ],
    "error": [
        "error 0x80070005", "a 'Not Responding' message", "a blank white screen",
        "'license expired'", "'something went wrong, try again later'",
    ],
    "peripheral": ["mouse", "keyboard", "second monitor", "headset", "docking station"],
    "share": ["Finance", "HR Forms", "Store Reports", "Donations Tracking", "Marketing"],
    "newhire": ["our new cashier", "a new assistant manager", "the new processor", "our new hire"],
    "mailbox": [
        "the store manager mailbox", "the donations inbox",
        "the HR shared mailbox", "the scheduling inbox",
    ],
}

ESC_GENERIC = [
    "Several of us are having the same problem.",
    "This is happening to everyone in the office.",
    "I can't do any work until this is fixed.",
]
ESC_POS = [
    "We have a line of customers waiting.",
    "This is affecting all the registers.",
    "We can only use one register right now.",
]

VAGUE_SUBJECTS = ["Help", "Not working", "Issue", "urgent!!", "IT problem", "Question", "Please call me"]

# category -> subcategory -> spec
CATALOG = {
    "Access & Accounts": {
        "Password Reset": {
            "weight": 14, "priority": "Medium", "kb": "KB-101",
            "kb_title": "Resetting a forgotten or expired password",
            "kb_summary": "Verify identity by callback to the number on file or manager confirmation, then reset and require a change at next sign-in.",
            "variants": [  # (possible subjects, matching description)
                (["Forgot my password", "Can't remember my Windows password"], "I forgot my password and can't log into my {device}. I tried {when} and it keeps saying the password is incorrect."),
                (["Password expired", "Password reset needed"], "My password expired {when} and now I can't sign in to anything. Can someone reset it?"),
                (["Password reset needed", "New password not working"], "Need a password reset please. I changed it last week and now it doesn't work."),
            ],
        },
        "Account Locked": {
            "weight": 7, "priority": "Medium", "kb": "KB-102",
            "kb_title": "Unlocking a locked-out account",
            "kb_summary": "Confirm identity, unlock the account, and check for old saved passwords on phones or mapped drives that keep re-locking it.",
            "variants": [  # (possible subjects, matching description)
                (["Account locked out", "Locked out of my computer"], "My account got locked {when} after I typed my password wrong a few times."),
                (["Says my account is locked", "Account locked"], "It says my account has been locked and to contact the administrator."),
                (["Keep getting locked out", "Account locked again"], "I keep getting locked out even after it gets unlocked. It happened again {when}."),
            ],
        },
        "Access Request": {
            "weight": 6, "priority": "Low", "kb": "KB-103",
            "kb_title": "Requesting access to a system or shared folder",
            "kb_summary": "Access needs manager approval; submit the Access Request catalog item with the system name and business reason.",
            "variants": [  # (possible subjects, matching description)
                (["Need access to shared drive", "Access to {share} folder"], "I need access to the {share} folder on the shared drive for my new role."),
                (["Access request for new hire", "New hire setup"], "{newhire} starts Monday and needs access to email and {app}."),
                (["Can't open the {share} folder", "Access denied on shared drive"], "When I try to open the {share} folder it says access denied. My manager said I should have it."),
            ],
        },
    },
    "Point of Sale": {
        "Register Down": {
            "weight": 8, "priority": "High", "kb": "KB-201", "sites": ["Store"],
            "kb_title": "Register won't boot or freezes",
            "kb_summary": "Power cycle the register and cash drawer, check the network cable, then escalate to the POS team if it won't reach the sign-in screen.",
            "variants": [  # (possible subjects, matching description)
                (["Register frozen", "{register} is down"], "{register} froze {when} and won't respond. We restarted it and it's stuck on the loading screen."),
                (["Register keeps restarting", "POS not working"], "The POS on {register} keeps restarting by itself in the middle of transactions."),
                (["Can't sign in to register", "POS error"], "{register} shows {error} when we try to sign in."),
            ],
            "escalators": ESC_POS,
        },
        "Card Reader": {
            "weight": 6, "priority": "High", "kb": "KB-202", "sites": ["Store"],
            "kb_title": "Card reader not accepting payments",
            "kb_summary": "Reseat the reader cable, restart the payment app, and run a test transaction; switch to the backup reader if it still fails.",
            "variants": [  # (possible subjects, matching description)
                (["Card reader not working", "Chip cards not reading"], "The card reader on {register} isn't reading chip cards. Tap works sometimes."),
                (["Payment terminal declining everything", "Cards getting declined"], "Every card is getting declined on {register} {when}, even cards that work at the other registers."),
                (["Can't take card payments", "Card reader not connected"], "The payment terminal on {register} says 'device not connected'."),
            ],
            "escalators": ESC_POS,
        },
        "Receipt Printer": {
            "weight": 4, "priority": "Medium", "kb": "KB-203", "sites": ["Store"],
            "kb_title": "Receipt printer not printing",
            "kb_summary": "Check paper roll orientation, clear jams, power cycle, and confirm the printer shows as connected in POS settings.",
            "variants": [  # (possible subjects, matching description)
                (["Receipt printer not printing", "No receipts coming out"], "The receipt printer on {register} stopped printing {when}. Paper is loaded."),
                (["Blank receipts", "Receipt printer problem"], "Receipts are coming out blank on {register}."),
                (["Receipt printer jammed", "Receipt printer beeping"], "The receipt printer keeps jamming and beeping."),
            ],
            "escalators": ESC_POS,
        },
    },
    "Email & Collaboration": {
        "Outlook": {
            "weight": 9, "priority": "Medium", "kb": "KB-301",
            "kb_title": "Outlook won't open or sync",
            "kb_summary": "Restart Outlook, check connection status, and repair the Office profile if mail still doesn't sync.",
            "variants": [  # (possible subjects, matching description)
                (["Outlook not opening", "Outlook won't start"], "Outlook won't open on my {device}. It just shows {error}."),
                (["Not getting emails", "Missing emails"], "I haven't received any emails {when}. People say they sent me stuff."),
                (["Outlook keeps asking for password", "Outlook password prompt"], "Outlook keeps popping up asking for my password over and over."),
            ],
            "escalators": ESC_GENERIC,
        },
        "Teams": {
            "weight": 5, "priority": "Low", "kb": "KB-302",
            "kb_title": "Teams audio, video, or sign-in problems",
            "kb_summary": "Check device settings in Teams, clear the Teams cache, and sign out and back in.",
            "variants": [  # (possible subjects, matching description)
                (["Teams no audio", "People can't hear me on Teams"], "Nobody can hear me on Teams calls. My headset works in other apps."),
                (["Can't join Teams meeting", "Teams meeting won't load"], "I can't join Teams meetings from my {device}, it just spins."),
                (["Teams won't sign in", "Teams sign-in error"], "Teams shows {error} when I try to sign in."),
            ],
        },
        "Shared Mailbox": {
            "weight": 3, "priority": "Low", "kb": "KB-303",
            "kb_title": "Getting access to a shared mailbox",
            "kb_summary": "Shared mailbox access needs owner approval; once granted it appears in Outlook automatically within a few hours.",
            "variants": [  # (possible subjects, matching description)
                (["Need access to shared mailbox", "Shared mailbox access"], "I need access to {mailbox} for my new role."),
                (["Shared inbox missing", "Shared mailbox disappeared"], "{mailbox} disappeared from my Outlook {when}."),
                (["Can't send from shared mailbox", "Shared mailbox send error"], "I can see {mailbox} but when I try to send from it I get {error}."),
            ],
        },
    },
    "Hardware": {
        "Printer/Scanner": {
            "weight": 8, "priority": "Medium", "kb": "KB-401",
            "kb_title": "Office printer or scanner problems",
            "kb_summary": "Check for jams and toner, restart the printer, and re-add it on the computer if jobs are stuck in the queue; for scan to email, check the address and the copier's email settings.",
            "variants": [  # (possible subjects, matching description)
                (["Printer not working", "Can't print"], "{printer} isn't printing anything, jobs just sit in the queue."),
                (["Printer paper jam", "Printer says jammed"], "{printer} says paper jam but there's nothing in there."),
                (["Scanner won't send to email", "Scan to email not working"], "Scan to email stopped working on {printer} {when}."),
            ],
            "escalators": ESC_GENERIC,
        },
        "Computer": {
            "weight": 7, "priority": "Medium", "kb": "KB-402",
            "kb_title": "Slow or unresponsive computer",
            "kb_summary": "Restart, check free disk space and pending updates, and run the hardware diagnostic if the problem continues.",
            "variants": [  # (possible subjects, matching description)
                (["Computer very slow", "{device} running slow"], "My {device} has been really slow {when}, takes forever to open anything."),
                (["{device} won't turn on", "Computer not powering on"], "My {device} won't power on. The light blinks but nothing happens."),
                (["Blue screen", "Computer keeps restarting"], "I keep getting a blue screen on my {device}, it restarts on its own."),
            ],
        },
        "Peripherals": {
            "weight": 4, "priority": "Low", "kb": "KB-403",
            "kb_title": "Mouse, keyboard, monitor, or dock issues",
            "kb_summary": "Try a different port, reseat the dock, and swap with a known-good device; request a replacement through the Hardware catalog item.",
            "variants": [  # (possible subjects, matching description)
                (["{peripheral} not working", "{peripheral} stopped working"], "My {peripheral} stopped working {when}."),
                (["Need a new {peripheral}", "Replacement {peripheral}"], "My {peripheral} is broken, can I get a replacement?"),
                (["Monitor not detected", "Second screen not working"], "My second monitor isn't detected when I plug into the docking station."),
            ],
        },
    },
    "Network": {
        "Wi-Fi": {
            "weight": 5, "priority": "Medium", "kb": "KB-501",
            "kb_title": "Wi-Fi connection problems",
            "kb_summary": "Forget and rejoin the network, confirm the correct SSID, and check whether other devices at the site are affected.",
            "variants": [  # (possible subjects, matching description)
                (["Can't connect to wifi", "Wi-Fi not working"], "My {device} won't connect to the Wi-Fi {when}."),
                (["Wifi keeps dropping", "Wi-Fi disconnecting"], "The Wi-Fi keeps dropping every few minutes."),
                (["Scanners losing Wi-Fi", "Wi-Fi in back room"], "The handheld scanners keep losing Wi-Fi in the back room."),
            ],
            "escalators": ESC_GENERIC,
        },
        "Internet Outage": {
            "weight": 3, "priority": "Urgent", "kb": "KB-502",
            "kb_title": "Site-wide internet outage",
            "kb_summary": "Check modem and firewall lights, power cycle in order (modem, firewall, switch), and contact the ISP if the circuit is down.",
            "variants": [  # (possible subjects, matching description)
                (["Internet down", "No internet here"], "The internet is down for everyone here {when}. Nothing will load."),
                (["Whole site offline", "No internet or phones"], "We have no internet at all, even the phones are down."),
                (["Nothing can connect", "Modem lights orange"], "None of the computers can connect. The modem lights are orange."),
            ],
        },
        "VPN": {
            "weight": 3, "priority": "Medium", "kb": "KB-503",
            "kb_title": "VPN won't connect",
            "kb_summary": "Confirm home internet works, update the VPN client, re-enter credentials, and approve the MFA prompt on your phone.",
            "variants": [  # (possible subjects, matching description)
                (["VPN not connecting", "Can't connect from home"], "I can't connect to the VPN from home {when}. It shows {error}."),
                (["VPN connected but no access", "Can't reach shared drive on VPN"], "The VPN connects but I can't get to the shared drive."),
                (["VPN keeps disconnecting", "VPN dropping"], "The VPN disconnects every 10 minutes."),
            ],
        },
    },
    "Software": {
        "Install Request": {
            "weight": 5, "priority": "Low", "kb": "KB-601",
            "kb_title": "Requesting new software",
            "kb_summary": "Submit the Software Request catalog item; licensed software needs manager approval before install.",
            "variants": [  # (possible subjects, matching description)
                (["Software install request", "Need {app} installed"], "Can you install {app} on my {device}? I need it for reports."),
                (["Can I get {app}?", "{app} for training"], "I need {app} for a training next week."),
                (["Need {app} installed", "New {device} missing {app}"], "My new {device} doesn't have {app} and I need it."),
            ],
        },
        "Application Error": {
            "weight": 6, "priority": "Medium", "kb": "KB-602",
            "kb_title": "Application crashing or showing errors",
            "kb_summary": "Reopen the app, install pending updates, and repair or reinstall if it still crashes; include the exact error text.",
            "variants": [  # (possible subjects, matching description)
                (["{app} crashing", "{app} keeps closing"], "{app} keeps crashing {when}."),
                (["Error in {app}", "{app} not working"], "When I open {app} I get {error}."),
                (["{app} freezing", "{app} not working"], "{app} freezes every time I try to save."),
            ],
            "escalators": ESC_GENERIC,
        },
    },
    "Phones": {
        "Desk Phone": {
            "weight": 3, "priority": "Medium", "kb": "KB-701",
            "kb_title": "Desk phone or voicemail problems",
            "kb_summary": "Check the network cable into the phone, unplug it for 10 seconds, and reset the voicemail PIN from the admin portal if needed.",
            "variants": [  # (possible subjects, matching description)
                (["No dial tone", "Phone not working"], "My desk phone has no dial tone {when}."),
                (["Phone not ringing", "Callers get busy signal"], "The main phone isn't ringing, callers get a busy signal."),
                (["Voicemail not working", "Forgot voicemail PIN"], "I forgot my voicemail PIN."),
            ],
            "escalators": ESC_GENERIC,
        },
    },
}


# Troubleshooting steps for each KB article, used to draft replies.
# user_steps: what the employee can try. it_steps: what IT does.
KB_DETAILS = {
    "KB-101": {"user_steps": ["If you think you may be mistyping it, check that Caps Lock is off",
                              "If you changed your password recently, sign in with the new one on a work computer "
                              "connected to the network so the change takes effect"],
               "it_steps": ["Verify identity by calling back the number on file or confirming with a manager",
                            "Reset a forgotten or expired password and require a change at next sign-in"]},
    "KB-102": {"user_steps": ["Wait 15 minutes before trying again",
                              "Sign out of email on your phone and other devices that may have an old password saved"],
               "it_steps": ["Confirm identity and unlock the account",
                            "Find the device that keeps sending the old password"]},
    "KB-103": {"user_steps": ["Ask your manager to approve the request",
                              "Include the folder or system name and why you need it"],
               "it_steps": ["Grant access after manager approval"]},
    "KB-201": {"user_steps": ["Restart the register and the cash drawer",
                              "Check that the network cable at the back of the register is firmly plugged in",
                              "Use another register in the meantime if one is available"],
               "it_steps": ["Escalate to the POS team if it still won't reach the sign-in screen"]},
    "KB-202": {"user_steps": ["Unplug the card reader cable and plug it back in", "Restart the payment app",
                              "Run a test transaction", "Switch to the backup reader if it still fails"],
               "it_steps": ["Contact the payment processor if the backup reader also fails"]},
    "KB-203": {"user_steps": ["Check that the paper roll is loaded with the shiny side facing the print head",
                              "Open the cover and clear any jammed paper", "Turn the printer off and on"],
               "it_steps": ["Confirm the printer shows as connected in POS settings"]},
    "KB-301": {"user_steps": ["Close Outlook completely and open it again",
                              "Check the bottom bar of Outlook for 'Disconnected' or 'Working offline'",
                              "Restart your computer"],
               "it_steps": ["Repair the Office profile if mail still doesn't sync"]},
    "KB-302": {"user_steps": ["Check your microphone and speaker in Teams settings under Devices",
                              "Sign out of Teams and sign back in", "Restart Teams"],
               "it_steps": ["Clear the Teams cache remotely if the problem continues"]},
    "KB-303": {"user_steps": ["Ask the mailbox owner to approve access",
                              "After access is granted, restart Outlook; the mailbox can take a few hours to appear"],
               "it_steps": ["Grant access once the owner approves"]},
    "KB-401": {"user_steps": ["Printing: check the printer screen for jams or low toner",
                              "Printing: turn the printer off and on",
                              "Printing: cancel stuck jobs and print again",
                              "Scan to email: check that the email address is typed correctly",
                              "Scan to email: try scanning a single page to rule out a size limit"],
               "it_steps": ["Printing: re-add the printer on the computer if jobs stay stuck",
                            "Scan to email: check the copier's email settings, such as the mail server sign-in"]},
    "KB-402": {"user_steps": ["Restart the computer", "Save your work and close programs you aren't using",
                              "Let pending updates finish"],
               "it_steps": ["Check disk space and run hardware diagnostics if the problem continues"]},
    "KB-403": {"user_steps": ["Unplug the device and plug it into a different port",
                              "Reseat the docking station cable", "Try a device that is known to work"],
               "it_steps": ["Send a replacement through the Hardware catalog item"]},
    "KB-501": {"user_steps": ["Forget the Wi-Fi network and join it again",
                              "Make sure you are on the correct work network",
                              "Check whether other devices nearby have the same problem"],
               "it_steps": ["Check the access point if several devices are affected"]},
    "KB-502": {"user_steps": ["Check the lights on the modem and firewall",
                              "Restart the modem, then the firewall, then the switch, in that order"],
               "it_steps": ["Contact the internet provider if the connection is still down"]},
    "KB-503": {"user_steps": ["Make sure your home internet works first", "Update the VPN client",
                              "Sign in again and approve the MFA prompt on your phone"],
               "it_steps": ["Check the VPN account if it still fails"]},
    "KB-601": {"user_steps": ["Submit the Software Request form", "Ask your manager to approve it"],
               "it_steps": ["Install the software after approval"]},
    "KB-602": {"user_steps": ["Close the app and open it again", "Install any pending updates",
                              "Write down the exact error message"],
               "it_steps": ["Repair or reinstall the app if it keeps failing"]},
    "KB-701": {"user_steps": ["Check that the network cable is plugged into the phone",
                              "Unplug the phone for 10 seconds and plug it back in"],
               "it_steps": ["Reset the voicemail PIN from the admin portal if needed"]},
}


class Slots(dict):
    """Fills {placeholders} with random values, reusing a value within one ticket."""

    def __init__(self, rng):
        super().__init__()
        self.rng = rng

    def __missing__(self, key):
        self[key] = self.rng.choice(SLOTS[key])
        return self[key]


def cap(text):
    return text[:1].upper() + text[1:]


def site_type(location):
    for prefix in ("Store", "Donation Center"):
        if location.startswith(prefix):
            return prefix
    return location


def bump(priority):
    return PRIORITIES[min(PRIORITIES.index(priority) + 1, len(PRIORITIES) - 1)]


def add_typos(text, rng, rate=0.05):
    """Swap two adjacent letters in a few longer words."""
    words = text.split(" ")
    for i, w in enumerate(words):
        if len(w) > 4 and w.isalpha() and rng.random() < rate:
            j = rng.randrange(len(w) - 1)
            words[i] = w[:j] + w[j + 1] + w[j] + w[j + 2:]
    return " ".join(words)


def random_timestamp(rng, end, days=180):
    # Fewer tickets on weekends, most during business hours.
    while True:
        day = end - timedelta(days=rng.randrange(days))
        if rng.random() < [1.0, 0.9, 0.85, 0.85, 0.8, 0.55, 0.4][day.weekday()]:
            break
    hour = rng.choices(range(7, 21), weights=[3, 6, 9, 9, 8, 7, 7, 8, 7, 6, 4, 3, 2, 1])[0]
    return day.replace(hour=hour, minute=rng.randrange(60), second=rng.randrange(60))


def flatten_catalog():
    return [(cat, sub, spec) for cat, subs in CATALOG.items() for sub, spec in subs.items()]


def make_ticket(rng, flat, end):
    cat, sub, spec = rng.choices(flat, weights=[s["weight"] for _, _, s in flat])[0]

    allowed = spec.get("sites")
    location = rng.choice([l for l in LOCATIONS if not allowed or site_type(l) in allowed])
    role = rng.choice(ROLES_BY_SITE[site_type(location)])

    slots = Slots(rng)
    subjects, body = rng.choice(spec["variants"])
    subject = cap(rng.choice(subjects).format_map(slots))
    description = cap(body.format_map(slots))
    priority = spec["priority"]
    tags = []

    # Business impact raises priority.
    if spec.get("escalators") and rng.random() < 0.2:
        description += " " + rng.choice(spec["escalators"])
        priority = bump(priority)
        tags.append("escalated")

    # Unhelpful subject line; the model has to read the body.
    if rng.random() < 0.08:
        subject = rng.choice(VAGUE_SUBJECTS)
        tags.append("vague_subject")

    # A second, unrelated issue in the same ticket. Label stays with the first.
    if rng.random() < 0.05:
        _, _, other = rng.choice([f for f in flat if f[1] != sub])
        extra = rng.choice(other["variants"])[1].format_map(Slots(rng))
        description += " Also, " + extra[:1].lower() + extra[1:]
        tags.append("multi_issue")

    if rng.random() < 0.3:
        noisy = add_typos(description, rng)
        if noisy != description:
            description = noisy
            tags.append("typos")
    if rng.random() < 0.15:
        description = description.lower()
        tags.append("lowercase")

    return {
        "created_at": random_timestamp(rng, end),
        "requester": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
        "role": role,
        "location": location,
        "subject": subject,
        "description": description,
        "category": cat,
        "subcategory": sub,
        "priority": priority,
        "kb_article": spec["kb"],
        "tags": ";".join(tags),
    }


FIELDS = [
    "ticket_id", "created_at", "requester", "role", "location", "subject",
    "description", "category", "subcategory", "priority", "kb_article", "tags",
]


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--eval-size", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent)
    parser.add_argument("--test-set", metavar="NAME",
                        help="write all tickets to tickets_NAME.csv as a separate test file; "
                             "leaves the practice, evaluation, and KB files untouched")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    flat = flatten_catalog()
    end = datetime(2026, 9, 1)

    tickets = sorted((make_ticket(rng, flat, end) for _ in range(args.count)), key=lambda t: t["created_at"])
    first_id = 90001 if args.test_set else 10001  # separate ID range so files never collide
    for i, t in enumerate(tickets):
        t["ticket_id"] = f"INC-{first_id + i}"
        t["created_at"] = t["created_at"].isoformat(sep=" ")

    if args.test_set:
        path = args.out / f"tickets_{args.test_set}.csv"
        write_csv(path, tickets)
        print(f"Wrote {len(tickets)} test tickets to {path}")
        return

    # Hold out a labeled evaluation set the agent never sees during development.
    shuffled = tickets[:]
    rng.shuffle(shuffled)
    eval_ids = {t["ticket_id"] for t in shuffled[: args.eval_size]}
    train = [t for t in tickets if t["ticket_id"] not in eval_ids]
    evals = [t for t in tickets if t["ticket_id"] in eval_ids]

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "tickets_train.csv", train)
    write_csv(args.out / "tickets_eval.csv", evals)

    kb = [
        {"id": s["kb"], "category": c, "subcategory": sub, "default_priority": s["priority"],
         "title": s["kb_title"], "summary": s["kb_summary"], **KB_DETAILS[s["kb"]]}
        for c, sub, s in flat
    ]
    (args.out / "kb_articles.json").write_text(json.dumps(kb, indent=2), encoding="utf-8")

    print(f"Wrote {len(train)} train + {len(evals)} eval tickets and {len(kb)} KB articles to {args.out}\n")
    print("By category:")
    for k, v in Counter(t["category"] for t in tickets).most_common():
        print(f"  {k:<24}{v:>6}")
    print("By priority:")
    for p in PRIORITIES:
        print(f"  {p:<24}{sum(t['priority'] == p for t in tickets):>6}")
    print("Noise tags:")
    for k, v in Counter(tag for t in tickets for tag in t["tags"].split(";") if tag).most_common():
        print(f"  {k:<24}{v:>6}")


if __name__ == "__main__":
    main()
