"""Finite exact BC303 T2 geometry controls; no measure or charge is read.

This replays the independent review predicates. It does not authenticate source atoms
or decide either T2 surplus threshold.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import pairwise, product
from math import isqrt

type Point = tuple[Fraction, Fraction]
type Matrix = tuple[int, int, int, int]

Q, H = Fraction(96, 25), Fraction(9977, 20000)
A, B = Fraction(3152, 3175), Fraction(2336, 3175)
DELTA = A - B
MARKS = ((A, B), (B, A))
MAX_T = Fraction(207107, 500000)


def add(a: Point, b: Point) -> Point:
    return a[0] + b[0], a[1] + b[1]


def sub(a: Point, b: Point) -> Point:
    return a[0] - b[0], a[1] - b[1]


def scale(a: Point, c: Fraction) -> Point:
    return c * a[0], c * a[1]


def turn(a: Point) -> Point:
    return -a[1], a[0]


def dot(a: Point, b: Point) -> Fraction:
    return a[0] * b[0] + a[1] * b[1]


def det(a: Point, b: Point) -> Fraction:
    return a[0] * b[1] - a[1] * b[0]


def ray(t: Fraction) -> Point:
    return (1 - t * t) / (1 + t * t), 2 * t / (1 + t * t)


def axis_set(r: Point) -> tuple[Point, ...]:
    s = turn(r)
    return r, s, scale(r, Fraction(-1)), scale(s, Fraction(-1))


def bins(r: Point) -> set[int]:
    x, y = r
    inequalities = (
        x >= y >= 0,
        y >= x >= 0,
        y >= -x >= 0,
        -x >= y >= 0,
        -x >= -y >= 0,
        -y >= -x >= 0,
        -y >= x >= 0,
        x >= -y >= 0,
    )
    return {i for i, value in enumerate(inequalities) if value}


def square(z: Point, r: Point, half: Fraction) -> tuple[Point, ...]:
    s = turn(r)
    return tuple(
        add(z, add(scale(r, half * x), scale(s, half * y)))
        for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))
    )


def edges(poly: tuple[Point, ...], p: Point) -> tuple[Fraction, ...]:
    return tuple(
        det(sub(y, x), sub(p, x)) for x, y in zip(poly, poly[1:] + poly[:1], strict=True)
    )


def labels(z: Point, r: Point) -> set[int]:
    result: set[int] = set()
    poly = square(z, r, H)
    for mark_number, mark in enumerate(MARKS):
        if min(edges(poly, mark)) < 0:
            continue
        displacement = sub(z, mark)
        for e in axis_set(r):
            if dot(displacement, e) >= 0 and dot(displacement, turn(e)) >= 0:
                result.update(8 * mark_number + j for j in bins(e))
    return result


def linear(m: Matrix, p: Point) -> Point:
    a, b, c, d = m
    return a * p[0] + b * p[1], c * p[0] + d * p[1]


def affine(m: Matrix, p: Point) -> Point:
    x, y = linear(m, p)
    return x + (Q if min(m[:2]) < 0 else 0), y + (Q if min(m[2:]) < 0 else 0)


D4: tuple[Matrix, ...] = tuple(
    m for sx, sy in product((-1, 1), repeat=2) for m in ((sx, 0, 0, sy), (0, sx, sy, 0))
)


def run_controls() -> dict[str, object]:
    """Check source-chart geometry, boundary cases, and the split witness exactly."""
    ts = tuple(MAX_T * j / 180 for j in range(181))
    lower_bounds = (Fraction(0), *((x + y) / (1 - x * y) for x, y in pairwise(ts)))
    upper_bounds = (*lower_bounds[1:], Fraction(1))
    assert all(
        0 <= lower_bound < u <= 1
        for lower_bound, u in zip(lower_bounds, upper_bounds, strict=True)
    )
    assert ts[-2] ** 2 + 2 * ts[-2] - 1 < 0 < ts[-1] ** 2 + 2 * ts[-1] - 1
    extent_squared = tuple(
        (1 + lower_bound) ** 2 / (4 * (1 + lower_bound * lower_bound))
        for lower_bound in lower_bounds
    )
    rational_extent_indices = [
        j
        for j, e2 in enumerate(extent_squared)
        if isqrt(e2.numerator) ** 2 == e2.numerator
        and isqrt(e2.denominator) ** 2 == e2.denominator
    ]
    assert rational_extent_indices == [0]
    charts = {
        (j, reflected): (r[1], r[0]) if reflected else r
        for j, t in enumerate(ts)
        for r in (ray(t),)
        for reflected in (False, True)
    }
    orientation_sets = {frozenset(axis_set(r)) for r in charts.values()}
    assert len(charts) == 362
    assert len(orientation_sets) == 361
    assert len({e for r in charts.values() for e in axis_set(r)}) == 1444

    alias_transport_checks = 0
    for m in D4:
        determinant = m[0] * m[3] - m[1] * m[2]
        for (j, reflected), r in charts.items():
            expected = charts[j, reflected ^ (determinant < 0)]
            assert {linear(m, e) for e in axis_set(r)} == set(axis_set(expected))
            proper_first = linear(m, r if determinant > 0 else turn(r))
            proper_second = linear(m, turn(r) if determinant > 0 else r)
            assert turn(proper_first) == proper_second
            alias_transport_checks += 1

    eligible = []
    critical_centre_checks = 0
    for (j, reflected), source_r in charts.items():
        eligible_rays = [e for e in axis_set(source_r) if 0 in bins(e)]
        if not eligible_rays:
            continue
        assert len(eligible_rays) == 1
        c, s = r = eligible_rays[0]
        eligible.append({"index": j, "reflected": reflected, "ray": list(map(str, r))})
        if j != 0:
            assert 0 < s < c
        assert (7 in set.union(*(bins(e) for e in axis_set(r)))) == (j == 0)
        x_cut, y_cut = H - DELTA * (c - s), DELTA * (c + s)
        assert 0 < x_cut < H
        assert 0 < y_cut < H
        x_values = (Fraction(0), x_cut / 2, x_cut, (x_cut + H) / 2, H)
        y_values = (Fraction(0), y_cut / 2, y_cut, (y_cut + H) / 2, H)
        for x, y in product(x_values, y_values):
            z = add(MARKS[0], add(scale(r, x), scale(turn(r), y)))
            lab = labels(z, r)
            contained2 = min(edges(square(z, r, H), MARKS[1])) >= 0
            expected_c = x <= x_cut and (j != 0 or y < DELTA)
            assert (contained2 and 0 in lab and 15 not in lab) == expected_c
            assert (not contained2 and 0 in lab) == (x > x_cut)
            if contained2 and expected_c:
                wall_clearances = (*z, Q - z[0], Q - z[1])
                actual_projection = all(
                    w >= 0 and w * w >= extent_squared[j] for w in wall_clearances
                )
                reduced_projection = z[0] >= 0 and z[0] * z[0] >= extent_squared[j]
                assert actual_projection == reduced_projection
            if x > x_cut:
                assert z[0] > A + (c - s) * (H - DELTA * c) > A
                assert z[1] >= B
                assert all(w > 0 and 2 * w * w > 1 for w in (*z, Q - z[0], Q - z[1]))
            critical_centre_checks += 1

    assert len(eligible) == 182
    assert {(row["index"], row["reflected"]) for row in eligible} == (
        {(0, False), (0, True), (180, True)} | {(j, False) for j in range(1, 180)}
    )
    assert len({tuple(row["ray"]) for row in eligible}) == 181

    z1, z2 = (Fraction(149, 100), Fraction(737, 1000)), (Fraction(71, 100), Fraction(5, 3))
    r1, r2 = ray(Fraction(0)), ray(MAX_T)
    u1, u2 = ray(Fraction(0)), ray(Fraction(207, 500))
    parents = (square(z1, u1, Fraction(1, 2)), square(z2, u2, Fraction(1, 2)))
    cores = (square(z1, r1, H), square(z2, r2, H))
    assert all(0 <= coordinate <= Q for p in parents for v in p for coordinate in v)
    assert all(
        min(edges(p, v)) > 0 for p, core in zip(parents, cores, strict=True) for v in core
    )
    assert [[min(edges(core, mark)) >= 0 for mark in MARKS] for core in cores] == [
        [True, False],
        [False, True],
    ]
    assert labels(z1, r1) == {0, 7}
    assert labels(z2, r2) == {9}
    parent_slope = u2[1] / u2[0]
    assert lower_bounds[180] < parent_slope < upper_bounds[180]
    normal = (Fraction(-1), Fraction(1))
    separation = min(dot(v, normal) for v in parents[1]) - max(
        dot(v, normal) for v in parents[0]
    )
    assert separation == Fraction(2022521, 878547000) > 0
    assert A + H - Fraction(1, 2) < 1

    fixture_d4_checks = 0
    for m in D4:
        corner = affine(m, (Fraction(0), Fraction(0)))
        pullback = (-1 if corner[0] == Q else 1, 0, 0, -1 if corner[1] == Q else 1)
        swapped = m[0] == 0
        for z, r in ((z1, r1), (z2, r2)):
            target_z = affine(pullback, affine(m, z))
            target_r = linear(pullback, linear(m, r))
            expected = (
                {8 * (1 - label // 8) + (7 - label % 8) % 8 for label in labels(z, r)}
                if swapped
                else labels(z, r)
            )
            assert labels(target_z, target_r) == expected
            fixture_d4_checks += 1

    return {
        "scope": "Finite exact geometry only; no atom file or charge evaluation",
        "source_charts": len(charts),
        "selected_orientations": len(orientation_sets),
        "signed_rays": 1444,
        "bin_zero_source_charts": len(eligible),
        "bin_zero_selected_orientations": 181,
        "d4_chart_and_proper_frame_checks": alias_transport_checks,
        "critical_centre_checks": critical_centre_checks,
        "split_fixture_corner_transport_checks": fixture_d4_checks,
        "rational_minimum_parent_extent_indices": rational_extent_indices,
        "split_parent_separation": str(separation),
        "axis_parent_centre_interval_width": str(A + H - Fraction(1, 2)),
    }
