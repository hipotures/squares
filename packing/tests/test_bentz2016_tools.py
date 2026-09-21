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
  distinct full boxes on both wall lines, and the distinctness predicate itself, which
  must decide on witness *identity* rather than on colour labels;
* the whole `n = 32` inventory, whose four counts are what exp-217's verdict is built
  on and what the second review found nothing pinning;
* the merge propagation on its own, with the wall-line pass deferred, because at
  `n = 22` the wall lines force every pair first and the propagation -- which is what
  moved exp-216's forced orbits from 11,483 to 16,060 -- never runs there otherwise;
* the two float or guarded margins the stack decides on, measured rather than asserted:
  the sampled orientation slack of the side-5 merge and the `EPS` guard of the side-6
  model.

Four tests are marked slow: each replay is a whole run of the table, whose
unavoidability screen -- 619 exact tilings of `[0, 5]^2` over the moves the proof uses
-- is 14s of its 15s, the whole `n = 21` inventory is 39s of classifying 167,915 pairs,
and the `n = 32` inventory is 23s of classifying 12,100 pairs at 50 digits. The tests
that are not marked cost about two seconds between them, and they are the ones that
would catch a broken port.
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
#: The `n = 32` inventory exp-217 scores on, re-derived after the second review found
#: the side-6 distinctness predicate unsound (it decided on colour labels rather than
#: on witness identity). The counts did not move under the fix.
N32_COUNTS = {"red_structures": 110, "blue_structures": 110, "raw_pairs": 12100, "orbits": 4146}
N32_CLASSES_RAW = {"kill": 11699, "forced": 401}
N32_CLASSES_ORBITS = {"kill": 3997, "forced": 149}
N32_ORBITS_ON_INTEGER_KEYS = 3089
#: The forced breakdown; the kill reasons key off a truncated row list, so they are
#: pinned by their total instead, and `needs-geometry` must stay absent.
N32_REASONS_RAW = {"forced: Theorem 8": 352, "forced: six distinct full": 49}
#: How far above the sampled-orientation slack the closest side-5 decision ran, and how
#: far above the side-6 `EPS` guard the closest deciding comparison ran. Both are
#: measured on the run: `0.0332 / 0.004 = 8.3` and `0.066 / 1e-30 = 6.6e28`.
ORIENTATION_MARGIN_FACTOR = 8
GUARD_MARGIN_FLOOR = 1e-2
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


#: What the merge propagation refuses at `n = 22` once the wall-line pass is deferred,
#: as `blue structure -> reason`. Both are hand-checkable against Theorem 8: an
#: uncovered blue point swept by a merged box is a box holding a point the theorem
#: denies it, and a double in a blue row freezes that row, after which the red end
#: point and its neighbour are swept into one box, which a singly covered point
#: forbids.
N22_MERGE_REFUSALS = {
    "U[(1,17/10)] G[]": "merged box sweeps the uncovered blue point (1,17/10)",
    "U[(4,17/10)] G[]": "merged box sweeps the uncovered blue point (4,17/10)",
    "U[(1,33/10)] G[]": "merged box sweeps the uncovered blue point (1,33/10)",
    "U[(4,33/10)] G[]": "merged box sweeps the uncovered blue point (4,33/10)",
    "U[] G[{(1,17/10),(2,17/10)}]": (
        "merged box holds the singly covered red point (1/2,17/10) with (3/2,17/10)"
    ),
    "U[] G[{(3,17/10),(4,17/10)}]": (
        "merged box holds the singly covered red point (7/2,17/10) with (9/2,17/10)"
    ),
    "U[] G[{(1,33/10),(2,33/10)}]": (
        "merged box holds the singly covered red point (1/2,33/10) with (3/2,33/10)"
    ),
    "U[] G[{(3,33/10),(4,33/10)}]": (
        "merged box holds the singly covered red point (7/2,33/10) with (9/2,33/10)"
    ),
}


def test_the_merge_propagation_decides_the_n22_control_with_the_wall_lines_deferred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Put the propagation on a case whose answer is a theorem, and pin what it says.

    At `n = 22` the wall-line pass forces every pair first, so in the control the
    propagation never runs and only its `n = 21` output is pinned -- although it is
    what moved exp-216 from 11,483 forced orbits to 16,060. Deferring the wall lines
    (their verdict is computed as usual and then reported as undecided) leaves the
    propagation as the only thing that can force. Theorem 11 says no 22 boxes of side
    above 1 fit in `[0, 5]^2`, so every refusal it makes here is correct and the
    interesting signal would be a refusal it cannot make; it refuses 8 of the 73, by
    two of its three mechanisms, and each refusal is checked against its reason below.
    """
    refused = {
        blue.label: one_spare_inventory.merge_propagation(red, blue)
        for red in [
            one_spare_inventory.structure_facts("red", st)
            for st in one_spare_inventory.structures(one_spare_inventory.RED, 0)
        ]
        for blue in [
            one_spare_inventory.structure_facts("blue", st)
            for st in one_spare_inventory.structures(one_spare_inventory.BLUE, 1)
        ]
    }
    assert {label: why for label, why in refused.items() if why} == N22_MERGE_REFUSALS

    wall_lines = one_spare_inventory.classify_by_wall_lines

    def deferred(
        red: one_spare_inventory.StructureFacts,
        blue: one_spare_inventory.StructureFacts,
        finish_ok: dict[int, bool],
    ) -> one_spare_inventory.Verdict:
        verdict = wall_lines(red, blue, finish_ok)
        return one_spare_inventory.Verdict(
            verdict.lines, "needs-geometry", "wall lines deferred: the propagation decides"
        )

    monkeypatch.setattr(one_spare_inventory, "classify_by_wall_lines", deferred)
    inventory = one_spare_inventory.run(
        0, 1, _finish_ok(), None, "n=22 with the wall lines deferred"
    )
    assert inventory["classes_raw_before_propagation"] == {"needs-geometry": 73}
    assert inventory["classes_raw"] == {"forced": 8, "needs-geometry": 65}
    assert inventory["orbits_converted_by_propagation"] == {"needs-geometry": 2}
    assert inventory["reasons_raw"] == {
        "forced: Theorem 8 propagated through merged boxes": 8,
        "needs-geometry: the propagation decides": 65,
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
    margins = inventory["orientation_margins"]
    assert isinstance(margins, dict)
    # The one float decision in the side-5 stack, measured rather than asserted. The
    # sampled minimum is an upper bound, so an overshoot past the slack would refuse a
    # box that fits, and a refusal is a forcing. Nothing came near: the closest of the
    # 144 sampled decisions sits 8.3 slacks from the threshold, and not one of them
    # refused, so every "does not fit a square of side 1.01" refusal in the run came
    # from the exact rational diameter test instead.
    assert margins["sampled_decisions"] == 144
    assert margins["refusals"] == 0
    min_abs_margin = margins["min_abs_margin"]
    assert isinstance(min_abs_margin, float)
    assert min_abs_margin > ORIENTATION_MARGIN_FACTOR * one_spare_inventory.ORIENTATION_SLACK


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


def test_side6_distinctness_needs_two_witnesses_not_two_colour_labels() -> None:
    """Carrying each other's end point is not distinctness, and once was read as it.

    Two counted boxes that know each other's end point and nothing else share both
    colour labels, which the predicate this replaced read as a proof that they are
    different boxes. They are not: one box holding one red point and one blue point
    explains both, and no contradiction follows. Distinctness needs two *different*
    points of one colour between them.
    """
    red_end = m6_model.point_key((m6_model.mpf(1), m6_model.mpf(1)))
    blue_end = m6_model.point_key((m6_model.mpf(1), m6_model.mpf(2)))
    span = (m6_model.mpf(0), m6_model.mpf(1))
    a = m6_model.CountedBox(
        "red", 0, "full", frozenset({("red", red_end), ("blue", blue_end)}), span
    )
    b = m6_model.CountedBox(
        "blue", 0, "full", frozenset({("blue", blue_end), ("red", red_end)}), span
    )
    assert {c for c, _ in a.known} & {c for c, _ in b.known} == {"red", "blue"}
    assert m6_model.boxes_are_distinct(a, b) is False
    other_red = m6_model.point_key((m6_model.mpf(2), m6_model.mpf(1)))
    c = m6_model.CountedBox(
        "blue", 1, "full", frozenset({("blue", blue_end), ("red", other_red)}), span
    )
    assert m6_model.boxes_are_distinct(a, c) is True


@pytest.mark.slow
def test_the_n32_inventory_reports_the_counts_exp217_scores_on() -> None:
    """Every number exp-217's verdict is built on, and the margins it decides through."""
    inventory = m6_model.run()
    assert inventory["counts"] == N32_COUNTS
    assert inventory["classes_raw"] == N32_CLASSES_RAW
    assert inventory["classes_orbits"] == N32_CLASSES_ORBITS
    assert inventory["orbits_on_exact_integer_keys"] == N32_ORBITS_ON_INTEGER_KEYS
    reasons = inventory["reasons_raw"]
    assert isinstance(reasons, dict)
    assert {key: n for key, n in reasons.items() if key.startswith("forced")} == N32_REASONS_RAW
    assert (
        sum(n for key, n in reasons.items() if key.startswith("kill"))
        == N32_CLASSES_RAW["kill"]
    )
    assert [key for key in reasons if key.startswith("needs-geometry")] == []
    assert inventory["invariance_ok"] is True
    control = inventory["zero_spare_n33_control"]
    assert isinstance(control, dict)
    assert control["class"] == "forced"
    margins = inventory["guard_margins"]
    assert isinstance(margins, dict)
    # The `EPS` guard measured rather than asserted. Every comparison the guard could
    # have flipped stands at least `GUARD_MARGIN_FLOOR` from its threshold, which is 28
    # orders of magnitude above the guard; the rest are exact ties, which the guard
    # decides the same way with or without it.
    deciding = margins["closest_deciding"]
    assert isinstance(deciding, dict)
    assert set(deciding) == {"close-pair", "meets-x", "meets-y", "reach"}
    assert all(float(value) > GUARD_MARGIN_FLOOR for value in deciding.values())


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
