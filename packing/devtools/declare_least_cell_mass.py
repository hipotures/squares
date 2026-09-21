"""Fill a frozen candidate's ``least_cell_mass`` declaration with a one-worker sweep.

A candidate frozen by `devtools.run_fractional_colgen` or `devtools.colgen_checkpoint`
without ``--verify-serial`` carries ``"least_cell_mass": null``: a declaration no run
has computed. `devtools.decide_certificate` refuses a null declaration at parse, so
such a candidate cannot be decided until the number is declared -- by a sweep the gate
then repeats on the frozen bytes and compares against both of its routes. This tool
makes that declaration and nothing else.

It runs `sqpack.fractional.certificate.verify` with exactly one worker, because a lane
holding one core never starts the pool (the fourth core is the gate's), rewrites the
record with the sweep's least cell mass, and prints the in-memory verdict for the
operator. It does not decide: an in-memory verdict is not evidence about any file
(D-433, D-441), and the retention boundary stays freeze-then-decide through the gate.
A candidate the sweep does not accept is left untouched and the exit code says so.
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

from sqpack.fractional.certificate import Certificate, verify
from sqpack.fractional.corner_clip import CornerClip, clip_from_optional, declared_class_clip
from sqpack.fractional.model import Atom


def corner_clip_of(record: dict[str, object], certificate: Certificate) -> CornerClip | None:
    """The clip the record declares, if any.

    There is no flag for this. The record is the declaration: a candidate frozen under
    lane-a Theorem B's free-corner hypothesis carries ``variant: class`` and
    ``corner_clip``, and the number declared here has to be the one the gate will then
    recompute from the same bytes under the same domain. A flag would let the two
    disagree silently. ``variant: class`` without ``corner_clip`` is refused for the
    same reason: a class record that swept the full domain would declare a number the
    gate never recomputes.
    """

    return clip_from_optional(
        declared_class_clip(record), certificate.outer_side, certificate.square_side
    )


def load_candidate(path: Path) -> tuple[Certificate, dict[str, object]]:
    """The candidate and its record, in the shape ``cases/*/replay.py`` reads."""

    record = json.loads(path.read_text())
    limit = Fraction(record["angle_limit"])
    steps = int(record["direction_steps"])
    certificate = Certificate(
        n=int(record["n"]),
        outer_side=Fraction(record["outer_side"]),
        square_side=Fraction(record["square_side"]),
        atoms=tuple(
            Atom(f"{index:04d}", Fraction(x), Fraction(y), Fraction(weight))
            for index, (x, y, weight) in enumerate(record["atoms"])
        ),
        half_tangents=tuple(limit * k / steps for k in range(steps + 1)),
        symmetry=record["symmetry"],
    )
    return certificate, record


def declare(path: Path, *, overwrite: bool = False) -> tuple[bool, str]:
    """Sweep with one worker and write the declaration; ``(accepted, detail)``.

    Refuses to touch a record that already declares a value unless ``overwrite``
    is given, so a retained file is never rewritten by accident.
    """

    certificate, record = load_candidate(path)
    if record.get("least_cell_mass") is not None and not overwrite:
        return False, f"{path} already declares least_cell_mass {record['least_cell_mass']}"
    clip = corner_clip_of(record, certificate)
    # A record without the declaration is swept by the call this tool always made.
    verdict = (
        verify(certificate, workers=1)
        if clip is None
        else verify(certificate, workers=1, clip=clip)
    )
    domain = "" if clip is None else f" under the corner clip d = {clip.depth}"
    detail = (
        f"one-worker sweep{domain}: accepted={verdict.accepted} "
        f"failures={verdict.failures} least cell mass {verdict.minimum_cell_mass}"
    )
    if not verdict.accepted or verdict.minimum_cell_mass is None:
        return False, detail
    record["least_cell_mass"] = str(verdict.minimum_cell_mass)
    path.write_text(json.dumps(record, indent=1) + "\n")
    return True, detail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--overwrite", action="store_true", help="replace an existing value")
    args = parser.parse_args(argv)
    failed = 0
    for path in args.paths:
        accepted, detail = declare(path, overwrite=args.overwrite)
        print(f"{path}: {detail}", flush=True)
        failed += not accepted
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
