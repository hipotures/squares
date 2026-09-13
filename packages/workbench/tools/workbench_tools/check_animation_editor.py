"""Exercise import, editing, replay, export and mode return in the built animation studio."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from playwright.sync_api import sync_playwright

from workbench_tools.build_site import build
from workbench_tools.probes import probe

FIXTURE = Path(__file__).resolve().parents[2] / "tests/fixtures/packing-animation-v1.json"


def check(page_path: Path, screenshots: Path | None = None) -> str:
    """Run against the delivered page, including the public API and actual DOM controls."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True, executable_path=os.environ.get("SQUARES_BROWSER_EXECUTABLE")
        )
        page = browser.new_page(
            reduced_motion="reduce", viewport={"width": 1440, "height": 1000}
        )
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(page_path.resolve().as_uri())
        page.locator("#mode-animate").click()

        def call(name: str, *arguments: Any) -> Any:
            return page.evaluate(probe("api/apply"), {"calls": [[name, *arguments]]})

        def require(condition: bool, message: str) -> None:  # noqa: FBT001
            if not condition:
                raise ValueError(message)

        initial = call("importAnimation", FIXTURE.read_text(encoding="utf-8"))
        require(initial["active"] and initial["n"] == 2, "import did not activate n = 2")
        require(not initial["guided"], "an earlier free frame inherited later guidance")
        require(page.locator("#animation-editor").is_visible(), "animation editor is hidden")
        require(
            page.locator("#animation-squares > g").count() == 2, "stage lost square identities"
        )
        if screenshots is not None:
            screenshots.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshots / "animation-desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        dimensions = page.evaluate(probe("layout/document-size"))
        require(
            dimensions["width"] <= dimensions["viewport"],
            f"animation editor overflows the mobile viewport: {dimensions}",
        )
        if screenshots is not None:
            page.screenshot(path=str(screenshots / "animation-mobile.png"), full_page=True)
        page.set_viewport_size({"width": 1440, "height": 1000})
        middle = call("seekAnimation", 0.5)
        require(
            middle["guided"] and middle["valid"] is False,
            "claimed feasibility bypassed geometry",
        )
        interpolated = call("seekAnimation", 0.25)
        require(
            interpolated["interpolated"] and interpolated["valid"] is None,
            "interpolation reused feasibility",
        )

        page.locator("#animation-loaded details summary").click()
        page.locator("#animation-frame").select_option("1")
        page.locator("#animation-poses").fill("[[0.5,0.5,0],[1.5,0.5,0]]")
        page.locator("#animation-save-frame").click()
        edited = json.loads(call("exportAnimation"))
        require("feasible" not in edited["frames"][1], "editing retained a feasibility claim")
        require(edited["frames"][2]["guided"], "editing laundered later guidance")
        require("<svg" in call("exportAnimationSvg"), "SVG export did not produce a drawing")

        page.locator("#animation-duration").fill("0.05")
        page.locator("#animation-duration").press("Tab")
        call("seekAnimation", 0)
        expected_first = call("exportAnimationSvg")
        with page.expect_download() as captured:
            page.locator("#animation-frames-export").click()
        capture_path = captured.value.path()
        require(capture_path is not None, "capture did not download its frame receipt")
        payload = json.loads(Path(str(capture_path)).read_text(encoding="utf-8"))
        receipt = payload["receipt"]
        require(receipt["status"] == "completed", "frame capture did not complete")
        require(receipt["scheduledFrames"] == 3, "frame capture lost its endpoint")
        require(
            receipt["frames"][0]["svg"] == expected_first, "capture differs from visible seek"
        )
        require(len(receipt["source"]["commit"]) == 40, "capture lost source identity")
        require(payload["animation"]["frames"][2]["guided"], "capture lost guidance ancestry")

        page.locator("#animation-play").click()
        played = call("animationState")
        require(
            played["time"] == 1 and not played["playing"],
            "reduced motion did not seek to the end",
        )
        # A rejected replacement must leave the checked document in place.
        page.locator("#animation-editor > details summary").click()
        page.locator("#animation-json").fill('{"contract":"unsupported"}')
        page.locator("#animation-load").click()
        require(
            call("animationState")["n"] == 2, "invalid import replaced the checked document"
        )
        require(
            "contract" in (page.locator("#animation-status").text_content() or ""),
            "invalid import has no useful error",
        )

        page.locator("#mode-pack").click()
        require(
            not page.locator("#animation-editor").is_visible(),
            "Pack did not relinquish the trace scene",
        )
        require(page.locator("#pack-squares").is_visible(), "Pack scene remained hidden")
        require(page.locator("#pack-workspace").is_visible(), "Pack controls remained hidden")
        require(not errors, "page errors: " + "; ".join(errors))
        browser.close()
    return (
        "animation import, geometry/guidance, frame edits, replay, "
        "SVG/JSON/frame capture, and Pack return"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path)
    parser.add_argument(
        "--screenshots", type=Path, help="also save desktop and mobile UI views"
    )
    options = parser.parse_args()
    if options.page is None:
        with tempfile.TemporaryDirectory(prefix="squares-animation-editor-") as directory:
            page = Path(directory) / "index.html"
            build(page.parent)
            result = check(page, options.screenshots)
    else:
        result = check(options.page, options.screenshots)
    print(f"OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
