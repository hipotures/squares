"""Hold every workbench view to one page structure, measured in Chromium.

The stylesheet's tokens say what the layout should be; this measures what it is. At each
declared viewport, in each view a reader reaches by ordinary navigation -- Animate on a bound
first proved here, Animate with nothing open, the animation studio, Pack and Search -- the
`design/layout-metrics` probe reads the page's boxes, and `findings` requires:

- **no horizontal overflow**, of the document or of the controls' column;
- **one gutter**: the column's inline padding on both sides is `--layout-gutter`;
- **shared edges**: every top-level block in the column starts at the column's left content
  edge and ends at its right one, whatever the mode;
- **one stack gap**: consecutive blocks, and consecutive panels on one line of a row of
  panels, are `--layout-stack-gap` apart, no block is drawn empty (which would double the gap
  around it), and the last panel on each line ends at the row's right edge;
- **one control height per kind**: every button, select, number and text field and chip is
  `--control-height`, every tab is `--tab-height`, every segment of a group has one height, and
  a segmented group is one control tall -- or, where a narrow window wraps it, a whole number of
  segments tall inside its border;
- **no overlapping panels**;
- on the stage, **OPEN only when something is open**, and **one badge type**: every badge
  label, `new result` included, in the same family, size and weight, each in the colour its
  badge calls for -- the star's scarlet for `new result`, the label grey for every other (the
  owner, 2026-09-17);
- on the stage, **one frame**: the catalogue's box, the trace of where it just was and the
  container Pack and the animation studio draw are all `--scene-frame-width` wide, and each is
  drawn in the colour its state calls for -- the best known side's green where the box locks
  there, the frames' grey where it does not and for the container, the lightest grey for the
  trace (the owner, 2026-09-17);
- on the stage, **the attribution** starts at the legend's left edge, within
  `ATTRIBUTION_SLACK` stage pixels, and stands just under it, its ink within
  `ATTRIBUTION_LEAD` of the legend's foot (the owner, 2026-09-21); and it is drawn over nothing,
  including in Pack and the studio, which do not show the legend and center their drawing.

`findings`, `facts_findings`, `frames_findings` and `attribution_findings` are pure functions of
the probe's output, so `tests/test_check_layout.py` proves each rule refuses a page that breaks
it without a browser. One rule cannot be: `_painted` reads the pixels once, at the narrowest
viewport, because an overlay Chromium has left unpainted still reports every box correctly.

`check_open` runs the views in a page a caller already has open, which is how `check_frontend`
adds this to a browser session it has already paid for; `check` opens its own. From `packing/`::

    uv run --frozen --all-extras --group dev python -m workbench_tools.check_layout \\
        [--page PAGE]
"""

from __future__ import annotations

import argparse
import io
import itertools
import os
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from playwright.sync_api import FloatRect, Page, sync_playwright

from workbench_tools.build_site import build
from workbench_tools.probes import probe

#: The viewports every view is held at: a laptop, a small laptop and a phone.
VIEWPORTS: tuple[tuple[int, int], ...] = ((1440, 900), (1024, 768), (390, 844))

#: Rounding slack, in CSS pixels: boxes land on device-pixel fractions.
SLACK = 0.6

#: Control kinds held to `--control-height`; tabs are held to `--tab-height`.
AT_CONTROL_HEIGHT = frozenset({"button", "select", "input-number", "input-text", "chip"})

#: A bound first proved here (n = 18) and an n with nothing open (n = 16).
#: It was n = 17 until T-032 adopted an external certificate there, which is exactly the
#: fact the star reports; the six that still qualify are n = 11, 12, 18, 19, 20 and 21.
STAR_N = 18
OPEN_NONE_N = 16
#: The step the one moving view is paused in. At rest the box is locked at the best known side
#: and drawn green, so a step on its way is the only place the frames' grey is drawn.
MOVING_N = 11
NEW_RESULT = "new result"

#: How far the attribution may sit from what it is set against, in stage pixels. The stage is a
#: 1920 x 1080 poster drawn at `--stage-scale`, so this is one pixel of the poster at every
#: window size rather than one device pixel at some.
ATTRIBUTION_SLACK = 1.0

#: How far below the legend's foot the attribution's ink may start and still stand just under
#: it, in stage pixels: one line of the legend's own 22 px type.
ATTRIBUTION_LEAD = 22.0

Metrics = Mapping[str, Any]


def _px(value: str | None) -> float | None:
    if value is None or not value.endswith("px"):
        return None
    return float(value[:-2])


def _near(a: float, b: float) -> bool:
    return abs(a - b) <= SLACK


def _overflow(m: Metrics) -> list[str]:
    found = []
    if m["documentWidth"] > m["viewport"]["width"] + SLACK:
        found.append(
            f"the page is {m['documentWidth']} px wide in a {m['viewport']['width']} window"
        )
    controls = m["controls"]
    if controls["scrollWidth"] > controls["clientWidth"] + SLACK:
        found.append(
            f"the controls scroll sideways: {controls['scrollWidth']} px of content in "
            f"{controls['clientWidth']}"
        )
    return found


def _edges(m: Metrics) -> list[str]:
    found = []
    controls, tokens = m["controls"], m["tokens"]
    gutter, stack = _px(tokens.get("gutter")), _px(tokens.get("stack"))
    if gutter is None or stack is None:
        found.append(
            f"the page declares no pixel --layout-gutter or --layout-stack-gap: {tokens}"
        )
    if not _near(controls["paddingLeft"], controls["paddingRight"]):
        found.append(
            f"the column's gutters differ: {controls['paddingLeft']} left, "
            f"{controls['paddingRight']} right"
        )
    found.extend(
        f"the column's {side} is {controls[side]}, not the {gutter} px gutter"
        for side in ("paddingLeft", "paddingRight")
        if gutter is not None and not _near(controls[side], gutter)
    )
    left = controls["left"] + controls["borderLeft"] + controls["paddingLeft"]
    right = controls["left"] + controls["borderLeft"] + controls["clientWidth"]
    right -= controls["paddingRight"]
    found.extend(
        f"{block['name']} spans {block['left']}..{block['right']}, not the column's "
        f"{left:.2f}..{right:.2f}"
        for block in m["blocks"]
        if not (_near(block["left"], left) and _near(block["right"], right))
    )
    # An empty block is still a flex item, so it doubles the gap around it without a gap of its
    # own ever reading wrong.
    found.extend(
        f"{block['name']} is drawn empty, and doubles the stack gap around it"
        for block in m["blocks"]
        if block["bottom"] - block["top"] <= SLACK
    )
    gaps: list[tuple[str, float]] = [
        (f"{above['name']} and {below['name']}", below["top"] - above["bottom"])
        for above, below in itertools.pairwise(m["blocks"])
    ]
    for row in m["rows"]:
        lines: dict[float, list[Mapping[str, Any]]] = {}
        for panel in row["panels"]:
            lines.setdefault(round(panel["top"]), []).append(panel)
        for line in lines.values():
            ordered = sorted(line, key=lambda panel: panel["left"])
            gaps.extend(
                (
                    f"{before['name']} and {after['name']} in {row['name']}",
                    after["left"] - before["right"],
                )
                for before, after in itertools.pairwise(ordered)
            )
            last = ordered[-1] if ordered else None
            if last is not None and not _near(last["right"], row["right"]):
                found.append(
                    f"{row['name']}'s line ends at {last['right']} ({last['name']}), "
                    f"short of the row's edge at {row['right']}"
                )
    wanted = stack if stack is not None else (gaps[0][1] if gaps else None)
    found.extend(
        f"{between} are {gap:.2f} apart, not {wanted:.2f}"
        for between, gap in gaps
        if wanted is not None and not _near(gap, wanted)
    )
    return found


def _controls(m: Metrics) -> list[str]:
    found = []
    control, tab = _px(m["tokens"].get("control")), _px(m["tokens"].get("tab"))
    if control is None or tab is None:
        found.append(
            f"the page declares no pixel --control-height or --tab-height: {m['tokens']}"
        )
    heights: dict[str, set[float]] = {}
    for item in m["controlsFound"]:
        heights.setdefault(item["kind"], set()).add(round(item["height"], 1))
        wanted = (
            control
            if item["kind"] in AT_CONTROL_HEIGHT
            else tab
            if item["kind"] == "tab"
            else None
        )
        if wanted is not None and not _near(item["height"], wanted):
            found.append(
                f"{item['kind']} {item['name']} is {item['height']} tall, not {wanted}"
            )
    found.extend(
        f"{kind} controls come in {len(values)} heights: {sorted(values)}"
        for kind, values in sorted(heights.items())
        if kind != "segmented" and max(values) - min(values) > SLACK
    )
    same = {
        kind: min(values)
        for kind, values in heights.items()
        if kind in AT_CONTROL_HEIGHT and max(values) - min(values) <= SLACK
    }
    if control is None and len(set(map(round, same.values()))) > 1:
        found.append(
            f"buttons, fields and chips are not one height: {dict(sorted(same.items()))}"
        )
    segments = heights.get("segment", set())
    height = control if control is not None else same.get("button")
    if segments and height is not None and max(segments) - min(segments) <= SLACK:
        segment = min(segments)
        border = (height - segment) / 2
        for item in m["controlsFound"]:
            if item["kind"] != "segmented":
                continue
            lines = (item["height"] - 2 * border) / segment
            if round(lines) < 1 or not _near(
                round(lines) * segment + 2 * border, item["height"]
            ):
                found.append(
                    f"segmented {item['name']} is {item['height']} tall, not a whole number of "
                    f"{segment} px segments inside a {height} px control"
                )
    return found


def _overlaps(m: Metrics) -> list[str]:
    found = []
    for a, b in itertools.combinations(m["panels"], 2):
        width = min(a["right"], b["right"]) - max(a["left"], b["left"])
        height = min(a["bottom"], b["bottom"]) - max(a["top"], b["top"])
        nested = all(
            (a[k] <= b[k] if k in ("left", "top") else a[k] >= b[k])
            for k in ("left", "top", "right", "bottom")
        ) or all(
            (b[k] <= a[k] if k in ("left", "top") else b[k] >= a[k])
            for k in ("left", "top", "right", "bottom")
        )
        if width > SLACK and height > SLACK and not nested:
            found.append(f"{a['name']} and {b['name']} overlap by {width:.1f} x {height:.1f}")
    return found


def facts_findings(layer: Metrics, *, star: bool | None = None) -> list[str]:
    """The stage panel's rules for one facts layer; `star` says whether `new result` is due."""
    found = []
    heads = [head.strip().lower() for head in layer["heads"]]
    if ("open" in heads) != (layer["openItems"] > 0):
        found.append(
            f"OPEN is {'headed' if 'open' in heads else 'not headed'} with "
            f"{layer['openItems']} open items"
        )
    badges = layer["badges"]
    types = {(b["family"], b["size"], b["weight"]) for b in badges}
    if len(types) > 1:
        found.append(
            f"the badge labels are set in {len(types)} different types: {sorted(types)}"
        )
    # One type, two colours: `new result` is the star's scarlet and every other badge the label
    # grey, which is the one thing that tells the row's one new claim from its standing ones.
    colours = layer["colours"]
    for badge in badges:
        starred = badge["text"] == NEW_RESULT
        wanted = colours["starred"] if starred else colours["label"]
        if badge["color"] != wanted:
            role = "the star's scarlet" if starred else "the label grey"
            found.append(
                f"the `{badge['text']}` label is {badge['color']}, not {role} {wanted}"
            )
    new = [b for b in badges if b["text"] == NEW_RESULT]
    if star is True and not (len(new) == 1 and "badge-star" in (new[0]["icon"] or "").split()):
        found.append(f"a bound first proved here has no `{NEW_RESULT}` star badge: {badges}")
    if star is False and new:
        found.append(f"`{NEW_RESULT}` is drawn where no bound was first proved: {badges}")
    return found


def frames_findings(frames: Metrics) -> list[str]:
    """Every way the stage's outer container borders break the one-frame rule.

    Three elements draw one: the catalogue's box, the trace of where it just was under it, and
    the container Pack and the animation studio draw. All three are one width, and the colour
    is the only thing that changes -- the box is the best known side's green where it locks
    there and the frames' grey on its way, the trace is the lightest grey the page draws a line
    in, and the container is the frames' grey. Widths are read on all three whether or not they
    are drawn, because a hidden element still computes one; colours only where they are drawn.
    """
    found = []
    tokens = frames["tokens"]
    width = _px(tokens.get("width"))
    if width is None:
        found.append(f"the page declares no pixel --scene-frame-width: {tokens}")
    parts = {name: frames[name] for name in ("container", "box", "trace")}
    for name, part in parts.items():
        measured = _px(part["strokeWidth"])
        if width is None or measured is None or not _near(measured, width):
            found.append(f"the {name} frame is {part['strokeWidth']} wide, not {width} px")
    box = parts["box"]
    if box["shown"]:
        wanted = tokens["locked"] if box["locked"] else tokens["frame"]
        role = "the best known side's green" if box["locked"] else "the frames' grey"
        if box["stroke"] != wanted:
            found.append(f"the box is {box['stroke']}, not {role} {wanted}")
    if parts["trace"]["shown"] and parts["trace"]["stroke"] != tokens["trace"]:
        found.append(
            f"the trace is {parts['trace']['stroke']}, not the lightest grey {tokens['trace']}"
        )
    if parts["container"]["shown"] and parts["container"]["stroke"] != tokens["frame"]:
        found.append(
            f"the container is {parts['container']['stroke']}, not the frames' grey "
            f"{tokens['frame']}"
        )
    return found


def attribution_findings(attribution: Metrics, *, aligned: bool) -> list[str]:
    """Every way the stage's attribution sits wrong; `aligned` says what it is set against.

    The repository's address starts at the legend's left edge and stands just under it, both
    read off what is drawn. Pack and the animation studio do not show the legend, so there
    `aligned` is false and only that it is drawn and what it clears are checked.
    """
    found = []
    if not (attribution["placed"] and attribution["shown"]):
        return ["the stage's attribution is not drawn"]
    # The start above is read in the overlay's own units, which are stage pixels only because
    # it is a 1920 x 1080 box over a 1920 x 1080 viewBox. That is measured, not assumed.
    poster = attribution["frame"]
    if not (
        _near(poster["left"], 0)
        and _near(poster["top"], 0)
        and _near(poster["right"], 1920)
        and _near(poster["bottom"], 1080)
    ):
        found.append(f"the attribution's overlay is not the stage's own box: {poster}")
    legend = attribution["legend"]
    ink = attribution["ink"]
    if aligned:
        start = attribution["left"]
        if legend is None or start is None:
            found.append(
                f"the attribution cannot be measured against the legend: starts at {start}, "
                f"legend {legend}"
            )
        else:
            if abs(start - legend["left"]) > ATTRIBUTION_SLACK:
                found.append(
                    f"the attribution starts at {start:.2f}, {abs(start - legend['left']):.2f} "
                    f"stage px from the legend's left edge at {legend['left']:.2f}"
                )
            lead = ink["top"] - legend["bottom"]
            if not 0 < lead <= ATTRIBUTION_LEAD:
                found.append(
                    f"the attribution's ink starts {lead:.2f} stage px below the legend's "
                    f"foot, not just under it (0 to {ATTRIBUTION_LEAD:.0f})"
                )
    for other in attribution["obstacles"]:
        width = min(ink["right"], other["right"]) - max(ink["left"], other["left"])
        height = min(ink["bottom"], other["bottom"]) - max(ink["top"], other["top"])
        if width > SLACK and height > SLACK:
            found.append(
                f"the attribution is drawn over {other['name']} by {width:.1f} x {height:.1f}"
            )
    return found


#: The sum of an RGB pixel's channels under which it counts as ink rather than paper. White is
#: 765 and the attribution is set in the scene's ink, far darker, so a region of paper alone
#: never reaches it.
INK = 720


def _painted(page: Page, attribution: Metrics) -> list[str]:
    """The attribution is painted, not merely laid out.

    Chromium leaves this nested SVG unpainted when the transform above it changes: narrowed
    through the review viewports to 390 px, the text vanished from the picture while every box
    it reports stayed right (measured 2026-09-17). The page answers by rewriting the two
    attributes it is placed by whenever the stage's scale moves, and nothing in the DOM shows
    the difference, so this reads the pixels instead, once, at the narrowest viewport a sweep
    ends on.
    """
    screen = attribution["screen"]
    if screen["width"] <= 0 or screen["height"] <= 0:
        return [f"the attribution has no box to photograph: {screen}"]
    clip: FloatRect = {
        "x": max(0.0, float(screen["x"]) - 2),
        "y": max(0.0, float(screen["y"]) - 2),
        "width": float(screen["width"]) + 4,
        "height": float(screen["height"]) + 4,
    }
    image = np.asarray(Image.open(io.BytesIO(page.screenshot(clip=clip))).convert("RGB"))
    darkest = int(image.astype(int).sum(axis=2).min())
    if darkest > INK:
        return [
            (
                f"the attribution is laid out at {clip} but nothing is painted there "
                f"(darkest pixel {darkest} of 765)"
            )
        ]
    return []


def findings(m: Metrics) -> list[str]:
    """Every way one measured page breaks the layout rules."""
    return [*_overflow(m), *_edges(m), *_controls(m), *_overlaps(m)]


def _api(page: Page, *calls: list[Any]) -> Any:
    return page.evaluate(probe("api/apply"), {"calls": list(calls)})


def _stage_n(n: int) -> Callable[[Page], None]:
    """Animate paused at the start of the step into n + 1, so the first facts layer is n's."""

    def drive(page: Page) -> None:
        if _api(page, ["mode"]) != "animate":
            page.locator("#mode-animate").click()
        _api(page, ["pause"], ["setStepN", n + 1], ["seek", 0])

    return drive


def _moving(n: int) -> Callable[[Page], None]:
    """Animate paused in the step into n where the container has just finished growing.

    The box is on its way rather than resting at the best known side, so this is the one view
    that draws it in the frames' grey; everywhere else it is locked and green.
    """

    def drive(page: Page) -> None:
        if _api(page, ["mode"]) != "animate":
            page.locator("#mode-animate").click()
        schedule = _api(page, ["pause"], ["setStepN", n], ["schedule"])
        _api(page, ["seek", schedule["containerEnd"]], ["pause"])

    return drive


def _studio(page: Page) -> None:
    _stage_n(STAR_N)(page)
    page.locator("#animation-example").click()


def _leave_studio(page: Page) -> None:
    page.locator("#animation-catalogue").click()


#: The views, each with how to reach it and how to leave it, the facts it must show, and whether
#: it shows the legend the attribution is set against.
VIEWS: tuple[
    tuple[str, Callable[[Page], None], Callable[[Page], None] | None, bool | None, bool], ...
] = (
    (f"animate at n = {STAR_N}", _stage_n(STAR_N), None, True, True),
    (f"animate at n = {OPEN_NONE_N}", _stage_n(OPEN_NONE_N), None, False, True),
    (f"animate mid-step into n = {MOVING_N}", _moving(MOVING_N), None, None, True),
    ("the animation studio", _studio, _leave_studio, None, False),
    ("pack", lambda page: page.locator("#mode-pack").click(), None, None, False),
    ("search", lambda page: page.locator("#mode-search").click(), None, None, False),
)


def check_open(page: Page, viewports: Sequence[tuple[int, int]] = VIEWPORTS) -> str:
    """Measure every view at every viewport in an open page; raise with every finding.

    Leaves the page in Animate at its starting viewport.
    """
    started = time.perf_counter()
    original = page.viewport_size
    failures: list[str] = []
    measured = 0
    #: Whether the box was seen locked and seen on its way. Its two colours are one rule, and a
    #: sweep that only ever saw it at rest would pass without the frames' grey being drawn once.
    locks: set[bool] = set()
    for label, enter, leave, star, aligned in VIEWS:
        enter(page)
        for width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            page.evaluate(probe("design/frames"))
            metrics = page.evaluate(probe("design/layout-metrics"))
            measured += 1
            found = findings(metrics)
            if star is not None:
                if metrics["facts"] is None:
                    found.append("the stage's facts panel is not drawn")
                else:
                    found.extend(facts_findings(metrics["facts"]["facts-a"], star=star))
            if metrics["frames"] is not None:
                found.extend(frames_findings(metrics["frames"]))
                if metrics["frames"]["box"]["shown"]:
                    locks.add(bool(metrics["frames"]["box"]["locked"]))
            if metrics["attribution"] is not None:
                found.extend(attribution_findings(metrics["attribution"], aligned=aligned))
            failures.extend(f"{label} at {width} x {height}: {item}" for item in found)
        if leave is not None:
            leave(page)
    if locks != {True, False}:
        failures.append(
            f"the sweep never saw the box both locked and on its way, so only one of its two "
            f"colours was measured: locked states seen {sorted(locks)}"
        )
    page.locator("#mode-animate").click()
    # The stage at its smallest, having been resized through every viewport above, which is the
    # state the overlay was found unpainted in.
    narrowest = min(viewports, key=lambda size: size[0])
    page.set_viewport_size({"width": narrowest[0], "height": narrowest[1]})
    page.evaluate(probe("design/frames"))
    smallest = page.evaluate(probe("design/layout-metrics"))["attribution"]
    if smallest is None:
        failures.append(f"no stage at {narrowest[0]} x {narrowest[1]} to photograph")
    else:
        failures.extend(
            f"animate at {narrowest[0]} x {narrowest[1]}: {item}"
            for item in _painted(page, smallest)
        )
    if original is not None:
        page.set_viewport_size(original)
    if failures:
        raise ValueError("workbench layout:\n  " + "\n  ".join(failures))
    return (
        f"one gutter, edge, stack gap and control height across {len(VIEWS)} views at "
        f"{len(viewports)} viewports ({measured} measurements, "
        f"{time.perf_counter() - started:.1f}s), OPEN only when open, one badge type with "
        f"`{NEW_RESULT}` alone in the star's scarlet, one frame width in its three colours, "
        f"and the attribution just under the legend at its left edge"
    )


def check(page_path: Path) -> str:
    """Open the page in its own browser and run `check_open`."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=os.environ.get("SQUARES_BROWSER_EXECUTABLE")
        )
        try:
            page = browser.new_page(
                reduced_motion="reduce",
                viewport={"width": VIEWPORTS[0][0], "height": VIEWPORTS[0][1]},
            )
            page.goto(page_path.resolve().as_uri())
            page.wait_for_function(probe("benchmark/page-api-ready"))
            page.evaluate(probe("capture/fonts-ready"))
            return check_open(page)
        finally:
            browser.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n\n")[0])
    parser.add_argument("--page", type=Path, help="reuse this built index.html")
    options = parser.parse_args()
    if options.page is not None:
        print(f"OK: {check(options.page)}")
        return 0
    with tempfile.TemporaryDirectory(prefix="squares-workbench-layout-") as scratch:
        page = Path(scratch) / "workbench" / "index.html"
        build(page.parent)
        print(f"OK: {check(page)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
