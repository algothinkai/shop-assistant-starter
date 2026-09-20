"""Synchronous decisions from async callbacks; no mutation or model calls here."""
import json
import math
from datetime import datetime, timezone
from shop_assistant.business import ShopError


def callbacks(shop, audit):
    async def before(data, tool_use_id, context):
        if data.get("hook_event_name") != "PreToolUse" or data.get("tool_name") != "mcp__shop__request_refund":
            return {}
        args = data.get("tool_input")
        reason = None
        if not isinstance(args, dict) or type(args.get("amount_cents")) is not int or args["amount_cents"] <= 0:
            reason = "Invalid amount. Correct the request before retrying."
        elif args["amount_cents"] > 50000:
            reason = "The experimental teaching ceiling is $500. Request human review; do not split the amount to bypass it."
        elif args.get("order_id") != "O-1003":
            reason = "This exercise is bound to T-1003/O-1003. Clarify the order identifier."
        else:
            try:
                if not shop.simulated_identity_verified("C-1003"):
                    reason = "Simulated identity is unverified. Request the local teaching identity step or human review."
            except ShopError:
                reason = "Local prerequisite state is unavailable. Stop and request human review."
        audit.append({"event": "PreToolUse", "tool_use_id": tool_use_id, "decision": "deny" if reason else "continue_permission_checks"})
        if reason:
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}
        return {}  # Does not bypass other permission checks or atomic business guards.

    async def after(data, tool_use_id, context):
        if data.get("hook_event_name") != "PostToolUse" or data.get("tool_name") != "mcp__shop__shipping_sample":
            return {}
        response = data.get("tool_response")
        if isinstance(response, dict) and response.get("isError") is True:
            audit.append({"event": "PostToolUse", "tool_use_id": tool_use_id, "normalization": "preserved_error"})
            return {}
        try:
            if not isinstance(response, dict) or len(response.get("content", [])) != 1:
                raise ValueError
            block = response["content"][0]
            if block.get("type") != "text":
                raise ValueError
            raw = json.loads(block["text"])
            stamp, status = raw["timestamp"], raw["status"]
            if type(stamp) in (int, float) and math.isfinite(stamp):
                when = datetime.fromtimestamp(stamp, timezone.utc)
            elif isinstance(stamp, str):
                when = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                if when.tzinfo is None:
                    raise ValueError
            else:
                raise ValueError
            if type(status) is int and status in (10, 20, 30):
                status = {10: "shipped", 20: "delivered", 30: "delayed"}[status]
            elif not isinstance(status, str) or status not in ("shipped", "delivered", "delayed"):
                raise ValueError
            value = {"timestamp_utc": when.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"), "status": status,
                     "source": "authored_carrier_fixture"}
            replacement = {"content": [{"type": "text", "text": json.dumps(value)}], "isError": False}
            outcome = "normalized"
        except (ValueError, TypeError, KeyError, OverflowError, OSError, AttributeError):
            replacement = {"content": [{"type": "text", "text": json.dumps({"code": "NORMALIZATION_FAILED", "message": "Carrier fixture format is invalid; do not infer shipment status."})}], "isError": True}
            outcome = "failed"
        audit.append({"event": "PostToolUse", "tool_use_id": tool_use_id, "normalization": outcome})
        return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "updatedToolOutput": replacement}}
    return before, after
