"""Parallel real structural workers, persisted manifest, then recovery in a new process."""
import argparse,json,subprocess,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .artifacts import TASKS,parse
from .workflow import manifest,recover,next_prompt


def main():
    p=argparse.ArgumentParser();p.add_argument("--scenario",choices=["fresh","changed","interrupted","corrupt"],default="fresh")
    p.add_argument("--recover",nargs=2,metavar=("ROOT","OUTPUT"));a=p.parse_args()
    if a.recover:
        root,out=map(Path,a.recover);index=parse((out/"manifest.json").read_bytes());result=recover(root,out,index)
        print(json.dumps({"verification":"LOCAL_WORKERS_NO_MODEL","recovery":result,"next_prompt":next_prompt(result,"Which refund-related functions should the next investigation read?")},indent=2));return 0
    repository=Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="shop-exploration-") as d:
        root=Path(d)/"source";out=Path(d)/"exports";out.mkdir()
        for relative in TASKS.values():
            target=root/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((repository/relative).read_bytes())
        tasks=list(TASKS)[:1] if a.scenario=="interrupted" else list(TASKS)
        def work(task):
            run=subprocess.run([sys.executable,"-m","exercises.exploration.worker",task,str(root),str(out)],capture_output=True,text=True,timeout=15)
            return json.loads(run.stdout)
        with ThreadPoolExecutor(max_workers=2) as pool:observed=list(pool.map(work,tasks))
        entries={v["task"]:v["entry"] for v in observed if v.get("status")=="exported"}
        index=manifest(entries);(out/"manifest.json").write_text(json.dumps(index))
        if a.scenario=="changed":
            source=root/TASKS["refund-code"];source.write_text(source.read_text()+"\n# Changed after investigation\n")
        if a.scenario=="corrupt":(out/entries["refund-code"]["file"]).write_text("{broken")
        # New process reloads the saved index; parent memory is not the recovery source.
        recovered=subprocess.run([sys.executable,"-m","exercises.exploration.demo","--recover",str(root),str(out)],capture_output=True,text=True,timeout=15)
        if recovered.returncode:print(json.dumps({"status":"recovery_failed"}));return 1
        print(json.dumps({"worker_events":observed,**json.loads(recovered.stdout)},indent=2));return 0


if __name__=="__main__":raise SystemExit(main())
