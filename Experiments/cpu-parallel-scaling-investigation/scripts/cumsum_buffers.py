#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';rows=[]
for op in ('double','double_separate','double_out','double_add','double_inplace','axis1','axis0'):
 for count in (1,2,4,8,16):
  ps=[]
  for i in range(count):
   ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--cpu',str(i),'--calls','60','--input','r18_d026'],stdout=subprocess.PIPE,text=True))
  res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
  row={'op':op,'workers':count,'latency_cpu_mean':sum(x['thread_cpu'] for x in res)/(count*60),'latency_wall_max':max(x['wall'] for x in res)/60,'faults_mean':sum(x['minor_faults'] for x in res)/count,'rss_max_kb':max(x['rss_kb'] for x in res),'details':res}
  rows.append(row);(P/'raw/cumsum_buffers.json').write_text(json.dumps(rows,indent=2))
  print(op,count,round(row['latency_cpu_mean']*1000,3),round(row['faults_mean'],1),flush=True)
