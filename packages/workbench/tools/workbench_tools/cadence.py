#!/usr/bin/env python3
"""Whether a delivered video's motion is smooth at its frame rate.

A capture seeks the page to every frame's own instant, so each frame is the page at exactly
k / fps seconds, and `delivery` checks that the file holds the frame rate and the duration the
receipt says. Neither says the motion is smooth. Two things can still spoil it, and a viewer
sees both:

- **A stutter**: a frame that repeats the one before it while things are moving. The page
  seeked, but the screenshot was taken before the new instant was painted, or the encoder
  dropped and duplicated a frame, and the motion stops for a sixtieth of a second and then
  jumps to catch up.
- **An uneven clock**: presentation times that are not evenly spaced, so frames are held for
  different lengths of time even though every one was drawn.

This decodes the file at a reduced size, measures how much each frame changes from the one
before, and finds every repeated frame that sits inside motion, and it reads every packet's
presentation time and measures how far any gap strays from 1 / fps. A frame that repeats
inside a still stretch, such as a dwell, is the picture holding, not a stutter, and is not
counted.

The measurement and the judgement are separate, and the judgement is pure, so the rules are
tested on recorded change series without a video.

Usage, from `packing/`:
    uv run --frozen --all-extras --group dev squares-workbench-check-cadence VIDEO [VIDEO ...]
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import subprocess
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

from workbench_tools.capture_video import PAGE, priced_range, render_frames
from workbench_tools.delivery import FRAME_PATTERN
from workbench_tools.probes import probe

#: The size frames are decoded at to measure change, in pixels. A square on the stage is tens of
#: pixels even at this size, so a moving one changes hundreds of the pixels measured.
MEASURE_WIDTH = 480
MEASURE_HEIGHT = 270

#: How far a pixel must change, on a 0 to 255 grey scale, to have moved rather than been
#: recolored. Motion is judged on pixels that move, not on the mean change: a slow color fade
#: is stored as 8-bit fills, so every square steps one level on one frame and none on the next,
#: and the mean change alternates 0.39, 0.00, 0.39 through every step's last frames while
#: nothing moves at all (measured on the n = 1..100 cut, 2026-09-21). A moving edge between a
#: square's black border and its fill changes by far more than this; a one-level step never
#: does.
MOVED_EDGE = 12

#: A frame in which at most this many pixels moved, at the measuring size, is a repeat. Encoder
#: rounding can move a handful; a square's edge moving one pixel moves dozens.
REPEAT = 20

#: How many pixels must move in the frame before a repeat and in the frame after it for the
#: repeat to be inside motion rather than a still stretch.
MOTION = 100

#: How far a presentation-time gap may stray from 1 / fps, in seconds, before the clock is
#: uneven. The container's timescale rounds times to about a microsecond at 60 fps.
CLOCK_SLACK = 1e-4


@dataclass(frozen=True, slots=True)
class Cadence:
    """What a video's frames and clock were measured to do."""

    frames: int
    fps: float
    stutters: tuple[int, ...]
    worst_gap_error: float
    still_frames: int

    def smooth(self) -> bool:
        return not self.stutters and self.worst_gap_error <= CLOCK_SLACK


def moved_pixels(before: np.ndarray, after: np.ndarray) -> int:
    """How many pixels changed by more than `MOVED_EDGE` between two grey frames."""
    return int(
        np.count_nonzero(np.abs(after.astype(np.int16) - before.astype(np.int16)) > MOVED_EDGE)
    )


def stutters(moving: Sequence[float]) -> list[int]:
    """The frames that repeat the one before them while the picture around them moves.

    `moving[i]` is how many pixels moved from frame `i` to frame `i + 1`. A repeat at `i` is a
    stutter when the frame into it and the frame out of it both moved: the picture was moving,
    stopped for one frame, and moved on. Returned as the index of the repeated frame.
    """
    return [
        i + 1
        for i in range(1, len(moving) - 1)
        if moving[i] <= REPEAT and moving[i - 1] > MOTION and moving[i + 1] > MOTION
    ]


def worst_gap_error(times: Sequence[float], fps: float) -> float:
    """The furthest any gap between consecutive presentation times strays from 1 / fps."""
    if len(times) < 2:
        return 0.0
    gaps = np.diff(np.asarray(times, dtype=float))
    return float(np.max(np.abs(gaps - 1.0 / fps)))


def judge(moving: Sequence[float], times: Sequence[float], fps: float) -> Cadence:
    """The cadence the measurements describe; `moving` is the moved-pixel series."""
    return Cadence(
        frames=len(moving) + 1,
        fps=fps,
        stutters=tuple(stutters(moving)),
        worst_gap_error=worst_gap_error(times, fps),
        still_frames=sum(1 for count in moving if count <= REPEAT),
    )


def _tool(name: str) -> str:
    found = shutil.which(name)
    if found is None:
        raise SystemExit(f"no {name} on PATH: install ffmpeg (`brew install ffmpeg`)")
    return found


#: Where on the stage a change is read separately, in stage pixels (left, top, right, bottom):
#: the packing's own box and the facts column beside it. A stutter in one and not the other says
#: which part of the page drew it.
REGIONS: dict[str, tuple[int, int, int, int]] = {
    "packing": (30, 12, 1086, 1068),
    "facts": (1100, 0, 1920, 1080),
}


def measure_regions(video: Path) -> dict[str, list[float]]:
    """Each frame's mean change over the whole stage and over each of `REGIONS`."""
    series: dict[str, list[float]] = {
        "moving": [],
        "all": [],
        **{name: [] for name in REGIONS},
    }
    scale = MEASURE_WIDTH / 1920
    cuts = {
        name: (
            slice(round(top * scale), round(bottom * scale)),
            slice(round(left * scale), round(right * scale)),
        )
        for name, (left, top, right, bottom) in REGIONS.items()
    }
    previous: np.ndarray | None = None
    for frame in _frames(video):
        if previous is not None:
            moved = np.abs(frame - previous)
            series["moving"].append(float(np.count_nonzero(moved > MOVED_EDGE)))
            series["all"].append(float(np.mean(moved)))
            for name, (rows, cols) in cuts.items():
                series[name].append(float(np.mean(moved[rows, cols])))
        previous = frame
    return series


def _frames(video: Path) -> Iterator[np.ndarray]:
    """Decode `video` in grey at `MEASURE_WIDTH` x `MEASURE_HEIGHT`, one array per frame."""
    command = [
        _tool("ffmpeg"),
        "-v",
        "error",
        "-i",
        str(video),
        "-vf",
        f"scale={MEASURE_WIDTH}:{MEASURE_HEIGHT}:flags=area,format=gray",
        "-f",
        "rawvideo",
        "-",
    ]
    size = MEASURE_WIDTH * MEASURE_HEIGHT
    with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder:
        if decoder.stdout is None:
            raise SystemExit(f"ffmpeg gave no output for {video}")
        while chunk := decoder.stdout.read(size):
            if len(chunk) < size:
                break
            yield (
                np.frombuffer(chunk, dtype=np.uint8)
                .astype(np.int16)
                .reshape(MEASURE_HEIGHT, MEASURE_WIDTH)
            )
    if decoder.returncode not in (0, None):
        raise SystemExit(f"ffmpeg could not decode {video}")


def frame_changes(frames_dir: Path, first: int, last: int) -> list[float]:
    """The same change as `measure_regions` reads off the video, read off the capture's own
    PNGs from frame `first` to `last`: where the two differ, the encoder made the difference."""
    changes: list[float] = []
    previous: np.ndarray | None = None
    for index in range(first, last + 1):
        image = Image.open(frames_dir / (FRAME_PATTERN % index)).convert("L")
        small = np.asarray(
            image.resize((MEASURE_WIDTH, MEASURE_HEIGHT), Image.Resampling.BOX), dtype=np.int16
        )
        if previous is not None:
            changes.append(float(np.mean(np.abs(small - previous))))
        previous = small
    return changes


#: How many pixels of a full-size frame may differ by more than `MOVED_EDGE` between two draws
#: of the same instant and the two still be the same frame. Chromium's antialiasing varies
#: between draws, but by a few grey levels at an edge, not by an edge's contrast; a frame the
#: capture recorded stale has every moving edge in the wrong place. A mean difference could not
#: tell these apart where little moves: dense frames of the whole ascent differed by 0.05 to
#: 0.065 in the mean from draw to draw (2026-09-21), the size of a small real motion.
RENDER_NOISE_PIXELS = 20


def unfaithful(frames_dir: Path, rendered: dict[int, bytes]) -> dict[int, str]:
    """Each re-rendered frame that differs from the kept PNG of the same index by more than
    `RENDER_NOISE_PIXELS` moved pixels, with the count and the stage box they fall in: an empty
    result says the capture recorded the page's own frames."""
    found: dict[int, str] = {}
    for index, png in sorted(rendered.items()):
        kept = np.asarray(Image.open(frames_dir / (FRAME_PATTERN % index)).convert("L"))
        fresh = np.asarray(Image.open(io.BytesIO(png)).convert("L"))
        moved = moved_pixels(kept, fresh)
        if moved > RENDER_NOISE_PIXELS:
            rows, cols = np.nonzero(
                np.abs(kept.astype(np.int16) - fresh.astype(np.int16)) > MOVED_EDGE
            )
            scale = 1920 / kept.shape[1]
            box = [round(v * scale) for v in (cols.min(), rows.min(), cols.max(), rows.max())]
            where = [
                name
                for name, (x0, y0, x1, y1) in REGIONS.items()
                if box[0] < x1 and box[2] > x0 and box[1] < y1 and box[3] > y0
            ]
            found[index] = f"{moved} px in {box} ({', '.join(where) or 'neither'})"
    return found


def verification(
    frames_dir: Path, rendered: dict[int, bytes], held: Sequence[int]
) -> tuple[list[str], bool]:
    """Whether each hold the video shows is the page's own, from fresh draws of it.

    A hold is the page's own when a fresh draw of the page holds there too: the frame and the
    one before it, drawn again, move no more than `RENDER_NOISE_PIXELS`. A hold that is not is
    a stutter the capture made. Separately, a kept frame that differs from its fresh draw says
    the page draws that instant differently when walked to than when jumped to, which is a
    property of the page rather than of the film. Returns the report and whether every hold is
    the page's own.
    """
    fresh = {
        i: np.asarray(Image.open(io.BytesIO(png)).convert("L")) for i, png in rendered.items()
    }
    made = [
        s
        for s in held
        if s - 1 in fresh
        and s in fresh
        and moved_pixels(fresh[s - 1], fresh[s]) > RENDER_NOISE_PIXELS
    ]
    lines = [
        (
            f"  drawn again from the page: {len(held) - len(made)} of {len(held)} holds are "
            "the page's own, a fresh draw holding there too"
        )
    ]
    if made:
        motion = {s: moved_pixels(fresh[s - 1], fresh[s]) for s in made}
        lines.append(
            f"  FAIL {len(made)} holds where a fresh draw moves (frame: pixels moved): "
            + ", ".join(f"{s}: {motion[s]}" for s in made[:16])
        )
        kept = {
            i: np.asarray(Image.open(frames_dir / (FRAME_PATTERN % i)).convert("L"))
            for i in made
        }
        late = [s for s in made if moved_pixels(kept[s], fresh[s - 1]) <= RENDER_NOISE_PIXELS]
        lines.append(
            f"  of those, {len(late)} are the page one frame early: the screenshot was taken "
            "before the new instant was painted"
        )
    off = unfaithful(frames_dir, rendered)
    if off:
        sample = "; ".join(f"{i}: {v}" for i, v in list(off.items())[:4])
        lines.append(
            f"  note: {len(off)} of {len(rendered)} frames draw differently walked to than "
            f"jumped to ({sample})"
        )
    lines.append("  smooth: every hold is the page's own" if not made else "  not smooth")
    return lines, not made


def measure_changes(video: Path) -> list[float]:
    """Each frame's mean change over the whole stage."""
    return measure_regions(video)["all"]


def measure_clock(video: Path) -> tuple[list[float], float]:
    """Every video packet's presentation time, in order, and the stream's frame rate."""
    rate = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=r_frame_rate",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    numerator, _, denominator = rate.partition("/")
    fps = float(numerator) / float(denominator or 1)
    listed = subprocess.run(
        [
            _tool("ffprobe"),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts_time",
            "-of",
            "csv=p=0",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return sorted(float(t) for t in listed if t and t != "N/A"), fps


#: The instants of a step's schedule a stutter is placed against, as the page reports them.
SCHEDULE_INSTANTS = (
    "moveStart",
    "containerEnd",
    "arrive",
    "arrived",
    "blocksStart",
    "blocksEnd",
    "moveEnd",
    "end",
)


def locate(
    frame: int, steps: Sequence[dict[str, object]], fps: float
) -> tuple[int, str, float]:
    """The step of a capture's receipt that `frame` belongs to: its n, kind and instant."""
    start = 0
    for step in steps:
        count = int(str(step["frames"]))
        if frame < start + count:
            return int(str(step["n"])), str(step["kind"]), (frame - start) / fps
        start += count
    raise ValueError(f"frame {frame} is past the receipt's last step")


def nearest_instant(t: float, schedule: dict[str, float], fps: float) -> str:
    """Which of the step's schedule instants `t` is nearest, and how many frames from it."""
    name, at = min(
        ((key, float(schedule[key])) for key in SCHEDULE_INSTANTS if key in schedule),
        key=lambda entry: abs(entry[1] - t),
    )
    return f"{round((t - at) * fps):+d} frames from {name}"


def schedules(page_path: Path, ns: Sequence[int]) -> dict[int, dict[str, float]]:
    """Each step's schedule as the page that was captured reports it."""
    found: dict[int, dict[str, float]] = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(page_path.resolve().as_uri())
        page.wait_for_function(probe("benchmark/page-api-ready"))
        for n in sorted(set(ns)):
            calls = [["pause"], ["setStepN", n], ["schedule"]]
            found[n] = page.evaluate(probe("api/apply"), {"calls": calls})
        browser.close()
    return found


def detail(
    changes: Sequence[float],
    cadence: Cadence,
    *,
    steps: Sequence[dict[str, object]] = (),
    timetable: dict[int, dict[str, float]] | None = None,
    regions: dict[str, list[float]] | None = None,
    frames_dir: Path | None = None,
    around: int = 4,
) -> list[str]:
    """The change series either side of each stutter, where it falls in the capture and how near
    it is to one of its step's phase boundaries, for telling a paint that was missed from an
    animation that really holds for a frame."""
    lines = []
    for frame in cadence.stutters:
        start = max(0, frame - 1 - around)
        window = " ".join(f"{c:.3f}" for c in changes[start : frame + around])
        where = ""
        if steps:
            n, kind, t = locate(frame, steps, cadence.fps)
            where = f", step into {n} ({kind}) at t {t:.3f} s"
            if timetable is not None and n in timetable:
                where += f", {nearest_instant(t, timetable[n], cadence.fps)}"
        lines.append(f"    frame {frame} ({frame / cadence.fps:.3f} s{where}): {window}")
        for name, series in (regions or {}).items():
            if name != "all":
                part = " ".join(f"{c:.3f}" for c in series[start : frame + around])
                lines.append(f"      {name:>8}: {part}")
        if frames_dir is not None:
            png = frame_changes(frames_dir, start, min(frame + around, len(changes)))
            lines.append(f"      {'pngs':>8}: " + " ".join(f"{c:.3f}" for c in png))
    return lines


def explain(
    video: Path,
    changes: Sequence[float],
    cadence: Cadence,
    *,
    priced: tuple[int, int] | None = None,
    regions: dict[str, list[float]] | None = None,
    frames_dir: Path | None = None,
) -> list[str]:
    """The detail lines, placed in the capture by its receipt and against the schedule of the
    page it was cut from, when that page is still the one the receipt names by digest.

    A cut with no receipt -- one its profile refused -- is placed by pricing `priced`, its
    range, from the built page, which is only right if the page has not changed since.
    """
    receipt_path = video.with_suffix(".receipt.json")
    if not receipt_path.is_file():
        if priced is None:
            return detail(changes, cadence, regions=regions, frames_dir=frames_dir)
        steps = priced_range(PAGE, priced[0], priced[1], round(cadence.fps))
        ns = [locate(frame, steps, cadence.fps)[0] for frame in cadence.stutters]
        note = [
            f"    (no receipt: placed by pricing n = {priced[0]} to {priced[1]} from {PAGE})"
        ]
        return [
            *note,
            *detail(
                changes,
                cadence,
                steps=steps,
                timetable=schedules(PAGE, ns),
                regions=regions,
                frames_dir=frames_dir,
            ),
        ]
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    steps = receipt["steps"]
    page = Path(receipt["page"])
    timetable = None
    note = []
    if (
        page.is_file()
        and hashlib.sha256(page.read_bytes()).hexdigest() == receipt["page_sha256"]
    ):
        ns = [locate(frame, steps, cadence.fps)[0] for frame in cadence.stutters]
        timetable = schedules(page, ns) if ns else {}
    else:
        note = [f"    ({page} is not the page this was cut from, so no schedule is read)"]
    return [
        *note,
        *detail(
            changes,
            cadence,
            steps=steps,
            timetable=timetable,
            regions=regions,
            frames_dir=frames_dir,
        ),
    ]


def cut_cited(video: Path) -> bool:
    """Whether a cut drew its CITATION section, as its receipt says. A cut without a receipt --
    one its profile refused -- is taken as plain, which is right only if it was cut plain."""
    receipt = video.with_suffix(".receipt.json")
    if not receipt.is_file():
        return False
    return json.loads(receipt.read_text(encoding="utf-8")).get("citations") is True


def report(video: Path, cadence: Cadence) -> str:
    """One paragraph a person reads: what was measured and whether it is smooth."""
    lines = [
        f"{video}: {cadence.frames} frames at {cadence.fps:g} fps",
        (
            f"  clock: every gap within {cadence.worst_gap_error * 1e6:.1f} us of "
            f"1/{cadence.fps:g} s"
        ),
        f"  still frames (the picture holding): {cadence.still_frames}",
    ]
    if cadence.stutters:
        at = ", ".join(f"{i / cadence.fps:.3f} s" for i in cadence.stutters[:12])
        lines.append(f"  FAIL {len(cadence.stutters)} repeated frames inside motion, at {at}")
    if cadence.worst_gap_error > CLOCK_SLACK:
        lines.append(f"  FAIL the clock is uneven beyond {CLOCK_SLACK * 1e6:.0f} us")
    lines.append("  smooth" if cadence.smooth() else "  not smooth")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("videos", type=Path, nargs="+")
    ap.add_argument(
        "--detail", action="store_true", help="print the changes around each stutter"
    )
    ap.add_argument(
        "--range",
        type=int,
        nargs=2,
        metavar=("FIRST", "LAST"),
        help="with --detail and no receipt: the range of the cut, priced from its page",
    )
    ap.add_argument("--frames", type=Path, help="with --detail: the capture's kept PNGs")
    ap.add_argument(
        "--dump",
        type=Path,
        help="with --verify: write the fresh draws here, beside nothing else",
    )
    ap.add_argument(
        "--verify",
        action="store_true",
        help="with --frames and --range: re-render each stutter and the frame before it",
    )
    o = ap.parse_args()
    failed = False
    for video in o.videos:
        times, fps = measure_clock(video)
        regions = measure_regions(video)
        changes = regions["all"]
        cadence = judge(regions["moving"], times, fps)
        print(report(video, cadence))
        if o.detail:
            print(
                "\n".join(
                    explain(
                        video,
                        changes,
                        cadence,
                        priced=o.range,
                        regions=regions,
                        frames_dir=o.frames,
                    )
                )
            )
        verified = False
        if o.verify and o.frames is not None and o.range is not None and cadence.stutters:
            indices = sorted({i for s in cadence.stutters for i in (s - 1, s)})
            rendered = render_frames(
                PAGE, o.range[0], o.range[1], round(fps), indices, citations=cut_cited(video)
            )
            if o.dump is not None:
                o.dump.mkdir(parents=True, exist_ok=True)
                for index, png in rendered.items():
                    (o.dump / (FRAME_PATTERN % index)).write_bytes(png)
            lines, verified = verification(o.frames, rendered, cadence.stutters)
            print("\n".join(lines))
        failed = failed or not (cadence.smooth() or verified)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
