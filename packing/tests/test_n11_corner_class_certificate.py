"""The T-031 case certificate is the retained exp-220 covering, byte for byte.

A live `certificate.json` under `cases/` is what `check_rung_figures` recomputes a
result's figures from, so the copy must never drift from the campaign record it stands
for, and it must keep declaring the class it was decided under.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

PACKING = Path(__file__).resolve().parents[1]
CASE = PACKING / "cases" / "n11_corner_class_certificate" / "certificate.json"
RETAINED = (
    PACKING
    / "campaign"
    / "series"
    / "series-000-smoke-and-calibration"
    / "results"
    / "agenda-040"
    / "exp-220-n11-96-25-class-covering.json"
)
DIGEST = "876820dde8d55c727dec73c85f245db27661556bb3c7aa06ffb15b01ec97a461"


def test_case_certificate_is_the_retained_exp_220_bytes() -> None:
    case_bytes = CASE.read_bytes()
    assert case_bytes == RETAINED.read_bytes()
    assert hashlib.sha256(case_bytes).hexdigest() == DIGEST


def test_case_certificate_declares_the_corner_class_and_its_mass() -> None:
    record = json.loads(CASE.read_text(encoding="utf-8"))
    assert record["variant"] == "class"
    assert Fraction(record["corner_clip"]) == Fraction(1, 2)
    assert record["claim"] == "corner class d = 1/2 excluded at s(11) >= 96/25"
    assert record["id"] == "C-n011-fractional-96-25-clip-1-2"
    assert record["n"] == 11
    assert Fraction(str(record["outer_side"])) == Fraction(96, 25)
    total = sum(Fraction(str(atom[2])) for atom in record["atoms"])
    assert total == Fraction(10868617, 1000000)
    assert len(record["atoms"]) == 680
