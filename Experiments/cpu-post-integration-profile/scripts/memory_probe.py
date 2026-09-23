"""Allocation and array-shape inspection on captured current-main states."""

from __future__ import annotations

import json
import resource
import tracemalloc
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import generate

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    stored = np.load(ROOT / "raw/current-states.npz")
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = generate.direction_net(case.half_tangents())
    records = []
    for round_index in (0, 18, 22):
        weights = stored["weights"][round_index][stored["membership"]]
        for direction_index in (0, 26, 90, 180):
            direction = directions[direction_index]
            args = (stored["points"], weights, direction,
                    float(case.outer_side), float(case.square_side))
            # Warm exact path before tracing; these runs are allocation
            # diagnostics, not a short-call performance benchmark.
            generate.placement_cells(*args, keep=3)
            faults_before = resource.getrusage(resource.RUSAGE_SELF).ru_minflt
            tracemalloc.start()
            placements = generate.placement_cells(*args, keep=3)
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            faults_after = resource.getrusage(resource.RUSAGE_SELF).ru_minflt
            cells = generate.event_grid(*args, build_reachable=False)
            compact, row_ids, firsts, offsets = generate._reachable_values(cells)
            records.append({
                "round": round_index, "direction": direction_index,
                "live_sites": int(np.count_nonzero(weights)),
                "grid_shape": cells.mass.shape,
                "grid_cells": cells.mass.size,
                "grid_bytes": cells.mass.nbytes,
                "projected_u_v_bytes": cells.u.nbytes + cells.v.nbytes,
                "event_bytes": cells.u_events.nbytes + cells.v_events.nbytes,
                "compact_cells": compact.size,
                "compact_bytes": compact.nbytes,
                "interval_metadata_bytes": row_ids.nbytes + firsts.nbytes + offsets.nbytes,
                "placements": len(placements),
                "peak_traced_bytes": peak,
                "retained_traced_bytes": current,
                "minor_faults_one_call": faults_after - faults_before,
            })
    data = {
        "note": "tracemalloc captures NumPy allocations but changes call timing; no latency inferred",
        "records": records,
    }
    (ROOT / "raw/memory-probe.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(data, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
