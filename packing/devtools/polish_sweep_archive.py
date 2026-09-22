#!/usr/bin/env python3
"""Polish an arm sweep's best pose per (cell, seed) with the LP-in-cell quench.

    polish_sweep_archive.py ARCHIVE.jsonl [ARCHIVE.jsonl ...] --json OUT.json

`run_arm_sweep.py` reports the side the annealer stopped at. That is the end of a
stochastic trajectory, not the bottom of the basin it is in: exp-001 read `n = 10` as a
polish failure because the search finds the right basin and stops `4.19e-04` short.
So the number a search round should be judged on is the *polished* side -- the annealer
pose run down to a fixed-cell local optimum by `sqpack.research.quench.quench_bracket`
-- and until this tool existed that step was taken in one-off code every time, which
`OR-1` says is a missing tool.

Three things it does that a loop over `quench_bracket` does not:

* **It reports the engine side and the polished side side by side**, so the polish's
  own contribution is visible rather than folded into one number. A polish that makes
  things worse is recorded as such and the engine pose is kept.
* **Nothing is reported that has not been repaired and re-checked.** The quench solves
  an LP, so its separations are non-negative only to solver tolerance. Every emitted
  pose is scaled apart about its centroid by the smallest factor that removes all
  penetration -- which can only *raise* the side, never flatter it -- re-measured, and
  emitted only when `sqpack.verify` agrees. The repair and the predicate are
  `run_basin_hopping`'s, so the two tools agree about what a contact is.
* **A side below the frontier record is a refusal, not a result.** It exits non-zero
  and says so on stderr. A record claim needs exact containment and exact
  disjointness, which an `f64` LP screen cannot supply at any tolerance.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from devtools.run_arm_sweep import frontier_best, grid_side
from devtools.run_basin_hopping import (
    POSE_TOLERANCE,
    repair,
    required_side,
    total_depth,
)
from sqpack.project import configured_project_root
from sqpack.research.quench import quench_bracket
from sqpack.verify import corners_from_poses, float_sign, verify_packing

ROOT = configured_project_root()
REPO = ROOT.parent


def shown(path: Path) -> str:
    """Repository-relative when it is inside the checkout, absolute otherwise."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def best_poses(paths: list[Path]) -> dict[tuple[int, int], dict[str, Any]]:
    """The lowest-side pose carrying coordinates, per (n, seed), over every archive.

    Both record kinds the engine writes -- `chain` and `summary` -- carry `x`, `y` and
    `t`, and the summary line repeats the best chain's pose. Taking the minimum over
    every line that has coordinates means nothing has to agree about which line is
    authoritative.
    """
    best: dict[tuple[int, int], dict[str, Any]] = {}
    for path in paths:
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if "best_side" not in record or "x" not in record:
                continue
            key = (int(record["n"]), int(record["seed"]))
            side = float(record["best_side"])
            if key not in best or side < float(best[key]["best_side"]):
                best[key] = {
                    "best_side": side,
                    "x": [float(v) for v in record["x"]],
                    "y": [float(v) for v in record["y"]],
                    "t": [float(v) for v in record["t"]],
                    "kind": record.get("kind"),
                    "chain": record.get("chain"),
                    "archive": shown(path),
                }
    return best


def separation(x: list[float], y: list[float], t: list[float]) -> float:
    """The least separating-axis gap over all pairs. Negative means a penetration.

    `run_basin_hopping.total_depth` answers only "is any pair overlapping"; a claimed
    improvement needs the *margin*, because a packing that clears the oracle's `1e-9`
    by `2e-9` and one that clears it by `1e-3` are not the same evidence.
    """
    least = math.inf
    for i in range(len(x)):
        ci, si = math.cos(t[i]), math.sin(t[i])
        for j in range(i + 1, len(x)):
            cj, sj = math.cos(t[j]), math.sin(t[j])
            dx, dy = x[i] - x[j], y[i] - y[j]
            half = 0.5 + 0.5 * (abs(ci * cj + si * sj) + abs(si * cj - ci * sj))
            least = min(
                least,
                max(
                    abs(dx * ci + dy * si) - half,
                    abs(dy * ci - dx * si) - half,
                    abs(dx * cj + dy * sj) - half,
                    abs(dy * cj - dx * sj) - half,
                ),
            )
    return least


def checked(x: list[float], y: list[float], t: list[float]) -> dict[str, Any] | None:
    """Repair, measure, and hand to the independent oracle. `None` if it refuses.

    The returned margins are what makes a reported side checkable rather than merely
    asserted: `separation` is how far the tightest pair is from touching, and
    `containment` how far the extreme corner is from the wall of the reported side.
    Both are zero-ish by construction at a tight packing; what would be alarming is a
    *negative* one, which the oracle also refuses.
    """
    x, y = repair(list(x), list(y), t)
    if total_depth(x, y, t) != 0.0:
        return None
    side = required_side(x, y, t)
    squares = corners_from_poses(x, y, t)
    xs = [px for square in squares for px, _ in square]
    ys = [py for square in squares for _, py in square]
    shifted = [[(px - min(xs), py - min(ys)) for px, py in square] for square in squares]
    report = verify_packing(shifted, side, sign=float_sign(POSE_TOLERANCE))
    if not report.valid:
        return None
    corners = [value for square in shifted for value in square]
    containment = min(min(px, py, side - px, side - py) for px, py in corners)
    return {
        "side": side,
        "x": x,
        "y": y,
        "separation": separation(x, y, t),
        "containment": containment,
    }


#: A round has to buy at least this much side to justify another one. HiGHS is asked
#: for 1e-10 feasibility, so anything smaller is the solver repeating itself.
ROUND_GAIN = 1e-12


def polish(
    pose: dict[str, Any], *, budget: float, rounds: int, deadline: float
) -> dict[str, Any]:
    """One (cell, seed): re-check the engine pose, quench it repeatedly, re-check.

    Repeatedly, because `quench_bracket` stops on its own cell conditions far more often
    than on its clock -- "re-read cell worse" and "cell cycle" are its two commonest
    exits on annealer output, and both leave an incumbent that is a perfectly good start
    for another bracket. Measured at `n = 19` on exp-202's archive, a single call used 4
    to 20 seconds of a 90-second budget and then stopped. Restarting from the *repaired*
    pose each time is what makes the next round a different problem.

    The loop ends when a round buys less than `ROUND_GAIN`, when the oracle refuses the
    round's pose, when `rounds` are used, or when the per-pose `deadline` passes.
    """
    started = time.time()
    x0, y0, t0 = pose["x"], pose["y"], pose["t"]
    engine = checked(x0, y0, t0)

    current = (list(x0), list(y0), list(t0))
    polished: dict[str, Any] | None = None
    theta = list(t0)
    trace: list[dict[str, Any]] = []
    lp_solves = 0
    for index in range(rounds):
        remaining = deadline - (time.time() - started)
        if remaining <= 0.0:
            break
        result = quench_bracket(
            list(current[0]), list(current[1]), list(current[2]),
            time_budget=min(budget, remaining),
        )  # fmt: skip
        lp_solves += result.lp_solves
        moved = [float(v) for v in result.theta]
        candidate = checked([float(v) for v in result.x], [float(v) for v in result.y], moved)
        trace.append(
            {
                "round": index,
                "side": None if candidate is None else candidate["side"],
                "converged": result.converged,
                "reason": result.reason,
                "seconds": round(time.time() - started, 3),
            }
        )
        if candidate is None:
            break
        improved = polished is None or candidate["side"] < polished["side"] - ROUND_GAIN
        if not improved:
            break
        polished = candidate
        theta = moved
        current = (list(candidate["x"]), list(candidate["y"]), list(moved))

    candidates: list[tuple[dict[str, Any], str, list[float]]] = []
    if engine is not None:
        candidates.append((engine, "engine", list(t0)))
    if polished is not None:
        candidates.append((polished, "polished", theta))
    kept = min(candidates, key=lambda c: c[0]["side"]) if candidates else None

    return {
        "engine_side_reported": pose["best_side"],
        "engine_side_rechecked": None if engine is None else engine["side"],
        "polished_side": None if polished is None else polished["side"],
        "best_verified_side": None if kept is None else kept[0]["side"],
        "best_verified_from": None if kept is None else kept[1],
        "least_pair_separation": None if kept is None else kept[0]["separation"],
        "least_containment_margin": None if kept is None else kept[0]["containment"],
        "quench_rounds": len(trace),
        "quench_converged": bool(trace and trace[-1]["converged"]),
        "quench_reason": trace[-1]["reason"] if trace else "no round ran",
        "quench_lp_solves": lp_solves,
        "quench_seconds": round(time.time() - started, 3),
        "quench_trace": trace,
        "pose": None if kept is None else {"x": kept[0]["x"], "y": kept[0]["y"], "t": kept[2]},
    }


def summarise(rows: list[dict[str, Any]], n: int) -> dict[str, Any]:
    """Per-cell statistics over the seeds whose pose survived the oracle."""
    sides = sorted(
        row["best_verified_side"] for row in rows if row["best_verified_side"] is not None
    )
    record, source = frontier_best(n)
    grid = grid_side(n)
    return {
        "n": n,
        "seeds": len(sides),
        "unadmitted_seeds": len(rows) - len(sides),
        "record": record,
        "record_source": source,
        "grid": grid,
        "median_side": statistics.median(sides) if sides else None,
        "best_side": sides[0] if sides else None,
        "worst_side": sides[-1] if sides else None,
        "best_gap_to_record": (sides[0] - record) if sides else None,
        "best_gap_to_grid": (sides[0] - grid) if sides else None,
        "at_grid_runs": sum(1 for s in sides if abs(s - grid) <= 1e-9),
        "below_grid_runs": sum(1 for s in sides if s < grid - 1e-9),
        "below_record_runs": sum(1 for s in sides if s < record - 1e-12),
    }


def num(value: float | None) -> str:
    """A side, or a dash where the oracle admitted nothing."""
    return "--" if value is None else f"`{value:.12f}`"


def margin(value: float | None) -> str:
    """A separation or containment margin, or a dash where there is none."""
    return "--" if value is None else f"`{value:+.2e}`"


def render(payload: dict[str, Any]) -> str:
    """The per-cell table, lifted from the payload and never retyped into prose."""
    lines = [
        "| n | record | grid | seeds | median | best | best - record | best - grid |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for cell in payload["cells"]:
        if cell["best_side"] is None:
            lines.append(
                f"| {cell['n']} | `{cell['record']:.6f}` | `{cell['grid']:.0f}` | 0 "
                "| -- | -- | -- | -- |"
            )
            continue
        lines.append(
            f"| {cell['n']} | `{cell['record']:.6f}` | `{cell['grid']:.0f}` "
            f"| {cell['seeds']} | `{cell['median_side']:.12f}` "
            f"| `{cell['best_side']:.12f}` "
            f"| `{cell['best_gap_to_record']:+.3e}` "
            f"| `{cell['best_gap_to_grid']:+.3e}` |"
        )
    lines.append("")
    lines.append(
        "| n | seed | engine | polished | kept | from | least pair gap "
        "| least wall gap | quench |"
    )
    lines.append("| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- |")
    lines.extend(
        f"| {row['n']} | {row['seed']} | {num(row['engine_side_rechecked'])} "
        f"| {num(row['polished_side'])} | {num(row['best_verified_side'])} "
        f"| {row['best_verified_from'] or '--'} "
        f"| {margin(row['least_pair_separation'])} "
        f"| {margin(row['least_containment_margin'])} "
        f"| {'converged' if row['quench_converged'] else row['quench_reason']} "
        f"({row['quench_rounds']} rounds, {row['quench_seconds']:.1f}s) |"
        for row in payload["rows"]
    )
    return "\n".join(lines)


def refusals(payload: dict[str, Any]) -> list[str]:
    """Why this payload must not pass: a refused pose, or a side below the record."""
    problems: list[str] = []
    for cell in payload["cells"]:
        if cell["unadmitted_seeds"]:
            problems.append(
                f"REFUSED: n={cell['n']}: {cell['unadmitted_seeds']} seed(s) produced no "
                "pose the oracle accepted"
            )
        if cell["below_record_runs"]:
            problems.append(
                f"BELOW RECORD: n={cell['n']}: {cell['below_record_runs']} verified run(s) "
                f"below the standing best {cell['record']} ({cell['record_source']}). "
                "This is an f64 screen, not a record: it needs exact containment and "
                "exact pairwise disjointness before it is anything."
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, nargs="+", help="arm-sweep JSONL archives")
    parser.add_argument("--json", type=Path, required=True, help="where the payload goes")
    parser.add_argument(
        "--quench-seconds", type=float, default=60.0, help="wall bound per quench call"
    )
    parser.add_argument(
        "--rounds", type=int, default=1, help="quench calls per pose, restarted each time"
    )
    parser.add_argument(
        "--pose-seconds", type=float, default=600.0, help="wall bound over all rounds"
    )
    parser.add_argument(
        "--cells", default="", help="comma-separated n to keep; empty keeps every cell"
    )
    options = parser.parse_args(argv)

    paths = [p if p.is_absolute() else ROOT / p for p in options.archives]
    missing = [shown(p) for p in paths if not p.exists()]
    if missing:
        print(f"refused: no such archive: {', '.join(missing)}", file=sys.stderr)
        return 1
    wanted = {int(v) for v in options.cells.split(",") if v.strip()}

    started = time.time()
    poses = best_poses(paths)
    rows: list[dict[str, Any]] = []
    for n, seed in sorted(poses):
        if wanted and n not in wanted:
            continue
        row = {"n": n, "seed": seed, "archive": poses[(n, seed)]["archive"]}
        row.update(
            polish(
                poses[(n, seed)],
                budget=options.quench_seconds,
                rounds=options.rounds,
                deadline=options.pose_seconds,
            )
        )
        rows.append(row)
        best = row["best_verified_side"]
        print(
            f"n={n} seed={seed} engine={row['engine_side_reported']:.12f} "
            f"kept={'none' if best is None else format(best, '.12f')} "
            f"{row['quench_seconds']:.1f}s",
            file=sys.stderr,
        )

    cells = sorted({row["n"] for row in rows})
    payload: dict[str, Any] = {
        "archives": [shown(p) for p in paths],
        "quench_seconds": options.quench_seconds,
        "quench_rounds_max": options.rounds,
        "pose_seconds": options.pose_seconds,
        "pose_tolerance": POSE_TOLERANCE,
        "host": {
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "loadavg": os.getloadavg(),
        },
        "seconds": round(time.time() - started, 3),
        "cells": [summarise([r for r in rows if r["n"] == n], n) for n in cells],
        "rows": rows,
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
