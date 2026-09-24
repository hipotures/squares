"""Long adjacent full-grid controls for the best screened row-strip sizes."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


for workers in (1, 16):
    for rows in (0, 64, 32):
        print(f"tile repeat w{workers} rows={rows}", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "bench_tile.py"), "--workers", str(workers),
             "--block-rows", str(rows), "--seconds", "20", "--samples", "3",
             "--tag", "repeat"],
            env=ENV, check=True,
        )
