"""Repeat every screened >=20% effect and each idle control for 20 s × 3."""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
matrix=json.loads((HERE.parent/"processed/matrix.json").read_text())
conditions=[(target,"sleep",0) for target in ("prefix","slab","top13","direction","register")]
conditions += [(r['target'],r['background'],r['bg_count']) for r in matrix['screen']
               if r['wall_inflation']>=1.2]
plan={"criterion":"screen wall inflation >=1.20 vs target idle",
      "target_seconds":20,"samples_per_condition":3,
      "conditions":[list(x) for x in conditions]}
(HERE.parent/"processed/repeat-plan.json").write_text(json.dumps(plan,indent=2)+'\n')
env=os.environ.copy()
env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
for position,(target,background,count) in enumerate(conditions,1):
    print(f'condition {position}/{len(conditions)}: {target} vs {background} × {count}',flush=True)
    subprocess.run([sys.executable,str(HERE/'bench.py'),'--target',target,
                    '--background',background,'--bg-count',str(count),
                    '--seconds','20','--samples','3','--tag','repeat'],
                   env=env,check=True)
