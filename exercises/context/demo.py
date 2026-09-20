"""Authored conversation, real local order read, actual on-disk case recovery."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from shop_assistant.business import ShopService, FIXTURES
from .state import new_case, save_snapshot
from .workflow import record_fact, trim_order, build_context, recover


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--scenario",choices=["resume","conflict","stale","corrupt"],default="resume")
    args=parser.parse_args()
    with tempfile.TemporaryDirectory() as d:
        shop=ShopService(Path(d)/"shop")
        raw=shop.get_order("O-1003");trimmed=trim_order(raw)
        state=new_case("case-1003")
        for field,value in [("order_id",raw["id"]),("amount_cents",raw["total_cents"]),("delivered_on",raw["delivered_on"]),("customer_expectation","Replacement by 2026-09-25, not a refund")]:
            state=record_fact(state,"damaged-kettle",field,value,"fixture:orders/O-1003" if field != "customer_expectation" else "authored:turn-1","2026-09-20T12:00:00+00:00")
        if args.scenario=="conflict":
            state=record_fact(state,"damaged-kettle","amount_cents",7500,"authored:customer-claim","2026-09-20T12:01:00+00:00")
        fingerprints={n:hashlib.sha256((FIXTURES/f"{n}.json").read_bytes()).hexdigest() for n in ["orders","policies"]}
        path=Path(d)/"case.json";save_snapshot(path,state,fingerprints)
        current=dict(fingerprints)
        if args.scenario=="stale": current["policies"]="changed-for-exercise"
        if args.scenario=="corrupt":path.write_text("{incomplete")
        try:
            restored=recover(path,current)
            context=build_context(restored["case"],[{"role":"user","content":"Check my replacement request."}],"Customer requested help") if restored["case"] is not None else None
            output={"verification":"LOCAL_NO_MODEL","recovery":restored,"context":context,"trimmed_order":trimmed,"ledger":shop.ledger()}
        except ValueError:
            output={"verification":"LOCAL_NO_MODEL","status":"invalid_snapshot","ledger":shop.ledger()}
        print(json.dumps(output,indent=2))
        return 1 if output.get("status")=="invalid_snapshot" else 0


if __name__=="__main__":
    raise SystemExit(main())
