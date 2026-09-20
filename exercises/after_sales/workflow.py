"""Deterministic local policy workflow, not model understanding or SDK hooks."""
import json
import re
from datetime import date
from shop_assistant.business import ShopError

FIELDS = {"intent", "human_requested", "order_candidates", "amount_cents", "reason", "as_of"}


def handle_case(shop, ticket_id, request):
    mode = "deterministic_local_workflow_no_model"
    def outcome(status, **fields):
        return {"mode": mode, "status": status, **fields}
    if not isinstance(request, dict) or set(request) - FIELDS:
        return outcome("invalid_request", code="INVALID_REQUEST")
    if type(request.get("human_requested")) is not bool:
        return outcome("invalid_request", code="INVALID_REQUEST")
    try:
        ticket = shop.ticket(ticket_id)
    except ShopError as error:
        return outcome("blocked", code=error.code, message=error.message)
    attempts = []
    order = None
    policy = None

    def handoff(cause):
        amount = request.get("amount_cents")
        details = {"ticket_id": ticket_id, "customer_id": ticket["customer_id"],
                   "order_id": order["id"] if order else None,
                   "root_cause": cause,
                   "requested_amount_cents": amount if type(amount) is int and amount > 0 else None,
                   "policy_id": policy["id"] if policy else None,
                   "policy_effective_on": policy["effective_on"] if policy else None,
                   "requested_as_of": request.get("as_of") if isinstance(request.get("as_of"), str) else None,
                   "customer_reason": request.get("reason", "").strip() if isinstance(request.get("reason", ""), str) else None,
                   "reported_order_id": ticket["order_id"],
                   "observed_order": {key: order[key] for key in ("id", "customer_id", "delivered_on", "status", "total_cents")} if order else None,
                   "observed_policy": dict(policy) if policy else None,
                   "attempts": list(attempts),
                   "recommended_action": "Human review requested. Confirm missing facts and applicable policy before promising any action.",
                   "teaching_only": True}
        # Existing local escalation persists the complete handoff as a reason.
        try:
            record = shop.escalate_case(ticket_id, json.dumps(details))
        except ShopError as error:
            return outcome("blocked", code=error.code, message=error.message, handoff=details)
        return outcome("needs_human_review", handoff=details, escalation=record)

    # Honor an explicit human request before lookup, identity checks or diagnosis.
    if request["human_requested"]:
        return handoff("EXPLICIT_HUMAN_REQUEST")
    if not (FIELDS - {"amount_cents"}).issubset(request):
        return outcome("invalid_request", code="INVALID_REQUEST")
    candidates = request["order_candidates"]
    if (request["intent"] not in ("refund", "inquiry")
            or (request["intent"] == "refund" and (type(request.get("amount_cents")) is not int or request["amount_cents"] <= 0))
            or not isinstance(request["reason"], str) or not request["reason"].strip()
            or not isinstance(candidates, list)
            or any(not isinstance(x, str) or not re.fullmatch(r"O-[0-9]{4}", x.strip().upper()) for x in candidates)
            or not isinstance(request["as_of"], str)):
        return outcome("invalid_request", code="INVALID_REQUEST")
    try:
        as_of = request["as_of"].strip()
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", as_of):
            raise ValueError
        date.fromisoformat(as_of)
    except ValueError:
        return outcome("invalid_request", code="INVALID_REQUEST")
    candidates = list(dict.fromkeys(x.strip().upper() for x in candidates))
    if len(candidates) != 1:
        return outcome("needs_clarification", code="AMBIGUOUS_ORDER",
                       question="Which exact order ID should we use? No order has been selected.")

    def call(name, *args):
        try:
            result = getattr(shop, name)(*args)
        except ShopError as error:
            attempts.append({"operation": name, "outcome": "error", "code": error.code})
            raise
        attempts.append({"operation": name, "outcome": "success"})
        return result

    try:
        order = call("get_order", candidates[0])
        if order["customer_id"] != ticket["customer_id"]:
            return outcome("needs_clarification", code="ORDER_CUSTOMER_MISMATCH",
                           question="The selected order does not match this training customer. Confirm the identifier.")
        policy = call("get_policy", ticket["topic"], as_of)
        if request["intent"] == "inquiry":
            return outcome("facts_ready", order=order, policy=policy)
        if ticket["topic"] != "returns":
            return handoff("POLICY_REVIEW_REQUIRED")
        if not shop.simulated_identity_verified(order["customer_id"]):
            return outcome("blocked", code="IDENTITY_REQUIRED",
                           message="Complete the explicit local teaching identity step before a refund.")
        # Defense in depth: the existing atomic business guard checks current
        # identity, date, amount and duplicate ledger records again at mutation.
        record = call("record_refund", order["id"], request["amount_cents"], request["reason"].strip(), as_of)
        return outcome("teaching_refund_recorded", record=record)
    except ShopError as error:
        if error.code == "ORDER_NOT_FOUND":
            return outcome("needs_clarification", code=error.code, question="Confirm the order identifier before continuing.")
        if error.code in ("POLICY_EXCEPTION", "POLICY_NOT_FOUND", "NOT_DELIVERED"):
            return handoff(error.code)
        return outcome("blocked", code=error.code, message=error.message)
