"""Build one full workbench page and run both browser behavior contracts against it."""

from __future__ import annotations

import tempfile
from pathlib import Path

from workbench_tools.build_site import build
from workbench_tools.check_accessibility import check as check_accessibility
from workbench_tools.check_animation_editor import check as check_animation_editor


def main() -> int:
    """Share the expensive deterministic build across the two Chromium checks."""
    with tempfile.TemporaryDirectory(prefix="squares-workbench-frontend-") as scratch:
        page = Path(scratch) / "workbench" / "index.html"
        build(page.parent)
        accessibility = check_accessibility(page)
        editor = check_animation_editor(page)
    print(f"OK: {accessibility}; {editor}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
