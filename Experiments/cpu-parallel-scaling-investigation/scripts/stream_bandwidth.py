#!/usr/bin/env python3
import json,subprocess,time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; C=P/'scripts/stress';rows=[]
for size in (0.25,2,8,64):
 for n in (1,2,4,8,16):
  ps=[subprocess.Popen(['taskset','-c',str(i),str(C),'stream','3',str(size)],stdout=subprocess.PIPE,text=True) for i in range(n)]
  t=time.perf_counter();detail=[json.loads(p.communicate(timeout=15)[0]) for p in ps];wall=time.perf_counter()-t
  # Every pass reads one full a, reads one full b and writes one full b; nominal traffic.
  nominal=sum(x['count']*3*size*1024*1024 for x in detail)
  row={'size_mb_per_array':size,'workers':n,'wall':wall,'nominal_gib_per_s':nominal/wall/(1024**3),'details':detail}
  rows.append(row);(P/'raw/stream_bandwidth.json').write_text(json.dumps(rows,indent=2))
  print(size,n,round(row['nominal_gib_per_s'],2),flush=True)
