"""Summarize long A/B/A guest replay under host vCPU pinning."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT.parent/"test01-counters/raw"

def stat(xs):
    return {"values":xs,"min":min(xs),"median":statistics.median(xs),
            "max":max(xs),"cv":statistics.pstdev(xs)/statistics.mean(xs)}

result={}
for tag in ("hostA","hostPinned","hostRestored"):
    paths=[SOURCE/f"proc-{tag}-w16-s{i}.json" for i in (1,2,3)]
    if not all(p.exists() for p in paths):continue
    samples=[json.loads(p.read_text()) for p in paths]
    result[tag]={"batch_wall":stat([s["batch_wall"] for s in samples]),
                 "wall":stat([s["wall_per_replay"] for s in samples])}
    for key in ("user","system","sched_wait","migrations","minor_faults"):
        result[tag][key]=stat([s["per_replay"][key] for s in samples])
    result[tag]["worker_cpu_median"]=result[tag]["user"]["median"]+result[tag]["system"]["median"]
if "hostA" in result and "hostPinned" in result:
    result["pinned_saving_vs_before"]={key:result["hostA"][key]["median"]-result["hostPinned"][key]["median"]
                                       for key in ("wall","user","system","sched_wait")}
if "hostRestored" in result:
    result["pinned_saving_vs_adjacent_control_median"]={key:
        statistics.median((result["hostA"][key]["median"],result["hostRestored"][key]["median"]))-
        result["hostPinned"][key]["median"] for key in ("wall","user","system","sched_wait")}
(ROOT/"processed").mkdir(exist_ok=True)
(ROOT/"processed/summary.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:{"wall":v["wall"]["median"],"worker_cpu":v["worker_cpu_median"]}
                  for k,v in result.items() if isinstance(v,dict) and isinstance(v.get("wall"),dict)},indent=2))
