"""Smoke-test bounded experimental Search runs in the built workbench."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from playwright.sync_api import Page, expect, sync_playwright

# The status line once a run stops, whichever way it stops.
SETTLED = re.compile(r"finished|cancelled|could not run")


def run_plan(page: Page, *, n: int, seeds: str, steps: int, repair: bool) -> str:
    """Fill the Search form, start a run, and return the status line once it settles."""
    page.locator("#search-n").fill(str(n))
    page.locator("#search-seeds").fill(seeds)
    page.locator("#search-steps").fill(str(steps))
    page.locator("#search-repair").set_checked(repair)
    page.locator("#search-start").click()
    status = page.locator("#search-status")
    expect(status).to_have_text(SETTLED)
    return status.inner_text()


def export_ledger(page: Page) -> dict[str, Any]:
    """Download the panel's ledger and parse it."""
    exported = page.locator("#search-export")
    expect(exported).to_be_enabled()
    with page.expect_download() as captured:
        exported.click()
    ledger_path = captured.value.path()
    if ledger_path is None:
        raise ValueError("Search ledger export did not download")
    return json.loads(Path(str(ledger_path)).read_text(encoding="utf-8"))


def check_bounded_run(page: Page) -> None:
    """One slot of one step records its outcome and exports it."""
    status = run_plan(page, n=1, seeds="0", steps=1, repair=False)
    if "finished" not in status:
        raise ValueError(f"Search did not finish its bounded slot: {status}")
    progress = page.locator("#search-progress").inner_text()
    if "1/1 slots" not in progress or "1 completed" not in progress:
        raise ValueError(f"Search did not record its bounded slot: {progress}")
    if "1 of 1 completed valid" not in progress:
        raise ValueError(f"Search did not summarise validity: {progress}")
    ledger = export_ledger(page)
    if len(ledger.get("outcomes", [])) != 1:
        raise ValueError("Search ledger omitted its completed slot")


def check_repair_run(page: Page) -> None:
    """Ticking Attempt Resolve runs Resolve and ranks the repaired state."""
    status = run_plan(page, n=5, seeds="0", steps=100, repair=True)
    if "could not run" in status or "finished" not in status:
        raise ValueError(f"Search with Resolve did not finish: {status}")
    ledger = export_ledger(page)
    configuration = ledger["plan"]["configurations"][0]["configuration"]
    if configuration["objective"]["state"] != "repaired":
        raise ValueError(f"Search with Resolve ranks {configuration['objective']['state']}")
    for outcome in ledger["outcomes"]:
        if outcome["status"] != "completed":
            raise ValueError(f"Search with Resolve left a slot {outcome['status']}")
        result = outcome["result"]
        if result["selectedState"] != "repaired" or result["repair"]["termination"] == (
            "not-requested"
        ):
            raise ValueError(f"Search with Resolve did not repair: {result['repair']}")
    steps = sum(outcome["result"]["work"]["physicsSteps"] for outcome in ledger["outcomes"])
    iterations = sum(
        outcome["result"]["work"]["repairIterations"] for outcome in ledger["outcomes"]
    )
    work = f"{steps} physics steps, {iterations} repair iterations"
    progress = page.locator("#search-progress").inner_text()
    if iterations < 1 or "1 of 1 completed valid" not in progress or work not in progress:
        raise ValueError(f"Search with Resolve summary lacks validity or {work}: {progress}")


def check(page_path: Path) -> str:
    """Run tiny plans and verify exportable outcomes, Resolve, and Pack return."""
    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=os.environ.get("SQUARES_BROWSER_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on(
            "console",
            lambda event: errors.append(event.text) if event.type == "error" else None,
        )
        page.goto(page_path.resolve().as_uri())
        page.locator("#mode-search").click()
        if not page.locator("#search-workspace").is_visible():
            raise ValueError("Search tab did not expose its panel")
        check_bounded_run(page)
        check_repair_run(page)
        page.locator("#mode-pack").click()
        if not page.locator("#pack-workspace").is_visible():
            raise ValueError("Pack did not return after Search")
        if errors:
            raise ValueError("Search page errors: " + "; ".join(errors))
        browser.close()
    return "bounded and Resolve Search runs, summaries, ledger export and Pack return"
