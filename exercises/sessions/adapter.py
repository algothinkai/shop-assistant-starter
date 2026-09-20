"""Learner SDK session adapter. Fixture success is not live resumption."""
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
    raise NotImplementedError("Choose fresh, resume or fork without reusing stale results")


def build_options(action, previous_id, cwd, model):
    raise NotImplementedError("Use explicit SDK session ID, isolated settings and bounded calls")


async def consume(messages):
    raise NotImplementedError("Require successful terminal result; retain only safe session metadata")
