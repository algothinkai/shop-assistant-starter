"""Supplied structural scanner and immutable local exports; not an AI agent."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from exercises.context.state import unique_object

TASKS = {"refund-code": "shop_assistant/business.py", "refund-tests": "tests/test_baseline.py"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bytes(root, relative):
    root=Path(root).resolve();path=(root/relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path outside exercise root")
    with path.open("rb") as stream:raw=stream.read(500001)
    if len(raw)>500000:raise ValueError("Exercise file too large")
    return raw


def parse(raw):
    return json.loads(raw,object_pairs_hook=unique_object)


def scan(root, task):
    if task not in TASKS:raise ValueError("Unknown task")
    filename=TASKS[task];raw=read_bytes(root,filename);source=raw.decode("utf-8");lines=source.splitlines()
    findings=[{"symbol":node.name,"line":node.lineno,"quote":lines[node.lineno-1]}
              for node in ast.walk(ast.parse(source)) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and "refund" in node.name]
    return {"version":1,"task":task,"method":"local_ast_scan_no_model",
            "observed_at":datetime.now(timezone.utc).isoformat(),"source":filename,"source_sha256":digest(raw),
            "findings":findings,"unknowns":["Syntactic matches do not prove runtime dependencies or test coverage."]}


def export(directory, value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False).encode();sha=digest(raw)
    if value.get("task") not in TASKS or len(raw)>500000:raise ValueError("Invalid export")
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    name=value["task"]+"-"+sha+".json";path=directory/name
    # Immutable content addressing: retries can reuse exactly identical bytes.
    try:
        with path.open("xb") as stream:stream.write(raw)
    except FileExistsError:
        if path.read_bytes()!=raw:raise ValueError("Conflicting immutable export")
    return {"file":name,"sha256":sha}
