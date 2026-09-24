"""Adjacent long ordered/balanced controls after the correctness preflight."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


for pair in (1, 2, 3):
    for mode in (("ordered", "balanced") if pair != 2 else ("balanced", "ordered")):
        print(f"balance pair {pair} mode {mode}", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "bench.py"), "--mode", mode,
             "--workers", "16", "--target-seconds", "22", "--samples", "1",
             "--tag", f"balance{pair}"],
            env=ENV, check=True,
        )
