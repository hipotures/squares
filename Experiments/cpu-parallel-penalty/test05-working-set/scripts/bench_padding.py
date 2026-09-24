"""Same logical full grid with controlled physical row stride."""
import argparse
import ctypes
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

LIB=ctypes.CDLL(str(HERE/"prefix_stride.so"))
FN=LIB.prefix_axis0_stride
FN.argtypes=[ctypes.c_void_p,ctypes.c_size_t,ctypes.c_size_t,ctypes.c_size_t]
FN.restype=None

def run_one(work,diff):
    np.copyto(work,diff)
    np.add.accumulate(work,axis=1,out=work)
    FN(work.ctypes.data,work.shape[0],work.shape[1],work.strides[0]//8)

def cpu():
    p=Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(") ",1)[1].split()
    t=os.sysconf("SC_CLK_TCK")
    return (int(p[11])+int(p[12]))/t

def worker(index,cpu_id,diff,pad,gate,seconds,output):
    os.sched_setaffinity(0,{cpu_id})
    diff=diff.copy()
    raw=np.empty((diff.shape[0],diff.shape[1]+pad),dtype=np.float64)
    work=raw[:,:diff.shape[1]]
    run_one(work,diff)
    h=hashlib.sha256(work.tobytes()).hexdigest()
    gate.wait();gate.wait()
    before=cpu();start=time.perf_counter();calls=0
    while time.perf_counter()-start<seconds:
        run_one(work,diff);calls+=1
    wall=time.perf_counter()-start;used_cpu=cpu()-before
    assert hashlib.sha256(work.tobytes()).hexdigest()==h
    output[index]={"cpu_id":cpu_id,"calls":calls,"wall":wall,"cpu":used_cpu,
                   "wall_per_call":wall/calls,"cpu_per_call":used_cpu/calls,"sha256":h}

def run(workers,pad,seconds,sample,tag):
    diff=capture()["diff"]
    reference=diff.copy()
    np.add.accumulate(reference,axis=1,out=reference)
    generate.accumulate_axis0(reference)
    raw=np.empty((diff.shape[0],diff.shape[1]+pad),dtype=np.float64)
    work=raw[:,:diff.shape[1]]
    run_one(work,diff)
    assert np.array_equal(work,reference)
    digest=hashlib.sha256(reference.tobytes()).hexdigest()
    ctx=mp.get_context('fork');gate=ctx.Barrier(workers+1)
    cpus=sorted(os.sched_getaffinity(0))[:workers]
    with ctx.Manager() as manager:
        output=manager.dict()
        ps=[ctx.Process(target=worker,args=(i,cpus[i],diff,pad,gate,seconds,output))
            for i in range(workers)]
        for p in ps:p.start()
        gate.wait();load={"loadavg":os.getloadavg(),
                          "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
        t=time.perf_counter();gate.wait()
        for p in ps:
            p.join(timeout=seconds+30);assert p.exitcode==0,p.exitcode
        batch=time.perf_counter()-t
        records=[output[i] for i in range(workers)]
    assert all(x['sha256']==digest for x in records)
    assert 10<=min(x['wall'] for x in records)<=60
    result={"workers":workers,"padding_columns":pad,"sample":sample,"tag":tag,
            "grid_shape":diff.shape,"logical_bytes":diff.nbytes,
            "physical_row_bytes":(diff.shape[1]+pad)*8,"batch_wall":batch,
            "sha256":digest,"load_before":load,"records":records,
            "median_cpu_per_call":float(np.median([x['cpu_per_call'] for x in records]))}
    rawdir=HERE.parent/'raw';rawdir.mkdir(parents=True,exist_ok=True)
    (rawdir/f'padding-p{pad}-w{workers}-{tag}-s{sample}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"workers":workers,"pad":pad,"sample":sample,
                      "ms_per_call":round(1000*result['median_cpu_per_call'],3),
                      "batch_wall":round(batch,2)}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--workers',type=int,choices=(1,16),required=True)
    p.add_argument('--padding',type=int,choices=(0,4,32,64,256),required=True)
    p.add_argument('--seconds',type=float,default=10.5)
    p.add_argument('--samples',type=int,default=1)
    p.add_argument('--tag',default='screen')
    a=p.parse_args()
    for sample in range(1,a.samples+1):run(a.workers,a.padding,a.seconds,sample,a.tag)

if __name__=='__main__':main()
