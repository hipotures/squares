"""Controls for the cadence check: a stutter is a repeat inside motion, not a still stretch.

`cadence` measures a delivered video, then judges the measurements with pure functions, so the
rules are tested here on moved-pixel series shaped like the capture's own: a step that dwells,
moves and settles, at 60 fps. The decoder and ffprobe are not mocked; the capture's own videos
are what they are run on.
"""

from __future__ import annotations

import numpy as np

from workbench_tools import cadence
from workbench_tools.cadence import MOTION, MOVED_EDGE, REPEAT, change_between

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


def test_a_frame_is_placed_at_the_instant_the_capture_seeked_to() -> None:
    """A step does not begin on the frame grid, so the frame counts alone place a frame early.

    The receipt says the step into 9 owns 54 frames, which is all counting them can say; the
    step's own length is not 54 sixtieths, so the instant the capture seeked frame 55 to is
    not `(55 - 54) / 60`. `Beat` carries the capture's own frame schedule where it has one and
    falls back to the counts where it does not. Naming an instant a frame out is what sent the
    2026-09-22 findings to `moveStart` when they sit at `arrive`.
    """
    steps = [
        {"n": 9, "kind": "prefix", "frames": 54},
        {"n": 10, "kind": "matched", "frames": 182},
    ]
    counted = cadence.Beat(steps=tuple(steps))
    assert counted.place(55, FPS) == (10, "matched", 1 / FPS)
    seeked = cadence.Beat(
        steps=tuple(steps),
        samples=(
            *(cadence.FrameSample(index=k, step=0, at=0.0) for k in range(55)),
            cadence.FrameSample(index=55, step=1, at=0.033),
        ),
    )
    assert seeked.place(55, FPS) == (10, "matched", 0.033)


def test_a_change_says_where_it_fell_and_how_hard() -> None:
    """A stroke fading and a square arriving both move thousands of pixels; the box and the
    peak are what tell them apart, and how the container box's one-frame blink was named."""
    paper = np.full((1080, 1920), 250, dtype=np.uint8)
    stroke = paper.copy()
    stroke[100:900, 200:203] = 20  # an outline drawn down the packing's own frame
    fading = change_between(stroke, paper)
    assert fading.peak > 200
    assert fading.regions == ("packing",)
    assert fading.box[2] - fading.box[0] < 20  # a line, not a region
    arriving = paper.copy()
    arriving[100:900, 200:900] = 120  # a square filling a region of the same height
    filled = change_between(paper, arriving)
    assert filled.moved > 10 * fading.moved
    assert filled.box[2] - filled.box[0] > 600
    assert change_between(paper, paper).moved == 0


def test_a_flagged_frame_is_read_again_at_full_size_before_it_is_called_a_stutter() -> None:
    """The series is measured at a sixteenth of the area, where a real change can average
    away. On the n = 1..100 cut 8 of 29 flagged frames moved 2,184 to 4,460 full-size pixels
    (2026-09-22): the film was smooth there and the measurement was not fine enough to say
    so. The judgement is unchanged -- it is asked at a finer resolution, not a looser one.
    """
    # A frame the reduced series calls a repeat, between two that moved.
    moving = [MOTION * 5, REPEAT // 2, MOTION * 5]
    times = [k / FPS for k in range(4)]
    assert cadence.stutters(moving) == [2]
    # Left to itself the rule keeps it, which is what it said before this pass existed.
    assert cadence.judge(moving, times, FPS).stutters == (2,)
    # A finer reading that finds real movement drops it; one that agrees keeps it.
    assert cadence.judge(moving, times, FPS, confirm=lambda _: []).stutters == ()
    assert cadence.judge(moving, times, FPS, confirm=list).stutters == (2,)


def test_the_full_size_threshold_is_the_reduced_one_at_the_same_scale() -> None:
    """Not a looser rule: `REPEAT` pixels of the measured frame are `FULL_REPEAT` of the real
    one, so both ask the same question of the same picture at two resolutions."""
    area = (1920 * 1080) / (cadence.MEASURE_WIDTH * cadence.MEASURE_HEIGHT)
    assert int(REPEAT * area) == cadence.FULL_REPEAT
