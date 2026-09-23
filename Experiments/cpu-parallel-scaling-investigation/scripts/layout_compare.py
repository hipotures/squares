#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for op in ('axis1','axis0','double','double_out'):
 for layout in ('C','F'):
  for n in (1,16):
   ps=[]
   for i in range(n):
    ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--layout',layout,'--cpu',str(i),'--calls','80','--input','r18_d026'],stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'op':op,'layout':layout,'workers':n,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(n*80),'wall_per_call_max':max(x['wall'] for x in res)/80,'faults_per_call':sum(x['minor_faults'] for x in res)/(n*80)}
   rows.append(row);(P/'raw/layout_compare.json').write_text(json.dumps(rows,indent=2))
   print(op,layout,n,round(row['cpu_per_call']*1000,3),flush=True)
