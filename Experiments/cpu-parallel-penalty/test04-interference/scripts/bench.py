"""Pinned target vs pinned background phase interference, long timed samples."""
import argparse
import csv
import json
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/"packing"))
from workload import Operation,capture

LIB=HERE/"register.so"
EVENTS="instructions,cycles,ls_any_fills_from_sys.all_dram_io"

def cpu():
    s=Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(") ",1)[1].split()
    ticks=os.sysconf("SC_CLK_TCK")
    return (int(s[11])+int(s[12]))/ticks

def task(role,kind,cpu_id,data,barrier,stop,seconds,result,distinct_index=None):
    os.sched_setaffinity(0,{cpu_id})
    if distinct_index is not None and kind in ("prefix","slab","top13"):
        data=capture(18,(distinct_index*13+7)%181)
    op=Operation(kind,data,LIB)
    warm=op()
    barrier.wait()
    barrier.wait()
    if role=="background":
        while not stop.is_set():op()
        return
    start_cpu=cpu()
    start=time.perf_counter()
    count=0
    last=warm
    while time.perf_counter()-start<seconds:
        last=op()
        count+=1
    wall=time.perf_counter()-start
    used_cpu=cpu()-start_cpu
    stop.set()
    if kind in ("prefix","slab","top13","direction"):
        assert last==warm,(kind,last,warm)
    result["value"]={"wall":wall,"cpu":used_cpu,"calls":count,
                     "wall_per_call":wall/count,"cpu_per_call":used_cpu/count,
                     "warm_value":float(warm),"last_value":float(last),
                     "target_cpu":cpu_id}

def once(target,background,count,seconds,sample,tag,distinct_bg=False):
    data=capture()
    cpus=sorted(os.sched_getaffinity(0))
    assert count+1<=len(cpus)
    ctx=mp.get_context("fork")
    barrier=ctx.Barrier(count+2)
    stop=ctx.Event()
    with ctx.Manager() as manager:
        result=manager.dict()
        tasks=[ctx.Process(target=task,args=("target",target,cpus[0],data,
               barrier,stop,seconds,result))]
        tasks += [ctx.Process(target=task,args=("background",background,cpus[i+1],
                  data,barrier,stop,seconds,result,i if distinct_bg else None))
                  for i in range(count)]
        for p in tasks:p.start()
        barrier.wait()  # workers warm and ready
        raw=HERE.parent/"raw"
        raw.mkdir(parents=True,exist_ok=True)
        csv_path=raw/f"perf-{target}-{background}-n{count}-{tag}-s{sample}.csv"
        perf=subprocess.Popen(["perf","stat","-x,","--no-big-num","-e",EVENTS,
                               "-p",str(tasks[0].pid),"-o",str(csv_path)])
        time.sleep(.3)
        assert perf.poll() is None
        load={"loadavg":os.getloadavg(),
              "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
        barrier.wait()
        tasks[0].join(timeout=seconds+30)
        assert tasks[0].exitcode==0,tasks[0].exitcode
        for p in tasks[1:]:
            p.join(timeout=10)
            assert p.exitcode==0,p.exitcode
        perf.send_signal(signal.SIGINT)
        perf.wait(timeout=10)
        value=dict(result["value"])
    assert 10<=value["wall"]<=60,value
    counters={}
    for row in csv.reader(csv_path.read_text().splitlines()):
        if len(row)>4 and row[0] and not row[0].startswith('#'):
            counters[row[2]]={"count":float(row[0]),"running_percent":float(row[4])}
    assert all(x["running_percent"]>=99.5 for x in counters.values())
    value.update({"target":target,"background":background,"bg_count":count,
                  "sample":sample,"tag":tag,"load_before":load,
                  "distinct_background_inputs":distinct_bg,
                  "counters":counters,"ipc":counters["instructions"]["count"]/
                                      counters["cycles"]["count"]})
    path=raw/f"{target}-{background}-n{count}-{tag}-s{sample}.json"
    path.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({"target":target,"background":background,"bg":count,
                      "sample":sample,"wall_per_call":value["wall_per_call"],
                      "cpu_per_call":value["cpu_per_call"],"ipc":value["ipc"]}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--target",choices=("prefix","slab","top13","direction","register"),required=True)
    p.add_argument("--background",choices=("sleep","register","stream","prefix","slab","top13"),required=True)
    p.add_argument("--bg-count",type=int,choices=(0,4,8,14),required=True)
    p.add_argument("--seconds",type=float,default=10.5)
    p.add_argument("--samples",type=int,default=1)
    p.add_argument("--tag",default="screen")
    p.add_argument("--distinct-bg",action="store_true")
    a=p.parse_args()
    for sample in range(1,a.samples+1):
        once(a.target,a.background,a.bg_count,a.seconds,sample,a.tag,a.distinct_bg)

if __name__=="__main__":main()
