#!/usr/bin/env python3
import json, subprocess, sys, time
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]; CAP=P/'raw/squares-numpy-capture-20260923'; W=P/'scripts/worker.py'; OUT=P/'workloads';OUT.mkdir(exist_ok=True)
orig=np.load(CAP/'r00_d026_flat.npy'); n=len(orig); finite=np.isfinite(orig);nf=finite.sum(); rng=np.random.default_rng(20260923)
cases={'actual':orig,'random_all':rng.random(n),'random_finite_inf':np.where(finite,rng.random(n),np.inf),'all_zero':np.zeros(n),'few_ties_inf':np.where(finite,rng.integers(0,4,n).astype(float),np.inf),'zero_inf_shuffled':rng.permutation(orig),'zero_inf_sorted':np.sort(orig),'zero_inf_reversed':np.sort(orig)[::-1]}
for name,arr in cases.items():np.save(OUT/f'{name}_flat.npy',arr)
rows=[]
for name in cases:
 for count in (1,2,4,8,16):
  if name not in ('actual','random_all','random_finite_inf','all_zero','few_ties_inf','zero_inf_shuffled') and count>1:continue
  ps=[]
  for i in range(count):
   cmd=[sys.executable,str(W),'--op','argpartition','--cpu',str(i),'--calls','4','--input',name,'--capture-dir',str(OUT)]
   ps.append(subprocess.Popen(cmd,stdout=subprocess.PIPE,text=True))
  results=[json.loads(proc.communicate(timeout=120)[0]) for proc in ps]
  row={'distribution':name,'workers':count,'finite':int(nf),'latency_per_call_wall':max(v['wall']/v['calls'] for v in results),'cpu_per_call_mean':sum(v['cpu'] for v in results)/(count*4),'worker_results':results}
  rows.append(row);(P/'raw/distribution.json').write_text(json.dumps(rows,indent=2))
  print(name,count,round(row['latency_per_call_wall']*1000,3),flush=True)
