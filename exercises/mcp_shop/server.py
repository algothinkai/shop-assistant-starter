"""Two local MCP servers. stdout is protocol only; no model or hosted service."""
import argparse
import json
import tempfile
from pathlib import Path
import anyio
from mcp import MCPError
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import (Tool, ToolAnnotations, ListToolsResult, Resource, ListResourcesResult,
                       ReadResourceResult, TextResourceContents)
from shop_assistant.business import ShopService
from .actions import handle_tool, failure
from .contracts import DEFINITIONS, PROFILES, CATALOG_URI, valid_arguments


def build_server(shop, profile, *, denied=False, transient_once=False):
    if profile not in PROFILES:
        raise ValueError("Unknown local server profile")
    remaining_fault = transient_once

    async def list_tools(context, params):
        return ListToolsResult(tools=[Tool(name=name, description=DEFINITIONS[name]["description"],
            inputSchema=DEFINITIONS[name]["input_schema"],
            annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
            for name in PROFILES[profile]])

    async def call_tool(context, params):
        nonlocal remaining_fault
        if (remaining_fault and params.name in PROFILES[profile] and not denied
                and valid_arguments(params.name, params.arguments or {})):
            remaining_fault = False
            return failure("SIMULATED_UNAVAILABLE", "transient", True,
                           "Injected local outage. Retry at most once in this exercise.")
        return handle_tool(shop, profile, params.name, params.arguments or {}, denied=denied)

    async def list_resources(context, params):
        resources = [Resource(uri=CATALOG_URI, name="Policy version catalog", mimeType="application/json",
                              description="Fictional policy topics, dates and IDs; read without exploratory tool calls.")] if profile == "policies" else []
        return ListResourcesResult(resources=resources)

    async def read_resource(context, params):
        if profile != "policies" or str(params.uri) != CATALOG_URI:
            raise MCPError(code=-32602, message="Unknown local resource")
        # Catalog metadata is read-only; use get_policy for the dated content.
        catalog = [{k: item[k] for k in ("id", "topic", "effective_on")} for item in shop.catalog["policies"].values()]
        return ReadResourceResult(contents=[TextResourceContents(uri=CATALOG_URI, mimeType="application/json", text=json.dumps(catalog))])

    return Server("shop-" + profile, version="stage-3-draft-1",
                  instructions="Fictional read-only teaching data; tool annotations are hints, not access control.",
                  on_list_tools=list_tools, on_call_tool=call_tool,
                  on_list_resources=list_resources, on_read_resource=read_resource)


async def serve(profile, denied, transient_once):
    with tempfile.TemporaryDirectory(prefix="shop-mcp-") as directory:
        server = build_server(ShopService(Path(directory)), profile, denied=denied, transient_once=transient_once)
        async with stdio_server() as (reader, writer):
            await server.run(reader, writer, server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, required=True)
    parser.add_argument("--deny", action="store_true", help="Simulate local tool permission denial; not real authentication")
    parser.add_argument("--transient-once", action="store_true", help="Inject one local retryable error; not an external outage")
    args = parser.parse_args()
    anyio.run(serve, args.profile, args.deny, args.transient_once)


if __name__ == "__main__":
    main()
