#!/usr/bin/env python3
import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];C=P/'scripts/cache_latency';rows=[]
for trial in range(2):
 for cpu in (0,8):
  for size in (8,16,24,32,48,64,96,128):
   for stride in (64,4096):
    res=json.loads(subprocess.check_output(['taskset','-c',str(cpu),str(C),str(size),'8000000',str(stride)],text=True));res.update({'cpu':cpu,'trial':trial});rows.append(res)
    (P/'raw/cache_stride.json').write_text(json.dumps(rows,indent=2))
    print(trial,cpu,size,stride,round(res['ns_per_access'],2),flush=True)
