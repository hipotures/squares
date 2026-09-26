"""Prepared integer predicates for repeated exact rational-square queries.

For a closed slab ``abs(a*x + b*y - c) <= h``, multiply the four fixed
rational coefficients by their positive least common denominator once. For a
query ``(X/D, Y/D)`` the test is then exactly
``(C-H)*D <= A*X + B*Y <= (C+H)*D``. Python integers are unbounded; there is
no float conversion, epsilon, rounding, or change from closed to open edges.

Preparation is local to one pricing/ceiling call. It is not a global cache and
never modifies or serialises the caller's squares. The float candidate survey
and exact-intersection construction remain the caller's responsibility.
"""

from __future__ import annotations

from collections.abc import Iterable
from fractions import Fraction
from math import gcd, lcm
from typing import Protocol

from sqpack.fractional.native_ab_hooks import exact_at, exact_cost

type IntegerSlab = tuple[int, int, int, int]
type HomogeneousPoint = tuple[int, int, int]
type Point = tuple[Fraction, Fraction]


class SlabSquare(Protocol):
    @property
    def ax(self) -> Fraction: ...
    @property
    def ay(self) -> Fraction: ...
    @property
    def u(self) -> Fraction: ...
    @property
    def bx(self) -> Fraction: ...
    @property
    def by(self) -> Fraction: ...
    @property
    def v(self) -> Fraction: ...
    @property
    def half(self) -> Fraction: ...


def _slab(a: Fraction, b: Fraction, c: Fraction, half: Fraction) -> IntegerSlab:
    denominator = lcm(a.denominator, b.denominator, c.denominator, half.denominator)
    aa = a.numerator * (denominator // a.denominator)
    bb = b.numerator * (denominator // b.denominator)
    cc = c.numerator * (denominator // c.denominator)
    hh = half.numerator * (denominator // half.denominator)
    return aa, bb, cc - hh, cc + hh


def _point(x: Fraction, y: Fraction) -> HomogeneousPoint:
    if x.denominator == y.denominator:
        return x.numerator, y.numerator, x.denominator
    common = gcd(x.denominator, y.denominator)
    x_multiplier = y.denominator // common
    y_multiplier = x.denominator // common
    return x.numerator * x_multiplier, y.numerator * y_multiplier, x.denominator * x_multiplier


def _contains(first: IntegerSlab, second: IntegerSlab, point: HomogeneousPoint) -> bool:
    x, y, denominator = point
    a, b, lower, upper = first
    projection = a * x + b * y
    if projection < lower * denominator or projection > upper * denominator:
        return False
    a, b, lower, upper = second
    projection = a * x + b * y
    return lower * denominator <= projection <= upper * denominator


class PreparedDepth:
    """Exact weighted depth and orbit reduced cost with coefficients prepared once."""

    def __init__(self, weighted: Iterable[tuple[SlabSquare, Fraction]]) -> None:
        self._weighted = tuple(
            (
                _slab(square.ax, square.ay, square.u, square.half),
                _slab(square.bx, square.by, square.v, square.half),
                weight,
            )
            for square, weight in weighted
        )

    @exact_at
    def at(self, x: Fraction, y: Fraction) -> Fraction:
        point = _point(x, y)
        return sum(
            (
                weight
                for first, second, weight in self._weighted
                if _contains(first, second, point)
            ),
            start=Fraction(0),
        )

    @exact_cost
    def reduced_cost(self, orbit: tuple[Point, ...], outer_side: Fraction) -> Fraction:
        half = outer_side / 2
        centred = tuple(_point(x - half, y - half) for x, y in orbit)
        price = Fraction(0)
        # Keep square/weight order and duplicate images, including stabilisers.
        for first, second, weight in self._weighted:
            covered = sum(1 for point in centred if _contains(first, second, point))
            price += weight * covered
        return Fraction(len(orbit)) - price
