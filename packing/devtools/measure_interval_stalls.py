#!/usr/bin/env python3
"""Measure the interval route at each of its two thresholds, and say where it stalls.

``sqpack.fractional.interval.verify_by_intervals`` runs its branch and bound against
one of two thresholds, and the difference is the whole of what this tool exists to
expose.

``condition5`` (``enclose=False``, the function's own default) settles a box as soon
as its lower bound reaches mass 1. That is Condition 5 and nothing more: the question
the theorem asks.

``enclosure`` (``enclose=True``) settles a box only against the least admissible point
value seen so far, which converges to the exact minimum. It therefore *pins* the least
covered mass, which is what ``devtools.decide_certificate`` needs in order to make the
two routes agree on a number rather than only on a verdict -- and it is the mode the
gate always runs.

The two can disagree, and the disagreement is diagnostic. A box that straddles a seam
-- one region's leave-edge on another's enter-edge, the case ``interval``'s own
``BOX_BUDGET`` comment describes -- cannot be split below ``RESOLUTION_FLOOR``, so it
is returned unresolved with a lower bound short of the true minimum by whatever the
seam costs. Under ``condition5`` that box is settled long before it stalls, provided
its bound clears 1. Under ``enclosure`` it stalls, the enclosure keeps a width, and the
gate refuses. The shortfall is a *relative* one, so reweighting the atom set moves both
ends of it together and cannot close it: a candidate refused this way is refused for
its geometry, not for its margin.

This tool decides nothing and retains nothing. ``devtools.decide_certificate`` is the
retention gate, it runs both routes on the frozen bytes, and a verdict from here is
evidence about *why* that gate says what it says -- never a substitute for it.

Usage, from ``packing/``::

    uv run --frozen --all-extras --group dev python -m devtools.measure_interval_stalls \\
        --source path/to/certificate.json --mode condition5 \\
        --report path/to/report.json --dump-stalls path/to/stalls.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import cast

from devtools.decide_certificate import load
from sqpack.fractional.interval import IntervalVerdict, verify_by_intervals

#: ``enclose`` for each mode name. ``condition5`` asks the theorem's question;
#: ``enclosure`` asks the gate's, which is strictly harder.
MODES = {"condition5": False, "enclosure": True}


def direction_rows(verdict: IntervalVerdict) -> list[dict[str, object]]:
    """One row per direction that stalled, was abandoned, or did not certify."""

    return [
        {
            "direction": outcome.label,
            "status": outcome.status,
            "boxes": outcome.boxes,
            "stalled": outcome.stalled,
            "budget_exhausted": outcome.budget_exhausted,
            "lower": None
            if outcome.lower is None
            else str(Fraction(outcome.lower, verdict.scale)),
            "upper": None
            if outcome.upper is None
            else str(Fraction(outcome.upper, verdict.scale)),
        }
        for outcome in verdict.directions
        if outcome.stalled or outcome.budget_exhausted or outcome.status != "certified"
    ]


def measure(source: Path, *, mode: str, stalls: Path | None) -> dict[str, object]:
    """Run one threshold over the frozen bytes and return what it did."""

    certificate, _ = load(source)
    stall_log: dict[str, list[list[float]]] = {}
    start = time.time()
    verdict = verify_by_intervals(
        certificate,
        enclose=MODES[mode],
        stall_log=stall_log if stalls is not None else None,
    )
    wall = time.time() - start
    enclosure = verdict.enclosure
    if stalls is not None:
        stalls.parent.mkdir(parents=True, exist_ok=True)
        stalls.write_text(
            json.dumps(
                {
                    "source": str(source),
                    "mode": mode,
                    "directions": {
                        label: {"count": len(boxes), "boxes": boxes}
                        for label, boxes in stall_log.items()
                        if boxes
                    },
                },
                indent=1,
            )
            + "\n"
        )
    return {
        "tool": "devtools.measure_interval_stalls",
        "source": str(source),
        "mode": mode,
        "enclose": MODES[mode],
        "n": certificate.n,
        "outer_side": str(certificate.outer_side),
        "atoms": len(certificate.atoms),
        "accepted": verdict.accepted,
        "failures": list(verdict.failures),
        "conditions": [
            {"name": condition.name, "status": condition.status, "detail": condition.detail}
            for condition in verdict.conditions
        ],
        "directions_searched": len(verdict.directions),
        "boxes": sum(outcome.boxes for outcome in verdict.directions),
        "stalled": sum(outcome.stalled for outcome in verdict.directions),
        "budget_exhausted": sum(outcome.budget_exhausted for outcome in verdict.directions),
        "enclosure": None if enclosure is None else [str(enclosure[0]), str(enclosure[1])],
        "enclosure_has_width": None if enclosure is None else enclosure[0] != enclosure[1],
        "unsettled_directions": direction_rows(verdict),
        "wall_seconds": round(wall, 1),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="the frozen candidate")
    parser.add_argument(
        "--mode",
        choices=sorted(MODES),
        required=True,
        help="condition5 settles boxes at mass 1; enclosure settles them at the minimum",
    )
    parser.add_argument("--report", type=Path, default=None, help="write the measurement here")
    parser.add_argument(
        "--dump-stalls", type=Path, default=None, help="write the stalled boxes as JSON"
    )
    args = parser.parse_args(argv)
    report = measure(args.source, mode=args.mode, stalls=args.dump_stalls)
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1) + "\n")
    print(
        f"{args.source}: mode {args.mode}, {report['directions_searched']} directions, "
        f"{report['boxes']} boxes, {report['stalled']} stalled, "
        f"accepted={report['accepted']} enclosure={report['enclosure']} "
        f"({report['wall_seconds']}s)",
        flush=True,
    )
    conditions = cast(list[dict[str, str]], report["conditions"])
    for condition in conditions:
        print(f"  {condition['status']:9} {condition['name']}", flush=True)
    print(
        "  NOT A RETENTION GATE: devtools.decide_certificate decides these bytes.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
