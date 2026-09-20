"""Fold the two writings of one upright square in a retained ceiling family.

`polish_ceiling_family.placement_orbits` refuses a record that repeats a placement
("merge duplicates first"), and a frozen cutting family trips that guard whenever a
reflection wrote an upright square twice: reflection maps half-tangent `t = 0` to
`(1 - 0) / (1 + 0) = 1`, which is the same geometry under another name. The fix is
the h216 recipe -- fold `t = 1` onto `t = 0` at the same centre and side and sum the
two weights -- and it is safe exactly because the two rows are one square, so the
family's total is unchanged and its depth is the depth it already had.

The defect this closes is process rather than mathematics. The recipe was applied by
a scratch script at h216 and again in Session 144 for exp-214 and exp-218, so the
retained merged bytes could not be re-derived by a command, which is what `OR-1`
forbids and what those two receipts name as tool debt.

The rule here is deliberately narrow. The only duplicate it will fold is one upright
square written once as `t = 0` and once as `t = 1`; any other repeated key -- a third
writing, two rows at the same tilted half-tangent, two rows both at `t = 0` -- is a
family this tool was not written for, and it aborts rather than quietly summing a
weight the depth argument never accounted for. `fold_half_tangent` is imported from
the polisher rather than restated, so the key that folds is the key that guard reads.

Run from `packing/`, with `uv run --frozen --all-extras --group dev` in front::

    python -m devtools.fold_ceiling_family FAMILY.json FAMILY-merged.json
    python -m devtools.fold_ceiling_family FAMILY.json OUT.json --check RETAINED.json

`--check` re-folds the source and compares the result against retained merged bytes --
placements as exact rationals, the total weight, and the folded count the retained
provenance claims -- printing every difference and exiting 1 if there is one. The
destination is always written, and may be neither the source nor the `--check` file.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools.polish_ceiling_family import fold_half_tangent
from sqpack.cover import write_text_atomic

TOOL = "devtools.fold_ceiling_family"
RULE = "fold half-tangent 1 to 0 at the same centre and side, summing weights"
UPRIGHT_WRITINGS = [Fraction(0), Fraction(1)]
REPORT_LIMIT = 10

Row = tuple[Fraction, Fraction, Fraction, Fraction, Fraction]
Key = tuple[Fraction, Fraction, Fraction, Fraction]


def placement_rows(record: dict[str, Any]) -> list[Row]:
    """Every placement as exact rationals: half-tangent, centre, weight, side."""

    rows: list[Row] = []
    for index, entry in enumerate(record["placements"]):
        values = [Fraction(value) for value in entry]
        if len(values) != 5:
            raise ValueError(f"placement {index} has {len(values)} fields, not 5")
        rows.append((values[0], values[1], values[2], values[3], values[4]))
    return rows


def fold(record: dict[str, Any]) -> dict[str, Any]:
    """The record with each upright square written once, and the total unchanged.

    Keys are `(folded half-tangent, centre x, centre y, side)`, the key
    `placement_orbits` deduplicates on. A key seen twice is folded only when its two
    writings are `t = 0` and `t = 1`; every other repeat raises. Order of first
    appearance is preserved, the caller's record is not mutated, and the arithmetic
    is exact, so the total weight out equals the total weight in.
    """

    rows = placement_rows(record)
    weights: dict[Key, Fraction] = {}
    writings: dict[Key, list[Fraction]] = {}
    order: list[Key] = []
    folded = 0
    for half_tangent, x, y, weight, side in rows:
        key = (fold_half_tangent(half_tangent), x, y, side)
        seen = writings.setdefault(key, [])
        if seen:
            if sorted([*seen, half_tangent]) != UPRIGHT_WRITINGS:
                named = ", ".join(str(t) for t in [*seen, half_tangent])
                raise ValueError(
                    "the record repeats a placement that is not one upright square: "
                    f"centre ({x}, {y}), side {side}, half-tangents {named}"
                )
            folded += 1
            weights[key] += weight
        else:
            weights[key] = weight
            order.append(key)
        seen.append(half_tangent)

    before = sum((row[3] for row in rows), Fraction(0))
    after = sum(weights.values(), Fraction(0))
    if before != after:
        raise ValueError(f"the fold changed the total weight: {before} became {after}")

    folded_record = dict(record)
    folded_record["placements"] = [
        [str(t), str(x), str(y), str(weights[(t, x, y, s)]), str(s)] for (t, x, y, s) in order
    ]
    folded_record["total_weight"] = str(after)
    folded_record["total_weight_float"] = float(after)
    provenance = dict(folded_record.get("provenance") or {})
    provenance["merge"] = {
        "tool": TOOL,
        "rule": RULE,
        "placements_before": len(rows),
        "placements_after": len(order),
        "folded": folded,
        "total_weight_preserved": str(after),
    }
    folded_record["provenance"] = provenance
    return folded_record


def folded_count(record: dict[str, Any]) -> int | None:
    """What a merged record's own provenance says it folded, if it says anything."""

    provenance = record.get("provenance")
    merge = provenance.get("merge") if isinstance(provenance, dict) else None
    count = merge.get("folded") if isinstance(merge, dict) else None
    return count if isinstance(count, int) else None


def differences(folded: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Every way the fold and the retained bytes disagree mathematically.

    Provenance is not compared: a retained record may name the scratch script that
    wrote it, and what has to match is the geometry, the weights and the total.
    """

    report: list[str] = []
    ours = placement_rows(folded)
    theirs = placement_rows(expected)
    if len(ours) != len(theirs):
        report.append(f"placement count: fold has {len(ours)}, expected has {len(theirs)}")
    if sorted(ours) == sorted(theirs):
        if ours != theirs:
            report.append("the same placements in a different order")
    else:
        mismatched = [
            (index, ours[index], theirs[index])
            for index in range(min(len(ours), len(theirs)))
            if ours[index] != theirs[index]
        ]
        for index, ours_row, theirs_row in mismatched[:REPORT_LIMIT]:
            report.append(
                f"placement {index}: fold {[str(v) for v in ours_row]} "
                f"!= expected {[str(v) for v in theirs_row]}"
            )
        if len(mismatched) > REPORT_LIMIT:
            report.append(f"... and {len(mismatched) - REPORT_LIMIT} further placements differ")

    ours_total = Fraction(folded["total_weight"])
    theirs_total = Fraction(expected["total_weight"])
    if ours_total != theirs_total:
        report.append(f"total weight: fold {ours_total} != expected {theirs_total}")

    claimed = folded_count(expected)
    ours_folded = folded_count(folded)
    if claimed is not None and claimed != ours_folded:
        report.append(f"folded count: fold {ours_folded} != expected {claimed}")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="the raw family to fold")
    parser.add_argument("destination", type=Path, help="where the folded family is written")
    parser.add_argument(
        "--check",
        type=Path,
        help="retained merged bytes the fold must reproduce; exits 1 on any difference",
    )
    args = parser.parse_args(argv)
    if args.destination.resolve() == args.source.resolve():
        parser.error("the source must be preserved; choose a separate destination")
    if args.check is not None and args.destination.resolve() == args.check.resolve():
        parser.error("--check compares against retained bytes; do not overwrite them")

    record: dict[str, Any] = json.loads(args.source.read_text(encoding="utf-8"))
    output = fold(record)
    write_text_atomic(args.destination, json.dumps(output, indent=1) + "\n")
    merge = output["provenance"]["merge"]
    print(
        json.dumps(
            {
                "source": str(args.source),
                "destination": str(args.destination),
                "placements_before": merge["placements_before"],
                "placements_after": merge["placements_after"],
                "folded": merge["folded"],
                "total_weight": merge["total_weight_preserved"],
                "total_weight_float": output["total_weight_float"],
            }
        ),
        flush=True,
    )
    if args.check is None:
        return 0

    expected: dict[str, Any] = json.loads(args.check.read_text(encoding="utf-8"))
    report = differences(output, expected)
    for line in report:
        print(line, flush=True)
    claimed = folded_count(expected)
    print(
        json.dumps(
            {
                "check": str(args.check),
                "matches": not report,
                "placements": len(expected["placements"]),
                "expected_folded": claimed,
                "differences": len(report),
            }
        ),
        flush=True,
    )
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
