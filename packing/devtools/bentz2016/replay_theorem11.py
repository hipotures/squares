"""Replay every quantitative step of Bentz 2016 Theorem 11 at the printed constants.

Twenty-four rows, each with its exact value, its decimal, and a pass or fail. The tool
exits non-zero if any row fails, so a wrong constant stops the lane rather than being
absorbed into a table nobody reads. That is `H-226`'s declared control: "a replay of
Theorem 11 that fails at the printed constants stops the lane and files a defect".

Usage, from `packing/`:

```
uv run --frozen --all-extras --group dev python -m devtools.bentz2016.replay_theorem11 \\
  --json campaign/.../bentz2016-theorem11-replay.json
```

`--negative-control` reruns the whole table with the finishing line at `(sqrt(2)-1)/2`,
the constant the transcription printed before `D-505`. Rows 11, 12, 14, 15 and the
region rows then fail, which is the point: the table is sensitive to the constant, so a
passing table is evidence and not decoration.

**What the rows are.** Rows 1 to 3 are unavoidability: the two base configurations and
every configuration the proof's moves reach, each checked as an exact tiling by Lemma
1, 2 and 6 regions (`devtools.bentz2016.geometry`). Rows 4 to 10 are the constants the
moves need. Rows 11 to 16 are the chord steps on the finishing line, including the two
chord infima. Rows 17 to 24 are the midpoint-region finish
(`devtools.bentz2016.regions`), with the corners checked against the coordinates the
paper prints beside Figures 4 and 5.

**Sources.** `packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md`:
Lemmas 1 to 7 at lines 55 to 92, Theorem 8 at 108, Theorem 9 at 124 to 160, Theorem 11
at 163 to 199. The constants are the ones the archived PDF prints, repaired in that
file by `D-505` (the finishing line and the standoff), `D-506` (Lemma 7's bound) and
`D-507` (Theorem 9's budget line).

**What is not replayed here.** Lemmas 1 to 7 are used, not proved: this tool checks
their hypotheses hold where the proof invokes them. Row 16's infimum is derived from
the two branches of the chord function of a square crossing a vertical line, with the
random screen reported beside it as a check on the algebra rather than as its source.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path

import sympy as sp

from devtools.bentz2016.geometry import M, base_rows, unavoidable
from devtools.bentz2016.regions import (
    HALF,
    LINE_X,
    STANDOFF,
    Candidate,
    FinishResult,
    finish_check,
)

S2 = sp.sqrt(2)
S3 = sp.sqrt(3)
#: The constant the transcription printed before `D-505`; the negative control.
WRONG_LINE_X: sp.Expr = (S2 - 1) / 2
#: Tolerance against a coordinate the paper prints to two decimals as "approximate".
PRINTED_TOL = sp.Rational(1, 50)
#: Grid of row shifts screened in row 3: -0.1 to 0.1 in steps of 0.01.
SHIFT_GRID: tuple[Fraction, ...] = tuple(Fraction(-1, 10) + Fraction(k, 100) for k in range(21))
#: Grid of end-point positions screened in row 3: 0.5 to 1.0 in steps of 0.01.
END_GRID: tuple[Fraction, ...] = tuple(Fraction(1, 2) + Fraction(k, 100) for k in range(51))


@dataclass(frozen=True)
class ReplayRow:
    """One row of the replay table."""

    number: int
    step: str
    exact: str
    decimal: str
    holds: bool
    note: str


def _dec(value: sp.Expr, places: int = 6) -> str:
    return f"{float(sp.N(value, 30)):.{places}f}"


def _row(
    number: int, step: str, exact: sp.Expr | str, *, holds: bool, note: str = ""
) -> ReplayRow:
    if isinstance(exact, str):
        return ReplayRow(number, step, exact, "", holds, note)
    return ReplayRow(number, step, str(sp.simplify(exact)), _dec(exact), holds, note)


def _with_shift(rows: list[list[Fraction]], i: int, t: Fraction) -> list[list[Fraction]]:
    moved = [row[:] for row in rows]
    moved[i] = [x + t for x in moved[i]]
    return moved


def _with_end_point(
    rows: list[list[Fraction]], i: int, b: Fraction, *, right: bool
) -> list[list[Fraction]]:
    moved = [row[:] for row in rows]
    if right:
        moved[i][-1] = Fraction(M) - b
    else:
        moved[i][0] = b
    return moved


def moved_configurations_hold(colour: str) -> tuple[bool, str, int]:
    """Row 3: every configuration the proof's moves reach is still unavoidable.

    The moves are the paper's (transcription line 171 for red, 173 for blue): shift a
    five-point row by `t` in `[-0.1, 0.1]` and back, and move an end point of such a
    row to `x = 1` or `x = 4` and back. Every lemma hypothesis is a polynomial
    inequality in the parameter whose extremes are at the endpoints -- squared side
    lengths are convex quadratics in `t`, Lemma 6's `a^2 + (1-b)^2` is convex in `b`,
    Lemma 2's `a + 2b` is linear -- so the endpoints decide and the interior grid is a
    screen. The simultaneous shift of both five-point rows, which the proof uses for
    red rows 2 and 4, is checked at both extremes.
    """
    rows = base_rows(colour)
    five = [i for i, row in enumerate(rows) if len(row) == 5]
    worst = ""
    checked = 0
    for i in five:
        for t in SHIFT_GRID:
            ok, notes = unavoidable(_with_shift(rows, i, t))
            checked += 1
            if not ok:
                worst = f"row {i + 1} shift {t}: {notes[1:3]}"
        for b in END_GRID:
            for right in (False, True):
                ok, notes = unavoidable(_with_end_point(rows, i, b, right=right))
                checked += 1
                if not ok:
                    worst = f"row {i + 1} end point at {b} right={right}: {notes[1:3]}"
    for t in (Fraction(-1, 10), Fraction(1, 10)):
        together = rows
        for i in five:
            together = _with_shift(together, i, t)
        ok, notes = unavoidable(together)
        checked += 1
        if not ok:
            worst = f"all five-point rows shifted {t}: {notes[1:3]}"
    note = worst or (
        f"five-point rows {[i + 1 for i in five]}: {checked} configurations, "
        f"shifts in [-1/10, 1/10] and end points in [1/2, 1], all tile"
    )
    return not worst, note, checked


def chord_infimum(x0: sp.Expr, line_x: sp.Expr) -> sp.Expr:
    """The infimum of the chord cut on `l` by a box in `S` covering `[x0, 1] x {y}`.

    A square of side `s > 1` at angle `th` in `[0, pi/4]` whose centre is at horizontal
    offset `t` from the line cuts a chord of `s / cos th` while `|t| <= s(cos-sin)/2`
    and `(s(cos+sin)/2 - |t|) / (sin th cos th)` beyond that. Both branches decrease in
    `|t|`, so the infimum sits at whichever extreme offset the two containments allow:
    the box must reach left to `x0`, giving `t <= s(cos+sin)/2 - (c - x0)`, and it must
    stay inside `S`, giving `t >= s(cos+sin)/2 - c`. The first extreme at `th = pi/4`
    is `2(c - x0)`; the second at `th = pi/4`, `s = 1` is `2(sqrt(2) - c)`, which is
    Lemma 5's value; the crossing branch never falls below `s > 1`. The infimum is the
    least of the three, approached as `s -> 1`.
    """
    right_branch = 2 * (line_x - x0)
    wall_branch = 2 * (S2 - line_x)
    return sp.Min(sp.Integer(1), right_branch, wall_branch)


def _chord_numeric(cx: float, cy: float, th: float, s: float, x0: float) -> float:
    """The chord a square cuts on the vertical line `x = x0`, for the random screen."""
    cs, sn = math.cos(th), math.sin(th)
    lo, hi = -1e9, 1e9
    for a, b in ((cs, sn), (-sn, cs)):
        k = (x0 - cx) * a
        if abs(b) < 1e-15:
            if abs(k) >= s / 2:
                return 0.0
            continue
        t1 = (-s / 2 - k) / b + cy
        t2 = (s / 2 - k) / b + cy
        lo = max(lo, min(t1, t2))
        hi = min(hi, max(t1, t2))
    return max(0.0, hi - lo)


def _covers(cx: float, cy: float, th: float, s: float, *, px: float, py: float) -> bool:
    cs, sn = math.cos(th), math.sin(th)
    dx, dy = px - cx, py - cy
    half = s / 2 + 1e-12
    return abs(dx * cs + dy * sn) <= half and abs(-dx * sn + dy * cs) <= half


def _inside_square(cx: float, cy: float, th: float, s: float) -> bool:
    r = (abs(math.cos(th)) + abs(math.sin(th))) * s / 2
    return cx - r >= -1e-12 and cy - r >= -1e-12 and cx + r <= M + 1e-12 and cy + r <= M + 1e-12


def chord_screen(x0: float, line_x: float, samples: int = 60000) -> float:
    """A random screen plus local descent on the chord infimum.

    This is a check on the algebra of `chord_infimum`, not its source: if a box were
    found cutting a chord below the analytic infimum, the algebra would be wrong. It
    is reported beside the exact value and gates rows 15 and 16. An earlier random
    search of this kind returned 0.8468 for the partial segment and was read as the
    infimum; it was a search artefact, and the exact value is `2 sqrt(2) - 2`.
    """
    rng = random.Random(7)
    y = 2.5
    best = 9.0
    best_box: tuple[float, float, float, float] | None = None
    for _ in range(samples):
        cx = rng.uniform(0.3, 1.9)
        cy = rng.uniform(y - 0.75, y + 0.75)
        th = rng.uniform(0, math.pi / 2)
        s = 1.0 + rng.random() * 0.01
        if not _inside_square(cx, cy, th, s):
            continue
        if not (_covers(cx, cy, th, s, px=x0, py=y) and _covers(cx, cy, th, s, px=1.0, py=y)):
            continue
        chord = _chord_numeric(cx, cy, th, s, line_x)
        if chord < best:
            best, best_box = chord, (cx, cy, th, s)
    if best_box is None:
        return best
    cx, cy, th, s = best_box
    step = 0.05
    while step > 1e-9:
        improved = False
        for dcx, dcy, dth, ds in (
            (step, 0.0, 0.0, 0.0),
            (-step, 0.0, 0.0, 0.0),
            (0.0, step, 0.0, 0.0),
            (0.0, -step, 0.0, 0.0),
            (0.0, 0.0, step, 0.0),
            (0.0, 0.0, -step, 0.0),
            (0.0, 0.0, 0.0, step),
            (0.0, 0.0, 0.0, -step),
        ):
            nxt = (cx + dcx, cy + dcy, th + dth, min(1.01, max(1.0, s + ds)))
            if not _inside_square(*nxt):
                continue
            if not (_covers(*nxt, px=x0, py=y) and _covers(*nxt, px=1.0, py=y)):
                continue
            chord = _chord_numeric(*nxt, line_x)
            if chord < best - 1e-13:
                best, (cx, cy, th, s) = chord, nxt
                improved = True
        if not improved:
            step /= 2
    return best


def chord_at_minimiser(x0: float, line_x: float) -> float:
    """The chord of the explicit near-extremal box: a 45-degree unit box at `(x0, y)`.

    Its left vertex sits a hair left of `(x0, y)`, so it covers the segment, and it is
    the box the analytic infimum is approached by as the side falls to 1.
    """
    eps = 1e-9
    cx = x0 - eps + 1.0 / math.sqrt(2)
    return _chord_numeric(cx, 2.5, math.pi / 4, 1.0, line_x)


def _printed_match(
    corners: list[Candidate], printed: list[tuple[str, str]]
) -> tuple[bool, sp.Expr, str]:
    """Do the computed corners agree with the coordinates the paper prints?

    The paper prints them to two decimals and calls them approximate, so the test is a
    tolerance, not equality. The worst deviation over the matched pairs is reported so
    a reader sees how close the printed figure is rather than only that it passed.
    """
    if len(corners) != len(printed):
        return False, sp.Integer(0), f"{len(corners)} corners, {len(printed)} printed"
    found = sorted(((sp.N(px, 30), sp.N(py, 30)) for px, py, _ in corners), key=str)
    want = sorted(
        ((sp.Rational(px), sp.Rational(py)) for px, py in printed), key=lambda p: p[1]
    )
    found = sorted(found, key=lambda p: p[1])
    worst = sp.Integer(0)
    for (fx, fy), (wx, wy) in zip(found, want, strict=True):
        worst = max(worst, abs(sp.N(fx - wx, 30)), abs(sp.N(fy - wy, 30)))
    shown = ", ".join(f"({_dec(px)}, {_dec(py)})" for px, py, _ in corners)
    note = f"{shown}; printed {printed}, worst deviation {_dec(worst)}"
    return bool(worst <= PRINTED_TOL), worst, note


def _sup_row(number: int, step: str, result: FinishResult | None, note: str) -> ReplayRow:
    if result is None:
        return _row(number, step, "region empty", holds=False, note=note)
    return _row(number, step, result.exact(), holds=result.forced, note=note)


def replay_rows(*, line_x: sp.Expr = LINE_X) -> list[ReplayRow]:
    """The twenty-four rows, computed at the given finishing-line constant."""
    rows: list[ReplayRow] = []
    standoff = STANDOFF
    x_left = line_x + standoff

    # ---- rows 1 to 3: unavoidability, by exact tiling.
    for number, colour in ((1, "red"), (2, "blue")):
        ok, notes = unavoidable(base_rows(colour))
        rows.append(
            _row(
                number,
                f"{colour.capitalize()} set unavoidable (Lemmas 1, 2, 6 tiling of [0,5]^2)",
                "area 25, 0 overlaps",
                holds=ok,
                note=notes[0],
            )
        )
    red_ok, red_note, red_n = moved_configurations_hold("red")
    blue_ok, blue_note, blue_n = moved_configurations_hold("blue")
    rows.append(
        _row(
            3,
            "Unavoidability under the row moves (red rows 2, 4; blue rows 1, 3, 5)",
            "all lemma hypotheses hold at every grid parameter",
            holds=red_ok and blue_ok,
            note=f"red: {red_note}; blue: {blue_note}; {red_n + blue_n} configurations",
        )
    )

    # ---- rows 4 to 10: the constants the moves need.
    rows.append(
        _row(
            4,
            "Row spacing 0.8 <= sqrt3/2 (Lemma 1)",
            S3 / 2 - sp.Rational(4, 5),
            holds=bool(sp.Rational(4, 5) <= S3 / 2),
            note="Lemma 1 needs sqrt(1/4 + v^2) <= 1 for the zigzag triangles",
        )
    )
    lemma2_b = S2 - sp.Rational(1, 2)
    rows.append(
        _row(
            5,
            "Wall distance 0.9 <= sqrt2 - 1/2 (Lemma 2, a = 1)",
            lemma2_b - sp.Rational(9, 10),
            holds=bool(lemma2_b >= sp.Rational(9, 10)),
            note="a + 2b <= 2 sqrt2 at a = 1 is b <= sqrt2 - 1/2; independent of l",
        )
    )
    shift_side = sp.sqrt(sp.Rational(36, 100) + sp.Rational(64, 100))
    rows.append(
        _row(
            6,
            "Shift 0.1 at spacing 0.8: triangle side sqrt(0.36 + 0.64)",
            shift_side,
            holds=bool(shift_side <= 1),
            note="exactly 1; Lemma 1 allows <= 1, so the equality is admissible",
        )
    )
    rows.append(
        _row(
            7,
            "Lemma 6 needs a = 0.8 < 2 sqrt2 - 2",
            2 * S2 - sp.Rational(14, 5),
            holds=bool(sp.Rational(4, 5) < 2 * S2 - 2),
            note="the quadrilateral at the wall beside a shifted five-point row",
        )
    )
    corner_d = sp.sqrt(sp.Rational(64, 100) + sp.Rational(36, 100))
    rows.append(
        _row(
            8,
            "Lemma 6 needs (0.8, 0.4) within 1 of (0, 1)",
            corner_d,
            holds=bool(corner_d <= 1),
            note="distance exactly 1 at b = 0.4, the shifted leftmost point",
        )
    )
    rows.append(
        _row(
            9,
            "Lemma 2 a = 1, b = 0.9: a + 2b <= 2 sqrt2",
            2 * S2 - sp.Rational(14, 5),
            holds=bool(1 + 2 * sp.Rational(9, 10) <= 2 * S2),
            note="the edge rectangles against the bottom and top walls",
        )
    )
    diag = sp.Rational(101, 100) * S2
    rows.append(
        _row(
            10,
            "Two blue points in one box are closer than the diagonal",
            diag,
            holds=bool(sp.simplify(diag**2 - 2 * sp.Rational(101, 100) ** 2) == 0),
            note="definition: the diagonal of a maximal box of side 1.01 (line 170)",
        )
    )

    # ---- rows 11 to 16: the chord steps on the finishing line l: x = c.
    lemma5 = sp.simplify(2 * S2 - 2 * line_x)
    rows.append(
        _row(
            11,
            "Lemma 5 on wall x = 0 and l: 2 sqrt2 - 2d at d = c",
            lemma5,
            holds=bool(lemma5 == 1),
            note="the wall chord is empty, so the common chord is min{1, 1} = 1 on l",
        )
    )
    lemma7_dist = sp.simplify(line_x - sp.Rational(2, 5))
    rows.append(
        _row(
            12,
            "Lemma 7 needs dist((0.4, y), l) > 0.51",
            lemma7_dist,
            holds=bool(lemma7_dist > sp.Rational(51, 100)),
            note="the covered point on the far side of l from the midpoint",
        )
    )
    lemma7_printed = sp.Rational(505, 1000) * S2 - sp.Rational(51, 100)
    rows.append(
        _row(
            13,
            "Lemma 7 proof: 0.505 sqrt2 - 0.51 < (sqrt2-1)/2",
            lemma7_printed,
            holds=bool(lemma7_printed < (S2 - 1) / 2),
            note=f"(sqrt2-1)/2 = {_dec((S2 - 1) / 2)}; the bound repaired by D-506",
        )
    )
    lemma7_sharp = sp.simplify(sp.Rational(505, 1000) * S2 - lemma7_dist)
    rows.append(
        _row(
            14,
            "Lemma 7 with the actual distance: 0.505 sqrt2 - dist((0.4, y), l)",
            lemma7_sharp,
            holds=bool(lemma7_sharp < (S2 - 1) / 2),
            note="how far past l the midpoint of a box covering (0.4, y) can sit",
        )
    )
    line_f = float(sp.N(line_x, 30))
    full_inf = sp.simplify(chord_infimum(sp.Rational(2, 5), line_x))
    screen_full = chord_screen(0.4, line_f)
    full_f = float(sp.N(full_inf, 30))
    rows.append(
        _row(
            15,
            "Chord infimum on l, boxes in S containing [0.4, 1] x {y}",
            full_inf,
            holds=bool(full_inf == 1) and screen_full >= full_f - 1e-9,
            note=(
                "branches min{s/cos th, 2(c - 0.4), 2(sqrt2 - c)}, minimised as s -> 1 "
                "by the axis-parallel box and by the wall-touching 45-degree box; "
                f"screen {screen_full:.6f}, minimiser {chord_at_minimiser(0.4, line_f):.9f}"
            ),
        )
    )
    part_inf = sp.simplify(chord_infimum(HALF, line_x))
    screen_part = chord_screen(0.5, line_f)
    part_f = float(sp.N(part_inf, 30))
    rows.append(
        _row(
            16,
            "Chord infimum on l, boxes in S containing [0.5, 1] x {y}",
            part_inf,
            holds=bool(part_inf == 2 * S2 - 2) and screen_part >= part_f - 1e-9,
            note=(
                "the 45-degree box with a vertex at (0.5, y), any s; below 1, so a "
                "partial box need not charge more than 1 and the finish is needed; "
                f"screen {screen_part:.6f}, minimiser {chord_at_minimiser(0.5, line_f):.9f}"
            ),
        )
    )

    # ---- rows 17 to 24: the midpoint-region finish.
    rows.append(
        _row(
            17,
            "Standoff sqrt2/2 - 1/2 equals Lemma 4's (sqrt2-1)/2",
            standoff,
            holds=bool(sp.simplify(standoff - (S2 - 1) / 2) == 0),
            note="the PDF writes Lemma 4's threshold the other way round (D-505)",
        )
    )
    printed_left = sp.Rational(112, 100)
    rows.append(
        _row(
            18,
            "Left edge of the shaded regions, c + standoff",
            x_left,
            holds=bool(abs(sp.N(x_left - printed_left, 30)) <= PRINTED_TOL),
            note=f"printed 1.12 beside Figure 4; deviation {_dec(x_left - printed_left)}",
        )
    )
    case1 = finish_check(
        sp.Rational(5, 2),
        [2, 3],
        {"(3/2,5/2)": (sp.Rational(3, 2), sp.Rational(5, 2))},
        line_x=line_x,
    )["(3/2,5/2)"]
    case1_corners = case1.corners if case1 is not None else []
    on_line = [c for c in case1_corners if sp.N(c[0] - x_left, 30) == 0]
    off_line = [c for c in case1_corners if sp.N(c[0] - x_left, 30) != 0]
    ok19, _, note19 = _printed_match(on_line, [("112/100", "245/100"), ("112/100", "255/100")])
    rows.append(_row(19, "Figure 4 corners on the line", "see note", holds=ok19, note=note19))
    ok20, _, note20 = _printed_match(off_line, [("12/10", "24/10"), ("12/10", "26/10")])
    rows.append(
        _row(20, "Figure 4 corners on the big circle", "see note", holds=ok20, note=note20)
    )
    rows.append(
        _sup_row(
            21,
            "Case 1: the region lies within 1/2 of (1.5, 2.5)",
            case1,
            "sup of the distance over the exact region; forced when below 1/2",
        )
    )
    case2 = finish_check(
        sp.Rational(9, 10), [0, 1], {"(c,1)": (line_x, sp.Integer(1))}, line_x=line_x
    )["(c,1)"]
    case2_corners = case2.corners if case2 is not None else []
    ok22, _, note22 = _printed_match(
        case2_corners, [("113/100", "56/100"), ("113/100", "124/100")]
    )
    rows.append(
        _row(
            22,
            "Figure 5 corners at y_1 = 0.9",
            "see note",
            holds=ok22,
            note=note22 + "; consistent with x rounded up to 1.13",
        )
    )
    rows.append(
        _sup_row(
            23,
            "Case 2: the region lies within 1/2 of (c, 1), y_1 = 0.9",
            case2,
            "Figure 3 puts the end point of row 1 at (0.5, 0.9)",
        )
    )
    case2_pdf = finish_check(line_x, [0, 1], {"(c,1)": (line_x, sp.Integer(1))}, line_x=line_x)[
        "(c,1)"
    ]
    rows.append(
        _sup_row(
            24,
            "Case 2 with the PDF's (0.5, sqrt2 - 1/2) in place of (0.5, 0.9)",
            case2_pdf,
            "the paper's own slip; the step holds with either value, so no defect is "
            "filed against the source and the transcription is not edited",
        )
    )
    return rows


def render(rows: list[ReplayRow]) -> str:
    """The replay table as Markdown."""
    out = [
        "| # | Step (paper) | Exact value | Decimal | Holds |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        mark = "yes" if row.holds else "**NO**"
        out.append(f"| {row.number} | {row.step} | `{row.exact}` | {row.decimal} | {mark} |")
    return "\n".join(out)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m devtools.bentz2016.replay_theorem11",
        description="Replay Bentz 2016 Theorem 11 at the printed constants.",
    )
    parser.add_argument("--json", dest="json_out", default=None, help="write the table here")
    parser.add_argument(
        "--negative-control",
        action="store_true",
        help="rerun at the transcription's pre-D-505 line (sqrt2-1)/2, which must fail",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    line_x = WRONG_LINE_X if args.negative_control else LINE_X
    label = "negative control (sqrt2-1)/2" if args.negative_control else "printed sqrt2 - 1/2"
    print(
        f"Bentz 2016 Theorem 11 replay; finishing line l: x = {sp.simplify(line_x)} [{label}]"
    )
    rows = replay_rows(line_x=line_x)
    print(render(rows))
    failed = [row for row in rows if not row.holds]
    print()
    for row in rows:
        print(f"  {row.number:2d} {'ok  ' if row.holds else 'FAIL'} {row.note}")
    print(f"\n{len(rows) - len(failed)} of {len(rows)} rows hold.")
    if args.json_out:
        payload = {
            "tool": "devtools.bentz2016.replay_theorem11",
            "line_x": str(sp.simplify(line_x)),
            "line_x_decimal": _dec(line_x, 12),
            "negative_control": bool(args.negative_control),
            "rows": [asdict(row) for row in rows],
            "rows_total": len(rows),
            "rows_failed": [row.number for row in failed],
            "all_hold": not failed,
        }
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
        print(f"replay written to {out}")
    if failed:
        print(f"rows that do not hold: {[row.number for row in failed]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
