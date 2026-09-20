"""The Bentz 2016 replay and the one-spare inventory (`H-226`, `H-227`).

`devtools/bentz2016/` replays every quantitative step of Bentz 2016 Theorem 11 at the
printed constants and enumerates the one-spare structures the theorem's argument would
have to handle at `n = 21` and `n = 32`. What is pinned here is the arithmetic those
records rest on, not their mathematical verdict:

* the 24-row replay, which must hold at the printed constants and must fail at the
  constant the transcription carried before `D-505` -- rows 11 and 15 are the two the
  finishing line moves first, and a table that passed either way would be decoration;
* the `n = 22` control, where Theorem 11 *is* a theorem, so all 73 blue structures must
  come out forced, and none of them by the finish this port derives rather than reads
  off the paper;
* one red structure of the `n = 21` inventory against all 2,365 blue structures, whose
  three class counts before the merge propagation are the scratch record's, not this
  port's, and the whole inventory in orbits on both sides of that propagation;
* the `n = 33` zero-spare control of the side-6 model, which must be forced by six
  distinct full boxes on both wall lines.

Three tests are marked slow: each replay is a whole run of the table, whose
unavoidability screen -- 619 exact tilings of `[0, 5]^2` over the moves the proof uses
-- is 14s of its 15s, and the whole `n = 21` inventory is 39s of classifying 167,915
pairs. The four tests that are not marked cost about a second and a half between them,
and they are the ones that would catch a broken port.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from devtools.bentz2016 import m6_model, one_spare_inventory, regions, replay_theorem11

#: One red structure of the `n = 21` inventory: the end point of red row 2 uncovered.
SLICE_RED = "U[(1/2,17/10)] G[]"
#: Its class counts over all 2,365 blue structures before the merge propagation, from
#: the Session 144 lane's `inventory_n21.json`: every orbit record expanded over its
#: `D2` images gives the class of each of the 167,915 raw pairs, and these are the
#: 2,365 with this red.
SLICE_COUNTS_BEFORE = {"forced": 240, "needs-geometry": 1516, "kill": 609}
#: The same slice with the propagation the review of the model added.
SLICE_COUNTS = {"forced": 405, "needs-geometry": 1381, "kill": 579}
#: The whole `n = 21` inventory in orbits, before and after the propagation.
N21_ORBITS_BEFORE = {"forced": 11483, "needs-geometry": 26908, "kill": 3733}
N21_ORBITS = {"forced": 16060, "needs-geometry": 22603, "kill": 3461}
#: The exact sups of the finish, per height, to six places (`regions.finish_table`).
FINISH_SUPS = ("0.497328", "0.450976", "0.381333", "0.450976", "0.497328")


def _finish_ok() -> dict[int, bool]:
    """The finish table as the inventory reads it, without the tool's printing."""
    table = regions.finish_table()
    ok: dict[int, bool] = {}
    for i in range(5):
        result = table[i + 1][one_spare_inventory.FINISH[i][0]]
        ok[i] = result is not None and result.forced
    return ok


def test_the_finish_closes_at_every_height_including_the_derived_red_rows() -> None:
    table = regions.finish_table()
    for i, expected in enumerate(FINISH_SUPS, start=1):
        result = table[i][one_spare_inventory.FINISH[i - 1][0]]
        assert result is not None
        assert f"{float(result.sup_num):.6f}" == expected
        assert result.forced is True
    assert [one_spare_inventory.FINISH[i][1] for i in range(5)] == [
        "finish-paper",
        "finish-derived",
        "finish-paper",
        "finish-derived",
        "finish-paper",
    ]


def test_the_n22_control_forces_every_structure_by_the_paper_s_own_finish() -> None:
    status, inventory = one_spare_inventory.self_test(_finish_ok(), None)
    assert status == 0
    assert inventory["counts"] == {
        "red_structures": 1,
        "blue_structures": 73,
        "raw_pairs": 73,
        "orbits": 22,
    }
    assert inventory["classes_raw"] == {"forced": 73}
    assert inventory["classes_orbits"] == {"forced": 22}
    assert inventory["reasons_raw"] == {
        "forced: Theorem 8 (trajectory through an uncovered point)": 4,
        "forced: five full boxes on one line": 10,
        "forced: four full + partial, paper finish (blue height 1/3/5)": 59,
    }
    assert inventory["invariance_ok"] is True


def test_one_red_structure_of_the_n21_inventory_matches_the_scratch_record() -> None:
    finish_ok = _finish_ok()
    reds = [
        one_spare_inventory.structure_facts("red", st)
        for st in one_spare_inventory.structures(one_spare_inventory.RED, 1)
    ]
    blues = [
        one_spare_inventory.structure_facts("blue", st)
        for st in one_spare_inventory.structures(one_spare_inventory.BLUE, 2)
    ]
    assert len(reds) == 71
    assert len(blues) == 2365
    red = next(fact for fact in reds if fact.label == SLICE_RED)
    verdicts = [one_spare_inventory.classify(red, blue, finish_ok) for blue in blues]
    assert dict(Counter(v.before for v in verdicts)) == SLICE_COUNTS_BEFORE
    assert dict(Counter(v.klass for v in verdicts)) == SLICE_COUNTS
    assert len(verdicts) == len(blues)


@pytest.mark.slow
def test_the_whole_n21_inventory_reports_both_sides_of_the_propagation() -> None:
    inventory = one_spare_inventory.run(1, 2, _finish_ok(), None, "n=21 test")
    assert inventory["counts"] == {
        "red_structures": 71,
        "blue_structures": 2365,
        "raw_pairs": 167915,
        "orbits": 42124,
    }
    assert inventory["classes_orbits_before_propagation"] == N21_ORBITS_BEFORE
    assert inventory["classes_orbits"] == N21_ORBITS
    assert inventory["orbits_converted_by_propagation"] == {
        "kill": 272,
        "needs-geometry": 4305,
    }
    assert inventory["classes_raw_before_propagation"] == {
        "forced": 45592,
        "needs-geometry": 107479,
        "kill": 14844,
    }
    assert inventory["classes_raw"] == {
        "forced": 63842,
        "needs-geometry": 90309,
        "kill": 13764,
    }
    assert inventory["invariance_ok"] is True


def test_the_n33_zero_spare_control_is_forced_by_six_distinct_full_boxes() -> None:
    verdict = m6_model.zero_spare_control()
    assert verdict.klass == "forced"
    assert "six distinct full boxes" in verdict.reason
    for side in m6_model.SIDES:
        assert verdict.lines[side].max_distinct_full == 6
        assert verdict.lines[side].full_rows == [
            ("blue", 1),
            ("blue", 3),
            ("blue", 5),
            ("red", 2),
            ("red", 4),
            ("red", 6),
        ]


@pytest.mark.slow
def test_the_replay_table_holds_at_the_printed_constants(tmp_path: Path) -> None:
    out = tmp_path / "replay.json"
    assert replay_theorem11.main(["--json", str(out)]) == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["line_x"] == "-1/2 + sqrt(2)"
    assert payload["negative_control"] is False
    assert payload["rows_total"] == 24
    assert payload["rows_failed"] == []
    assert payload["all_hold"] is True
    rows = {row["number"]: row for row in payload["rows"]}
    assert all(row["holds"] for row in rows.values())
    assert rows[11]["exact"] == "1"
    assert rows[15]["exact"] == "1"
    assert rows[16]["exact"] == "-2 + 2*sqrt(2)"
    assert rows[21]["decimal"] == "0.381333"
    assert rows[23]["decimal"] == "0.497328"
    assert rows[24]["decimal"] == "0.484441"


@pytest.mark.slow
def test_the_replay_fails_at_the_line_the_transcription_printed_before_d505(
    tmp_path: Path,
) -> None:
    out = tmp_path / "negative-control.json"
    assert replay_theorem11.main(["--negative-control", "--json", str(out)]) == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["line_x"] == "-1/2 + sqrt(2)/2"
    assert payload["negative_control"] is True
    assert payload["all_hold"] is False
    rows = {row["number"]: row for row in payload["rows"]}
    assert rows[11]["holds"] is False
    assert rows[15]["holds"] is False
    assert rows[1]["holds"] is True
    assert rows[2]["holds"] is True
