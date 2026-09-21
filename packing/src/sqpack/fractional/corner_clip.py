"""The convex corner clip: a domain predicate for lane-a Theorem B's free corners.

Lane-a's Theorem B bins each container corner by its penetration ``delta_j``, the
least value of ``x + y`` any unit square of the packing reaches in that corner's
frame. In a *free* bin the closed triangle ``T_d = {x, y >= 0, x + y <= d}`` meets no
square of the packing, so every core -- the closed ``B``-square at a net direction that
a unit square carries about its own centre -- avoids ``T_d`` as well, and the covering
program need only require mass 1 on the cores that do. Removing the rest is a *domain
cut*: it takes placements out of the row set without taking a unit out of the count,
which is the one thing Lemma D's ceiling does not already price.

The predicate, exactly
----------------------

Lemma 2, scaled from the unit square to a square of side ``S``: the linear functional
``x + y`` is extreme at the square's vertices, where it takes the four values
``a + b + S * {cos t, sin t, -sin t, -cos t}`` for a square centred at ``(a, b)`` at
angle ``t``. So

    min over the square of (x + y) = a + b - S * max(|cos t|, |sin t|)

and the square meets ``T_d`` exactly when that value is at most ``d``. Write
``reach = B * max(|cos t|, |sin t|)``. The four corners of the container are the D4
orbit of one, so with ``sigma`` in ``{+1, -1}^2`` and ``m`` the number of ``-1``s in it,
a core meets the triangle at corner ``sigma`` exactly when

    sigma_x * a + sigma_y * b - reach  <=  d - m * L

and the kept domain at one direction is the intersection of the four open complements:
the centre domain with four 45-degree corner cuts, hence **convex**, which is what lets
the event-cell sweep take a clip rather than a new engine (lane-a, 2026-09-08).

``max(|cos|, |sin|)`` rather than ``cos``
-----------------------------------------

On the net's own arc ``[0, pi/4]`` the two agree and lane-a prints ``cos``. They part
company as soon as an angle is folded, and two consumers fold: the interval route
searches the *doubled* net, ``theta_k`` and ``pi/2 - theta_k``, and a retained ceiling
family stores mirrored placements at half-tangent ``(1 - t) / (1 + t)``, whose angle is
near ``pi/2`` while the square itself is near axis-parallel. Using ``cos`` there reads a
flush corner core as deep in the container. Measured: it halves the mass the retained
88-family loses to the clip at ``96/25``, from 4 to 2, and so reports the residual as 9
where R1 measured 7.

Soundness, both ways
--------------------

*As a row domain.* If a unit square ``Q`` avoids ``T_d`` then its core ``P`` is a subset
of ``Q`` and avoids ``T_d`` too, so a core outside the kept domain is one no packing of
the free class can produce and dropping its row is sound. This is the corrected clip;
the earlier ``a + b > d + cos theta``, which tested the *unit* square at the core's net
angle, is unsafe and lane-a records the exact counterexample.

*As a constraint set.* Corner by corner the clip is also tight, which is what a ceiling
family on it needs in order to kill anything. Given a core at net angle ``t`` whose
centre clears one corner's cut, a unit square at the same angle containing it may be
offset by ``(1 - B) / 2`` in each rotated coordinate, which raises ``x + y`` at its
centre by ``(1 - B) / 2 * ((c + s) + |c - s|) = (1 - B) * max(c, s)``; that parent's
penetration at that corner is then exactly the core's. So no core is kept that a unit
square could not have produced at the corner in question, and the rows the clip leaves
are not slack by a margin the geometry could have removed. Against all four corners at
once the shift would have to serve four constraints with one vector, so the kept set may
still be a superset there; that direction is the safe one for a covering program, and a
ceiling family on the kept set bounds the program this repository actually runs.

Two boundary conventions, on purpose
------------------------------------

The exact free class is the **open** set ``{penetration > d}``: the triangle ``T_d`` is
closed, so a core whose penetration is exactly ``d`` touches it and no packing of the
class produces that core. The module keeps the boundary on one side in one place and on
the other side in the other, because the two consumers move in opposite directions and
each gets the side that is safe for it:

* ``excludes`` / ``excludes_square`` exclude on ``penetration <= d``, so the set they
  *keep* is the open ``{penetration > d}`` -- the class exactly. Their consumers
  (`colgen.dual_support`, `colgen.check_ceiling` through `colgen.square_excluded`,
  `ceiling`'s K4 condition, and the independent reader's K4) **drop** what the predicate
  excludes, and dropping a member of a ceiling family only weakens the ceiling it
  proves, never invalidates it, so parting with the boundary band there costs at most
  bound and never soundness.
* ``thresholds`` / ``half_planes`` / ``clip_polygon`` keep the **closed**
  ``{penetration >= d}``: the kept side of each half-plane is ``>=``, so the sweep's
  domain is the class's closure, larger by one measure-zero band. Its consumer
  **quantifies** Condition 5 over what is kept, so the extra band is extra rows the class
  cannot realise and a strictly harder Condition 5.

So the two kept sets differ on exactly the boundary band ``{penetration == d}``, and the
direction of the difference is chosen per consumer. Do not "tidy" one into the other
without re-deciding which way its consumer is conservative: making ``half_planes`` open
would drop rows out of a covering program, which is the unsound direction.
`test_the_two_kept_sets_differ_exactly_on_the_boundary_band` pins both.

Every quantity here is a ``Fraction``. With the half-tangent ``t`` rational,
``cos = (1 - t^2) / (1 + t^2)`` and ``sin = 2t / (1 + t^2)`` are rational, so ``reach``
is rational and no angle, tolerance or float takes part in the predicate.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

#: A closed half-plane in the rotated ``(u, v)`` frame, kept where
#: ``nu * u + nv * v >= offset``.
type HalfPlane = tuple[Fraction, Fraction, Fraction]

#: The four corner sign patterns, in the order (0,0), (L,0), (0,L), (L,L).
_CORNERS: tuple[tuple[int, int], ...] = ((1, 1), (-1, 1), (1, -1), (-1, -1))


class EmptyClippedDomainError(ValueError):
    """The clip leaves no admissible centre at some direction.

    Raised rather than returning an empty cell set, because a Condition 5 with nothing
    to quantify over is vacuously true and a gate that accepted it would be reporting a
    pass on an empty class. Every caller turns this into a refusal.
    """


@dataclass(frozen=True, slots=True)
class CornerClip:
    """Lane-a Theorem B's free-corner cut at one threshold, as an exact predicate.

    ``depth`` is the threshold ``d`` of the triangle ``T_d``. Theorem B states the bins
    for ``0 < d <= 1``; above 1 the uniqueness of the occupant fails and the clip is not
    the theorem's, so the value is refused here rather than silently reinterpreted.

    The methods do not all keep the same side of the boundary ``penetration == d``:
    ``excludes`` and ``excludes_square`` keep the open side, ``thresholds``,
    ``half_planes`` and ``clip_polygon`` the closed one, each because that is the
    conservative direction for its own consumer. "Two boundary conventions, on purpose"
    in the module docstring says which is which and why, and every method below repeats
    its own convention.
    """

    outer_side: Fraction
    square_side: Fraction
    depth: Fraction

    def __post_init__(self) -> None:
        if self.outer_side <= 0 or self.square_side <= 0:
            raise ValueError("sides must be positive")
        if not 0 < self.depth <= 1:
            raise ValueError("the corner threshold d must satisfy 0 < d <= 1")

    def reach(self, cosine: Fraction, sine: Fraction) -> Fraction:
        """``B * max(|cos|, |sin|)``: how far the core reaches past its centre in x + y.

        Folded, so a direction past ``pi/4`` -- the interval route's reflected net, a
        ceiling family's mirrored placement -- gets the same constant as the square it
        is congruent to.
        """

        return self.square_side * max(abs(cosine), abs(sine))

    def penetration(
        self, x: Fraction, y: Fraction, cosine: Fraction, sine: Fraction
    ) -> Fraction:
        """The least ``x + y`` the core reaches in any of the four corner frames."""

        reach = self.reach(cosine, sine)
        return min(sx * x + sy * y - reach + self._offset(sx, sy) for sx, sy in _CORNERS)

    def excludes(self, x: Fraction, y: Fraction, cosine: Fraction, sine: Fraction) -> bool:
        """Whether the core at this centre and direction meets some corner triangle.

        Closed: a core touching ``T_d`` at one point meets it, so the test is ``<=``,
        which is the closed triangle of the theorem. The set this predicate **keeps** is
        therefore the open ``{penetration > d}`` -- the free class exactly, boundary
        band excluded. That is the safe side for its consumers, which drop what it
        excludes from a ceiling family (`colgen.dual_support`, `colgen.check_ceiling`,
        `ceiling`'s K4); ``half_planes`` keeps the other side for its own
        consumer. See "Two boundary conventions, on purpose" in the module docstring.
        """

        return self.penetration(x, y, cosine, sine) <= self.depth

    def square_penetration(
        self,
        axes: tuple[Fraction, Fraction, Fraction, Fraction],
        centre: tuple[Fraction, Fraction],
        half: Fraction,
    ) -> Fraction:
        """The same quantity for a closed square given as two orthonormal slabs.

        ``axes`` is ``(ax, ay, bx, by)``: the square is
        ``|a . q - a . c| <= half`` and ``|b . q - b . c| <= half`` with ``a`` and ``b``
        orthonormal, which is the form `colgen.Square` and `ceiling.Placement` are
        stored in, and a D4 image of one has its axes permuted and signed. Writing the
        predicate over the axes rather than over an angle means a reader never has to
        recover the angle from the image, and it reduces to
        ``c_x + c_y - B max(cos, sin)`` for the concentric net square.
        """

        ax, ay, bx, by = axes
        centre_x, centre_y = centre
        return min(
            sx * centre_x
            + sy * centre_y
            - half * (abs(sx * ax + sy * ay) + abs(sx * bx + sy * by))
            + self._offset(sx, sy)
            for sx, sy in _CORNERS
        )

    def excludes_square(
        self,
        axes: tuple[Fraction, Fraction, Fraction, Fraction],
        centre: tuple[Fraction, Fraction],
        half: Fraction,
    ) -> bool:
        """Whether that closed square meets some corner triangle.

        The same closed ``<=`` test as `excludes`, hence the same open kept set.
        """

        return self.square_penetration(axes, centre, half) <= self.depth

    def thresholds(self, cosine: Fraction, sine: Fraction) -> tuple[Fraction, ...]:
        """``d + reach - offset`` per corner: the kept side's bound in container terms.

        The kept side is the **closed** one, ``>=``, as in `half_planes`.
        """

        reach = self.reach(cosine, sine)
        return tuple(self.depth + reach - self._offset(sx, sy) for sx, sy in _CORNERS)

    def half_planes(self, cosine: Fraction, sine: Fraction) -> tuple[HalfPlane, ...]:
        """The four kept half-planes in the rotated ``(u, v)`` frame.

        With ``u = c x + s y`` and ``v = -s x + c y`` the inverse is ``x = c u - s v``
        and ``y = s u + c v``, so ``sigma_x x + sigma_y y`` is
        ``(sigma_x c + sigma_y s) u + (sigma_y c - sigma_x s) v``. The kept side is
        ``>= d + reach - offset``: the **closed** ``{penetration >= d}``, the class's
        closure rather than the class. Keeping that measure-zero boundary band retains
        rows the class cannot realise, which makes Condition 5 strictly harder and is
        the safe direction for a covering program -- the opposite side from `excludes`,
        deliberately. See "Two boundary conventions, on purpose" in the module
        docstring.
        """

        reach = self.reach(cosine, sine)
        return tuple(
            (
                sx * cosine + sy * sine,
                sy * cosine - sx * sine,
                self.depth + reach - self._offset(sx, sy),
            )
            for sx, sy in _CORNERS
        )

    def clip_polygon(
        self,
        polygon: tuple[tuple[Fraction, Fraction], ...],
        cosine: Fraction,
        sine: Fraction,
    ) -> tuple[tuple[Fraction, Fraction], ...]:
        """Clip a convex rational polygon in ``(u, v)`` by the four half-planes.

        Closed, as `half_planes` is: a vertex exactly on a cut is kept.
        """

        clipped = polygon
        for half_plane in self.half_planes(cosine, sine):
            clipped = _clip_half_plane(clipped, half_plane)
            if not clipped:
                return ()
        return clipped

    def _offset(self, sign_x: int, sign_y: int) -> Fraction:
        """``m * L`` for the corner: the shift that puts that corner at the origin."""

        negatives = (sign_x < 0) + (sign_y < 0)
        return negatives * self.outer_side


def _clip_half_plane(
    polygon: tuple[tuple[Fraction, Fraction], ...], half_plane: HalfPlane
) -> tuple[tuple[Fraction, Fraction], ...]:
    """Sutherland--Hodgman against ``nu * u + nv * v >= offset``, exactly.

    Convexity is what makes one pass enough: the intersection of a convex polygon with a
    half-plane is convex and the walk visits each edge once. Every coordinate stays a
    ``Fraction``, so the clipped polygon's vertices are exact and the event grid built
    from them is the grid the sweep decides on.
    """

    if not polygon:
        return ()
    nu, nv, offset = half_plane
    output: list[tuple[Fraction, Fraction]] = []
    previous = polygon[-1]
    previous_value = nu * previous[0] + nv * previous[1] - offset
    for current in polygon:
        current_value = nu * current[0] + nv * current[1] - offset
        if (current_value >= 0) != (previous_value >= 0):
            factor = previous_value / (previous_value - current_value)
            output.append(
                (
                    previous[0] + factor * (current[0] - previous[0]),
                    previous[1] + factor * (current[1] - previous[1]),
                )
            )
        if current_value >= 0:
            output.append(current)
        previous, previous_value = current, current_value
    return tuple(output)


def clip_from_optional(
    depth: Fraction | None, outer_side: Fraction, square_side: Fraction
) -> CornerClip | None:
    """``None`` in, ``None`` out: the one place a driver turns a flag into a clip."""

    if depth is None:
        return None
    return CornerClip(outer_side, square_side, depth)


__all__ = [
    "CornerClip",
    "EmptyClippedDomainError",
    "HalfPlane",
    "clip_from_optional",
]
