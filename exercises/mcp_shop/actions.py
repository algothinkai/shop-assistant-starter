"""Stage 3 exercise: implement the scoped dispatcher and structured failures."""
import json
from mcp.types import CallToolResult, TextContent


def result(value, *, error=False):
    return CallToolResult(content=[TextContent(text=json.dumps(value))], structuredContent=value, isError=error)


def failure(code, category, retryable, message):
    return result({"error": {"code": code, "errorCategory": category,
                             "isRetryable": retryable, "message": message}}, error=True)


def handle_tool(shop, profile, name, arguments, *, denied=False):
    return failure("NOT_READY", "validation", False, "Implement the Stage 3 dispatcher before claiming the tool works.")
