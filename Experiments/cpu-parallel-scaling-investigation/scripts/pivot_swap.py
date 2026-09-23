#!/usr/bin/env python3
import json,time
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];a=np.load(P/'raw/squares-numpy-capture-20260923/r00_d026_flat.npy');n=len(a);step=(n-1)//8;sample=np.arange(1,9)*step
b=a.copy();zero_sample=sample[b[sample]==0];inf_other=np.flatnonzero(np.isposinf(b));inf_other=inf_other[~np.isin(inf_other,sample)][:3]
for z,i in zip(zero_sample[:3],inf_other):b[z],b[i]=b[i],b[z]
assert np.sum(np.isfinite(a))==np.sum(np.isfinite(b));assert np.all(np.sort(a[sample])[:5]==0);assert np.isinf(np.sort(b[sample])[4]);
rows=[]
for name,x in [('actual',a),('three_sample_swaps',b)]:
 np.argpartition(x,12)
 for rep in range(7):
  t=time.perf_counter();indices=np.argpartition(x,12)[:13];dt=time.perf_counter()-t
  rows.append({'case':name,'rep':rep,'seconds':dt,'candidate_values':x[indices].tolist(),'sample_values':x[sample].tolist()})
  print(name,rep,round(dt*1000,3),flush=True)
(P/'raw/pivot_swap.json').write_text(json.dumps(rows,indent=2))
np.save(P/'workloads/three_sample_swaps_flat.npy',b)
