"""Check keyboard and reduced-motion behavior in the built workbench.

The default command builds a fresh, full-corpus page before opening it. ``--page`` lets
another durable check reuse a page it has already built without changing the assertions.

Usage, from ``packing/``::

    uv run --frozen --all-extras --group dev python -m workbench_tools.check_accessibility
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from workbench_tools.build_site import build
from workbench_tools.probes import probe


def _look(page: Page, name: str, /, **argument: Any) -> Any:
    """Evaluate one checked probe, passing values through Playwright's data channel."""
    return page.evaluate(probe(name), argument or None)


def check(page_path: Path) -> str:
    """Exercise semantics, keyboard editing, and reduced-motion transport."""
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:  # noqa: FBT001
        if not condition:
            errors.append(message)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(reduced_motion="reduce")
        page = context.new_page()
        page.on(
            "console",
            lambda event: (
                errors.append(f"console.{event.type}: {event.text}")
                if event.type == "error"
                else None
            ),
        )
        page.on("pageerror", lambda error: errors.append(f"pageerror: {error}"))
        page.goto(page_path.resolve().as_uri())
        page.wait_for_timeout(500)

        stage = page.locator("#stage")
        require(stage.get_attribute("role") == "region", "the stage is not a region")
        described_by = stage.get_attribute("aria-describedby") or ""
        require(
            "stage-accessible-description" in described_by,
            "the stage does not name its accessible description",
        )
        description = page.locator("#stage-accessible-description").text_content() or ""
        require("Pack mode shows n = 17" in description, "the description omits Pack n = 17")
        require("17 squares" in description, "the description omits the visible square count")

        stage.focus()
        page.keyboard.press("Enter")
        require(
            _look(page, "accessibility/active-identity") == "0", "Enter did not focus square 0"
        )
        page.keyboard.press("ArrowRight")
        packing = _look(page, "api/apply", calls=[["optimizeState"]])
        require(bool(packing["edited"]), "ArrowRight did not edit the focused square")
        require(
            _look(page, "accessibility/active-identity") == "0",
            "keyboard editing lost the focused square",
        )
        page.keyboard.press("Escape")
        require(
            _look(page, "accessibility/active-identity") == "stage",
            "Escape did not focus the stage",
        )

        _look(page, "api/apply", calls=[["setMode", "pack"]])
        before = _look(page, "api/apply", calls=[["optimizeState"]])["steps"]
        page.locator("#play").click()
        after = _look(page, "api/apply", calls=[["optimizeState"]])
        require(not after["running"], "reduced-motion Pack transport remained active")
        require(after["steps"] == before + 120, "reduced-motion Pack did not advance 120 steps")
        require(
            "Advance the packing strategy"
            in (page.locator("#play").get_attribute("aria-label") or ""),
            "Pack transport lost its accessible action label",
        )

        _look(
            page,
            "api/apply",
            calls=[["setMode", "animate"], ["setRange", 17, 18]],
        )
        page.locator("#play").click()
        animated = _look(page, "api/apply", calls=[["state"]])
        require(not animated["playing"], "reduced-motion Animate transport remained active")
        require(animated["shownN"] == 17, "reduced-motion Animate did not advance one result")
        rewound = _look(page, "api/apply", calls=[["seek", 0], ["state"]])
        require(
            rewound["shownN"] == 16, "seeking to zero did not restore the range predecessor"
        )

        context.close()
        browser.close()

    if errors:
        raise ValueError("workbench accessibility check failed:\n  - " + "\n  - ".join(errors))
    return "stage semantics, roving focus, keyboard editing, and reduced-motion transport"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path, help="reuse this built index.html")
    options = parser.parse_args()

    if options.page is not None:
        if not options.page.is_file():
            parser.error(f"page does not exist: {options.page}")
        result = check(options.page)
    else:
        with tempfile.TemporaryDirectory(prefix="squares-workbench-accessibility-") as scratch:
            page = Path(scratch) / "workbench" / "index.html"
            build(page.parent)
            result = check(page)
    print(f"OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
