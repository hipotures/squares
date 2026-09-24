"""Summarize retained proc and perf long replay samples, including CV."""
import csv
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/"raw"

def summary(values):
    return {"values":values,"min":min(values),"median":statistics.median(values),
            "max":max(values),"cv":statistics.pstdev(values)/statistics.mean(values)}

def perf(path):
    result={}
    for row in csv.reader(path.read_text().splitlines()):
        if len(row)<5 or not row[0] or row[0].startswith("#"):continue
        try: value=float(row[0])
        except ValueError:continue
        result[row[2]]={"count":value,"unit":row[1],"running_percent":float(row[4])}
    return result

out={"workers":{}}
for workers in (1,2,4,8,16):
    proc=[json.loads((RAW/f"proc-w{workers}-s{i}.json").read_text()) for i in (1,2,3)]
    ps=[json.loads((RAW/f"perf-w{workers}-s{i}.json").read_text()) for i in (1,2,3)]
    counters=[perf(RAW/f"perf-w{workers}-s{i}.csv") for i in (1,2,3)]
    record={"proc":{},"perf":{},"perf_running_percent":{}}
    for key in ("wall_per_replay", "batch_wall"):
        record["proc"][key]=summary([x[key] for x in proc])
        record["perf"][key]=summary([x[key] for x in ps])
    for key in proc[0]["per_replay"]:
        record["proc"][key]=summary([x["per_replay"][key] for x in proc])
        record["perf"][key]=summary([x["per_replay"][key] for x in ps])
    for event in counters[0]:
        record["perf"][event]=summary([c[event]["count"]/p["repeats"]
                                      for c,p in zip(counters,ps)])
        record["perf_running_percent"][event]=[c[event]["running_percent"] for c in counters]
    record["derived"]={
        "worker_cpu":record["perf"]["user"]["median"]+record["perf"]["system"]["median"],
        "ipc":record["perf"]["instructions"]["median"]/record["perf"]["cycles"]["median"],
        "instructions_per_direction":record["perf"]["instructions"]["median"]/(23*181),
        "cycles_per_direction":record["perf"]["cycles"]["median"]/(23*181),
        "dram_fills_per_second":record["perf"]["ls_any_fills_from_sys.all_dram_io"]["median"]/
                                  record["perf"]["wall_per_replay"]["median"],
    }
    out["workers"][str(workers)]=record
base=out["workers"]["1"]
for w,record in out["workers"].items():
    record["relative_to_one"]={key:record["perf"][key]["median"]/base["perf"][key]["median"]
        for key in ("wall_per_replay","instructions","cycles","ls_any_fills_from_sys.all_dram_io",
                    "sched_wait","system")}
    record["relative_to_one"]["worker_cpu"]=record["derived"]["worker_cpu"]/base["derived"]["worker_cpu"]
(ROOT/"processed").mkdir(exist_ok=True)
(ROOT/"processed/summary.json").write_text(json.dumps(out,indent=2)+"\n")
for w,record in out["workers"].items():
    print(w,round(record["perf"]["wall_per_replay"]["median"],3),
          round(record["derived"]["worker_cpu"],3),
          round(record["relative_to_one"]["instructions"],3),
          round(record["relative_to_one"]["cycles"],3),
          round(record["derived"]["ipc"],3),
          round(record["perf"]["sched_wait"]["median"],3))
