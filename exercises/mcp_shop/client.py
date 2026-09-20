"""Actual stdio client helpers; never a model or Claude Code verification."""
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

ROOT = Path(__file__).resolve().parents[2]


def connect(profile, *flags):
    return Client(StdioServerParameters(command=sys.executable,
        args=["-m", "exercises.mcp_shop.server", "--profile", profile, *flags],
        cwd=ROOT, env={"PYTHONPATH": str(ROOT)}), read_timeout_seconds=10)


async def call_with_retry(client, name, arguments, *, max_attempts=2):
    if type(max_attempts) is not int or not 1 <= max_attempts <= 2:
        raise ValueError("Stage 3 retries are capped at two attempts")
    attempts = []
    for _ in range(max_attempts):
        response = await client.call_tool(name, arguments)
        attempts.append(response.model_dump(mode="json", by_alias=True))
        error = (response.structured_content or {}).get("error", {})
        if not response.is_error or error.get("isRetryable") is not True:
            break
    return response, attempts
