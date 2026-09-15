"""Check the catalogue Animate view on a built, deployable workbench page.

Animate still runs on the retained controller in `application.js`, driven here through
`window.atlasTransitions`, real keys and a real mouse. Pack and Search have their own
contracts (`check_pack_panel.py`, `check_search_panel.py`); this file holds what is true of
the page's own view, and of the page's global handlers while another panel owns it.

The checks are sections, each a function taking a `Session` and returning the phrase the
summary line reports. A new contract is a new function appended to `SECTIONS`: sections share
one browser page, run in order, and must leave the view paused on the default style.

Every browser assertion is a probe file under `probes/`, loaded by `probes.probe` and given
its values as its one argument; nothing here writes JavaScript.

Usage, from ``packing/``::

    uv run --frozen --all-extras --group dev python -m workbench_tools.check_animate_view
"""

from __future__ import annotations

import argparse
import math
import os
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, sync_playwright

from workbench_tools.build_site import build
from workbench_tools.probes import probe


@dataclass
class Session:
    """One page, and the failures collected against it."""

    page: Page
    failures: list[str] = field(default_factory=list)

    def look(self, name: str, /, **argument: Any) -> Any:
        """Evaluate one probe, with its argument."""
        return self.page.evaluate(probe(name), argument or None)

    def api(self, *calls: tuple[Any, ...]) -> Any:
        """Several calls on the Animate API in one turn; the last one's answer comes back."""
        return self.look("api/apply", calls=[list(call) for call in calls])

    def require(self, condition: bool, message: str) -> None:  # noqa: FBT001 - the assertion
        if not condition:
            self.failures.append(message)

    def enter_animate(self) -> None:
        """Enter Animate by its tab; if a failed section hid the tab, by the API, and say so."""
        tab = self.page.locator("#mode-animate")
        if tab.is_visible():
            tab.click()
        else:
            self.failures.append("the Animate tab is hidden")
            self.api(("setMode", "animate"), ("setCapture", False))
        self.require(self.api(("mode",)) == "animate", "the Animate tab did not enter Animate")


def keyboard_ownership(session: Session) -> str:
    """The page's global shortcuts act only while the Animate view owns the page."""
    page = session.page
    # From load: the page opens on Pack, and a shortcut letter there is Pack's business.
    page.locator("#pack-count").focus()
    page.locator("#pack-count").blur()
    page.keyboard.press("c")
    session.require(
        not session.look("animate/input-owner")["capture"],
        "a bare `c` at load entered capture mode behind Pack",
    )

    page.locator("#mode-search").click()
    seeds = page.locator("#search-seeds")
    seeds.fill("")
    seeds.focus()
    page.keyboard.type("0, 5")
    page.keyboard.press("ArrowLeft")
    owner = session.look("animate/input-owner")
    session.require(
        owner["seeds"] == "0, 5" and owner["focused"] == "search-seeds",
        f"typing into Search's seeds field was taken by the page's shortcuts: {owner}",
    )
    session.require(
        owner["transport"] == "Play",
        f"Space or an arrow in Search ran the hidden Animate transport: {owner}",
    )
    page.locator("#search-n").fill("1")
    page.locator("#search-steps").fill("1")
    seeds.fill("0")
    page.locator("#search-start").focus()
    page.keyboard.press("c")
    session.require(
        not session.look("animate/input-owner")["capture"],
        "a bare `c` with Search's Start focused entered capture mode",
    )
    page.keyboard.press(" ")
    export = page.locator("#search-export")
    started = False
    for _ in range(100):
        if export.is_enabled():
            started = True
            break
        page.wait_for_timeout(50)
    session.require(started, "Space on a focused Search Start did not run the search")
    session.enter_animate()
    return "shortcuts yield to Pack at load and to Search's fields and buttons"


def gap_bar_through_dwell(session: Session) -> str:
    """Through the dwell the bar measures only the squares drawn, against their own record."""
    for n in (17, 26):
        for sample in session.look("animate/gap-through-dwell", n=n):
            label = f"step into {n} at t = {sample['t']:.3f}"
            session.require(
                sample["n"] == n - 1, f"{label}: the bar describes n = {sample['n']}"
            )
            session.require(
                sample["valid"] is True,
                f"{label}: the bar calls n - 1's own record not a packing: {sample}",
            )
            session.require(
                math.isclose(sample["side"], sample["record"], rel_tol=1e-6),
                f"{label}: the side {sample['side']} is not n - 1's record {sample['record']}",
            )
    return "the dwell's bar measures only the squares drawn"


SECTIONS: tuple[Callable[[Session], str], ...] = (
    keyboard_ownership,
    gap_bar_through_dwell,
)


def check(page_path: Path) -> str:
    """Run every section against one page; raise with every failure if any section failed."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=os.environ.get("SQUARES_BROWSER_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        session = Session(page)
        page.on("pageerror", lambda error: session.failures.append(f"pageerror: {error}"))
        page.on(
            "console",
            lambda event: (
                session.failures.append(f"console.{event.type}: {event.text}")
                if event.type == "error"
                else None
            ),
        )
        page.goto(page_path.resolve().as_uri())
        page.wait_for_timeout(500)
        done = []
        for section in SECTIONS:
            if section is not keyboard_ownership and session.api(("mode",)) != "animate":
                session.enter_animate()
            try:
                done.append(section(session))
            except Exception as error:  # noqa: BLE001 - one broken section must not hide the rest
                session.failures.append(f"{section.__name__} stopped: {error}")
        browser.close()
    if session.failures:
        raise ValueError("Animate view:\n  " + "\n  ".join(session.failures))
    return "; ".join(done)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path)
    options = parser.parse_args()
    if options.page is None:
        with tempfile.TemporaryDirectory(prefix="squares-animate-view-") as directory:
            page = Path(directory) / "index.html"
            build(page.parent)
            result = check(page)
    else:
        result = check(options.page)
    print(f"OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
