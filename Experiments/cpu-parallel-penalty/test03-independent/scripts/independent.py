"""Fixed-share, preloaded, pinned processes; no pool, queue, or timed result transfer."""
import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "packing"))
from devtools import bench_colgen
from sqpack.fractional.generate import direction_net, placement_cells

DATA = ROOT / "Experiments/cpu-post-integration-profile/raw/current-states.npz"


def stats():
    parts = Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(") ",1)[1].split()
    ticks = os.sysconf("SC_CLK_TCK")
    return (int(parts[11])+int(parts[12]))/ticks


def checksums(placements):
    digests=[]
    for round_index, direction_index, found in placements:
        h = hashlib.sha256()
        h.update(round_index.to_bytes(2,"little"))
        h.update(direction_index.to_bytes(2,"little"))
        for mass, cu, cv, covers in found:
            h.update(np.asarray((mass,cu,cv),dtype=np.float64).tobytes())
            h.update(np.packbits(covers).tobytes())
        digests.append((round_index,direction_index,h.hexdigest()))
    return digests


def worker(index, n, cpu, gate, warmtimes, repeats, output, weights, points,
           membership, directions, outer, side):
    os.sched_setaffinity(0, {cpu})
    share = tuple((j,d) for j,d in enumerate(directions) if j % n == index)
    def one(collect=False):
        values = []
        count = 0
        for r, orbit_weights in enumerate(weights):
            site_weights = orbit_weights[membership]
            for j, d in share:
                found = placement_cells(points,site_weights,d,outer,side,keep=3)
                count += len(found)
                if collect: values.append((r,j,found))
        return count, values
    t = time.perf_counter()
    count, values = one(True)
    warmtimes[index] = time.perf_counter()-t
    digests = checksums(values)
    gate.wait()  # ready after loading and warming
    gate.wait()  # common timed start
    before = stats()
    start = time.perf_counter()
    for _ in range(repeats.value):
        actual, _ = one()
        assert actual == count
    elapsed = time.perf_counter()-start
    cpu_time = stats()-before
    gate.wait()  # all workers finished, no result data exchanged
    output[index] = {"worker":index,"cpu":cpu,"directions":len(share),
                     "warm_seconds":warmtimes[index],"wall_seconds":elapsed,
                     "cpu_seconds":cpu_time,"placement_count":count,"digests":digests}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workers",type=int,choices=(1,2,4,8,16),required=True)
    p.add_argument("--samples",type=int,default=3)
    p.add_argument("--target",type=float,default=22.)
    p.add_argument("--perf",action="store_true")
    a=p.parse_args()
    stored=np.load(DATA)
    weights,points,membership=(stored[x] for x in ("weights","points","membership"))
    case=bench_colgen.Case(n=12,outer_side=Fraction(99,25))
    directions=direction_net(case.half_tangents())
    cpus=sorted(os.sched_getaffinity(0))[:a.workers]
    ctx=mp.get_context("fork")
    for sample in range(1,a.samples+1):
        gate=ctx.Barrier(a.workers+1)
        warmtimes=ctx.Array("d",a.workers)
        repeats=ctx.Value("i",0)
        with ctx.Manager() as manager:
            output=manager.dict()
            processes=[ctx.Process(target=worker,args=(i,a.workers,cpus[i],gate,
                warmtimes,repeats,output,weights,points,membership,directions,
                float(case.outer_side),float(case.square_side))) for i in range(a.workers)]
            for process in processes: process.start()
            gate.wait()  # all warm and ready
            repeats.value=max(1,math.ceil(a.target/max(warmtimes)))
            perf=None
            if a.perf:
                csv_path=HERE.parent/"raw"/f"independent-perf-w{a.workers}-s{sample}.csv"
                csv_path.parent.mkdir(parents=True,exist_ok=True)
                perf=subprocess.Popen(["perf","stat","-x,","--no-big-num",
                    "-e","instructions,cycles,ls_any_fills_from_sys.all_dram_io",
                    "-p",','.join(str(x.pid) for x in processes),"-o",str(csv_path)])
                time.sleep(.3)
                assert perf.poll() is None
            load={"loadavg":os.getloadavg(),
                  "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
            t=time.perf_counter()
            gate.wait()
            gate.wait()
            wall=time.perf_counter()-t
            if perf:
                perf.send_signal(signal.SIGINT)
                perf.wait(timeout=10)
            for process in processes:
                process.join()
                assert process.exitcode==0
            data=[output[i] for i in range(a.workers)]
        assert 10 <= wall <= 60,wall
        canonical=sorted(item for part in data for item in part["digests"])
        assert len(canonical)==23*181
        digest=hashlib.sha256(''.join(x[2] for x in canonical).encode()).hexdigest()
        result={"workers":a.workers,"sample":sample,"repeats":repeats.value,
                "batch_wall":wall,"wall_per_replay":wall/repeats.value,
                "cpu_per_replay":sum(x["cpu_seconds"] for x in data)/repeats.value,
                "load_before":load,"canonical_sha256":digest,"perf":a.perf,
                "workers_data":[{k:v for k,v in x.items() if k!="digests"} for x in data]}
        stem="independent-perf" if a.perf else "independent"
        dest=HERE.parent/"raw"/f"{stem}-w{a.workers}-s{sample}.json"
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps({"workers":a.workers,"sample":sample,"repeats":repeats.value,
                          "wall":round(result["wall_per_replay"],4),
                          "cpu":round(result["cpu_per_replay"],4)}),flush=True)

if __name__=="__main__":main()
