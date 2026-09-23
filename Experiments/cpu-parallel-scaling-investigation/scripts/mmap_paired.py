#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for op in ('argpartition','double'):
 for n in (1,16):
  for trial,mm in enumerate((False,True,True,False)):
   ps=[]
   for i in range(n):
    cmd=[sys.executable,str(W),'--op',op,'--cpu',str(i),'--calls','80','--input','r18_d026']
    if mm:cmd.append('--mmap')
    ps.append(subprocess.Popen(cmd,stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'op':op,'workers':n,'trial':trial,'mmap':mm,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(n*80),'wall_per_call_max':max(x['wall'] for x in res)/80,'details':res}
   rows.append(row);(P/'raw/mmap_paired.json').write_text(json.dumps(rows,indent=2))
   print(op,n,trial,mm,round(row['cpu_per_call']*1000,3),flush=True)
