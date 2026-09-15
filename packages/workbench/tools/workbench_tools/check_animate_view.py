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


def colours_by_instant(session: Session) -> str:
    """A frame's colours are a function of its instant, not of the seeks before it."""
    for n in (26, 110, 272):
        for walk in (6, 24):
            fills = session.look("animate/seek-fills", n=n, at=0.6, walk=walk)
            direct = fills["direct"]
            for route in ("walked", "again"):
                differ = sum(1 for a, b in zip(direct, fills[route], strict=True) if a != b)
                session.require(
                    len(direct) == n and differ == 0,
                    f"step into {n}: the {route} seek ({walk} steps) paints {differ} of "
                    f"{len(direct)} fills differently from a direct seek to the same instant",
                )
    return "direct, walked and revisited seeks paint alike"


def seeks_anywhere(session: Session) -> str:
    """Every instant of a step can be drawn, the ends included, under every style."""
    swept = session.look(
        "animate/seek-grid",
        ns=[10, 17, 26],
        styles=["tween", "physics", "bodies"],
        levels=[0, 3, 10],
        k=48,
    )
    session.require(
        swept["seeks"] == 3 * 3 * 3 * 49 and not swept["failures"],
        f"{len(swept['failures'])} of {swept['seeks']} seeks threw: {swept['failures'][:4]}",
    )
    return f"{swept['seeks']} seeks drawn"


def seeds(session: Session) -> str:
    """One seed replays, another differs, and a new seed stops a run it would orphan."""
    runs = session.look("animate/seed-poses", n=26, at=0.55, seeds=[7, 8, 7])
    session.require([run["seed"] for run in runs] == [7, 8, 7], f"setSeed did not take: {runs}")
    session.require(runs[0]["poses"] == runs[2]["poses"], "seed 7 does not replay its poses")
    session.require(runs[0]["poses"] != runs[1]["poses"], "seeds 7 and 8 draw the same poses")
    run = session.look("animate/seed-during-run", n=17)
    session.require(
        run["before"]["playing"] and run["before"]["optimizing"],
        f"the hand's run did not start, so the seed check tested nothing: {run}",
    )
    session.require(
        not run["after"]["playing"] and not run["after"]["optimizing"],
        f"a new seed left the page playing with no run behind it: {run['after']}",
    )
    return "seeds replay and a new seed ends the run"


def scope(session: Session) -> str:
    """Pair-moving calls keep the stage inside the range, and a run ends where one starts."""
    steps = session.look(
        "animate/scope",
        calls=[
            ["pause"],
            ["setRange", 17, 17],
            ["goTo", 26],
            ["setRange", 20, 30],
            ["goTo", 99],
            ["seekSequence", 0],
            ["seekSequence", 1e9],
            ["setRange", 17, 17],
            ["grab", 0],
            ["release"],
            ["play"],
            ["playAll"],
            ["stopAll"],
        ],
    )
    for step in steps:
        session.require(
            step["inside"], f"`{step['call']}` left the stage outside the range: {step}"
        )
    one_step = steps[2]
    session.require(
        (one_step["from"], one_step["to"], one_step["n"]) == (27, 27, 27),
        f"goTo on a one-step range did not carry the range with it: {one_step}",
    )
    session.require(
        (steps[4]["n"], steps[5]["n"], steps[6]["n"]) == (30, 20, 30),
        f"goTo and seekSequence did not hold a wide range's ends: {steps[4:7]}",
    )
    session.require(
        steps[10]["optimizing"] and not steps[11]["optimizing"],
        f"playAll ran continuous play on top of the hand's run: {steps[10:12]}",
    )
    return "goTo, seekSequence and playAll keep to the range"


def transport_loop(session: Session) -> str:
    """Play pressed in the frame a step ended starts one loop, not a second."""
    loops = session.look("animate/tick-loops", n=17, frames=30)
    session.require(loops["replayed"], f"the step never ended inside a frame: {loops}")
    session.require(
        loops["ticks"] <= loops["frames"] + 2,
        f"{loops['ticks']} tick requests in {loops['frames']} frames: two loops are running",
    )
    return "one playback loop"


def drag_ends(session: Session) -> str:
    """A key that ends the run mid-drag does not leave the page marked as dragging."""
    page = session.page
    session.look("animate/rest-poses", n=17)
    x, y = session.look("stage/screen-of", index=0)
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 5, y)
    session.require(
        session.look("animate/hand")["dragging"],
        "a press on a square did not start a drag, so the check tested nothing",
    )
    page.keyboard.press("Home")
    page.mouse.up()
    session.require(
        not session.look("animate/hand")["dragging"],
        "a key that ended the run mid-drag left `body.dragging` behind",
    )
    session.api(("pause",), ("seek", 0))
    return "a drag always ends"


def drag_past_walls(session: Session) -> str:
    """A square dragged past the walls with a real mouse stays under the cursor."""
    page = session.page
    poses = session.look("animate/rest-poses", n=17)
    index = max(range(len(poses)), key=lambda i: poses[i][0])
    x, y = session.look("stage/screen-of", index=index)
    page.mouse.move(x, y)
    page.mouse.down()
    for k in range(1, 11):
        page.mouse.move(x + 15 * k, y)
    for k in range(10):
        page.mouse.move(x + 150 + (1 if k % 2 == 0 else 0), y)
    held = session.look("stage/screen-of", index=index)
    away = math.dist(held, (x + 150, y))
    session.require(
        session.look("animate/hand")["held"] == index,
        f"the drag did not hold square {index}, so the check tested nothing",
    )
    session.require(
        away < 3, f"a square dragged past the wall is {away:.1f} px from the cursor"
    )
    page.mouse.up()
    session.require(
        session.look("animate/hand") == {"held": -1, "dragging": False},
        f"release did not end the drag: {session.look('animate/hand')}",
    )
    session.api(("pause",), ("seek", 0))
    return "a dragged square stays under the cursor"


SECTIONS: tuple[Callable[[Session], str], ...] = (
    keyboard_ownership,
    gap_bar_through_dwell,
    colours_by_instant,
    seeks_anywhere,
    seeds,
    scope,
    transport_loop,
    drag_ends,
    drag_past_walls,
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
