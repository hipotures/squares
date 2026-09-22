"""Controls for the cadence check: a stutter is a repeat inside motion, not a still stretch.

`cadence` measures a delivered video, then judges the measurements with pure functions, so the
rules are tested here on moved-pixel series shaped like the capture's own: a step that dwells,
moves and settles, at 60 fps. The decoder and ffprobe are not mocked; the capture's own videos
are what they are run on.
"""

from __future__ import annotations

import numpy as np

from workbench_tools import cadence
from workbench_tools.cadence import MOTION, MOVED_EDGE, REPEAT

FPS = 60.0
#: A step's moved pixels frame to frame: a dwell that holds, a move, and a settle that holds.
DWELL = [0.0] * 30
MOVE = [800.0, 1100.0, 1300.0, 1200.0, 1000.0, 900.0, 700.0, 500.0]
STEP = [*DWELL, *MOVE, *DWELL]


def test_a_step_that_holds_moves_and_holds_again_has_no_stutter() -> None:
    assert cadence.stutters(STEP) == []


def test_a_frame_repeated_in_the_middle_of_motion_is_a_stutter() -> None:
    # The screenshot beat the paint: the motion stops for one frame and catches up.
    stuttered = [*DWELL, 800.0, 1100.0, 0.0, 2500.0, 1000.0, 900.0, *DWELL]
    [at] = cadence.stutters(stuttered)
    assert at == len(DWELL) + 3


def test_a_repeat_where_motion_begins_or_ends_is_the_picture_holding() -> None:
    edges = [*DWELL, 900.0, 1000.0, *DWELL, 1000.0, 800.0]
    assert cadence.stutters(edges) == []


def test_a_near_repeat_counts_and_motion_too_small_to_see_does_not() -> None:
    near = [*DWELL, 800.0, REPEAT / 2, 900.0, *DWELL]
    assert len(cadence.stutters(near)) == 1
    faint = [*DWELL, MOTION / 2, 0.0, MOTION / 2, *DWELL]
    assert cadence.stutters(faint) == []


def test_a_one_level_color_step_moves_no_pixel_and_an_edge_does() -> None:
    # The fault the mean change could not tell apart: a slow fade steps every fill one level.
    before = np.full((270, 480), 120, dtype=np.uint8)
    faded = before + 1
    assert cadence.moved_pixels(before, faded) == 0
    moved = before.copy()
    moved[100:140, 200:202] = 20  # a black border one pixel further on
    assert cadence.moved_pixels(before, moved) == 80
    assert int(np.int16(120) - np.int16(20)) > MOVED_EDGE


def test_an_even_clock_has_no_error_and_one_long_gap_is_measured() -> None:
    even = [k / FPS for k in range(600)]
    assert cadence.worst_gap_error(even, FPS) < 1e-12
    held = [*even[:300], *(t + 1 / FPS for t in even[300:])]
    assert abs(cadence.worst_gap_error(held, FPS) - 1 / FPS) < 1e-9


def test_a_smooth_cadence_needs_both_no_stutter_and_an_even_clock() -> None:
    even = [k / FPS for k in range(len(STEP) + 1)]
    assert cadence.judge(STEP, even, FPS).smooth()
    uneven = [*even[:10], *(t + 0.002 for t in even[10:])]
    assert not cadence.judge(STEP, uneven, FPS).smooth()
    stuttered = [*DWELL, 800.0, 1100.0, 0.0, 2500.0, 1000.0, *DWELL]
    times = [k / FPS for k in range(len(stuttered) + 1)]
    assert not cadence.judge(stuttered, times, FPS).smooth()
    assert cadence.judge(STEP, even, FPS).still_frames == 2 * len(DWELL)


def test_a_finding_is_placed_in_its_step_and_against_its_schedule() -> None:
    steps = [
        {"n": 9, "kind": "prefix", "frames": 54},
        {"n": 10, "kind": "matched", "frames": 182},
    ]
    assert cadence.locate(60, steps, FPS) == (10, "matched", 0.1)
    schedule = {"moveStart": 0.6, "moveEnd": 2.728, "end": 3.028}
    assert cadence.nearest_instant(0.617, schedule, FPS) == "+1 frames from moveStart"
