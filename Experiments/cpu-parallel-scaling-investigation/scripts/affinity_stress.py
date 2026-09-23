#!/usr/bin/env python3
import json,os,subprocess,sys,time
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'scripts/worker.py';C=P/'scripts/stress';rows=[]
scenarios=[('near4',0,[1,2,3,4]),('far4',0,[8,9,10,11]),('cross8',0,[1,2,3,4,8,9,10,11]),('near7',0,list(range(1,8))),('far7',0,list(range(8,15))),('far4_swap',8,[0,1,2,3]),('near4_swap',8,[9,10,11,12])]
for size in ('0.25','2','8','64'):
 for name,target_cpu,bg_cpus in scenarios:
  for op in ('argpartition','double'):
   ps=[]
   try:
    for cpu in bg_cpus:ps.append(subprocess.Popen(['taskset','-c',str(cpu),str(C),'stream','8',size],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL))
    time.sleep(.25)
    cmd=[sys.executable,str(W),'--op',op,'--cpu',str(target_cpu),'--calls',str(160 if op=='argpartition' else 80),'--input','r18_d026']
    res=json.loads(subprocess.check_output(cmd,text=True))
    row={'size_mb_per_array':float(size),'scenario':name,'target_cpu':target_cpu,'background_cpus':bg_cpus,'op':op,'target':res,'bg_alive':sum(p.poll() is None for p in ps)}
    rows.append(row);(P/'raw/affinity_stress.json').write_text(json.dumps(rows,indent=2))
    print(size,name,op,round(res['wall'],3),flush=True)
   finally:
    for p in ps:p.terminate()
    for p in ps:
     try:p.wait(timeout=1)
     except subprocess.TimeoutExpired:p.kill();p.wait()
