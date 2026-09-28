"""Closed-cover geometry is exact and cannot be relabeled as a fixed-B proof."""
import json
from fractions import Fraction
from types import SimpleNamespace

import pytest

from sqpack.fractional.hybrid_bins import (
    angle_bin, bin_count, bundle, common_denominator, export_integer, parse_bundle,
)
from sqpack.fractional.hybrid_support import parse_measure


def test_complete_bin_range_and_shrink():
    assert bin_count(6000) == 2486
    assert angle_bin(6000, 0).square_side == Fraction(999666, 1000000)
    for k in [0, 1, 1000, 2485]:
        geom = angle_bin(6000, k)
        assert geom.cosine ** 2 + geom.sine ** 2 == 1
        k2, n = k + 1, 6000
        c1, s1 = Fraction(n*n-k2*k2, n*n+k2*k2), Fraction(2*n*k2, n*n+k2*k2)
        cos_gap = geom.cosine * c1 + geom.sine * s1
        sin_gap = geom.cosine * s1 - geom.sine * c1
        assert geom.square_side * (cos_gap + sin_gap) <= 1
        assert geom.minimum_unit_width <= min(geom.cosine + geom.sine, c1 + s1)
        low, high = geom.centre_range(Fraction(4))
        assert low + high == 4
        assert low >= geom.square_side * (geom.cosine + geom.sine) / 2


def test_rational_export_and_rounding():
    point = (Fraction(1, 3), Fraction(2, 7))
    sites = SimpleNamespace(outer_side=Fraction(3), orbits=((point,),), positions=lambda: (point,))
    below = parse_measure(export_integer(sites, [0.3], weight_scale=10, up=False).encode())
    above = parse_measure(export_integer(sites, [0.3], weight_scale=10, up=True).encode())
    value = Fraction.from_float(0.3)
    assert below.mass <= value <= above.mass
    assert above.atoms[0][:2] == point


def test_bundle_preserves_exact_identity():
    text = "3 1\n2\n10\n1\n3 3 1\n"
    record = bundle(text, 6000)
    parsed, measure = parse_bundle(json.dumps(record).encode())
    assert parsed == record
    assert measure.mass == Fraction(1, 10)
    assert "square_side" not in record
    assert record["status"] == "UNVERIFIED"
    for key, value in [("total_mass", "1"), ("outer_side", "4"), ("n", True),
                       ("net", 0), ("cover_sha256", "0" * 64),
                       ("geometry_rule", "fixed-B"), ("status", "VERIFIED")]:
        mutated = {**record, key: value}
        with pytest.raises(ValueError, match="bin|candidate"):
            parse_bundle(json.dumps(mutated).encode())


def test_no_silent_snap_of_imported_geometry():
    with pytest.raises(ValueError, match="lattice limit"):
        common_denominator(Fraction(3), [(Fraction(1, 1000003), Fraction(1))])
    with pytest.raises(ValueError, match="outside"):
        angle_bin(6000, 2486)
    with pytest.raises(ValueError, match="empty probe"):
        sites = SimpleNamespace(outer_side=Fraction(3), orbits=(), positions=lambda: ())
        export_integer(sites, [], weight_scale=10)


def test_unknown_or_conditional_bundle_is_refused():
    record = bundle("3 1\n1\n10\n1\n1 1 1\n", 6000)
    with pytest.raises(ValueError, match="contract"):
        parse_bundle(json.dumps({**record, "region": "corner"}).encode())
    raw = json.dumps(record)[:-1] + ',"net":6000}'
    with pytest.raises(ValueError, match="duplicate"):
        parse_bundle(raw.encode())
