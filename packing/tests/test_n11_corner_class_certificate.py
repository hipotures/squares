"""The T-031 case certificate is the retained exp-220 covering, byte for byte.

A live `certificate.json` under `cases/` is what `check_rung_figures` recomputes a
result's figures from, so the copy must never drift from the campaign record it stands
for, and it must keep declaring the class it was decided under.

Two tests replay the retention gate itself on that copy, which is what makes the two
evidence atoms' `replay_status: passed` a measurement rather than an assertion: one
decides the file under `--corner-clip 1/2` and reads the headline, the least charge and
the digest off the gate's own output, the other watches it refuse the same bytes without
the flag. Only the deciding one is marked slow -- both gate routes over these 680 atoms
are 33s, and its measurement is argued in `tests/test_module_boundaries.py`, where every
slow marker states its cost. The refusal never reaches either route, costs nothing, and
stays on the pull-request surface, which is where a gate that stopped refusing should be
caught.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from devtools import decide_certificate

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
#: The least charge both gate routes report on these bytes, which T-031 quotes.
LEAST_CELL_MASS = Fraction(2000013, 2000000)


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


@pytest.mark.slow
def test_the_gate_decides_the_case_certificate_under_the_corner_clip(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The gate's own decision, replayed on the case file (the T-022 pattern).

    The byte pin above catches drift of the artifact. This catches drift of the
    instrument: change `CornerClip.half_planes` or the sweep's Condition-5 decision and
    the two evidence atoms' `replay_status: passed` stops being true, which is what
    `V4` rests on. Both gate routes run here, because the gate refuses the file unless
    the exact sweep and the interval branch and bound both accept and agree.
    """

    assert decide_certificate.main(["--corner-clip", "1/2", str(CASE)]) == 0
    printed = capsys.readouterr().out
    assert "corner clip d = 1/2" in printed
    assert (
        "RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS "
        "(no square meets x + y <= 1/2 in any corner frame)"
    ) in printed
    assert f"agree at {LEAST_CELL_MASS}" in printed
    assert f"sha256 {DIGEST}" in printed


def test_the_gate_refuses_the_case_certificate_without_the_flag(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Without `--corner-clip` the bytes cannot be read as a bound on s(11)."""

    assert decide_certificate.main([str(CASE)]) == 1
    printed = capsys.readouterr().out
    assert "REFUSED" in printed
    assert "variant 'class' is declared" in printed
    assert "pass --corner-clip d" in printed
