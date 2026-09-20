"""Explicit offline hook probe or opt-in live SDK run with local credentials."""
import argparse
import asyncio
import importlib.metadata
import json
import os
import tempfile
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ResultMessage
from shop_assistant.business import ShopService
from .adapter import build_options, content, REFUND, SHIPPING


async def run(live):
    model = os.environ.get("ANTHROPIC_MODEL") if live else "offline-no-model"
    if not model:
        print("Set ANTHROPIC_MODEL locally for an explicit live run. Authentication also stays local; no key is collected here.")
        return 2
    with tempfile.TemporaryDirectory(prefix="shop-hooks-") as directory:
        shop = ShopService(Path(directory))
        audit = []
        options = build_options(shop, audit, model)
        options.cwd = directory
        observations = []
        terminal = None
        if live:
            # Keep raw SDK/server exceptions and credentials out of printed output.
            try:
                async with asyncio.timeout(60):
                    async with ClaudeSDKClient(options=options) as client:
                        await client.query("In this fictional teaching case, call shipping_sample with format unix. Then request_refund for O-1003, amount_cents 7600, reason Unwanted kettle, as_of 2026-09-15. If denied, report that prerequisite and stop; do not retry or work around it.")
                        async for message in client.receive_response():
                            observations.append(type(message).__name__)
                            if isinstance(message, ResultMessage):
                                known_subtypes = {"success", "error_max_turns", "error_max_budget_usd", "error_during_execution", "error_max_structured_output_retries"}
                                known_reasons = {"end_turn", "max_tokens", "max_turns", "max_budget_usd", "success", "refusal", "stop_sequence"}
                                terminal = {"subtype": message.subtype if message.subtype in known_subtypes else "unrecognized",
                                            "is_error": message.is_error is not False,
                                            "terminal_reason": message.terminal_reason if message.terminal_reason in known_reasons or message.terminal_reason is None else "unrecognized",
                                            "stop_reason": message.stop_reason if message.stop_reason in known_reasons or message.stop_reason is None else "unrecognized"}
            except Exception as error:
                print(json.dumps({"mode": "live_sdk_attempt", "status": "UNVERIFIED", "error_type": type(error).__name__, "hook_events": audit}))
                return 1
        else:
            before = options.hooks["PreToolUse"][0].hooks[0]
            after = options.hooks["PostToolUse"][0].hooks[0]
            observations.append(await before({"hook_event_name": "PreToolUse", "tool_name": REFUND,
                "tool_input": {"order_id": "O-1003", "amount_cents": 7600}}, "offline-refund", {}))
            observations.append(await after({"hook_event_name": "PostToolUse", "tool_name": SHIPPING,
                "tool_response": content({"timestamp": 1788220800, "status": 20})}, "offline-shipping", {}))
        verified = any(e.get("decision") == "deny" for e in audit) and any(e.get("normalization") == "normalized" for e in audit)
        hooks_observed = verified
        if live:
            verified = bool(verified and terminal and terminal["subtype"] == "success" and not terminal["is_error"]
                            and terminal["terminal_reason"] in (None, "success", "end_turn")
                            and terminal["stop_reason"] in (None, "end_turn", "stop_sequence"))
        print(json.dumps({"mode": "live_sdk_attempt" if live else "offline_registered_callbacks_no_model",
            "sdk_version": importlib.metadata.version("claude-agent-sdk"),
            "status": ("OBSERVED_REQUESTED_HOOKS" if verified else "UNVERIFIED") if live else "OFFLINE_ONLY",
            "hook_events": audit, "hooks_observed": hooks_observed, "terminal": terminal, "observations": observations, "ledger": shop.ledger()}, indent=2))
        return 0 if not live or verified else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Deliberate billable local SDK call; requires local authentication/model; capped at 4 turns, $0.10 and 60 seconds")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.live)))


if __name__ == "__main__":
    main()
