"""Perf attach to warm replay workers for three long timed samples per count."""
import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/"packing"),str(ROOT/"Experiments/cpu-chunk-integration")]
from devtools import bench_colgen
from sqpack.fractional.generate import direction_net
import replay
from bench_proc import proc

DATA=ROOT/"Experiments/cpu-post-integration-profile/raw/current-states.npz"
EVENTS="instructions,cycles,ls_any_fills_from_sys.all_dram_io,task-clock,context-switches,cpu-migrations,page-faults"

def vcpu_ticks():
    return {line.split()[0]:list(map(int,line.split()[1:]))
            for line in Path('/proc/stat').read_text().splitlines()
            if line.startswith('cpu') and line[3:4].isdigit()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workers",type=int,choices=(1,2,4,8,16),required=True)
    p.add_argument("--samples",type=int,default=3)
    p.add_argument("--sample-start",type=int,default=1)
    p.add_argument("--target",type=float,default=22.)
    p.add_argument("--events",default=EVENTS)
    p.add_argument("--tag",default="")
    a=p.parse_args()
    stored=np.load(DATA)
    weights,points,membership=(stored[x] for x in ("weights","points","membership"))
    case=bench_colgen.Case(n=12,outer_side=Fraction(99,25))
    directions=direction_net(case.half_tangents())
    pool=ProcessPoolExecutor(max_workers=a.workers) if a.workers>1 else None
    try:
        params=(weights,points,membership,directions,float(case.outer_side),
                float(case.square_side),pool)
        def run():
            value=replay.replay(*params)
            assert np.array_equal(value.pop("row_directions"),stored["directions"])
            assert np.array_equal(value.pop("row_centres"),stored["centres"])
            return value
        warm=run()
        repeats=max(1,math.ceil(a.target/warm["wall_seconds"]))
        pids=[p.pid for p in pool._processes.values()] if pool else [os.getpid()]
        for sample in range(a.sample_start,a.sample_start+a.samples):
            raw=HERE.parent/"raw"
            raw.mkdir(parents=True,exist_ok=True)
            perf_path=raw/f"perf{a.tag}-w{a.workers}-s{sample}.csv"
            perf=subprocess.Popen(["perf","stat","-x,","--no-big-num", "-e",a.events,
                                    "-p",",".join(map(str,pids)),"-o",str(perf_path)])
            time.sleep(0.3)  # allow perf to attach before the timed region
            if perf.poll() is not None:
                raise RuntimeError(f"perf failed before sample: {perf_path.read_text()}")
            before={pid:proc(pid) for pid in pids}
            vcpu_before=vcpu_ticks()
            load=replay.load()
            t=time.perf_counter()
            runs=[run() for _ in range(repeats)]
            wall=time.perf_counter()-t
            after={pid:proc(pid) for pid in pids}
            vcpu_after=vcpu_ticks()
            perf.send_signal(signal.SIGINT)
            perf.wait(timeout=10)
            assert 10<=wall<=60,wall
            totals={k:sum(after[pid][k]-before[pid][k] for pid in pids)/repeats
                    for k in before[pids[0]]}
            output={"workers":a.workers,"sample":sample,"repeats":repeats,
                    "batch_wall":wall,"wall_per_replay":wall/repeats,
                    "per_replay":totals,"load_before":load,"perf_events":a.events,
                    "perf_raw":str(perf_path),"pids":pids,"replays":runs,
                    "worker_affinity":{str(pid):sorted(os.sched_getaffinity(pid)) for pid in pids},
                    "vcpu_ticks_before":vcpu_before,"vcpu_ticks_after":vcpu_after}
            dest=raw/f"perf{a.tag}-w{a.workers}-s{sample}.json"
            dest.write_text(json.dumps(output,indent=2)+"\n")
            print(json.dumps({"workers":a.workers,"sample":sample,
                "wall":round(wall/repeats,4),"cpu":round(totals["user"]+totals["system"],4),
                "wait":round(totals["sched_wait"],4),
                "perf_tail":perf_path.read_text().splitlines()[-2:]}),flush=True)
    finally:
        if pool: pool.shutdown()

if __name__=="__main__":main()
