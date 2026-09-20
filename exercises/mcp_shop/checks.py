"""Real local stdio protocol checks plus role/request boundaries; no model calls."""
import json
import unittest
from .client import connect, call_with_retry
from .contracts import CATALOG_URI
from .model_settings import request_settings


class ProtocolChecks(unittest.IsolatedAsyncioTestCase):
    async def test_two_live_servers_discover_distinct_tools_and_resources(self):
        async with connect("orders") as orders, connect("policies") as policies:
            self.assertEqual(orders.protocol_version, "2026-07-28")
            self.assertEqual(policies.protocol_version, "2026-07-28")
            self.assertEqual({t.name for t in (await orders.list_tools()).tools}, {"get_order", "find_orders"})
            self.assertEqual({t.name for t in (await policies.list_tools()).tools}, {"get_policy"})
            self.assertEqual((await orders.list_resources()).resources, [])
            catalog = await policies.read_resource(CATALOG_URI)
            self.assertEqual(json.loads(catalog.contents[0].text)[0]["effective_on"], "2026-06-01")
            order = await orders.call_tool("get_order", {"order_id": "O-1001"})
            self.assertFalse(order.is_error)
            self.assertEqual(order.structured_content["id"], "O-1001")
            policy = await policies.call_tool("get_policy", {"topic": "returns", "as_of": "2026-09-15"})
            self.assertFalse(policy.is_error)
            self.assertEqual(policy.structured_content["id"], "POL-RETURN-2026-09")

    async def test_validation_business_permission_and_empty_are_distinct(self):
        async with connect("orders") as orders:
            for arguments in [{"order_id": 7}, {"order_id": "../x"}, {"order_id": "O-1001", "extra": True}]:
                error = await orders.call_tool("get_order", arguments)
                self.assertTrue(error.is_error)
                self.assertEqual(error.structured_content["error"]["errorCategory"], "validation")
                self.assertFalse(error.structured_content["error"]["isRetryable"])
            missing, attempts = await call_with_retry(orders, "get_order", {"order_id": "O-9999"})
            self.assertEqual(missing.structured_content["error"]["code"], "ORDER_NOT_FOUND")
            self.assertEqual(len(attempts), 1)
            empty = await orders.call_tool("find_orders", {"customer_id": "C-9999"})
            self.assertFalse(empty.is_error)
            self.assertEqual(empty.structured_content, {"orders": []})
            forbidden = await orders.call_tool("record_refund", {"order_id": "O-1001"})
            self.assertTrue(forbidden.is_error)
            self.assertEqual(forbidden.structured_content["error"]["errorCategory"], "permission")

    async def test_bounded_retry_only_for_injected_transient_error(self):
        async with connect("orders", "--transient-once") as client:
            response, attempts = await call_with_retry(client, "get_order", {"order_id": "O-1001"})
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]["structuredContent"]["error"]["errorCategory"], "transient")
            self.assertFalse(response.is_error)
        async with connect("orders", "--deny") as client:
            response, attempts = await call_with_retry(client, "get_order", {"order_id": "O-1001"})
            self.assertTrue(response.is_error)
            self.assertEqual(len(attempts), 1)
            self.assertEqual(response.structured_content["error"]["errorCategory"], "permission")

    async def test_invalid_input_does_not_consume_or_retry_transient_fault(self):
        for profile, name, invalid, valid in [
            ("orders", "get_order", {"order_id": 7}, {"order_id": "O-1001"}),
            ("policies", "get_policy", {"topic": "returns", "as_of": "2026-02-31"},
             {"topic": "returns", "as_of": "2026-09-15"}),
        ]:
            async with connect(profile, "--transient-once") as client:
                response, attempts = await call_with_retry(client, name, invalid)
                self.assertTrue(response.is_error)
                self.assertEqual(response.structured_content["error"]["errorCategory"], "validation")
                self.assertEqual(len(attempts), 1)
                response, attempts = await call_with_retry(client, name, valid)
                self.assertEqual(len(attempts), 2)
                self.assertEqual(attempts[0]["structuredContent"]["error"]["code"], "SIMULATED_UNAVAILABLE")
                self.assertFalse(response.is_error)

    async def test_invalid_date_and_unknown_resource_fail_explicitly(self):
        from mcp import MCPError
        async with connect("policies") as client:
            response = await client.call_tool("get_policy", {"topic": "returns", "as_of": "2026-02-31"})
            self.assertTrue(response.is_error)
            self.assertEqual(response.structured_content["error"]["errorCategory"], "validation")
            with self.assertRaises(MCPError):
                await client.read_resource("shop://policies/missing")


class RequestChecks(unittest.TestCase):
    def test_choice_is_scoped_and_does_not_change_permissions(self):
        for profile in ("orders", "policies"):
            for mode in ("auto", "any"):
                settings = request_settings(profile, mode)
                self.assertEqual(settings["tool_choice"], {"type": mode})
                self.assertNotIn("record_refund", {t["name"] for t in settings["tools"]})
        forced = request_settings("orders", "tool", "get_order")
        self.assertEqual(forced["tool_choice"], {"type": "tool", "name": "get_order"})
        with self.assertRaises(ValueError):
            request_settings("policies", "tool", "get_order")


if __name__ == "__main__":
    unittest.main()
