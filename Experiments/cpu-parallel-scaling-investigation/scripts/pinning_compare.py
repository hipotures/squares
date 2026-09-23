#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for op in ('argpartition','double'):
 for n in (8,16):
  for trial,pinned in enumerate((True,False,False,True)):
   ps=[]
   for i in range(n):
    ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--cpu',str(i if pinned else -1),'--calls','60','--input','r18_d026'],stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'op':op,'workers':n,'pinned':pinned,'trial':trial,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(n*60),'wall_per_call_max':max(x['wall'] for x in res)/60}
   rows.append(row);(P/'raw/pinning_compare.json').write_text(json.dumps(rows,indent=2))
   print(op,n,pinned,round(row['cpu_per_call']*1000,3),round(row['wall_per_call_max']*1000,3),flush=True)
