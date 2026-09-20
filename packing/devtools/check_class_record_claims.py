#!/usr/bin/env python3
"""A retained class record must not also carry the unconditional claim or id.

`devtools.decide_certificate` refuses a class certificate whose `claim` is the
unconditional sentence `s(n) >= L` or whose `id` is the unconditional id, and
`sqpack.fractional.corner_clip` builds the class strings so a clipped run cannot write
them by accident. Both act on a record as it is decided or written. Neither says
anything about the bytes that are *kept*.

`exp-219-n11-96-25-clip-covering.json` is what that permitted: a covering frozen under
the corner clip, retained with `variant: class` and `corner_clip: 1/2` beside the
unconditional `id` `C-n011-fractional-96-25` and the unconditional `claim`
`s(11) >= 96/25`. Retaining it is deliberate -- it is the demonstration of review defect
D1, and both receipts say so -- but only prose separates those bytes from a genuine
unconditional n = 11 certificate at 96/25, and nothing mechanical stopped the *next*
record from landing in the same shape (review finding L3).

This sweep is that mechanism. Every JSON record that declares `variant: class` or
carries a `corner_clip` must state a class `claim` (the corner-class sentence, never
`s(n) >= L`) and, when it carries an `id`, a class id (one with a `-clip-` segment).
The one exemption is named below with its reason, and a stale exemption is a failure
too: if `exp-219` is ever rewritten or removed, the entry goes with it rather than
quietly covering some later record at the same path.

Usage:
    uv run --frozen --all-extras --group dev python -m devtools.check_class_record_claims
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKING = Path(__file__).resolve().parent.parent
REPO = PACKING.parent
#: Directories that hold no retained record and are large enough to be worth skipping.
SKIP = {".venv", ".git", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache"}
#: The unconditional claim sentence's opening, which a class record may never state.
UNCONDITIONAL_CLAIM_PREFIX = "s("
#: What a class id carries and an unconditional id does not.
CLASS_ID_SEGMENT = "-clip-"

#: Retained records allowed in the shape above, each with the reason it is retained.
#: Repository-relative, as every declared path in the record is.
EXEMPT: dict[str, str] = {
    "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/"
    "exp-219-n11-96-25-clip-covering.json": (
        "the retained demonstration of review defect D1: a clipped covering frozen "
        "before the claim strings moved under the clip, kept as the evidence that the "
        "defect was real. The gate refuses it, and both agenda-040 receipts say so"
    ),
}


def records(root: Path) -> list[Path]:
    """Every JSON file under `root` that mentions either declaration field."""

    found: list[Path] = []
    for path in sorted(root.rglob("*.json")):
        if SKIP & set(path.parts):
            continue
        raw = path.read_bytes()
        if b'"variant"' in raw or b'"corner_clip"' in raw:
            found.append(path)
    return found


def problems(record: dict[str, object]) -> list[str]:
    """Every way one record states a class hypothesis in unconditional strings."""

    variant = record.get("variant")
    clip = record.get("corner_clip")
    if variant != "class" and clip is None:
        return []
    found: list[str] = []
    claim = record.get("claim")
    if isinstance(claim, str) and claim.startswith(UNCONDITIONAL_CLAIM_PREFIX):
        found.append(f"declares the unconditional claim {claim!r}")
    identifier = record.get("id")
    if isinstance(identifier, str) and CLASS_ID_SEGMENT not in identifier:
        found.append(f"carries the unconditional id {identifier!r}")
    return found


def check(root: Path = REPO) -> list[str]:
    """Every failure, as a line naming the record and what it states."""

    failures: list[str] = []
    seen: set[str] = set()
    for path in records(root):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        found = problems(record)
        if not found:
            continue
        relative = path.relative_to(root).as_posix()
        if relative in EXEMPT:
            seen.add(relative)
            continue
        failures.extend(f"{relative} {line} beside variant: class" for line in found)
    for relative, reason in EXEMPT.items():
        if relative not in seen:
            failures.append(
                f"{relative} is exempted for a shape it no longer has ({reason}); "
                "drop the exemption rather than leaving it to cover a later record"
            )
    return failures


def main() -> int:
    failures = check()
    for line in failures:
        print(line)
    print(f"class record claims: {len(failures)} failures, {len(EXEMPT)} exempt")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
