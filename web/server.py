#!/usr/bin/env python3
"""Local web demo for the triage agent.

    python web/server.py          then open http://localhost:8000

Listens only on this computer (127.0.0.1), so nobody else on the network can use it.
Uses Python's built-in web server, so nothing extra needs to be installed.
"""

import csv
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from triage.agent import TriageAgent  # noqa: E402
from triage.config import load_config  # noqa: E402
from triage.serialize import result_to_dict  # noqa: E402

WEB = Path(__file__).resolve().parent
STATIC = {"/": ("demo.html", "text/html"), "/style.css": ("style.css", "text/css"),
          "/render.js": ("render.js", "text/javascript")}
EXAMPLES = {"INC-10349": "Wi-Fi, several people", "INC-10118": "Card reader, customers waiting",
            "INC-10026": "Expired password", "INC-10091": "Two problems in one", "INC-10165": "Teams sign-in"}
FIELDS = ("subject", "description", "requester", "role", "location")

config = load_config()
agent = TriageAgent(config)


def load_examples():
    found = {}
    for path in sorted((ROOT / "data").glob("tickets_*.csv")):
        with open(path, newline="", encoding="utf-8") as f:
            for t in csv.DictReader(f):
                if t["ticket_id"] in EXAMPLES:
                    found[t["ticket_id"]] = {"label": EXAMPLES[t["ticket_id"]], **{k: t[k] for k in FIELDS}}
    examples = [found[i] for i in EXAMPLES if i in found]
    examples.append({"label": "Scan to email", "subject": "Scanner broken",
                     "description": "Scan to email stopped working on the copier.",
                     "requester": "Sam Rivera", "role": "Retail Associate", "location": "Store 001"})
    return examples


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in STATIC:
            name, kind = STATIC[self.path]
            self._send(200, (WEB / name).read_bytes(), kind)
        elif self.path == "/api/examples":
            self._send(200, load_examples())
        else:
            self._send(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/triage":
            return self._send(404, {"error": "Not found"})
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 20_000)
            body = json.loads(self.rfile.read(length) or b"{}")
            ticket = {k: str(body.get(k, "")).strip()[:2000] for k in FIELDS}
        except (ValueError, json.JSONDecodeError):
            return self._send(400, {"error": "The request wasn't valid JSON."})
        if not ticket["subject"] or not ticket["description"]:
            return self._send(400, {"error": "Add a subject and a description."})
        ticket["ticket_id"] = "DEMO"
        try:
            result = agent.run(ticket)
        except Exception as exc:
            msg = str(exc)
            if "Connection" in type(exc).__name__:
                msg = f"Can't reach Ollama at {config.base_url}. Open the Ollama app and try again."
            elif "not found" in msg.lower():
                msg = f"A model isn't downloaded. Run: ollama pull {config.model} (and {config.embed_model})"
            return self._send(502, {"error": msg})
        self._send(200, result_to_dict(ticket, result, config))

    def log_message(self, fmt, *args):  # quieter console
        if self.command == "POST":
            sys.stderr.write(f"{self.command} {self.path} {args[1] if len(args) > 1 else ''}\n")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Demo running at http://localhost:{port}   (Ctrl+C to stop)")
    print(f"Classifier: {config.model}   Replies: {config.reply_model or config.model}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
