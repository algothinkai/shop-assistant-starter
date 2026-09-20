"""Scoped read-only dispatch with structured recoverability metadata."""
import json
from datetime import date
from jsonschema import Draft202012Validator
from mcp.types import CallToolResult, TextContent
from shop_assistant.business import ShopError
from .contracts import DEFINITIONS, PROFILES


def result(value, *, error=False):
    return CallToolResult(content=[TextContent(text=json.dumps(value))], structuredContent=value, isError=error)


def failure(code, category, retryable, message):
    return result({"error": {"code": code, "errorCategory": category,
                             "isRetryable": retryable, "message": message}}, error=True)


def handle_tool(shop, profile, name, arguments, *, denied=False):
    if denied or name not in PROFILES.get(profile, ()):
        return failure("TOOL_NOT_ALLOWED", "permission", False,
                       "This local server profile cannot perform that operation.")
    if not Draft202012Validator(DEFINITIONS[name]["input_schema"]).is_valid(arguments):
        return failure("INVALID_ARGUMENT", "validation", False,
                       "Arguments must match the discovered schema; correct them before retrying.")
    try:
        if name == "get_order":
            value = shop.get_order(arguments["order_id"])
        elif name == "find_orders":
            value = {"orders": [dict(item) for item in shop.catalog["orders"].values()
                                if item["customer_id"] == arguments["customer_id"]]}
        else:
            date.fromisoformat(arguments["as_of"])
            value = shop.get_policy(arguments["topic"], arguments["as_of"])
        return result(value)
    except ValueError:
        return failure("INVALID_DATE", "validation", False, "Use a real ISO calendar date.")
    except ShopError as error:
        return failure(error.code, "transient" if error.retryable else "business",
                       error.retryable, error.message)
