"""Export one explicit packing-animation record as a self-contained SVG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from workbench_tools.animation_records import decode_animation
from workbench_tools.animation_render import export_svg


def main() -> int:
    """Run the strict v1 animation-to-SVG command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("animation", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--width", type=int, default=960)
    options = parser.parse_args()

    raw = cast(object, json.loads(options.animation.read_text(encoding="utf-8")))
    document = decode_animation(raw)
    svg = export_svg(document, width=options.width)
    options.out.write_text(svg, encoding="utf-8")
    guided = any(document.frame_is_guided(frame) for frame in document.frames)
    tag = " [GUIDED]" if guided else ""
    print(f"{options.out}  {len(svg):,} bytes  {len(document.frames)} frames{tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
