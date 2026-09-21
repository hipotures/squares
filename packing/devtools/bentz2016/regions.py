"""Exact midpoint regions for the partial-box finish of Bentz 2016 Theorem 11.

The last step of Theorem 11 (transcription lines 180 to 198) is a region argument. One
of the five counted boxes, `B_i`, covers only the partial segment `[1/2, 1] x {y_i}`
rather than the full `[0.4, 1] x {y_i}`, so it need not charge more than 1 on the
finishing line `l: x = c`. The other four do charge more than 1, which confines
`B_i`'s chord to `{c} x (i-1, i)` and denies `B_i` the two points `(c, i-1)`, `(c, i)`.
The midpoint `m` of `B_i` then satisfies, writing `rho = 0.505 sqrt(2)` for the half
diagonal of a maximal box:

- `x_m >= c + (sqrt(2)/2 - 1/2)`, or the chord would exceed 1 by Lemma 4 or Lemma 5;
- `dist(m, e) <= rho` where `e = (1/2, y_i)`, because `e` lies in `B_i`;
- `dist(m, g) >= 1/2` for each denied point `g`, because a box contains the closed
  disc of radius 1/2 about its midpoint.

The finish is `sup dist(m, T) < 1/2` over that region for a target `T` the box cannot
also contain: then `T` lies in `B_i` after all, and the contradiction closes the case.
The paper runs it twice, at `y_3` against `T = (3/2, 5/2)` (case 1, transcription line
183) and at `y_1` against `T = (c, 1)` (case 2, line 191).

**Why the sup is exact.** The region is compact and bounded by one vertical line and
two or three circles. The distance to a fixed target attains its maximum on the
boundary, and on each boundary curve at an endpoint of the arc -- an intersection with
another constraint curve -- or at a critical point of the distance along that curve,
which for a line is the foot of the perpendicular and for a circle is one of the two
points of the ray through the centre. Every candidate is written in closed form and
filtered by exact membership, so the reported sup is an algebraic number and not a
sample.

**The constant.** `c = sqrt(2) - 1/2`, read off the archived PDF's glyph positions;
the transcription had printed `(sqrt(2) - 1)/2` and `D-505` records the repair. The
standoff `sqrt(2)/2 - 1/2` is Lemma 4's threshold `(sqrt(2) - 1)/2` written the other
way round, which `replay_theorem11` row 17 checks. `line_x` is a parameter throughout
so a wrong constant can be run as a negative control.

**What is modelled and what is not.** The region is the *necessary* condition on the
midpoint that the paper derives; it is not claimed to be attained. A `forced` verdict
therefore says the case closes, and a `not forced` verdict says only that this target
does not close it -- never that a packing exists.

Records: `H-226`, `H-227`; defects `D-505`, `D-506`, `D-507`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import sympy as sp

S2 = sp.sqrt(2)
#: The finishing line `l: x = c`, as printed on PDF pages 6 to 8 (`D-505`).
LINE_X: sp.Expr = S2 - sp.Rational(1, 2)
#: Lemma 4's threshold, written as the PDF writes it in Theorem 11.
STANDOFF: sp.Expr = S2 / 2 - sp.Rational(1, 2)
#: Half the diagonal of a maximal box (side 1.01), transcription line 170.
RHO: sp.Expr = sp.Rational(505, 1000) * S2
HALF = sp.Rational(1, 2)
#: Digits used to decide membership and to order candidates; margins here are ~1e-2.
PREC = 60
#: Membership tolerance, far below any margin in the problem.
TOL = sp.Rational(1, 10**40)

#: Bentz Figure 3 row heights, as exact rationals.
ROW_Y: tuple[sp.Expr, ...] = (
    sp.Rational(9, 10),
    sp.Rational(17, 10),
    sp.Rational(5, 2),
    sp.Rational(33, 10),
    sp.Rational(41, 10),
)


@dataclass(frozen=True)
class VerticalLine:
    """The half-plane `x >= x0`."""

    x0: sp.Expr

    def label(self) -> str:
        return f"x={sp.N(self.x0, 6)}"


@dataclass(frozen=True)
class Circle:
    """A disc constraint: inside the closed disc, or outside the open one."""

    cx: sp.Expr
    cy: sp.Expr
    r: sp.Expr
    inside: bool

    def label(self) -> str:
        where = "in" if self.inside else "out"
        return f"{where}({sp.N(self.cx, 6)},{sp.N(self.cy, 6)};r={sp.N(self.r, 6)})"


type Constraint = VerticalLine | Circle
type Candidate = tuple[sp.Expr, sp.Expr, str]


@dataclass(frozen=True)
class FinishResult:
    """One target of one finish: the exact sup of the distance over the region.

    `sup` is the algebraic number as it falls out of the candidate that attains it.
    `exact()` runs it through `simplify`, which is seconds of work for a nested
    radical and is therefore left to whoever prints it; `sup_num` and `forced` need
    only numeric evaluation and are cheap.
    """

    target: str
    sup: sp.Expr
    at: Candidate
    corners: list[Candidate]

    def exact(self) -> sp.Expr:
        """The simplified radical form, for a table a reader checks by eye."""
        return sp.simplify(self.sup)

    @property
    def sup_num(self) -> sp.Expr:
        return sp.N(self.sup, PREC)

    @property
    def forced(self) -> bool:
        """The sup is below 1/2, so the box must contain the target after all."""
        return bool(sp.N(self.sup, PREC) < HALF)


def _num(e: sp.Expr) -> sp.Expr:
    return sp.N(e, PREC)


type NumericConstraint = tuple[str, sp.Expr, sp.Expr, sp.Expr]


def numeric_constraints(cons: list[Constraint]) -> list[NumericConstraint]:
    """Evaluate the constraint data once, to `PREC` digits.

    Membership is decided on these numbers rather than on the symbolic slack. That is
    not a loss of rigour at the scale of this problem: every margin here is of order
    `1e-2` and the decision tolerance is `1e-40`, so a candidate can neither be
    admitted nor rejected by rounding. It is what makes the table seconds rather than
    minutes, because a nested radical costs the same to evaluate once as to evaluate
    inside every constraint of every target.
    """
    out: list[NumericConstraint] = []
    for con in cons:
        if isinstance(con, VerticalLine):
            out.append(("line", _num(con.x0), sp.Float(0), sp.Float(0)))
            continue
        kind = "in" if con.inside else "out"
        out.append((kind, _num(con.cx), _num(con.cy), _num(con.r * con.r)))
    return out


def in_region_numeric(xn: sp.Expr, yn: sp.Expr, ncons: list[NumericConstraint]) -> bool:
    """Membership of an already-evaluated point in already-evaluated constraints."""
    for kind, a, b, r2 in ncons:
        if kind == "line":
            if xn - a < -TOL:
                return False
            continue
        slack = (xn - a) ** 2 + (yn - b) ** 2 - r2
        if kind == "in" and slack > TOL:
            return False
        if kind == "out" and slack < -TOL:
            return False
    return True


def in_region(pt: tuple[sp.Expr, sp.Expr], cons: list[Constraint]) -> bool:
    """Membership of a candidate point in the region."""
    return in_region_numeric(_num(pt[0]), _num(pt[1]), numeric_constraints(cons))


def _circle_line(con: Circle, line: VerticalLine, label: str) -> list[Candidate]:
    """Where a vertical line meets a circle, in closed form."""
    # Expanded so the radicand reads as a single algebraic number rather than as
    # the unevaluated difference it is built from; the value is unchanged.
    disc = sp.expand(con.r * con.r - (line.x0 - con.cx) ** 2)
    if _num(disc) < 0:
        return []
    root = sp.sqrt(disc)
    return [(line.x0, con.cy + root, label), (line.x0, con.cy - root, label)]


def _circle_circle(a: Circle, b: Circle, label: str) -> list[Candidate]:
    """Where two circles meet, by the radical line, in closed form."""
    dx, dy = b.cx - a.cx, b.cy - a.cy
    dd = sp.sqrt(dx * dx + dy * dy)
    if _num(dd) == 0:
        return []
    along = (a.r * a.r - b.r * b.r + dd * dd) / (2 * dd)
    off2 = sp.expand(a.r * a.r - along * along)
    if _num(off2) < 0:
        return []
    off = sp.sqrt(off2)
    mx, my = a.cx + along * dx / dd, a.cy + along * dy / dd
    return [
        (mx + off * dy / dd, my - off * dx / dd, label),
        (mx - off * dy / dd, my + off * dx / dd, label),
    ]


def curve_intersections(cons: list[Constraint]) -> list[Candidate]:
    """Every pairwise intersection of the constraint curves, in closed form.

    Closed form rather than a solver call: the curves are one vertical line and a
    handful of circles, so each of the two cases is three lines of algebra, and a
    solver call here is several seconds per table where this is a fraction of one.
    """
    pts: list[Candidate] = []
    for i in range(len(cons)):
        for j in range(i + 1, len(cons)):
            first, second = cons[i], cons[j]
            label = f"{first.label()} & {second.label()}"
            match first, second:
                case VerticalLine(), VerticalLine():
                    continue
                case VerticalLine(), Circle():
                    pts += _circle_line(second, first, label)
                case Circle(), VerticalLine():
                    pts += _circle_line(first, second, label)
                case Circle(), Circle():
                    pts += _circle_circle(first, second, label)
    return pts


def distance_critical_points(
    cons: list[Constraint], target: tuple[sp.Expr, sp.Expr]
) -> list[Candidate]:
    """Critical points of the distance to `target` along each constraint curve."""
    tx, ty = target
    pts: list[Candidate] = []
    for con in cons:
        if isinstance(con, VerticalLine):
            pts.append((con.x0, ty, f"foot on {con.label()}"))
            continue
        d = sp.sqrt((tx - con.cx) ** 2 + (ty - con.cy) ** 2)
        if _num(d) == 0:
            continue
        ux, uy = (tx - con.cx) / d, (ty - con.cy) / d
        pts.append((con.cx + con.r * ux, con.cy + con.r * uy, f"near point on {con.label()}"))
        pts.append((con.cx - con.r * ux, con.cy - con.r * uy, f"far point on {con.label()}"))
    return pts


def region_constraints(
    y_i: sp.Expr,
    denied_heights: list[int],
    *,
    line_x: sp.Expr = LINE_X,
    e_x: sp.Expr = HALF,
    rho: sp.Expr = RHO,
) -> list[Constraint]:
    """The midpoint region of a partial box at height `y_i` with the given denied points."""
    cons: list[Constraint] = [
        VerticalLine(line_x + STANDOFF),
        Circle(e_x, y_i, rho, inside=True),
    ]
    cons += [Circle(line_x, sp.Integer(k), HALF, inside=False) for k in denied_heights]
    return cons


def region_corners(cons: list[Constraint]) -> list[Candidate]:
    """The curve intersections that actually lie in the region: its corners."""
    return [c for c in curve_intersections(cons) if in_region((c[0], c[1]), cons)]


def sup_distance(
    cons: list[Constraint], target: tuple[sp.Expr, sp.Expr], name: str = "target"
) -> FinishResult | None:
    """The exact `sup` of `dist(., target)` over the region, and where it is attained.

    Returns `None` when no candidate lies in the region, which means the region is
    empty. An empty region establishes nothing on its own, so the caller reports it
    rather than reading it as a finish.
    """
    ncons = numeric_constraints(cons)
    intersections = curve_intersections(cons)
    tx, ty = _num(target[0]), _num(target[1])
    corners: list[Candidate] = []
    best: Candidate | None = None
    best_d: sp.Expr | None = None
    best_num: sp.Expr | None = None
    for index, (px, py, lab) in enumerate(
        [*intersections, *distance_critical_points(cons, target)]
    ):
        xn, yn = _num(px), _num(py)
        if not in_region_numeric(xn, yn, ncons):
            continue
        if index < len(intersections):
            corners.append((px, py, lab))
        d_num = sp.sqrt((xn - tx) ** 2 + (yn - ty) ** 2)
        if best_num is None or d_num > best_num:
            best = (px, py, lab)
            best_d = sp.sqrt((px - target[0]) ** 2 + (py - target[1]) ** 2)
            best_num = d_num
    if best is None or best_d is None:
        return None
    return FinishResult(target=name, sup=best_d, at=best, corners=corners)


def _without_own_disc(
    cons: list[Constraint], target: tuple[sp.Expr, sp.Expr]
) -> list[Constraint]:
    """Drop the denied-point disc centred on the target.

    A target that is itself a denied point has its own disc among the constraints.
    Keeping it would not empty the region -- it would hold every point of the region at
    distance at least 1/2 from the target, so the sup could never drop below 1/2 and
    the finish could never close. The sup has to be taken over the larger region, which
    is where the contradiction is derived, so the target's own disc is dropped for that
    target.
    """
    return [
        con
        for con in cons
        if not (
            isinstance(con, Circle)
            and not con.inside
            and _num(con.cx - target[0]) == 0
            and _num(con.cy - target[1]) == 0
        )
    ]


def finish_check(
    y_i: sp.Expr,
    denied_heights: list[int],
    targets: dict[str, tuple[sp.Expr, sp.Expr]],
    *,
    line_x: sp.Expr = LINE_X,
    e_x: sp.Expr = HALF,
) -> dict[str, FinishResult | None]:
    """For a partial box at height `y_i`, report `sup dist < 1/2` for each target."""
    cons_all = region_constraints(y_i, denied_heights, line_x=line_x, e_x=e_x)
    return {
        name: sup_distance(_without_own_disc(cons_all, target), target, name)
        for name, target in targets.items()
    }


def finish_targets(
    height: int, *, line_x: sp.Expr = LINE_X, e_x: sp.Expr = HALF
) -> dict[str, tuple[sp.Expr, sp.Expr]]:
    """The three targets tried at one height, 1-based.

    The two denied points `(c, i-1)`, `(c, i)` are the paper's; the third, the next
    point of the partial box's own row, is the *derived* finish this port adds. It is
    what closes a partial box at a red height, where neither of the paper's two cases
    applies, and it is flagged as derived wherever it is used.
    """
    y = ROW_Y[height - 1]
    return {
        f"(c,{height - 1})": (line_x, sp.Integer(height - 1)),
        f"(c,{height})": (line_x, sp.Integer(height)),
        f"({e_x + 1},{y})": (e_x + 1, y),
    }


def finish_table(
    *, line_x: sp.Expr = LINE_X, e_x: sp.Expr = HALF
) -> dict[int, dict[str, FinishResult | None]]:
    """The forced targets for a partial box at each of the five heights.

    Denied points are `(c, i-1)` and `(c, i)`: the chord of a partial box at height
    `i` is confined to `{c} x (i-1, i)` by the four full chords.
    """
    return {
        i: finish_check(
            ROW_Y[i - 1],
            [i - 1, i],
            finish_targets(i, line_x=line_x, e_x=e_x),
            line_x=line_x,
            e_x=e_x,
        )
        for i in range(1, len(ROW_Y) + 1)
    }


def _report(table: dict[int, dict[str, FinishResult | None]]) -> dict[str, object]:
    payload: dict[str, object] = {}
    for i, row in table.items():
        print(f"height {i} (y = {ROW_Y[i - 1]}):")
        entry: dict[str, object] = {}
        for name, result in row.items():
            if result is None:
                print(f"    target {name}: region empty, no finish")
                entry[name] = None
                continue
            print(
                f"    target {name}: sup = {sp.N(result.sup, 20)} "
                f"forced={result.forced} at {result.at[2]}"
            )
            entry[name] = {
                "sup": str(result.exact()),
                "sup_num": str(sp.N(result.sup, 20)),
                "forced": result.forced,
                "at": result.at[2],
                "corners": [
                    [str(sp.N(px, 15)), str(sp.N(py, 15)), lab]
                    for px, py, lab in result.corners
                ],
            }
        payload[str(i)] = entry
    return payload


def main() -> int:
    """Print the finish table and write it beside this module's other receipts."""
    print(
        f"x_left = c + standoff = {sp.simplify(LINE_X + STANDOFF)} "
        f"= {sp.N(LINE_X + STANDOFF, 15)}"
    )
    payload = _report(finish_table())
    out = Path("bentz2016-finish-table.json")
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"finish table written to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
