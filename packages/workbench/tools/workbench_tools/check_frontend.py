"""Build one full workbench page and run the browser behavior contracts against it."""

from __future__ import annotations

import tempfile
from pathlib import Path

from workbench_tools.build_site import build
from workbench_tools.check_accessibility import check as check_accessibility
from workbench_tools.check_animation_editor import check as check_animation_editor
from workbench_tools.check_pack_panel import check as check_pack_panel
from workbench_tools.check_search_panel import check as check_search_panel
from workbench_tools.check_stage_resize import check as check_stage_resize


def main() -> int:
    """Share the deterministic build across the Chromium checks."""
    with tempfile.TemporaryDirectory(prefix="squares-workbench-frontend-") as scratch:
        page = Path(scratch) / "workbench" / "index.html"
        build(page.parent)
        accessibility = check_accessibility(page)
        editor = check_animation_editor(page)
        pack = check_pack_panel(page)
        search = check_search_panel(page)
        resize = check_stage_resize(page)
    print(f"OK: {accessibility}; {editor}; {pack}; {search}; {resize}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
