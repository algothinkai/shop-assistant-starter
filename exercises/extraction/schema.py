"""Nullable values avoid forcing invented facts; provenance is checked separately."""
FIELDS = {"order_id": "string", "purchase_date": "string", "currency": "string", "total_cents": "integer", "customer_name": "string"}
SCHEMA = {"type": "object", "additionalProperties": False, "required": list(FIELDS),
          "properties": {name: {"type": "object", "additionalProperties": False,
              "required": ["value", "evidence"], "properties": {
                  "value": {"type": [kind, "null"]}, "evidence": {"type": ["string", "null"]}}}
              for name, kind in FIELDS.items()}}
