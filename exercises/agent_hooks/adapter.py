"""Pinned Agent SDK registration. Construction alone does not call a model."""
import json
from claude_agent_sdk import ClaudeAgentOptions, HookMatcher, tool, create_sdk_mcp_server
from exercises.after_sales.workflow import handle_case
from .callbacks import callbacks

REFUND = "mcp__shop__request_refund"
SHIPPING = "mcp__shop__shipping_sample"


def content(value, error=False):
    return {"content": [{"type": "text", "text": json.dumps(value)}], "isError": error}


def build_options(shop, audit, model):
    @tool("request_refund", "Request a fictional T-1003 kettle refund. Identity is local teaching state. Never moves money.",
          {"type": "object", "properties": {"order_id": {"type": "string"}, "amount_cents": {"type": "integer"},
           "reason": {"type": "string"}, "as_of": {"type": "string"}},
           "required": ["order_id", "amount_cents", "reason", "as_of"], "additionalProperties": False})
    async def refund(args):
        result = handle_case(shop, "T-1003", {"intent": "refund", "human_requested": False,
            "order_candidates": [args["order_id"]], "amount_cents": args["amount_cents"],
            "reason": args["reason"], "as_of": args["as_of"]})
        return content(result, result["status"] != "teaching_refund_recorded")

    @tool("shipping_sample", "Read one authored carrier-format fixture, not a live shipment. unix and iso encode the same instant/status.",
          {"type": "object", "properties": {"format": {"type": "string", "enum": ["unix", "iso"]}},
           "required": ["format"], "additionalProperties": False})
    async def shipping(args):
        if args["format"] == "unix":
            value = {"timestamp": 1788220800, "status": 20}
        else:
            value = {"timestamp": "2026-09-01T01:00:00+01:00", "status": "delivered"}
        return content(value)

    before, after = callbacks(shop, audit)
    return ClaudeAgentOptions(model=model, stderr=lambda _line: None, tools=[], setting_sources=[], strict_mcp_config=True,
        mcp_servers={"shop": create_sdk_mcp_server("shop", tools=[refund, shipping])},
        allowed_tools=[REFUND, SHIPPING], max_turns=4, max_budget_usd=0.10,
        hooks={"PreToolUse": [HookMatcher(matcher="^mcp__shop__request_refund$", hooks=[before])],
               "PostToolUse": [HookMatcher(matcher="^mcp__shop__shipping_sample$", hooks=[after])]})
