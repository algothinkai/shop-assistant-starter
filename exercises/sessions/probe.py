"""Bounded four-call experiment. Query is injected for explicit offline tests."""
import json
from .adapter import build_options, consume

BASE = {"case_code": "training-cobalt", "amount_cents": 7600}
ALTERNATIVE = {"case_code": "training-cobalt", "amount_cents": 7500}


async def probe(query, cwd, model):
    trace=[]
    parent=None
    steps=[("fresh", 'Remember these fictional case facts: case_code=training-cobalt; amount_cents=7600. Return only a JSON object with these two fields.', BASE),
           ("resume", 'Return only the case_code and amount_cents already recorded in this conversation as a JSON object. Do not guess missing facts.', BASE),
           ("fork", 'Explore an alternative in this branch only: set amount_cents to7500, keep the recorded case_code. Return only those two fields as JSON.', ALTERNATIVE),
           ("resume", 'Return only the current case_code and amount_cents already recorded in this original conversation as JSON. Do not guess missing facts.', BASE)]
    for action,prompt,expected in steps:
        options=build_options(action,parent,cwd,model)
        try:
            result=await consume(query(prompt=prompt,options=options))
        except Exception:
            result={"status":"failed","session_id":None,"text":None}
        sid=result["session_id"]
        relation=(sid is not None and (action=="fresh" or (sid != parent if action=="fork" else sid==parent)))
        try:
            observed=json.loads(result["text"]) if isinstance(result.get("text"),str) else None
        except ValueError:
            observed=None
        verified=result["status"]=="success" and relation and observed==expected
        trace.append({"action":action,"terminal":result["status"],"session_id":sid,
                      "id_relation_correct":relation,"facts_match":observed==expected})
        if not verified:
            return {"status":"unverified","trace":trace}
        if action=="fresh":parent=sid
    return {"status":"observed_sequence","trace":trace}
