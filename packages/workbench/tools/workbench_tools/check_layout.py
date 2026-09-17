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
  label, `new result` included, in the same family, size, weight and colour.

`findings` is a pure function of the probe's output, so `tests/test_check_layout.py` proves each
rule refuses a page that breaks it without a browser. `check_open` runs the views in a page a
caller already has open, which is how `check_frontend` adds this to a browser session it has
already paid for; `check` opens its own. From `packing/`::

    uv run --frozen --all-extras --group dev python -m workbench_tools.check_layout \\
        [--page PAGE]
"""

from __future__ import annotations

import argparse
import itertools
import os
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from workbench_tools.build_site import build
from workbench_tools.probes import probe

#: The viewports every view is held at: a laptop, a small laptop and a phone.
VIEWPORTS: tuple[tuple[int, int], ...] = ((1440, 900), (1024, 768), (390, 844))

#: Rounding slack, in CSS pixels: boxes land on device-pixel fractions.
SLACK = 0.6

#: Control kinds held to `--control-height`; tabs are held to `--tab-height`.
AT_CONTROL_HEIGHT = frozenset({"button", "select", "input-number", "input-text", "chip"})

#: A bound first proved here (n = 17) and an n with nothing open (n = 16).
STAR_N = 17
OPEN_NONE_N = 16
NEW_RESULT = "new result"

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
    types = {(b["family"], b["size"], b["weight"], b["color"]) for b in badges}
    if len(types) > 1:
        found.append(
            f"the badge labels are set in {len(types)} different types: {sorted(types)}"
        )
    new = [b for b in badges if b["text"] == NEW_RESULT]
    if star is True and not (len(new) == 1 and "badge-star" in (new[0]["icon"] or "").split()):
        found.append(f"a bound first proved here has no `{NEW_RESULT}` star badge: {badges}")
    if star is False and new:
        found.append(f"`{NEW_RESULT}` is drawn where no bound was first proved: {badges}")
    return found


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


def _studio(page: Page) -> None:
    _stage_n(STAR_N)(page)
    page.locator("#animation-example").click()


def _leave_studio(page: Page) -> None:
    page.locator("#animation-catalogue").click()


#: The views, each with how to reach it and how to leave it, and the facts it must show.
VIEWS: tuple[
    tuple[str, Callable[[Page], None], Callable[[Page], None] | None, bool | None], ...
] = (
    ("animate at n = 17", _stage_n(STAR_N), None, True),
    ("animate at n = 16", _stage_n(OPEN_NONE_N), None, False),
    ("the animation studio", _studio, _leave_studio, None),
    ("pack", lambda page: page.locator("#mode-pack").click(), None, None),
    ("search", lambda page: page.locator("#mode-search").click(), None, None),
)


def check_open(page: Page, viewports: Sequence[tuple[int, int]] = VIEWPORTS) -> str:
    """Measure every view at every viewport in an open page; raise with every finding.

    Leaves the page in Animate at its starting viewport.
    """
    started = time.perf_counter()
    original = page.viewport_size
    failures: list[str] = []
    measured = 0
    for label, enter, leave, star in VIEWS:
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
            failures.extend(f"{label} at {width} x {height}: {item}" for item in found)
        if leave is not None:
            leave(page)
    page.locator("#mode-animate").click()
    if original is not None:
        page.set_viewport_size(original)
    if failures:
        raise ValueError("workbench layout:\n  " + "\n  ".join(failures))
    return (
        f"one gutter, edge, stack gap and control height across {len(VIEWS)} views at "
        f"{len(viewports)} viewports ({measured} measurements, "
        f"{time.perf_counter() - started:.1f}s), OPEN only when open, one badge type"
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
