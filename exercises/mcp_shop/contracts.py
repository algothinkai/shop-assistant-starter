"""Purpose-specific local MCP contracts, shared with the request-shaping lab."""
ORDER_ID = {"type": "string", "pattern": "^O-[0-9]{4}$"}
CUSTOMER_ID = {"type": "string", "pattern": "^C-[0-9]{4}$"}


def schema(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


DEFINITIONS = {
    "get_order": {"name": "get_order", "description": "Read one fictional order by exact ID (for example O-1001). Returns order facts or ORDER_NOT_FOUND. Use find_orders only when the customer ID is known instead. Never refunds or verifies identity.", "input_schema": schema({"order_id": ORDER_ID})},
    "find_orders": {"name": "find_orders", "description": "Find fictional orders for one exact customer ID (for example C-1001). Returns an object with an orders array, possibly empty; an empty array is success. Does not search names, change orders or decide policy.", "input_schema": schema({"customer_id": CUSTOMER_ID})},
    "get_policy": {"name": "get_policy", "description": "Read the fictional policy version effective on an explicit ISO date for a topic. Use for a dated policy decision, not order lookup. The policy catalog resource lists available topics/versions. Does not authorize exceptions or refunds.", "input_schema": schema({"topic": {"type": "string", "enum": ["shipping", "returns", "damage", "warranty"]}, "as_of": {"type": "string", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}})},
}
PROFILES = {"orders": ("get_order", "find_orders"), "policies": ("get_policy",)}
CATALOG_URI = "shop://policies/catalog"
