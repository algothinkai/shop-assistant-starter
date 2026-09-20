"""One bounded structural investigation in its own process; no model or network."""
import argparse,json
from .artifacts import TASKS,scan,export


def main():
    p=argparse.ArgumentParser();p.add_argument("task",choices=TASKS);p.add_argument("root");p.add_argument("output")
    a=p.parse_args()
    try:result=export(a.output,scan(a.root,a.task))
    except (OSError,ValueError,SyntaxError):
        print(json.dumps({"task":a.task,"status":"failed"}));return 1
    print(json.dumps({"task":a.task,"status":"exported","entry":result}));return 0


if __name__=="__main__":raise SystemExit(main())
