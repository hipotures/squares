"""Full-grid row-strip fusion preserving the exact prefix addition order."""
import argparse
import hashlib
import json
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

def prefix(grid,block_rows):
    if block_rows==0:
        np.add.accumulate(grid,axis=1,out=grid)
        generate.accumulate_axis0(grid)
        return
    for start in range(0,grid.shape[0],block_rows):
        end=min(start+block_rows,grid.shape[0])
        block=grid[start:end]
        np.add.accumulate(block,axis=1,out=block)
        generate.accumulate_axis0(grid[max(0,start-1):end])

def cpu():
    f=Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(") ",1)[1].split()
    t=os.sysconf("SC_CLK_TCK")
    return (int(f[11])+int(f[12]))/t

def worker(index,cpu_id,diff,block_rows,gate,seconds,output):
    os.sched_setaffinity(0,{cpu_id})
    diff=diff.copy()
    work=np.empty_like(diff)
    def one():
        np.copyto(work,diff)
        prefix(work,block_rows)
    one()
    h=hashlib.sha256(work.tobytes()).hexdigest()
    gate.wait();gate.wait()
    before=cpu();start=time.perf_counter();calls=0
    while time.perf_counter()-start<seconds:
        one();calls+=1
    wall=time.perf_counter()-start;used_cpu=cpu()-before
    assert hashlib.sha256(work.tobytes()).hexdigest()==h
    output[index]={"cpu_id":cpu_id,"calls":calls,"wall":wall,"cpu":used_cpu,
                   "wall_per_call":wall/calls,"cpu_per_call":used_cpu/calls,
                   "sha256":h}

def run(workers,block_rows,seconds,sample,tag):
    data=capture();diff=data["diff"]
    expected=np.empty_like(diff);np.copyto(expected,diff);prefix(expected,0)
    check=np.empty_like(diff);np.copyto(check,diff);prefix(check,block_rows)
    assert np.array_equal(check,expected)
    digest=hashlib.sha256(expected.tobytes()).hexdigest()
    ctx=mp.get_context('fork');gate=ctx.Barrier(workers+1)
    cpus=sorted(os.sched_getaffinity(0))[:workers]
    with ctx.Manager() as manager:
        output=manager.dict()
        ps=[ctx.Process(target=worker,args=(i,cpus[i],diff,block_rows,gate,seconds,output))
            for i in range(workers)]
        for p in ps:p.start()
        gate.wait()
        load={"loadavg":os.getloadavg(),
              "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
        t=time.perf_counter();gate.wait()
        for p in ps:
            p.join(timeout=seconds+30);assert p.exitcode==0,p.exitcode
        wall=time.perf_counter()-t
        records=[output[i] for i in range(workers)]
    assert all(x['sha256']==digest for x in records)
    assert 10<=min(x['wall'] for x in records)<=60
    result={"workers":workers,"block_rows":block_rows,"sample":sample,"tag":tag,
            "target_seconds":seconds,"batch_wall":wall,"grid_shape":diff.shape,
            "grid_bytes":diff.nbytes,"sha256":digest,"load_before":load,"records":records,
            "median_cpu_per_call":float(np.median([x['cpu_per_call'] for x in records])),
            "median_wall_per_call":float(np.median([x['wall_per_call'] for x in records]))}
    raw=HERE.parent/'raw';raw.mkdir(parents=True,exist_ok=True)
    (raw/f'tile-b{block_rows}-w{workers}-{tag}-s{sample}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"workers":workers,"block_rows":block_rows,"sample":sample,
                      "ms_per_call":round(1000*result['median_cpu_per_call'],3),
                      "batch_wall":round(wall,2)}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--workers',type=int,choices=(1,16),required=True)
    p.add_argument('--block-rows',type=int,choices=(0,32,64,128,256),required=True)
    p.add_argument('--seconds',type=float,default=20.)
    p.add_argument('--samples',type=int,default=3)
    p.add_argument('--tag',default='final')
    a=p.parse_args()
    for sample in range(1,a.samples+1):run(a.workers,a.block_rows,a.seconds,sample,a.tag)

if __name__=='__main__':main()
