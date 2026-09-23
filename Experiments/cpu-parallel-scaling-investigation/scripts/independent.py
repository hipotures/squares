#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; W=P/'scripts/worker.py'
PY=Path(sys.executable)
raw=P/'raw/independent'; raw.mkdir(exist_ok=True)
allruns=[]
for op in ('argpartition','double'):
 for count in (1,2,4,8,16):
  for trial in range(2):
   key=f'{op}_{count}_{trial}'; start=raw/f'{key}.start'; start.unlink(missing_ok=True); ready=[]; procs=[]; outs=[]
   for i in range(count):
    r=raw/f'{key}_{i}.ready'; o=raw/f'{key}_{i}.json'; r.unlink(missing_ok=True); o.unlink(missing_ok=True); ready.append(r);outs.append(o)
    procs.append(subprocess.Popen([str(PY),str(W),'--op',op,'--cpu',str(i),'--calls',str(160//count),'--input','r18_d026','--ready-file',str(r),'--start-file',str(start),'--out',str(o)],stdout=subprocess.DEVNULL,stderr=(raw/'errors.log').open('a')))
   deadline=time.time()+90
   while not all(r.exists() for r in ready):
    if time.time()>deadline: raise RuntimeError(f'not ready {key}')
    time.sleep(.01)
   tmp=raw/f'{key}.tmp'; tmp.write_text(str(time.perf_counter()+.25)); tmp.replace(start)
   for proc in procs: proc.wait(timeout=120)
   results=[json.loads(o.read_text()) for o in outs]
   row={'op':op,'workers':count,'trial':trial,'makespan':max(x['start']+x['wall'] for x in results)-min(x['start'] for x in results),'cpu_sum':sum(x['cpu'] for x in results),'calls':sum(x['calls'] for x in results),'minor_faults':sum(x['minor_faults'] for x in results),'workers_detail':results}
   allruns.append(row); (P/'raw/independent.json').write_text(json.dumps(allruns,indent=2))
   print(op,count,trial,'wall',round(row['makespan'],3),'cpu',round(row['cpu_sum'],3),flush=True)
