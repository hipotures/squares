"""Summarize fixed-share controls and verify one canonical checksum."""
import csv
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/"raw"

def summarize(xs):
    return {"values":xs,"min":min(xs),"median":statistics.median(xs),
            "max":max(xs),"cv":statistics.pstdev(xs)/statistics.mean(xs)}

out={"workers":{},"perf":{}}
hashes=set()
for workers in (1,2,4,8,16):
    samples=[json.loads((RAW/f"independent-w{workers}-s{i}.json").read_text())
             for i in (1,2,3)]
    hashes.update(x["canonical_sha256"] for x in samples)
    out["workers"][str(workers)]={
        "wall_per_replay":summarize([x["wall_per_replay"] for x in samples]),
        "cpu_per_replay":summarize([x["cpu_per_replay"] for x in samples]),
        "batch_wall":summarize([x["batch_wall"] for x in samples]),
        "checksum":samples[0]["canonical_sha256"]}
assert len(hashes)==1,hashes
for workers in (1,16):
    samples=[json.loads((RAW/f"independent-perf-w{workers}-s{i}.json").read_text())
             for i in (1,2,3)]
    hashes.update(x["canonical_sha256"] for x in samples)
    counter=[]
    for sample,x in enumerate(samples,1):
        rows=list(csv.reader((RAW/f"independent-perf-w{workers}-s{sample}.csv").read_text().splitlines()))
        counter.append({row[2]:float(row[0])/x["repeats"] for row in rows
                        if len(row)>4 and row[0] and not row[0].startswith('#')})
    out["perf"][str(workers)]={key:summarize([x[key] for x in counter])
                               for key in counter[0]}
assert len(hashes)==1,hashes
out["checksum"]=next(iter(hashes))
one=out["workers"]["1"]
for workers,x in out["workers"].items():
    x["relative_cpu"]=x["cpu_per_replay"]["median"]/one["cpu_per_replay"]["median"]
    x["speedup"]=one["wall_per_replay"]["median"]/x["wall_per_replay"]["median"]
for key in out["perf"]["1"]:
    out["perf"]["16"][key]["relative_to_one"]=out["perf"]["16"][key]["median"]/out["perf"]["1"][key]["median"]
(ROOT/"processed").mkdir(exist_ok=True)
(ROOT/"processed/summary.json").write_text(json.dumps(out,indent=2)+"\n")
for workers,x in out["workers"].items():
    print(workers,round(x["wall_per_replay"]["median"],3),
          round(x["cpu_per_replay"]["median"],3),round(x["relative_cpu"],3))
