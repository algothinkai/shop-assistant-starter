"""A single allowlisted client tool reusing the fictional shop function."""
import json
import re
from shop_assistant.business import ShopError

TOOLS = [{"name": "get_order", "description": "Read a fictional local order by its exact order ID. Returns current order facts; never changes payment or identity state.",
          "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                           "required": ["order_id"], "additionalProperties": False}}]


def dispatch(shop, block):
    try:
        if block["name"] != "get_order":
            raise ShopError("UNKNOWN_TOOL", "Only get_order is available in Stage 2.")
        args = block["input"]
        if (not isinstance(args, dict) or set(args) != {"order_id"}
                or not isinstance(args["order_id"], str)
                or not re.fullmatch(r"O-[0-9]{4}", args["order_id"])):
            raise ShopError("INVALID_ARGUMENT", "Use one order_id such as O-1001.")
        value = shop.get_order(args["order_id"])
        error = False
    except ShopError as exc:
        value = {"error": exc.as_dict()}
        error = True
    return {"type": "tool_result", "tool_use_id": block["id"],
            "content": json.dumps(value), "is_error": error}
