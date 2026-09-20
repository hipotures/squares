"""Source-bound exact C charge sweep and S first-owner filter for BC303 T2.

The C open-cell reduction and the S strip are proved in the accepted charge bridge.
A low S strip charge is only failure of a sufficient test, not an S witness.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction
from itertools import pairwise
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from cases.n11_five_dot_cover.bc303_t2_geometry_control import (
    DELTA,
    MARKS,
    MAX_T,
    A,
    H,
    Point,
    Q,
    add,
    axis_set,
    bins,
    dot,
    edges,
    labels,
    ray,
    scale,
    square,
    turn,
)

SCALE = 4_000_000
C_POSITIVE = 4_524_200
S_FIRST_POSITIVE = 4_524_185
ATOM_COUNT = 377
TOTAL_INTEGER_MASS = 45_048_398
DIRECTION_STEPS = 180
SOURCE_REVISION = "8f4eca7d23cdfc32091b9f783fdcadf7cb269615"
SOURCE_PATH = (
    "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/"
    "bc-293-measure-free-96-25.json"
)
# 2026-09-20: re-bound to 8f4eca7d after the corner-clip instrument (Session 145,
# PR 206) changed these modules on clip-free-identical code paths; the replay
# reproduced the retained determination unchanged.
SOURCE_FILES = (
    SOURCE_PATH,
    "packing/devtools/owner_footprints.py",
    "packing/src/sqpack/fractional/adaptive.py",
    "packing/src/sqpack/fractional/model.py",
    "packing/src/sqpack/fractional/sweep.py",
    "packing/cases/n11_five_dot_cover/wall-containment-contract.md",
)
REPO = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class AtomMass:
    point: Point
    integer_weight: int


@dataclass(frozen=True, slots=True)
class Chart:
    index: int
    reflected: bool
    selected_ray: Point
    lower_tangent: Fraction
    upper_tangent: Fraction
    x_cut: Fraction

    @property
    def axis(self) -> bool:
        return self.index == 0


@dataclass(frozen=True, slots=True)
class Cell:
    x_low: Fraction
    x_high: Fraction
    y_low: Fraction
    y_high: Fraction


@dataclass(frozen=True, slots=True)
class Minimum:
    integer_mass: int
    chart: Chart
    cell: Cell


class RangeMinimum:
    """Integer range addition and stable leftmost minimum over open y intervals."""

    def __init__(self, count: int) -> None:
        if count <= 0:
            raise ValueError("the y arrangement needs an open interval")
        self.count = count
        self.minimum = [0] * (4 * count)
        self.lazy = [0] * (4 * count)

    def add(self, left: int, right: int, amount: int) -> None:
        def visit(node: int, start: int, end: int) -> None:
            if right <= start or end <= left:
                return
            if left <= start and end <= right:
                self.minimum[node] += amount
                self.lazy[node] += amount
                return
            middle = (start + end) // 2
            visit(node * 2, start, middle)
            visit(node * 2 + 1, middle, end)
            self.minimum[node] = self.lazy[node] + min(
                self.minimum[node * 2], self.minimum[node * 2 + 1]
            )

        if not 0 <= left <= right <= self.count:
            raise ValueError("range update outside the y arrangement")
        if left < right:
            visit(1, 0, self.count)

    def prefix_minimum(self, stop: int) -> tuple[int, int]:
        if not 0 < stop <= self.count:
            raise ValueError("prefix must contain an open y interval")

        def visit(node: int, start: int, end: int, carry: int) -> tuple[int, int]:
            if end <= stop:
                if end - start == 1:
                    return carry + self.minimum[node], start
                if self.minimum[node * 2] <= self.minimum[node * 2 + 1]:
                    return visit(node * 2, start, (start + end) // 2, carry + self.lazy[node])
                return visit(node * 2 + 1, (start + end) // 2, end, carry + self.lazy[node])
            middle = (start + end) // 2
            if stop <= middle:
                return visit(node * 2, start, middle, carry + self.lazy[node])
            first = visit(node * 2, start, middle, carry + self.lazy[node])
            second = visit(node * 2 + 1, middle, end, carry + self.lazy[node])
            return min(first, second)

        return visit(1, 0, self.count, 0)


def git_bytes(revision: str, relative_path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(REPO), "show", f"{revision}:{relative_path}"],
        capture_output=True,
        check=True,
    ).stdout


def source_atoms() -> tuple[AtomMass, ...]:
    """Compare every source byte with the reviewed revision before parsing rows."""
    reviewed_atoms = git_bytes(SOURCE_REVISION, SOURCE_PATH)
    for relative_path in SOURCE_FILES:
        current = (REPO / relative_path).read_bytes()
        if current != git_bytes(SOURCE_REVISION, relative_path):
            raise ValueError(f"reviewed source differs: {relative_path}")
    return parse_atom_rows((REPO / SOURCE_PATH).read_bytes(), reviewed_atoms)


def parse_atom_rows(current: bytes, reviewed: bytes) -> tuple[AtomMass, ...]:
    """The byte comparison detects a changed row before any charge can be used."""
    if current != reviewed:
        raise ValueError("the atom source differs from the reviewed Git revision")
    payload = json.loads(current)
    if (
        payload["outer_side"] != "96/25"
        or payload["square_side"] != "9977/10000"
        or payload["angle_limit"] != "207107/500000"
        or payload["direction_steps"] != DIRECTION_STEPS
        or payload["least_cell_mass"] != "800003/800000"
        or payload["total_mass"] != "22524199/2000000"
        or payload["symmetry"] != "D4"
    ):
        raise ValueError("BC293 source header differs from the frozen domain")
    rows = payload["atoms"]
    if len(rows) != ATOM_COUNT:
        raise ValueError("BC293 source needs exactly 377 atoms")
    atoms: list[AtomMass] = []
    sites: set[Point] = set()
    for row in rows:
        if (
            not isinstance(row, list)
            or len(row) != 3
            or any(not isinstance(v, str) for v in row)
        ):
            raise ValueError("an atom row is not three rational strings")
        x, y, weight = map(Fraction, row)
        if not (0 <= x <= Q and 0 <= y <= Q and weight >= 0):
            raise ValueError("an atom lies outside the nonnegative source contract")
        scaled = weight * SCALE
        if scaled.denominator != 1 or (x, y) in sites:
            raise ValueError("an atom weight is off the integer grid or its site repeats")
        atoms.append(AtomMass((x, y), int(scaled)))
        sites.add((x, y))
    if sum(atom.integer_weight for atom in atoms) != TOTAL_INTEGER_MASS:
        raise ValueError("the 377 atom weights do not sum to the retained total")
    return tuple(atoms)


def execution_revision(expected: str) -> str:
    """Resolve Git at this module's path, never at the caller's working directory."""
    actual = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if len(expected) != 40 or expected != actual:
        raise ValueError(
            f"wrong executing checkout revision: expected {expected}, actual {actual}"
        )
    dirty = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if dirty:
        raise ValueError("target run requires a clean committed checkout")
    return actual


def charts() -> tuple[Chart, ...]:
    tangents = tuple(MAX_T * index / DIRECTION_STEPS for index in range(DIRECTION_STEPS + 1))
    seams = (
        Fraction(0),
        *((left + right) / (1 - left * right) for left, right in pairwise(tangents)),
        Fraction(1),
    )
    result: list[Chart] = []
    for index, tangent in enumerate(tangents):
        original = ray(tangent)
        for reflected in (False, True):
            source_ray = (original[1], original[0]) if reflected else original
            selected = [candidate for candidate in axis_set(source_ray) if 0 in bins(candidate)]
            if not selected:
                continue
            if len(selected) != 1:
                raise ValueError("source chart has ambiguous bin-0 first ray")
            c, s = selected[0]
            result.append(
                Chart(
                    index=index,
                    reflected=reflected,
                    selected_ray=(c, s),
                    lower_tangent=seams[index],
                    upper_tangent=seams[index + 1],
                    x_cut=H - DELTA * (c - s),
                )
            )
    validate_manifest(tuple(result))
    return tuple(result)


def validate_manifest(manifest: tuple[Chart, ...]) -> None:
    expected = {(0, False), (0, True), (DIRECTION_STEPS, True)} | {
        (index, False) for index in range(1, DIRECTION_STEPS)
    }
    identities = {(chart.index, chart.reflected) for chart in manifest}
    if (
        len(manifest) != 182
        or identities != expected
        or len({c.selected_ray for c in manifest}) != 181
    ):
        raise ValueError("the complete 182-chart source manifest is missing or duplicated")
    if any(not 0 < c.x_cut < H for c in manifest):
        raise ValueError("source C/S cut is not interior")


def wall_cell_feasible(chart: Chart, x_high: Fraction, y_low: Fraction) -> bool:
    if chart.axis:
        return True
    c, s = chart.selected_ray
    maximum = A + c * x_high - s * y_low
    if maximum <= 0:
        raise ValueError("left-wall maximum must be positive before squaring")
    lower = chart.lower_tangent
    return 4 * maximum * maximum * (1 + lower * lower) > (1 + lower) ** 2


def charge_at(atoms: tuple[AtomMass, ...], centre: Point, core_ray: Point) -> int:
    transverse = turn(core_ray)
    return sum(
        atom.integer_weight
        for atom in atoms
        if abs(dot((atom.point[0] - centre[0], atom.point[1] - centre[1]), core_ray)) <= H
        and abs(dot((atom.point[0] - centre[0], atom.point[1] - centre[1]), transverse)) <= H
    )


def sweep_chart(
    chart: Chart, atoms: tuple[AtomMass, ...]
) -> tuple[Minimum, Minimum, dict[str, int]]:
    """Query C and S from one exact open-cell arrangement for one source chart."""
    if not 0 < chart.x_cut < H or (chart.axis and not 0 < DELTA < H):
        raise ValueError("open-cell reduction refuses a lower-dimensional domain")
    x_levels = {Fraction(0), chart.x_cut, H}
    y_levels = {Fraction(0), H}
    if chart.axis:
        y_levels.add(DELTA)
    rectangles: list[tuple[Fraction, Fraction, Fraction, Fraction, int]] = []
    transverse = turn(chart.selected_ray)
    for atom in atoms:
        displacement = (atom.point[0] - MARKS[0][0], atom.point[1] - MARKS[0][1])
        u, v = dot(displacement, chart.selected_ray), dot(displacement, transverse)
        x_low, x_high = max(Fraction(0), u - H), min(H, u + H)
        y_low, y_high = max(Fraction(0), v - H), min(H, v + H)
        if x_low < x_high and y_low < y_high:
            x_levels.update((x_low, x_high))
            y_levels.update((y_low, y_high))
            rectangles.append((x_low, x_high, y_low, y_high, atom.integer_weight))
    xs, ys = sorted(x_levels), sorted(y_levels)
    events: list[list[tuple[int, int, int]]] = [[] for _ in xs]
    for x_low, x_high, y_low, y_high, weight in rectangles:
        first, last = bisect_left(ys, y_low), bisect_left(ys, y_high)
        events[bisect_left(xs, x_low)].append((first, last, weight))
        events[bisect_left(xs, x_high)].append((first, last, -weight))
    tree = RangeMinimum(len(ys) - 1)
    c_best: Minimum | None = None
    s_best: Minimum | None = None
    c_queried = 0
    s_queried = 0
    for x_index, (x_low, x_high) in enumerate(pairwise(xs)):
        # All coincident starts and ends are applied before querying this open strip.
        for first, last, weight in events[x_index]:
            tree.add(first, last, weight)
        if x_high <= chart.x_cut:
            if chart.axis:
                c_stop = bisect_left(ys, DELTA)
            else:
                low, high = 0, len(ys) - 1
                while low < high:
                    middle = (low + high) // 2
                    if wall_cell_feasible(chart, x_high, ys[middle]):
                        low = middle + 1
                    else:
                        high = middle
                c_stop = low
            if c_stop:
                mass, y_index = tree.prefix_minimum(c_stop)
                c_queried += c_stop
                cell = Cell(x_low, x_high, ys[y_index], ys[y_index + 1])
                if c_best is None or mass < c_best.integer_mass:
                    c_best = Minimum(mass, chart, cell)
        if x_low >= chart.x_cut:
            mass, y_index = tree.prefix_minimum(len(ys) - 1)
            s_queried += len(ys) - 1
            cell = Cell(x_low, x_high, ys[y_index], ys[y_index + 1])
            if s_best is None or mass < s_best.integer_mass:
                s_best = Minimum(mass, chart, cell)
    if c_best is None or s_best is None:
        raise ValueError("positive-area C and S domains must each have an open cell")
    return (
        c_best,
        s_best,
        {
            "x_strips": len(xs) - 1,
            "y_intervals": len(ys) - 1,
            "nondegenerate_rectangles": len(rectangles),
            "c_feasible_cells": c_queried,
            "s_strip_cells": s_queried,
        },
    )


def centre_of(chart: Chart, x: Fraction, y: Fraction) -> Point:
    return add(MARKS[0], add(scale(chart.selected_ray, x), scale(turn(chart.selected_ray), y)))


def rational_cell_centre(minimum: Minimum) -> Point:
    chart, cell = minimum.chart, minimum.cell
    for exponent in range(1, 257):
        divisor = 2**exponent
        x = cell.x_high - (cell.x_high - cell.x_low) / divisor
        y = cell.y_low + (cell.y_high - cell.y_low) / divisor
        if wall_cell_feasible(chart, x, y):
            return centre_of(chart, x, y)
    raise ValueError("failed to construct the promised rational feasible cell centre")


def rational_parent(chart: Chart, centre: Point) -> Point:
    if chart.axis:
        return Fraction(1), Fraction(0)
    core = square(centre, chart.selected_ray, H)
    for exponent in range(1, 129):
        denominator = 2**exponent
        bounds = []
        for boundary in (chart.lower_tangent, chart.upper_tangent):
            low, high = 0, denominator
            while low < high:
                middle = (low + high) // 2
                candidate = Fraction(middle, denominator)
                whole = (
                    2 * candidate / (1 - candidate * candidate)
                    if candidate < 1
                    else Fraction(10)
                )
                if whole > boundary:
                    high = middle
                else:
                    low = middle + 1
            bounds.append(low)
        for numerator in (bounds[0], bounds[1] - 1):
            if not 0 <= numerator < denominator:
                continue
            original = ray(Fraction(numerator, denominator))
            tangent = original[1] / original[0]
            if not chart.lower_tangent < tangent < chart.upper_tangent:
                continue
            candidate_ray = (original[1], original[0]) if chart.reflected else original
            parent = square(centre, candidate_ray, Fraction(1, 2))
            if all(0 <= coordinate <= Q for vertex in parent for coordinate in vertex) and all(
                min(edges(parent, vertex)) > 0 for vertex in core
            ):
                return candidate_ray
    raise ValueError("failed to construct a rational physical parent in the source cell")


def source_cell_admits(chart: Chart, physical_ray: Point) -> bool:
    """Undo source reflection and the square's quarter-turn symmetry."""
    for oriented in axis_set(physical_ray):
        folded = (oriented[1], oriented[0]) if chart.reflected else oriented
        if folded[0] <= 0 or folded[1] < 0:
            continue
        tangent = folded[1] / folded[0]
        if chart.lower_tangent <= tangent <= chart.upper_tangent:
            return True
    return False


def replay(minimum: Minimum, atoms: tuple[AtomMass, ...], role: str) -> dict[str, Any]:
    chart = minimum.chart
    centre = (
        rational_cell_centre(minimum)
        if role == "C"
        else centre_of(
            chart,
            (minimum.cell.x_low + minimum.cell.x_high) / 2,
            (minimum.cell.y_low + minimum.cell.y_high) / 2,
        )
    )
    parent_ray = rational_parent(chart, centre)
    if charge_at(atoms, centre, chart.selected_ray) != minimum.integer_mass:
        raise ValueError("closed atom replay disagrees with the open-cell minimum")
    complete_labels = labels(centre, chart.selected_ray)
    if 0 not in complete_labels or 15 in complete_labels:
        raise ValueError("witness has wrong complete forced-0 label set")
    core = square(centre, chart.selected_ray, H)
    owned = [min(edges(core, mark)) >= 0 for mark in MARKS]
    if owned != ([True, True] if role == "C" else [True, False]):
        raise ValueError("witness has wrong mark ownership role")
    parent = square(centre, parent_ray, Fraction(1, 2))
    if dot(parent_ray, parent_ray) != 1:
        raise ValueError("physical parent ray is not unit length")
    if any(coordinate < 0 or coordinate > Q for vertex in parent for coordinate in vertex):
        raise ValueError("physical parent leaves the container")
    if any(min(edges(parent, vertex)) <= 0 for vertex in core):
        raise ValueError("core is not strictly contained in its physical parent")
    if not source_cell_admits(chart, parent_ray):
        raise ValueError("physical parent is outside its declared source cell")
    return {
        "role": role,
        "source_index": chart.index,
        "reflected": chart.reflected,
        "centre": list(map(str, centre)),
        "selected_core_ray": list(map(str, chart.selected_ray)),
        "physical_parent_ray": list(map(str, parent_ray)),
        "labels": sorted(complete_labels),
        "owns_marks": owned,
        "integer_charge": minimum.integer_mass,
    }


def serialized_minimum(value: Minimum) -> dict[str, Any]:
    return {
        "integer_charge": value.integer_mass,
        "source_index": value.chart.index,
        "reflected": value.chart.reflected,
        "open_cell": {
            "x": [str(value.cell.x_low), str(value.cell.x_high)],
            "y": [str(value.cell.y_low), str(value.cell.y_high)],
        },
    }


def run_target(expected_revision: str, output: Path) -> dict[str, Any]:
    revision = execution_revision(expected_revision)
    atoms = source_atoms()
    manifest = charts()
    per_chart: list[dict[str, Any]] = []
    c_best: Minimum | None = None
    s_best: Minimum | None = None
    for chart in manifest:
        c_value, s_value, counts = sweep_chart(chart, atoms)
        per_chart.append(
            {
                "source_index": chart.index,
                "reflected": chart.reflected,
                "c_minimum": c_value.integer_mass,
                "s_first_owner_minimum": s_value.integer_mass,
                **counts,
            }
        )
        if c_best is None or c_value.integer_mass < c_best.integer_mass:
            c_best = c_value
        if s_best is None or s_value.integer_mass < s_best.integer_mass:
            s_best = s_value
    if c_best is None or s_best is None or len(per_chart) != 182:
        raise ValueError("the all-chart sweep is incomplete")
    c_replay = replay(c_best, atoms, "C")
    s_replay = replay(s_best, atoms, "S_first_owner")
    result = {
        "experiment": "exp-158",
        "source_revision": SOURCE_REVISION,
        "source_file": SOURCE_PATH,
        "executing_revision": revision,
        "atom_count": len(atoms),
        "integer_total_mass": sum(atom.integer_weight for atom in atoms),
        "eligible_source_charts": len(manifest),
        "distinct_orientations": len({chart.selected_ray for chart in manifest}),
        "c_threshold": C_POSITIVE,
        "s_first_owner_threshold": S_FIRST_POSITIVE,
        "c_minimum": serialized_minimum(c_best),
        "s_first_owner_minimum": serialized_minimum(s_best),
        "c_witness": c_replay,
        "s_first_owner_witness": s_replay,
        "c_outcome": "positive" if c_best.integer_mass >= C_POSITIVE else "replayed_refuter",
        "s_first_owner_outcome": "sufficient_positive"
        if s_best.integer_mass >= S_FIRST_POSITIVE
        else "filter_failed_only",
        "per_chart": per_chart,
        "scope": (
            "Local BC303 C and S first-owner filters only; "
            "no actual S pair or global s(11) claim"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, delete=False
    ) as temporary:
        json.dump(result, temporary, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(output)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    source_parser = subparsers.add_parser(
        "source-check", help="authenticate source without evaluating charge"
    )
    source_parser.add_argument("--expect-implementation-revision", required=True)
    run_parser = subparsers.add_parser(
        "run", help="perform the preregistered all-chart target sweep"
    )
    run_parser.add_argument("--expect-implementation-revision", required=True)
    run_parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    revision = execution_revision(args.expect_implementation_revision)
    if args.operation == "source-check":
        atoms = source_atoms()
        manifest = charts()
        print(
            json.dumps(
                {
                    "source_revision": SOURCE_REVISION,
                    "executing_revision": revision,
                    "atoms": len(atoms),
                    "eligible_source_charts": len(manifest),
                    "scope": "source and manifest only; no target charge",
                },
                sort_keys=True,
            )
        )
    else:
        result = run_target(args.expect_implementation_revision, args.output)
        print(
            json.dumps(
                {
                    "experiment": result["experiment"],
                    "c_outcome": result["c_outcome"],
                    "s_first_owner_outcome": result["s_first_owner_outcome"],
                    "output": str(args.output),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
