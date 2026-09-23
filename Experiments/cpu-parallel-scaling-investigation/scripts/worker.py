#!/usr/bin/env python3
import argparse, json, os, resource, time
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
CAP=P/'raw/squares-numpy-capture-20260923'
p=argparse.ArgumentParser()
p.add_argument('--op',required=True)
p.add_argument('--cpu',type=int,required=True)
p.add_argument('--calls',type=int,default=100)
p.add_argument('--input',default='r18_d026')
p.add_argument('--capture-dir',type=Path,default=CAP)
p.add_argument('--mmap',action='store_true')
p.add_argument('--layout',choices=['C','F'],default='C')
p.add_argument('--start-file',type=Path)
p.add_argument('--ready-file',type=Path)
p.add_argument('--out',type=Path)
p.add_argument('--mode',choices=['measure','stress'],default='measure')
a=p.parse_args()
if a.cpu >= 0: os.sched_setaffinity(0,{a.cpu})
flat=np.asarray(np.load(a.capture_dir/f'{a.input}_flat.npy',mmap_mode='r')) if a.mmap else np.load(a.capture_dir/f'{a.input}_flat.npy') if a.op.startswith('arg') else None
grid=np.asarray(np.load(a.capture_dir/f'{a.input}_grid.npy',mmap_mode='r')) if a.mmap else np.load(a.capture_dir/f'{a.input}_grid.npy') if a.op.startswith('double') or a.op.startswith('axis') else None
if grid is not None and a.layout=='F': grid=np.asfortranarray(grid)
out1=np.empty_like(grid) if grid is not None else None
out2=np.empty_like(grid) if grid is not None else None
# Inputs loaded and operations warmed before start synchronization.
def work():
 if a.op=='argpartition': return float(np.argpartition(flat,12)[0])
 if a.op=='argfinite':
  ix=np.flatnonzero(np.isfinite(flat)); return float(ix[np.argpartition(flat[ix],min(12,len(ix)-1))[0]])
 if a.op=='double': return float(np.cumsum(np.cumsum(grid,axis=1),axis=0)[0,0])
 if a.op=='double_separate':
  tmp=np.cumsum(grid,axis=1); result=np.cumsum(tmp,axis=0); return float(result[0,0])
 if a.op=='double_add':
  np.add.accumulate(grid,axis=1,out=out1); np.add.accumulate(out1,axis=0,out=out2); return float(out2[0,0])
 if a.op=='double_out':
  np.cumsum(grid,axis=1,out=out1); np.cumsum(out1,axis=0,out=out2); return float(out2[0,0])
 if a.op=='double_inplace':
  np.copyto(out1,grid); np.cumsum(out1,axis=1,out=out1); np.cumsum(out1,axis=0,out=out1); return float(out1[0,0])
 if a.op=='axis1': return float(np.cumsum(grid,axis=1)[0,0])
 if a.op=='axis0': return float(np.cumsum(grid,axis=0)[0,0])
 raise ValueError(a.op)
work()
if a.ready_file: a.ready_file.write_text('ready')
if a.start_file:
 while not a.start_file.exists(): time.sleep(.001)
 start=float(a.start_file.read_text()); time.sleep(max(0,start-time.perf_counter()))
else: start=time.perf_counter()
ru=resource.getrusage(resource.RUSAGE_SELF); faults0=ru.ru_minflt
cpu0=time.process_time(); thread0=time.thread_time(); nthreads0=len(list(Path('/proc/self/task').iterdir())); wall0=time.perf_counter(); checksum=0.0; calls=0
if a.mode=='stress':
 while time.perf_counter()-wall0<30:
  checksum+=work(); calls+=1
else:
 for _ in range(a.calls): checksum+=work(); calls+=1
result={'op':a.op,'cpu_pin':a.cpu,'calls':calls,'wall':time.perf_counter()-wall0,'cpu':time.process_time()-cpu0,'thread_cpu':time.thread_time()-thread0,'threads_before':nthreads0,'threads_after':len(list(Path('/proc/self/task').iterdir())),'minor_faults':resource.getrusage(resource.RUSAGE_SELF).ru_minflt-faults0,'rss_kb':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'checksum':checksum,'start':wall0}
if a.out: a.out.write_text(json.dumps(result)+'\n')
else: print(json.dumps(result))
