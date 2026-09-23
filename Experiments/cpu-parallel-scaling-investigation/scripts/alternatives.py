#!/usr/bin/env python3
import json,time,resource
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];CAP=P/'raw/squares-numpy-capture-20260923'; rows=[]
def original(a):return np.argpartition(a,12)[:13]
def finite_then_select(a):
 ix=np.flatnonzero(np.isfinite(a));return ix[np.argpartition(a[ix],min(12,len(ix)-1))[:13]]
def threshold_recover(a):
 threshold=np.partition(a,12)[12];return np.flatnonzero(a<=threshold)[:13]
def first_finite(a):return np.flatnonzero(np.isfinite(a))[:13]
def shuffle_then_select(a):
 order=np.arange(len(a));np.random.default_rng(12345).shuffle(order); return order[np.argpartition(a[order],12)[:13]]
def small_k_only(a):return np.argpartition(a,2)[:3]
methods={'original':original,'finite_then_select':finite_then_select,'partition_threshold':threshold_recover,'first_finite':first_finite,'shuffle_then_select':shuffle_then_select,'small_k_3_only':small_k_only}
for key in ('r00_d026','r18_d026'):
 a=np.load(CAP/f'{key}_flat.npy');trueval=np.sort(a[original(a)]);k=5 if key.startswith('r00') else 20
 for name,fn in methods.items():
  fn(a); times=[];faults=[];indices=None
  for _ in range(k):
   ru=resource.getrusage(resource.RUSAGE_SELF).ru_minflt;t=time.perf_counter();indices=fn(a);times.append(time.perf_counter()-t);faults.append(resource.getrusage(resource.RUSAGE_SELF).ru_minflt-ru)
  valid_values=bool(len(indices)==13 and np.array_equal(np.sort(a[indices]),trueval))
  row={'input':key,'method':name,'median_s':float(np.median(times)),'min_s':float(min(times)),'times':times,'faults':faults,'candidate_count':len(indices),'same_selected_values':valid_values,'same_indices':bool(np.array_equal(np.sort(indices),np.sort(original(a)))),'indices':indices[:13].tolist()}
  rows.append(row);(P/'raw/alternatives.json').write_text(json.dumps(rows,indent=2))
  print(key,name,round(row['median_s']*1000,3),valid_values,row['same_indices'],flush=True)
