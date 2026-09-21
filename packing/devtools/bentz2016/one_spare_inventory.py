"""The one-spare structure inventory for Bentz 2016's Theorem 8 argument.

Usage, from `packing/`:

```
python -m devtools.bentz2016.one_spare_inventory --check [--json OUT]
python -m devtools.bentz2016.one_spare_inventory --n 21 [--json OUT]
python -m devtools.bentz2016.one_spare_inventory --n 32 [--json OUT]
```

`--check` is the control: the zero-spare n = 22 case, where Theorem 11 is a theorem and
every structure must come out forced. `--n 21` is `H-226`'s target, `--n 32` is
`H-227`'s, and `--n 32` runs the side-6 model in `devtools.bentz2016.m6_model`.

## The model

A packing of `N` boxes (open squares of side above 1) in `[0, 5]^2` meets the red set
(22 points) and the blue set (23 points) of Figure 3, both unavoidable, so every box
holds a point of each colour. With `k = |P| - N` spares in a colour, that colour's
*structure* is the exact list of uncovered points and of multiply covered groups; every
other point of that colour is covered by a box holding no second point of its colour.
The enumeration is complete for `k <= 2`: one spare is one uncovered point or one
double, and two spares are two uncovered points, an uncovered point with a double, two
disjoint doubles, or a triple. Doubles and triples are sets of pairwise distance below
`1.01 sqrt(2)`, the diagonal of a maximal box (transcription line 170); on this lattice
the pairwise test is exact for triples, because the only triples it admits are the 28
"row pair plus apex" sets of spread `1 x 0.8`.

**Theorem 8 freezing.** Conditions 2 and 3 of Theorem 8 (transcription lines 110 to
112) freeze every uncovered point and every point of a multiply covered group. The
paper's moves are then: shift a five-point row by 0.1 and back, which needs the whole
row unfrozen, and move an end point to `x = 1` or `x = 4` and back, which needs that
end point unfrozen. Four-point rows cannot move at all: Lemma 2 at the far wall would
need `a = 1.1`. So at each height the box of the five-point row's end point contains

- `[0.4, 1] x {y_i}` (**full**), whose chord on `l` exceeds 1 (replay rows 11 to 15);
- `[0.5, 1] x {y_i}` (**partial**), which needs the finish of Theorem 11 (replay rows
  17 to 24 and `devtools.bentz2016.regions`);
- nothing, when the end point is itself frozen or uncovered.

Both vertical wall lines are used, `x = c` and `x = 5 - c`. A frozen point anywhere in
a row kills that row's shift toward *both* walls, which is why a structure can lose
charges on both lines at once.

**Distinctness needs no case split.** A counted box holds its own singly covered end
point and, through `(1, y_i)`, a point of the other colour. Two counted boxes at
different heights would therefore put two points of one colour into a box that already
holds a singly covered point of that colour. A red double does not merge two of the
five boxes: the double's end point is frozen and has no trajectory at all, so the
charge is lost rather than shared.

**Immediate contradiction.** A trajectory that passes through an uncovered point of
the other colour contradicts Theorem 8 directly.

## The three classes

- **forced**: an immediate contradiction; or a line with five full boxes; or a line
  with four full and one partial whose finish target is forced. The finish is the
  paper's at blue heights 1, 3 and 5 (its cases 2 and 1) and *derived here* at red
  heights 2 and 4, where the region lies within 0.450976 of the next red point.
- **needs-geometry**: some line carries full plus partial at least five, but no
  printed or derived finish applies. The claim each such structure needs is recorded
  in its reason string; it is not assumed.
- **kill**: every line carries at most four counted boxes. That is `H-226`'s own
  registered kill for the proof strategy as stated. It names the case that needs new
  geometry; it does **not** produce a packing and says nothing about `s(21)`.

Classes are invariant under the configuration's `D2` symmetry (`x -> 5 - x`,
`y -> 5 - y`); the run checks that on every pair and counts orbits by canonical form.

## The merge propagation

The lane's only immediate contradiction was a trajectory through an uncovered point of
the other colour. The review of the model showed that Theorem 8, convexity and the
1.01-diagonal bound give more, and `merge_propagation` is that strengthening: two swept
segments that meet cannot lie in two boxes of a packing, so their boxes merge, and a
merged box is refused when it sweeps an uncovered point, when it holds a singly covered
point of one colour beside another point of that colour, or when the points it must
contain do not fit in a square of side 1.01.

It runs by default on every pair the wall-line count leaves non-forced, and it can only
add contradictions, never remove one. Both readings are reported: `verdict.before`
carries the wall-line class, and the inventory prints and writes
`classes_raw_before_propagation` and `classes_orbits_before_propagation` beside the
propagated counts. At `n = 21` it converts 272 kill and 4,305 needs-geometry orbits,
leaving 3,461 and 22,603. `n = 32` runs the side-6 model, which does not carry this
pass.

**What is not modelled.** Two limits, both of which cut against the kill class and are
stated rather than smoothed over:

- The second point of a five-point row can be moved within `[1.5, 1.6]` once that row's
  end point sits at `x = 1`, which Lemma 1 allows. It is not modelled because it earns
  nothing: the segment it sweeps reaches neither wall line, so it adds no charge.
- The two horizontal wall lines `y = c`, `y = 5 - c` cannot be charged by these row
  moves at all, because a column cannot move: displacing one point vertically stretches
  a triangle side to `sqrt(1 + delta^2)`. They are charged instead by the transposed
  configurations `R^T`, `B^T`, whose structures this toolkit cannot correlate with
  `(R, B)`. So a kill here is a kill on **every** wall line only for the structure
  paired with its own transposed twin, which leaves at most four charges on all four;
  for an arbitrary pair the transposed lines are an independent draw that doubles the
  chances and changes no per-structure verdict.

No move outside the paper's toolkit is modelled.

Records: `H-226`, `H-227`; defects `D-505`, `D-506`, `D-507`.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from functools import cache
from itertools import combinations
from pathlib import Path
from typing import cast

from devtools.bentz2016.geometry import ROW_Y, M, base_rows, points, unavoidable
from devtools.bentz2016.regions import finish_table

#: `(1.01 sqrt(2))^2`: two points of one box are closer than the maximal diagonal.
DIAG2 = Fraction(101, 100) ** 2 * 2

RED = points("red")
BLUE = points("blue")
ROWS = {"red": base_rows("red"), "blue": base_rows("blue")}
FIVE_ROWS = {
    colour: [i for i, row in enumerate(ROWS[colour]) if len(row) == 5]
    for colour in ("red", "blue")
}
OTHER = {"red": "blue", "blue": "red"}
HEIGHT_COLOUR = {i: ("red" if i in FIVE_ROWS["red"] else "blue") for i in range(5)}
SIDES = ("L", "R")

#: Per height (0-based), the target the finish forces and which finish it is.
#: Heights 1 and 3 are red, and their finish is derived here rather than printed.
FINISH: dict[int, tuple[str, str]] = {
    0: ("(c,1)", "finish-paper"),
    1: ("(3/2,17/10)", "finish-derived"),
    2: ("(3/2,5/2)", "finish-paper"),
    3: ("(3/2,33/10)", "finish-derived"),
    4: ("(c,4)", "finish-paper"),
}

type Point = tuple[Fraction, Fraction]
type Group = frozenset[Point]
type Structure = tuple[frozenset[Point], tuple[Group, ...]]
type StructureKey = tuple[tuple[Point, ...], tuple[tuple[Point, ...], ...]]


def d2(p: Point, q: Point) -> Fraction:
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def close_pairs(pts: list[Point]) -> list[Group]:
    """Pairs that could share one box: closer than the diagonal of a maximal box."""
    return [frozenset(pair) for pair in combinations(pts, 2) if d2(*pair) < DIAG2]


def close_triples(pts: list[Point]) -> list[Group]:
    """Triples that could share one box, by the same pairwise test.

    The pairwise test is exact on this lattice: every triple it admits has spread
    `1 x 0.8`, which fits in a maximal box, so no triple is admitted that could not
    occur and none that could is missed.
    """
    out: list[Group] = []
    for triple in combinations(pts, 3):
        if not all(d2(a, b) < DIAG2 for a, b in combinations(triple, 2)):
            continue
        xs = [p[0] for p in triple]
        ys = [p[1] for p in triple]
        if max(xs) - min(xs) >= Fraction(101, 100) or max(ys) - min(ys) >= Fraction(101, 100):
            raise AssertionError(f"triple does not fit a maximal box: {triple}")
        out.append(frozenset(triple))
    return out


def structures(pts: list[Point], k: int) -> list[Structure]:
    """Every structure with `k` spares, as `(uncovered, groups)`."""
    if k == 0:
        return [(frozenset(), ())]
    pairs = close_pairs(pts)
    if k == 1:
        return [(frozenset([p]), ()) for p in pts] + [(frozenset(), (pair,)) for pair in pairs]
    if k == 2:
        out: list[Structure] = [(frozenset(ab), ()) for ab in combinations(pts, 2)]
        out += [(frozenset([p]), (pair,)) for p in pts for pair in pairs if p not in pair]
        out += [
            (frozenset(), tuple(sorted((a, b), key=sorted)))
            for a, b in combinations(pairs, 2)
            if not (a & b)
        ]
        out += [(frozenset(), (t,)) for t in close_triples(pts)]
        return out
    raise ValueError(f"only k <= 2 is enumerated, got {k}")


def sym_point(p: Point, k: int) -> Point:
    """One of the four `D2` images of a point: bit 0 mirrors `x`, bit 1 mirrors `y`."""
    x, y = p
    if k & 1:
        x = M - x
    if k & 2:
        y = M - y
    return (x, y)


def sym_structure(st: Structure, k: int) -> Structure:
    uncovered, groups = st
    return (
        frozenset(sym_point(p, k) for p in uncovered),
        tuple(sorted((frozenset(sym_point(p, k) for p in g) for g in groups), key=sorted)),
    )


def key_structure(st: Structure) -> StructureKey:
    uncovered, groups = st
    return (
        tuple(sorted(uncovered)),
        tuple(tuple(sorted(g)) for g in sorted(groups, key=sorted)),
    )


def format_structure(st: Structure) -> str:
    uncovered, groups = st
    u = ",".join(f"({p[0]},{p[1]})" for p in sorted(uncovered))
    g = ";".join(
        "{" + ",".join(f"({p[0]},{p[1]})" for p in sorted(group)) + "}" for group in groups
    )
    return f"U[{u}] G[{g}]"


def frozen_points(st: Structure) -> set[Point]:
    """Every point Theorem 8 freezes: the uncovered ones and every point of a group."""
    uncovered, groups = st
    return set(uncovered) | {p for g in groups for p in g}


#: The side of a maximal box: an open square of side above 1 that holds two points of
#: one colour has them closer than `1.01 sqrt(2)` (transcription line 170), so every
#: merged box below must fit inside a square of this side.
MAX_SIDE = Fraction(101, 100)
#: Orientations sampled when a merged point set has to be tested against that side.
#: The minimum over orientations of the bounding square is a continuous, piecewise
#: smooth function of the angle with a handful of critical points, so a thousand
#: samples over the quarter turn bracket it to better than `1e-5`; the slack below is
#: two orders of magnitude wider than that, and no decision here is within it.
ORIENTATION_SAMPLES = 1000
#: How far over `MAX_SIDE` the sampled square must be before the box is refused.
ORIENTATION_SLACK = 4e-3

#: A horizontal segment `(x0, x1, y)` a point is known to sweep, so its box contains it.
type Segment = tuple[Fraction, Fraction, Fraction]
#: A merge key: one colour's point, standing for the box that covers it.
type MergeKey = tuple[str, Point]


def swept_segments(
    colour: str, st: Structure
) -> tuple[dict[Point, Segment], tuple[tuple[Point, Segment], ...]]:
    """What each covered point of one colour is known to sweep, and each group's hull.

    Theorem 8 keeps a point inside one box along its whole trajectory, and a box is
    convex, so the box covering a point contains the segment the point sweeps. On a
    five-point row with nothing frozen that is `[0.4, 1]` for the left end point, its
    mirror for the right, and `[x - 0.1, x + 0.1]` for an interior point, because the
    row shifts 0.1 either way. With something frozen in the row the shift is gone and
    only the end point's own move survives, giving `[0.5, 1]` and its mirror. A frozen
    point sweeps nothing, and neither does any point of a four-point row.

    The second returned list is each group's same-row hull: two points of one group lie
    in one box, so that box contains the segment between them. It is keyed by the
    group's first point, which is the key the group's members are merged onto.
    """
    uncovered, groups = st
    frozen = frozen_points(st)
    segments: dict[Point, Segment] = {}
    for i, xs in enumerate(ROWS[colour]):
        y = ROW_Y[i]
        row: list[Point] = [(x, y) for x in xs]
        if len(xs) != 5:
            segments.update({p: (p[0], p[0], y) for p in row if p not in uncovered})
            continue
        row_free = not any(p in frozen for p in row)
        for j, p in enumerate(row):
            if p in uncovered:
                continue
            x = p[0]
            if p in frozen:
                segments[p] = (x, x, y)
            elif row_free:
                if j == 0:
                    segments[p] = (Fraction(2, 5), Fraction(1), y)
                elif j == len(row) - 1:
                    segments[p] = (Fraction(4), Fraction(23, 5), y)
                else:
                    segments[p] = (x - Fraction(1, 10), x + Fraction(1, 10), y)
            elif j == 0:
                segments[p] = (Fraction(1, 2), Fraction(1), y)
            elif j == len(row) - 1:
                segments[p] = (Fraction(4), Fraction(9, 2), y)
            else:
                segments[p] = (x, x, y)
    hulls: list[tuple[Point, Segment]] = []
    for group in groups:
        members = sorted(group)
        for a, b in combinations(members, 2):
            if a[1] == b[1]:
                hulls.append((members[0], (a[0], b[0], a[1])))
    return segments, tuple(hulls)


def _merge_components(
    red: StructureFacts, blue: StructureFacts
) -> list[tuple[list[MergeKey], list[Segment]]]:
    """Merge the boxes that two swept segments force to be the same box.

    Two segments that meet cannot lie in different boxes of a packing: the boxes are
    disjoint and each contains its whole segment. Merging on that relation, and on
    membership of a group, is the transitive closure of an interval-overlap graph, so
    one sweep per row settles it rather than a fixed point over component pairs.
    """
    parent: dict[MergeKey, MergeKey] = {}

    def find(key: MergeKey) -> MergeKey:
        parent.setdefault(key, key)
        root = key
        while parent[root] != root:
            root = parent[root]
        while parent[key] != root:
            parent[key], key = root, parent[key]
        return root

    def union(a: MergeKey, b: MergeKey) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    items: dict[MergeKey, list[Segment]] = {}
    for colour, facts in (("red", red), ("blue", blue)):
        segments, hulls = facts.swept
        for point, segment in segments.items():
            items.setdefault((colour, point), []).append(segment)
        for first, segment in hulls:
            items.setdefault((colour, first), []).append(segment)
        for group in facts.structure[1]:
            members = sorted(group)
            for other in members[1:]:
                union((colour, members[0]), (colour, other))
    by_row: dict[Fraction, list[tuple[Fraction, Fraction, MergeKey]]] = {}
    for key, segments in items.items():
        for x0, x1, y in segments:
            by_row.setdefault(y, []).append((x0, x1, key))
    for row in by_row.values():
        row.sort()
        reach = row[0][1]
        previous = row[0][2]
        for x0, x1, key in row[1:]:
            if x0 <= reach:
                union(previous, key)
                reach = max(reach, x1)
            else:
                reach = x1
            previous = key
    components: dict[MergeKey, tuple[list[MergeKey], list[Segment]]] = {}
    for key, segments in items.items():
        members, collected = components.setdefault(find(key), ([], []))
        members.append(key)
        collected.extend(segments)
    return list(components.values())


def _min_enclosing_square(points: tuple[tuple[Fraction, Fraction], ...]) -> float:
    """The least side of a square containing the points, over sampled orientations."""
    placed = [(float(x), float(y)) for x, y in points]
    best = float("inf")
    for k in range(ORIENTATION_SAMPLES):
        angle = k * (math.pi / 2) / ORIENTATION_SAMPLES
        cos, sin = math.cos(angle), math.sin(angle)
        us = [x * cos + y * sin for x, y in placed]
        vs = [-x * sin + y * cos for x, y in placed]
        best = min(best, max(max(us) - min(us), max(vs) - min(vs)))
    return best


#: Every sampled orientation decision made in this process, as
#: `sampled side - (MAX_SIDE + ORIENTATION_SLACK)`: positive refuses the box, negative
#: keeps it, and the distance from zero is how far that decision was from flipping.
#: One entry per distinct point set, because the decision below is memoised.
_ORIENTATION_MARGINS: dict[tuple[tuple[Fraction, Fraction], ...], float] = {}


def orientation_margins() -> dict[str, object]:
    """How close the sampled orientation decisions came to their threshold.

    The sampled minimum is an *upper* bound on the true least enclosing square, and
    exceeding the threshold refuses the box, which is a contradiction, which is a
    forcing -- so a sampling overshoot wider than `ORIENTATION_SLACK` would manufacture
    a forcing. This reports what the slack was previously only asserted to have: the
    closest any decision came to flipping, measured on the run rather than argued in a
    comment. It is cumulative over the process, because the decision is memoised, which
    only makes the reported minimum more conservative.
    """
    margins = list(_ORIENTATION_MARGINS.values())
    return {
        "sampled_decisions": len(margins),
        "orientation_samples": ORIENTATION_SAMPLES,
        "slack": ORIENTATION_SLACK,
        "min_abs_margin": min((abs(m) for m in margins), default=None),
        "refusals": sum(1 for m in margins if m > 0),
    }


@cache
def _too_big_for_one_box(points: tuple[tuple[Fraction, Fraction], ...]) -> bool:
    """Do these points need a square of side above 1.01, so no box holds them all?

    Cheap first: a diameter at or below the side fits, and a diameter at or above the
    diagonal cannot. Only the band between them reaches the sampled minimum, and the
    same point sets recur across thousands of pairs, so the answer is memoised. Every
    sampled decision records its margin above or below the threshold, which
    `orientation_margins` reports.
    """
    if len(points) < 2:
        return False
    diameter2 = max((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 for a, b in combinations(points, 2))
    if diameter2 <= MAX_SIDE**2:
        return False
    if diameter2 >= 2 * MAX_SIDE**2:
        return True
    margin = _min_enclosing_square(points) - (float(MAX_SIDE) + ORIENTATION_SLACK)
    _ORIENTATION_MARGINS[points] = margin
    return margin > 0


def merge_propagation(red: StructureFacts, blue: StructureFacts) -> str | None:
    """Theorem 8 propagated through the merged boxes: a contradiction, or `None`.

    The lane's own immediate contradiction was one case of this -- a trajectory through
    an uncovered point of the other colour. Theorem 8, convexity and the 1.01 diagonal
    give more, and this is the strengthening the review of the model asked for. Merge
    every pair of boxes that two meeting segments force together, then refuse the merged
    box if

    * it contains an uncovered point, which Theorem 8 denies to every box;
    * it holds a singly covered point of one colour together with another point of that
      colour, which is what "singly covered" rules out; or
    * the points it must contain do not fit in a square of side 1.01, the largest box a
      packing of this many boxes can have.

    Each is a contradiction with the assumed packing, so the structure is forced. The
    pass never turns a forced verdict into anything else: it only adds contradictions.
    """
    components = _merge_components(red, blue)
    facts = {"red": red, "blue": blue}
    for colour in ("red", "blue"):
        for point in facts[colour].uncovered:
            for _, segments in components:
                for x0, x1, y in segments:
                    if y == point[1] and x0 <= point[0] <= x1:
                        return (
                            f"merged box sweeps the uncovered {colour} point "
                            f"({point[0]},{point[1]})"
                        )
    for members, segments in components:
        for colour in ("red", "blue"):
            frozen = frozen_points(facts[colour].structure)
            same = [p for c, p in members if c == colour]
            single = [p for p in same if p not in frozen]
            if single and len(same) >= 2:
                partner = next(p for p in same if p != single[0])
                return (
                    f"merged box holds the singly covered {colour} point "
                    f"({single[0][0]},{single[0][1]}) with ({partner[0]},{partner[1]})"
                )
        corners = tuple(
            sorted({(x0, y) for x0, _, y in segments} | {(x1, y) for _, x1, y in segments})
        )
        if _too_big_for_one_box(corners):
            return f"merged box does not fit a square of side 1.01: {list(corners)}"
    return None


@dataclass(frozen=True)
class StructureFacts:
    """Everything the classifier needs from one colour's structure, computed once.

    The inventory evaluates up to 168,000 pairs, and every fact here depends on one
    structure alone, so computing them per pair would repeat the same work thousands
    of times.
    """

    label: str
    uncovered: frozenset[Point]
    #: `(height, side) -> status`, for the heights this colour owns.
    status: dict[tuple[int, str], str]
    #: The `D2` images' canonical keys, index 0 being the identity.
    keys: tuple[StructureKey, ...]
    #: The structure itself, which the merge propagation needs point by point.
    structure: Structure
    #: Every point's swept segment, and the same-row hulls of its groups.
    swept: tuple[dict[Point, Segment], tuple[tuple[Point, Segment], ...]]


def structure_facts(colour: str, st: Structure) -> StructureFacts:
    frozen = frozen_points(st)
    uncovered, _ = st
    status: dict[tuple[int, str], str] = {}
    for i in FIVE_ROWS[colour]:
        y = ROW_Y[i]
        row_pts = [(x, y) for x in ROWS[colour][i]]
        row_frozen = any(p in frozen for p in row_pts)
        for side in SIDES:
            end = (Fraction(1, 2), y) if side == "L" else (Fraction(9, 2), y)
            if end in uncovered:
                status[i, side] = "uncovered"
            elif end in frozen:
                status[i, side] = "frozen"
            elif row_frozen:
                status[i, side] = "partial"
            else:
                status[i, side] = "full"
    return StructureFacts(
        label=format_structure(st),
        uncovered=uncovered,
        status=status,
        keys=tuple(key_structure(sym_structure(st, k)) for k in range(4)),
        structure=st,
        swept=swept_segments(colour, st),
    )


def canonical(red: StructureFacts, blue: StructureFacts) -> tuple[StructureKey, StructureKey]:
    """The canonical representative of the pair's `D2` orbit."""
    return min((red.keys[k], blue.keys[k]) for k in range(4))


@dataclass
class LineInfo:
    """One wall line's counted boxes, by height (1-based in the report)."""

    full: list[int]
    partial: list[int]
    status: list[tuple[str, str]]


@dataclass
class Verdict:
    lines: dict[str, LineInfo]
    klass: str
    reason: str
    #: The class before the merge propagation ran; equal to `klass` when it did not
    #: fire, so both numbers can be reported from one pass.
    before: str = ""

    def __post_init__(self) -> None:
        self.before = self.before or self.klass


def _line_info(red: StructureFacts, blue: StructureFacts, side: str) -> LineInfo:
    facts = {"red": red, "blue": blue}
    status = [(HEIGHT_COLOUR[i], facts[HEIGHT_COLOUR[i]].status[i, side]) for i in range(5)]
    return LineInfo(
        full=[i for i, (_, s) in enumerate(status) if s == "full"],
        partial=[i for i, (_, s) in enumerate(status) if s == "partial"],
        status=status,
    )


def _immediate(
    red: StructureFacts, blue: StructureFacts, side: str, line: LineInfo
) -> str | None:
    """A trajectory through an uncovered point of the other colour (Theorem 8)."""
    facts = {"red": red, "blue": blue}
    for i in [*line.full, *line.partial]:
        colour = HEIGHT_COLOUR[i]
        y = ROW_Y[i]
        end = (Fraction(1, 2), y) if side == "L" else (Fraction(9, 2), y)
        crossing = (Fraction(1), y) if side == "L" else (Fraction(4), y)
        if crossing in facts[OTHER[colour]].uncovered:
            return (
                f"{side}: trajectory of {colour} ({end[0]},{end[1]}) passes the "
                f"uncovered {OTHER[colour]} point ({crossing[0]},{crossing[1]})"
            )
    return None


def _four_full_and_a_partial(
    lines: dict[str, LineInfo], finish_ok: dict[int, bool]
) -> Verdict | None:
    """A line with four full boxes and one partial: the finish decides it, or nobody does."""
    for side in SIDES:
        line = lines[side]
        if len(line.full) != 4 or len(line.partial) != 1:
            continue
        i = line.partial[0]
        target, kind = FINISH[i]
        if finish_ok[i]:
            return Verdict(
                lines,
                "forced",
                f"{side}: four full + partial at height {i + 1}, {kind} forces {target}",
            )
        return Verdict(
            lines,
            "needs-geometry",
            f"{side}: four full + partial at height {i + 1}; "
            f"finish target {target} not established",
        )
    return None


def classify_by_wall_lines(
    red: StructureFacts, blue: StructureFacts, finish_ok: dict[int, bool]
) -> Verdict:
    """The wall-line verdict alone, before the merge propagation: the lane's original."""
    lines = {side: _line_info(red, blue, side) for side in SIDES}
    for side in SIDES:
        immediate = _immediate(red, blue, side, lines[side])
        if immediate:
            return Verdict(lines, "forced", "theorem8-uncovered-on-trajectory: " + immediate)
    for side in SIDES:
        if len(lines[side].full) >= 5:
            return Verdict(lines, "forced", f"{side}: five full boxes")
    four_plus_one = _four_full_and_a_partial(lines, finish_ok)
    if four_plus_one is not None:
        return four_plus_one
    best = max(SIDES, key=lambda s: len(lines[s].full) + len(lines[s].partial))
    line = lines[best]
    counted = len(line.full) + len(line.partial)
    if counted >= 5:
        return Verdict(
            lines,
            "needs-geometry",
            f"{best}: {len(line.full)} full at heights {[i + 1 for i in line.full]} + "
            f"{len(line.partial)} partial at heights {[i + 1 for i in line.partial]}; "
            "claim needed: these cannot coexist on l",
        )
    return Verdict(
        lines,
        "kill",
        f"at most {counted} counted boxes on either line "
        f"(best {best}: full {[i + 1 for i in line.full]}, "
        f"partial {[i + 1 for i in line.partial]})",
    )


def classify(
    red: StructureFacts,
    blue: StructureFacts,
    finish_ok: dict[int, bool],
    *,
    propagate: bool = True,
) -> Verdict:
    """Classify one (red, blue) pair as forced, needs-geometry, or kill.

    Two passes. The first counts charges on the two wall lines, which is the lane's
    original classification and is what `verdict.before` reports. The second is the
    merge propagation the review of the model asked for: Theorem 8 through the boxes
    two meeting segments force together, which can only turn a non-forced verdict
    forced. `propagate=False` runs the first pass alone, for reporting the two side by
    side rather than for deciding anything.
    """
    verdict = classify_by_wall_lines(red, blue, finish_ok)
    if not propagate or verdict.klass == "forced":
        return verdict
    merged = merge_propagation(red, blue)
    if merged is None:
        return verdict
    return Verdict(
        verdict.lines,
        "forced",
        "theorem8-merge: " + merged,
        before=verdict.klass,
    )


#: The mechanisms a `forced` verdict can come from, matched against its reason in
#: order, so the merge propagation is read before the plain Theorem 8 hit it
#: generalises.
FORCED_MECHANISMS: tuple[tuple[str, str], ...] = (
    ("theorem8-merge", "forced: Theorem 8 propagated through merged boxes"),
    ("theorem8", "forced: Theorem 8 (trajectory through an uncovered point)"),
    ("five full", "forced: five full boxes on one line"),
    ("finish-paper", "forced: four full + partial, paper finish (blue height 1/3/5)"),
    ("finish-derived", "forced: four full + partial, derived finish (red height 2/4)"),
)


def _forced_reason_key(reason: str) -> str:
    for marker, label in FORCED_MECHANISMS:
        if marker in reason:
            return label
    return "forced: " + reason


def reason_key(verdict: Verdict) -> str:
    """A coarse grouping of reasons, for the summary table."""
    reason = verdict.reason
    if verdict.klass == "forced":
        return _forced_reason_key(reason)
    if verdict.klass == "needs-geometry":
        return "needs-geometry: " + reason.split(": ", 1)[1].split(";")[0]
    return "kill: " + reason.split("(")[0].strip()


def finish_table_ok() -> dict[int, bool]:
    """Recompute the finish exactly and report, per height, whether it closes."""
    table = finish_table()
    ok: dict[int, bool] = {}
    for i in range(5):
        target = FINISH[i][0]
        result = table[i + 1][target]
        ok[i] = bool(result is not None and result.forced)
        sup = "region empty" if result is None else str(result.sup_num)
        print(f"  finish height {i + 1}: target {target} sup dist = {sup} forced = {ok[i]}")
    return ok


def run(
    k_red: int, k_blue: int, finish_ok: dict[int, bool], out_path: str | None, label: str
) -> dict[str, object]:
    """Enumerate every (red, blue) pair, classify it, and report the inventory."""
    reds = [structure_facts("red", st) for st in structures(RED, k_red)]
    blues = [structure_facts("blue", st) for st in structures(BLUE, k_blue)]
    print(
        f"{label}: red structures k={k_red}: {len(reds)}; "
        f"blue structures k={k_blue}: {len(blues)}; pairs: {len(reds) * len(blues)}"
    )
    for name, group, k in (
        ("red", structures(RED, k_red), k_red),
        ("blue", structures(BLUE, k_blue), k_blue),
    ):
        kinds = Counter((len(u), tuple(sorted(len(g) for g in gs))) for u, gs in group)
        print(f"  {name} kinds at k={k} (|uncovered|, group sizes): {dict(kinds)}")
    orbits: dict[tuple[StructureKey, StructureKey], dict[str, object]] = {}
    classes_raw: Counter[str] = Counter()
    classes_raw_before: Counter[str] = Counter()
    reasons_raw: Counter[str] = Counter()
    invariance_ok = True
    for red in reds:
        for blue in blues:
            verdict = classify(red, blue, finish_ok)
            classes_raw[verdict.klass] += 1
            classes_raw_before[verdict.before] += 1
            reasons_raw[reason_key(verdict)] += 1
            key = canonical(red, blue)
            seen = orbits.get(key)
            if seen is not None:
                if seen["class"] != verdict.klass:
                    invariance_ok = False
                seen["size"] = int(seen["size"]) + 1  # pyright: ignore[reportArgumentType]
                continue
            orbits[key] = {
                "red": red.label,
                "blue": blue.label,
                "size": 1,
                "class": verdict.klass,
                "class_before_propagation": verdict.before,
                "reason": verdict.reason,
                "lines": {
                    side: {
                        "full": [i + 1 for i in verdict.lines[side].full],
                        "partial": [i + 1 for i in verdict.lines[side].partial],
                    }
                    for side in SIDES
                },
            }
    classes_orbits = Counter(str(v["class"]) for v in orbits.values())
    classes_orbits_before = Counter(str(v["class_before_propagation"]) for v in orbits.values())
    print(f"  raw pairs classified: {sum(classes_raw.values())} -> {dict(classes_raw)}")
    print(f"    before the merge propagation: {dict(classes_raw_before)}")
    print(
        f"  orbits under D2: {len(orbits)} -> {dict(classes_orbits)} "
        f"(class is D2-invariant: {invariance_ok})"
    )
    print(f"    before the merge propagation: {dict(classes_orbits_before)}")
    converted = Counter(
        str(v["class_before_propagation"])
        for v in orbits.values()
        if v["class"] != v["class_before_propagation"]
    )
    print(f"  orbits the merge propagation converted to forced: {dict(converted)}")
    print("  reasons (raw):")
    for reason, count in sorted(reasons_raw.items(), key=lambda kv: -kv[1]):
        print(f"    {count:7d}  {reason}")
    patterns: Counter[str] = Counter()
    for orbit in orbits.values():
        if orbit["class"] == "forced":
            continue
        lines = cast("dict[str, dict[str, list[int]]]", orbit["lines"])
        shape = ", ".join(
            f"({side}: {len(lines[side]['full'])} full, {len(lines[side]['partial'])} partial)"
            for side in SIDES
        )
        patterns[f"{orbit['class']} {shape}"] += int(orbit["size"])  # pyright: ignore[reportArgumentType]
    if patterns:
        print("  non-forced patterns -> raw count:")
        for shape, count in sorted(patterns.items(), key=lambda kv: -kv[1]):
            print(f"    {count:7d}  {shape}")
    margins = orientation_margins()
    print(
        f"  sampled orientation decisions: {margins['sampled_decisions']} "
        f"({margins['refusals']} refused a merged box); closest any came to the "
        f"1.01 + {ORIENTATION_SLACK} threshold: {margins['min_abs_margin']}"
    )
    inventory: dict[str, object] = {
        "tool": "devtools.bentz2016.one_spare_inventory",
        "label": label,
        "k_red": k_red,
        "k_blue": k_blue,
        "counts": {
            "red_structures": len(reds),
            "blue_structures": len(blues),
            "raw_pairs": len(reds) * len(blues),
            "orbits": len(orbits),
        },
        "classes_raw": dict(classes_raw),
        "classes_raw_before_propagation": dict(classes_raw_before),
        "classes_orbits": dict(classes_orbits),
        "classes_orbits_before_propagation": dict(classes_orbits_before),
        "orbits_converted_by_propagation": dict(converted),
        "reasons_raw": dict(reasons_raw),
        "non_forced_patterns_raw": dict(patterns),
        "invariance_ok": invariance_ok,
        "orientation_margins": orientation_margins(),
        "orbits": list(orbits.values()),
    }
    if out_path:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(inventory, indent=1) + "\n", encoding="utf-8")
        print(f"  inventory written to {out}")
    return inventory


def self_test(
    finish_ok: dict[int, bool], out_path: str | None
) -> tuple[int, dict[str, object]]:
    """The n = 22 control: Theorem 11 is a theorem, so every structure must be forced."""
    inventory = run(0, 1, finish_ok, out_path, "self-test n=22 (red k=0, blue k=1)")
    counts = inventory["counts"]
    classes = inventory["classes_raw"]
    assert isinstance(counts, dict)
    assert isinstance(classes, dict)
    reasons = inventory["reasons_raw"]
    assert isinstance(reasons, dict)
    problems: list[str] = []
    if classes.get("forced", 0) != counts["raw_pairs"]:
        problems.append(f"n=22 is not fully forced: {classes}")
    if not inventory["invariance_ok"]:
        problems.append("the class is not D2-invariant")
    if any("finish-derived" in reason for reason in reasons):
        problems.append("n=22 needed the derived finish, which the paper does not have")
    for problem in problems:
        print(f"SELF-TEST FAILED: {problem}")
    if problems:
        return 1, inventory
    print(
        "SELF-TEST PASSED: every n=22 structure is forced by the paper's argument "
        "(Theorem 11 reproduced on all structures, without the paper's x < 2 reduction)"
    )
    return 0, inventory


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m devtools.bentz2016.one_spare_inventory",
        description="Enumerate and classify the one-spare structures of Bentz 2016.",
    )
    parser.add_argument("--check", action="store_true", help="the n = 22 control")
    parser.add_argument("--n", type=int, choices=[21, 32], help="the case to inventory")
    parser.add_argument(
        "--json", dest="json_out", default=None, help="write the inventory here"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.check and args.n is None:
        _parser().print_help()
        return 1
    if args.n == 32:
        # Imported here, not at the top: `m6_model` sets mpmath's global precision
        # to 50 digits on import, and the side-5 paths are exact and must not
        # depend on that being done.
        from devtools.bentz2016 import m6_model  # noqa: PLC0415

        return m6_model.main(args.json_out)
    for colour in ("red", "blue"):
        ok, notes = unavoidable(ROWS[colour])
        if not ok:
            print(f"base {colour} set is not unavoidable: {notes}")
            return 1
    print("base red/blue sets unavoidable (exact tiling): OK")
    print("finish table (exact, devtools.bentz2016.regions):")
    finish_ok = finish_table_ok()
    if args.check:
        status, _ = self_test(finish_ok, args.json_out)
        return status
    run(1, 2, finish_ok, args.json_out, "n=21 (red k=1, blue k=2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
