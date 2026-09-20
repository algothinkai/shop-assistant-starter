"""Directly callable fictional shop functions and truthful local event history."""

from __future__ import annotations

import json
import os
import tempfile
import fcntl
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from datetime import date, datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any, Callable, Iterator, TypeVar


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
T = TypeVar("T")


class ShopError(Exception):
    """A structured training error; retryable means another call could help."""

    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable

    def as_dict(self) -> dict[str, object]:
        return {"code": self.code, "message": self.message, "retryable": self.retryable}


def _initial_state() -> dict[str, Any]:
    return {
        "verified_customers": [],
        "refund_ledger": [],
        "escalations": [],
        "events": [],
        "results": {},
        "next_run": 1,
        "next_event": 1,
    }


class ShopService:
    """One local teaching store; it never calls a network or payment service."""

    def __init__(self, state_dir: Path | None = None):
        self.catalog = {
            name: {item["id"]: item for item in json.loads((FIXTURES / f"{name}.json").read_text())}
            for name in ("products", "customers", "orders", "policies", "tickets")
        }
        self.state_dir = state_dir or ROOT / ".local"
        self.state_path = self.state_dir / "state.json"
        self._lock = RLock()
        self._context: ContextVar[tuple[str | None, str | None]] = ContextVar(
            "shop_event_context", default=(None, None)
        )
        self._state = _initial_state()

    def _read_state(self) -> dict[str, Any]:
        if not self.state_path.exists():
            return _initial_state()
        try:
            return json.loads(self.state_path.read_text())
        except (json.JSONDecodeError, OSError) as error:
            raise ShopError("STATE_INVALID", "Local state cannot be read. Stop the server and run scripts/reset.") from error

    def _save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix="state-", suffix=".json", dir=self.state_dir)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(self._state, stream, indent=2)
                stream.write("\n")
            os.replace(temporary, self.state_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @contextmanager
    def _state_guard(self, *, persist: bool = False, reload: bool = True) -> Iterator[None]:
        """Reload under a cross-process lock before any state read or write."""
        with self._lock:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            with (self.state_dir / "state.lock").open("a+") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                try:
                    if reload:
                        self._state = self._read_state()
                    yield
                    if persist:
                        self._save()
                finally:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

    def reset(self) -> None:
        """Clear only local teaching state, including previous demo observations."""
        with self._state_guard(persist=True, reload=False):
            self._state = _initial_state()

    def _event(self, kind: str, operation: str, detail: object) -> None:
        ticket_id, run_id = self._context.get()
        with self._state_guard(persist=True):
            event = {
                "id": f"E-{self._state['next_event']:04d}",
                "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "ticket_id": ticket_id,
                "run_id": run_id,
                "kind": kind,
                "operation": operation,
                "detail": deepcopy(detail),
            }
            self._state["next_event"] += 1
            self._state["events"].append(event)

    def _invoke(self, operation: str, arguments: dict[str, object], action: Callable[[], T]) -> T:
        self._event("call", operation, arguments)
        try:
            result = action()
        except ShopError as error:
            self._event("error", operation, error.as_dict())
            raise
        except Exception as error:
            safe = ShopError("UNEXPECTED_ERROR", "Local function failed; inspect code and retry.")
            self._event("error", operation, {**safe.as_dict(), "exception_type": type(error).__name__})
            raise safe from error
        self._event("result", operation, result)
        return result

    def list_tickets(self) -> list[dict[str, Any]]:
        return [deepcopy(ticket) for ticket in self.catalog["tickets"].values()]

    def ticket(self, ticket_id: str) -> dict[str, Any]:
        ticket = self.catalog["tickets"].get(ticket_id)
        if ticket is None:
            raise ShopError("TICKET_NOT_FOUND", "Choose an existing training ticket.")
        return deepcopy(ticket)

    def case_facts(self, ticket_id: str) -> dict[str, Any]:
        ticket = self.ticket(ticket_id)
        return {
            "ticket": ticket,
            "customer": deepcopy(self.catalog["customers"].get(ticket["customer_id"])),
            "order": deepcopy(self.catalog["orders"].get(ticket["order_id"])),
            "policy": self._policy_for(ticket["topic"], "2026-09-15"),
        }

    def _lookup(self, kind: str, item_id: str) -> dict[str, Any]:
        item = self.catalog[kind].get(item_id)
        if item is None:
            singular = kind[:-1].upper()
            raise ShopError(f"{singular}_NOT_FOUND", f"No local {kind[:-1]} matches {item_id}.")
        return deepcopy(item)

    def get_order(self, order_id: str) -> dict[str, Any]:
        return self._invoke("get_order", {"order_id": order_id}, lambda: self._lookup("orders", order_id))

    def get_customer(self, customer_id: str) -> dict[str, Any]:
        return self._invoke(
            "get_customer", {"customer_id": customer_id}, lambda: self._lookup("customers", customer_id)
        )

    def _policy_for(self, topic: str, as_of: str) -> dict[str, Any]:
        try:
            when = date.fromisoformat(as_of)
        except ValueError as error:
            raise ShopError("INVALID_DATE", "Use an ISO date such as 2026-09-15.") from error
        matches = [
            policy
            for policy in self.catalog["policies"].values()
            if policy["topic"] == topic and date.fromisoformat(policy["effective_on"]) <= when
        ]
        if not matches:
            raise ShopError("POLICY_NOT_FOUND", "No policy was effective for that topic and date.")
        return deepcopy(max(matches, key=lambda item: item["effective_on"]))

    def get_policy(self, topic: str, as_of: str) -> dict[str, Any]:
        return self._invoke(
            "get_policy", {"topic": topic, "as_of": as_of}, lambda: self._policy_for(topic, as_of)
        )

    def read_receipt(self, order_id: str) -> str:
        def action() -> str:
            order = self._lookup("orders", order_id)
            receipt_name = order["receipt"]
            if not receipt_name.startswith("R-") or Path(receipt_name).name != receipt_name:
                raise ShopError("RECEIPT_INVALID", "Receipt reference is invalid.")
            path = ROOT / "receipts" / receipt_name
            if not path.is_file():
                raise ShopError("RECEIPT_NOT_FOUND", "No local text receipt is available.")
            return path.read_text()

        return self._invoke("read_receipt", {"order_id": order_id}, action)

    def set_simulated_identity(self, customer_id: str, verified: bool) -> dict[str, object]:
        def action() -> dict[str, object]:
            self._lookup("customers", customer_id)
            if type(verified) is not bool:
                raise ShopError("INVALID_IDENTITY_STATE", "Use an explicit Boolean for simulated identity.")
            with self._state_guard(persist=True):
                known: set[str] = set(self._state["verified_customers"])
                if verified:
                    known.add(customer_id)
                else:
                    known.discard(customer_id)
                self._state["verified_customers"] = sorted(known)
            return {"customer_id": customer_id, "simulated_identity_verified": verified}

        return self._invoke(
            "set_simulated_identity", {"customer_id": customer_id, "verified": verified}, action
        )

    def record_refund(
        self, order_id: str, amount_cents: int, reason: str, as_of: str
    ) -> dict[str, object]:
        """Append a local ledger item after teaching guards; never move money."""

        def action() -> dict[str, object]:
            with self._state_guard(persist=True):
                # Verification, policy checks and ledger append form one local
                # transaction. Concurrent revocation cannot slip between them.
                order = self._lookup("orders", order_id)
                if order["customer_id"] not in self._state["verified_customers"]:
                    raise ShopError("IDENTITY_REQUIRED", "Simulated identity check is required before a refund.")
                if not order["delivered_on"]:
                    raise ShopError("NOT_DELIVERED", "This training order has no delivery date.")
                policy = self._policy_for("returns", as_of)
                days = (date.fromisoformat(as_of) - date.fromisoformat(order["delivered_on"])).days
                window = 45 if policy["id"] == "POL-RETURN-2026-09" else 30
                if days < 0 or days > window:
                    raise ShopError("POLICY_EXCEPTION", "Return window needs human review.")
                if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or not 0 < amount_cents <= order["total_cents"]:
                    raise ShopError("INVALID_AMOUNT", "Amount must be positive cents at most the order total.")
                if not reason.strip():
                    raise ShopError("MISSING_REASON", "Record a reason for the teaching ledger.")
                if any(item["order_id"] == order_id for item in self._state["refund_ledger"]):
                    raise ShopError("ALREADY_RECORDED", "This order already has a teaching refund record.")
                item = {
                    "id": f"RF-{len(self._state['refund_ledger']) + 1:04d}",
                    "order_id": order_id,
                    "amount_cents": amount_cents,
                    "reason": reason,
                    "policy_id": policy["id"],
                    "teaching_ledger_only": True,
                }
                self._state["refund_ledger"].append(item)
            return deepcopy(item)

        return self._invoke(
            "record_refund",
            {"order_id": order_id, "amount_cents": amount_cents, "reason": reason, "as_of": as_of},
            action,
        )

    def escalate_case(self, ticket_id: str, reason: str) -> dict[str, object]:
        def action() -> dict[str, object]:
            self.ticket(ticket_id)
            if not reason.strip():
                raise ShopError("MISSING_REASON", "Explain why a human needs the case.")
            with self._state_guard(persist=True):
                item = {"id": f"H-{len(self._state['escalations']) + 1:04d}", "ticket_id": ticket_id, "reason": reason}
                self._state["escalations"].append(item)
            return deepcopy(item)

        return self._invoke("escalate_case", {"ticket_id": ticket_id, "reason": reason}, action)

    def events(self, ticket_id: str | None = None) -> list[dict[str, Any]]:
        with self._state_guard():
            events = self._state["events"]
            return deepcopy([event for event in events if ticket_id is None or event["ticket_id"] == ticket_id])

    def ledger(self) -> list[dict[str, Any]]:
        with self._state_guard():
            return deepcopy(self._state["refund_ledger"])

    def simulated_identity_verified(self, customer_id: str) -> bool:
        with self._state_guard():
            return customer_id in self._state["verified_customers"]

    def latest_result(self, ticket_id: str) -> dict[str, Any] | None:
        with self._state_guard():
            result = self._state["results"].get(ticket_id)
            return deepcopy(result) if result else None

    def run_preset(self, ticket_id: str) -> dict[str, Any]:
        """Run fixed demo logic against real local functions, then record outcome."""
        ticket = self.ticket(ticket_id)
        with self._state_guard(persist=True):
            run_id = f"RUN-{self._state['next_run']:04d}"
            self._state["next_run"] += 1
        context_token = self._context.set((ticket_id, run_id))
        try:
            try:
                scenario = ticket["scenario"]
                if scenario == "read_only_success":
                    order = self.get_order(ticket["order_id"])
                    policy = self.get_policy("shipping", "2026-09-15")
                    status = "completed"
                    summary = f"Preset result: {order['id']} is {order['status']}. {order['shipping']}. Policy {policy['id']} was checked."
                    recovery = "Compare the result with the actual order and policy events."
                elif scenario == "policy_and_receipt":
                    order = self.get_order(ticket["order_id"])
                    policy = self.get_policy("damage", "2026-09-15")
                    receipt = self.read_receipt(order["id"])
                    status = "needs_human_review"
                    summary = f"Preset result: receipt for {order['id']} has {len(receipt.splitlines())} text lines; {policy['id']} calls for a human review before any refund promise."
                    recovery = "Inspect the receipt and policy events; a later stage can design the structured handoff."
                elif scenario == "blocked_refund":
                    self.record_refund(ticket["order_id"], 7600, "Customer request", "2026-09-15")
                    status = "completed"
                    summary = "Preset result: a local teaching refund was recorded."
                    recovery = "Inspect the ledger entry."
                elif scenario == "missing_order":
                    self.get_order(ticket["order_id"])
                    status = "completed"
                    summary = "Preset result: order was found."
                    recovery = "Inspect the order event."
                else:
                    raise ShopError("UNKNOWN_SCENARIO", "No preset exists for this training ticket.")
            except ShopError as error:
                status = "blocked"
                summary = f"Preset stopped: {error.code} — {error.message} No successful resolution was recorded."
                recovery = "Read the failed call and its error event. Clarify the missing fact or ask a human; then reset or retry."
            result = {
                "ticket_id": ticket_id,
                "run_id": run_id,
                "mode": "fixed_preset_no_model",
                "status": status,
                "summary": summary,
                "recovery": recovery,
            }
            self._event("demo_outcome", "run_preset", result)
            with self._state_guard(persist=True):
                self._state["results"][ticket_id] = result
            return deepcopy(result)
        finally:
            self._context.reset(context_token)
