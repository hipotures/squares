"""Long current separation replay with per-worker /proc CPU and schedstat."""
import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "packing"), str(ROOT / "Experiments/cpu-chunk-integration")]
from devtools import bench_colgen
from sqpack.fractional.generate import direction_net
import replay

DATA = ROOT / "Experiments/cpu-post-integration-profile/raw/current-states.npz"
TICKS = os.sysconf("SC_CLK_TCK")


def proc(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    sched = list(map(int, Path(f"/proc/{pid}/schedstat").read_text().split()))
    status = Path(f"/proc/{pid}/status").read_text().splitlines()
    vals = {}
    for line in status:
        if line.startswith(("voluntary_ctxt_switches:", "nonvoluntary_ctxt_switches:")):
            key, value = line.split(":", 1)
            vals[key] = int(value.strip())
    sched_text = Path(f"/proc/{pid}/sched").read_text().splitlines()
    migrations = next(int(line.split(":",1)[1].strip()) for line in sched_text
                      if line.strip().startswith("se.nr_migrations"))
    return {"user": int(fields[11])/TICKS, "system": int(fields[12])/TICKS,
            "minor_faults": int(fields[7]), "migrations": migrations,
            "sched_run": sched[0]/1e9, "sched_wait": sched[1]/1e9,
            **vals}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--workers", type=int, choices=(1,2,4,8,16), required=True)
    p.add_argument("--samples", type=int, default=3)
    p.add_argument("--target", type=float, default=22)
    p.add_argument("--tag", default="")
    a = p.parse_args()
    stored = np.load(DATA)
    weights, points, membership = (stored[x] for x in ("weights", "points", "membership"))
    case = bench_colgen.Case(n=12, outer_side=Fraction(99,25))
    directions = direction_net(case.half_tangents())
    pool = ProcessPoolExecutor(max_workers=a.workers) if a.workers > 1 else None
    try:
        params = (weights, points, membership, directions,
                  float(case.outer_side), float(case.square_side), pool)
        def run():
            value = replay.replay(*params)
            assert np.array_equal(value.pop("row_directions"), stored["directions"])
            assert np.array_equal(value.pop("row_centres"), stored["centres"])
            return value
        warm = run()
        repeats = max(1, math.ceil(a.target/warm["wall_seconds"]))
        pids = [p.pid for p in pool._processes.values()] if pool else [os.getpid()]
        for sample in range(1,a.samples+1):
            before = {pid: proc(pid) for pid in pids}
            load = replay.load()
            t = time.perf_counter()
            runs = [run() for _ in range(repeats)]
            wall = time.perf_counter()-t
            after = {pid: proc(pid) for pid in pids}
            assert 10 <= wall <= 60, wall
            totals = {k:sum(after[pid][k]-before[pid][k] for pid in pids)/repeats
                      for k in before[pids[0]]}
            output = {"workers":a.workers,"sample":sample,"repeats":repeats,
                      "batch_wall":wall,"wall_per_replay":wall/repeats,
                      "per_replay":totals,"load_before":load,"pids":pids,
                      "affinity":{str(pid):sorted(os.sched_getaffinity(pid)) for pid in pids},
                      "warmup":warm["wall_seconds"],"replays":runs}
            dest = HERE.parent/"raw"/f"proc{a.tag}-w{a.workers}-s{sample}.json"
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_text(json.dumps(output,indent=2)+"\n")
            print(json.dumps({"workers":a.workers,"sample":sample,
                              "wall":round(wall/repeats,4),
                              "cpu":round(totals["user"]+totals["system"],4),
                              "wait":round(totals["sched_wait"],4)}),flush=True)
    finally:
        if pool: pool.shutdown()

if __name__ == "__main__": main()
