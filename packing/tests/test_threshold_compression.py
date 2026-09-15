"""Exact, target-blind controls for threshold-certificate orbit compression."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

import pytest

from cases.n11_threshold_certificate.replay import certificate as t025_certificate
from devtools.decide_threshold_certificate import load
from sqpack.fractional.certificate import d4_images
from sqpack.fractional.model import Atom
from sqpack.fractional.threshold import ThresholdAtom, ThresholdCertificate
from sqpack.fractional.threshold_compression import (
    CompressionPolicy,
    PointOrbitSelection,
    SelectionManifestError,
    ThresholdNetSpec,
    ThresholdOrbitSelection,
    canonical_catalog_record,
    catalog_sha256,
    compare_scaled_support,
    decompress_selection,
    inventory_certificate,
    measure_selection,
    ordered_support,
    parse_selection_manifest,
    quantize_upward,
    quantized_inventory_budget,
    selection_manifest_record,
    serialize_selection_manifest,
    serialize_threshold_certificate,
    threshold_certificate_record,
)

CASES = Path(__file__).parents[1] / "cases" / "n11_threshold_certificate"


def _tiny_certificate(
    *,
    point_weight: Fraction = Fraction(1, 7),
    threshold_weight: Fraction = Fraction(2, 11),
    threshold: int = 2,
    multiplicities: tuple[int, ...] = (1, 2),
) -> ThresholdCertificate:
    outer_side = Fraction(4)
    point = (Fraction(1, 3), Fraction(2, 3))
    atoms = tuple(
        Atom(f"p{index}", x, y, point_weight)
        for index, (x, y) in enumerate(sorted(set(d4_images(*point, outer_side))))
    )
    threshold_atom = ThresholdAtom(
        ((Fraction(1, 2), Fraction(3, 4)), (Fraction(5, 4), Fraction(7, 6))),
        threshold,
        threshold_weight,
        multiplicities,
    )
    threshold_atoms = tuple(
        ThresholdAtom(
            tuple((x, y) for x, y, _ in key[0]),
            key[1],
            threshold_weight,
            tuple(count for _, _, count in key[0]),
        )
        for key in sorted({image.key for image in threshold_atom.images(outer_side)})
    )
    return ThresholdCertificate(
        n=11,
        outer_side=outer_side,
        square_side=Fraction(9, 10),
        atoms=atoms,
        threshold_atoms=threshold_atoms,
        half_tangents=(Fraction(0), Fraction(1, 5)),
    )


def _canonical_manifest_bytes(record: object) -> bytes:
    return (
        json.dumps(
            record,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def test_t025_inventory_is_the_frozen_119_orbits_and_904_atoms() -> None:
    source = t025_certificate()
    inventory = inventory_certificate(source)

    assert inventory.point_orbit_count == 79
    assert inventory.threshold_orbit_count == 40
    assert inventory.orbit_count == 119
    assert inventory.point_atom_count == 584
    assert inventory.threshold_atom_count == 320
    assert inventory.atom_count == 904
    assert inventory.total_budget == Fraction(685457679, 62500000)
    assert ordered_support(inventory) == tuple(sorted(ordered_support(inventory)))


def test_t026_has_t025_support_and_one_exact_common_weight_scale() -> None:
    t025 = inventory_certificate(t025_certificate())
    for filename in (
        "certificate-191-50-net720.json",
        "certificate-191-50-net1440.json",
    ):
        t026_path = CASES / filename
        t026 = inventory_certificate(load(t026_path.read_bytes())[0])

        relation = compare_scaled_support(t025, t026)

        assert relation.support_equal
        assert relation.weights_have_common_scale
        assert relation.matches
        assert relation.common_weight_scale == Fraction(500000000, 498684619)


def test_upward_quantization_has_the_frozen_t025_budget() -> None:
    inventory = inventory_certificate(t025_certificate())

    assert quantize_upward(Fraction(1, 10), 3) == Fraction(1, 3)
    assert quantize_upward(Fraction(2, 3), 3) == Fraction(2, 3)
    assert quantized_inventory_budget(inventory, 30000) == Fraction(82373, 7500)
    assert quantized_inventory_budget(inventory, 30000) < 11


def test_inventory_refuses_a_broken_point_orbit() -> None:
    source = _tiny_certificate()
    broken = ThresholdCertificate(
        n=source.n,
        outer_side=source.outer_side,
        square_side=source.square_side,
        atoms=source.atoms[:-1],
        threshold_atoms=source.threshold_atoms,
        half_tangents=source.half_tangents,
    )

    with pytest.raises(ValueError, match=r"point orbit .* is not D4-complete"):
        inventory_certificate(broken)


def test_inventory_refuses_different_weights_inside_one_orbit() -> None:
    source = _tiny_certificate()
    first = source.atoms[0]
    broken = ThresholdCertificate(
        n=source.n,
        outer_side=source.outer_side,
        square_side=source.square_side,
        atoms=(Atom(first.label, first.x, first.y, first.weight + 1), *source.atoms[1:]),
        threshold_atoms=source.threshold_atoms,
        half_tangents=source.half_tangents,
    )

    with pytest.raises(ValueError, match=r"point orbit .* does not have one weight"):
        inventory_certificate(broken)


def test_threshold_multiplicity_is_part_of_support_and_budget() -> None:
    weighted = inventory_certificate(_tiny_certificate(multiplicities=(1, 2)))
    all_ones = inventory_certificate(_tiny_certificate(multiplicities=(1, 1)))

    relation = compare_scaled_support(weighted, all_ones)

    assert not relation.threshold_support_equal
    assert not relation.support_equal
    assert relation.common_weight_scale is None
    orbit = weighted.threshold_orbits[0]
    assert orbit.token_count == 3
    assert orbit.budget_coefficient == 8


def test_inventory_refuses_a_broken_threshold_orbit() -> None:
    source = _tiny_certificate()
    broken = ThresholdCertificate(
        n=source.n,
        outer_side=source.outer_side,
        square_side=source.square_side,
        atoms=source.atoms,
        threshold_atoms=source.threshold_atoms[:-1],
        half_tangents=source.half_tangents,
    )

    with pytest.raises(ValueError, match=r"threshold orbit .* is not D4-complete"):
        inventory_certificate(broken)


def test_inventory_refuses_non_d4_symmetry_before_orbit_expansion() -> None:
    source = _tiny_certificate()
    broken = ThresholdCertificate(
        n=source.n,
        outer_side=source.outer_side,
        square_side=source.square_side,
        atoms=source.atoms,
        threshold_atoms=source.threshold_atoms,
        half_tangents=source.half_tangents,
        symmetry="C4",
    )

    with pytest.raises(ValueError, match="compression inventory requires D4"):
        inventory_certificate(broken)


def test_catalog_digest_is_canonical_and_weight_sensitive() -> None:
    first = inventory_certificate(_tiny_certificate())
    reordered_source = _tiny_certificate()
    reordered = ThresholdCertificate(
        n=reordered_source.n,
        outer_side=reordered_source.outer_side,
        square_side=reordered_source.square_side,
        atoms=tuple(reversed(reordered_source.atoms)),
        threshold_atoms=tuple(reversed(reordered_source.threshold_atoms)),
        half_tangents=reordered_source.half_tangents,
    )
    second = inventory_certificate(reordered)
    changed = inventory_certificate(_tiny_certificate(point_weight=Fraction(1, 8)))

    assert canonical_catalog_record(first) == canonical_catalog_record(second)
    assert catalog_sha256(first) == catalog_sha256(second)
    assert catalog_sha256(first) != catalog_sha256(changed)
    assert len(catalog_sha256(first)) == 64


def test_t025_catalog_digest_is_frozen() -> None:
    inventory = inventory_certificate(t025_certificate())

    assert catalog_sha256(inventory) == (
        "8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75"
    )


def test_selection_metrics_and_synthetic_decompression_are_exact() -> None:
    inventory = inventory_certificate(_tiny_certificate())
    point = PointOrbitSelection(inventory.point_orbits[0].representative, Fraction(3, 10))
    threshold = ThresholdOrbitSelection(
        inventory.threshold_orbits[0].representative, Fraction(5, 12)
    )
    policy = CompressionPolicy(max_orbits=2, minimum_compression_factor=Fraction(1))

    metrics = measure_selection(inventory, (point,), (threshold,), policy)
    decompressed = decompress_selection(inventory, (point,), (threshold,), policy)

    assert metrics.selected_orbits == 2
    assert metrics.expanded_atoms == 16
    assert metrics.coordinate_parameters == 6
    assert metrics.distinct_weights == 2
    assert metrics.threshold_templates == 1
    assert metrics.total_budget == 8 * Fraction(3, 10) + 8 * Fraction(5, 12)
    assert metrics.budget_below_n
    assert metrics.compression_factor == 1
    assert metrics.satisfies_policy
    assert decompressed.point_mass == 8 * Fraction(3, 10)
    assert decompressed.threshold_budget == 8 * Fraction(5, 12)
    assert decompress_selection(inventory, (point,), (threshold,), policy).to_record() == (
        decompressed.to_record()
    )


def test_full_t025_selection_decompresses_to_a_canonical_equivalent() -> None:
    inventory = inventory_certificate(t025_certificate())
    points = tuple(
        PointOrbitSelection(orbit.representative, orbit.weight)
        for orbit in inventory.point_orbits
    )
    thresholds = tuple(
        ThresholdOrbitSelection(orbit.representative, orbit.weight)
        for orbit in inventory.threshold_orbits
    )
    source_policy = CompressionPolicy(max_orbits=119, minimum_compression_factor=Fraction(1))

    manifest = serialize_selection_manifest(inventory, points, thresholds)
    parsed_points, parsed_thresholds = parse_selection_manifest(manifest, inventory)
    rebuilt = decompress_selection(
        inventory, parsed_points, parsed_thresholds, source_policy
    )

    assert manifest == serialize_selection_manifest(
        inventory, parsed_points, parsed_thresholds
    )
    assert len(selection_manifest_record(inventory, points, thresholds)["orbits"]) == 119
    assert canonical_catalog_record(inventory_certificate(rebuilt)) == (
        canonical_catalog_record(inventory)
    )

    encoded = serialize_threshold_certificate(rebuilt)
    loaded, record = load(encoded)

    assert record == threshold_certificate_record(rebuilt)
    assert canonical_catalog_record(inventory_certificate(loaded)) == (
        canonical_catalog_record(inventory)
    )


def test_default_policy_accepts_a_synthetic_23_orbit_boundary() -> None:
    inventory = inventory_certificate(t025_certificate())
    point_selections = tuple(
        PointOrbitSelection(orbit.representative, Fraction(1, 30000))
        for orbit in inventory.point_orbits[:22]
    )
    threshold_selections = (
        ThresholdOrbitSelection(
            inventory.threshold_orbits[0].representative, Fraction(1, 30000)
        ),
    )
    manifest = serialize_selection_manifest(
        inventory, point_selections, threshold_selections
    )
    parsed_points, parsed_thresholds = parse_selection_manifest(manifest, inventory)

    metrics = measure_selection(inventory, parsed_points, parsed_thresholds)
    decompressed = decompress_selection(inventory, parsed_points, parsed_thresholds)

    assert metrics.selected_orbits == 23
    assert metrics.point_orbits == 22
    assert metrics.threshold_orbits == 1
    assert metrics.compression_factor == Fraction(119, 23)
    assert metrics.satisfies_policy
    assert inventory_certificate(decompressed).point_orbit_count == 22
    assert inventory_certificate(decompressed).threshold_orbit_count == 1

    loaded, _ = load(serialize_threshold_certificate(decompressed))

    assert canonical_catalog_record(inventory_certificate(loaded)) == (
        canonical_catalog_record(inventory_certificate(decompressed))
    )


def test_serializer_refuses_a_net_other_than_the_explicit_t025_net() -> None:
    source = t025_certificate()

    with pytest.raises(ValueError, match="direction net does not equal"):
        serialize_threshold_certificate(
            source,
            ThresholdNetSpec(direction_steps=179, angle_limit=Fraction(207107, 500000)),
        )


def test_default_policy_refuses_24_orbits_before_decompression() -> None:
    inventory = inventory_certificate(t025_certificate())
    selections = tuple(
        PointOrbitSelection(orbit.representative, orbit.weight)
        for orbit in inventory.point_orbits[:24]
    )

    manifest = serialize_selection_manifest(inventory, selections, ())
    parsed_points, parsed_thresholds = parse_selection_manifest(manifest, inventory)
    metrics = measure_selection(inventory, parsed_points, parsed_thresholds)

    assert metrics.selected_orbits == 24
    assert not metrics.within_orbit_ceiling
    assert not metrics.meets_compression_factor
    assert not metrics.satisfies_policy
    with pytest.raises(ValueError, match="selection has 24 orbits"):
        decompress_selection(inventory, parsed_points, parsed_thresholds)


def test_selection_manifest_is_canonical_source_bound_and_nonempty() -> None:
    inventory = inventory_certificate(t025_certificate())
    first = PointOrbitSelection(
        inventory.point_orbits[0].representative, Fraction(1, 17)
    )
    second = PointOrbitSelection(
        inventory.point_orbits[1].representative, Fraction(1, 19)
    )
    threshold = ThresholdOrbitSelection(
        inventory.threshold_orbits[0].representative, Fraction(1, 23)
    )

    canonical = serialize_selection_manifest(
        inventory, (first, second), (threshold,)
    )
    reordered = serialize_selection_manifest(
        inventory, (second, first), (threshold,)
    )
    record = json.loads(canonical)

    assert canonical == reordered
    assert record["source_catalog_sha256"] == catalog_sha256(inventory)
    assert [row["kind"] for row in record["orbits"]] == [
        "point",
        "point",
        "threshold",
    ]
    with pytest.raises(ValueError, match="at least one positive orbit"):
        selection_manifest_record(inventory, (), ())
    with pytest.raises(SelectionManifestError, match="canonically serialized"):
        parse_selection_manifest(
            json.dumps(record, separators=(",", ":")).encode(), inventory
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("duplicate", "selected more than once"),
        ("missing", "fields differ"),
        ("off-support", "outside the source catalog"),
        ("wrong-type", "must be a JSON object"),
        ("wrong-threshold", "outside the source catalog"),
        ("negative", "positive weight"),
        ("zero", "positive weight"),
        ("nonrational-string", "not canonically spelled"),
        ("nonrational-number", "floating"),
        ("foreign-catalog", "foreign source catalog"),
    ],
)
def test_selection_manifest_refuses_x032_mutations(
    mutation: str, message: str
) -> None:
    inventory = inventory_certificate(_tiny_certificate())
    point = PointOrbitSelection(inventory.point_orbits[0].representative, Fraction(1, 7))
    threshold = ThresholdOrbitSelection(
        inventory.threshold_orbits[0].representative, Fraction(2, 11)
    )
    record: dict[str, Any] = selection_manifest_record(
        inventory, (point,), (threshold,)
    )
    rows = cast(list[dict[str, Any]], record["orbits"])
    point_row, threshold_row = rows

    if mutation == "duplicate":
        rows.append(dict(point_row))
    elif mutation == "missing":
        point_row.pop("weight")
    elif mutation == "off-support":
        cast(list[object], point_row["representative"])[0] = "999"
    elif mutation == "wrong-type":
        point_row["kind"] = "threshold"
    elif mutation == "wrong-threshold":
        representative = cast(dict[str, object], threshold_row["representative"])
        representative["threshold"] = 1
    elif mutation == "negative":
        point_row["weight"] = "-1"
    elif mutation == "zero":
        point_row["weight"] = "0"
    elif mutation == "nonrational-string":
        point_row["weight"] = "0.5"
    elif mutation == "nonrational-number":
        point_row["weight"] = 0.5
    elif mutation == "foreign-catalog":
        record["source_catalog_sha256"] = "0" * 64
    else:  # pragma: no cover - the parameter list is the mutation registry
        raise AssertionError(f"unhandled mutation {mutation}")

    with pytest.raises(SelectionManifestError, match=message):
        parse_selection_manifest(_canonical_manifest_bytes(record), inventory)


def test_selection_manifest_refuses_duplicate_keys_and_approximate_json() -> None:
    inventory = inventory_certificate(_tiny_certificate())
    duplicate = (
        b'{"orbits":[],"schema":"packing.squares:ThresholdOrbitSelection/v1",'
        b'"schema":"duplicate","source_catalog_sha256":"' + b"0" * 64 + b'"}\n'
    )
    approximate = (
        b'{"orbits":[],"schema":"packing.squares:ThresholdOrbitSelection/v1",'
        b'"source_catalog_sha256":0.5}\n'
    )

    with pytest.raises(SelectionManifestError, match="duplicate JSON object key"):
        parse_selection_manifest(duplicate, inventory)
    with pytest.raises(SelectionManifestError, match="floating"):
        parse_selection_manifest(approximate, inventory)


@pytest.mark.parametrize("denominator", [0, -1, True])
def test_quantizer_refuses_invalid_denominators(denominator: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        quantize_upward(Fraction(1, 2), denominator)


def test_support_relation_refuses_nonuniform_weight_scaling() -> None:
    reference = inventory_certificate(_tiny_certificate())
    candidate = inventory_certificate(
        _tiny_certificate(point_weight=Fraction(2, 7), threshold_weight=Fraction(3, 11))
    )

    relation = compare_scaled_support(reference, candidate)

    assert relation.support_equal
    assert not relation.weights_have_common_scale
    assert relation.common_weight_scale is None


def test_selection_and_quantization_refuse_inexact_weights() -> None:
    inventory = inventory_certificate(_tiny_certificate())

    with pytest.raises(TypeError, match="exact Fraction"):
        PointOrbitSelection(inventory.point_orbits[0].representative, 0.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="exact Fraction"):
        quantize_upward(0.5, 10)  # type: ignore[arg-type]
