#!/usr/bin/env python3
import json,subprocess,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]; CAP=P/'raw/squares-numpy-capture-20260923'; W=P/'scripts/worker.py'; OUT=P/'workloads';OUT.mkdir(exist_ok=True)
rng=np.random.default_rng(777); source=np.load(CAP/'r18_d026_flat.npy'); grid_source=np.load(CAP/'r18_d026_grid.npy')
items=[('tiny',64,10000),('small',181,2000),('medium',512,300),('late',979,50),('round0',1247,30)]
for label,side,calls in items:
 n=side*side; flat=rng.choice(source,size=n,replace=True); grid=rng.choice(grid_source.ravel(),size=n,replace=True).reshape(side,side)
 np.save(OUT/f'size_{label}_flat.npy',flat);np.save(OUT/f'size_{label}_grid.npy',grid)
rows=[]
for label,side,calls in items:
 for op in ('argpartition','double'):
  for count in (1,2,4,8,16):
   ps=[]
   for i in range(count):
    ps.append(subprocess.Popen([sys.executable,str(W),'--op',op,'--cpu',str(i),'--calls',str(calls),'--input',f'size_{label}','--capture-dir',str(OUT)],stdout=subprocess.PIPE,text=True))
   res=[json.loads(p.communicate(timeout=120)[0]) for p in ps]
   row={'size':label,'elements':side*side,'op':op,'workers':count,'calls_per_worker':calls,'wall_per_call_max':max(x['wall']/calls for x in res),'cpu_per_call_mean':sum(x['cpu'] for x in res)/(count*calls),'faults_per_call_mean':sum(x['minor_faults'] for x in res)/(count*calls),'details':res}
   rows.append(row);(P/'raw/working_set.json').write_text(json.dumps(rows,indent=2))
   print(label,op,count,round(row['cpu_per_call_mean']*1000,3),flush=True)
