"""Authored host envelopes, not actual model output."""

from copy import deepcopy
import json
from exercises.code_review.fixtures import ISSUE


def envelope(host, findings=None):
    result = {"findings": findings if findings is not None else [deepcopy(ISSUE)]}
    if host == "claude":
        return (
            json.dumps(
                {
                    "type": "result",
                    "subtype": "success",
                    "is_error": False,
                    "structured_output": result,
                }
            ),
            None,
            0,
        )
    final = json.dumps(result)
    events = [
        {"type": "thread.started", "thread_id": "authored"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {"id": "authored-message", "type": "agent_message", "text": final},
        },
        {"type": "turn.completed", "usage": {}},
    ]
    return "\n".join(map(json.dumps, events)), final, 0
