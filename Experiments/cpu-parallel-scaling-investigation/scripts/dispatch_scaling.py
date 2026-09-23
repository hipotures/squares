#!/usr/bin/env python3
import json,os,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for inp in ('r00_d026','r18_d026'):
 for n in (1,2,4,8,16):
  calls=10 if inp.startswith('r00') else 80
  ps=[]
  for i in range(n):
   ps.append(subprocess.Popen([sys.executable,str(W),'--op','argpartition','--cpu',str(i),'--calls',str(calls),'--input',inp],stdout=subprocess.PIPE,text=True))
  res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
  row={'input':inp,'workers':n,'calls_per_worker':calls,'disabled':os.environ.get('NPY_DISABLE_CPU_FEATURES'),'cpu_per_call':sum(x['thread_cpu'] for x in res)/(n*calls),'wall_per_call_max':max(x['wall'] for x in res)/calls,'details':res}
  rows.append(row);(P/'raw/dispatch_scaling_generic.json').write_text(json.dumps(rows,indent=2))
  print(inp,n,round(row['cpu_per_call']*1000,3),flush=True)
