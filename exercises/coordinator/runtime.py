"""Read-only fictional source service. No model, ledger or external fetch here."""

from copy import deepcopy
import json
from claude_agent_sdk import tool, create_sdk_mcp_server
from exercises.research.fixtures import SOURCES
from exercises.research.synthesis import synthesize, day

PREFIX = "mcp__research__"
TOPICS = ("returns", "shipping")


def response(value, error=False):
    return {"content": [{"type": "text", "text": json.dumps(value)}], "isError": error}


class ResearchRuntime:
    def __init__(self, topics, as_of="2026-09-15", fault="none"):
        if (
            not isinstance(topics, list)
            or not topics
            or len(set(topics)) != len(topics)
            or any(t not in TOPICS for t in topics)
            or fault not in ("none", "transient", "persistent")
        ):
            raise ValueError("Choose distinct known topics and a documented fault")
        day(as_of)
        self.topics = topics[:]
        self.as_of = as_of
        self.fault = fault
        self.sources = deepcopy(SOURCES)
        self.catalog = {s["id"]: s for s in self.sources}
        self.reads = {}
        self.reports = {}
        self.events = []
        self.revision = 0
        self.inspected = -1

    def scope(self, topic):
        return [s["id"] for s in self.sources if s["topic"] == topic]

    def context(self, topic, goal):
        return {
            "goal": goal,
            "topic": topic,
            "as_of": self.as_of,
            "source_ids": self.scope(topic),
            "prior_report": deepcopy(self.reports.get(topic)),
            "coverage": self.coverage()["topics"][topic],
            "constraints": "Fictional sources; no refund authority; keep dates and conflicting values.",
        }

    def coverage(self):
        return synthesize(self.topics, self.as_of, self.reports, self.sources)

    def investigate(self, topic, source_ids):
        if (
            topic not in self.topics
            or not isinstance(source_ids, list)
            or len(source_ids) > 3
            or any(
                not isinstance(s, str) or s not in self.scope(topic) for s in source_ids
            )
            or len(set(source_ids)) != len(source_ids)
        ):
            raise ValueError("Investigation exceeds assigned topic")
        # Each selected source receives at most two local attempts per invocation.
        # The coordinator chooses any later re-delegation; this is not a fixed pipeline.
        for sid in source_ids:
            attempts = []
            for attempt in range(1, 3):
                fail = sid == "FAQ-RETURNS-2026-09" and (
                    self.fault == "persistent"
                    or (self.fault == "transient" and attempt == 1)
                )
                attempts.append(
                    {"attempt": attempt, "outcome": "timeout" if fail else "ok"}
                )
                if not fail:
                    break
            self.reads[sid] = {"ok": not fail, "attempts": attempts}
            self.events.append(
                {
                    "event": "source_read",
                    "source_id": sid,
                    "topic": topic,
                    "attempts": deepcopy(attempts),
                    "fault_mode": self.fault,
                }
            )
        findings = []
        failed = []
        for sid, read in self.reads.items():
            if self.catalog[sid]["topic"] != topic:
                continue
            if not read["ok"]:
                failed.append(sid)
                continue
            findings.extend(
                {"source_id": sid, "key": key, **deepcopy(claim)}
                for key, claim in self.catalog[sid]["claims"].items()
            )
        status = "error" if failed else "ok" if findings else "empty"
        report = {
            "topic": topic,
            "status": status,
            "attempts": [
                {
                    "query": "Read selected sources: " + ", ".join(source_ids),
                    "outcome": status,
                }
            ],
            "findings": findings,
            "error": None
            if not failed
            else {
                "type": "timeout",
                "retryable": True,
                "alternatives": [
                    "Retry only failed sources later: " + ", ".join(failed),
                    "Ask a human for the dated policy copy.",
                ],
            },
        }
        self.reports[topic] = report
        self.revision += 1
        self.events.append(
            {
                "event": "report",
                "topic": topic,
                "revision": self.revision,
                "failed_sources": failed,
            }
        )
        return {
            "report": deepcopy(report),
            "source_metadata": [
                deepcopy(s)
                for s in self.sources
                if s["id"] in self.reads and s["topic"] == topic
            ],
            "read_attempts": [
                deepcopy(e)
                for e in self.events
                if e["event"] == "source_read" and e["topic"] == topic
            ],
        }

    def inspect(self):
        self.inspected = self.revision
        result = self.coverage()
        self.events.append(
            {
                "event": "coverage",
                "revision": self.revision,
                "statuses": {k: v["coverage"] for k, v in result["topics"].items()},
            }
        )
        return result

    def server(self):
        @tool(
            "investigate",
            "Read selected fictional policy source IDs for one assigned topic. Locally retries transient timeouts once, preserves partial findings and dates. Use returned failed IDs for any targeted later investigation.",
            {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": list(TOPICS)},
                    "source_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "maxItems": 3,
                    },
                },
                "required": ["topic", "source_ids"],
                "additionalProperties": False,
            },
        )
        async def investigate(args):
            try:
                return response(self.investigate(args["topic"], args["source_ids"]))
            except (ValueError, KeyError, TypeError):
                return response({"error": "invalid_scope"}, True)

        @tool(
            "inspect_coverage",
            "Coordinator only: inspect current source-linked coverage, conflicts, partial failures and exact missing claims. No policy decision or payment action.",
            {"type": "object", "properties": {}, "additionalProperties": False},
        )
        async def inspect(_args):
            return response(self.inspect())

        self.handlers = {
            "investigate": investigate.handler,
            "inspect_coverage": inspect.handler,
        }
        return create_sdk_mcp_server(
            name="research", version="1.0.0", tools=[investigate, inspect]
        )
