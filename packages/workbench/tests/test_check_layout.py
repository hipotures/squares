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

from workbench_tools.check_layout import facts_findings, findings

TYPE = {"family": '"Source Sans 3", sans-serif', "size": "28px", "weight": "500"}
LABEL = {**TYPE, "color": "rgb(71, 82, 95)"}


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
        badges.insert(0, {"icon": "badge badge-star", "text": "new result", **LABEL})
    return {
        "heads": ["Proven", "Open"] if open_items else ["Proven"],
        "openItems": open_items,
        "badges": badges,
    }


def test_a_page_that_keeps_every_rule_passes() -> None:
    assert findings(_page()) == []
    assert facts_findings(_layer(star=True, open_items=2), star=True) == []
    assert facts_findings(_layer(star=False, open_items=0), star=False) == []


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
