"""Three long samples around the screened footprint knees."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
MIB = 1024 * 1024


for kind, sizes in (("prefix", (2, 8, 16)), ("top13", (4, 16, 32))):
    for size in sizes:
        for workers in (1, 16):
            print(f"repeat {kind} {size} MiB w{workers}", flush=True)
            subprocess.run(
                [sys.executable, str(HERE / "bench_sizes.py"), "--kind", kind,
                 "--bytes", str(size * MIB), "--workers", str(workers),
                 "--seconds", "20", "--samples", "3", "--tag", "repeat"],
                env=ENV, check=True,
            )
