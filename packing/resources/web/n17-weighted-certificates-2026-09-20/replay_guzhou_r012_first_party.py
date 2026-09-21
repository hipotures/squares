#!/usr/bin/env python3
"""First-party check of the Guzhou R012 lower-bound certificate for ``s(17)``.

R012 (github.com/Guzhou0806/n17-square-packing, commit
``931a0dfd64302e277057006e99388fe5c00b7f53``, archived beside this file) claims

    s(17) >= 461300/99999 = L / A,   L = 4613/1000,  A = 99999/100000.

Its own replay entry point (``verify.py``) discharges the coverage obligation with
``sweep.py``, an exact event-cell sweep adapted from this repository's
``sqpack.fractional.sweep``.  This script deliberately does **not** import, copy or
re-derive that sweep.  It decides the same obligation with the repository's *other*
decision procedure, ``sqpack.fractional.interval``: branch and bound over boxes of
centres in floating-point interval arithmetic with directed rounding.  The two methods
fail differently -- the sweep by a wrong cell set or a wrong domain polygon, the
interval search by an enclosure too wide to resolve -- which is the whole point of
running it here.

What is checked, per the certificate's own structure:

* the archived bytes, against ``MANIFEST.json`` and against a pinned digest of the
  manifest itself (``--allow-unpinned-manifest`` relaxes only the latter);
* the measure: 206 integer orbit rows expanded under the eight symmetries of
  ``[0, L]^2`` to 1616 distinct atoms of total mass ``M``;
* the closed-form arithmetic: ``T = 2880 h``, ``T^2 + 2T - 1 > 0``,
  ``17 gamma - M = 701/250000``, ``(L/A)^2`` against the pinned Mira endpoint;
* the catalogue: 2925 closed parent intervals, contiguous from 0 to ``T``, 48 of them
  at core directions off the ``k h`` net;
* obligation (i), strict containment of the core in every parent of the interval:
  ``B max_{u in {a,b}} (cos(t)cos(u) + sin(t)sin(u) + |sin(t)cos(u) - cos(t)sin(u)|) < A``
  with the relative angle inside ``pi/4``;
* obligation (ii), the parent-centre inset ``r = (A/2) min(f(a), f(b))`` with
  ``f(u) = (1 + 2u - u^2)/(1 + u^2)``, and ``B (c(t) + s(t))/2 <= r < L/2``;
* obligation (iii), that every centre in the closed square ``[r, L - r]^2`` carries
  captured mass at least ``gamma`` -- decided by the interval branch and bound over a
  domain restricted to exactly that square.

Everything except obligation (iii) is exact ``Fraction`` arithmetic.  Obligation (iii)
is decided with outward-rounded interval arithmetic over exact integer masses, so a
certified answer is a lower bound on the true covered mass and a refutation is a genuine
admissible centre.

Threshold.  The obligation is ``mass >= gamma`` with ``gamma = 250023/250000 > 1``, not
the ``mass >= 1`` of the Burns--Massaccesi conditions.  No rescaling of the measure is
needed: ``DirectionSearch.search`` takes an arbitrary integer ``prune_at`` on the
certificate's own mass scale, so the threshold used is ``ceil(gamma * scale)``, which for
an integer mass is exactly equivalent to ``mass >= gamma``.  The scale and the threshold
are recorded in the receipt.

Run from ``packing/``::

    uv run --frozen --all-extras --group dev python \\
        resources/web/n17-weighted-certificates-2026-09-20/replay_guzhou_r012_first_party.py \\
        --entries all --workers 4 --tag 001

Standard library plus ``numpy`` and ``sqpack``.  No network, no JavaScript, no optimizer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import math
import multiprocessing
import platform
import time
from collections.abc import Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import numpy as np

from sqpack.fractional.interval import (
    INT64_MASS_LIMIT,
    MAX_INTERVAL_ATOMS,
    AtomData,
    DirectionOutcome,
    DirectionSearch,
    Interval,
    IntervalInputError,
    Rotation,
    rotation_from_half_tangent,
)

HERE = Path(__file__).resolve().parent
DEFAULT_CERT = HERE / "guzhou0806-n17-square-packing" / "certificates" / "R012"
DEFAULT_RECEIPTS = HERE / "receipts"
# The repository root, so every recorded path means one thing wherever it is read.
REPO = HERE.parents[3]

# The upstream commit the archived tree was taken from, for the receipt only.
SOURCE_COMMIT = "931a0dfd64302e277057006e99388fe5c00b7f53"

# SHA-256 of the archived ``MANIFEST.json``.  Pinned here so that the file set cannot be
# re-described by swapping the manifest along with the data.
PINNED_MANIFEST_SHA256 = "9ad92ab5b80a9de54c1d84661c4753a5800e25ef90b02577ee405e51a1ad294d"

# The certificate's own digest of the expanded 1616-atom measure, recomputed here as a
# binding between these bytes and the object the upstream PROOF.md describes.
SOURCE_ATOM_DIGEST = "ae469399ced8580ddddcef6edc234cf9becd7e94df7752aa8b4f9cefcbaf3643"

# Theorem parameters, pinned so a changed catalogue is a refusal and not a new theorem.
PINNED_PARAMETERS = {
    "L": "4613/1000",
    "A": "99999/100000",
    "h": "207107/1440000000",
    "T": "207107/500000",
    "mass": "424969/25000",
    "gamma": "250023/250000",
    "target": "461300/99999",
}
PINNED_RANGES = [
    [16, 978, "6249/6250"],
    [978, 1145, "49992449/50000000"],
    [1145, 2881, "19997/20000"],
]
PINNED_PREVIOUS_ENDPOINT_SQUARED = Fraction(
    17650291964463886688094912400, 829429719507765981945905041
)
EXPECTED_ORBITS = 206
EXPECTED_ATOMS = 1616
EXPECTED_ENTRIES = 2925
EXPECTED_OFF_NET = 48
EXPECTED_MASS_GAP = Fraction(701, 250000)

# The Mira certificate R012's sites descend from, and its own manifest's digest for it.
# R012 does not cite a site-level provenance; this check establishes one from the bytes.
DEFAULT_MIRA = (
    HERE / "mira-17squares" / "certificates" / "lower_bound_4p613" / "best-certificate.json"
)
PINNED_MIRA_SHA256 = "749f13335980a66a27a2304f212b5d8796390c81b962149647a4d9ff43a228ec"
MIRA_GRID = 100000
EXPECTED_MIRA_ATOMS = 1620


class CheckError(RuntimeError):
    """A pinned fact did not hold.  Never a verdict about the theorem."""


def require(ok: bool, message: str) -> None:  # noqa: FBT001
    if not ok:
        raise CheckError(message)


# ---------------------------------------------------------------------------
# Exact rational geometry.  These are definitions, not an algorithm.
# ---------------------------------------------------------------------------


def trig(half_tangent: Fraction) -> tuple[Fraction, Fraction]:
    """``(cos, sin)`` of ``2 arctan(u)``, exactly."""
    require(0 <= half_tangent < 1, f"half-tangent {half_tangent} outside [0, 1)")
    square = half_tangent * half_tangent
    return (1 - square) / (1 + square), 2 * half_tangent / (1 + square)


def width_factor(half_tangent: Fraction) -> Fraction:
    """``f(u) = cos + sin``, the half-extent factor of an axis-aligned bounding box."""
    cosine, sine = trig(half_tangent)
    return cosine + sine


def exact_capture(
    atoms: Sequence[tuple[Fraction, Fraction, Fraction]],
    side: Fraction,
    direction: tuple[Fraction, Fraction],
    centre: tuple[Fraction, Fraction],
) -> tuple[Fraction, list[int]]:
    """Closed capture: mass and atom indices inside the closed ``side``-square."""
    cosine, sine = direction
    half = side / 2
    x0, y0 = centre
    captured: list[int] = []
    total = Fraction(0)
    for index, (x, y, weight) in enumerate(atoms):
        dx, dy = x - x0, y - y0
        if abs(cosine * dx + sine * dy) <= half and abs(-sine * dx + cosine * dy) <= half:
            captured.append(index)
            total += weight
    return total, captured


# ---------------------------------------------------------------------------
# Archive integrity.
# ---------------------------------------------------------------------------


def recorded_path(path: Path) -> str:
    """Repository-relative when the path is inside the repository, as the record requires."""
    resolved = path.resolve()
    return resolved.relative_to(REPO).as_posix() if resolved.is_relative_to(REPO) else str(resolved)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in items:
            require(key not in out, f"duplicate JSON key {key!r} in {path.name}")
            out[key] = value
        return out

    def reject(value: str) -> Any:
        raise CheckError(f"non-finite JSON constant {value!r} in {path.name}")

    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=reject
    )


def check_integrity(cert_dir: Path, *, allow_unpinned_manifest: bool) -> dict[str, Any]:
    manifest_path = cert_dir / "MANIFEST.json"
    require(manifest_path.is_file(), f"no MANIFEST.json under {cert_dir}")
    manifest_sha = sha256_of(manifest_path)
    if not allow_unpinned_manifest:
        require(
            manifest_sha == PINNED_MANIFEST_SHA256,
            f"MANIFEST.json digest {manifest_sha} is not the pinned "
            f"{PINNED_MANIFEST_SHA256}; this is not the archived R012",
        )
    manifest = load_json(manifest_path)
    files = cast(dict[str, str], manifest["files"])
    present = {
        path.relative_to(cert_dir).as_posix()
        for path in cert_dir.rglob("*")
        if path.is_file() and path.relative_to(cert_dir).as_posix() != "MANIFEST.json"
    }
    for path in cert_dir.rglob("*"):
        require(not path.is_symlink(), f"symlink inside the certificate: {path}")
    require(present == set(files), "certificate file set differs from its manifest")
    for name, digest in sorted(files.items()):
        relative = Path(name)
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            f"unsafe manifest path {name!r}",
        )
        actual = sha256_of(cert_dir / relative)
        require(actual == digest, f"SHA-256 mismatch for {name}: {actual} != {digest}")
    return {
        "manifest_sha256": manifest_sha,
        "manifest_pinned": manifest_sha == PINNED_MANIFEST_SHA256,
        "files": {name: files[name] for name in sorted(files)},
        "file_count": len(files),
    }


# ---------------------------------------------------------------------------
# The measure and the catalogue.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """One catalogue row, with the two derived quantities obligation (iii) needs."""

    index: int
    low: Fraction
    high: Fraction
    t: Fraction
    side: Fraction
    inset: Fraction
    margin: Fraction
    off_net: bool


@dataclass(frozen=True)
class Problem:
    outer: Fraction
    parent_side: Fraction
    gamma: Fraction
    step: Fraction
    net_end: Fraction
    total_mass: Fraction
    atoms: tuple[tuple[Fraction, Fraction, Fraction], ...]
    entries: tuple[Entry, ...]
    closed_form: dict[str, Any]


def expand_measure(
    rows: Sequence[Sequence[int]], outer: Fraction
) -> tuple[tuple[tuple[Fraction, Fraction, Fraction], ...], list[list[int]]]:
    """The D4 orbit expansion, with the orbit each atom came from."""
    require(len(rows) == EXPECTED_ORBITS, f"expected {EXPECTED_ORBITS} orbit rows")
    measure: dict[tuple[Fraction, Fraction], tuple[Fraction, int]] = {}
    for orbit_index, row in enumerate(rows):
        require(
            len(row) == 3 and all(type(value) is int for value in row),
            f"orbit row {orbit_index} is not three integers",
        )
        x = Fraction(row[0], 100000)
        y = Fraction(row[1], 100000)
        weight = Fraction(row[2], 1000000)
        require(0 <= x <= outer and 0 <= y <= outer, f"orbit {orbit_index} outside container")
        require(weight > 0, f"orbit {orbit_index} has non-positive weight")
        images = {
            (a, b)
            for u, v in ((x, y), (y, x))
            for a in (u, outer - u)
            for b in (v, outer - v)
        }
        require(
            not images.intersection(measure), f"orbit {orbit_index} overlaps an earlier orbit"
        )
        for point in images:
            measure[point] = (weight, orbit_index)
    ordered = sorted(measure)
    atoms = tuple((x, y, measure[(x, y)][0]) for x, y in ordered)
    members: list[list[int]] = [[] for _ in range(len(rows))]
    for atom_index, point in enumerate(ordered):
        members[measure[point][1]].append(atom_index)
    return atoms, members


def atom_digest(atoms: Sequence[tuple[Fraction, Fraction, Fraction]]) -> str:
    canonical = json.dumps(
        [[str(value) for value in row] for row in atoms], separators=(",", ":")
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def snap_to_grid(value: Fraction, grid: int) -> tuple[Fraction, bool]:
    """Nearest multiple of ``1/grid``, half away from zero, and whether it was a tie.

    A tie makes "the nearest grid point" ambiguous, so it is reported rather than
    silently resolved: a provenance claim that depends on a tie-breaking convention is
    a claim about the convention.
    """
    scaled = value * grid
    doubled = 2 * scaled
    tie = doubled.denominator == 1 and doubled.numerator % 2 != 0
    nearest = (scaled.numerator * 2 + scaled.denominator) // (2 * scaled.denominator)
    return Fraction(nearest, grid), tie


def check_mira_provenance(
    mira_path: Path,
    atoms: Sequence[tuple[Fraction, Fraction, Fraction]],
    outer: Fraction,
    *,
    allow_unpinned: bool,
) -> dict[str, Any]:
    """R012's sites are Mira's sites snapped to the ``1/100000`` grid, and no lighter.

    R012 ships its measure as 206 integer orbit rows on a ``1e-5`` grid and asserts no
    provenance for the numbers.  Mira's ``best-certificate.json`` carries 1620 atoms at
    full rational precision.  Rounding each Mira site to the nearest grid point and
    summing the weights of sites that then coincide reproduces R012's 1616 sites exactly,
    and every R012 weight is at least the Mira weight it sits on.  That is a statement
    about these two files and nothing more -- in particular it is not a proof that R012's
    measure inherits Mira's coverage, since moving a site by up to ``5e-6`` moves the
    ``B``-square boundary it sits on, and only the coverage sweep can say what that costs.
    """
    digest = sha256_of(mira_path)
    if not allow_unpinned:
        require(
            digest == PINNED_MIRA_SHA256,
            f"Mira best-certificate.json digest {digest} is not the pinned "
            f"{PINNED_MIRA_SHA256}",
        )
    document = load_json(mira_path)
    require(
        Fraction(document["outer_side"]) == outer,
        "the Mira certificate is for a different container side",
    )
    rows = document["atoms"]
    require(
        len(rows) == EXPECTED_MIRA_ATOMS,
        f"{len(rows)} Mira atoms, not the expected {EXPECTED_MIRA_ATOMS}",
    )
    declared_mass = Fraction(document["total_mass"])
    merged: dict[tuple[Fraction, Fraction], Fraction] = {}
    largest_move = Fraction(0)
    ties = 0
    mira_mass = Fraction(0)
    for row in rows:
        x, y, weight = (Fraction(value) for value in row)
        mira_mass += weight
        snapped_x, tie_x = snap_to_grid(x, MIRA_GRID)
        snapped_y, tie_y = snap_to_grid(y, MIRA_GRID)
        ties += int(tie_x) + int(tie_y)
        largest_move = max(largest_move, abs(x - snapped_x), abs(y - snapped_y))
        site = (snapped_x, snapped_y)
        merged[site] = merged.get(site, Fraction(0)) + weight
    require(mira_mass == declared_mass, "the Mira atoms do not sum to their declared mass")
    require(ties == 0, f"{ties} Mira coordinates sit exactly halfway between grid points")
    ours = {(x, y): weight for x, y, weight in atoms}
    missing = sorted(set(ours) - set(merged))
    extra = sorted(set(merged) - set(ours))
    excesses = [ours[site] - merged[site] for site in ours if site in merged]
    matched = not missing and not extra
    dominates = matched and all(excess >= 0 for excess in excesses)
    return {
        "mira_file": recorded_path(mira_path),
        "mira_sha256": digest,
        "mira_sha256_pinned": digest == PINNED_MIRA_SHA256,
        "mira_atoms": len(rows),
        "mira_total_mass": str(mira_mass),
        "grid": MIRA_GRID,
        "half_step_ties": ties,
        "merged_sites": len(merged),
        "r012_sites": len(ours),
        "site_sets_identical": matched,
        "sites_only_in_r012": len(missing),
        "sites_only_in_snapped_mira": len(extra),
        "largest_coordinate_move": str(largest_move),
        "largest_coordinate_move_float": float(largest_move),
        "r012_weight_dominates_mira_everywhere": dominates,
        "least_weight_excess": str(min(excesses)) if excesses else None,
        "greatest_weight_excess": str(max(excesses)) if excesses else None,
        "sites_with_zero_excess": sum(1 for excess in excesses if excess == 0),
        "sites_with_negative_excess": sum(1 for excess in excesses if excess < 0),
        "passed": matched and dominates,
    }


def build_entries(catalogue: dict[str, Any], step: Fraction, net_end: Fraction) -> list[
    tuple[Fraction, Fraction, Fraction, Fraction]
]:
    explicit = catalogue["low"]
    require(len(explicit) == 60, "expected 60 explicit catalogue entries")
    rows: list[tuple[Fraction, Fraction, Fraction, Fraction]] = []
    for row in explicit:
        require(
            len(row) == 4 and all(isinstance(value, str) for value in row),
            "explicit entry is not four rational strings",
        )
        low, high, t, side = (Fraction(value) for value in row)
        rows.append((low, high, t, side))
    require(catalogue["ranges"] == PINNED_RANGES, "catalogue range definitions changed")
    half = Fraction(1, 2)
    for first, stop, side_text in PINNED_RANGES:
        side = Fraction(side_text)
        rows.extend(
            (
                max(Fraction(0), (k - half) * step),
                min(net_end, (k + half) * step),
                k * step,
                side,
            )
            for k in range(first, stop)
        )
    return rows


def load_problem(cert_dir: Path) -> Problem:
    catalogue = load_json(cert_dir / "catalogue.json")
    for key, expected in PINNED_PARAMETERS.items():
        require(
            catalogue[key] == expected,
            f"catalogue {key} is {catalogue[key]!r}, not the pinned {expected!r}",
        )
    outer = Fraction(PINNED_PARAMETERS["L"])
    parent_side = Fraction(PINNED_PARAMETERS["A"])
    step = Fraction(PINNED_PARAMETERS["h"])
    net_end = Fraction(PINNED_PARAMETERS["T"])
    declared_mass = Fraction(PINNED_PARAMETERS["mass"])
    gamma = Fraction(PINNED_PARAMETERS["gamma"])
    target = Fraction(PINNED_PARAMETERS["target"])

    atoms, _members = expand_measure(load_json(cert_dir / "orbits.json"), outer)
    require(
        len(atoms) == EXPECTED_ATOMS, f"expanded to {len(atoms)} atoms, not {EXPECTED_ATOMS}"
    )
    total_mass = sum((atom[2] for atom in atoms), Fraction(0))
    require(
        total_mass == declared_mass, f"expanded mass {total_mass} != declared {declared_mass}"
    )
    digest = atom_digest(atoms)

    require(net_end == 2880 * step, "T is not 2880 h")
    require(net_end * net_end + 2 * net_end - 1 > 0, "the net does not reach tan(pi/8)")
    mass_gap = 17 * gamma - total_mass
    require(
        mass_gap == EXPECTED_MASS_GAP, f"17 gamma - M = {mass_gap}, not {EXPECTED_MASS_GAP}"
    )
    require(mass_gap > 0, "17 gamma does not exceed the total mass")
    require(target == outer / parent_side, "target is not L/A")
    previous = Fraction(catalogue["previous_endpoint_squared"])
    require(
        previous == PINNED_PREVIOUS_ENDPOINT_SQUARED, "pinned comparison endpoint changed"
    )
    squared_gain = target * target - previous
    require(squared_gain > 0, "no strict improvement over the pinned endpoint")

    rows = build_entries(catalogue, step, net_end)
    entries: list[Entry] = []
    cursor = Fraction(0)
    margins: list[Fraction] = []
    for index, (low, high, t, side) in enumerate(rows):
        require(low == cursor, f"entry {index} starts at {low}, not at the cursor {cursor}")
        require(0 <= low < high < 1, f"entry {index} has a degenerate parent interval")
        require(0 <= t < 1, f"entry {index} core direction outside [0, 1)")
        require(0 < side < parent_side < outer, f"entry {index} has a bad core side")
        cos_t, sin_t = trig(t)
        factors: list[Fraction] = []
        widths: list[Fraction] = []
        for endpoint in (low, high):
            cos_u, sin_u = trig(endpoint)
            dot = cos_t * cos_u + sin_t * sin_u
            cross = abs(sin_t * cos_u - cos_t * sin_u)
            require(dot > 0, f"entry {index}: relative angle at least a quarter turn")
            require(dot >= cross, f"entry {index}: relative angle outside pi/4")
            factors.append(dot + cross)
            widths.append(cos_u + sin_u)
        margin = parent_side - side * max(factors)
        require(
            margin > 0, f"entry {index}: core not strictly inside the whole parent interval"
        )
        inset = parent_side * min(widths) / 2
        require(
            side * (cos_t + sin_t) / 2 <= inset,
            f"entry {index}: core can leave the container at a legal parent centre",
        )
        require(inset < outer / 2, f"entry {index}: parent-centre domain is degenerate")
        entries.append(
            Entry(
                index=index,
                low=low,
                high=high,
                t=t,
                side=side,
                inset=inset,
                margin=margin,
                off_net=(t / step).denominator != 1,
            )
        )
        margins.append(margin)
        cursor = high
    require(len(entries) == EXPECTED_ENTRIES, f"{len(entries)} entries, not {EXPECTED_ENTRIES}")
    require(cursor == net_end, f"catalogue ends at {cursor}, not at T = {net_end}")
    off_net = sum(entry.off_net for entry in entries)
    require(off_net == EXPECTED_OFF_NET, f"{off_net} off-net entries, not {EXPECTED_OFF_NET}")

    closed_form = {
        "expanded_atom_sha256": digest,
        "expanded_atom_sha256_matches_source": digest == SOURCE_ATOM_DIGEST,
        "orbits": EXPECTED_ORBITS,
        "atoms": len(atoms),
        "total_mass": str(total_mass),
        "gamma": str(gamma),
        "mass_gap_17gamma_minus_M": str(mass_gap),
        "net_end_T": str(net_end),
        "T_squared_plus_2T_minus_1": str(net_end * net_end + 2 * net_end - 1),
        "entries": len(entries),
        "off_net_entries": off_net,
        "least_containment_margin": str(min(margins)),
        "least_containment_margin_entry": min(
            range(len(margins)), key=lambda i: margins[i]
        ),
        "target_lower_bound": str(target),
        "target_squared_minus_pinned_endpoint_squared": str(squared_gain),
    }
    return Problem(
        outer=outer,
        parent_side=parent_side,
        gamma=gamma,
        step=step,
        net_end=net_end,
        total_mass=total_mass,
        atoms=atoms,
        entries=tuple(entries),
        closed_form=closed_form,
    )


# ---------------------------------------------------------------------------
# Obligation (iii) through the repository's interval branch and bound.
# ---------------------------------------------------------------------------


def build_atom_data(atoms: Sequence[tuple[Fraction, Fraction, Fraction]]) -> AtomData:
    """``AtomData`` from raw rationals, with the guards ``AtomData.of`` applies.

    ``AtomData.of`` takes a ``Certificate``, whose invariants (a net starting at zero,
    ``Condition`` bookkeeping) are not R012's shape.  The atoms are the same object
    either way: coordinate enclosures plus exact integer masses on a common scale.
    """
    require(
        len(atoms) <= MAX_INTERVAL_ATOMS,
        f"{len(atoms)} atoms exceeds the interval verifier's {MAX_INTERVAL_ATOMS}",
    )
    scale = 1
    for _, _, weight in atoms:
        require(weight >= 0, "the interval verifier requires nonnegative weights")
        scale = math.lcm(scale, weight.denominator)
        require(17 * scale < INT64_MASS_LIMIT, "weight scale too large for exact int64 masses")
    masses = [int(weight * scale) for _, _, weight in atoms]
    total = sum(masses)
    require(total < INT64_MASS_LIMIT, "total scaled mass too large for int64 arithmetic")
    xs = [Interval.of(x) for x, _, _ in atoms]
    ys = [Interval.of(y) for _, y, _ in atoms]
    return AtomData(
        xlo=np.array([value.lo for value in xs]),
        xhi=np.array([value.hi for value in xs]),
        ylo=np.array([value.lo for value in ys]),
        yhi=np.array([value.hi for value in ys]),
        mass=np.array(masses, dtype=np.int64),
        scale=scale,
        total=total,
    )


class RestrictedSearch(DirectionSearch):
    """``DirectionSearch`` over R012's parent-centre square ``[r, L - r]^2``.

    The stock search bounds centres to ``[h, L - h]^2`` with ``h = B(c + s)/2``, the
    largest domain on which the core stays inside the container.  R012 restricts further,
    to the union over the parent interval of the *parent's* legal centre squares, which
    is ``[r, L - r]^2`` with ``r = (A/2) min(f(a), f(b)) >= h``.  Obligation (ii) is what
    proves ``r >= h``, so this is a sub-domain of the stock one and never a widening.

    Only the domain changes.  ``tighten`` derives an outward-rounded superset of each
    box's intersection with ``[margin, far]^2`` and ``admissible`` accepts a point only
    when its enclosure provably lies inside, so replacing the two endpoints keeps both
    the lower bound and the refutation sound.  The initial box is re-derived by the same
    formulas the base class uses: with both rotation components non-negative, ``u`` is
    extreme at the near and far corners and ``v`` at the two off-diagonal corners.
    """

    def __init__(
        self,
        atoms: AtomData,
        rotation: Rotation,
        outer_side: Interval,
        square_side: Interval,
        *,
        near: Fraction,
        far: Fraction,
    ) -> None:
        super().__init__(atoms, rotation, outer_side, square_side)
        contained_core_margin = self.margin
        margin = Interval.of(near)
        beyond = Interval.of(far)
        if margin.lo < contained_core_margin.lo:
            raise IntervalInputError(
                "the restricted domain is not inside the contained-core domain"
            )
        if beyond.lo <= margin.hi:
            raise IntervalInputError("the restricted centre domain is degenerate")
        self.margin = margin
        self.far = beyond
        span = rotation.cosine + rotation.sine
        u_min = span * margin
        u_max = span * beyond
        v_min = rotation.cosine * margin - rotation.sine * beyond
        v_max = rotation.cosine * beyond - rotation.sine * margin
        self.initial = np.array([[u_min.lo, u_max.hi, v_min.lo, v_max.hi]])
        if not np.isfinite(self.initial).all():
            raise IntervalInputError("the restricted initial box is not finite")


def decide_entry(
    atom_data: AtomData,
    outer: Fraction,
    *,
    label: str,
    t: Fraction,
    side: Fraction,
    inset: Fraction,
    threshold: int,
) -> DirectionOutcome:
    """Decide ``mass >= threshold/scale`` over ``[inset, outer - inset]^2`` at ``t``."""
    rotation = rotation_from_half_tangent(label, t)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        search = RestrictedSearch(
            atom_data,
            rotation,
            Interval.of(outer),
            Interval.of(side),
            near=inset,
            far=outer - inset,
        )
        return search.search(prune_at=threshold)


_WORKER: tuple[AtomData, Fraction, int] | None = None


def _initialize(
    atoms: tuple[tuple[Fraction, Fraction, Fraction], ...], outer: Fraction, threshold: int
) -> None:
    global _WORKER  # noqa: PLW0603
    _WORKER = (build_atom_data(atoms), outer, threshold)


def _run(job: tuple[int, Fraction, Fraction, Fraction]) -> dict[str, Any]:
    assert _WORKER is not None
    atom_data, outer, threshold = _WORKER
    index, t, side, inset = job
    started = time.monotonic()
    outcome = decide_entry(
        atom_data,
        outer,
        label=str(index),
        t=t,
        side=side,
        inset=inset,
        threshold=threshold,
    )
    return {
        "index": index,
        "status": outcome.status,
        "lower_scaled": outcome.lower,
        "upper_scaled": outcome.upper,
        "boxes": outcome.boxes,
        "stalled": outcome.stalled,
        "budget_exhausted": outcome.budget_exhausted,
        "seconds": round(time.monotonic() - started, 4),
    }


# ---------------------------------------------------------------------------
# Negative controls.
# ---------------------------------------------------------------------------


def control_counterexamples(
    cert_dir: Path, problem: Problem, atom_data: AtomData, threshold: int
) -> list[dict[str, Any]]:
    """The five retained failing recipes, at their stated centres and over two domains."""
    records: list[dict[str, Any]] = []
    examples = load_json(cert_dir / "counterexamples.json")
    require(len(examples) == 5, "expected five retained counterexamples")
    for position, example in enumerate(examples):
        side = Fraction(example["B"])
        t = Fraction(example["t"])
        centre = (Fraction(example["centre"][0]), Fraction(example["centre"][1]))
        low, high = (Fraction(value) for value in example["parent_interval"])
        inset = problem.parent_side * min(width_factor(low), width_factor(high)) / 2
        cos_t, sin_t = trig(t)
        in_domain = all(inset <= value <= problem.outer - inset for value in centre)
        endpoints = [trig(u) for u in (low, high)]
        widest = max(
            cos_t * cos_u + sin_t * sin_u + abs(sin_t * cos_u - cos_t * sin_u)
            for cos_u, sin_u in endpoints
        )
        interior = side * widest < problem.parent_side
        mass, captured = exact_capture(problem.atoms, side, (cos_t, sin_t), centre)
        stated_mass = Fraction(example["mass"])
        contained_core = side * (cos_t + sin_t) / 2
        restricted = decide_entry(
            atom_data,
            problem.outer,
            label=f"cx{position}",
            t=t,
            side=side,
            inset=inset,
            threshold=threshold,
        )
        enlarged = decide_entry(
            atom_data,
            problem.outer,
            label=f"cx{position}-enlarged",
            t=t,
            side=side,
            inset=contained_core,
            threshold=threshold,
        )
        records.append(
            {
                "control": "counterexample",
                "position": position,
                "t": str(t),
                "B": str(side),
                "parent_interval": [str(low), str(high)],
                "inset": str(inset),
                "contained_core_inset": str(contained_core),
                "centre_is_a_legal_parent_centre": in_domain,
                "core_strictly_inside_parent": interior,
                "exact_mass_at_stated_centre": str(mass),
                "stated_mass": str(stated_mass),
                "mass_matches_stated": mass == stated_mass,
                "atom_count": len(captured),
                "stated_atom_count": example["atom_count"],
                "atom_count_matches": len(captured) == example["atom_count"],
                "below_one": mass < 1,
                "below_gamma": mass < problem.gamma,
                "restricted_domain_status": restricted.status,
                "restricted_domain_least_point_mass": (
                    None
                    if restricted.upper is None
                    else str(Fraction(restricted.upper, atom_data.scale))
                ),
                "enlarged_domain_status": enlarged.status,
                "enlarged_domain_least_point_mass": (
                    None
                    if enlarged.upper is None
                    else str(Fraction(enlarged.upper, atom_data.scale))
                ),
                "passed": (
                    in_domain
                    and interior
                    and mass == stated_mass
                    and len(captured) == example["atom_count"]
                    and mass < 1
                    and mass < problem.gamma
                    and restricted.status == "refuted"
                    and enlarged.status == "refuted"
                ),
            }
        )
    return records


def control_raised_threshold(
    problem: Problem, atom_data: AtomData, entry: Entry, threshold: int
) -> dict[str, Any]:
    """The threshold is load-bearing: one unit above what the entry achieves must refuse."""
    baseline = decide_entry(
        atom_data,
        problem.outer,
        label=f"{entry.index}",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=threshold,
    )
    if baseline.upper is None:
        return {
            "control": "raised-threshold",
            "entry": entry.index,
            "passed": False,
            "note": "no admissible point sampled; control inconclusive",
        }
    raised = baseline.upper + 1
    outcome = decide_entry(
        atom_data,
        problem.outer,
        label=f"{entry.index}-raised",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=raised,
    )
    return {
        "control": "raised-threshold",
        "entry": entry.index,
        "baseline_status": baseline.status,
        "baseline_least_point_mass": str(Fraction(baseline.upper, atom_data.scale)),
        "raised_threshold_scaled": raised,
        "raised_threshold": str(Fraction(raised, atom_data.scale)),
        "raised_status": outcome.status,
        "passed": baseline.status == "certified" and outcome.status == "refuted",
    }


def control_gamma_is_tight(
    problem: Problem, atom_data: AtomData, entry: Entry, threshold: int
) -> dict[str, Any]:
    """``gamma`` is attained, so one unit above it must be refused.

    R012's catalogue minimum is exactly ``gamma``; there is no slack anywhere to spend.
    At an entry that attains it, raising the threshold by a single unit of the mass scale
    -- ``1/1000000``, the smallest change the data can express -- has to turn the verdict
    from certified into refuted.  A checker that passes this entry at ``gamma + 1`` is not
    measuring the measure.
    """
    baseline = decide_entry(
        atom_data,
        problem.outer,
        label=f"{entry.index}",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=threshold,
    )
    raised = decide_entry(
        atom_data,
        problem.outer,
        label=f"{entry.index}-gamma+1",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=threshold + 1,
    )
    attains_gamma = baseline.upper == threshold
    return {
        "control": "gamma-is-tight",
        "entry": entry.index,
        "baseline_status": baseline.status,
        "baseline_least_point_mass": (
            None if baseline.upper is None else str(Fraction(baseline.upper, atom_data.scale))
        ),
        "entry_attains_gamma": attains_gamma,
        "raised_threshold": str(Fraction(threshold + 1, atom_data.scale)),
        "raised_status": raised.status,
        "raised_least_point_mass": (
            None if raised.upper is None else str(Fraction(raised.upper, atom_data.scale))
        ),
        "passed": (
            baseline.status == "certified" and attains_gamma and raised.status == "refuted"
        ),
    }


def control_lightened_measure(
    problem: Problem,
    orbit_members: Sequence[Sequence[int]],
    atom_data: AtomData,
    entry: Entry,
    threshold: int,
) -> dict[str, Any]:
    """A measure with one orbit emptied must be refused where it was tight.

    The seed is the search's own witness for ``entry``: the float centre is read back as
    an exact rational, the captured atoms are recounted exactly, and the orbits carrying
    that mass are emptied one at a time, heaviest contribution first, until the exact
    mass at that centre drops below ``gamma``.  A measure that light cannot satisfy the
    obligation at a centre we have exhibited, so the search must refuse it.
    """
    baseline = decide_entry(
        atom_data,
        problem.outer,
        label=f"{entry.index}",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=threshold,
    )
    if baseline.witness is None:
        return {
            "control": "lightened-measure",
            "entry": entry.index,
            "passed": False,
            "note": "no witness centre; control inconclusive",
        }
    cos_t, sin_t = trig(entry.t)
    u = Fraction(baseline.witness[0])
    v = Fraction(baseline.witness[1])
    centre = (cos_t * u - sin_t * v, sin_t * u + cos_t * v)
    mass, captured = exact_capture(problem.atoms, entry.side, (cos_t, sin_t), centre)
    owner = {atom: orbit for orbit, atoms in enumerate(orbit_members) for atom in atoms}
    contribution: dict[int, Fraction] = {}
    for atom in captured:
        orbit = owner[atom]
        contribution[orbit] = contribution.get(orbit, Fraction(0)) + problem.atoms[atom][2]
    emptied: list[int] = []
    remaining = mass
    for orbit, amount in sorted(contribution.items(), key=lambda kv: (-kv[1], kv[0])):
        if remaining < problem.gamma:
            break
        emptied.append(orbit)
        remaining -= amount
    if remaining >= problem.gamma:
        return {
            "control": "lightened-measure",
            "entry": entry.index,
            "passed": False,
            "note": "emptying every captured orbit still leaves mass at or above gamma",
        }
    drop = set(emptied)
    dropped_atoms = {atom for orbit in drop for atom in orbit_members[orbit]}
    lightened = tuple(
        (x, y, Fraction(0) if index in dropped_atoms else w)
        for index, (x, y, w) in enumerate(problem.atoms)
    )
    lightened_data = build_atom_data(lightened)
    require(
        lightened_data.scale == atom_data.scale,
        "lightening changed the mass scale, so the pinned threshold would not transfer",
    )
    outcome = decide_entry(
        lightened_data,
        problem.outer,
        label=f"{entry.index}-lightened",
        t=entry.t,
        side=entry.side,
        inset=entry.inset,
        threshold=threshold,
    )
    return {
        "control": "lightened-measure",
        "entry": entry.index,
        "baseline_status": baseline.status,
        "witness_exact_mass": str(mass),
        "witness_atom_count": len(captured),
        "orbits_emptied": emptied,
        "mass_at_witness_after_lightening": str(remaining),
        "lightened_status": outcome.status,
        "passed": baseline.status == "certified" and outcome.status == "refuted",
    }


def control_faithful_restriction(
    problem: Problem, atom_data: AtomData, entry: Entry
) -> dict[str, Any]:
    """The restricted initial box really does enclose the domain it claims to.

    The property that matters is exact, not comparative: the four corners of the rotated
    centre square are rational numbers, and the initial box has to bracket all of them,
    or the branch and bound starts from a region that misses admissible centres.  Checked
    here against the exact corner coordinates, at the entry's own inset ``r`` and at the
    contained-core inset ``B(c + s)/2``.

    The second half checks the restriction is only a restriction.  Run at the
    contained-core inset, ``RestrictedSearch`` decides the same domain the stock
    ``DirectionSearch`` does, so the two must reach the same verdict.  The two initial
    boxes are recorded but are not the test: the stock class re-derives the inset through
    interval arithmetic and so starts from a slightly looser enclosure of the same square.
    """
    cos_t, sin_t = trig(entry.t)
    contained_core = entry.side * (cos_t + sin_t) / 2
    rotation = rotation_from_half_tangent(str(entry.index), entry.t)
    encloses_exactly = True
    for near in (entry.inset, contained_core):
        far = problem.outer - near
        with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
            search = RestrictedSearch(
                atom_data,
                rotation,
                Interval.of(problem.outer),
                Interval.of(entry.side),
                near=near,
                far=far,
            )
        corners = ((near, near), (far, near), (far, far), (near, far))
        rotated = [(cos_t * x + sin_t * y, cos_t * y - sin_t * x) for x, y in corners]
        box = search.initial[0]
        lo_u, hi_u = Fraction(box[0]), Fraction(box[1])
        lo_v, hi_v = Fraction(box[2]), Fraction(box[3])
        encloses_exactly &= all(
            lo_u <= u <= hi_u and lo_v <= v <= hi_v for u, v in rotated
        )
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        stock = DirectionSearch(
            atom_data, rotation, Interval.of(problem.outer), Interval.of(entry.side)
        )
        mine = RestrictedSearch(
            atom_data,
            rotation,
            Interval.of(problem.outer),
            Interval.of(entry.side),
            near=contained_core,
            far=problem.outer - contained_core,
        )
        stock_outcome = stock.search(prune_at=None)
        mine_outcome = mine.search(prune_at=None)
    agree = (
        stock_outcome.status == mine_outcome.status
        and stock_outcome.lower == mine_outcome.lower
        and stock_outcome.upper == mine_outcome.upper
    )
    return {
        "control": "faithful-restriction",
        "entry": entry.index,
        "initial_box_encloses_exact_domain_corners": bool(encloses_exactly),
        "restriction_is_inside_contained_core": entry.inset >= contained_core,
        "stock_margin": [stock.margin.lo, stock.margin.hi],
        "restricted_margin_at_contained_core": [mine.margin.lo, mine.margin.hi],
        "stock_initial": stock.initial[0].tolist(),
        "restricted_initial_at_contained_core": mine.initial[0].tolist(),
        "stock_enclosed_minimum": (
            None
            if stock_outcome.lower is None
            else str(Fraction(stock_outcome.lower, atom_data.scale))
        ),
        "restricted_enclosed_minimum": (
            None
            if mine_outcome.lower is None
            else str(Fraction(mine_outcome.lower, atom_data.scale))
        ),
        "same_verdict_on_the_same_domain": agree,
        "passed": bool(encloses_exactly) and agree and entry.inset >= contained_core,
    }


# ---------------------------------------------------------------------------
# Entry selection and the run.
# ---------------------------------------------------------------------------


def select_entries(spec: str, entries: Sequence[Entry]) -> tuple[list[int], str]:
    total = len(entries)
    text = spec.strip().lower()
    if text == "all":
        return list(range(total)), "all"
    if text == "explicit":
        return list(range(60)), "the 60 explicit entries"
    if text == "offnet":
        return [e.index for e in entries if e.off_net], "the 48 off-net entries"
    if text == "subset":
        chosen = set(range(60))
        chosen |= {e.index for e in entries if e.off_net}
        chosen |= set(range(0, total, 10))
        return sorted(chosen), "explicit + off-net + every tenth entry"
    if text.startswith("every:"):
        stride = int(text.split(":", 1)[1])
        require(stride >= 1, "stride must be at least 1")
        return list(range(0, total, stride)), f"every {stride}th entry"
    chosen: set[int] = set()
    for raw in text.split(","):
        piece = raw.strip()
        if not piece:
            continue
        if "-" in piece:
            first, last = piece.split("-", 1)
            chosen |= set(range(int(first), int(last) + 1))
        else:
            chosen.add(int(piece))
    require(bool(chosen), f"no entries selected by {spec!r}")
    require(
        all(0 <= index < total for index in chosen), f"entry index out of range in {spec!r}"
    )
    return sorted(chosen), f"{len(chosen)} explicitly listed entries"


def read_source_minima(path: Path | None) -> dict[int, str]:
    """Per-entry minima from the source replay's ``coverage.jsonl``, plain or ``.xz``."""
    if path is None:
        return {}
    raw = path.read_bytes()
    text = (lzma.decompress(raw) if path.suffix == ".xz" else raw).decode("utf-8")
    minima: dict[int, str] = {}
    for line in text.splitlines():
        row = json.loads(line)
        minima[int(row["index"])] = str(row["minimum"])
    return minima


def emit(log: list[str], text: str) -> None:
    print(text, flush=True)  # noqa: T201 -- printing is this tool's reporting channel
    log.append(text)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--certificate-dir", type=Path, default=DEFAULT_CERT)
    parser.add_argument("--receipts-dir", type=Path, default=DEFAULT_RECEIPTS)
    parser.add_argument("--tag", default="001", help="receipt filename suffix")
    parser.add_argument(
        "--entries",
        default="all",
        help="all | explicit | offnet | subset | every:N | comma list with a-b ranges",
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="records and controls only; no obligation (iii)",
    )
    parser.add_argument("--skip-controls", action="store_true")
    parser.add_argument(
        "--control-entry", type=int, default=0, help="entry index seeding the search controls"
    )
    parser.add_argument(
        "--tight-entry",
        type=int,
        default=2240,
        help="entry whose minimum is exactly gamma, for the gamma+1 control",
    )
    parser.add_argument("--mira-certificate", type=Path, default=DEFAULT_MIRA)
    parser.add_argument("--skip-mira-provenance", action="store_true")
    parser.add_argument("--allow-unpinned-mira", action="store_true")
    parser.add_argument(
        "--source-coverage",
        type=Path,
        default=None,
        help="the source replay's coverage.jsonl, read for comparison only",
    )
    parser.add_argument("--allow-unpinned-manifest", action="store_true")
    args = parser.parse_args(argv)

    log: list[str] = []
    started = time.monotonic()
    cert_dir = args.certificate_dir.resolve()
    receipts = args.receipts_dir.resolve()
    receipts.mkdir(parents=True, exist_ok=True)
    stem = f"guzhou-r012-first-party-{args.tag}"

    emit(log, f"first-party R012 check, certificate {recorded_path(cert_dir)}")
    emit(log, f"upstream commit {SOURCE_COMMIT}")
    emit(
        log,
        f"python {platform.python_version()} on {platform.system()},"
        f" numpy {np.__version__}",
    )

    integrity = check_integrity(
        cert_dir, allow_unpinned_manifest=args.allow_unpinned_manifest
    )
    emit(
        log,
        f"integrity: {integrity['file_count']} files match MANIFEST.json"
        f" (manifest sha256 {integrity['manifest_sha256']},"
        f" pinned={integrity['manifest_pinned']})",
    )

    problem = load_problem(cert_dir)
    _atoms, orbit_members = expand_measure(load_json(cert_dir / "orbits.json"), problem.outer)
    for key, value in problem.closed_form.items():
        emit(log, f"closed form: {key} = {value}")

    provenance: dict[str, Any] = {"checked": False}
    if not args.skip_mira_provenance:
        provenance = check_mira_provenance(
            args.mira_certificate.resolve(),
            problem.atoms,
            problem.outer,
            allow_unpinned=args.allow_unpinned_mira,
        )
        provenance["checked"] = True
        emit(log, "")
        for key, value in provenance.items():
            emit(log, f"mira provenance: {key} = {value}")

    atom_data = build_atom_data(problem.atoms)
    scale = atom_data.scale
    threshold_exact = problem.gamma * scale
    threshold = -((-threshold_exact.numerator) // threshold_exact.denominator)
    emit(
        log,
        f"mass scale {scale}; gamma {problem.gamma} = {threshold_exact} on that scale;"
        f" interval threshold prune_at = {threshold}"
        f" ({'exact' if threshold_exact.denominator == 1 else 'ceiling'})",
    )
    emit(log, f"total scaled mass {atom_data.total} = {Fraction(atom_data.total, scale)}")

    controls: list[dict[str, Any]] = []
    if not args.skip_controls:
        seed = problem.entries[args.control_entry]
        emit(log, "")
        emit(log, f"controls (seed entry {seed.index}, t={seed.t}, B={seed.side}):")
        tight = problem.entries[args.tight_entry]
        controls.append(control_faithful_restriction(problem, atom_data, seed))
        controls.append(control_raised_threshold(problem, atom_data, seed, threshold))
        controls.append(control_gamma_is_tight(problem, atom_data, tight, threshold))
        controls.append(
            control_lightened_measure(problem, orbit_members, atom_data, seed, threshold)
        )
        controls.append(
            control_lightened_measure(problem, orbit_members, atom_data, tight, threshold)
        )
        controls.extend(control_counterexamples(cert_dir, problem, atom_data, threshold))
        for record in controls:
            detail = {
                key: value
                for key, value in record.items()
                if key not in ("control", "passed")
            }
            position = "" if "position" not in record else f" #{record['position']}"
            emit(
                log,
                f"  control {record['control']}{position}:"
                f" {'PASS' if record['passed'] else 'FAIL'}"
                f" {json.dumps(detail, sort_keys=True)}",
            )

    controls_ok = all(record["passed"] for record in controls) if controls else None

    source_minima = read_source_minima(args.source_coverage)
    selected: list[int] = []
    selection_text = "coverage not run"
    rows: list[dict[str, Any]] = []
    coverage_summary: dict[str, Any] = {}
    if not args.no_coverage:
        selected, selection_text = select_entries(args.entries, problem.entries)
        emit(log, "")
        emit(
            log,
            f"obligation (iii): {len(selected)} of {len(problem.entries)} entries"
            f" ({selection_text}), {args.workers} workers",
        )
        jobs = [
            (
                problem.entries[index].index,
                problem.entries[index].t,
                problem.entries[index].side,
                problem.entries[index].inset,
            )
            for index in selected
        ]
        by_index = {entry.index: entry for entry in problem.entries}
        jsonl_path = receipts / f"{stem}.jsonl"
        coverage_started = time.monotonic()
        done = 0
        pool: ProcessPoolExecutor | None = None
        with jsonl_path.open("w", encoding="utf-8") as handle:
            if args.workers <= 1:
                _initialize(problem.atoms, problem.outer, threshold)
                results: Iterable[dict[str, Any]] = (_run(job) for job in jobs)
            else:
                pool = ProcessPoolExecutor(
                    max_workers=args.workers,
                    mp_context=multiprocessing.get_context("spawn"),
                    initializer=_initialize,
                    initargs=(problem.atoms, problem.outer, threshold),
                )
                results = pool.map(_run, jobs, chunksize=4)
            for result in results:
                entry = by_index[result["index"]]
                lower = result["lower_scaled"]
                upper = result["upper_scaled"]
                row = {
                    "index": entry.index,
                    "a": str(entry.low),
                    "b": str(entry.high),
                    "t": str(entry.t),
                    "B": str(entry.side),
                    "r": str(entry.inset),
                    "off_net": entry.off_net,
                    "status": result["status"],
                    "certified_lower_bound": (
                        None if lower is None else str(Fraction(lower, scale))
                    ),
                    "least_point_mass": (
                        None if upper is None else str(Fraction(upper, scale))
                    ),
                    "meets_gamma": lower is not None and lower >= threshold,
                    "boxes": result["boxes"],
                    "stalled": result["stalled"],
                    "budget_exhausted": result["budget_exhausted"],
                    "seconds": result["seconds"],
                }
                if source_minima:
                    source = source_minima.get(entry.index)
                    row["source_minimum"] = source
                    row["bracket_contains_source_minimum"] = (
                        source is not None
                        and lower is not None
                        and upper is not None
                        and Fraction(lower, scale) <= Fraction(source) <= Fraction(upper, scale)
                    )
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                rows.append(row)
                done += 1
                if done % 100 == 0:
                    emit(
                        log,
                        f"  {done}/{len(jobs)} entries,"
                        f" {time.monotonic() - coverage_started:.1f}s elapsed",
                    )
            if pool is not None:
                pool.shutdown()
        rows.sort(key=lambda row: cast(int, row["index"]))
        certified = [row for row in rows if row["status"] == "certified" and row["meets_gamma"]]
        bad = [row for row in rows if row not in certified]
        least = min(
            (row for row in rows if row["certified_lower_bound"] is not None),
            key=lambda row: Fraction(cast(str, row["certified_lower_bound"])),
            default=None,
        )
        coverage_summary = {
            "selection": selection_text,
            "selected": len(selected),
            "of": len(problem.entries),
            "complete_catalogue": len(selected) == len(problem.entries),
            "certified": len(certified),
            "not_certified": len(bad),
            "not_certified_indices": [row["index"] for row in bad][:50],
            "least_certified_lower_bound": (
                None if least is None else least["certified_lower_bound"]
            ),
            "least_certified_lower_bound_entry": None if least is None else least["index"],
            "gamma": str(problem.gamma),
            "total_boxes": sum(cast(int, row["boxes"]) for row in rows),
            "total_stalled": sum(cast(int, row["stalled"]) for row in rows),
            "budget_exhausted_entries": [
                row["index"] for row in rows if row["budget_exhausted"]
            ],
            "coverage_seconds": round(time.monotonic() - coverage_started, 2),
            "jsonl": jsonl_path.name,
            "jsonl_sha256": sha256_of(jsonl_path),
        }
        if source_minima:
            mismatched = [
                row["index"]
                for row in rows
                if row.get("bracket_contains_source_minimum") is False
            ]
            coverage_summary["source_comparison"] = {
                "compared": len([row for row in rows if row.get("source_minimum")]),
                "brackets_containing_source_minimum": len(
                    [row for row in rows if row.get("bracket_contains_source_minimum")]
                ),
                "mismatched_indices": mismatched[:50],
            }
        for key, value in coverage_summary.items():
            emit(log, f"coverage: {key} = {value}")

    complete = bool(coverage_summary.get("complete_catalogue"))
    all_certified = bool(coverage_summary) and coverage_summary["not_certified"] == 0
    provenance_ok = (not provenance["checked"]) or bool(provenance["passed"])
    if not provenance_ok:
        status = "MIRA_PROVENANCE_FAILED"
    elif args.no_coverage:
        status = "RECORDS_ONLY_NO_COVERAGE"
    elif controls_ok is False:
        status = "CONTROL_FAILED"
    elif not all_certified:
        status = "NOT_CERTIFIED"
    elif complete:
        status = "FULL_CATALOGUE_CERTIFIED"
    else:
        status = "PARTIAL_SUBSET_CERTIFIED"

    summary: dict[str, Any] = {
        "tool": "replay_guzhou_r012_first_party.py",
        "tool_sha256": sha256_of(Path(__file__).resolve()),
        "method": (
            "sqpack.fractional.interval branch and bound over centre boxes, domain"
            " restricted to the R012 parent-centre square; independent of the"
            " event-cell sweep lineage that the source's sweep.py shares with"
            " sqpack.fractional.sweep"
        ),
        "claim_under_test": "s(17) >= 461300/99999",
        "source_commit": SOURCE_COMMIT,
        "certificate_dir": recorded_path(cert_dir),
        "integrity": integrity,
        "mira_provenance": provenance,
        "closed_form": problem.closed_form,
        "mass_scale": scale,
        "interval_threshold_scaled": threshold,
        "interval_threshold": str(Fraction(threshold, scale)),
        "controls_run": len(controls),
        "controls_passed": controls_ok,
        "controls": controls,
        "coverage": coverage_summary,
        "status": status,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "seconds": round(time.monotonic() - started, 2),
        "scope": (
            "Obligation (iii) is decided by outward-rounded interval arithmetic over exact"
            " integer masses: a certified entry is a proved lower bound on the covered mass"
            " over the whole closed centre domain. A PARTIAL status decides only the entries"
            " listed in the JSONL and says nothing about the rest of the catalogue."
        ),
    }
    (receipts / f"{stem}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    emit(log, "")
    if status == "FULL_CATALOGUE_CERTIFIED":
        emit(
            log,
            f"STATUS FULL {status}: all {len(problem.entries)} catalogue entries certified"
            f" at or above gamma = {problem.gamma}"
            f" (least certified lower bound {coverage_summary['least_certified_lower_bound']}"
            f" at entry {coverage_summary['least_certified_lower_bound_entry']});"
            f" {len(controls)} controls passed",
        )
    elif status == "PARTIAL_SUBSET_CERTIFIED":
        emit(
            log,
            f"STATUS PARTIAL {status}: {coverage_summary['selected']} of"
            f" {len(problem.entries)} entries ({selection_text}) certified at or above"
            f" gamma = {problem.gamma}; the remaining"
            f" {len(problem.entries) - coverage_summary['selected']} entries were NOT run,"
            f" so the catalogue claim is not decided by this run",
        )
    else:
        emit(log, f"STATUS {status}")
    (receipts / f"{stem}.log").write_text("\n".join(log) + "\n", encoding="utf-8")
    return 0 if status in ("FULL_CATALOGUE_CERTIFIED", "PARTIAL_SUBSET_CERTIFIED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
