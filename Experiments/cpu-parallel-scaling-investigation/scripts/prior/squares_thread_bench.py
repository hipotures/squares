"""Temporary thread-direction benchmark for the n=12 fractional search.

Run from packing/ with the project's uv-managed Python:
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    uv run --frozen python /tmp/squares_thread_bench.py --workers 4 \
      rounds --n 12 --side 99/25

Only the solve_rows direction loop is changed, in memory. No repository file is edited.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from devtools import bench_colgen as bench  # noqa: E402
from sqpack.fractional import colgen  # noqa: E402


ORIGINAL = """        for index, direction in enumerate(directions):
            for mass, cu, cv, covers in placement_cells(
                points,
                site_weights,
                direction,
                outer,
                side,
                keep=rows_per_direction,
                clip=clip,
            ):
"""
REPLACEMENT = """        def evaluate_direction(direction):
            return placement_cells(
                points,
                site_weights,
                direction,
                outer,
                side,
                keep=rows_per_direction,
                clip=clip,
            )

        for index, direction_cells in enumerate(executor.map(evaluate_direction, directions)):
            for mass, cu, cv, covers in direction_cells:
"""


def make_parallel_solve_rows(workers: int):
    source = textwrap.dedent(inspect.getsource(colgen.solve_rows))
    if source.count(ORIGINAL) != 1:
        raise RuntimeError("solve_rows direction loop differs from expected source")
    modified = source.replace(ORIGINAL, REPLACEMENT)
    namespace = dict(vars(colgen))
    exec(compile(modified, "<temporary parallel solve_rows>", "exec"), namespace)
    solve = namespace["solve_rows"]

    def parallel_solve_rows(*args, **kwargs):
        # Construct and close once per solve_rows call. Both costs are inside the
        # benchmark's solve_rows wall timer; direction tasks reuse this pool.
        with ThreadPoolExecutor(max_workers=workers) as executor:
            namespace["executor"] = executor
            try:
                return solve(*args, **kwargs)
            finally:
                del namespace["executor"]

    return parallel_solve_rows


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--pid-file", type=Path, default=Path("/tmp/squares_n12_thread_pid"))
    settings, remaining = parser.parse_known_args()
    if settings.workers < 1:
        parser.error("--workers must be positive")
    settings.pid_file.write_text(f"{os.getpid()}\n")
    state = {}
    original_row_run = bench._row_run
    original_emit = bench._emit

    def capture_row_run(*args, **kwargs):
        result = original_row_run(*args, **kwargs)
        state["least_covered"] = result[3].least_covered
        return result

    def emit_with_least(report, out):
        report["least_covered"] = state.get("least_covered")
        return original_emit(report, out)

    bench._row_run = capture_row_run
    bench._emit = emit_with_least
    bench.solve_rows = make_parallel_solve_rows(settings.workers)
    return bench.main(remaining)


if __name__ == "__main__":
    raise SystemExit(main())
