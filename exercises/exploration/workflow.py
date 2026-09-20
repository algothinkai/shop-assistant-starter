"""Source-bound local recovery. Fresh syntax is not verified runtime behavior."""
import ast
from datetime import datetime
import re
from .artifacts import TASKS, read_bytes, digest, parse


def manifest(exports):
    if not isinstance(exports, dict) or not set(exports) <= set(TASKS):
        raise ValueError("Unknown exploration task")
    entries={task:None for task in TASKS}
    for task,entry in exports.items():
        if not isinstance(entry,dict) or set(entry)!={"file","sha256"}:
            raise ValueError("Invalid export entry")
        sha=entry["sha256"]
        if not isinstance(sha,str) or re.fullmatch(r"[0-9a-f]{64}",sha) is None:
            raise ValueError("Invalid export digest")
        if entry["file"] != task+"-"+sha+".json":
            raise ValueError("Invalid export filename")
        entries[task]=dict(entry)
    return {"version":1,"tasks":entries}


def recover(root, directory, index):
    if (not isinstance(index,dict) or set(index)!={"version","tasks"}
            or type(index["version"]) is not int or index["version"]!=1
            or not isinstance(index["tasks"],dict) or set(index["tasks"])!=set(TASKS)):
        raise ValueError("Invalid exploration manifest")
    normalized=manifest({k:v for k,v in index["tasks"].items() if v is not None})
    fresh={};rerun=[]
    for task,entry in normalized["tasks"].items():
        try:
            if entry is None:raise ValueError("Missing export")
            raw=read_bytes(directory,entry["file"])
            if digest(raw)!=entry["sha256"]:raise ValueError("Export changed")
            value=parse(raw)
            expected={"version","task","method","observed_at","source","source_sha256","findings","unknowns"}
            if not isinstance(value,dict) or set(value)!=expected:raise ValueError("Invalid export shape")
            if (type(value["version"]) is not int or value["version"]!=1 or value["task"]!=task
                    or value["source"]!=TASKS[task] or value["method"]!="local_ast_scan_no_model"):
                raise ValueError("Wrong source or method")
            stamp=datetime.fromisoformat(value["observed_at"])
            if stamp.tzinfo is None:raise ValueError("Missing timestamp zone")
            source=read_bytes(root,TASKS[task])
            if digest(source)!=value["source_sha256"]:raise ValueError("Source changed")
            source_text=source.decode("utf-8");lines=source_text.splitlines();findings=value["findings"]
            definitions={(n.name,n.lineno) for n in ast.walk(ast.parse(source_text))
                         if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
            if not isinstance(findings,list) or not 1<=len(findings)<=100:
                raise ValueError("No bounded findings")
            for finding in findings:
                if not isinstance(finding,dict) or set(finding)!={"symbol","line","quote"}:
                    raise ValueError("Invalid finding")
                line=finding["line"];symbol=finding["symbol"]
                if (type(line) is not int or not 1<=line<=len(lines) or not isinstance(symbol,str)
                        or not symbol.isidentifier() or "refund" not in symbol or (symbol,line) not in definitions
                        or lines[line-1]!=finding["quote"]):
                    raise ValueError("Unsupported source citation")
            unknowns=value["unknowns"]
            if (not isinstance(unknowns,list) or not 1<=len(unknowns)<=10
                    or any(not isinstance(u,str) or not 1<=len(u)<=500 for u in unknowns)):
                raise ValueError("Missing method limits")
            fresh[task]=value
        except (OSError,ValueError,TypeError,KeyError,SyntaxError):
            rerun.append(task)
    return {"status":"ready" if not rerun else "partial","fresh":fresh,"rerun":rerun}


def next_prompt(recovered, question):
    if (not isinstance(recovered,dict) or set(recovered)!={"status","fresh","rerun"}
            or recovered["status"] not in ("ready","partial") or not isinstance(recovered["fresh"],dict)
            or not isinstance(recovered["rerun"],list)
            or not isinstance(question,str) or not question.strip() or len(question)>1000):
        raise ValueError("Invalid next-phase context")
    fresh=recovered["fresh"];pending=recovered["rerun"]
    if (set(fresh)&set(pending) or set(fresh)|set(pending)!=set(TASKS)
            or len(pending)!=len(set(pending))
            or (recovered["status"]=="ready")!= (not pending)):
        raise ValueError("Inconsistent task states")
    sections=["VERIFIED SOURCE SNAPSHOTS (structural findings, not runtime proof)"]
    for task,value in fresh.items():
        sections.append(task+" | "+value["source_sha256"]+" | "+value["observed_at"])
        for item in value["findings"]:
            sections.append(f'{value["source"]}:{item["line"]} — {item["symbol"]}: {item["quote"]}')
        sections.append("Unknowns: "+"; ".join(value["unknowns"]))
    sections.extend(["RERUN BEFORE RELYING ON THESE TASKS: "+", ".join(pending),"NEXT QUESTION",question])
    prompt="\n".join(sections)
    if len(prompt)>20000:raise ValueError("Next-phase context exceeds local bound")
    return prompt
