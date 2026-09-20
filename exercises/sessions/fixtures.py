"""Authored SDK messages, never presented as model or transcript evidence."""
import json
from claude_agent_sdk import ResultMessage

PARENT="12345678-1234-4234-8234-123456789abc"
CHILD="12345678-1234-4234-8234-123456789abd"


def result(sid=PARENT, subtype="success", text=None, **kwargs):
    return ResultMessage(subtype=subtype,duration_ms=1,duration_api_ms=0,is_error=subtype!="success",
                         num_turns=1,session_id=sid,result=text,**kwargs)


def authored_query():
    count=0
    async def query(*,prompt,options):
        nonlocal count
        count+=1
        yield result(CHILD if count==3 else PARENT,text=json.dumps({"case_code":"training-cobalt","amount_cents":7500 if count==3 else 7600}))
    return query
