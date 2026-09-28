"""Exact bin geometry and a distinct closed-unit-cover artifact format.

The fixed-B Certificate is deliberately not used for this representation.
The final covering claim is decided by the pinned Rust and Python checkers.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from sqpack.fractional.hybrid_support import UPSTREAM, SourceMeasure, parse_measure

SCHEMA = "hybrid-bin-cover/v1"
RULE = "evand-full-gap-floor-1e6-unit-centre-envelope/v1"
QUANTUM = 1_000_000


@dataclass(frozen=True)
class AngleBin:
    index: int
    net: int
    cosine: Fraction
    sine: Fraction
    square_side: Fraction
    minimum_unit_width: Fraction

    def centre_range(self, side: Fraction) -> tuple[Fraction, Fraction]:
        half = self.minimum_unit_width / 2
        return half, side - half


def bin_count(net: int) -> int:
    if not 3 <= net <= 12000:
        raise ValueError("this experimental bin net must be between 3 and 12000")
    count = math.isqrt(2 * net * net) - net
    while (count + net) ** 2 < 2 * net * net:
        count += 1
    return count


def angle_bin(net: int, index: int) -> AngleBin:
    if not 0 <= index < bin_count(net):
        raise ValueError("bin index outside the complete D4 angle range")
    c0, s0, g0 = net * net - index * index, 2 * index * net, net * net + index * index
    k1 = index + 1
    c1, s1, g1 = net * net - k1 * k1, 2 * k1 * net, net * net + k1 * k1
    cd, sd = c0 * c1 + s0 * s1, c0 * s1 - s0 * c1
    sigma = Fraction(g0 * g1 * QUANTUM // (cd + sd), QUANTUM)
    width = Fraction(min((c0 + s0) * QUANTUM // g0,
                         (c1 + s1) * QUANTUM // g1), QUANTUM)
    return AngleBin(index, net, Fraction(c0, g0), Fraction(s0, g0), sigma, width)


def common_denominator(side: Fraction, points: Any) -> int:
    """Never snap imported support to make it fit the external integer domain."""
    denominator = side.denominator
    for x, y in points:
        denominator = math.lcm(denominator, x.denominator, y.denominator)
        if denominator > 1_000_000:
            raise ValueError("exact imported coordinates exceed the external lattice limit; use B/C or an external-only seed")
    return denominator


def export_integer(sites: Any, weights: Any, *, weight_scale: int,
                   factor: Fraction = Fraction(1), up: bool = True) -> str:
    """Exact rounding of binary64 weights; all imported coordinates remain exact."""
    if len(weights) != len(sites.orbits) or not 1 <= weight_scale <= 10**12 or factor <= 0:
        raise ValueError("invalid integer export dimensions or weight scale")
    points = sites.positions()
    denominator = common_denominator(sites.outer_side, points)
    lines = []
    for orbit, weight in zip(sites.orbits, weights, strict=True):
        if not math.isfinite(float(weight)) or weight < 0:
            raise ValueError("export requires finite nonnegative LP weights")
        value = Fraction.from_float(float(weight)) * factor * weight_scale
        numerator = math.ceil(value) if up else math.floor(value)
        if numerator <= 0:
            continue
        for x, y in orbit:
            lines.append(f"{int(x * denominator)} {int(y * denominator)} {numerator}")
    if not lines:
        raise ValueError("empty probe: initialize covering rows before exporting")
    side = sites.outer_side
    text = f"{side.numerator} {side.denominator}\n{denominator}\n{weight_scale}\n{len(lines)}\n"
    return text + "\n".join(lines) + "\n"


def bundle(text: str, net: int) -> dict[str, Any]:
    measure = parse_measure(text.encode())
    bin_count(net)
    if not 1 < measure.side < 4 or measure.mass >= 12:
        raise ValueError("candidate requires side in (1,4) and total mass below twelve")
    return {
        "schema": SCHEMA, "geometry_rule": RULE, "status": "UNVERIFIED",
        "n": 12, "outer_side": str(measure.side), "net": net, "upstream": UPSTREAM,
        "total_mass": str(measure.mass), "cover_sha256": measure.sha256,
        "certificate_txt": text,
    }


def parse_bundle(raw: bytes) -> tuple[dict[str, Any], SourceMeasure]:
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("bin bundle exceeds the input limit")
    def object_pairs(pairs: Any) -> dict[str, Any]:
        record: dict[str, Any] = {}
        for key, value in pairs:
            if key in record:
                raise ValueError("duplicate bin bundle key")
            record[key] = value
        return record
    record = json.loads(raw, object_pairs_hook=object_pairs)
    if not isinstance(record, dict):
        raise ValueError("bin bundle must be an object")
    keys = {"schema", "geometry_rule", "status", "n", "outer_side", "net", "upstream",
            "total_mass", "cover_sha256", "certificate_txt"}
    if (set(record) != keys or record["schema"] != SCHEMA or record["geometry_rule"] != RULE
            or record["upstream"] != UPSTREAM or type(record["n"]) is not int or record["n"] != 12
            or type(record["net"]) is not int or record["status"] != "UNVERIFIED"):
        raise ValueError("unknown or mismatched bin bundle contract")
    bin_count(record["net"])
    text = record["certificate_txt"]
    if not isinstance(text, str) or text.lstrip().startswith("{"):
        raise ValueError("bin bundle must embed a plain integer certificate")
    measure = parse_measure(text.encode())
    if (measure.sha256 != record["cover_sha256"] or str(measure.side) != record["outer_side"]
            or str(measure.mass) != record["total_mass"] or measure.mass >= 12
            or not 1 < measure.side < 4):
        raise ValueError("bin bundle geometry, mass or digest mismatch")
    common_denominator(measure.side, [(x, y) for x, y, _ in measure.atoms])
    return record, measure
