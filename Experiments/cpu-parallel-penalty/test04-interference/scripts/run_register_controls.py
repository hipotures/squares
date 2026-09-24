"""Long compute-only controls for the backgrounds used in causal claims."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


for background in ("stream", "prefix", "slab", "top13"):
    print(f"register target vs {background} × 14", flush=True)
    subprocess.run(
        [sys.executable, str(HERE / "bench.py"), "--target", "register",
         "--background", background, "--bg-count", "14", "--seconds", "20",
         "--samples", "3", "--tag", "register-control"],
        env=ENV, check=True,
    )
