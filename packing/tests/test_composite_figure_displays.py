"""A displayed bound must stay true as written, in both directions.

The figure prints six decimals of numbers it stores to twelve or more, so every display
is a rounding, and the direction is the whole question. A lower bound rounded up and an
upper bound rounded down each print a claim the record does not support.

The lower bound's rule was reasoned out when the figure was built (`_lower_text`); the
upper bound's was not, and rounded to nearest. Measured over the corpus on 2026-09-22,
51 of the 265 open cases printed an upper bound below the bound they stand for: at
n = 29 the certified `5.93383346...` printed as `s(29) <= 5.933833`, a stronger bound
than anything on record (`think-1z70`). Nothing read the displays, so nothing said so.

These tests read them: the two helpers on their own, and every display in the retained
record against the value it was made from.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from devtools.build_composite_figure_data import _lower_text, _side_text, _upper_text

FIGURE = Path(__file__).resolve().parents[1] / "atlas/known-best/composite-figure.json"

#: What six decimals can be away from the value they display, at most.
STEP = Decimal("0.000001")


def _entries() -> list[dict[str, Any]]:
    document: dict[str, Any] = json.loads(FIGURE.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = document["figure"]["entries"]
    assert len(entries) == 324, f"{FIGURE} carries {len(entries)} entries, not the corpus"
    return entries


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        # 1 + sqrt(17) = 5.123105625617661..., which rounds up to 5.123106: above the bound.
        ("5.12310562562", "5.123105"),
        ("5.9338334626769", "5.933833"),
        ("3.877083", "3.877083"),
    ],
)
def test_a_lower_bound_is_cut_off_and_never_printed_above_itself(
    value: str, shown: str
) -> None:
    assert _lower_text(value) == shown
    assert Decimal(_lower_text(value)) <= Decimal(value)


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        # The n = 29 certificate: to nearest this printed 5.933833, under the bound.
        ("5.9338334626769", "5.933834"),
        ("4.675530094", "4.675531"),
        ("3.877083", "3.877083"),
    ],
)
def test_an_upper_bound_is_rounded_away_and_never_printed_below_itself(
    value: str, shown: str
) -> None:
    assert _upper_text(value) == shown
    assert Decimal(_upper_text(value)) >= Decimal(value)


def test_an_equality_keeps_the_nearest_six_decimals() -> None:
    # An equality claims neither direction, so it is the closest six decimals to the value.
    assert _side_text("3.8284271247") == "3.828427"
    assert abs(Decimal(_side_text("5.9338334626769")) - Decimal("5.9338334626769")) <= STEP


def test_every_displayed_bound_in_the_record_stays_true_as_written() -> None:
    wrong: list[str] = []
    for packing in _entries():
        n = packing["n"]
        side = packing["side"]
        value = Decimal(str(side["value"]))
        shown = Decimal(str(side["display"]).split()[-1])
        if side["relation"] == "equality":
            if abs(shown - value) > STEP:
                wrong.append(f"n = {n}: equality shows {shown} for {value}")
        elif shown < value:
            wrong.append(f"n = {n}: upper bound shows {shown}, below the stored {value}")
        lower = packing["lower"]
        floor = Decimal(str(lower["value"]))
        printed = Decimal(str(lower["display"]).split()[-1])
        if printed > floor:
            wrong.append(f"n = {n}: lower bound shows {printed}, above the stored {floor}")
    assert wrong == [], wrong
