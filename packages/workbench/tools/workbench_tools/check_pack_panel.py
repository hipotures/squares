"""Exercise the independent Pack panel on a built, deployable workbench page."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from workbench_tools.build_site import build


def check(page_path: Path) -> str:
    """Drive Pack through its public controls and inspect the rendered stage."""
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
        page.locator("#mode-pack").click()
        panel = page.locator("#pack-workspace")
        squares = page.locator("#pack-squares > g")

        def require(condition: bool, message: str) -> None:  # noqa: FBT001
            if not condition:
                raise ValueError(message)

        require(
            panel.is_visible(),
            "Pack panel is hidden after choosing Pack: " + "; ".join(errors),
        )
        require(squares.count() == 17, "Pack did not draw all 17 starting squares")
        require(not page.locator("#squares").is_visible(), "catalogue scene still owns Pack")
        require("n = 17" in page.locator("#pack-status").inner_text(), "Pack status lost n")

        page.locator("#pack-count").fill("7")
        page.locator("#pack-seed").fill("42")
        page.locator("#pack-start").select_option("random")
        page.locator("#pack-apply").click()
        require(
            squares.count() == 7,
            f"Pack count did not reach 7: {squares.count()} nodes; "
            f"{page.locator('#pack-status').inner_text()}",
        )
        random_poses = squares.evaluate_all(
            "nodes => nodes.map(node => node.getAttribute('transform'))"
        )
        stepped = page.evaluate("() => window.packWorkbench.step(1)")
        require(stepped["latest"]["work"]["baseSteps"] == 1, "Pack API step did not advance")
        scene_match = page.evaluate(
            """() => {
              const snapshot = window.packWorkbench.state().snapshot;
              const nodes = [...document.querySelectorAll('#pack-squares > g')];
              if (nodes.length !== snapshot.poses.length) return false;
              return snapshot.poses.every((pose, index) => {
                const match = nodes[index].getAttribute('transform')?.match(
                  /^translate\\(([^ ]+) ([^)]+)\\) rotate\\(([^)]+)\\)/
                );
                if (!match) return false;
                return Math.abs(Number(match[1]) - (pose.x - snapshot.container.originX)) < 1e-9
                  && Math.abs(Number(match[2]) - (pose.y - snapshot.container.originY)) < 1e-9
                  && Math.abs(Number(match[3]) - pose.angle * 180 / Math.PI) < 1e-9;
              });
            }"""
        )
        require(scene_match, "Pack API snapshot does not match the visible square transforms")
        hidden_legacy = page.evaluate(
            """() => {
              try { window.atlasTransitions.optimizeStep(1); return null; }
              catch (error) { return String(error); }
            }"""
        )
        require(
            isinstance(hidden_legacy, str) and "packWorkbench" in hidden_legacy,
            f"legacy optimizer advanced behind the Pack scene: {hidden_legacy}",
        )
        page.locator("#pack-apply").click()
        require(
            random_poses
            == squares.evaluate_all(
                "nodes => nodes.map(node => node.getAttribute('transform'))"
            ),
            "the same random seed does not reproduce its starting arrangement",
        )
        page.locator("#pack-run").click()
        require("1 steps" in page.locator("#pack-status").inner_text(), "Run did not advance")
        page.locator("#pack-restart").click()
        require(
            "0 steps" in page.locator("#pack-status").inner_text(), "Restart did not rewind"
        )
        require(
            random_poses
            == squares.evaluate_all(
                "nodes => nodes.map(node => node.getAttribute('transform'))"
            ),
            "Restart did not recover the same start",
        )

        imported = {
            "squareSide": 1,
            "container": {"originX": 0, "originY": 0, "side": 2},
            "poses": [{"x": 0.5, "y": 0.5, "angle": 0}],
        }
        page.locator("#pack-workspace details summary").click()
        page.locator("#pack-json").fill(json.dumps(imported))
        page.locator("#pack-load").click()
        require(squares.count() == 1, "import did not draw its one square")
        require("n = 1" in page.locator("#pack-status").inner_text(), "import did not set n")
        require(
            page.locator("#pack-start").input_value() == "given",
            "import did not identify its given arrangement",
        )
        with page.expect_download() as download:
            page.locator("#pack-export").click()
        export_path = download.value.path()
        require(export_path is not None, "Pack export did not download a snapshot")
        exported = json.loads(Path(str(export_path)).read_text(encoding="utf-8"))
        require(exported == imported, "Pack snapshot export differs from its imported geometry")

        page.locator("#pack-json").fill('{"poses":[]}')
        page.locator("#pack-load").click()
        require(squares.count() == 1, "a rejected import replaced the checked arrangement")
        require(
            "snapshot" in page.locator("#pack-status").inner_text().lower(),
            "a rejected import has no useful error",
        )
        page.locator("#pack-resolve").click()
        require(
            "Resolve" in page.locator("#pack-repair-status").inner_text(),
            "Resolve did not expose its receipt",
        )

        page.locator("#mode-animate").click()
        require(not panel.is_visible(), "Pack panel remains visible in Animate")
        page.locator("#mode-pack").click()
        require(
            panel.is_visible() and squares.count() == 1, "Pack lost its arrangement on return"
        )
        page.set_viewport_size({"width": 390, "height": 844})
        # Chromium delivers the resize event after set_viewport_size returns. Wait for
        # the stage's JS scale to reflect the new viewport before testing overflow.
        page.wait_for_function(
            "document.querySelector('#stage-wrap').getBoundingClientRect().width <= innerWidth"
        )
        width = page.evaluate("document.documentElement.scrollWidth")
        require(width <= 390, f"Pack overflows the mobile viewport: {width}px")
        require(not errors, "page errors: " + "; ".join(errors))
        browser.close()
    return (
        "Pack count, seeded starts, transport, import/export, Resolve, "
        "mode return and mobile fit"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--page", type=Path)
    options = parser.parse_args()
    if options.page is None:
        with tempfile.TemporaryDirectory(prefix="squares-pack-panel-") as directory:
            page = Path(directory) / "index.html"
            build(page.parent)
            result = check(page)
    else:
        result = check(options.page)
    print(f"OK: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
