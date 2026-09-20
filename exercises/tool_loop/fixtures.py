"""Authored protocol fixtures, not captured model output or live evidence."""
from copy import deepcopy


def message(reason, *content):
    return {"stop_reason": reason, "content": list(content)}


def text(value):
    return {"type": "text", "text": value}


def call(identifier, order="O-1001", name="get_order"):
    return {"type": "tool_use", "id": identifier, "name": name, "input": {"order_id": order}}


SCENARIOS = {
    "happy": [message("tool_use", text("I will inspect the order."), call("u1")),
              message("end_turn", text("Fixture summary: inspect the returned order facts; no model ran."))],
    "missing": [message("tool_use", call("u1", "O-9999")),
                message("end_turn", text("Fixture summary: ask for the missing order ID; no model ran."))],
    "multiple": [message("tool_use", call("u1"), call("u2", "O-1002")),
                 message("tool_use", call("u3", "O-1003")),
                 message("end_turn", text("Fixture summary: three read-only lookups; no model ran."))],
    "truncated": [message("max_tokens", text("All done, trust me."), call("u1"))],
}


class SequenceTransport:
    def __init__(self, responses):
        self.responses = deepcopy(responses)
        self.requests = []

    def __call__(self, history):
        self.requests.append(deepcopy(history))
        if not self.responses:
            raise AssertionError("Unexpected request beyond fixture sequence")
        return self.responses.pop(0)
