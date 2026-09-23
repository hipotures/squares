#!/usr/bin/env python3
import json, subprocess, sys, time
from pathlib import Path
P=Path(__file__).resolve().parents[1]; W=P/'scripts/worker.py'; C=P/'scripts/stress'; R=P/'raw/target_stress'; R.mkdir(exist_ok=True)
rows=[]
for bg in ('idle','compute','stream','argpartition','double'):
 for n in (0,1,2,4,8,14):
  for target in ('fixed','argpartition','double'):
   if n==0 and bg!='idle': continue
   ps=[]; ready=[]
   try:
    for i in range(1,n+1):
     if bg in ('idle','compute','stream'):
      ps.append(subprocess.Popen(['taskset','-c',str(i),str(C),bg,'30'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
     else:
      r=R/f'ready_{i}';r.unlink(missing_ok=True);ready.append(r)
      ps.append(subprocess.Popen([sys.executable,str(W),'--op',bg,'--cpu',str(i),'--mode','stress','--input','r18_d026','--ready-file',str(r)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
    deadline=time.time()+30
    while ready and not all(x.exists() for x in ready):
     if time.time()>deadline:raise RuntimeError('background not ready')
     time.sleep(.02)
    if bg=='stream' and n: time.sleep(.3)
    if target=='fixed':
     cmd=['taskset','-c','0',str(C),'fixed','500000000']
     t=time.perf_counter(); v=json.loads(subprocess.check_output(cmd,text=True)); v['wall']=time.perf_counter()-t
    else:
     cmd=[sys.executable,str(W),'--op',target,'--cpu','0','--calls',str(160 if target=='argpartition' else 80),'--input','r18_d026']
     v=json.loads(subprocess.check_output(cmd,text=True))
    row={'background':bg,'background_count':n,'target':target,'target_result':v,'bg_alive':sum(p.poll() is None for p in ps)}
    rows.append(row);(P/'raw/target_stress.json').write_text(json.dumps(rows,indent=2))
    print(bg,n,target,round(v['wall'],3),flush=True)
   finally:
    for proc in ps: proc.terminate()
    for proc in ps:
     try:proc.wait(timeout=2)
     except subprocess.TimeoutExpired:proc.kill();proc.wait()
