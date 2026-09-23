#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for inp in ('r00_d026','r18_d026'):
 for op in ('argpartition','argfinite'):
  calls=6 if inp.startswith('r00') and op=='argpartition' else 80
  for n in (1,2,4,8,16):
   ps=[]
   for cpu in range(n):
    ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--cpu',str(cpu),'--calls',str(calls),'--input',inp],stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'input':inp,'op':op,'workers':n,'calls_per_worker':calls,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(n*calls),'wall_per_call_max':max(x['wall'] for x in res)/calls,'faults_per_call':sum(x['minor_faults'] for x in res)/(n*calls),'details':res}
   rows.append(row);(P/'raw/selection_scaling.json').write_text(json.dumps(rows,indent=2))
   print(inp,op,n,round(row['cpu_per_call']*1000,3),flush=True)
