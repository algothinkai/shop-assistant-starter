"""Default authored protocol probe; explicit optional billable SDK experiment."""
import argparse
import asyncio
import importlib.metadata
import json
import os
import tempfile
from claude_agent_sdk import query
from .fixtures import authored_query
from .probe import probe


async def run(live):
    model=os.environ.get("ANTHROPIC_MODEL","") if live else "offline-no-model"
    if not model:
        print(json.dumps({"verification":"UNVERIFIED","status":"missing_explicit_model"}))
        return 2
    with tempfile.TemporaryDirectory(prefix="shop-sessions-") as directory:
        try:
            async with asyncio.timeout(60):
                output=await probe(query if live else authored_query(),directory,model)
        except Exception:
            output={"status":"unverified","trace":[]}
        print(json.dumps({"verification":("OBSERVED_LIVE_SEQUENCE" if output["status"]=="observed_sequence" else "UNVERIFIED") if live else "OFFLINE_ONLY",
                          "sdk_version":importlib.metadata.version("claude-agent-sdk"), **output},indent=2))
        return 0 if output["status"]=="observed_sequence" else 1


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live",action="store_true",help="Potentially billable: up to four SDK calls, each2turns/$0.10; local auth and explicit model required")
    args=p.parse_args();raise SystemExit(asyncio.run(run(args.live)))


if __name__=="__main__": main()
