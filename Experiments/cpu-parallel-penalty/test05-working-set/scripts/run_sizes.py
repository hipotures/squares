"""One long screen per size, kernel, and worker count; no concurrent runs."""
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
SIZES=(256*1024,1*1024**2,2*1024**2,4*1024**2,8*1024**2,
       12*1024**2,16*1024**2,24*1024**2,32*1024**2)
env=os.environ.copy()
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
for kind in ('prefix','top13'):
    for bytes_ in SIZES:
        for workers in (1,4,8,16):
            print(f'workload {kind} {bytes_} bytes {workers} workers',flush=True)
            subprocess.run([sys.executable,str(HERE/'bench_sizes.py'),'--kind',kind,
                            '--bytes',str(bytes_),'--workers',str(workers),
                            '--seconds','10.5','--samples','1','--tag','screen'],
                           env=env,check=True)
