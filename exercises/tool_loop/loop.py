"""Manual client-tool loop. Protocol termination is not business resolution."""
from copy import deepcopy
from .tools import dispatch
from .transport import TransportFailure


def run_loop(send, shop, prompt, *, max_turns=6):
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 10_000:
        raise ValueError("Use a bounded nonempty prompt.")
    if type(max_turns) is not int or not 1 <= max_turns <= 12:
        raise ValueError("Use a turn safety bound from 1 to 12.")
    history = [{"role": "user", "content": prompt}]
    trace, seen = [], set()
    errors = 0

    def finish(status, reason, text=""):
        return {"status": status, "stop_reason": reason, "text": text,
                "tool_errors": errors, "history": deepcopy(history), "trace": deepcopy(trace)}

    for turn in range(1, max_turns + 1):
        try:
            response = send(deepcopy(history))
        except TransportFailure as exc:
            trace.append({"event": "transport_error", "turn": turn, "detail": str(exc)})
            return finish("interrupted", "transport_error")
        if not isinstance(response, dict) or not isinstance(response.get("stop_reason"), str):
            return finish("interrupted", "protocol_error")
        reason = response["stop_reason"]
        trace.append({"event": "response", "turn": turn, "stop_reason": reason})
        # Truncation may include incomplete blocks: do not execute or replay them.
        if reason not in {"end_turn", "tool_use"}:
            return finish("interrupted", reason)
        content = response.get("content")
        if not isinstance(content, list):
            return finish("interrupted", "protocol_error")
        calls = []
        for block in content:
            if not isinstance(block, dict):
                return finish("interrupted", "protocol_error")
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                continue
            if (block.get("type") != "tool_use" or not isinstance(block.get("id"), str)
                    or not 1 <= len(block["id"]) <= 256
                    or not isinstance(block.get("name"), str) or not block["name"]
                    or "input" not in block):
                return finish("interrupted", "protocol_error")
            calls.append(block)
        ids = [block["id"] for block in calls]
        if (len(ids) != len(set(ids)) or seen.intersection(ids) or len(calls) > 8
                or (reason == "tool_use" and not calls)
                or (reason == "end_turn" and calls)):
            return finish("interrupted", "protocol_error")
        history.append({"role": "assistant", "content": deepcopy(content)})
        if reason == "end_turn":
            return finish("ended", reason, "\n".join(b["text"] for b in content))
        seen.update(ids)
        results = []
        for block in calls:
            result = dispatch(shop, block)
            errors += int(result["is_error"])
            results.append(result)
            trace.append({"event": "tool_result", "turn": turn,
                          "tool_use_id": block["id"], "is_error": result["is_error"]})
        history.append({"role": "user", "content": results})
    trace.append({"event": "safety_stop", "detail": "turn_limit"})
    return finish("interrupted", "turn_limit")
