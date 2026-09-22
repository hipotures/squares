#!/usr/bin/env python3
"""Re-rationalise a frozen certificate's atom weights at a declared ``n``.

Two facts about the five conditions meet here.

**Only Condition 2 mentions ``n``.** Conditions 1, 3, 4 and 5 are about the atom
set, the container and the direction net; ``n`` enters once, as the requirement
that the total mass fall strictly below it. So one atom set certifies
``s(n) >= L`` for every integer ``n`` above its mass, which is what
``sqpack.fractional.certificate.least_size_certified`` already says and what
``devtools.decide_certificate`` already prints as ``certifies every n >= k``.

**Scaling the weights up trades that mass headroom for Condition 5 margin.**
Covered mass is a positive linear functional of the weights over a cell set fixed
by the atom *coordinates*, so multiplying every weight by ``bump >= 1`` and
rounding up to a multiple of ``1/scale`` multiplies the total by at least ``bump``
and the least covered cell mass by at least ``bump`` as well, over the same cells.
Condition 1 survives because equal weights stay equal, and Conditions 3 and 4 never
saw the weights.

That is the trade this tool makes. A covering that converged far below its ``n``
spends the gap on margin: the freeze bump in
``sqpack.fractional.colgen.rationalise_sites`` is ``1 + 1e-6``, which clears
Condition 5 by microns and leaves the interval branch and bound unable to separate
the least cell from 1 -- it stalls, and a stalled route decides nothing. A bump of
a few per cent, affordable whenever the mass sits well below ``n``, moves the least
cell mass far enough above 1 that outward-rounded interval arithmetic can see it.

What this tool does **not** do is decide anything. It writes bytes with
``least_cell_mass: null``, exactly as a freeze does, so the declaration is made by
``devtools.declare_least_cell_mass`` and the verdict by
``devtools.decide_certificate`` on the bytes -- freeze, declare, decide, unchanged
(D-433, D-441). It refuses rather than writes when the restatement is not one the
source bytes support: a bump below 1 (which would shave tight cells, D-433), a
total mass not strictly below the declared ``n``, a side above
``ceil(sqrt(n)) * B``, a declared source least cell mass the bump cannot lift to 1,
or any closed-form condition that fails on the result.

Usage, from ``packing/``::

    uv run --frozen --all-extras --group dev python -m devtools.rebump_certificate \\
        --source path/to/source-certificate.json --n 27 --bump 103/100 \\
        --output path/to/n27-certificate.json --report path/to/report.json
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path

from devtools.decide_certificate import load
from devtools.run_fractional_colgen import certificate_json
from sqpack.fractional.certificate import (
    Certificate,
    ceiling_side,
    closed_form_conditions,
    least_size_certified,
)
from sqpack.fractional.model import Atom

#: The largest common denominator this tool will round onto. The interval route
#: refuses a scale whose integer masses leave ``int64``; this refuses a pathological
#: set of denominators before the least common multiple is paid for.
MAX_SCALE = 10**12


class RebumpRefusal(ValueError):
    """The requested restatement is not one the source bytes support."""


def weight_scale(certificate: Certificate) -> int:
    """The least common denominator of the atom weights, bounded as it grows."""

    scale = 1
    for atom in certificate.atoms:
        scale = math.lcm(scale, atom.weight.denominator)
        if scale > MAX_SCALE:
            raise RebumpRefusal(
                f"the atom weights need a denominator above the {MAX_SCALE} scale limit; "
                "pass --scale to round onto a coarser grid"
            )
    return scale


def rebumped_atoms(certificate: Certificate, *, bump: Fraction, scale: int) -> tuple[Atom, ...]:
    """Every weight multiplied by ``bump`` and rounded up to a multiple of ``1/scale``.

    Rounding up rather than to nearest is the same choice ``rationalise_sites``
    makes and for the same reason: rounding down can drop a tight cell below 1, and
    the covering leaves every held row tight (D-433). Rounding up only adds, so the
    lower bound ``bump * least`` on the new least covered mass survives it.
    """

    return tuple(
        Atom(
            atom.label,
            atom.x,
            atom.y,
            Fraction(math.ceil(atom.weight * bump * scale), scale),
        )
        for atom in certificate.atoms
    )


def restated(certificate: Certificate, *, n: int, bump: Fraction, scale: int) -> Certificate:
    """The same sites, the same net, the same ``B``: heavier weights and a new ``n``."""

    return Certificate(
        n=n,
        outer_side=certificate.outer_side,
        square_side=certificate.square_side,
        atoms=rebumped_atoms(certificate, bump=bump, scale=scale),
        half_tangents=certificate.half_tangents,
        symmetry=certificate.symmetry,
    )


def declared_least_cell_mass(record: dict[str, object]) -> Fraction | None:
    """The source's own declaration, or ``None`` when no run computed one."""

    value = record.get("least_cell_mass")
    if value is None:
        return None
    if not isinstance(value, str):
        raise RebumpRefusal(f"source least_cell_mass {value!r} is not an exact rational string")
    return Fraction(value)


def refusals(
    restatement: Certificate, *, bump: Fraction, source_least: Fraction | None
) -> list[str]:
    """Everything wrong with the restatement, named rather than counted."""

    problems: list[str] = []
    ceiling = ceiling_side(restatement.n, restatement.square_side)
    if restatement.outer_side > ceiling:
        problems.append(
            f"side {restatement.outer_side} is above the ceiling {ceiling} "
            f"= ceil(sqrt({restatement.n})) * B"
        )
    problems.extend(
        f"{condition.name} failed: {condition.detail}"
        for condition in closed_form_conditions(restatement)
        if not condition.holds
    )
    if source_least is not None and bump * source_least < 1:
        problems.append(
            f"the source declares least cell mass {source_least} and the bump {bump} "
            f"lifts it only to {bump * source_least} < 1; Condition 5 would fail"
        )
    return problems


def rebump(
    source: Path,
    output: Path,
    *,
    n: int | None,
    bump: Fraction,
    scale: int | None,
) -> dict[str, object]:
    """Write the restated bytes and return the measurement, or refuse.

    ``n`` defaults to the least size the restated mass certifies, so the common case
    -- take this atom set as far down as its mass allows -- needs no arithmetic at
    the call site.
    """

    if bump < 1:
        raise RebumpRefusal(
            f"bump {bump} is below 1; shaving a weight drops a tight cell below 1 (D-433)"
        )
    certificate, record = load(source)
    source_least = declared_least_cell_mass(record)
    grid = weight_scale(certificate) if scale is None else scale
    if grid < 1:
        raise RebumpRefusal(f"scale {grid} must be a positive integer")
    heavier = rebumped_atoms(certificate, bump=bump, scale=grid)
    total = sum((atom.weight for atom in heavier), start=Fraction(0))
    target = least_size_certified(total) if n is None else n
    restatement = restated(certificate, n=target, bump=bump, scale=grid)
    problems = refusals(restatement, bump=bump, source_least=source_least)
    if problems:
        raise RebumpRefusal("; ".join(problems))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(certificate_json(restatement, None))
    return {
        "tool": "devtools.rebump_certificate",
        "source": str(source),
        "output": str(output),
        "bump": str(bump),
        "scale": grid,
        "n": restatement.n,
        "outer_side": str(restatement.outer_side),
        "square_side": str(restatement.square_side),
        "atoms": len(restatement.atoms),
        "source_total_mass": str(certificate.total_mass),
        "total_mass": str(restatement.total_mass),
        "total_mass_decimal": f"{float(restatement.total_mass):.9f}",
        "mass_headroom_to_n": str(restatement.n - restatement.total_mass),
        "source_least_cell_mass": None if source_least is None else str(source_least),
        "least_cell_mass_lower_bound": (
            None if source_least is None else str(bump * source_least)
        ),
        "certifies_every_n_at_least": least_size_certified(restatement.total_mass),
        "ceiling": str(ceiling_side(restatement.n, restatement.square_side)),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="the frozen candidate")
    parser.add_argument("--output", type=Path, required=True, help="where to write the bytes")
    parser.add_argument(
        "--n",
        type=int,
        default=None,
        help="the n to declare; default is the least size the restated mass certifies",
    )
    parser.add_argument(
        "--bump",
        type=Fraction,
        required=True,
        help="factor applied to every weight before rounding up; must be at least 1",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=None,
        help="denominator to round onto; default is the source weights' own",
    )
    parser.add_argument("--report", type=Path, default=None, help="write the measurement here")
    args = parser.parse_args(argv)
    try:
        report = rebump(
            args.source, args.output, n=args.n, bump=args.bump, scale=args.scale
        )
    except RebumpRefusal as error:
        print(f"{args.source}: REFUSED: {error}", flush=True)
        return 1
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=1) + "\n")
    print(
        f"{args.output}: n = {report['n']}, bump {report['bump']}, scale {report['scale']}, "
        f"mass {report['total_mass']} = {report['total_mass_decimal']}, "
        f"headroom {report['mass_headroom_to_n']}, "
        f"least cell mass at least {report['least_cell_mass_lower_bound']}",
        flush=True,
    )
    print(
        "  NOT DECIDED: declare least_cell_mass, then run devtools.decide_certificate "
        "on these bytes.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
