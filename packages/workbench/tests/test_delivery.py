"""Controls for the delivery profiles: what is asked of the encoder, and what is checked.

`conformance` and `parse_probe` are pure functions over plain data, so the cases here run
with no ffmpeg, no browser and no fixture video: a conforming measurement, then one
constraint broken at a time, then the ceilings present under `social` and absent under
`archive`.

What these cannot establish is that `parse_probe` reads what `ffprobe` actually emits, so
the recorded payload below is a real one, taken from `ffprobe -show_streams -show_format
-of json` over a capture of the workbench page. Beyond that, every capture measures its own
output and refuses to write a receipt for a file that does not conform, so a parse that
stopped working stops the next cut rather than passing quietly.
"""

from __future__ import annotations

import json
from itertools import pairwise
from pathlib import Path
from textwrap import dedent

import pytest

from workbench_tools import delivery
from workbench_tools.delivery import PROFILES, DeliveredVideo

STAGE = (1920, 1080)

#: Trimmed from a real `ffprobe` run over `ascent-1-100-30fps.mp4`, keeping the keys the
#: parse reads and one it must ignore.
PROBE_PAYLOAD = dedent("""
    {
      "streams": [
        {
          "codec_type": "video",
          "codec_name": "h264",
          "profile": "High",
          "level": 40,
          "pix_fmt": "yuv420p",
          "width": 1920,
          "height": 1080,
          "r_frame_rate": "30/1",
          "duration": "111.400000",
          "nb_frames": "3342"
        }
      ],
      "format": {"duration": "111.400000", "size": "11659739", "nb_streams": "1"}
    }
    """).strip()


def _delivered(**overrides: object) -> DeliveredVideo:
    fields: dict[str, object] = {
        "codec": "h264",
        "h264_profile": "High",
        "level": 40,
        "pixel_format": "yuv420p",
        "width": STAGE[0],
        "height": STAGE[1],
        "fps": 30.0,
        "seconds": 111.4,
        "bytes": 11_659_739,
        "faststart": True,
    }
    fields.update(overrides)
    return DeliveredVideo(**fields)  # pyright: ignore[reportArgumentType]


def _failures(profile_name: str, **overrides: object) -> list[str]:
    """Conformance of a measurement against a capture that asked for exactly it.

    The receipt's duration follows the measured one, so overriding `seconds` moves the file
    and the run it claims to hold together and tests only the ceiling.
    """
    delivered = _delivered(**overrides)
    return delivery.conformance(
        PROFILES[profile_name],
        delivered,
        fps=30,
        width=STAGE[0],
        height=STAGE[1],
        seconds=float(overrides.get("seconds", 111.4)),  # pyright: ignore[reportArgumentType]
    )


# ------------------------------------------------------------------------------- the profiles


def test_every_profile_declares_a_level_the_frame_size_can_hold() -> None:
    # Level 4.0's decoded-picture-buffer admits 1080p; a profile that named a lower one
    # would encode files no player would accept, and nothing else here would say so.
    for profile in PROFILES.values():
        assert profile.level_tag >= 40
        assert profile.pixel_format == "yuv420p"


def test_the_encoder_is_built_from_the_profile_and_carries_the_honesty_statement(
    tmp_path: Path,
) -> None:
    out = tmp_path / "ascent.partial.mp4"
    arguments = delivery.encode_arguments(
        PROFILES["social"],
        "ffmpeg",
        tmp_path / "frames",
        30,
        out,
        page_sha256="ab" * 32,
        title="n = 2 to 3",
        comment="transitions are not packings.",
    )
    assert arguments[-1] == str(out)
    assert "-y" not in arguments
    flags = list(pairwise(arguments))
    assert ("-crf", "18") in flags
    assert ("-preset", "slow") in flags
    assert ("-profile:v", "high") in flags
    assert ("-level", "4.0") in flags
    assert ("-pix_fmt", "yuv420p") in flags
    assert ("-movflags", "+faststart") in flags
    assert ("-i", str(tmp_path / "frames" / delivery.FRAME_PATTERN)) in flags
    comments = [v for flag, v in flags if flag == "-metadata" and v.startswith("comment=")]
    assert len(comments) == 1
    assert "not packings" in comments[0]
    assert "ab" * 32 in comments[0]


# --------------------------------------------------------------------------- what ffprobe said


def test_a_probe_payload_becomes_the_stream_it_describes() -> None:
    delivered = delivery.parse_probe(PROBE_PAYLOAD, size=11_659_739, has_faststart=True)
    assert delivered == _delivered()


def test_a_stream_without_its_own_duration_falls_back_to_the_container() -> None:
    payload = json.loads(PROBE_PAYLOAD)
    del payload["streams"][0]["duration"]
    assert (
        delivery.parse_probe(json.dumps(payload), size=1, has_faststart=True).seconds == 111.4
    )


def test_a_payload_with_no_video_stream_or_no_duration_anywhere_is_refused() -> None:
    payload = json.loads(PROBE_PAYLOAD)
    payload["streams"][0]["codec_type"] = "audio"
    with pytest.raises(ValueError, match="no video stream"):
        delivery.parse_probe(json.dumps(payload), size=1, has_faststart=True)
    payload = json.loads(PROBE_PAYLOAD)
    del payload["streams"][0]["duration"]
    del payload["format"]["duration"]
    with pytest.raises(ValueError, match="duration"):
        delivery.parse_probe(json.dumps(payload), size=1, has_faststart=True)


# --------------------------------------------------------------------------------- conformance


def test_the_file_the_capture_produced_meets_both_profiles() -> None:
    assert _failures("archive") == []
    assert _failures("social") == []


def test_each_stream_constraint_fails_on_its_own_and_says_which_value_was_which() -> None:
    broken = {
        "codec": ("codec", {"codec": "hevc"}),
        "h264 profile": ("h264 profile", {"h264_profile": "Main"}),
        # The defect this pins: left alone, x264 at `-preset slow` keeps five reference
        # frames and tags the file 5.0, which is what the profile exists to stop.
        "level": ("level", {"level": 50}),
        "pixel format": ("pixel format", {"pixel_format": "yuv444p"}),
        "frame size": ("frame size", {"width": 1280, "height": 720}),
        "frame rate": ("frame rate", {"fps": 25.0}),
        "faststart": ("faststart", {"faststart": False}),
    }
    for constraint, overrides in broken.values():
        failures = _failures("archive", **overrides)
        assert len(failures) == 1, failures
        assert failures[0].startswith(f"{constraint}: declared ")


def _duration_failures(measured: float) -> list[str]:
    """Conformance of a file whose length disagrees with the run the receipt describes."""
    return delivery.conformance(
        PROFILES["archive"],
        _delivered(seconds=measured),
        fps=30,
        width=STAGE[0],
        height=STAGE[1],
        seconds=111.4,
    )


def test_a_duration_more_than_one_frame_from_the_receipt_is_a_failure() -> None:
    # The container rounds to its timescale, so a fraction of a frame is the file being
    # written; a whole frame is the file not holding the run the receipt describes.
    assert _duration_failures(111.4 + 0.9 / 30) == []
    off = _duration_failures(111.4 + 2.0 / 30)
    assert len(off) == 1
    assert off[0].startswith("duration: declared ")
    assert "frames apart" in off[0]


def test_the_ceilings_bind_under_social_and_are_absent_under_archive() -> None:
    # The whole ascent: an archive master at any length, and past what an X post takes.
    long_run = {"seconds": 382.733}
    assert _failures("archive", **long_run) == []
    over = _failures("social", **long_run)
    assert len(over) == 1
    assert over[0].startswith("social duration ceiling: declared 140.0")

    heavy = {"bytes": 600 * 1000 * 1000}
    assert _failures("archive", **heavy) == []
    assert any(f.startswith("social byte ceiling") for f in _failures("social", **heavy))


def test_a_report_names_every_failure_and_says_so_when_there_are_none() -> None:
    conforming = delivery.report(PROFILES["social"], _delivered(), [])
    assert conforming.endswith("conforms")
    failing = delivery.report(
        PROFILES["social"], _delivered(level=50), _failures("social", level=50)
    )
    assert "FAIL level: declared 40, measured 50" in failing


# ------------------------------------------------------------------------------------ fidelity


def test_the_fidelity_command_puts_each_option_on_the_side_of_i_it_belongs_to(
    tmp_path: Path,
) -> None:
    # The defect this pins: a frame count before the second `-i` is read as an input option
    # on the video, and ffmpeg refuses the command outright rather than measuring anything.
    arguments = delivery.fidelity_arguments(
        "ffmpeg",
        tmp_path / "frames",
        tmp_path / "ascent.mp4",
        fps=30,
        first_frame=9900,
        frames=600,
        filter_name="psnr",
    )
    inputs = [i for i, a in enumerate(arguments) if a == "-i"]
    assert len(inputs) == 2
    for option in ("-start_number", "-framerate"):
        assert arguments.index(option) < inputs[0]
    assert inputs[0] < arguments.index("-ss") < inputs[1]
    assert arguments.index("-frames:v") > inputs[1]
    # The video is seeked to where the PNG window starts, or the two inputs are different
    # instants and the figure means nothing.
    assert arguments[arguments.index("-ss") + 1] == f"{9900 / 30:.6f}"
    # Quieting ffmpeg would quiet the summary line this command exists to read.
    assert ("-v", "info") in list(pairwise(arguments))


def test_a_fidelity_window_must_hold_at_least_one_frame(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one frame"):
        delivery.fidelity(tmp_path, tmp_path / "v.mp4", fps=30, first_frame=0, frames=0)


def test_a_filter_that_reported_no_figure_is_an_error_rather_than_a_zero() -> None:
    # A regex that quietly missed would report perfect fidelity as 0.0 dB or, worse, as a
    # number from the wrong filter. The measurement fails instead.
    assert delivery.filter_figure("PSNR ... average:47.31 min:40.02", "psnr") == 47.31
    assert delivery.filter_figure("SSIM Y:0.99 U:0.99 All:0.99412 (22.3)", "ssim") == 0.99412
    with pytest.raises(ValueError, match="no psnr figure"):
        delivery.filter_figure("ffmpeg said nothing useful", "psnr")


def test_faststart_is_read_from_the_bytes_rather_than_taken_on_trust(tmp_path: Path) -> None:
    front = tmp_path / "front.mp4"
    front.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00\x00\x00\x08moov" + b"\x00" * 64)
    assert delivery.faststart(front)
    back = tmp_path / "back.mp4"
    back.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 8192 + b"moov")
    assert not delivery.faststart(back)
