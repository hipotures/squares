"""Serial screening of bitwise-verified full-grid row strips and padding."""

import os
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENV = os.environ.copy()
ENV.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")


def run(*args):
    print(" ".join(args), flush=True)
    subprocess.run([sys.executable, str(HERE / args[0]), *args[1:]], env=ENV, check=True)


def main():
    run("verify_tiles.py")
    for script, name, values in (
        ("bench_tile.py", "--block-rows", (0, 32, 64, 128, 256)),
        ("bench_padding.py", "--padding", (0, 4, 32, 64, 256)),
    ):
        for workers in (1, 16):
            for value in values:
                run(script, "--workers", str(workers), name, str(value),
                    "--seconds", "10.5", "--samples", "1", "--tag", "screen")


if __name__ == "__main__":
    main()
