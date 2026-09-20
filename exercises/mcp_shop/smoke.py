"""Local subprocess MCP evidence, including explicit injected failure traces."""
import json
import importlib.metadata
import anyio
from .client import connect, call_with_retry
from .contracts import CATALOG_URI


async def run():
    async with connect("orders") as orders, connect("policies") as policies:
        out = {"mode": "local_stdio_mcp_no_model", "sdk": importlib.metadata.version("mcp"),
               "servers": {}}
        for name, client in [("orders", orders), ("policies", policies)]:
            out["servers"][name] = {"protocol": client.protocol_version,
                "name": client.server_info.name,
                "tools": (await client.list_tools()).model_dump(mode="json", by_alias=True),
                "resources": (await client.list_resources()).model_dump(mode="json", by_alias=True)}
        out["order"] = (await orders.call_tool("get_order", {"order_id": "O-1001"})).model_dump(mode="json", by_alias=True)
        out["missing"] = (await orders.call_tool("get_order", {"order_id": "O-9999"})).model_dump(mode="json", by_alias=True)
        out["empty"] = (await orders.call_tool("find_orders", {"customer_id": "C-9999"})).model_dump(mode="json", by_alias=True)
        out["catalog"] = (await policies.read_resource(CATALOG_URI)).model_dump(mode="json", by_alias=True)
        out["policy"] = (await policies.call_tool("get_policy", {"topic": "returns", "as_of": "2026-09-15"})).model_dump(mode="json", by_alias=True)
    async with connect("orders", "--transient-once") as fault:
        _, out["injected_transient_attempts"] = await call_with_retry(fault, "get_order", {"order_id": "O-1001"})
    async with connect("orders", "--deny") as denied:
        _, out["simulated_permission_attempts"] = await call_with_retry(denied, "get_order", {"order_id": "O-1001"})
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    anyio.run(run)
