#!/usr/bin/env python3
"""One-sided tilt slopes of a known-best witness, by the fixed-cell LP.

    measure_tilt_slopes.py --cells 18,19,26 --json OUT.json

Several retained records are *axis-plus-one-angle*: every square is either axis aligned
or carries one common tilt. `n = 19` is 11 at `0` and 8 at `45`, `n = 26` is 17 at `0`
and 9 at `45`, `n = 18` is 10 at `0` and 8 at `24.2951889`. Inside that family the side
is a function of the single tilt once the centres are re-optimised, and re-optimising
the centres at a fixed tilt is exactly the LP `sqpack.research.quench` solves.

So the record's local optimality within its own family is a two-number question: move
the common tilt by `+delta` and by `-delta`, re-solve the centres and the side, and ask
whether the side went **up both times**. A negative one-sided slope is not a rounding
artefact, it is a smaller packing in the same family.

**One-sided, never a central difference.** `H-019` measured a genuine kink at `n = 11`,
one-sided slopes `0.175` and `0.384` about the same point; a two-sided finite difference
there reports the average of two different derivatives and can be any sign. The two
branches are therefore computed and reported separately and never averaged.

**The re-solve is a fixed *point*, not a single LP.** `solve_to_fixed_point` re-reads
the cell from its own solution and repeats, because one `solve_cell` returns an upper
bound that depends on where the caller started. A run whose fixed point did not settle
is reported with `settled: false` and carries no verdict.

The value at `delta = 0` is reported too, against the witness's published side. It is an
independent reading of the record: the LP may not reproduce the published side from the
published centres, and if it comes out *below*, that is its own finding.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from sqpack.project import configured_project_root
from sqpack.research.quench import solve_to_fixed_point
from sqpack.yamlio import safe_load

ROOT = configured_project_root()
REPO = ROOT.parent

#: Below this the branch is called flat rather than signed: the LP is asked for 1e-10
#: primal feasibility, so a slope built from differences near that scale is solver noise.
SLOPE_NOISE = 1e-7


def shown(path: Path) -> str:
    """Repository-relative when it is inside the checkout, absolute otherwise."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def witness_pose(n: int) -> dict[str, Any]:
    """The known-best witness as `f64` centres and radian angles, plus its classes."""
    path = ROOT / "witnesses" / "known-best" / f"n-{n:03d}.yaml"
    witness = safe_load(path.read_text())["witness"]
    if witness["representation"] != "center-angle":
        message = f"n={n}: witness is {witness['representation']}, not center-angle"
        raise SystemExit(message)
    if witness["coordinates"]["angle_unit"] != "degrees":
        message = f"n={n}: witness angles are not in degrees"
        raise SystemExit(message)
    squares = witness["squares"]
    x = [float(square["center"][0]) for square in squares]
    y = [float(square["center"][1]) for square in squares]
    degrees = [float(square["angle"]) for square in squares]
    classes: dict[str, list[int]] = {}
    for index, degree in enumerate(degrees):
        classes.setdefault(f"{degree:.9f}", []).append(index)
    return {
        "witness": shown(path),
        "n": n,
        "published_side": float(witness["side"]),
        "x": x,
        "y": y,
        "degrees": degrees,
        "theta": [math.radians(degree) for degree in degrees],
        "classes": classes,
    }


def tilt_class(pose: dict[str, Any]) -> tuple[str, list[int]]:
    """The single non-axis angle class. Refuses anything that is not one common tilt."""
    tilted = {key: members for key, members in pose["classes"].items() if float(key) != 0.0}
    if len(tilted) != 1:
        message = (
            f"n={pose['n']}: expected exactly one non-axis angle class, "
            f"found {sorted(pose['classes'])}"
        )
        raise SystemExit(message)
    return next(iter(tilted.items()))


def solve_at(pose: dict[str, Any], members: list[int], delta: float) -> dict[str, Any]:
    """Re-solve centres and side with the tilted class moved by `delta` radians."""
    theta = list(pose["theta"])
    for index in members:
        theta[index] += delta
    started = time.time()
    result = solve_to_fixed_point(theta, list(pose["x"]), list(pose["y"]), pose["n"])
    if result is None:
        return {
            "delta": delta,
            "side": None,
            "settled": False,
            "reason": "initial cell infeasible",
            "seconds": round(time.time() - started, 3),
        }
    return {
        "delta": delta,
        "side": float(result.side),
        "settled": bool(result.settled),
        "reason": result.reason,
        "lp_solves": result.solves,
        "cell_changes": result.changes,
        "seconds": round(time.time() - started, 3),
    }


def branch(base: float | None, moved: dict[str, Any], delta: float) -> dict[str, Any]:
    """One one-sided slope: `(s(base +- delta) - s(base)) / delta`, sign kept."""
    if base is None or moved["side"] is None or not moved["settled"]:
        return {"slope": None, "verdict": "unsettled"}
    slope = (moved["side"] - base) / abs(delta)
    if abs(moved["side"] - base) <= SLOPE_NOISE:
        verdict = "flat-within-solver-noise"
    elif slope > 0.0:
        verdict = "positive"
    else:
        verdict = "NEGATIVE"
    return {"slope": slope, "difference": moved["side"] - base, "verdict": verdict}


def measure(n: int, deltas: list[float]) -> dict[str, Any]:
    """Both one-sided slopes at each delta, plus the delta-zero reading."""
    pose = witness_pose(n)
    key, members = tilt_class(pose)
    at_zero = solve_at(pose, members, 0.0)
    base = at_zero["side"] if at_zero["settled"] else None
    branches: list[dict[str, Any]] = []
    for delta in deltas:
        plus = solve_at(pose, members, delta)
        minus = solve_at(pose, members, -delta)
        branches.append(
            {
                "delta_rad": delta,
                "delta_deg": math.degrees(delta),
                "plus": {**plus, **branch(base, plus, delta)},
                "minus": {**minus, **branch(base, minus, delta)},
            }
        )
    return {
        "n": n,
        "witness": pose["witness"],
        "published_side": pose["published_side"],
        "tilt_deg": float(key),
        "tilted_squares": len(members),
        "axis_squares": pose["n"] - len(members),
        "at_zero": at_zero,
        "lp_minus_published": None if base is None else base - pose["published_side"],
        "branches": branches,
    }


def cell_side(entry: dict[str, Any]) -> str:
    """A solved side, or a dash where the fixed point did not settle."""
    return "--" if entry["side"] is None else f"`{entry['side']:.12f}`"


def cell_slope(entry: dict[str, Any]) -> str:
    """A one-sided slope, or a dash where there is none to report."""
    return "--" if entry["slope"] is None else f"`{entry['slope']:+.6e}`"


def render(payload: dict[str, Any]) -> str:
    """The slope table, lifted from the payload and never retyped into prose."""
    lines = [
        "| n | tilt (deg) | tilted | published side | LP at delta=0 | LP - published |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cell in payload["cells"]:
        drift = cell["lp_minus_published"]
        lines.append(
            f"| {cell['n']} | `{cell['tilt_deg']:.7f}` | {cell['tilted_squares']} "
            f"| `{cell['published_side']:.12f}` | {cell_side(cell['at_zero'])} "
            f"| {'--' if drift is None else f'`{drift:+.3e}`'} |"
        )
    lines.append("")
    lines.append("| n | delta (rad) | s(+delta) | slope + | s(-delta) | slope - | verdict |")
    lines.append("| ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for cell in payload["cells"]:
        for item in cell["branches"]:
            plus, minus = item["plus"], item["minus"]
            lines.append(
                f"| {cell['n']} | `{item['delta_rad']:.1e}` "
                f"| {cell_side(plus)} | {cell_slope(plus)} "
                f"| {cell_side(minus)} | {cell_slope(minus)} "
                f"| {plus['verdict']} / {minus['verdict']} |"
            )
    return "\n".join(lines)


def refusals(payload: dict[str, Any]) -> list[str]:
    """A negative one-sided slope is a sub-record candidate and stops this tool."""
    problems: list[str] = []
    for cell in payload["cells"]:
        for item in cell["branches"]:
            for name in ("plus", "minus"):
                entry = item[name]
                if entry["verdict"] == "NEGATIVE":
                    problems.append(
                        f"NEGATIVE SLOPE: n={cell['n']} {name} branch at delta="
                        f"{item['delta_rad']:.1e} rad gives side {entry['side']:.12f} "
                        f"against {cell['at_zero']['side']:.12f} at the witness tilt. "
                        "Inside the axis-plus-one-angle family this is a smaller packing; "
                        "it is an f64 LP screen and needs exact containment and exact "
                        "pairwise disjointness before it is anything."
                    )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", required=True, help="comma-separated n")
    parser.add_argument(
        "--deltas",
        default="1e-3,1e-4,1e-5",
        help="comma-separated tilt perturbations, in radians",
    )
    parser.add_argument("--json", type=Path, required=True, help="where the payload goes")
    options = parser.parse_args(argv)

    cells = [int(value) for value in options.cells.split(",")]
    deltas = [float(value) for value in options.deltas.split(",")]
    if any(delta <= 0.0 for delta in deltas):
        print("refused: every delta must be positive", file=sys.stderr)
        return 1

    started = time.time()
    payload: dict[str, Any] = {
        "cells": [measure(n, deltas) for n in cells],
        "deltas_rad": deltas,
        "slope_noise_floor": SLOPE_NOISE,
        "host": {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "loadavg": os.getloadavg(),
        },
        "seconds": round(time.time() - started, 3),
    }
    out = options.json if options.json.is_absolute() else ROOT / options.json
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(render(payload))
    print(json.dumps({"wrote": shown(out)}))

    problems = refusals(payload)
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
