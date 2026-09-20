SCHEMA = {"type": "object", "additionalProperties": False,
          "required": ["stated_total_cents", "calculated_total_cents", "difference_cents", "conflict_detected", "category", "category_detail"],
          "properties": {
              "stated_total_cents": {"type": ["integer", "null"]},
              "calculated_total_cents": {"type": ["integer", "null"]},
              "difference_cents": {"type": ["integer", "null"]},
              "conflict_detected": {"type": "boolean"},
              "category": {"type": "string", "enum": ["kettle", "grinder", "filter", "other", "unclear"]},
              "category_detail": {"type": ["string", "null"]}}}
