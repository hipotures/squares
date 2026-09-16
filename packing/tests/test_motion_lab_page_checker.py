"""Failure controls for the Motion Lab browser checker and its committed report."""

from __future__ import annotations

import json
from copy import deepcopy
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from devtools import check_motion_lab_pages as checker
from sqpack.cli import validate


def _reports() -> tuple[list[checker.State], list[checker.State]]:
    exact = [
        {
            "step": "opened",
            "readouts": dict.fromkeys(checker.EXACT_READOUTS, "written"),
            "plane": "first drawing",
            "plane_visible": True,
        },
        {
            "step": "changed",
            "readouts": dict.fromkeys(checker.EXACT_READOUTS, "written"),
            "plane": "second drawing",
            "plane_visible": True,
        },
    ]
    general = [
        {
            "step": "opened",
            "readouts": {"diagnostics-value": "No conflicts"},
            "accepted": "first drawing",
            "accepted_visible": True,
        },
        {
            "step": "changed",
            "readouts": {"diagnostics-value": "No conflicts"},
            "accepted": "second drawing",
            "accepted_visible": True,
        },
    ]
    return exact, general


def test_an_invisible_drawing_fails_even_when_its_markup_changes() -> None:
    exact, general = _reports()
    exact[0]["plane_visible"] = False
    general[1]["accepted_visible"] = False

    assert checker.faults(exact, general, [], {"exact": True, "general": True}) == [
        "exact lab: the drawing is not visible",
        "general lab: the drawing is not visible",
    ]


def test_an_unpainted_drawing_fails_even_when_visible_and_its_markup_changes() -> None:
    exact, general = _reports()

    assert checker.faults(exact, general, [], {"exact": False, "general": False}) == [
        "exact lab: the drawing has no painted geometry",
        "general lab: the drawing has no painted geometry",
    ]


def test_a_live_negative_control_rejects_a_vacuous_paint_probe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inserted: list[str] = []

    class StyleStub:
        def evaluate(self, source: str) -> None:
            assert source == checker.REMOVE_ELEMENT

    class PageStub:
        def add_style_tag(self, *, content: str) -> StyleStub:
            inserted.append(content)
            return StyleStub()

    monkeypatch.setattr(
        checker,
        "_painted_geometry",
        lambda *_arguments: checker.PaintObservation(
            painted=True,
            restored=True,
            painted_pixels=checker.MIN_PAINTED_PIXELS,
            restoration_pixels=0,
        ),
    )

    fault = checker._negative_control_fault(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        PageStub(),  # type: ignore[arg-type]
        checker.EXACT_PAINT,
        name="opacity-zero",
        css=checker.EXACT_PAINT.opacity_zero_css,
    )

    assert fault == (
        "the paint check accepted its opacity-zero negative control: "
        f"{checker.MIN_PAINTED_PIXELS} materially changed pixels"
    )
    assert inserted == [checker.EXACT_PAINT.opacity_zero_css]


def _png(
    pixels: list[tuple[int, int, int]], *, size: tuple[int, int], compression: int
) -> bytes:
    image = Image.new("RGB", size)
    image.putdata(pixels)
    encoded = BytesIO()
    image.save(encoded, format="PNG", compress_level=compression)
    return encoded.getvalue()


def test_the_paint_oracle_compares_decoded_pixels_with_bounded_noise() -> None:
    width = checker.MIN_PAINTED_PIXELS + checker.MAX_RESTORATION_PIXELS + 1
    white = [(255, 255, 255)] * width
    baseline = _png(white, size=(width, 1), compression=0)
    reencoded = _png(white, size=(width, 1), compression=9)
    assert baseline != reencoded

    hidden_pixels = [(0, 0, 0)] * checker.MIN_PAINTED_PIXELS + white[
        checker.MIN_PAINTED_PIXELS :
    ]
    hidden = _png(hidden_pixels, size=(width, 1), compression=0)
    tolerated_pixels = white.copy()
    tolerated_pixels[: checker.MAX_RESTORATION_PIXELS] = [(0, 0, 0)] * (
        checker.MAX_RESTORATION_PIXELS
    )
    tolerated = _png(tolerated_pixels, size=(width, 1), compression=0)
    rejected_pixels = tolerated_pixels.copy()
    rejected_pixels[checker.MAX_RESTORATION_PIXELS] = (0, 0, 0)
    rejected = _png(rejected_pixels, size=(width, 1), compression=0)

    assert checker._paint_observation(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        baseline, hidden, reencoded
    ) == checker.PaintObservation(
        painted=True,
        restored=True,
        painted_pixels=checker.MIN_PAINTED_PIXELS,
        restoration_pixels=0,
    )
    assert checker._paint_observation(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        baseline, hidden, tolerated
    ).restored
    assert not checker._paint_observation(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        baseline, hidden, rejected
    ).restored
    assert not checker._paint_observation(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        baseline, reencoded, reencoded
    ).painted


def test_the_pixel_metric_has_an_exact_channel_boundary_and_fails_closed() -> None:
    baseline = _png([(100, 100, 100)], size=(1, 1), compression=0)
    accepted = _png(
        [(100 + checker.PIXEL_CHANNEL_TOLERANCE, 100, 100)],
        size=(1, 1),
        compression=0,
    )
    counted = _png(
        [(100 + checker.PIXEL_CHANNEL_TOLERANCE + 1, 100, 100)],
        size=(1, 1),
        compression=0,
    )
    wider = _png([(100, 100, 100)] * 2, size=(2, 1), compression=0)

    assert (
        checker._changed_pixels(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            baseline, accepted
        )
        == 0
    )
    assert (
        checker._changed_pixels(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            baseline, counted
        )
        == 1
    )
    assert (
        checker._changed_pixels(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
            baseline, wider
        )
        is None
    )
    assert checker._paint_observation(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        baseline, wider, wider
    ) == checker.PaintObservation(
        painted=False,
        restored=False,
        painted_pixels=None,
        restoration_pixels=None,
    )


def test_a_wrong_computation_fails_the_committed_report(tmp_path: Path) -> None:
    exact, general = _reports()
    expected: dict[str, Any] = {"exact": exact, "general": general}
    golden = tmp_path / "motion-lab-pages.json"
    golden.write_text(json.dumps(expected, indent=2, sort_keys=True), encoding="utf-8")
    actual = deepcopy(expected)
    actual["exact"][0]["readouts"]["contacts-value"] = "wrong contacts"

    found = checker._golden_faults(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        actual, golden
    )

    assert len(found) == 1
    assert "motion lab report differs from" in found[0]
    assert "wrong contacts" in found[0]


def test_the_committed_report_is_nonempty_and_covers_every_driven_state() -> None:
    report = json.loads(checker.GOLDEN_REPORT.read_text(encoding="utf-8"))
    assert len(report["exact"]) == 36
    assert len(report["general"]) == 12
    assert all("plane_visible" in state for state in report["exact"])
    assert all("accepted_visible" in state for state in report["general"])
    assert report["painted"] == {"exact": True, "general": True}


def test_a_diagnostic_report_cannot_overwrite_the_golden(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    golden = tmp_path / "motion-lab-pages.json"

    assert checker.main(["--golden", str(golden), "--report", str(golden)]) == 2
    assert "must not overwrite" in capsys.readouterr().err


def test_the_chromium_gate_compares_the_motion_labs_with_the_golden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[tuple[str, ...]] = []

    def record(_context: validate.Context, commands: Any, **_options: Any) -> str:
        captured.extend(tuple(command) for command in commands)
        return ""

    monkeypatch.setattr(validate, "_commands", record)
    validate._workbench_frontend(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        validate.Context(deep=False, strict=False, jobs=1, inner_jobs=1, environment={})
    )
    motion = next(
        command for command in captured if "devtools.check_motion_lab_pages" in command
    )
    assert motion[-2:] == (
        "--golden",
        "tests/golden/motion-lab-pages.json",
    )
