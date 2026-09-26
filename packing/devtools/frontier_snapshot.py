"""Lossless raw-LP evidence for cheap re-rationalisation, never a certificate.

Hexadecimal float strings round-trip the exact binary64 weights. All geometric
coordinates remain exact rationals. Loading this record never grants proof status.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from devtools.frontier_io import atomic_json, read_json
from sqpack.fractional.certificate import Certificate
from sqpack.fractional.colgen import SiteSet, rationalise_sites
from sqpack.fractional.generate import net_half_tangents


def save(
    path: Path, sites: SiteSet, weights: np.ndarray, *,
    n: int, square_side: Fraction, angle_limit: Fraction, direction_steps: int,
) -> None:
    values = [float(value) for value in weights]
    if len(values) != len(sites.orbits) or not all(map(math.isfinite, values)):
        raise ValueError("invalid raw LP weights")
    atomic_json(path, {
        "schema": 1, "purpose": "search-only-raw-lp",
        "n": n, "outer_side": str(sites.outer_side), "square_side": str(square_side),
        "angle_limit": str(angle_limit), "direction_steps": direction_steps,
        "orbits": [[[str(x), str(y)] for x, y in orbit] for orbit in sites.orbits],
        "weights_hex": [value.hex() for value in values],
    })


def load(path: Path) -> tuple[dict[str, Any], SiteSet, np.ndarray]:
    record = read_json(path)
    if record.get("schema") != 1 or record.get("purpose") != "search-only-raw-lp":
        raise ValueError("unsupported raw LP snapshot")
    side = Fraction(record["outer_side"])
    orbits = tuple(tuple((Fraction(x), Fraction(y)) for x, y in orbit)
                   for orbit in record["orbits"])
    if not orbits or any(not 1 <= len(orbit) <= 8 for orbit in orbits):
        raise ValueError("invalid raw orbit cardinality")
    if any(not (0 <= x <= side and 0 <= y <= side) for orbit in orbits for x, y in orbit):
        raise ValueError("raw sites outside the container")
    weights = np.array([float.fromhex(value) for value in record["weights_hex"]], dtype=float)
    if len(weights) != len(orbits) or not np.all(np.isfinite(weights)):
        raise ValueError("invalid raw weight vector")
    if type(record["direction_steps"]) is not int or not 1 <= record["direction_steps"] <= 10000:
        raise ValueError("invalid raw direction count")
    return record, SiteSet(side, orbits), weights


def rationalise(path: Path, scale: int) -> Certificate:
    if scale < 1:
        raise ValueError("rationalisation scale must be positive")
    record, sites, weights = load(path)
    # The production rationaliser (including its safety bump) is the only one
    # used here. Smaller rounding slack must still pass the full exact gate.
    atoms = rationalise_sites(sites, weights, scale=scale)
    return Certificate(
        n=int(record["n"]), outer_side=sites.outer_side,
        square_side=Fraction(record["square_side"]), atoms=atoms,
        half_tangents=net_half_tangents(Fraction(record["angle_limit"]), record["direction_steps"]),
    )
