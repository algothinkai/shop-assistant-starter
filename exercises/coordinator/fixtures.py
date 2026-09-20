"""Authored SDK protocol events; never evidence of live delegation decisions."""

import json
from claude_agent_sdk import (
    AssistantMessage,
    UserMessage,
    ToolUseBlock,
    ToolResultBlock,
    ResultMessage,
)
from .runtime import PREFIX


def terminal(error=False):
    return ResultMessage(
        subtype="error_max_turns" if error else "success",
        duration_ms=1,
        duration_api_ms=0,
        is_error=error,
        num_turns=3,
        session_id="00000000-0000-0000-0000-000000000007",
        result="Authored fixture",
        stop_reason="end_turn",
    )


async def call_hook(options, name, args, call_id, role=None):
    hook = options.hooks["PreToolUse"][0].hooks[0]
    data = {
        "hook_event_name": "PreToolUse",
        "tool_name": name,
        "tool_input": args,
        "tool_use_id": call_id,
    }
    if role:
        data.update(agent_type=role, agent_id="child-" + role)
    return (await hook(data, call_id, {}))["hookSpecificOutput"]


async def authored_stream(runtime, options):
    # Deliberately incomplete first returns report creates a real coverage gap.
    # This script is an authored scenario, not a coordinator policy.
    batches = [
        [
            (t, runtime.scope(t)[:1] if t == "returns" else runtime.scope(t))
            for t in runtime.topics
        ]
    ]
    for round_number in range(2):
        if round_number:
            missing = (
                runtime.coverage()["topics"]
                .get("returns", {})
                .get("missing_sources", [])
            )
            if not missing:
                break
            batches.append([("returns", missing)])
        tasks = batches[round_number]
        blocks = []
        for index, (topic, ids) in enumerate(tasks):
            call_id = f"delegate-{round_number}-{index}"
            args = {
                "subagent_type": topic + "-research",
                "prompt": "Investigate dated evidence: " + ", ".join(ids),
            }
            blocks.append(ToolUseBlock(id=call_id, name="Agent", input=args))
        yield AssistantMessage(content=blocks, model="authored")
        for block, (topic, ids) in zip(blocks, tasks):
            hook = await call_hook(options, "Agent", block.input, block.id)
            if hook["permissionDecision"] != "allow":
                raise AssertionError("Fixture delegation denied")
            args = {"topic": topic, "source_ids": ids}
            child_id = block.id + "-read"
            yield AssistantMessage(
                content=[
                    ToolUseBlock(id=child_id, name=PREFIX + "investigate", input=args)
                ],
                model="authored",
                parent_tool_use_id=block.id,
            )
            guard = await call_hook(
                options, PREFIX + "investigate", args, child_id, topic + "-research"
            )
            if guard["permissionDecision"] != "allow":
                raise AssertionError("Fixture read denied")
            result = await runtime.handlers["investigate"](args)
            yield UserMessage(
                content=[
                    ToolResultBlock(
                        tool_use_id=child_id,
                        content=result["content"],
                        is_error=result["isError"],
                    )
                ],
                parent_tool_use_id=block.id,
            )
            yield UserMessage(
                content=[
                    ToolResultBlock(
                        tool_use_id=block.id,
                        content="Authored agent returned its report",
                        is_error=False,
                    )
                ]
            )
        inspect_id = f"inspect-{round_number}"
        yield AssistantMessage(
            content=[
                ToolUseBlock(id=inspect_id, name=PREFIX + "inspect_coverage", input={})
            ],
            model="authored",
        )
        await call_hook(options, PREFIX + "inspect_coverage", {}, inspect_id)
        result = await runtime.handlers["inspect_coverage"]({})
        yield UserMessage(
            content=[
                ToolResultBlock(
                    tool_use_id=inspect_id, content=result["content"], is_error=False
                )
            ]
        )
    yield terminal()
