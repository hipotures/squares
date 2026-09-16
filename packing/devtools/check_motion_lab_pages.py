"""Drive both Motion Lab pages in Chromium and report what their controls draw.

The labs had no browser check: their tests read the rendered HTML and run the models in
Node, so nothing proved that a page's scripts run in a page. That mattered when the
scripts became module scripts (think-6o9n), which changes how a browser runs them. This
loads each page from a file, works its controls through Playwright's own input and locator
calls, and fails on an uncaught error, a console error, an unpainted primary drawing, or a
readout the page script never wrote. The paint check compares actual stage pixels with and
without the primary square layer, then proves itself against opacity-zero and transparent
paint controls. Every observation must match the committed golden report, so a model that
computes a different state fails even when it still draws. `--report` writes the observed
JSON for diagnosis.

The general lab's numerical run needs its loopback service, so only its editor is driven
here: selection, keyboard moves and rotations, snapping, and reset, all of which go through
the editor model the page script reads from `globalThis.MotionLabEditor`.

Usage, from `packing/`:
    uv run --frozen --all-extras --group dev python -m devtools.check_motion_lab_pages
    uv run --frozen --all-extras --group dev python -m devtools.check_motion_lab_pages \\
        --exact EXACT.html --general GENERAL.html --report REPORT.json \\
        --golden GOLDEN.json
"""

from __future__ import annotations

import argparse
import difflib
import io
import json
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from playwright.sync_api import ConsoleMessage, Error, Locator, Page, sync_playwright

from devtools.render_general_motion_lab import (
    DEFAULT_SEED,
    DEFAULT_SIDE,
    DEFAULT_SQUARE_COUNT,
    render_general_motion_lab,
)
from devtools.render_packing_motion_lab import render_motion_lab
from sqpack.probes import probe

GOLDEN_REPORT = Path(__file__).resolve().parents[1] / "tests/golden/motion-lab-pages.json"
PROBES = Path(__file__).resolve().parent / "probes"
REMOVE_ELEMENT = probe(PROBES, "check_motion_lab_pages/remove_element")

# Run 35075455272 showed that two Linux Chromium PNG encodings of the restored exact
# stage need not be byte-identical. Decoded-pixel measurements on both pages changed at
# least 176,572 pixels when the primary layer was removed, and zero for both live
# mutants. Ignore a small antialiasing-channel delta, require substantive painted area,
# and permit only a negligible restoration fringe.
PIXEL_CHANNEL_TOLERANCE = 8
MIN_PAINTED_PIXELS = 10_000
MAX_RESTORATION_PIXELS = 256

ImagePixels = NDArray[np.int16]

#: The exact lab's readouts, each written by the page script's first update.
EXACT_READOUTS = (
    "scene-value",
    "parameter-name",
    "parameter-value",
    "evidence-value",
    "source-value",
    "claim-value",
    "angle-value",
    "contacts-value",
    "stage-description",
    "motion-note",
    "live-region",
)
EXACT_TOGGLES = ("ids-toggle", "contacts-toggle", "trails-toggle", "tangent-toggle")
#: The one readout the exact lab's markup leaves empty. The golden below holds every readout;
#: this sentinel gives a direct diagnostic when the page script did not run at all.
EXACT_WRITTEN = ("angle-value",)

#: The general lab's setup readouts, written by `renderSetup` through the editor model.
GENERAL_READOUTS = (
    "run-readout-title",
    "mode-value",
    "groups-value",
    "diagnostics-value",
    "selection-value",
    "event-value",
    "live-region",
)

State = dict[str, Any]


class Painted(TypedDict):
    """Whether each page's representative primary geometry changes its stage pixels."""

    exact: bool
    general: bool


@dataclass(frozen=True)
class PaintObservation:
    """One stage differential and whether removing its fixture restored the baseline."""

    painted: bool
    restored: bool
    painted_pixels: int | None = None
    restoration_pixels: int | None = None


@dataclass(frozen=True)
class PaintProbe:
    """One SVG stage, its primary geometry, and the mutations that must blank it."""

    stage: str
    geometry: str
    hidden_css: str
    opacity_zero_css: str
    transparent_css: str


EXACT_PAINT = PaintProbe(
    stage="#motion-stage",
    geometry="#square-layer",
    hidden_css="#square-layer { opacity: 0 !important; }",
    opacity_zero_css=(
        "#math-plane, #label-layer, #obstruction-badge { opacity: 0 !important; }"
    ),
    transparent_css=(
        "#square-layer .square { fill: transparent !important; "
        "stroke: transparent !important; }"
    ),
)
GENERAL_PAINT = PaintProbe(
    stage="#free-stage",
    geometry="#accepted-layer",
    hidden_css="#accepted-layer { opacity: 0 !important; }",
    opacity_zero_css="#free-math-plane, #free-label-layer { opacity: 0 !important; }",
    transparent_css=(
        "#accepted-layer .editor-square { fill: transparent !important; "
        "stroke: transparent !important; }"
    ),
)


def _stage_pixels(stage: Locator) -> bytes:
    return stage.screenshot(animations="disabled", caret="hide", scale="css")


def _image_pixels(content: bytes) -> ImagePixels:
    with Image.open(io.BytesIO(content)) as image:
        return np.asarray(image.convert("RGB"), dtype=np.int16)


def _changed_pixels(left: bytes, right: bytes) -> int | None:
    """Count materially changed pixels, or refuse screenshots with different shapes."""
    left_pixels = _image_pixels(left)
    right_pixels = _image_pixels(right)
    if left_pixels.shape != right_pixels.shape:
        return None
    channel_delta = np.abs(left_pixels - right_pixels).max(axis=2)
    return int(np.count_nonzero(channel_delta > PIXEL_CHANNEL_TOLERANCE))


def _paint_observation(
    baseline: bytes, without_geometry: bytes, restored: bytes
) -> PaintObservation:
    painted_pixels = _changed_pixels(baseline, without_geometry)
    restoration_pixels = _changed_pixels(baseline, restored)
    return PaintObservation(
        painted=painted_pixels is not None and painted_pixels >= MIN_PAINTED_PIXELS,
        restored=(
            restoration_pixels is not None and restoration_pixels <= MAX_RESTORATION_PIXELS
        ),
        painted_pixels=painted_pixels,
        restoration_pixels=restoration_pixels,
    )


def _difference_detail(changed: int | None) -> str:
    if changed is None:
        return "different screenshot dimensions"
    return f"{changed} materially changed pixels"


def _painted_geometry(page: Page, paint: PaintProbe) -> PaintObservation:
    """Whether removing representative geometry changes the pixels of its SVG stage."""
    stage = page.locator(paint.stage)
    geometry = page.locator(paint.geometry)
    if stage.count() != 1 or geometry.count() != 1 or not stage.is_visible():
        return PaintObservation(painted=False, restored=True)
    baseline = _stage_pixels(stage)
    hidden_style = page.add_style_tag(content=paint.hidden_css)
    try:
        without_geometry = _stage_pixels(stage)
    finally:
        hidden_style.evaluate(REMOVE_ELEMENT)
    restored = _stage_pixels(stage)
    return _paint_observation(baseline, without_geometry, restored)


def _negative_control_fault(
    page: Page, paint: PaintProbe, *, name: str, css: str
) -> str | None:
    """Apply one live paint mutation and report an oracle that accepts it."""
    control_style = page.add_style_tag(content=css)
    try:
        observed = _painted_geometry(page, paint)
    finally:
        control_style.evaluate(REMOVE_ELEMENT)
    if not observed.restored:
        return (
            f"the paint check did not restore its {name} fixture: "
            f"{_difference_detail(observed.restoration_pixels)}"
        )
    if observed.painted:
        return (
            f"the paint check accepted its {name} negative control: "
            f"{_difference_detail(observed.painted_pixels)}"
        )
    return None


def _exact_state(page: Page, step: str) -> State:
    return {
        "step": step,
        "readouts": {name: page.locator(f"#{name}").text_content() for name in EXACT_READOUTS},
        "valuetext": page.locator("#parameter-input").get_attribute("aria-valuetext"),
        "plane": page.locator("#math-plane").inner_html(),
        "plane_visible": page.locator("#math-plane").is_visible(),
        "labels": page.locator("#label-layer").inner_html(),
        "branch_hidden": page.locator("#branch-panel").is_hidden(),
        "owner_disabled": page.locator("#owner-select").is_disabled(),
    }


def _options(page: Page, select: str) -> list[str]:
    return [
        option.get_attribute("value") or ""
        for option in page.locator(f"#{select} option").all()
    ]


def drive_exact(page: Page) -> list[State]:
    """Every motion and stratum at three path positions, every owner, the overlays on."""
    states = [_exact_state(page, "opened")]
    for toggle in EXACT_TOGGLES:
        page.locator(f"#{toggle}").check()
    states.append(_exact_state(page, "overlays on"))
    for motion in _options(page, "motion-select"):
        page.locator("#motion-select").select_option(motion)
        for stratum in _options(page, "stratum-select"):
            page.locator("#stratum-select").select_option(stratum)
            for position in ("0", "500", "1000"):
                page.locator("#parameter-input").fill(position)
                states.append(_exact_state(page, f"{motion} {stratum} at {position}"))
            if not page.locator("#owner-select").is_disabled():
                for owner in _options(page, "owner-select"):
                    page.locator("#owner-select").select_option(owner)
                    states.append(_exact_state(page, f"{motion} {stratum} owner {owner}"))
    page.locator("#restart-button").click()
    states.append(_exact_state(page, "restarted"))
    return states


def _general_state(page: Page, step: str) -> State:
    return {
        "step": step,
        "readouts": {
            name: page.locator(f"#{name}").text_content() for name in GENERAL_READOUTS
        },
        "accepted": page.locator("#accepted-layer").inner_html(),
        "accepted_visible": page.locator("#accepted-layer").is_visible(),
        "labels": page.locator("#free-label-layer").inner_html(),
        "rotate_disabled": page.locator("#rotate-left-button").is_disabled(),
    }


def drive_general(page: Page) -> list[State]:
    """Select a square, move and rotate it by keyboard and button, then snap and reset."""
    states = [_general_state(page, "opened")]
    stage = page.locator("#free-stage")
    # The square drawn last is the one on top, so a click at its centre reaches it.
    page.locator("#accepted-layer [data-square-id]").last.click()
    states.append(_general_state(page, "top square clicked"))
    # A key pressed on a square selects it: the stage's handler reads the event's target.
    square = page.locator('#accepted-layer [data-square-id="0"]').first
    for key in ("ArrowRight", "ArrowRight", "Shift+ArrowUp", "q", "e", "e"):
        square.press(key)
        states.append(_general_state(page, f"pressed {key} on square 0"))
    page.locator("#rotate-left-button").click()
    states.append(_general_state(page, "rotated left"))
    page.locator("#snapping-toggle").uncheck()
    for key in ("ArrowLeft", "ArrowDown"):
        stage.press(key)
        states.append(_general_state(page, f"unsnapped, pressed {key}"))
    page.locator("#reset-button").click()
    states.append(_general_state(page, "reset"))
    return states


def run_page(
    path: Path, drive: Callable[[Page], list[State]], paint: PaintProbe
) -> tuple[list[State], list[str], bool]:
    """Load one page, drive it, and return its states, errors, and paint verdict."""
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})

            def on_console(message: ConsoleMessage) -> None:
                if message.type == "error":
                    errors.append(f"console: {message.text}")

            def on_error(error: Error) -> None:
                errors.append(f"uncaught: {error.message}")

            page.on("console", on_console)
            page.on("pageerror", on_error)
            page.goto(path.resolve().as_uri(), wait_until="load")
            states = drive(page)
            observation = _painted_geometry(page, paint)
            if not observation.restored:
                errors.append(
                    "the paint check did not restore its positive fixture: "
                    f"{_difference_detail(observation.restoration_pixels)}"
                )
            for name, css in (
                ("opacity-zero", paint.opacity_zero_css),
                ("transparent-paint", paint.transparent_css),
            ):
                if control_fault := _negative_control_fault(page, paint, name=name, css=css):
                    errors.append(control_fault)
        finally:
            browser.close()
    return states, errors, observation.painted


def faults(
    exact: list[State], general: list[State], errors: list[str], painted: Painted
) -> list[str]:
    """What says a page script did not run, or ran and failed."""
    found = list(errors)
    opened = exact[0]["readouts"]
    found.extend(
        f"exact lab: #{name} was never written" for name in EXACT_WRITTEN if not opened[name]
    )
    if len({state["plane"] for state in exact}) < 2:
        found.append("exact lab: no control changed the drawing")
    if not all(state["plane_visible"] for state in exact):
        found.append("exact lab: the drawing is not visible")
    if not painted["exact"]:
        found.append("exact lab: the drawing has no painted geometry")
    if general[0]["readouts"]["diagnostics-value"] in {None, "", "Checking…"}:
        found.append("general lab: the setup diagnostics were never written")
    if len({state["accepted"] for state in general}) < 2:
        found.append("general lab: no edit changed the drawing")
    if not all(state["accepted_visible"] for state in general):
        found.append("general lab: the drawing is not visible")
    if not painted["general"]:
        found.append("general lab: the drawing has no painted geometry")
    return found


def _golden_faults(report: State, golden_path: Path) -> list[str]:
    """Describe a missing, invalid, or behaviorally different committed report."""
    try:
        expected = json.loads(golden_path.read_text(encoding="utf-8"))
    except OSError as error:
        return [f"motion lab golden is unreadable: {golden_path}: {error}"]
    except json.JSONDecodeError as error:
        return [f"motion lab golden is invalid JSON: {golden_path}: {error}"]
    if expected == report:
        return []
    expected_lines = json.dumps(expected, indent=2, sort_keys=True).splitlines()
    actual_lines = json.dumps(report, indent=2, sort_keys=True).splitlines()
    preview = "\n".join(
        islice(
            difflib.unified_diff(
                expected_lines,
                actual_lines,
                fromfile=str(golden_path),
                tofile="actual motion lab report",
                lineterm="",
            ),
            24,
        )
    )
    return [f"motion lab report differs from {golden_path}:\n{preview}"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exact", type=Path, help="the exact n=5 lab; rendered fresh if omitted"
    )
    parser.add_argument(
        "--general", type=Path, help="the general lab; rendered fresh if omitted"
    )
    parser.add_argument("--report", type=Path, help="write every observation here as JSON")
    parser.add_argument(
        "--golden",
        type=Path,
        default=GOLDEN_REPORT,
        help="committed report every observation must match",
    )
    arguments = parser.parse_args(argv)
    if (
        arguments.report is not None
        and arguments.report.resolve() == arguments.golden.resolve()
    ):
        print("FAIL: --report must not overwrite the --golden evidence", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="squares-motion-lab-") as scratch:
        exact_page = arguments.exact
        if exact_page is None:
            exact_page = Path(scratch) / "exact.html"
            exact_page.write_text(render_motion_lab(), encoding="utf-8")
        general_page = arguments.general
        if general_page is None:
            general_page = Path(scratch) / "general.html"
            general_page.write_text(
                render_general_motion_lab(
                    n=DEFAULT_SQUARE_COUNT, seed=DEFAULT_SEED, side=DEFAULT_SIDE
                ),
                encoding="utf-8",
            )
        exact, exact_errors, exact_painted = run_page(exact_page, drive_exact, EXACT_PAINT)
        general, general_errors, general_painted = run_page(
            general_page, drive_general, GENERAL_PAINT
        )
    painted: Painted = {"exact": exact_painted, "general": general_painted}
    report = {"exact": exact, "general": general, "painted": painted}
    if arguments.report is not None:
        arguments.report.write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
    problems = faults(
        exact,
        general,
        [f"exact lab {error}" for error in exact_errors]
        + [f"general lab {error}" for error in general_errors],
        painted,
    )
    problems.extend(_golden_faults(report, arguments.golden))
    if problems:
        print("FAIL:\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    print(
        f"OK: exact lab drove {len(exact)} states and the general lab {len(general)}, "
        "with visible drawings matching the committed report"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
