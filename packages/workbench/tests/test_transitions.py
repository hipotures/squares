"""Controls for the transition contract, over fills the page actually drew.

`transition_contract` is pure: it takes what `probes/transitions/sweep.js` sampled and returns
findings. So each rule is tested here on a recorded shape -- the fills are the ones
`check_transitions --trace` read off the page, the faulty ones before their fix and the clean
ones after -- with no browser. What these cannot establish is that the probe reads the page
correctly; `unsampled` is the rule that fails a sweep which read nothing, and `check_frontend`
runs the whole contract against the built page on every pull request.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pytest

from workbench_tools import transition_contract as contract
from workbench_tools.check_transitions import FPS, MIN_RED_FRAMES, judge

SCARLET = "#893d4a"

#: Square 5 on the step into 11, after the fix: yellow drains to grey, the grey moves to the new
#: shade, and pink comes up out of it.
YELLOW_TO_GREY = ("#d3d36c", "#d2d27e", "#d0d197", "#cecfb0", "#cdcdc3", "#cccccb", "#cccccc")
GREY_DOWN = ("#c2c2c2", "#b7b7b7", "#afafaf", "#a7a7a7")
GREY_TO_PINK = (
    "#aca5a9",
    "#b3a2ab",
    "#b89fac",
    "#bd9dad",
    "#c29aaf",
    "#c697b0",
    "#ca95b1",
    "#ce92b3",
    "#d190b3",
    "#d38fb4",
    "#d58eb5",
    "#d68db5",
)


def _frames(
    *squares: tuple[int, Sequence[str | None]], opacity: float = 1.0
) -> list[dict[str, Any]]:
    """Frames at the capture rate holding each square's fills, one per frame; None is absent."""
    length = max(len(fills) for _, fills in squares)
    return [
        {
            "t": index / FPS,
            "squares": [
                [identity, fills[index], opacity]
                for identity, fills in squares
                if index < len(fills) and fills[index] is not None
            ],
        }
        for index in range(length)
    ]


# ---------------------------------------------------------------------------------- the color


def test_the_conversion_reads_the_owners_scarlet_and_a_neutral_grey() -> None:
    lightness, chroma, hue = contract.oklch(SCARLET)
    assert abs(hue - contract.SCARLET_HUE) < 1
    assert chroma > contract.SCARLET_CHROMA
    assert 0.4 < lightness < 0.5
    assert contract.oklch("#636363")[1] < 1e-3
    with pytest.raises(ValueError, match="six-digit"):
        contract.oklch("#abc")


def test_a_color_that_drains_to_grey_and_returns_in_its_new_hue_breaks_no_rule() -> None:
    frames = _frames((5, (*YELLOW_TO_GREY, *GREY_DOWN, *GREY_TO_PINK)))
    assert contract.third_hues(11, frames) == []
    assert contract.hue_turns(11, frames) == []
    assert contract.lightness_jumps(11, frames, arriving=11) == []
    assert contract.chroma_bumps(11, frames) == []


def test_the_old_hue_coming_back_before_the_new_one_is_a_turn_not_a_third_hue() -> None:
    # The fault the owner saw: out of the grey came yellow again, then pink. Both are ends of
    # the blend, so `third_hues` has nothing to say; the turn from one to the other without
    # passing through grey is what `hue_turns` exists to catch.
    frames = _frames(
        (5, (*YELLOW_TO_GREY, "#cdcdc3", "#cecfb0", "#d0d197", "#ce92b3", "#d68db5"))
    )
    assert contract.third_hues(11, frames) == []
    [finding] = contract.hue_turns(11, frames)
    assert finding.rule == "hue turns outside grey"
    assert finding.frame == len(YELLOW_TO_GREY) + 3


def test_a_blend_that_sweeps_through_a_hue_neither_end_has_is_a_third_hue() -> None:
    # Green to scarlet the short way round the wheel passes yellow.
    frames = _frames((3, ("#347060", "#d3d36c", SCARLET)))
    [finding] = contract.third_hues(9, frames)
    assert finding.frame == 1


def test_chroma_rising_on_the_way_into_a_crossing_is_a_bump() -> None:
    frames = _frames((5, ("#d3d36c", "#d0d197", "#d2d27e", "#cccccc", "#d3d36c")))
    [finding] = contract.chroma_bumps(11, frames)
    assert "on the way into" in finding.detail


# ------------------------------------------------------------------------------ the lightness

#: A grey that climbs slowly and then drops a shade in one frame, as square 5 did into 11.
SNAP = ("#c8c8c8", "#cacaca", "#cccccc", "#a7a7a7", "#a7a7a7")


def test_a_grey_that_drops_a_shade_in_one_frame_is_a_lightness_jump() -> None:
    [finding] = contract.lightness_jumps(11, _frames((5, SNAP)), arriving=11)
    assert finding.rule == "lightness jump"
    assert finding.frame == 3


def test_the_arriving_square_may_change_lightness_as_it_fades_in() -> None:
    assert contract.lightness_jumps(11, _frames((11, SNAP)), arriving=11) == []


def test_a_join_between_moving_runs_is_exempt_only_inside_the_merge_window() -> None:
    frames = _frames((5, SNAP))
    assert contract.lightness_jumps(11, frames, 11, merging=(0.0, 0.1)) == []
    # The last checkpoint sits on the window's end and shows on the first frame after it: the
    # interval from frame 2 (t 0.033) to frame 3 (t 0.050) holds an end at 0.04.
    assert contract.lightness_jumps(11, frames, 11, merging=(0.0, 0.04)) == []
    assert len(contract.lightness_jumps(11, frames, 11, merging=(0.0, 0.03))) == 1


def test_the_merge_window_is_the_one_the_page_folds_runs_in() -> None:
    # Into 51: moveStart 0.600, end 3.028, under the default fade.
    start, end = contract.merge_window(
        {"moveStart": 0.6, "end": 3.028},
        {"out": 0.45, "in": 0.3, "hueOut": 0.35, "hueIn": 0.35},
    )
    assert start == pytest.approx(1.05)
    assert end == pytest.approx(2.378)


# ----------------------------------------------------------------------------------- the view


def test_a_view_that_turns_back_within_a_step_is_a_reversal() -> None:
    # Into 10, frame 37, before the physics view was anchored to the room.
    [finding] = contract.view_jerks(10, [4.50, 4.578, 4.482])
    assert finding.rule == "view reversal"
    assert contract.view_jerks(10, [4.36, 4.37, 4.38, 4.38]) == []


def test_a_view_that_moves_too_far_in_one_frame_or_between_steps_is_a_jump() -> None:
    [finding] = contract.view_jerks(10, [3.27, 3.27 + 2 * contract.VIEW_STEP_LIMIT])
    assert finding.rule == "view jump"
    # Into 10, when the physics view took n + 1's side from its first frame.
    [boundary] = contract.boundary_jerk(10, 3.270, 3.796)
    assert boundary.rule == "view jump across the boundary"
    assert contract.boundary_jerk(10, 3.270, 3.300) == []


def test_the_box_may_grow_only_on_the_first_frame_after_the_move_starts() -> None:
    times = [0.0, 0.1, 0.2, 0.3]
    assert contract.box_growth(9, [3.0, 3.0, 4.0, 3.9], times, move_start=0.1) == []
    # At `move_start` itself the step is still in its dwell.
    [early] = contract.box_growth(9, [3.0, 4.0, 4.0, 4.0], times, move_start=0.1)
    assert early.frame == 1
    [late] = contract.box_growth(9, [3.0, 3.0, 4.0, 4.1], times, move_start=0.1)
    assert late.frame == 3


# ------------------------------------------------------------------------- the arriving square


def test_only_opaque_saturated_scarlet_counts_as_red() -> None:
    frames = [
        *_frames((9, (SCARLET,)), opacity=0.5),
        *_frames((9, (SCARLET, SCARLET, SCARLET, "#437f6f", "#437f6f"))),
    ]
    assert contract.red_frames(frames, arriving=9) == 3


def test_a_still_pair_may_shade_a_neighbor_but_not_turn_its_hue() -> None:
    # The neighbor of the square arriving into 8 takes a darker shade of the same green.
    darker = _frames((5, ("#7ebba9", "#7ebba9", "#437f6f")))
    assert contract.still_recolors(8, darker, arriving=8) == []
    # The olive the whole grid flashed over n = 96..102.
    olive = _frames((5, ("#437f6f", "#a3a580", "#437f6f")))
    [finding] = contract.still_recolors(97, olive, arriving=97)
    assert finding.rule == "still pair recolors"


def test_a_step_with_no_opaque_square_checked_nothing_and_fails() -> None:
    assert len(contract.unsampled(11, _frames((5, YELLOW_TO_GREY), opacity=0.0))) == 1
    assert contract.unsampled(11, _frames((5, YELLOW_TO_GREY))) == []


# ---------------------------------------------------------------------------------- the judge


def _sweep(n: int, frames: list[dict[str, Any]]) -> dict[str, Any]:
    for frame in frames:
        frame.setdefault("view", 4.36)
        frame.setdefault("box", 4.0)
    return {
        "n": n,
        "moveStart": 0.0,
        "schedule": {"moveStart": 0.0, "end": frames[-1]["t"]},
        "fade": {"out": 0.45, "in": 0.3, "hueOut": 0.35, "hueIn": 0.35},
        "frames": frames,
    }


def test_the_judge_reports_an_arriving_square_that_is_never_red() -> None:
    frames = _frames((5, ("#347060",) * 4), (9, (None, "#437f6f", "#437f6f", "#437f6f")))
    findings, red = judge(_sweep(9, frames), still=True)
    assert red == 0
    assert [f.rule for f in findings] == ["arriving square not red"]
    assert red < MIN_RED_FRAMES


def test_the_judge_passes_a_step_whose_new_square_arrives_red() -> None:
    # Scarlet, then through grey to its own green: the crossing the contract asks for.
    arriving = (None, SCARLET, SCARLET, SCARLET, "#636363", "#437f6f")
    frames = _frames((5, ("#347060",) * 6), (9, arriving))
    findings, red = judge(_sweep(9, frames), still=True)
    assert red == 3
    assert findings == []


def test_a_summary_counts_findings_by_rule() -> None:
    frames = _frames((5, SNAP), (6, SNAP))
    assert contract.summarize(contract.lightness_jumps(11, frames, 11)) == {"lightness jump": 2}
