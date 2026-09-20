"""Explicit SDK session contracts; authored messages do not prove live behavior."""
from pathlib import Path
from uuid import UUID
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage
from exercises.context.state import versions


def session_id(value):
    try:
        return str(UUID(value)) if isinstance(value, str) else None
    except ValueError:
        return None


def choose_action(mode, previous_id, saved_versions, current_versions):
    if mode not in ("fresh", "resume", "fork"):
        raise ValueError("Choose fresh, resume or fork")
    current = versions(current_versions)
    if mode == "fresh":
        return "fresh"
    if session_id(previous_id) is None:
        raise ValueError("An explicit session ID is required")
    return mode if versions(saved_versions) == current else "fresh"


def build_options(action, previous_id, cwd, model):
    if action not in ("fresh", "resume", "fork"):
        raise ValueError("Invalid session action")
    prior = session_id(previous_id)
    if action != "fresh" and prior is None:
        raise ValueError("An explicit session ID is required")
    if not isinstance(model, str) or not model.strip() or len(model) > 200:
        raise ValueError("Choose an explicit model")
    if not isinstance(cwd, (str, Path)) or not Path(cwd).is_dir():
        raise ValueError("Use an existing local working directory")
    return ClaudeAgentOptions(model=model, cwd=str(Path(cwd).resolve()), tools=[],
        mcp_servers={}, strict_mcp_config=True, setting_sources=[],
        continue_conversation=False, resume=None if action == "fresh" else prior,
        fork_session=action == "fork", max_turns=2, max_budget_usd=0.10,
        stderr=lambda _line: None)


async def consume(messages):
    terminal = None
    count = 0
    sid = None
    try:
        seen = 0
        async for message in messages:
            seen += 1
            if seen > 1000:
                return {"status": "failed", "session_id": sid, "text": None}
            if isinstance(message, ResultMessage):
                count += 1
                if count == 1:
                    terminal = message
                    sid = session_id(message.session_id)
    except Exception:
        return {"status": "failed", "session_id": sid, "text": None}
    valid = (count == 1 and sid is not None and terminal.subtype == "success"
             and terminal.is_error is False
             and terminal.stop_reason in (None, "end_turn", "stop_sequence")
             and terminal.terminal_reason in (None, "success", "end_turn")
             and isinstance(terminal.result, str) and len(terminal.result) <= 10000)
    return {"status": "success" if valid else "failed", "session_id": sid,
            "text": terminal.result if valid else None}
