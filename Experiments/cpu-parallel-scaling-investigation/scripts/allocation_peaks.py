#!/usr/bin/env python3
import gc,json,resource,tracemalloc
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];CAP=P/'raw/squares-numpy-capture-20260923';a=np.load(CAP/'r00_d026_flat.npy');g=np.load(CAP/'r18_d026_grid.npy');r=[]
def finite(x):
 ix=np.flatnonzero(np.isfinite(x));return ix[np.argpartition(x[ix],12)[:13]]
def first(x):return np.flatnonzero(np.isfinite(x))[:13]
def threshold(x):
 k=np.partition(x,12)[12];return np.flatnonzero(x<=k)[:13]
def shuffle(x):
 ix=np.arange(x.size);np.random.default_rng(123).shuffle(ix);return ix[np.argpartition(x[ix],12)[:13]]
out1=np.empty_like(g);out2=np.empty_like(g)
def out_reuse():
 np.cumsum(g,axis=1,out=out1);np.cumsum(out1,axis=0,out=out2);return out2
def inplace_reuse():
 np.copyto(out1,g);np.add.accumulate(out1,axis=1,out=out1);np.add.accumulate(out1,axis=0,out=out1);return out1
methods={'cumsum_out_reuse':out_reuse,'cumsum_inplace_reuse':inplace_reuse,'argpartition':lambda:np.argpartition(a,12)[:13],'finite_then_select':lambda:finite(a),'first_finite':lambda:first(a),'partition_threshold':lambda:threshold(a),'shuffle_then_select':lambda:shuffle(a),'cumsum_nested':lambda:np.cumsum(np.cumsum(g,axis=1),axis=0)}
for name,fn in methods.items():
 gc.collect();tracemalloc.start();base=tracemalloc.get_traced_memory()[0];res=fn();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();row={'method':name,'peak_extra_bytes':peak-base,'output_bytes':res.nbytes,'array_size':a.size if not name.startswith('cumsum') else g.size};r.append(row);print(row,flush=True)
(P/'raw/allocation_peaks.json').write_text(json.dumps(r,indent=2))
