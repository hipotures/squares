"""Long controls with separate retained direction grids for backgrounds."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


for target, background in (
    ("prefix", "prefix"),
    ("slab", "slab"),
    ("top13", "top13"),
):
    print(f"distinct {target} vs {background} × 14", flush=True)
    subprocess.run(
        [sys.executable, str(HERE / "bench.py"), "--target", target,
         "--background", background, "--bg-count", "14", "--distinct-bg",
         "--seconds", "20", "--samples", "3", "--tag", "distinct"],
        env=ENV, check=True,
    )
