#!/usr/bin/env python3
"""Capture the workbench's animation to a video file, with a receipt for what it shows.

The end product is a file the owner can upload. Frames come from the built workbench page
driven in a headless browser through the page's own clock, so a captured frame is the frame
the page draws at that instant rather than a second rendering that happens to agree -- which
is what makes "the video matches the workbench" a fact rather than a hope.

Capture preview is on for every frame: the controls, the kind tag and everything else that
explains the page are hidden, so nothing that is scaffolding survives into the file. The
stage is 1920x1080 in its own coordinates, so a 1080p capture is one page pixel per video
pixel and 4K is the same page at a device scale of two.

**The receipt is not optional.** A video of a packing search is a claim about what was
reached, and a file on its own cannot be checked: the receipt written beside it names the
page it came from by digest, the range, the frame rate, and, per step, the record the step
was aiming at and whether it actually landed on it. A step that did not land is reported as
a step that did not land rather than quietly filmed.

What this does NOT yet do is play a PackingStrategy document: the workbench animates the
retained corpus, and the strategy documents `build_ascent` writes reach the renderer by the
SVG path instead. Wiring the two together is `think-883t`, and until it lands the receipt
names records rather than strategy documents.

Usage, from `packing/`:
    uv run --frozen --all-extras --group dev python -m workbench_tools.capture_video --to 24
    uv run --frozen --all-extras --group dev python -m workbench_tools.capture_video \
        --from 100 --to 110 --fps 60 --height 2160 --out /tmp/ascent-4k.mp4
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from workbench_tools.probes import probe

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO = PACKAGE_ROOT.parents[1]
PACKING = REPO / "packing"
PAGE = PACKING / "site/workbench/index.html"

#: The stage's own coordinates. Every capture is this shape, scaled: the page lays itself out
#: in these units and a capture that changed the aspect would be cropping the poster, not
#: resizing it.
STAGE_WIDTH = 1920
STAGE_HEIGHT = 1080

#: What `--height` may ask for. A device scale below one resamples the page down and blurs the
#: 28 px type the panel is built around, which is the whole reason the type scale has a floor.
HEIGHTS = {1080: 1, 2160: 2}


def _control(
    page: Any,
    *,
    commands: list[list[Any]] | None = None,
    read: list[str] | None = None,
    prepare: bool = False,
) -> dict[str, Any]:
    """Drive and inspect the page through the strict capture controller."""
    request: dict[str, Any] = {}
    if commands:
        request["commands"] = commands
    if read:
        request["read"] = read
    if prepare:
        request.update({"prepare": True, "capture": True})
    return page.evaluate(probe("capture/control"), request)


def _encoder() -> str:
    """The ffmpeg to encode with, or an error saying how to get one."""
    found = shutil.which("ffmpeg")
    if found is None:
        raise SystemExit(
            "no ffmpeg on PATH: install one (`brew install ffmpeg`) or put it on PATH. "
            "The frames are captured either way; only the encode step needs it."
        )
    return found


def _steps(page: Any, first: int, last: int) -> list[dict[str, Any]]:
    """The pairs the range covers, as the page reports them.

    A pair is named by the n it steps *into*, which is how the workbench's own range control
    reads, so `--from 2 --to 24` is the ascent that ends with the 24-square packing.
    """
    pairs = _control(page, read=["pairs"])["pairs"]
    chosen = [p for p in pairs if first <= p["n"] + 1 <= last]
    if not chosen:
        have = f"{pairs[0]['n'] + 1} to {pairs[-1]['n'] + 1}"
        raise SystemExit(f"no steps in {first}..{last}: the page carries {have}")
    return chosen


def _capture(
    page: Any, steps: list[dict[str, Any]], fps: int, frames_dir: Path
) -> list[dict[str, Any]]:
    """Every frame of every step, to numbered PNGs. Returns what each step reached.

    The clock is the page's: `duration(index)` is how long that step lasts and `seek` puts it
    at an instant, so the frame count follows from the page rather than from a guess about how
    long a step ought to take. Sampling at the step's own end (rather than one frame short of
    it) is deliberate -- the settled packing is the frame the step exists to arrive at.
    """
    receipt = []
    index = 0
    for step in steps:
        selected = _control(
            page,
            commands=[["select", step["index"]]],
            read=["duration"],
        )
        seconds = selected["duration"]
        count = max(1, round(seconds * fps))
        started = time.monotonic()
        for frame in range(count + 1):
            at = seconds * frame / count
            _control(page, commands=[["seek", at]])
            page.screenshot(path=str(frames_dir / f"f{index:07d}.png"), type="png")
            index += 1
        drawing = time.monotonic() - started
        # The bar holds still through the motion and catches up when the picture settles, so it
        # is asked to redraw before it is read: what goes in the receipt is the settled answer.
        settled = _control(
            page,
            commands=[["refreshGap"]],
            read=["gap"],
        )
        bar = settled["gap"]
        receipt.append(
            {
                "n": bar["n"],
                "kind": step["kind"],
                "seconds": round(seconds, 4),
                "frames": count + 1,
                "record": bar["record"],
                "reached": bar["side"],
                "landed_on_record": bool(bar["met"]),
                "excess": bar["excess"],
                # What this step cost to draw. A capture is the slowest thing built here -- a
                # screenshot per frame through a real browser -- and it is the first place an
                # algorithm that got slower would show as the film taking twice as long to make.
                # Recorded per step rather than as a total so a step that is slow says which.
                "ms_per_frame": round(1000 * drawing / (count + 1), 1),
            }
        )
    return receipt


def _capture_animation(
    page: Any,
    source: str,
    fps: int,
    frames_dir: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Capture an imported v1 animation at the document's declared duration."""
    imported = _control(
        page,
        prepare=True,
        commands=[["importAnimation", source]],
        read=["animation", "exportAnimation"],
    )
    state = imported["animation"]
    if not state["active"]:
        raise ValueError("the imported animation did not become active")
    document = json.loads(imported["exportAnimation"])
    duration = float(state["durationSeconds"])
    if not 0 < duration < float("inf"):
        raise ValueError(f"animation duration must be positive and finite, got {duration!r}")
    frame_count = max(1, round(duration * fps))
    started = time.monotonic()
    last: dict[str, Any] = state
    for frame in range(frame_count + 1):
        last = _control(
            page,
            commands=[["seekAnimation", frame / frame_count]],
            read=["animation"],
        )["animation"]
        page.screenshot(path=str(frames_dir / f"f{frame:07d}.png"), type="png")
    drawing = time.monotonic() - started
    return (
        [
            {
                "n": last["n"],
                "seconds": duration,
                "frames": frame_count + 1,
                "guided": last["guided"],
                "valid": last["valid"],
                "ms_per_frame": round(1000 * drawing / (frame_count + 1), 1),
            }
        ],
        document,
    )


def _encode(ffmpeg: str, frames_dir: Path, fps: int, out: Path) -> list[str]:
    """The frames to an H.264 file anything will play. Returns the command, for the receipt.

    `yuv420p` and the even-dimension scale are not taste: without them QuickTime and most
    browsers refuse the file outright, which would make an unplayable "uploadable" video.
    """
    command = [
        ffmpeg,
        "-y",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "f%07d.png"),
        "-c:v",
        "libx264",
        "-preset",
        "slow",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        str(out),
    ]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise SystemExit(f"ffmpeg failed:\n{done.stderr[-2000:]}")
    return command


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", type=Path, default=PAGE, help="the built workbench page")
    ap.add_argument("--from", dest="first", type=int, default=2, help="the n to start at")
    ap.add_argument("--to", dest="last", type=int, default=24, help="the n to end on")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--height", type=int, default=1080, choices=sorted(HEIGHTS))
    ap.add_argument(
        "--animation",
        type=Path,
        help="capture this PackingAnimation/v1 document instead of the retained catalogue",
    )
    ap.add_argument("--out", type=Path, default=PACKING / "site/workbench/ascent.mp4")
    ap.add_argument("--keep-frames", action="store_true", help="leave the PNGs for inspection")
    o = ap.parse_args()

    if not o.page.exists():
        raise SystemExit(f"{o.page} is not built: run `squares-workbench-build` first")
    ffmpeg = _encoder()
    scale = HEIGHTS[o.height]
    started_all = time.monotonic()

    from playwright.sync_api import sync_playwright  # noqa: PLC0415  (optional dev dependency)

    o.out.parent.mkdir(parents=True, exist_ok=True)
    holder = Path(tempfile.mkdtemp(prefix="capture-video-"))
    frames_dir = holder / "frames"
    frames_dir.mkdir()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(
                viewport={"width": STAGE_WIDTH, "height": STAGE_HEIGHT},
                device_scale_factor=scale,
            )
            page.goto(o.page.resolve().as_uri(), wait_until="load")
            page.evaluate(probe("capture/fonts-ready"))
            # Animate is the mode that plays a range; capture preview is what hides the chrome.
            if o.animation is None:
                _control(page, prepare=True, commands=[["setMode", "animate"]])
                steps = _steps(page, o.first, o.last)
                print(
                    f"{len(steps)} steps, n = {o.first} to {o.last}, {o.fps} fps at {o.height}p"
                )
                receipt = _capture(page, steps, o.fps, frames_dir)
                animation = None
            else:
                source = o.animation.read_text(encoding="utf-8")
                receipt, animation = _capture_animation(page, source, o.fps, frames_dir)
                print(
                    f"animation {o.animation.name}, {receipt[0]['seconds']} s, "
                    f"{o.fps} fps at {o.height}p"
                )
            browser.close()
        command = _encode(ffmpeg, frames_dir, o.fps, o.out)
    finally:
        if o.keep_frames:
            print(f"  frames left in {frames_dir}")
        else:
            shutil.rmtree(holder, ignore_errors=True)

    frames = sum(step["frames"] for step in receipt)
    missed = [
        step["n"]
        for step in receipt
        if "landed_on_record" in step and not step["landed_on_record"]
    ]
    drawn = [step["ms_per_frame"] for step in receipt]
    document = {
        "page": str(o.page.relative_to(PACKING) if o.page.is_relative_to(PACKING) else o.page),
        "page_sha256": _digest(o.page),
        "video": o.out.name,
        "video_sha256": _digest(o.out),
        "range": [o.first, o.last],
        **(
            {
                "animation": str(o.animation),
                "animation_sha256": hashlib.sha256(o.animation.read_bytes()).hexdigest(),
                "animation_contract": animation["contract"],
            }
            if o.animation is not None and animation is not None
            else {}
        ),
        "fps": o.fps,
        "size": [STAGE_WIDTH * scale, STAGE_HEIGHT * scale],
        "frames": frames,
        "seconds": round(frames / o.fps, 3),
        "steps_off_record": missed,
        # The run's own cost, beside what it produced.
        "capture_seconds": round(took := time.monotonic() - started_all, 1),
        "ms_per_frame": {
            "mean": round(sum(drawn) / len(drawn), 1),
            "worst": max(drawn),
            "worst_at_n": receipt[drawn.index(max(drawn))]["n"],
        },
        "encoder": command,
        "steps": receipt,
    }
    receipt_path = o.out.with_suffix(".receipt.json")
    receipt_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    size_mb = o.out.stat().st_size / 1e6
    summary = f"{frames} frames, {document['seconds']}s, {size_mb:.1f} MB in {took:.0f}s"
    print(f"  {o.out}: {summary}")
    print(f"  {receipt_path}")
    if missed:
        print(f"  {len(missed)} step(s) did not land on the record: n = {missed[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
