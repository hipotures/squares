"""Run the existing exact retained-row witness check on incremental HiGHS rows."""
import sys
from pathlib import Path

import numpy as np

from sqpack.fractional import colgen

from bench_lp import Incremental

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packing/benchmarks/round0_selector"))
import exact_row_check  # noqa: E402

model = None


def solve(sites, rows):
    global model
    if model is None:
        model = Incremental(sites.sizes())
    _, _, weights, duals, value, status = model.solve(rows.stacked())
    if status != "HighsModelStatus.kOptimal":
        return None
    return weights, np.maximum(duals, 0), value


colgen.solve_lp = solve
raise SystemExit(exact_row_check.main())
