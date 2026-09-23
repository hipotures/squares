#!/usr/bin/env python3
"""Count exact accepted-SHA workload shapes while preserving production routines."""
from __future__ import annotations
import json, os, resource, sys, time, subprocess
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
import numpy as np
from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.colgen import _direction_task
from sqpack.fractional.generate import direction_net

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'cpu-post-integration-profile'/'scripts'))
from replay_separation import replay
COUNTS={}
ORIG_EVENT=generate.event_grid
ORIG_COMPACT=generate._reachable_values
ORIG_SELECT=generate._least_finite_indices

def event_grid(*args,**kwargs):
    cells=ORIG_EVENT(*args,**kwargs)
    g=(cells.mass.shape[0]+1)*(cells.mass.shape[1]+1)
    COUNTS['grid_cells']=COUNTS.get('grid_cells',0)+int(g)
    weights=args[1]
    live=int(np.count_nonzero(weights>0))
    if not live: live=(len(weights)+max(1,len(weights)//600)-1)//max(1,len(weights)//600)
    COUNTS['scatter_support_sites']=COUNTS.get('scatter_support_sites',0)+live
    return cells

def compact(cells):
    values,row_ids,firsts,offsets=ORIG_COMPACT(cells)
    COUNTS['compact_cells']=COUNTS.get('compact_cells',0)+int(values.size)
    COUNTS['compact_metadata_rows']=COUNTS.get('compact_metadata_rows',0)+int(row_ids.size)
    return values,row_ids,firsts,offsets

def select(flat,count,**kwargs):
    COUNTS['selector_input_cells']=COUNTS.get('selector_input_cells',0)+int(flat.size)
    COUNTS['selector_k']=count
    return ORIG_SELECT(flat,count,**kwargs)

def init_worker():
    generate.event_grid=event_grid
    generate._reachable_values=compact
    generate._least_finite_indices=select

def task(args):
    COUNTS.clear()
    before=resource.getrusage(resource.RUSAGE_SELF); start=time.perf_counter()
    result=generate.placement_cells(args[0],args[1],args[2],args[3],args[4],keep=args[5],clip=args[6])
    after=resource.getrusage(resource.RUSAGE_SELF)
    cpu=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime
    elapsed=time.perf_counter()-start
    return result,{'grid_cells':COUNTS.get('grid_cells',0),'compact_cells':COUNTS.get('compact_cells',0),
        'compact_metadata_rows':COUNTS.get('compact_metadata_rows',0),
        'scatter_support_sites':COUNTS.get('scatter_support_sites',0),
        'selector_input_cells':COUNTS.get('selector_input_cells',0),'selector_k':COUNTS.get('selector_k',0),
        'minor_faults':after.ru_minflt-before.ru_minflt,'major_faults':after.ru_majflt-before.ru_majflt,
        'worker_cpu_seconds':cpu,'task_wall_seconds':elapsed,'total_wall':elapsed,'total_cpu':cpu,
        'pid':os.getpid(),'task_start_at':start,'task_end_at':time.perf_counter()}

def main():
    workers=16
    stored=np.load(ROOT.parent/'cpu-post-integration-profile'/'raw/current-states.npz')
    weights,points,membership=(stored[n] for n in ('weights','points','membership'))
    case=bench_colgen.Case(n=12,outer_side=Fraction(99,25))
    dirs=direction_net(case.half_tangents())
    pool=ProcessPoolExecutor(max_workers=workers,initializer=init_worker)
    params=(weights,points,membership,dirs,float(case.outer_side),float(case.square_side),pool)
    try:
        result=replay(*params,task_function=task,profiled=True)
    finally: pool.shutdown()
    data={'commit':subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip(),'workers':workers,
        'wall_s':result['wall_seconds'],
        'worker_metrics':result['worker_metrics'],'rounds':len(result['rounds']),
        'directions_per_round':len(dirs),'logical_traffic_model':{
          'prefix_read_write_bytes':int(result['worker_metrics']['grid_cells']*32),
          'difference_grid_zero_write_bytes':int(result['worker_metrics']['grid_cells']*8),
          'difference_scatter_update_read_write_bytes':int(result['worker_metrics']['scatter_support_sites']*4*16),
          'compaction_read_bytes':int(result['worker_metrics']['compact_cells']*8),
          'compaction_write_bytes':int(result['worker_metrics']['compact_cells']*8),
          'top13_input_read_bytes':int(result['worker_metrics']['selector_input_cells']*8),
          'compact_metadata_write_bytes':int(result['worker_metrics']['compact_metadata_rows']*24),
          'notes':'Explicit logical element traffic only; not DRAM counters. Excludes projections, event/index arrays, small selector/placement intermediates, cache-line write allocation, and allocator metadata.'}}
    (ROOT/'raw/logical-traffic.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))

if __name__=='__main__': main()
