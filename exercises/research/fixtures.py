"""Authored research reports; neither an AI agent nor an external policy source."""
from copy import deepcopy
import json
from pathlib import Path

SOURCES=json.loads((Path(__file__).with_name("sources.json")).read_text())


def finding(source_id):
    source=next(s for s in SOURCES if s["id"]==source_id)
    key=next(iter(source["claims"]));claim=source["claims"][key]
    return {"source_id":source_id,"key":key,"value":deepcopy(claim["value"]),"quote":claim["quote"]}


def report(topic, ids=(), status="ok"):
    return {"topic":topic,"status":status,"attempts":[{"query":"Read dated "+topic+" sources","outcome":status}],
            "findings":[finding(i) for i in ids],
            "error":{"type":"timeout","retryable":True,"alternatives":["Retry this source later or ask a human for the policy copy."]} if status=="error" else None}
