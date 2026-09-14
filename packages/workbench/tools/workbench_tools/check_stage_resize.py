"""Drag, key, reload and reset the separator between the stage and the controls."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from workbench_tools.build_site import build

KEY = "squares.workbench.stageShare"


def check(page_path: Path) -> str:
    """Drive the separator by pointer and keyboard on the built page in a 1440 x 1000 window."""
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=os.environ.get("SQUARES_BROWSER_EXECUTABLE")
        )
        page = browser.new_page(
            reduced_motion="reduce", viewport={"width": 1440, "height": 1000}
        )
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(page_path.resolve().as_uri())
        handle = page.locator("#stage-resize")

        def require(condition: bool, message: str) -> None:  # noqa: FBT001
            if not condition:
                raise ValueError(message)

        def stage_height(view: Page) -> float:
            return float(view.evaluate("document.getElementById('stage-wrap').offsetHeight"))

        def fits(view: Page) -> bool:
            return bool(
                view.evaluate(
                    "document.getElementById('controls').getBoundingClientRect().bottom"
                    " <= window.innerHeight + 1"
                )
            )

        require(handle.get_attribute("role") == "separator", "the handle is not a separator")
        require(
            handle.get_attribute("aria-orientation") == "horizontal"
            and handle.get_attribute("aria-controls") == "controls"
            and handle.get_attribute("tabindex") == "0",
            "the separator does not name its orientation, its region or its focus",
        )
        automatic = stage_height(page)
        require(
            abs(float(handle.get_attribute("aria-valuenow") or "nan") - automatic) <= 1,
            "the separator's value is not the stage height",
        )

        box = handle.bounding_box()
        if box is None:
            raise ValueError("the separator is not drawn")
        x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x, y + 80, steps=8)
        page.mouse.up()
        dragged = stage_height(page)
        require(
            abs(dragged - (automatic + 80)) <= 2,
            f"dragging 80 px down moved the stage from {automatic} to {dragged}",
        )
        require(fits(page), "the controls overflow the window after a drag")
        require(
            not page.evaluate("document.body.classList.contains('resizing')"),
            "the page is still marked as resizing after the drag",
        )

        handle.focus()
        page.keyboard.press("ArrowUp")
        keyed = stage_height(page)
        require(abs(keyed - (dragged - 16)) <= 2, f"ArrowUp moved {dragged} to {keyed}")
        page.keyboard.press("Home")
        require(
            abs(stage_height(page) - 120) <= 2, "Home did not raise the stage to its minimum"
        )
        page.keyboard.press("End")
        require(fits(page), "End pushed the controls out of the window")
        page.keyboard.press("Shift+ArrowUp")
        shifted = stage_height(page)

        page.reload()
        restored = stage_height(page)
        require(
            abs(restored - shifted) <= 2,
            f"a reload did not keep the stage at {shifted}, it came back at {restored}",
        )
        page.locator("#stage-resize").dblclick()
        reset = stage_height(page)
        require(
            abs(reset - automatic) <= 2,
            f"double-click did not return to the automatic {automatic}: {reset}",
        )
        require(
            page.evaluate(f"window.localStorage.getItem({KEY!r})") is None,
            "double-click did not forget the stored share",
        )
        page.locator("#mode-search").click()
        require(not handle.is_visible(), "the separator shows over Search")
        page.locator("#mode-animate").click()
        require(handle.is_visible(), "the separator did not come back with Animate")
        require(not errors, "page errors: " + "; ".join(errors))
        browser.close()
    return (
        "stage separator drag, arrows, Home and End, reload persistence, double-click reset "
        "and Search hiding"
    )


def main() -> int:
    """Check a supplied page, or build one first."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, help="reuse this built index.html")
    args = parser.parse_args()
    if args.page is not None:
        print(f"OK: {check(args.page)}")
        return 0
    with tempfile.TemporaryDirectory(prefix="squares-workbench-resize-") as scratch:
        page = Path(scratch) / "workbench" / "index.html"
        build(page.parent)
        print(f"OK: {check(page)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
