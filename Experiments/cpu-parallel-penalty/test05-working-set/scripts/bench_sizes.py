"""Current prefix and native top-13 kernels across controlled active sizes."""
import argparse
import hashlib
import json
import math
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/"packing"),str(ROOT/"Experiments/cpu-parallel-penalty/test04-interference/scripts")]
from sqpack.fractional import generate
from workload import capture

SIZES=[256*1024,1*1024**2,2*1024**2,4*1024**2,8*1024**2,
       12*1024**2,16*1024**2,24*1024**2,32*1024**2]

def cpu():
    parts=Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(") ",1)[1].split()
    ticks=os.sysconf("SC_CLK_TCK")
    return (int(parts[11])+int(parts[12]))/ticks

def input_array(kind,bytes_,real):
    if kind=="prefix":
        side=int(math.sqrt(bytes_//8))
        source=real["diff"]
        if side<=source.shape[0]:return source[:side,:side].copy()
        repeats=math.ceil(side/source.shape[0])
        return np.tile(source,(repeats,repeats))[:side,:side].copy()
    length=bytes_//8
    source=real["flat"]
    if length<=source.size:return source[:length].copy()
    return np.resize(source,length).astype(np.float64,copy=False)

def worker(index,cpu_id,kind,array,gate,seconds,output):
    os.sched_setaffinity(0,{cpu_id})
    array=np.array(array,copy=True)  # production workers operate on distinct direction grids
    work=np.empty_like(array) if kind=="prefix" else None
    def op():
        if kind=="prefix":
            np.copyto(work,array)
            np.add.accumulate(work,axis=1,out=work)
            generate.accumulate_axis0(work)
            return float(work[-1,-1])
        return int(generate._least_finite_indices(array,13)[0])
    warm=op()
    gate.wait()
    gate.wait()
    before=cpu()
    start=time.perf_counter()
    calls=0
    last=warm
    while time.perf_counter()-start<seconds:
        last=op();calls+=1
    wall=time.perf_counter()-start
    used_cpu=cpu()-before
    assert last==warm,(last,warm)
    output[index]={"cpu_id":cpu_id,"calls":calls,"wall":wall,"cpu":used_cpu,
                   "wall_per_call":wall/calls,"cpu_per_call":used_cpu/calls,
                   "checksum":hashlib.sha256(array.tobytes()).hexdigest(),
                   "output":last}

def run(kind,bytes_,workers,seconds,sample,tag):
    real=capture()
    array=input_array(kind,bytes_,real)
    cpus=sorted(os.sched_getaffinity(0))[:workers]
    ctx=mp.get_context("fork")
    gate=ctx.Barrier(workers+1)
    with ctx.Manager() as manager:
        output=manager.dict()
        ps=[ctx.Process(target=worker,args=(i,cpus[i],kind,array,gate,seconds,output))
            for i in range(workers)]
        for p in ps:p.start()
        gate.wait()
        load={"loadavg":os.getloadavg(),
              "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
        start=time.perf_counter()
        gate.wait()
        for p in ps:
            p.join(timeout=seconds+30)
            assert p.exitcode==0,p.exitcode
        total_wall=time.perf_counter()-start
        records=[output[i] for i in range(workers)]
    assert all(x["checksum"]==records[0]["checksum"] and x["output"]==records[0]["output"] for x in records)
    assert 10<=min(x["wall"] for x in records)<=60
    result={"kind":kind,"requested_bytes":bytes_,"actual_bytes":array.nbytes,
            "shape":array.shape,"workers":workers,"sample":sample,"tag":tag,
            "target_seconds":seconds,"wall":total_wall,"load_before":load,
            "records":records,"median_wall_per_call":float(np.median([x["wall_per_call"] for x in records])),
            "median_cpu_per_call":float(np.median([x["cpu_per_call"] for x in records]))}
    raw=HERE.parent/"raw";raw.mkdir(parents=True,exist_ok=True)
    path=raw/f"{kind}-{bytes_}-w{workers}-{tag}-s{sample}.json"
    path.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"kind":kind,"bytes":bytes_,"workers":workers,
        "sample":sample,"ms_per_call":round(1000*result["median_cpu_per_call"],3),
        "wall":round(total_wall,2)}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--kind",choices=("prefix","top13"),required=True)
    p.add_argument("--bytes",type=int,required=True)
    p.add_argument("--workers",type=int,choices=(1,4,8,16),required=True)
    p.add_argument("--samples",type=int,default=1)
    p.add_argument("--seconds",type=float,default=10.5)
    p.add_argument("--tag",default="screen")
    a=p.parse_args()
    for sample in range(1,a.samples+1):run(a.kind,a.bytes,a.workers,a.seconds,sample,a.tag)

if __name__=="__main__":main()
