"""Exact configuration and lemma predicates for Bentz 2016 (arXiv:1606.03746).

Everything in this module is exact. Coordinates are `Fraction`s and every lemma
hypothesis that involves `sqrt(2)` or `sqrt(3)` is tested through its square, so no
floating point enters the unavoidability argument at all.

Lemma numbering follows the archived transcription,
`packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md`:

- **Lemma 1** (line 55): a triangle whose three sides are at most 1. A box whose
  midpoint lies in it contains one of its vertices.
- **Lemma 2** (line 63): a rectangle `[0, a] x [0, b]` against a wall with `a <= 1`,
  `b <= 1` and `a + 2b <= 2 sqrt(2)`. A box whose midpoint lies in it meets the wall
  or contains one of the two far corners.
- **Lemma 6** (line 87): the quadrilateral `(0, 0), (0, 1), (a, 0), (a, b)` against a
  wall with `0 < a < 2 sqrt(2) - 2`, `0 < b <= 1` and `(a, b)` within 1 of `(0, 1)`.
  A box whose midpoint lies in it meets the wall or contains `(0, 1)` or `(a, b)`.

A configuration of points is *unavoidable* in `S = [0, m]^2` when `S` is tiled by such
regions whose off-wall vertices are configuration points: a box inside `S` has its
midpoint in some region, and every conclusion the region's lemma allows puts a
configuration point in the box (a box contained in `S` can never meet a wall of `S`).
That is the argument of Bentz 2016 Section 2, and `unavoidable` below is its checker.

What this module does **not** model: boxes are never constructed. Unavoidability is
decided by the tiling and the lemma hypotheses alone, exactly as the paper decides it.

Used by `devtools.bentz2016.replay_theorem11` (rows 1 to 3 of the replay table) and by
`devtools.bentz2016.one_spare_inventory`, which re-checks the base configurations
before it enumerates anything. Records: `H-226`, `H-227`; defects `D-505`, `D-506`,
`D-507` against the transcription.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import combinations, pairwise

type Point = tuple[Fraction, Fraction]
type Polygon = list[Point]
type Region = tuple[str, Polygon, bool, str]

#: Side of the square for Theorem 11 (n = 22, and the n = 21 one-spare inventory).
M = 5

#: Bentz Figure 3 row heights, bottom to top.
ROW_Y: tuple[Fraction, ...] = (
    Fraction(9, 10),
    Fraction(17, 10),
    Fraction(5, 2),
    Fraction(33, 10),
    Fraction(41, 10),
)

#: The five-point rows sit at x = 0.5, 1.5, ..., 4.5; the four-point rows at 1, ..., 4.
XS5: tuple[Fraction, ...] = tuple(Fraction(1, 2) + j for j in range(5))
XS4: tuple[Fraction, ...] = tuple(Fraction(1) + j for j in range(4))


def base_rows(colour: str) -> list[list[Fraction]]:
    """The x-coordinates per row, bottom to top, of the red or blue configuration.

    Red rows 2 and 4 carry five points; blue rows 1, 3 and 5 do. Together the two
    colours are exactly the 45 points of
    `{0.5, 1, ..., 4.5} x {0.9, 1.7, 2.5, 3.3, 4.1}` (transcription line 165).
    """
    if colour == "red":
        return [list(XS4), list(XS5), list(XS4), list(XS5), list(XS4)]
    if colour == "blue":
        return [list(XS5), list(XS4), list(XS5), list(XS4), list(XS5)]
    raise ValueError(f"unknown colour {colour!r}")


def points(colour: str) -> list[Point]:
    """Every point of one colour, as `(x, y)` pairs."""
    return [(x, y) for y, xs in zip(ROW_Y, base_rows(colour), strict=True) for x in xs]


def d2(p: Point, q: Point) -> Fraction:
    """The squared distance between two exact points."""
    return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2


def le_sqrt(v: Fraction, r: Fraction) -> bool:
    """`v <= sqrt(r)`, decided exactly by squaring (`v` may be negative)."""
    return v <= 0 or v * v <= r


def lt_sqrt(v: Fraction, r: Fraction) -> bool:
    """`v < sqrt(r)`, decided exactly by squaring (`v` may be negative)."""
    return v < 0 or v * v < r


def lemma1_ok(tri: tuple[Point, Point, Point]) -> tuple[bool, str]:
    """Lemma 1's hypothesis: a non-degenerate triangle with all three sides at most 1."""
    a, b, c = tri
    sides = [d2(a, b), d2(b, c), d2(a, c)]
    twice_area = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return all(s <= 1 for s in sides) and twice_area != 0, f"L1 sides^2={sides}"


def lemma2_ok(a: Fraction, b: Fraction) -> tuple[bool, str]:
    """Lemma 2's hypothesis: `0 < a <= 1`, `0 < b <= 1` and `a + 2b <= 2 sqrt(2)`.

    The last is tested as `(a + 2b)^2 <= 8`, which is equivalent for `a + 2b >= 0`.
    """
    ok = a > 0 and b > 0 and a <= 1 and b <= 1 and le_sqrt(a + 2 * b, Fraction(8))
    return ok, f"L2 a={a} b={b} (a+2b)^2={(a + 2 * b) ** 2}<=8"


def lemma6_ok(a: Fraction, b: Fraction) -> tuple[bool, str]:
    """Lemma 6's hypothesis on the wall quadrilateral.

    `0 < a < 2 sqrt(2) - 2`, `0 < b <= 1`, and `(a, b)` within 1 of `(0, 1)`. The first
    is tested as `(a + 2)^2 < 8`.
    """
    ok = a > 0 and lt_sqrt(a + 2, Fraction(8)) and 0 < b <= 1 and a * a + (1 - b) ** 2 <= 1
    note = f"L6 a={a} b={b} (a+2)^2={(a + 2) ** 2}<8 a^2+(1-b)^2={a * a + (1 - b) ** 2}<=1"
    return ok, note


def strip_regions(
    y_lo: Fraction, xs_lo: list[Fraction], y_hi: Fraction, xs_hi: list[Fraction], m: Fraction
) -> list[Region]:
    """The regions tiling `[0, m] x [y_lo, y_hi]` between two consecutive rows.

    The row with `k + 1` points `a_0 < ... < a_k` and the row with `k` points
    `b_0 < ... < b_{k-1}` must interleave, `a_j <= b_j <= a_{j+1}`. The strip is then
    tiled by the zigzag triangles `(a_0, b_0, a_1), (b_0, a_1, b_1), ...` (Lemma 1) and
    two wall quadrilaterals (Lemma 6). Returns `(kind, polygon, hypothesis_holds, note)`.
    """
    lo_xs, hi_xs = sorted(xs_lo), sorted(xs_hi)
    ya, yb = y_lo, y_hi
    if len(lo_xs) < len(hi_xs):
        lo_xs, hi_xs, ya, yb = hi_xs, lo_xs, yb, ya
    if len(lo_xs) != len(hi_xs) + 1:
        raise ValueError(f"rows do not interleave in count: {lo_xs} {hi_xs}")
    for j in range(len(hi_xs)):
        if not lo_xs[j] <= hi_xs[j] <= lo_xs[j + 1]:
            raise ValueError(f"rows do not interleave: {lo_xs} {hi_xs}")
    zig: Polygon = []
    for j in range(len(hi_xs)):
        zig.append((lo_xs[j], ya))
        zig.append((hi_xs[j], yb))
    zig.append((lo_xs[-1], ya))
    regions: list[Region] = []
    a = abs(y_hi - y_lo)
    for side, near, far, wx in (
        ("L", zig[0], zig[1], Fraction(0)),
        ("R", zig[-1], zig[-2], m),
    ):
        near_d = near[0] - wx if side == "L" else wx - near[0]
        far_d = far[0] - wx if side == "L" else wx - far[0]
        poly: Polygon = [(wx, near[1]), near, far, (wx, far[1])]
        if far_d == 1 and near_d <= 1:
            ok, note = lemma6_ok(a, near_d)
            kind = "L6"
        else:
            ok, note = False, f"unhandled wall piece far={far} near={near}"
            kind = "??"
        regions.append((kind, poly, ok, f"{side}-wall {note}"))
    for i in range(len(zig) - 2):
        tri = (zig[i], zig[i + 1], zig[i + 2])
        ok, note = lemma1_ok(tri)
        regions.append(("L1", list(tri), ok, note))
    return regions


def edge_regions(y: Fraction, xs: list[Fraction], m: Fraction, *, bottom: bool) -> list[Region]:
    """The Lemma 2 rectangles between a wall-parallel edge row and its wall."""
    regions: list[Region] = []
    b = y if bottom else m - y
    cuts = [Fraction(0), *sorted(xs), m]
    for x0, x1 in pairwise(cuts):
        a = x1 - x0
        ok, note = lemma2_ok(a, b)
        y0, y1 = (Fraction(0), y) if bottom else (y, m)
        poly: Polygon = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        regions.append(("L2", poly, ok, f"edge {note}"))
    return regions


def all_regions(
    rows: list[list[Fraction]], m: Fraction = Fraction(M), ys: tuple[Fraction, ...] = ROW_Y
) -> list[Region]:
    """Every region of the tiling induced by one configuration."""
    regs = edge_regions(ys[0], rows[0], m, bottom=True)
    for i in range(len(ys) - 1):
        regs += strip_regions(ys[i], rows[i], ys[i + 1], rows[i + 1], m)
    regs += edge_regions(ys[-1], rows[-1], m, bottom=False)
    return regs


def poly_area2(poly: Polygon) -> Fraction:
    """Twice the absolute area of a simple polygon, by the shoelace formula."""
    s = Fraction(0)
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    return abs(s)


def convex_interiors_overlap(p_poly: Polygon, q_poly: Polygon) -> bool:
    """Separating-axis test for two convex polygons with exact coordinates.

    True exactly when the *interiors* intersect; touching along an edge or at a vertex
    is not an overlap, which is what a tiling needs.
    """
    for poly in (p_poly, q_poly):
        n = len(poly)
        for i in range(n):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % n]
            nx, ny = y1 - y0, x0 - x1
            proj_p = [nx * x + ny * y for x, y in p_poly]
            proj_q = [nx * x + ny * y for x, y in q_poly]
            if max(proj_p) <= min(proj_q) or max(proj_q) <= min(proj_p):
                return False
    return True


def check_tiling(regs: list[Region], m: Fraction) -> tuple[bool, str]:
    """The regions tile `[0, m]^2`: their areas sum to `m^2` and no two interiors meet."""
    area = sum((poly_area2(r[1]) for r in regs), Fraction(0)) / 2
    if area != m * m:
        return False, f"area {area} != {m * m}"
    for (i, r), (j, s) in combinations(enumerate(regs), 2):
        if convex_interiors_overlap(r[1], s[1]):
            return False, f"overlap between region {i} and {j}"
    return True, f"area {area} == {m * m}, no overlaps"


def unavoidable(
    rows: list[list[Fraction]], m: Fraction = Fraction(M), ys: tuple[Fraction, ...] = ROW_Y
) -> tuple[bool, list[str]]:
    """Is this configuration unavoidable in `[0, m]^2`?

    True when the induced regions tile the square and every region's lemma hypothesis
    holds. The returned notes lead with the tiling note and then name every region
    whose hypothesis failed.
    """
    regs = all_regions(rows, m, ys)
    ok_tiling, note = check_tiling(regs, m)
    bad = [f"{kind} {poly} {n}" for kind, poly, ok, n in regs if not ok]
    return ok_tiling and not bad, [note, *bad]


def main() -> int:
    """Report the two base configurations, as a smoke check of this module."""
    failed = 0
    for colour in ("red", "blue"):
        ok, notes = unavoidable(base_rows(colour))
        print(f"{colour}: unavoidable={ok} points={len(points(colour))} {notes[0]}")
        for note in notes[1:]:
            print(f"    {note}")
        failed += 0 if ok else 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
