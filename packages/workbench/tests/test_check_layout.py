"""The layout check's rules, without a browser.

`check_layout.check_open` measures the built page in Chromium inside `check_frontend`. What is
tested here is what decides the verdict: one well-formed page passes, and each rule refuses a
page that breaks it in exactly the way it names. Each negative control changes one measurement.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

import pytest

from workbench_tools.check_layout import (
    attribution_findings,
    facts_findings,
    findings,
    frames_findings,
)

TYPE = {"family": '"Source Sans 3", sans-serif', "size": "28px", "weight": "500"}
#: The label grey (`--scene-label`) and the star's scarlet (`--scene-proved`), as a computed
#: colour is reported. `new result` is the one badge label set in the second.
GREY = "rgb(71, 82, 95)"
SCARLET = "rgb(163, 18, 63)"
LABEL = {**TYPE, "color": GREY}
STARRED = {**TYPE, "color": SCARLET}
#: The frames' three colours: `--scene-frame`, `--scene-frame-locked`, `--scene-trace`.
FRAME = "rgb(125, 133, 144)"
LOCKED = "rgb(23, 121, 74)"
TRACE = "rgb(223, 227, 231)"


def _panel(name: str, left: float, right: float, top: float, bottom: float) -> dict[str, Any]:
    return {"name": name, "left": left, "right": right, "top": top, "bottom": bottom}


def _page() -> dict[str, Any]:
    """A 1024-wide page that keeps every rule: a 16 px gutter, 8 px gaps, 28 px controls."""
    law = _panel("#law-box", 16, 700, 120, 250)
    walls = _panel("#wall-box", 708, 1008, 120, 250)
    return {
        "viewport": {"width": 1024, "height": 768},
        "documentWidth": 1024,
        "controls": {
            "left": 0,
            "top": 400,
            "right": 1024,
            "bottom": 768,
            "clientWidth": 1024,
            "scrollWidth": 1024,
            "clientHeight": 368,
            "scrollHeight": 600,
            "paddingLeft": 16,
            "paddingRight": 16,
            "borderLeft": 0,
        },
        "tokens": {"gutter": "16px", "stack": "8px", "control": "28px", "tab": "32px"},
        "blocks": [
            _panel("#mode-subpanel", 16, 1008, 8, 112),
            {**_panel("div.panel-row", 16, 1008, 120, 250)},
            _panel("#animation-editor", 16, 1008, 258, 400),
        ],
        "panels": [
            _panel("#mode-subpanel", 16, 1008, 8, 112),
            law,
            walls,
            _panel("#animation-editor", 16, 1008, 258, 400),
        ],
        "rows": [{**_panel("div.panel-row", 16, 1008, 120, 250), "panels": [law, walls]}],
        "controlsFound": [
            {"kind": "tab", "name": "#mode-animate", "height": 32},
            {"kind": "button", "name": "#play", "height": 28},
            {"kind": "select", "name": "#style-select", "height": 28},
            {"kind": "input-number", "name": "#range-from", "height": 28},
            {"kind": "segment", "name": "button.on", "height": 26},
            {"kind": "segment", "name": "button", "height": 26},
            {"kind": "segmented", "name": "#initial-seg", "height": 28},
            {"kind": "segmented", "name": "#phase-seg", "height": 54},
        ],
        "facts": None,
    }


def _layer(*, star: bool, open_items: int) -> dict[str, Any]:
    badges = [{"icon": "badge badge-solid", "text": "exact", **LABEL}]
    if star:
        badges.insert(0, {"icon": "badge badge-star", "text": "new result", **STARRED})
    return {
        "heads": ["Proven", "Open"] if open_items else ["Proven"],
        "openItems": open_items,
        "colours": {"starred": SCARLET, "label": GREY},
        "badges": badges,
    }


def _frames(*, locked: bool = True, catalogue: bool = True) -> dict[str, Any]:
    """The stage's three outer container borders as the catalogue or as Pack draws them."""
    return {
        "container": {
            "shown": not catalogue,
            "stroke": FRAME,
            "strokeWidth": "4px",
            "locked": False,
        },
        "box": {
            "shown": catalogue,
            "stroke": LOCKED if locked else FRAME,
            "strokeWidth": "4px",
            "locked": locked,
        },
        "trace": {"shown": catalogue, "stroke": TRACE, "strokeWidth": "4px", "locked": False},
        "tokens": {"width": "4px", "frame": FRAME, "locked": LOCKED, "trace": TRACE},
    }


def _attribution() -> dict[str, Any]:
    """The address just under the legend, starting at its left edge, over nothing."""
    return {
        "placed": True,
        "shown": True,
        "left": 1116.0,
        "baseline": 1027.5,
        "legend": {"left": 1116.0, "right": 1884.0, "top": 906.0, "bottom": 997.5},
        "ink": {"left": 1116.0, "right": 1351.0, "top": 1005.0, "bottom": 1033.0},
        "frame": {"left": 0.0, "top": 0.0, "right": 1920.0, "bottom": 1080.0},
        "screen": {"x": 932.9, "y": 352.5, "width": 97.2, "height": 13.0},
        "family": '"Source Sans 3", sans-serif',
        "size": "26px",
        "weight": "400",
        "fill": FRAME,
        "obstacles": [
            {"name": "#packing-svg", "left": 60, "right": 1060, "top": 12, "bottom": 983},
            {"name": "div.numeral", "left": 476, "right": 680.8, "top": 973, "bottom": 1074},
            {"name": "#site-note", "left": 0, "right": 1860, "top": 2500, "bottom": 2560},
        ],
    }


def test_a_page_that_keeps_every_rule_passes() -> None:
    assert findings(_page()) == []
    assert facts_findings(_layer(star=True, open_items=2), star=True) == []
    assert facts_findings(_layer(star=False, open_items=0), star=False) == []
    assert frames_findings(_frames()) == []
    assert frames_findings(_frames(locked=False)) == []
    assert frames_findings(_frames(catalogue=False)) == []
    assert attribution_findings(_attribution(), aligned=True) == []
    assert attribution_findings(_attribution(), aligned=False) == []


def _set(path: str, value: Any) -> Callable[[dict[str, Any]], None]:
    def change(page: dict[str, Any]) -> None:
        *parents, leaf = path.split(".")
        node: Any = page
        for key in parents:
            node = node[int(key)] if key.isdigit() else node[key]
        node[int(leaf) if leaf.isdigit() else leaf] = value

    return change


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (_set("documentWidth", 1100), "the page is 1100 px wide"),
        (_set("controls.scrollWidth", 1200), "the controls scroll sideways"),
        (_set("controls.paddingRight", 12), "the column's gutters differ"),
        (_set("tokens.gutter", "12px"), "not the 12.0 px gutter"),
        (_set("tokens.stack", None), "declares no pixel --layout-gutter"),
        # The search workspace, centred at 1100 px inside a wider column.
        (_set("blocks.2.left", 170), "#animation-editor spans 170..1008"),
        # The mode tabs' panel, as wide as its tabs.
        (_set("blocks.0.right", 246), "#mode-subpanel spans 16..246"),
        (_set("blocks.2.top", 272), "are 22.00 apart, not 8.00"),
        # Pack's step-animation row, emptied by hiding its one panel: 8 + 0 + 8 between blocks.
        (_set("blocks.1.bottom", 120), "div.panel-row is drawn empty"),
        (
            _set("rows.0.panels.1.left", 718),
            "#law-box and #wall-box in div.panel-row are 18.00 apart",
        ),
        (_set("rows.0.panels.1.right", 900), "line ends at 900"),
        (_set("controlsFound.1.height", 24.5), "button #play is 24.5 tall, not 28.0"),
        (_set("controlsFound.3.height", 30), "input-number #range-from is 30 tall"),
        (_set("controlsFound.0.height", 36), "tab #mode-animate is 36 tall, not 32.0"),
        (_set("controlsFound.5.height", 48), "segment controls come in 2 heights"),
        (_set("controlsFound.7.height", 40), "segmented #phase-seg is 40 tall"),
        (_set("tokens.control", None), "declares no pixel --control-height"),
        (_set("panels.2.left", 690), "#law-box and #wall-box overlap by 10.0 x 130.0"),
    ],
)
def test_each_layout_rule_refuses_the_page_that_breaks_it(
    change: Callable[[dict[str, Any]], None], expected: str
) -> None:
    page = copy.deepcopy(_page())
    change(page)
    found = findings(page)
    assert any(expected in item for item in found), found


def test_heights_without_tokens_still_have_to_agree() -> None:
    """A page with no control token is still refused for mixing control heights."""
    page = _page()
    page["tokens"]["control"] = None
    page["controlsFound"][2]["height"] = 30
    assert any("not one height" in item for item in findings(page))


def test_a_nested_panel_is_not_an_overlap() -> None:
    page = _page()
    page["panels"].append(_panel("fieldset", 30, 990, 270, 390))
    assert findings(page) == []


def test_open_is_headed_only_when_something_is_open() -> None:
    headed_over_nothing = _layer(star=False, open_items=0)
    headed_over_nothing["heads"] = ["Proven", "Open"]
    assert facts_findings(headed_over_nothing) == ["OPEN is headed with 0 open items"]
    unheaded_items = _layer(star=False, open_items=2)
    unheaded_items["heads"] = ["Proven"]
    assert facts_findings(unheaded_items) == ["OPEN is not headed with 2 open items"]


def test_new_result_is_a_badge_in_the_badges_own_type() -> None:
    serif = _layer(star=True, open_items=2)
    serif["badges"][0]["family"] = '"PT Serif", serif'
    assert any("2 different types" in item for item in facts_findings(serif, star=True))
    missing = _layer(star=False, open_items=2)
    assert any("has no `new result`" in item for item in facts_findings(missing, star=True))
    not_a_star = _layer(star=True, open_items=2)
    not_a_star["badges"][0]["icon"] = "badge badge-solid"
    assert any("has no `new result`" in item for item in facts_findings(not_a_star, star=True))
    unearned = _layer(star=True, open_items=2)
    assert any(
        "where no bound was first proved" in item
        for item in facts_findings(unearned, star=False)
    )


def test_new_result_is_the_one_badge_label_in_the_stars_scarlet() -> None:
    """The owner's colour, 2026-09-17: scarlet for `new result`, the label grey for the rest."""
    greyed = _layer(star=True, open_items=2)
    greyed["badges"][0]["color"] = GREY
    assert [
        item for item in facts_findings(greyed, star=True) if "the star's scarlet" in item
    ] == [f"the `new result` label is {GREY}, not the star's scarlet {SCARLET}"]
    spread = _layer(star=True, open_items=2)
    spread["badges"][1]["color"] = SCARLET
    assert [item for item in facts_findings(spread, star=True) if "the label grey" in item] == [
        f"the `exact` label is {SCARLET}, not the label grey {GREY}"
    ]
    # The colour is the only thing that differs: a `new result` in a second size is still one.
    resized = _layer(star=True, open_items=2)
    resized["badges"][0]["size"] = "26px"
    assert any("2 different types" in item for item in facts_findings(resized, star=True))


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (_set("box.strokeWidth", "1.5px"), "the box frame is 1.5px wide, not 4.0 px"),
        (_set("trace.strokeWidth", "1.5px"), "the trace frame is 1.5px wide, not 4.0 px"),
        (_set("container.strokeWidth", "2px"), "the container frame is 2px wide, not 4.0 px"),
        (_set("tokens.width", None), "declares no pixel --scene-frame-width"),
        (_set("box.stroke", "rgb(0, 0, 0)"), "the box is rgb(0, 0, 0), not the best known"),
        (_set("trace.stroke", "rgb(0, 0, 0)"), "the trace is rgb(0, 0, 0), not the lightest"),
    ],
)
def test_each_frame_rule_refuses_the_stage_that_breaks_it(
    change: Callable[[dict[str, Any]], None], expected: str
) -> None:
    frames = copy.deepcopy(_frames())
    change(frames)
    found = frames_findings(frames)
    assert any(expected in item for item in found), found


def test_the_box_is_grey_on_its_way_and_green_only_where_it_locks() -> None:
    """One width, and the lock is the only colour change (the owner, 2026-09-17)."""
    green_on_its_way = _frames(locked=False)
    green_on_its_way["box"]["stroke"] = LOCKED
    assert frames_findings(green_on_its_way) == [
        f"the box is {LOCKED}, not the frames' grey {FRAME}"
    ]
    grey_at_rest = _frames()
    grey_at_rest["box"]["stroke"] = FRAME
    assert frames_findings(grey_at_rest) == [
        f"the box is {FRAME}, not the best known side's green {LOCKED}"
    ]
    black_container = _frames(catalogue=False)
    black_container["container"]["stroke"] = "rgb(0, 0, 0)"
    assert frames_findings(black_container) == [
        f"the container is rgb(0, 0, 0), not the frames' grey {FRAME}"
    ]


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        (_set("left", 1110.0), "starts at 1110.00, 6.00 stage px from the legend's left edge"),
        # Drawn over the legend's last line, and left far below it.
        (_set("ink.top", 990.0), "ink starts -7.50 stage px below the legend's foot"),
        (_set("ink.top", 1040.0), "ink starts 42.50 stage px below the legend's foot"),
        (_set("legend", None), "cannot be measured against the legend"),
        (_set("left", None), "cannot be measured against the legend"),
        # The overlay's units are stage pixels only because its box is the stage's; a box that
        # is not makes the two numbers above mean something else.
        (_set("frame.right", 1024.0), "overlay is not the stage's own box"),
    ],
)
def test_each_attribution_anchor_refuses_the_stage_that_breaks_it(
    change: Callable[[dict[str, Any]], None], expected: str
) -> None:
    attribution = copy.deepcopy(_attribution())
    change(attribution)
    found = attribution_findings(attribution, aligned=True)
    assert any(expected in item for item in found), found


def test_the_attribution_is_drawn_and_clears_what_the_stage_draws() -> None:
    hidden = _attribution()
    hidden["placed"] = False
    assert attribution_findings(hidden, aligned=True) == [
        "the stage's attribution is not drawn"
    ]
    # A stage laid out so that the packing reaches into the address's corner.
    over_the_packing = copy.deepcopy(_attribution())
    over_the_packing["obstacles"][0]["right"] = 1600
    over_the_packing["obstacles"][0]["bottom"] = 1050
    assert any(
        "drawn over #packing-svg" in item
        for item in attribution_findings(over_the_packing, aligned=True)
    )
    # The legend is not shown in Pack and the studio, so where the address starts is not checked
    # there, but what it is drawn over still is: those modes center the packing, and at the
    # legend's left edge the address sat across it.
    clear = copy.deepcopy(_attribution())
    clear["legend"] = None
    clear["ink"] = {"left": 1649.0, "right": 1884.0, "top": 1005.0, "bottom": 1033.0}
    clear["obstacles"][0] = {
        "name": "#packing-svg",
        "left": 460,
        "right": 1516,
        "top": 12,
        "bottom": 1068,
    }
    assert attribution_findings(clear, aligned=False) == []
    across = copy.deepcopy(clear)
    across["ink"] = _attribution()["ink"]
    assert any(
        "drawn over #packing-svg" in item
        for item in attribution_findings(across, aligned=False)
    )
