"""G3: the independent reader uses the same K2/K3 inequalities as verify_ceiling.

Equality of total to n, or of max depth to 1, is stronger than weak duality needs.
A slack family with depth below 1 or total above n is still a ceiling.
"""

from __future__ import annotations

from fractions import Fraction

from devtools.independent_ceiling_reader import (
    Record,
    Square,
    check_k2,
    check_k3,
    controls,
    decide,
)

B = Fraction(9, 10)
SIDE = Fraction(2)
NET = [Fraction(0), Fraction(1, 5)]


def _corners(*, n: int, weight: Fraction = Fraction(1)) -> Record:
    low, high = B / 2, SIDE - B / 2
    squares = [Square(Fraction(0), x, y, weight, B) for x in (low, high) for y in (low, high)]
    return Record(n=n, outer_side=SIDE, square_side=B, net=NET, squares=squares)


def test_four_unit_corners_still_prove_the_ceiling_at_four() -> None:
    verdict = decide(_corners(n=4))
    assert verdict["proved"]
    assert verdict["K2"]["holds"]
    assert verdict["K3"]["holds"]
    assert verdict["K2"]["max_depth"] == "1"


def test_total_above_n_is_a_ceiling() -> None:
    verdict = decide(_corners(n=3))
    assert verdict["K3"]["holds"]
    assert verdict["proved"]


def test_total_below_n_is_refused() -> None:
    verdict = decide(_corners(n=5))
    assert not verdict["K3"]["holds"]
    assert not verdict["proved"]


def test_depth_below_one_is_accepted_when_total_meets_n() -> None:
    record = _corners(n=2, weight=Fraction(1, 2))
    k2 = check_k2(record)
    k3 = check_k3(record)
    assert k2["max_depth"] == "1/2"
    assert k2["holds"]
    assert k3["holds"]
    assert decide(record)["proved"]


def test_the_weight_scale_control_fails_depth_not_total() -> None:
    """Scaling 8/7 pushes depth above 1; total 32/7 is still at least n."""

    scaled = next(
        outcome
        for outcome in controls(_corners(n=4))
        if outcome["control"] == "weights scaled by 8/7"
    )
    assert scaled["as_expected"]
    assert scaled["observed_failures"] == ["K2"]
    assert scaled["max_depth"] == "8/7"
