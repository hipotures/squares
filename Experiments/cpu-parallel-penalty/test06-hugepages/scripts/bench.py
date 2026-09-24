"""Same real full-grid prefix with verified normal vs THP-backed buffers."""
import argparse
import csv
import ctypes
import hashlib
import json
import mmap
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/"packing"),str(ROOT/"Experiments/cpu-parallel-penalty/test04-interference/scripts")]
from sqpack.fractional import generate
from workload import capture

HUGE=2*1024*1024

def map_array(shape,mode):
    bytes_=int(np.prod(shape))*8
    length=((bytes_+HUGE-1)//HUGE+2)*HUGE
    mapping=mmap.mmap(-1,length,flags=mmap.MAP_PRIVATE|mmap.MAP_ANONYMOUS,
                      prot=mmap.PROT_READ|mmap.PROT_WRITE)
    mapping.madvise(mmap.MADV_HUGEPAGE if mode=='huge' else mmap.MADV_NOHUGEPAGE)
    base=ctypes.addressof(ctypes.c_char.from_buffer(mapping))
    offset=(-base)%HUGE
    array=np.ndarray(shape,dtype=np.float64,buffer=mapping,offset=offset)
    return mapping,array

def smaps_for(address):
    lines=Path('/proc/self/smaps').read_text().splitlines()
    record=None
    for line in lines:
        bits=line.split()
        if bits and '-' in bits[0]:
            pair=bits[0].split('-',1)
            try: lo,hi=int(pair[0],16),int(pair[1],16)
            except ValueError:continue
            record={"range":bits[0],"fields":{}} if lo<=address<hi else None
        elif record is not None and ':' in line:
            key,value=line.split(':',1)
            record['fields'][key]=value.strip()
            if key=='VmFlags':break
    assert record is not None,address
    return record

def proc_metrics():
    f=Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(') ',1)[1].split()
    t=os.sysconf('SC_CLK_TCK')
    return {"user":int(f[11])/t,"system":int(f[12])/t,"minor_faults":int(f[7])}

def worker(index,cpu_id,diff,mode,gate,seconds,precheck,output):
    os.sched_setaffinity(0,{cpu_id})
    input_map,input_array=map_array(diff.shape,mode)
    output_map,work=map_array(diff.shape,mode)
    np.copyto(input_array,diff)
    work.fill(0)
    def one():
        np.copyto(work,input_array)
        np.add.accumulate(work,axis=1,out=work)
        generate.accumulate_axis0(work)
    one()
    digest=hashlib.sha256(work.tobytes()).hexdigest()
    maps={"input":smaps_for(input_array.ctypes.data),
          "output":smaps_for(work.ctypes.data)}
    precheck[index]=maps
    gate.wait();gate.wait()
    before=proc_metrics();start=time.perf_counter();calls=0
    while time.perf_counter()-start<seconds:
        one();calls+=1
    wall=time.perf_counter()-start;after=proc_metrics()
    used_cpu=after['user']+after['system']-before['user']-before['system']
    assert hashlib.sha256(work.tobytes()).hexdigest()==digest
    output[index]={"cpu_id":cpu_id,"calls":calls,"wall":wall,"cpu":used_cpu,
                   "cpu_per_call":used_cpu/calls,"wall_per_call":wall/calls,
                   "minor_faults":after['minor_faults']-before['minor_faults'],
                   "system_cpu":after['system']-before['system'],
                   "sha256":digest,"smaps_before":maps,
                   "smaps_after":{"input":smaps_for(input_array.ctypes.data),
                                  "output":smaps_for(work.ctypes.data)}}
    # Process exit releases both mappings after the post-timing smaps receipt.

def huge_kib(maps):
    return sum(int(maps[k]['fields'].get('AnonHugePages','0 kB').split()[0])
               for k in ('input','output'))

def run(mode,workers,seconds,sample,tag):
    diff=capture()['diff']
    ref=diff.copy();np.add.accumulate(ref,axis=1,out=ref);generate.accumulate_axis0(ref)
    digest=hashlib.sha256(ref.tobytes()).hexdigest()
    cpus=sorted(os.sched_getaffinity(0))[:workers]
    ctx=mp.get_context('fork');gate=ctx.Barrier(workers+1)
    with ctx.Manager() as manager:
        precheck=manager.dict();output=manager.dict()
        ps=[ctx.Process(target=worker,args=(i,cpus[i],diff,mode,gate,seconds,
                                           precheck,output)) for i in range(workers)]
        for p in ps:p.start()
        gate.wait()
        before=[precheck[i] for i in range(workers)]
        confirmed=all(huge_kib(m)>=8192 if mode=='huge' else huge_kib(m)==0
                      for m in before)
        raw=HERE.parent/'raw';raw.mkdir(parents=True,exist_ok=True)
        csv_path=raw/f'perf-{mode}-w{workers}-{tag}-s{sample}.csv'
        perf=subprocess.Popen(['perf','stat','-x,','--no-big-num','-e',
            'instructions,cycles,ls_any_fills_from_sys.all_dram_io,ls_l1_d_tlb_miss.all_l2_miss',
            '-p',','.join(str(p.pid) for p in ps),'-o',str(csv_path)])
        time.sleep(.3)
        assert perf.poll() is None
        load={"loadavg":os.getloadavg(),
              "cpu_pressure":Path('/proc/pressure/cpu').read_text().strip()}
        t=time.perf_counter();gate.wait()
        for p in ps:
            p.join(timeout=seconds+30);assert p.exitcode==0,p.exitcode
        batch=time.perf_counter()-t
        perf.send_signal(signal.SIGINT);perf.wait(timeout=10)
        records=[output[i] for i in range(workers)]
    assert all(x['sha256']==digest for x in records)
    assert 10<=min(x['wall'] for x in records)<=60
    counters={}
    for row in csv.reader(csv_path.read_text().splitlines()):
        if len(row)>4 and row[0] and not row[0].startswith('#'):
            counters[row[2]]={"count":float(row[0]),"running_percent":float(row[4])}
    assert all(c['running_percent']>=99.5 for c in counters.values())
    result={"mode":mode,"workers":workers,"sample":sample,"tag":tag,
            "target_seconds":seconds,"batch_wall":batch,"grid_shape":diff.shape,
            "grid_bytes":diff.nbytes,"sha256":digest,
            "hugepages_confirmed_before_timing":confirmed,
            "huge_kib_before_by_worker":[huge_kib(m) for m in before],
            "load_before":load,"records":records,"counters":counters,
            "median_cpu_per_call":float(np.median([x['cpu_per_call'] for x in records]))}
    (raw/f'{mode}-w{workers}-{tag}-s{sample}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({"mode":mode,"workers":workers,"sample":sample,
                      "huge_confirmed":confirmed,"huge_kib_min":min(result['huge_kib_before_by_worker']),
                      "ms_per_call":round(1000*result['median_cpu_per_call'],3)}),flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--mode',choices=('normal','huge'),required=True)
    p.add_argument('--workers',type=int,choices=(1,16),required=True)
    p.add_argument('--seconds',type=float,default=20.)
    p.add_argument('--samples',type=int,default=3)
    p.add_argument('--tag',default='final')
    a=p.parse_args()
    for sample in range(1,a.samples+1):run(a.mode,a.workers,a.seconds,sample,a.tag)

if __name__=='__main__':main()
