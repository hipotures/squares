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

`--check` re-folds the source and compares the result against retained merged bytes,
printing every difference and exiting 1 if there is one: the container and net the
family is a ceiling for (`n`, `outer_side`, `square_side`, `half_tangents`), the
placements as exact rationals **in order**, the total weight, and the folded count the
retained provenance claims. Row order is part of the contract rather than an
incidental: the fold emits keys in order of first appearance, so the same source rows
always fold to the same sequence, and an order difference means the bytes were not
re-derived from these rows by this rule. Provenance is not compared, because a retained
record may name the scratch script that wrote it. The destination is always written,
and may be neither the source nor the `--check` file.

A refusal is a printed line and a non-zero exit, as at the sibling devtools, not a
traceback; every rational is read from a string, so a placement or a total written as a
JSON float is refused rather than silently binarised.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from devtools.polish_ceiling_family import fold_half_tangent
from sqpack.cover import write_text_atomic

TOOL = "devtools.fold_ceiling_family"
RULE = "fold half-tangent 1 to 0 at the same centre and side, summing weights"
UPRIGHT_WRITINGS = [Fraction(0), Fraction(1)]
REPORT_LIMIT = 10


class FamilyFormatError(ValueError):
    """The JSON cannot be read as an exact ceiling family.

    A `ValueError` so that `main`'s refusal path and every caller that already treats a
    malformed family as a refusal keep working unchanged, named so the refusals this
    module raises about its input are distinguishable from the arithmetic ones.
    """


Row = tuple[Fraction, Fraction, Fraction, Fraction, Fraction]
Key = tuple[Fraction, Fraction, Fraction, Fraction]


def load(path: Path) -> dict[str, Any]:
    """One family record, or a refusal naming the file rather than a traceback."""

    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path} is not JSON: {error}") from error
    if not isinstance(record, dict):
        raise FamilyFormatError(f"{path} is not a family record object")
    return cast("dict[str, Any]", record)


def exact(value: object, where: str) -> Fraction:
    """One exact rational, read from its string spelling and nothing else.

    A JSON float has already lost the value by the time this sees it, so it is refused
    rather than binarised -- which is what every other exact-rational reader in this
    area does, and what a tool that claims to preserve a total exactly has to do.
    """

    if not isinstance(value, str):
        raise FamilyFormatError(
            f"{where}: exact rationals are written as strings, got {type(value).__name__} "
            f"{value!r}"
        )
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        message = f"{where}: {value!r} is not an exact rational ({error})"
        raise FamilyFormatError(message) from error


def placement_rows(record: dict[str, Any]) -> list[Row]:
    """Every placement as exact rationals: half-tangent, centre, weight, side."""

    placements = record.get("placements")
    if not isinstance(placements, list):
        raise FamilyFormatError("the record has no 'placements' list")
    rows: list[Row] = []
    for index, entry in enumerate(placements):
        if not isinstance(entry, list):
            raise FamilyFormatError(f"placement {index} is not a list")
        if len(entry) != 5:
            raise ValueError(f"placement {index} has {len(entry)} fields, not 5")
        values = [
            exact(value, f"placement {index} field {field}")
            for field, value in enumerate(entry)
        ]
        rows.append((values[0], values[1], values[2], values[3], values[4]))
    return rows


def declared_total(record: dict[str, Any], where: str) -> Fraction:
    """The total the record's own header declares, as an exact rational."""

    if "total_weight" not in record:
        raise ValueError(f"{where}: the record declares no total_weight")
    return exact(record["total_weight"], f"{where}: total_weight")


def fold(record: dict[str, Any]) -> dict[str, Any]:
    """The record with each upright square written once, and the total unchanged.

    Keys are `(folded half-tangent, centre x, centre y, side)`, the key
    `placement_orbits` deduplicates on. A key seen twice is folded only when its two
    writings are `t = 0` and `t = 1`; every other repeat raises. Order of first
    appearance is preserved, the caller's record is not mutated, and the arithmetic
    is exact, so the total weight out equals the total weight in.

    Two total checks, both with content. First the record is required to be internally
    consistent: its declared `total_weight` must equal the sum of its own rows, so a
    header that disagrees with its placements is refused rather than silently corrected
    into a self-consistent record and then reported as preserved. Then the emitted
    placement strings are summed back and required to equal that same declared total,
    which exercises the serialisation the destination actually receives. The earlier
    `before != after` guard compared a sum with itself and could not fire (review
    finding M2).
    """

    rows = placement_rows(record)
    declared = declared_total(record, "the source family")
    summed = sum((row[3] for row in rows), Fraction(0))
    if declared != summed:
        raise ValueError(
            f"the record's declared total_weight {declared} is not the sum of its own "
            f"placements {summed}; the bytes are internally inconsistent"
        )
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

    folded_record = dict(record)
    folded_record["placements"] = [
        [str(t), str(x), str(y), str(weights[(t, x, y, s)]), str(s)] for (t, x, y, s) in order
    ]
    after = sum((row[3] for row in placement_rows(folded_record)), Fraction(0))
    if after != declared:
        raise ValueError(f"the fold changed the total weight: {declared} became {after}")
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


def required(record: dict[str, Any], field: str, where: str) -> object:
    """One field a ceiling family always carries, or a refusal naming it."""

    if field not in record:
        raise ValueError(f"{where}: the record declares no {field}")
    return record[field]


def net(record: dict[str, Any], where: str) -> list[Fraction]:
    """The record's half-tangent net as exact rationals, in the order written."""

    values = required(record, "half_tangents", where)
    if not isinstance(values, list):
        raise FamilyFormatError(f"{where}: half_tangents is not a list")
    return [
        exact(value, f"{where}: half_tangents[{index}]") for index, value in enumerate(values)
    ]


def container_differences(folded: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Every way the two records describe a different problem.

    `n`, `outer_side`, `square_side` and `half_tangents` say which container and which
    net the family is a ceiling for, and `fold` carries all four through from the source
    untouched. Comparing only the rows made `--check` report `matches: true` for
    retained bytes describing a different container (review finding M3), which is the
    opposite of what the flag is for.
    """

    report: list[str] = []
    if folded.get("n") != expected.get("n"):
        report.append(f"n: fold {folded.get('n')!r} != expected {expected.get('n')!r}")
    for field in ("outer_side", "square_side"):
        ours = exact(required(folded, field, "fold"), f"fold: {field}")
        theirs = exact(required(expected, field, "expected"), f"expected: {field}")
        if ours != theirs:
            report.append(f"{field}: fold {ours} != expected {theirs}")
    ours_net = net(folded, "fold")
    theirs_net = net(expected, "expected")
    if ours_net != theirs_net:
        report.append(
            f"half_tangents: fold has {len(ours_net)}, expected has {len(theirs_net)}"
            if len(ours_net) != len(theirs_net)
            else "half_tangents: the same count in a different order or at other values"
        )
    return report


def differences(folded: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    """Every way the fold and the retained bytes disagree mathematically.

    The container and net come first (`container_differences`), then the placements in
    order, the total and the folded count. Row order counts: the fold emits keys in
    order of first appearance, so re-folding the same source always gives the same
    sequence, and a permutation means the retained bytes were not produced from these
    rows by this rule -- the docstrings now say so rather than calling order incidental
    (review finding M3).

    Provenance is not compared: a retained record may name the scratch script that
    wrote it, and what has to match is the problem, the geometry, the weights and the
    total.
    """

    report: list[str] = container_differences(folded, expected)
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

    ours_total = declared_total(folded, "fold")
    theirs_total = declared_total(expected, "expected")
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

    try:
        record = load(args.source)
        output = fold(record)
    except (ValueError, OSError) as error:
        # A refusal line and a non-zero exit, as at the sibling devtools, rather than a
        # traceback on a malformed family (review finding L2).
        print(json.dumps({"tool": TOOL, "source": str(args.source), "refused": str(error)}))
        return 2
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

    try:
        expected = load(args.check)
        report = differences(output, expected)
        claimed = folded_count(expected)
        placements = len(placement_rows(expected))
    except (ValueError, OSError) as error:
        print(json.dumps({"tool": TOOL, "check": str(args.check), "refused": str(error)}))
        return 2
    for line in report:
        print(line, flush=True)
    print(
        json.dumps(
            {
                "check": str(args.check),
                "matches": not report,
                "placements": placements,
                "expected_folded": claimed,
                "differences": len(report),
            }
        ),
        flush=True,
    )
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
