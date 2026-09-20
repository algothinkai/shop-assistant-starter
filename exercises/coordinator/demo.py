"""Explicit live opt-in; offline mode is authored SDK events plus real local tools."""

import argparse
import asyncio
import json
import os
import tempfile
from claude_agent_sdk import query
from .adapter import build_options, consume
from .runtime import ResearchRuntime


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--topics",
        nargs="+",
        choices=["returns", "shipping"],
        default=["returns", "shipping"],
    )
    parser.add_argument(
        "--fault", choices=["none", "transient", "persistent"], default="none"
    )
    args = parser.parse_args()
    model = os.environ.get("ANTHROPIC_MODEL", "")
    if args.live and not model.strip():
        print(
            json.dumps(
                {"verification": "UNVERIFIED", "reason": "missing_explicit_model"}
            )
        )
        return 2
    runtime = ResearchRuntime(args.topics, fault=args.fault)
    with tempfile.TemporaryDirectory(prefix="shop-research-") as cwd:
        options = build_options(
            runtime, cwd, model if args.live else "offline-test-model"
        )
        if args.live:
            prompt = (
                "Investigate these requested topics as of "
                + runtime.as_of
                + ": "
                + ", ".join(runtime.topics)
                + ". Explain any unresolved evidence without choosing a disputed policy."
            )
            stream = query(prompt=prompt, options=options)
        else:
            from .fixtures import authored_stream

            stream = authored_stream(runtime, options)
        try:
            async with asyncio.timeout(120):
                result = await consume(stream, runtime)
        except TimeoutError:
            result = {
                "status": "unverified",
                "reason": "time_limit",
                "coverage": runtime.coverage(),
            }
    print(
        json.dumps(
            {
                "verification": "LIVE_OBSERVATIONS"
                if args.live
                else "AUTHORED_SDK_EVENTS_REAL_LOCAL_TOOLS",
                "result": result,
                "events": runtime.events,
            },
            indent=2,
        )
    )
    return 0 if result.get("status") == "observed_workflow" else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
