"""Recompute every retained n=12 placement row with exact rational geometry.

This is a correctness diagnostic, not a timed solver benchmark. A stored float
centre is read as its exact binary rational, then both container containment
and all site-cover coefficients are re-decided using Fraction arithmetic. When
rounding at an event boundary changes one coefficient, search nearby exact
rational centres for a witness to the *same complete row vector*.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from solver_benchmark import _install_baseline_selector

from devtools import bench_colgen
from sqpack.fractional.generate import direction_net


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--selector", choices=("current", "baseline"), default="current")
    args = parser.parse_args()
    if args.selector == "baseline":
        _install_baseline_selector()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    run, sites, rows, _solution = bench_colgen._row_run(  # noqa: SLF001 - validation seam
        case, grids, max_rounds=60, rows_per_direction=3
    )
    matrix = rows.stacked()
    positions = sites.positions()
    membership = sites.membership()
    directions = direction_net(case.half_tangents())
    by_direction: dict[int, list[int]] = defaultdict(list)
    for row_index, direction_index in enumerate(rows.directions):
        by_direction[direction_index].append(row_index)
    outside = []
    mismatch = []
    recovered = []
    unresolved = []
    half = case.square_side / 2
    for direction_index, row_indices in by_direction.items():
        direction = directions[direction_index]
        ux, uy = direction.ux, direction.uy
        projected = tuple((ux * px + uy * py, -uy * px + ux * py) for px, py in positions)
        extent = half * (ux + uy)

        def admissible(
            u: Fraction,
            v: Fraction,
            *,
            rotation_x: Fraction = ux,
            rotation_y: Fraction = uy,
            margin: Fraction = extent,
        ) -> bool:
            x, y = rotation_x * u - rotation_y * v, rotation_y * u + rotation_x * v
            return (
                margin <= x <= case.outer_side - margin
                and margin <= y <= case.outer_side - margin
            )

        def coefficients(
            u: Fraction,
            v: Fraction,
            projected_sites: tuple[tuple[Fraction, Fraction], ...] = projected,
        ) -> np.ndarray:
            covers = [
                index
                for index, (site_u, site_v) in enumerate(projected_sites)
                if abs(site_u - u) <= half and abs(site_v - v) <= half
            ]
            return np.bincount(membership[covers], minlength=len(sites.orbits))

        for row_index in row_indices:
            cu_float, cv_float = rows.centres[row_index]
            cu, cv = Fraction(cu_float), Fraction(cv_float)
            if not admissible(cu, cv):
                outside.append({"row": row_index, "direction": direction_index})
            exact_row = coefficients(cu, cv)
            if not np.array_equal(exact_row, matrix[row_index]):
                delta = exact_row - matrix[row_index]
                entry = {
                    "row": row_index,
                    "direction": direction_index,
                    "different_columns": int(np.count_nonzero(delta)),
                    "exact_minus_float_positive": int(np.count_nonzero(delta > 0)),
                    "exact_minus_float_negative": int(np.count_nonzero(delta < 0)),
                }
                mismatch.append(entry)
                witness = None
                for exponent in (15, 14, 13, 12, 11, 10, 9, 8):
                    step = Fraction(1, 10**exponent)
                    for du, dv in (
                        (step, 0),
                        (-step, 0),
                        (0, step),
                        (0, -step),
                        (step, step),
                        (step, -step),
                        (-step, step),
                        (-step, -step),
                    ):
                        u, v = cu + du, cv + dv
                        if admissible(u, v) and np.array_equal(
                            coefficients(u, v), matrix[row_index]
                        ):
                            witness = {
                                **entry,
                                "u": str(u),
                                "v": str(v),
                                "shift_u": str(du),
                                "shift_v": str(dv),
                            }
                            break
                    if witness is not None:
                        break
                if witness is None:
                    unresolved.append(entry)
                else:
                    recovered.append(witness)
    report = {
        "selector": args.selector,
        "rounds": run.rounds,
        "rows": len(rows),
        "objective": run.objective,
        "stopped": run.stopped,
        "rows_checked": len(rows),
        "centres_outside_exact_domain": len(outside),
        "rows_different_from_exact_coverage": len(mismatch),
        "rows_with_nearby_exact_witness": len(recovered),
        "rows_without_exact_witness": len(unresolved),
        "outside_samples": outside[:20],
        "mismatch_samples": mismatch[:20],
        "recovered_witnesses": recovered,
        "unresolved_rows": unresolved,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return (
        0
        if run.stopped == "converged: every placement covers mass 1"
        and not outside
        and not unresolved
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
