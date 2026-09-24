"""Three adjacent normal/verified-THP controls at one and 16 workers."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


for workers in (1, 16):
    for pair in (1, 2, 3):
        for mode in ("normal", "huge"):
            print(f"hugepage pair {pair} workers {workers} mode {mode}", flush=True)
            subprocess.run(
                [sys.executable, str(HERE / "bench.py"), "--mode", mode,
                 "--workers", str(workers), "--seconds", "20", "--samples", "1",
                 "--tag", f"pair{pair}"],
                env=ENV, check=True,
            )
