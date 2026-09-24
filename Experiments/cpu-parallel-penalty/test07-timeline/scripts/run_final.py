"""Adjacent long production/ordered/cost-first controls, balanced by order."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
ORDERS = (
    ("production", "ordered", "cost-first"),
    ("ordered", "cost-first", "production"),
    ("cost-first", "production", "ordered"),
)


for pair, modes in enumerate(ORDERS, 1):
    for mode in modes:
        print(f"pair {pair} mode {mode}", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "bench.py"), "--mode", mode,
             "--workers", "16", "--target-seconds", "22", "--samples", "1",
             "--tag", f"pair{pair}"],
            env=ENV, check=True,
        )
