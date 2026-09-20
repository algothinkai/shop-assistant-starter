"""Authored delegated reports, deterministic synthesis; no live agents."""
import argparse,json
from .fixtures import SOURCES,report
from .synthesis import synthesize


def main():
    p=argparse.ArgumentParser();p.add_argument("--scenario",choices=["conflict","historical","gap","empty","failure","partial"],default="conflict");args=p.parse_args()
    sources=SOURCES;topics=["returns"];as_of="2026-09-15"
    data={"returns":report("returns",["POL-RETURN-2026-09","FAQ-RETURNS-2026-09"])}
    if args.scenario=="historical":as_of="2026-08-15";data={"returns":report("returns",["POL-RETURN-2026-06","POL-RETURN-2026-09","FAQ-RETURNS-2026-09"])}
    if args.scenario=="gap":data={"returns":report("returns",["POL-RETURN-2026-09"])}
    if args.scenario in ("empty","failure"):data={"returns":report("returns",status="empty" if args.scenario=="empty" else "error")}
    if args.scenario=="partial":topics.append("shipping");data={"returns":report("returns",["POL-RETURN-2026-09"],"error"),"shipping":report("shipping",["POL-SHIP-2026-06"])}
    print(json.dumps({"verification":"AUTHORED_REPORTS_NO_AGENTS","result":synthesize(topics,as_of,data,sources)},indent=2))


if __name__=="__main__":main()
