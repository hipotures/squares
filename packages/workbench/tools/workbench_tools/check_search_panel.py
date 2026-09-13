"""Smoke-test a bounded experimental Search run in the built workbench."""

from __future__ import annotations

import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def check(page_path: Path) -> str:
    """Run one tiny plan and verify an exportable outcome and Pack return."""
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
        page.locator("#search-n").fill("1")
        page.locator("#search-seeds").fill("0")
        page.locator("#search-steps").fill("1")
        page.locator("#search-start").click()
        page.locator("#search-export").wait_for(state="visible")
        page.wait_for_function("!document.getElementById('search-export').disabled")
        progress = page.locator("#search-progress").inner_text()
        if "1/1 slots" not in progress or "1 completed" not in progress:
            raise ValueError(f"Search did not record its bounded slot: {progress}")
        with page.expect_download() as captured:
            page.locator("#search-export").click()
        ledger_path = captured.value.path()
        if ledger_path is None:
            raise ValueError("Search ledger export did not download")
        ledger = json.loads(Path(str(ledger_path)).read_text(encoding="utf-8"))
        if len(ledger.get("outcomes", [])) != 1:
            raise ValueError("Search ledger omitted its completed slot")
        page.locator("#mode-pack").click()
        if not page.locator("#pack-workspace").is_visible():
            raise ValueError("Pack did not return after Search")
        if errors:
            raise ValueError("Search page errors: " + "; ".join(errors))
        browser.close()
    return "bounded Search run, progress, ledger export and Pack return"
