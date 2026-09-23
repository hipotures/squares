#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py'; rows=[]
for op in ('argpartition','double'):
 for mmap in (False,True):
  for count in (1,8,16):
   for trial in range(2):
    ps=[]
    for i in range(count):
     cmd=[sys.executable,str(W),'--op',op,'--cpu',str(i),'--calls','60','--input','r18_d026']
     if mmap:cmd.append('--mmap')
     ps.append(subprocess.Popen(cmd,stdout=subprocess.PIPE,text=True))
    res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
    row={'op':op,'mmap':mmap,'workers':count,'trial':trial,'cpu_per_call':sum(x['thread_cpu'] for x in res)/(count*60),'wall_per_call_max':max(x['wall'] for x in res)/60,'faults_mean':sum(x['minor_faults'] for x in res)/count}
    rows.append(row);(P/'raw/mmap_test.json').write_text(json.dumps(rows,indent=2))
    print(op,mmap,count,trial,round(row['cpu_per_call']*1000,3),flush=True)
