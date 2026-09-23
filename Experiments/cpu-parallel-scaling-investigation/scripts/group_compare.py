#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
groups={'low8':list(range(8)),'high8':list(range(8,16)),'even8':list(range(0,16,2)),'odd8':list(range(1,16,2))}
for op in ('argpartition','double'):
 for trial in range(2):
  for name,cpus in groups.items():
   ps=[]
   for cpu in cpus:ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--cpu',str(cpu),'--calls','80','--input','r18_d026'],stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'op':op,'group':name,'trial':trial,'cpus':cpus,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(len(cpus)*80),'wall_per_call_max':max(x['wall'] for x in res)/80}
   rows.append(row);(P/'raw/group_compare.json').write_text(json.dumps(rows,indent=2))
   print(op,trial,name,round(row['cpu_per_call']*1000,3),flush=True)
