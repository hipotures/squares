"""The transition contract: what a step may and may not look like, frame by frame.

About ten visual regressions landed in one session -- a yellow mid-blend, a grey flash, the
view jerking, the new square's red vanishing, a red-green-red thrash, a whole grid flashing
olive -- and every one passed the unit tests, the Python tests and `check_animate_view`,
because none of those check what the animation looks like over time. Each was found by the
owner watching and then diagnosed with JavaScript typed into a browser, which is the one-off
measurement OR-1 exists to forbid, and which is why the same class of fault kept coming back.

This module is the contract those measurements should have been. Its functions are pure: they
take what `probes/transitions/sweep.js` sampled and return findings, so they run without a
browser and are tested on recorded shapes. `check_transitions` drives the page and applies them.

A finding names the rule, the step, the frame and the value, because a red check is only useful
if it says where to look.

The rules, each written against a fault that actually shipped:

- **No third hue.** A blend never shows a hue neither of its ends has.
- **A hue turns only through grey.** While a square carries chroma its hue holds.
- **No lightness jump.** A shade blends; it does not snap, in grey or in color.
- **The crossing is symmetric.** Chroma falls into a crossing and rises out of it without a
  bump, and the rise shows no hue the fall did not.
- **The view does not jerk.** Its size moves one way within a step, a bounded amount per frame.
- **The box never grows** after the one instant the move begins.
- **The arriving square is red.** It is saturated scarlet for a declared number of frames.
- **A still pair does not recolor** a square that does not move.
- **Something was sampled.** A step with no opaque square checked nothing, and fails.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

#: Below this OKLab chroma a sample is neutral and its hue is noise: a hue test on it would
#: report the angle of a point at the origin.
CHROMA_FLOOR = 0.03

#: How far a sample's hue may sit from its nearer end before it is a hue neither end has, in
#: degrees. The angle families are further apart than this, so a real third hue clears it.
HUE_SLACK = 20.0

#: How much a chroma may rise on the way into a crossing, or fall on the way out, before it is
#: a bump rather than rounding. OKLab chroma of an 8-bit sRGB fill moves by about this much
#: between adjacent codes.
CHROMA_JITTER = 0.004

#: How far the view may move in one frame, in world units. The largest honest change -- the
#: room growing by one unit as ceil(sqrt(n)) steps -- spread over an 18-frame dwell is about
#: 0.06 a frame; a jump is ten times that.
VIEW_STEP_LIMIT = 0.2

#: How far a square's hue may wander while it carries chroma, in degrees. `mix` blends hues
#: closer than its `HUE_ARC_LIMIT` (25) along the arc without passing through neutral, and a
#: fill just above `CHROMA_FLOOR` carries about eight degrees of rounding in its angle; past
#: their sum the hue is visibly turning into another one.
HUE_RUN_SPREAD = 35.0

#: How far a square's OKLab lightness may move in one frame. The quickest honest change is a
#: shade blend over a color fade of about 0.3 s, which at 60 fps moves under 0.01 a frame even
#: at smootherstep's steepest; one palette shade to the next is about 0.1. So a move of this
#: size in one frame is a snap, not a blend.
LIGHTNESS_STEP_LIMIT = 0.04

#: The arriving square's scarlet: its hue in degrees, how near a sample must be to count, and
#: the chroma it must carry to be "saturated". Measured off the owner's own `#893d4a`.
SCARLET_HUE = 11.0
SCARLET_HUE_SLACK = 15.0
SCARLET_CHROMA = 0.08


@dataclass(frozen=True, slots=True)
class Finding:
    """One broken rule, with where to look."""

    rule: str
    n: int
    frame: int
    detail: str

    def __str__(self) -> str:
        return f"{self.rule} at the step into {self.n}, frame {self.frame}: {self.detail}"


def _srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.040_45 else ((value + 0.055) / 1.055) ** 2.4


def oklch(hex_color: str) -> tuple[float, float, float]:
    """A `#rrggbb` fill as OKLCH: lightness, chroma, hue in degrees.

    The same conversion `src/view/colour.ts` paints with, so a hue measured here is the hue the
    page computed rather than an approximation of it.
    """
    value = hex_color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"not a six-digit fill: {hex_color!r}")
    red, green, blue = (_srgb_to_linear(int(value[i : i + 2], 16) / 255) for i in (0, 2, 4))
    long = math.cbrt(0.412_221_470_8 * red + 0.536_332_536_3 * green + 0.051_445_992_9 * blue)
    medium = math.cbrt(0.211_903_498_2 * red + 0.680_699_545_1 * green + 0.107_396_956_6 * blue)
    short = math.cbrt(0.088_302_461_9 * red + 0.281_718_837_6 * green + 0.629_978_700_5 * blue)
    lightness = 0.210_454_255_3 * long + 0.793_617_785 * medium - 0.004_072_046_8 * short
    a = 1.977_998_495_1 * long - 2.428_592_205 * medium + 0.450_593_709_9 * short
    b = 0.025_904_037_1 * long + 0.782_771_766_2 * medium - 0.808_675_766 * short
    return lightness, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def hue_gap(left: float, right: float) -> float:
    """The shorter way round the wheel between two hues, in degrees."""
    gap = abs(left - right) % 360
    return min(gap, 360 - gap)


def tracks(frames: Sequence[dict[str, Any]]) -> dict[int, list[tuple[int, str, float]]]:
    """Each square's samples, keyed by identity: (frame, fill, opacity) in frame order."""
    out: dict[int, list[tuple[int, str, float]]] = {}
    for index, frame in enumerate(frames):
        for identity, fill, opacity in frame["squares"]:
            if fill:
                out.setdefault(int(identity), []).append((index, str(fill), float(opacity)))
    return out


def _ends(track: Sequence[tuple[int, str, float]]) -> tuple[float, float] | None:
    """The hue a track starts and ends on, reading past neutral samples at either end."""
    chromatic = [oklch(fill) for _, fill, opacity in track if opacity >= 1]
    chromatic = [(c, h) for _, c, h in chromatic if c >= CHROMA_FLOOR]
    if not chromatic:
        return None
    return chromatic[0][1], chromatic[-1][1]


def third_hues(n: int, frames: Sequence[dict[str, Any]]) -> list[Finding]:
    """Samples whose hue is near neither end of their own square's blend.

    Only fully opaque samples count: a square fading in over white reads as a pale version of
    whatever it is, which is opacity rather than hue.
    """
    findings: list[Finding] = []
    for identity, track in tracks(frames).items():
        ends = _ends(track)
        if ends is None:
            continue
        start, end = ends
        for frame, fill, opacity in track:
            if opacity < 1:
                continue
            _, chroma, hue = oklch(fill)
            if chroma < CHROMA_FLOOR:
                continue
            if min(hue_gap(hue, start), hue_gap(hue, end)) > HUE_SLACK:
                findings.append(
                    Finding(
                        "third hue",
                        n,
                        frame,
                        f"square {identity} is {fill} (hue {hue:.0f}, chroma {chroma:.3f}) "
                        f"between ends at hue {start:.0f} and {end:.0f}",
                    )
                )
                break
    return findings


def hue_turns(n: int, frames: Sequence[dict[str, Any]]) -> list[Finding]:
    """A square whose hue turns while it carries chroma, rather than through grey.

    A change of hue is allowed only where the square has no hue to show: each stretch of
    samples above `CHROMA_FLOOR` must hold one hue, to within `HUE_RUN_SPREAD`. This is the
    rule `third_hues` cannot state, since the fault it closes shows no third hue at all: a
    square came back from grey in its OLD hue and turned to the new one a few frames later, a
    yellow reappearing on the way to pink. Both ends were yellow and pink, so `third_hues` had
    nothing to report.
    """
    findings: list[Finding] = []
    for identity, track in tracks(frames).items():
        first: tuple[int, float] | None = None
        for frame, fill, opacity in track:
            if opacity < 1:
                continue
            _, chroma, hue = oklch(fill)
            if chroma < CHROMA_FLOOR:
                first = None
                continue
            if first is None:
                first = (frame, hue)
                continue
            if hue_gap(hue, first[1]) > HUE_RUN_SPREAD:
                findings.append(
                    Finding(
                        "hue turns outside grey",
                        n,
                        frame,
                        f"square {identity} turns from hue {first[1]:.0f} (frame {first[0]}) "
                        f"to {hue:.0f} at chroma {chroma:.3f} without passing through grey",
                    )
                )
                break
    return findings


def merge_window(schedule: dict[str, float], fade: dict[str, float]) -> tuple[float, float]:
    """The seconds in which moving runs may join, as `assignGroups` in the page schedules it.

    From the moment the chroma has drained to the moment the hue starts back: the window the
    moving palette is drawn in, read at fixed checkpoints across it.
    """
    start = schedule["moveStart"] + fade["out"]
    return start, schedule["end"] - fade["in"] - fade["hueIn"]


def lightness_jumps(
    n: int,
    frames: Sequence[dict[str, Any]],
    arriving: int,
    merging: tuple[float, float] | None = None,
) -> list[Finding]:
    """A square whose lightness moves more than `LIGHTNESS_STEP_LIMIT` in one frame.

    The arriving square is exempt: it fades in over white, and a fade is opacity. Every other
    square's shade must blend, grey included, where a snap is still a flash: the fault this
    closes was a grey that climbed to one shade and dropped to the next in a single frame.

    Frames inside `merging` are exempt too, and deliberately. There two moving runs that touch
    join, and the smaller takes the larger's color at once: the moving palette says which
    squares travel together, and a join is the moment that changes. Drained to grey it is a
    change of grey, which this rule would otherwise report. Whether a join should blend
    instead is the owner's call, tracked on its own bead, not something to decide here.
    """
    findings: list[Finding] = []
    for identity, track in tracks(frames).items():
        if identity == arriving:
            continue
        previous: tuple[int, float] | None = None
        for frame, fill, opacity in track:
            if opacity < 1:
                previous = None
                continue
            lightness = oklch(fill)[0]
            # A join shows on the first frame at or after its checkpoint, so what is exempt is a
            # frame interval that holds one: the last checkpoint sits on the window's end and
            # lands on the frame after it.
            joining = (
                merging is not None
                and frame > 0
                and float(frames[frame - 1]["t"]) < merging[1]
                and float(frames[frame]["t"]) > merging[0]
            )
            if (
                previous is not None
                and not joining
                and frame == previous[0] + 1
                and abs(lightness - previous[1]) > LIGHTNESS_STEP_LIMIT
            ):
                findings.append(
                    Finding(
                        "lightness jump",
                        n,
                        frame,
                        f"square {identity} moves L {previous[1]:.3f} -> {lightness:.3f} "
                        "in one frame",
                    )
                )
                break
            previous = (frame, lightness)
    return findings


def chroma_bumps(n: int, frames: Sequence[dict[str, Any]]) -> list[Finding]:
    """A crossing whose chroma does not fall then rise.

    For each square that passes near neutral, chroma must not rise before its lowest sample nor
    fall after it, beyond `CHROMA_JITTER`. A bump on the way back up is the asymmetry the owner
    saw: the drain leaves smoothly and the return shows something on its way.
    """
    findings: list[Finding] = []
    for identity, track in tracks(frames).items():
        chromas = [oklch(fill)[1] for _, fill, opacity in track if opacity >= 1]
        frame_of = [frame for frame, _, opacity in track if opacity >= 1]
        if len(chromas) < 3 or min(chromas) >= CHROMA_FLOOR:
            continue
        low = chromas.index(min(chromas))
        for i in range(1, low + 1):
            if chromas[i] > chromas[i - 1] + CHROMA_JITTER:
                findings.append(
                    Finding(
                        "chroma bump",
                        n,
                        frame_of[i],
                        f"square {identity} rises {chromas[i - 1]:.3f} -> {chromas[i]:.3f} "
                        "on the way into its crossing",
                    )
                )
                break
        for i in range(low + 1, len(chromas)):
            if chromas[i] < chromas[i - 1] - CHROMA_JITTER:
                findings.append(
                    Finding(
                        "chroma bump",
                        n,
                        frame_of[i],
                        f"square {identity} falls {chromas[i - 1]:.3f} -> {chromas[i]:.3f} "
                        "on the way out of its crossing",
                    )
                )
                break
    return findings


def view_jerks(n: int, views: Sequence[float]) -> list[Finding]:
    """A view that moves too far in one frame, or turns back within the step."""
    findings: list[Finding] = []
    direction = 0
    for frame in range(1, len(views)):
        step = views[frame] - views[frame - 1]
        if abs(step) > VIEW_STEP_LIMIT:
            findings.append(
                Finding(
                    "view jump",
                    n,
                    frame,
                    f"the view moves {views[frame - 1]:.3f} -> {views[frame]:.3f} in one frame",
                )
            )
        if abs(step) > 1e-9:
            here = 1 if step > 0 else -1
            if direction and here != direction:
                findings.append(
                    Finding(
                        "view reversal",
                        n,
                        frame,
                        f"the view turns back at {views[frame - 1]:.3f} -> {views[frame]:.3f}",
                    )
                )
            direction = here
    return findings


def boundary_jerk(n: int, last_view: float, next_first_view: float) -> list[Finding]:
    """The view between the last frame of one step and the first of the next."""
    step = next_first_view - last_view
    if abs(step) > VIEW_STEP_LIMIT:
        return [
            Finding(
                "view jump across the boundary",
                n,
                0,
                f"the view moves {last_view:.3f} -> {next_first_view:.3f} between steps",
            )
        ]
    return []


def box_growth(
    n: int, boxes: Sequence[float], times: Sequence[float], move_start: float
) -> list[Finding]:
    """The bound box growing after the one instant it is allowed to, at the move's start.

    That instant is the first frame AFTER `move_start`: at `move_start` itself the step is
    still in its dwell and the box is at n's side, so a frame index rounded from the time would
    land one short and report the allowed change as a fault.
    """
    allowed = next((i for i, t in enumerate(times) if t > move_start), len(times))
    for frame in range(1, len(boxes)):
        if frame == allowed:
            continue
        if boxes[frame] > boxes[frame - 1] + 1e-6:
            return [
                Finding(
                    "box grows",
                    n,
                    frame,
                    f"the box widens {boxes[frame - 1]:.4f} -> {boxes[frame]:.4f}",
                )
            ]
    return []


def red_frames(frames: Sequence[dict[str, Any]], arriving: int) -> int:
    """How many frames show the arriving square opaque and saturated scarlet."""
    count = 0
    for frame in frames:
        for identity, fill, opacity in frame["squares"]:
            if int(identity) != arriving or not fill or float(opacity) < 1:
                continue
            _, chroma, hue = oklch(str(fill))
            if chroma >= SCARLET_CHROMA and hue_gap(hue, SCARLET_HUE) <= SCARLET_HUE_SLACK:
                count += 1
    return count


def still_recolors(n: int, frames: Sequence[dict[str, Any]], arriving: int) -> list[Finding]:
    """On a still pair, a square other than the arriving one whose HUE changes.

    Its shade may change and should: shade counts full-side contacts, and the square beside the
    new one gains a contact when it lands. What must not happen is the hue moving, which on a
    step where nothing rearranges is the whole grid flashing another color.
    """
    for identity, track in tracks(frames).items():
        if identity == arriving:
            continue
        hues = [h for _, c, h in (oklch(fill) for _, fill, _ in track) if c >= CHROMA_FLOOR]
        if hues and max(hue_gap(h, hues[0]) for h in hues) > HUE_SLACK:
            return [
                Finding(
                    "still pair recolors",
                    n,
                    track[0][0],
                    f"square {identity}'s hue moves on a step where nothing rearranges",
                )
            ]
    return []


def unsampled(n: int, frames: Sequence[dict[str, Any]]) -> list[Finding]:
    """A step in which no square was ever read opaque.

    The color rules skip samples that are not fully opaque, so a probe that misread opacity
    passes every one of them while checking nothing. That is not hypothetical: the first sweep
    read an unset inline style as 0, every square came back transparent, and the contract
    reported the step clean.
    """
    if any(float(opacity) >= 1 for frame in frames for _, _, opacity in frame["squares"]):
        return []
    return [Finding("nothing sampled", n, 0, "no square is opaque in any frame")]


def summarize(findings: Iterable[Finding]) -> dict[str, int]:
    """How many findings each rule produced, for a one-line report."""
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.rule] = counts.get(finding.rule, 0) + 1
    return counts
