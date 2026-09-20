"""Offline request shape only: no model call or evidence of model selection."""
from copy import deepcopy
from .contracts import DEFINITIONS, PROFILES


def request_settings(profile, choice="auto", forced_name=None):
    if profile not in PROFILES or choice not in {"auto", "any", "tool"}:
        raise ValueError("Unknown profile or tool-choice mode")
    if choice == "tool":
        if forced_name not in PROFILES[profile]:
            raise ValueError("Forced tool must be inside the assigned role")
        tool_choice = {"type": "tool", "name": forced_name}
    elif forced_name is not None:
        raise ValueError("Name is only valid with forced tool choice")
    else:
        tool_choice = {"type": choice}
    return {"tools": [deepcopy(DEFINITIONS[n]) for n in PROFILES[profile]], "tool_choice": tool_choice}
