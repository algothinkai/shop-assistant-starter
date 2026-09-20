"""Small local HTML workbench. No JavaScript, model call or external fetch."""

from __future__ import annotations

import json
import secrets
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

from .business import ShopError, ShopService


STYLE = (Path(__file__).resolve().parent / "workbench.css").read_bytes()


def h(value: object) -> str:
    return escape(str(value), quote=True)


def _detail(value: object) -> str:
    return h(json.dumps(value, indent=2, ensure_ascii=False) if not isinstance(value, str) else value)


def render_page(shop: ShopService, ticket_id: str, csrf_token: str) -> str:
    facts = shop.case_facts(ticket_id)
    ticket = facts["ticket"]
    order = facts["order"]
    customer = facts["customer"]
    policy = facts["policy"]
    latest = shop.latest_result(ticket_id)
    events = [
        event
        for event in shop.events(ticket_id)
        if latest is not None and event["run_id"] == latest["run_id"]
    ]
    ledger = [item for item in shop.ledger() if item["order_id"] == ticket["order_id"]]
    ticket_links = "".join(
        f'<li><a href="/?ticket={quote(item["id"])}" '
        f'{"aria-current=\"page\"" if item["id"] == ticket_id else ""}>'
        f'<span class="ticket-id">{h(item["id"])}</span>'
        f'<strong>{h(item["subject"])}</strong>'
        f'<span class="ticket-topic">{h(item["topic"])}</span>'
        f'{"<span class=\"selected-label\">Selected</span>" if item["id"] == ticket_id else ""}'
        "</a></li>"
        for item in shop.list_tickets()
    )
    result_html = (
        f'<div class="status status-{h(latest["status"])}"><strong>{h(latest["status"].replace("_", " ").title())}</strong>'
        f'<span>{h(latest["run_id"])}</span></div>'
        f'<p>{h(latest["summary"])}</p><p class="recovery"><strong>Next step:</strong> {h(latest["recovery"])}</p>'
        if latest
        else '<div class="status status-unrun"><strong>Not run</strong><span>No result for this ticket yet</span></div>'
        '<p>Predict what the fixed preset will read or change, then run it and inspect the events.</p>'
    )
    event_items = "".join(
        f'<li class="event event-{h(event["kind"])}">'
        f'<div class="event-head"><strong>{h(event["kind"].replace("_", " ").title())}</strong>'
        f'<span>{h(event["operation"])}</span></div>'
        f'<p class="event-meta">{h(event["id"])} · {h(event["ticket_id"])} · '
        f'{h(event["run_id"])} · {h(event["at"])}</p>'
        f'<pre>{_detail(event["detail"])}</pre></li>'
        for event in events[-30:]
    )
    if not event_items:
        event_items = '<li class="empty-event">No function events for this ticket yet.</li>'
    order_text = (
        f'{h(order["id"])} · {h(order["status"])} · {h(order["shipping"])}'
        if order
        else 'No matching order in fixtures; the preset lookup will fail.'
    )
    receipt_text = h(order["receipt"]) if order else 'Unknown until the order is clarified'
    ledger_text = (
        ", ".join(f'{h(item["id"])} · USD {item["amount_cents"] / 100:.2f} · {h(item["policy_id"])}' for item in ledger)
        if ledger
        else 'No teaching refund entry for this order.'
    )
    identity = (
        'Verified (simulated local teaching state)'
        if shop.simulated_identity_verified(ticket["customer_id"])
        else 'Unverified (simulated local teaching state)'
    )
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shop Assistant · local workbench</title><link rel="stylesheet" href="/static/workbench.css"></head>
<body><a class="skip" href="#case-title">Skip to selected case</a>
<header class="site-head"><div class="wrap"><p class="eyebrow">ALGOTHINK · TRAINING PROJECT</p>
<h1>Shop Assistant workbench</h1><p class="lede">A fictional coffee-equipment support desk. Think through a ticket, run a fixed preset, then inspect what the local functions actually did.</p>
<div class="notice"><strong>Fixed demo; no model call.</strong> Identity is simulated. Refunds write only a local teaching ledger; no payment moves.</div></div></header>
<main class="wrap grid"><nav class="ticket-nav" aria-label="Training tickets"><h2>Choose a ticket</h2><p>Four fixed scenarios. Start with a prediction.</p><ul>{ticket_links}</ul></nav>
<div class="main-column"><section id="case" class="panel" aria-labelledby="case-title"><p class="eyebrow">SELECTED CASE · {h(ticket_id)}</p><h2 id="case-title" tabindex="-1">{h(ticket["subject"])}</h2>
<p class="customer-message">“{h(ticket["message"])}”</p><dl class="facts">
<div><dt>Customer</dt><dd>{h(customer["name"]) if customer else 'Unknown'} · {h(ticket["customer_id"])}</dd></div>
<div><dt>Identity</dt><dd>{h(identity)}</dd></div>
<div><dt>Order</dt><dd>{order_text}</dd></div>
<div><dt>Receipt source</dt><dd>{receipt_text} · fictional local text file</dd></div>
<div><dt>Policy version</dt><dd>{h(policy["id"])} · effective {h(policy["effective_on"])} · checked as of 2026-09-15</dd></div>
</dl><details><summary>Read policy text</summary><p>{h(policy["text"])}</p></details><details><summary>Reveal reference observation after predicting</summary><p><strong>Reference observation:</strong> {h(ticket["expected_observation"])}</p></details></section>
<section class="panel action-panel" aria-labelledby="action-title"><p class="eyebrow">PREDICT → RUN → INSPECT</p><h2 id="action-title">What will happen?</h2>
<p>Before running, name the function you expect to be called and one result or error you expect to see. The workbench does not score your prediction.</p>
<form method="post" action="/run"><input type="hidden" name="ticket_id" value="{h(ticket_id)}"><input type="hidden" name="csrf" value="{h(csrf_token)}">
<button type="submit">Run preset demo</button><span class="inline-note">Fixed demo; no model call</span></form></section>
<section id="result" class="panel" aria-labelledby="result-title"><p class="eyebrow">OVERALL DEMO OUTCOME</p><h2 id="result-title" tabindex="-1">Result for {h(ticket_id)}</h2>{result_html}</section>
<section class="panel" aria-labelledby="event-title"><p class="eyebrow">OBSERVED EVIDENCE</p><h2 id="event-title">Local function events</h2><p>Chronological calls, results and errors for the latest run of {h(ticket_id)}. Earlier runs remain in the local state file. A successful function call does not mean the whole case was resolved.</p><ol class="events">{event_items}</ol></section>
<section class="panel ledger" aria-labelledby="ledger-title"><p class="eyebrow">SIMULATED STATE</p><h2 id="ledger-title">Teaching refund ledger</h2><p>{ledger_text}</p></section></div></main>
<footer class="wrap footer">Stage 0 · Local-only fictional data · <a href="/healthz">Health</a> · Reset with <code>scripts/reset</code></footer></body></html>'''


def handler_for(shop: ShopService, csrf_token: str):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            route = urlsplit(self.path)
            if route.path == "/static/workbench.css":
                return self._send(200, STYLE, "text/css; charset=utf-8")
            if route.path == "/healthz":
                return self._send(200, b'{"status":"ok","mode":"fixed_preset_no_model"}', "application/json")
            if route.path != "/":
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            ticket_id = parse_qs(route.query).get("ticket", ["T-1001"])[0]
            try:
                html = render_page(shop, ticket_id, csrf_token).encode()
            except ShopError:
                return self._send(404, b"Training ticket not found", "text/plain; charset=utf-8")
            return self._send(200, html, "text/html; charset=utf-8")

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/run":
                return self._send(404, b"Not found", "text/plain; charset=utf-8")
            port = self.server.server_address[1]
            allowed_origins = {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}
            origin = self.headers.get("Origin")
            if origin and origin not in allowed_origins:
                return self._send(403, b"Origin denied", "text/plain; charset=utf-8")
            if self.headers.get("Content-Type", "").split(";")[0] != "application/x-www-form-urlencoded":
                return self._send(415, b"Form encoding required", "text/plain; charset=utf-8")
            try:
                size = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return self._send(400, b"Invalid length", "text/plain; charset=utf-8")
            if not 0 < size <= 4096:
                return self._send(413, b"Invalid form size", "text/plain; charset=utf-8")
            fields = parse_qs(self.rfile.read(size).decode("utf-8", errors="replace"))
            if not secrets.compare_digest(fields.get("csrf", [""])[0], csrf_token):
                return self._send(403, b"Form token denied", "text/plain; charset=utf-8")
            ticket_id = fields.get("ticket_id", [""])[0]
            try:
                shop.run_preset(ticket_id)
            except ShopError:
                return self._send(404, b"Training ticket not found", "text/plain; charset=utf-8")
            self.send_response(303)
            self.send_header("Location", f"/?ticket={quote(ticket_id)}#result-title")
            self.send_header("Content-Length", "0")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

    return Handler


def serve(shop: ShopService, port: int = 8765) -> None:
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_for(shop, token))
    print(f"Shop Assistant preset workbench: http://127.0.0.1:{server.server_address[1]}")
    print("Fixed demo; no model call. Stop with Ctrl-C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
