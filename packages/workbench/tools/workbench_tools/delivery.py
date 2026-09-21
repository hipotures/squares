#!/usr/bin/env python3
"""Named delivery profiles for a captured video, and the check that the file is one.

A capture ends in a file somebody uploads. Between the frames and the upload sits a set of
constraints that has nothing to do with packing -- which H.264 level a phone will decode,
which pixel format a browser will play, how long a post may run -- and until now those
constraints lived in one hard-coded ffmpeg command and were never checked against what came
out of it. A flag ffmpeg ignored, a filter that changed the frame size, an encoder that
raised the level to buy a reference frame: any of these would leave the receipt reading as
though the file were what was asked for.

**A profile is one declaration used twice.** `encode_arguments` builds the command from it
and `conformance` compares the encoded stream against the same fields, so what was asked for
and what arrived are compared rather than assumed. This is the shape `capture_video` already
uses for the frame clock, where `price_steps` refuses a run whose steps do not add up to the
page's own figure for the range: a claim about the output is worth having only when
something would fail if it were false.

Two profiles, differing only in their ceilings, because a ceiling belongs to a destination
and an encode does not:

- `archive` is the master. Nothing is traded for anyone's upload rules.
- `social` carries the tightest ceiling we actually face, which is an X post: 140 seconds
  and 512 MB.

Level 4.0 is in both. x264 at `-preset slow` keeps five reference frames, whose
decoded-picture-buffer size at 1920x1080 is past what level 4.0 admits, so left alone it
tags the file 5.0 -- a compatibility cost bought with a compression gain measured at under
one per cent on this content. 1080p30 needs level 4.0, and a master tagged for hardware that
cannot play it is not a better master.

Fidelity is measured but never made a threshold: `fidelity` reports PSNR and SSIM against
the capture's own PNG frames, so a quality figure is distance from the page rather than
from another encode. What counts as good enough is a judgement, and a judgement that
silently became a number would stop being one.

Usage, from `packing/`:
    uv run --frozen --all-extras --group dev python -m workbench_tools.delivery VIDEO
    uv run --frozen --all-extras --group dev python -m workbench_tools.delivery VIDEO \\
        --frames /path/to/frames --from-frame 9900 --frames-window 900
"""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

Runner = Callable[..., subprocess.CompletedProcess[str]]

#: The frames' file names, numbered from zero without gaps, which is what ffmpeg's image
#: sequence reader requires. `capture_video` writes them and `fidelity` reads them back.
FRAME_PATTERN = "f%07d.png"

#: How far the stream's own duration may sit from the receipt's, in frames. One frame: the
#: container rounds a duration to its timescale, and a whole frame of drift means the file
#: does not hold the run the receipt describes.
DURATION_TOLERANCE_FRAMES = 1.0

#: What `moov` sitting this far into the file means: the index is at the front, so a browser
#: can start playing before the download ends. `+faststart` is what puts it there, and this
#: is how we read the result rather than trusting the flag.
FASTSTART_WINDOW_BYTES = 4096


@dataclass(frozen=True, slots=True)
class DeliveryProfile:
    """What a delivered file must be, used to encode it and then to check it.

    `max_seconds` and `max_bytes` are the destination's ceilings and are `None` on a profile
    that has none. `crf` and `preset` sit here rather than on the capture because they are
    the axis a future destination would move.
    """

    name: str
    crf: int
    preset: str
    h264_profile: str
    level: str
    pixel_format: str
    max_seconds: float | None
    max_bytes: int | None

    @property
    def level_tag(self) -> int:
        """The level as ffprobe reports it: `4.0` is 40, which is how H.264 encodes it."""
        major, minor = self.level.split(".")
        return int(major) * 10 + int(minor)


#: X accepts a video up to 140 s and 512 MB on a standard post. Both are the platform's
#: published limits rather than observed behaviour, so a file that clears them may still be
#: refused for a reason we do not model -- what the check buys is that it will not be
#: refused for one we do.
_X_MAX_SECONDS = 140.0
_X_MAX_BYTES = 512 * 1000 * 1000

PROFILES: dict[str, DeliveryProfile] = {
    "archive": DeliveryProfile(
        name="archive",
        crf=18,
        preset="slow",
        h264_profile="high",
        level="4.0",
        pixel_format="yuv420p",
        max_seconds=None,
        max_bytes=None,
    ),
    "social": DeliveryProfile(
        name="social",
        crf=18,
        preset="slow",
        h264_profile="high",
        level="4.0",
        pixel_format="yuv420p",
        max_seconds=_X_MAX_SECONDS,
        max_bytes=_X_MAX_BYTES,
    ),
}

DEFAULT_PROFILE = "archive"


@dataclass(frozen=True, slots=True)
class DeliveredVideo:
    """The encoded stream as `ffprobe` reports it, beside the file's own size."""

    codec: str
    h264_profile: str
    level: int
    pixel_format: str
    width: int
    height: int
    fps: float
    seconds: float
    bytes: int
    faststart: bool


@dataclass(frozen=True, slots=True)
class Fidelity:
    """Distance from the page's own pixels, over the window of frames that produced it."""

    psnr_db: float
    ssim: float
    first_frame: int
    frames: int


def metadata_comment(page_sha256: str, statement: str) -> str:
    """The MP4 comment: the receipt's statement and the page digest, for a video on its own."""
    return f"{statement} page sha256 {page_sha256}"


def encode_arguments(
    profile: DeliveryProfile,
    ffmpeg: str,
    frames_dir: Path,
    fps: int,
    out: Path,
    *,
    page_sha256: str,
    title: str,
    comment: str,
) -> list[str]:
    """The ffmpeg command that encodes the frames to an H.264 MP4 the profile describes.

    The pixel format and the even-dimension scale are not taste: without them QuickTime and
    most browsers refuse the file outright, which would make an unplayable "uploadable"
    video. `+faststart` puts the index first so a browser can start playing before the
    download ends. `-n` rather than `-y`: the output is a fresh temporary beside the
    destination, and ffmpeg overwriting anything would mean it was not.
    """
    return [
        ffmpeg,
        "-n",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / FRAME_PATTERN),
        "-c:v",
        "libx264",
        "-preset",
        profile.preset,
        "-crf",
        str(profile.crf),
        "-profile:v",
        profile.h264_profile,
        "-level",
        profile.level,
        "-pix_fmt",
        profile.pixel_format,
        "-vf",
        "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-movflags",
        "+faststart",
        "-metadata",
        f"title={title}",
        "-metadata",
        f"comment={metadata_comment(page_sha256, comment)}",
        "-f",
        "mp4",
        str(out),
    ]


def _rate(text: str) -> float:
    """A frame rate as ffprobe writes it, `30/1` or `30`."""
    if "/" in text:
        numerator, denominator = text.split("/", 1)
        return float(numerator) / float(denominator) if float(denominator) else 0.0
    return float(text)


def faststart(video: Path, *, window: int = FASTSTART_WINDOW_BYTES) -> bool:
    """Whether `moov` sits at the front of the file, read rather than taken on trust."""
    head = video.read_bytes()[:window]
    return b"moov" in head


def parse_probe(payload: str, *, size: int, has_faststart: bool) -> DeliveredVideo:
    """Turn `ffprobe -show_streams -show_format -of json` into a `DeliveredVideo`.

    Kept apart from running ffprobe so the parse is testable on recorded output. The stream's
    own duration is preferred over the container's, and the container's is the fallback for a
    stream that does not carry one.
    """
    document: dict[str, Any] = json.loads(payload)
    streams = [s for s in document.get("streams", []) if s.get("codec_type") == "video"]
    if not streams:
        raise ValueError("the file carries no video stream")
    stream = streams[0]
    container = document.get("format", {})
    seconds = stream.get("duration") or container.get("duration")
    if seconds is None:
        raise ValueError("neither the stream nor the container states a duration")
    return DeliveredVideo(
        codec=str(stream["codec_name"]),
        h264_profile=str(stream.get("profile", "")),
        level=int(stream.get("level", -1)),
        pixel_format=str(stream["pix_fmt"]),
        width=int(stream["width"]),
        height=int(stream["height"]),
        fps=_rate(str(stream["r_frame_rate"])),
        seconds=float(seconds),
        bytes=size,
        faststart=has_faststart,
    )


def measure(
    video: Path, *, ffprobe: str | None = None, run: Runner = subprocess.run
) -> DeliveredVideo:
    """What the encoded file actually is."""
    found = ffprobe or shutil.which("ffprobe")
    if found is None:
        raise SystemExit(
            "no ffprobe on PATH: install one (`brew install ffmpeg`) or put it on PATH. "
            "Without it the encoded file cannot be checked against its profile."
        )
    done = run(
        [
            found,
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise SystemExit(f"ffprobe failed on {video}:\n{done.stderr[-2000:]}")
    return parse_probe(done.stdout, size=video.stat().st_size, has_faststart=faststart(video))


def _mismatch(constraint: str, declared: object, measured: object) -> str:
    """A failure names the constraint, then what was asked for, then what arrived.

    That order because the useful question on a red check is always which of the two is
    wrong, and reading the declaration first is how you decide.
    """
    return f"{constraint}: declared {declared!r}, measured {measured!r}"


def conformance(
    profile: DeliveryProfile,
    delivered: DeliveredVideo,
    *,
    fps: int,
    width: int,
    height: int,
    seconds: float,
) -> list[str]:
    """Every way the file fails its profile, or an empty list.

    `seconds`, `width` and `height` come from the capture rather than the profile: they are
    what this run asked for, and a profile that fixed them could not describe both a 1080p
    and a 4K cut.
    """
    failures: list[str] = []
    if delivered.codec != "h264":
        failures.append(_mismatch("codec", "h264", delivered.codec))
    if delivered.h264_profile.lower() != profile.h264_profile.lower():
        failures.append(_mismatch("h264 profile", profile.h264_profile, delivered.h264_profile))
    if delivered.level != profile.level_tag:
        failures.append(_mismatch("level", profile.level_tag, delivered.level))
    if delivered.pixel_format != profile.pixel_format:
        failures.append(_mismatch("pixel format", profile.pixel_format, delivered.pixel_format))
    if (delivered.width, delivered.height) != (width, height):
        failures.append(
            _mismatch(
                "frame size", f"{width}x{height}", f"{delivered.width}x{delivered.height}"
            )
        )
    if not math.isclose(delivered.fps, fps, rel_tol=0, abs_tol=1e-6):
        failures.append(_mismatch("frame rate", fps, delivered.fps))
    drift = abs(delivered.seconds - seconds)
    if drift * fps > DURATION_TOLERANCE_FRAMES:
        failures.append(
            _mismatch("duration", f"{seconds:.3f}s", f"{delivered.seconds:.3f}s")
            + f" ({drift * fps:.1f} frames apart)"
        )
    if not delivered.faststart:
        failures.append(_mismatch("faststart", "moov at the front", "moov at the back"))
    if profile.max_seconds is not None and delivered.seconds > profile.max_seconds:
        failures.append(
            _mismatch(
                f"{profile.name} duration ceiling", profile.max_seconds, delivered.seconds
            )
        )
    if profile.max_bytes is not None and delivered.bytes > profile.max_bytes:
        failures.append(
            _mismatch(f"{profile.name} byte ceiling", profile.max_bytes, delivered.bytes)
        )
    return failures


#: Where each fidelity filter writes its summary figure. A regex that quietly missed would
#: report perfect fidelity as a zero, or as a number lifted from the wrong filter, so a miss
#: raises rather than defaulting.
FILTER_FIGURES: dict[str, re.Pattern[str]] = {
    "psnr": re.compile(r"average:([0-9.]+)"),
    "ssim": re.compile(r"\bAll:([0-9.]+)"),
}


def filter_figure(text: str, name: str) -> float:
    """The figure `ffmpeg`'s `psnr` or `ssim` filter wrote to stderr."""
    found = FILTER_FIGURES[name].search(text)
    if found is None:
        raise ValueError(f"ffmpeg reported no {name} figure; it said:\n{text[-2000:]}")
    return float(found.group(1))


def fidelity_arguments(
    ffmpeg: str,
    frames_dir: Path,
    video: Path,
    *,
    fps: int,
    first_frame: int,
    frames: int,
    filter_name: str,
) -> list[str]:
    """The ffmpeg command comparing a window of PNG frames against the same span of video.

    Argument position is the whole subtlety here, and getting it wrong is not a wrong number
    but a refusal: `-start_number`, `-framerate` and `-ss` are *input* options and must
    precede the `-i` they belong to, while the frame count is an *output* option. Put the
    count before the second `-i` and ffmpeg reads it as an input option on the video and
    stops. The PNG sequence would otherwise run to the end of the capture, so the output
    count is what bounds the window.

    The video is seeked to where the window starts, `first_frame / fps`, so the two inputs
    are the same instants. A window that lined up wrongly shows as a PSNR in the twenties
    rather than the forties, which is its own check.
    """
    return [
        ffmpeg,
        # `info`, not `error`: both filters write their summary at info level, so quieting
        # ffmpeg quiets the only line this command exists to read.
        "-v",
        "info",
        "-start_number",
        str(first_frame),
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / FRAME_PATTERN),
        "-ss",
        f"{first_frame / fps:.6f}",
        "-i",
        str(video),
        "-lavfi",
        f"[0:v][1:v]{filter_name}",
        "-frames:v",
        str(frames),
        "-f",
        "null",
        "-",
    ]


def fidelity(
    frames_dir: Path,
    video: Path,
    *,
    fps: int,
    first_frame: int,
    frames: int,
    ffmpeg: str | None = None,
    run: Runner = subprocess.run,
) -> Fidelity:
    """PSNR and SSIM of the encoded file against the PNG frames the capture wrote.

    The window is declared rather than defaulted to the start of the run: the ascent opens on
    three squares against white, which says nothing about how the encoder handles n = 300.
    """
    if frames <= 0:
        raise ValueError(f"a fidelity window needs at least one frame, got {frames}")
    found = ffmpeg or shutil.which("ffmpeg")
    if found is None:
        raise SystemExit("no ffmpeg on PATH: install one (`brew install ffmpeg`).")
    figures: dict[str, float] = {}
    for name in FILTER_FIGURES:
        done = run(
            fidelity_arguments(
                found,
                frames_dir,
                video,
                fps=fps,
                first_frame=first_frame,
                frames=frames,
                filter_name=name,
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        figures[name] = filter_figure(done.stderr, name)
    return Fidelity(
        psnr_db=figures["psnr"],
        ssim=figures["ssim"],
        first_frame=first_frame,
        frames=frames,
    )


def report(profile: DeliveryProfile, delivered: DeliveredVideo, failures: Sequence[str]) -> str:
    """One block naming the profile, what arrived, and every way it missed."""
    summary = (
        f"{profile.name}: {delivered.codec} {delivered.h264_profile}@{delivered.level} "
        f"{delivered.pixel_format} {delivered.width}x{delivered.height} "
        f"{delivered.fps:g} fps, {delivered.seconds:.3f} s, {delivered.bytes / 1e6:.1f} MB"
        f"{'' if delivered.faststart else ', no faststart'}"
    )
    lines = [summary]
    lines.extend(f"  FAIL {failure}" for failure in failures)
    if not failures:
        lines.append("  conforms")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument(
        "--profile",
        default=None,
        choices=sorted(PROFILES),
        help="the profile to check against; the video's receipt names it by default",
    )
    ap.add_argument("--frames", type=Path, help="the capture's retained PNGs, for fidelity")
    ap.add_argument("--from-frame", type=int, default=0, help="first frame of the window")
    ap.add_argument("--frames-window", type=int, default=900, help="frames in the window")
    o = ap.parse_args()

    if not o.video.exists():
        raise SystemExit(f"{o.video} does not exist")
    receipt_path = o.video.with_suffix(".receipt.json")
    receipt: dict[str, Any] = (
        json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.exists() else {}
    )
    name = o.profile or receipt.get("profile") or DEFAULT_PROFILE
    profile = PROFILES[name]
    delivered = measure(o.video)
    size = receipt.get("size") or [delivered.width, delivered.height]
    failures = conformance(
        profile,
        delivered,
        fps=int(receipt.get("fps", round(delivered.fps))),
        width=int(size[0]),
        height=int(size[1]),
        seconds=float(receipt.get("seconds", delivered.seconds)),
    )
    print(report(profile, delivered, failures))
    if o.frames is not None:
        measured = fidelity(
            o.frames,
            o.video,
            fps=int(receipt.get("fps", round(delivered.fps))),
            first_frame=o.from_frame,
            frames=o.frames_window,
        )
        print(
            f"  fidelity over {measured.frames} frames from {measured.first_frame}: "
            f"{measured.psnr_db:.2f} dB PSNR, {measured.ssim:.5f} SSIM"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
