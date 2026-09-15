#!/usr/bin/env python3
"""Admit Route S's exact, target-blind threshold-certificate compression surface.

This command does not optimize a certificate and does not run a coverage verifier.  It
binds the fixed T-025 control and T-026 support/rescaling sentinel to one deterministic
orbit catalogue, checks the predeclared compression policy, and exercises the
decompressor on a synthetic selection.  ``--output`` writes only the typed admission
receipt; ``--check`` recomputes that receipt and compares it with the retained bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from collections.abc import Sequence
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path, PurePosixPath
from typing import Any, Final, Never, cast

from strif import atomic_output_file

from devtools.decide_threshold_certificate import load as load_threshold_certificate
from sqpack.fractional.threshold_compression import (
    SELECTION_MANIFEST_SCHEMA,
    CompressionPolicy,
    OrbitInventory,
    PointOrbitSelection,
    SelectionManifestError,
    ThresholdOrbitSelection,
    canonical_catalog_record,
    catalog_sha256,
    compare_scaled_support,
    decompress_selection,
    inventory_certificate,
    measure_selection,
    ordered_support,
    parse_selection_manifest,
    quantized_inventory_budget,
    selection_manifest_record,
    serialize_selection_manifest,
    serialize_threshold_certificate,
)

PACKING = Path(__file__).resolve().parent.parent
REPOSITORY = PACKING.parent
ADMISSION: Final = PACKING / (
    "cases/n11_threshold_certificate/route-s-compression-admission.json"
)
RECEIPT: Final = PACKING / (
    "cases/n11_threshold_certificate/route-s-compression-admission-receipt.json"
)
ADMISSION_PATH: Final = (
    "packing/cases/n11_threshold_certificate/route-s-compression-admission.json"
)
SOURCE_PATH: Final = "packing/cases/n11_threshold_certificate/certificate.json"
T025_CERTIFICATE_SHA256: Final = (
    "3935651af614eb3e9a1926179925f98643beb17ed1764a323fe83a527f4bad5c"
)
T025_CATALOG_SHA256: Final = (
    "8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75"
)
T026_NET720_CERTIFICATE_SHA256: Final = (
    "fff8b2bcab95a0041e69fec30c704dd708908125883b6ed645bc2c653ecbf8cf"
)
T026_NET720_COROLLARY_SHA256: Final = (
    "c955057bddc1ae45775d66f094781d54cd7c07e1c0d75a2691f48ab73130298b"
)
T026_NET720_CATALOG_SHA256: Final = (
    "b797cdf458d60623cf49e063df9f2c73ffc4a3c3f7be1f17f57fda32dc76e3f2"
)
T026_NET1440_CERTIFICATE_SHA256: Final = (
    "dc2da20c75d952690c93d67fb4b3eb8552e879585902fde98eedc9b3179ed3d0"
)
T026_NET1440_COROLLARY_SHA256: Final = (
    "04fd6bbca1941671ddbabbe359219011b8217818b0a291f4c9a00f5fa7834f8e"
)
T026_NET1440_CATALOG_SHA256: Final = (
    "43c2b94f932bb233c71191940447a6d761387041637dab72c9a1a5ed89aea925"
)
SCHEMA: Final = "packing.squares:ThresholdCompressionAdmission/v1"
RECEIPT_SCHEMA: Final = "packing.squares:ThresholdCompressionAdmissionReceipt/v1"
MAX_JSON_BYTES: Final = 256 * 1024
MAX_JSON_DEPTH: Final = 16
MAX_INTEGER_DIGITS: Final = 6
SHA256_LENGTH: Final = 64
MAX_CERTIFICATE_BYTES: Final = 2 * 1024 * 1024
QUANTIZATION_DENOMINATOR: Final = 30_000
SYNTHETIC_WEIGHT: Final = Fraction(1, QUANTIZATION_DENOMINATOR)


@dataclass(frozen=True, slots=True)
class SentinelAnchor:
    """Checker-owned identity for one independently authenticated T-026 sentinel."""

    direction_steps: int
    role: str
    path: str
    sha256: str
    source_path: str
    source_sha256: str
    catalog_sha256: str


SENTINELS: Final = (
    SentinelAnchor(
        direction_steps=720,
        role="T-026 720-step support and rescaling sentinel",
        path=(
            "packing/cases/n11_threshold_certificate/"
            "t-026-net720-dilation-limit-corollary.json"
        ),
        sha256=T026_NET720_COROLLARY_SHA256,
        source_path=(
            "packing/cases/n11_threshold_certificate/certificate-191-50-net720.json"
        ),
        source_sha256=T026_NET720_CERTIFICATE_SHA256,
        catalog_sha256=T026_NET720_CATALOG_SHA256,
    ),
    SentinelAnchor(
        direction_steps=1440,
        role="T-026 1440-step support and rescaling sentinel",
        path=(
            "packing/cases/n11_threshold_certificate/"
            "t-026-dilation-limit-corollary.json"
        ),
        sha256=T026_NET1440_COROLLARY_SHA256,
        source_path=(
            "packing/cases/n11_threshold_certificate/certificate-191-50-net1440.json"
        ),
        source_sha256=T026_NET1440_CERTIFICATE_SHA256,
        catalog_sha256=T026_NET1440_CATALOG_SHA256,
    ),
)


class AdmissionError(ValueError):
    """The admission record or one of its bound sources is not admissible."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise AdmissionError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _integer(raw: str) -> int:
    digits = raw.removeprefix("-")
    if len(digits) > MAX_INTEGER_DIGITS:
        raise AdmissionError("JSON integer exceeds the digit limit")
    return int(raw)


def _inexact(raw: str) -> Never:
    raise AdmissionError(f"floating or nonfinite JSON number {raw!r} is forbidden")


def _bounded_regular_bytes(path: Path, *, limit: int, label: str) -> bytes:
    """Read a regular, non-symlink file without letting its size drive allocation."""
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise AdmissionError(f"{label} must be a regular file")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise AdmissionError(f"{label} exceeds the {limit}-byte limit")
    return data


def _check_depth(text: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise AdmissionError("JSON nesting exceeds the depth limit")
        elif char in "]}":
            depth -= 1


def load_json(
    path: Path, *, label: str, limit: int = MAX_JSON_BYTES
) -> tuple[dict[str, Any], bytes]:
    """Load one bounded exact JSON object, refusing aliases and approximate numbers."""
    try:
        data = _bounded_regular_bytes(path, limit=limit, label=label)
        text = data.decode("utf-8")
        _check_depth(text)
        decoded = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_int=_integer,
            parse_float=_inexact,
            parse_constant=_inexact,
        )
    except AdmissionError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise AdmissionError(f"cannot read {label}: {error}") from None
    if not isinstance(decoded, dict):
        raise AdmissionError(f"{label} must be a JSON object")
    return cast(dict[str, Any], decoded), data


def _keys(value: object, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdmissionError(f"{label} must be a JSON object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AdmissionError(f"{label} fields differ: missing={missing}, extra={extra}")
    return cast(dict[str, Any], value)


def _repo_path(value: object, *, expected: str, label: str) -> Path:
    """Accept exactly one normalized repository-relative path and keep it in the repo."""
    if not isinstance(value, str):
        raise AdmissionError(f"{label} must be a repository-relative path string")
    pure = PurePosixPath(value)
    malformed = (
        pure.is_absolute()
        or "." in pure.parts
        or ".." in pure.parts
        or pure.as_posix() != value
    )
    if malformed:
        raise AdmissionError(f"{label} is not a normalized repository-relative path")
    if value != expected:
        raise AdmissionError(f"{label} is {value!r}; expected frozen path {expected!r}")
    path = (REPOSITORY / pure).absolute()
    resolved = path.resolve()
    if not resolved.is_relative_to(REPOSITORY.resolve()):
        raise AdmissionError(f"{label} escapes the repository")
    if resolved != path:
        raise AdmissionError(f"{label} resolves through a symlink")
    return path


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != SHA256_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise AdmissionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _load_certificate(path: Path, *, label: str) -> tuple[object, bytes]:
    data = _bounded_regular_bytes(path, limit=MAX_CERTIFICATE_BYTES, label=label)
    try:
        certificate, _ = load_threshold_certificate(data)
    except (TypeError, ValueError, RecursionError) as error:
        raise AdmissionError(f"cannot load {label}: {error}") from None
    return certificate, data


def _expected_admission(
    *,
    source_inventory: OrbitInventory,
    sentinel_inventories: tuple[OrbitInventory, ...],
) -> dict[str, Any]:
    if len(sentinel_inventories) != len(SENTINELS):
        raise AdmissionError("the ordered T-026 sentinel inventory is incomplete")
    sentinel_records: list[dict[str, Any]] = []
    for anchor, sentinel_inventory in zip(
        SENTINELS, sentinel_inventories, strict=True
    ):
        relation = compare_scaled_support(source_inventory, sentinel_inventory)
        if not relation.matches:
            raise AdmissionError(
                f"T-026 net-{anchor.direction_steps} does not preserve T-025 support "
                "under one exact scale"
            )
        sentinel_records.append(
            {
                "direction_steps": anchor.direction_steps,
                "role": anchor.role,
                "path": anchor.path,
                "sha256": anchor.sha256,
                "source_path": anchor.source_path,
                "source_sha256": anchor.source_sha256,
                "catalog_sha256": anchor.catalog_sha256,
                "point_support_equal": relation.point_support_equal,
                "threshold_support_equal": relation.threshold_support_equal,
                "common_weight_scale": str(relation.common_weight_scale),
                "support_equal": relation.support_equal,
                "weights_have_common_scale": relation.weights_have_common_scale,
            }
        )
    rounded_budget = quantized_inventory_budget(source_inventory, QUANTIZATION_DENOMINATOR)
    if rounded_budget >= source_inventory.n:
        raise AdmissionError("the denominator-30000 upward-rounding control exceeds budget")
    return {
        "schema": SCHEMA,
        "control": {
            "role": "matched T-025 control",
            "path": SOURCE_PATH,
            "sha256": T025_CERTIFICATE_SHA256,
            "n": source_inventory.n,
            "outer_side": str(source_inventory.outer_side),
            "square_side": str(source_inventory.square_side),
            "symmetry": source_inventory.symmetry,
            "total_budget": str(source_inventory.total_budget),
            "catalog_sha256": T025_CATALOG_SHA256,
            "point_orbits": source_inventory.point_orbit_count,
            "threshold_orbits": source_inventory.threshold_orbit_count,
            "orbits": source_inventory.orbit_count,
            "point_atoms": source_inventory.point_atom_count,
            "threshold_atoms": source_inventory.threshold_atom_count,
            "atoms": source_inventory.atom_count,
        },
        "sentinels": sentinel_records,
        "family": {
            "kind": "fixed-source-support D4-orbit selection",
            "catalog_schema": canonical_catalog_record(source_inventory)["schema"],
            "manifest_schema": SELECTION_MANIFEST_SCHEMA,
            "manifest_nonempty": True,
            "manifest_source_bound": True,
            "selection_unit": "one complete source D4 orbit",
            "geometry_rule": "select source orbit representatives without moving sites",
            "weight_rule": "one positive exact rational weight per selected orbit",
            "max_orbits": 23,
            "minimum_compression_factor": "5",
            "baseline_orbits": source_inventory.orbit_count,
            "success_rule": (
                "at most 23 selected orbits and compression factor at least 5, followed "
                "on a later branch by unchanged exact budget and complete coverage replay"
            ),
            "park_rule": (
                "park only this fixed-source-support family after exact infeasibility or "
                "retained counterexample cells; do not refute Route S"
            ),
        },
        "quantization_control": {
            "role": "arithmetic control only; not support-compression success",
            "direction": "upward",
            "denominator": QUANTIZATION_DENOMINATOR,
            "rounded_budget": str(rounded_budget),
            "budget_below_n": True,
        },
        "execution_boundary": {
            "target_ran": False,
            "optimizer_ran": False,
            "coverage_ran": False,
            "candidate_created": False,
            "experiment_created": False,
        },
    }


def _validate_paths_and_digests(
    admission: dict[str, Any],
) -> None:
    """Refuse path aliases and any substitution for a checker-owned digest anchor."""
    _keys(
        admission,
        {
            "schema",
            "control",
            "sentinels",
            "family",
            "quantization_control",
            "execution_boundary",
        },
        "admission",
    )
    if admission["schema"] != SCHEMA:
        raise AdmissionError(f"admission schema must be {SCHEMA!r}")
    control = _keys(
        admission["control"],
        {
            "role",
            "path",
            "sha256",
            "n",
            "outer_side",
            "square_side",
            "symmetry",
            "total_budget",
            "catalog_sha256",
            "point_orbits",
            "threshold_orbits",
            "orbits",
            "point_atoms",
            "threshold_atoms",
            "atoms",
        },
        "control",
    )
    _repo_path(control["path"], expected=SOURCE_PATH, label="control.path")
    declared = _digest(control["sha256"], label="control.sha256")
    if declared != T025_CERTIFICATE_SHA256:
        raise AdmissionError("control digest differs from the checker-owned T-025 anchor")
    if (
        _digest(control["catalog_sha256"], label="control.catalog_sha256")
        != T025_CATALOG_SHA256
    ):
        raise AdmissionError(
            "control catalogue digest differs from the checker-owned T-025 anchor"
        )
    sentinels = admission["sentinels"]
    if not isinstance(sentinels, list) or len(sentinels) != len(SENTINELS):
        raise AdmissionError("sentinels must be the ordered 720-step and 1440-step pair")
    for index, (value, anchor) in enumerate(zip(sentinels, SENTINELS, strict=True)):
        label = f"sentinels[{index}]"
        sentinel = _keys(
            value,
            {
                "direction_steps",
                "role",
                "path",
                "sha256",
                "source_path",
                "source_sha256",
                "catalog_sha256",
                "point_support_equal",
                "threshold_support_equal",
                "common_weight_scale",
                "support_equal",
                "weights_have_common_scale",
            },
            label,
        )
        if sentinel["direction_steps"] != anchor.direction_steps:
            raise AdmissionError(f"{label} is out of the frozen sentinel order")
        _repo_path(sentinel["path"], expected=anchor.path, label=f"{label}.path")
        _repo_path(
            sentinel["source_path"],
            expected=anchor.source_path,
            label=f"{label}.source_path",
        )
        if _digest(sentinel["sha256"], label=f"{label}.sha256") != anchor.sha256:
            raise AdmissionError(
                f"{label} digest differs from the checker-owned corollary anchor"
            )
        if (
            _digest(sentinel["source_sha256"], label=f"{label}.source_sha256")
            != anchor.source_sha256
        ):
            raise AdmissionError(
                f"{label} source digest differs from the checker-owned certificate anchor"
            )
        if (
            _digest(sentinel["catalog_sha256"], label=f"{label}.catalog_sha256")
            != anchor.catalog_sha256
        ):
            raise AdmissionError(
                f"{label} catalogue digest differs from the checker-owned catalogue anchor"
            )


def _manifest_roundtrip(
    inventory: OrbitInventory,
    point_selections: tuple[PointOrbitSelection, ...],
    threshold_selections: tuple[ThresholdOrbitSelection, ...],
) -> tuple[
    tuple[PointOrbitSelection, ...],
    tuple[ThresholdOrbitSelection, ...],
    bytes,
]:
    manifest = serialize_selection_manifest(
        inventory, point_selections, threshold_selections
    )
    parsed_points, parsed_thresholds = parse_selection_manifest(manifest, inventory)
    if (parsed_points, parsed_thresholds) != (point_selections, threshold_selections):
        raise AdmissionError("selection-manifest round trip changed the selected orbits")
    if (
        serialize_selection_manifest(inventory, parsed_points, parsed_thresholds)
        != manifest
    ):
        raise AdmissionError("selection-manifest serialization is not byte stable")
    return parsed_points, parsed_thresholds, manifest


def _loaded_inventory(certificate: object) -> OrbitInventory:
    encoded = serialize_threshold_certificate(certificate)  # type: ignore[arg-type]
    loaded, _ = load_threshold_certificate(encoded)
    return inventory_certificate(loaded)  # type: ignore[arg-type]


def _synthetic_selections(
    inventory: OrbitInventory,
) -> tuple[tuple[PointOrbitSelection, ...], tuple[ThresholdOrbitSelection, ...]]:
    policy = CompressionPolicy()
    point_count = min(len(inventory.point_orbits), policy.max_orbits - 1)
    points = tuple(
        PointOrbitSelection(orbit.representative, SYNTHETIC_WEIGHT)
        for orbit in inventory.point_orbits[:point_count]
    )
    threshold_needed = policy.max_orbits - point_count
    thresholds = tuple(
        ThresholdOrbitSelection(orbit.representative, SYNTHETIC_WEIGHT)
        for orbit in inventory.threshold_orbits[:threshold_needed]
    )
    return points, thresholds


def _synthetic_decompressor_check(inventory: OrbitInventory) -> dict[str, Any]:
    """Exercise the admitted family at its ceiling without making a candidate."""
    policy = CompressionPolicy()
    points, thresholds = _synthetic_selections(inventory)
    parsed_points, parsed_thresholds, manifest = _manifest_roundtrip(
        inventory, points, thresholds
    )
    metrics = measure_selection(inventory, parsed_points, parsed_thresholds, policy)
    decompressed = decompress_selection(
        inventory, parsed_points, parsed_thresholds, policy
    )
    reconstructed = _loaded_inventory(decompressed)
    if reconstructed.atom_count != metrics.expanded_atoms:
        raise AdmissionError("synthetic decompressor disagrees with its exact atom metric")
    if reconstructed.total_budget != metrics.total_budget:
        raise AdmissionError("synthetic decompressor changed its uniform exact weights")
    return {
        "role": "target-blind decompressor control",
        "synthetic_weight": str(SYNTHETIC_WEIGHT),
        "manifest_schema": SELECTION_MANIFEST_SCHEMA,
        "manifest_sha256": _sha256(manifest),
        "manifest_bytes": len(manifest),
        "manifest_roundtrip": True,
        "certificate_loader_roundtrip": True,
        "baseline_orbits": metrics.baseline_orbits,
        "point_orbits": metrics.point_orbits,
        "threshold_orbits": metrics.threshold_orbits,
        "selected_orbits": metrics.selected_orbits,
        "expanded_atoms": metrics.expanded_atoms,
        "coordinate_parameters": metrics.coordinate_parameters,
        "distinct_weights": metrics.distinct_weights,
        "threshold_templates": metrics.threshold_templates,
        "compression_factor": str(metrics.compression_factor),
        "within_orbit_ceiling": metrics.within_orbit_ceiling,
        "meets_compression_factor": metrics.meets_compression_factor,
        "satisfies_policy": metrics.satisfies_policy,
        "decompressed_point_atoms": reconstructed.point_atom_count,
        "decompressed_threshold_atoms": reconstructed.threshold_atom_count,
        "decompressed_budget": str(reconstructed.total_budget),
    }


def _full_control_roundtrip(inventory: OrbitInventory) -> dict[str, Any]:
    """Round-trip a full manifest and recover T-025 through its existing loader."""
    points = tuple(
        PointOrbitSelection(orbit.representative, orbit.weight)
        for orbit in inventory.point_orbits
    )
    thresholds = tuple(
        ThresholdOrbitSelection(orbit.representative, orbit.weight)
        for orbit in inventory.threshold_orbits
    )
    parsed_points, parsed_thresholds, manifest = _manifest_roundtrip(
        inventory, points, thresholds
    )
    policy = CompressionPolicy(
        max_orbits=inventory.orbit_count,
        minimum_compression_factor=Fraction(1),
    )
    reconstructed = _loaded_inventory(
        decompress_selection(inventory, parsed_points, parsed_thresholds, policy)
    )
    if canonical_catalog_record(reconstructed) != canonical_catalog_record(inventory):
        raise AdmissionError("full T-025 decompression is not canonically equivalent")
    return {
        "role": "full authenticated T-025 manifest and decompressor control",
        "canonical_equivalent": True,
        "manifest_schema": SELECTION_MANIFEST_SCHEMA,
        "manifest_sha256": _sha256(manifest),
        "manifest_bytes": len(manifest),
        "manifest_roundtrip": True,
        "certificate_loader_roundtrip": True,
        "catalog_sha256": catalog_sha256(reconstructed),
        "orbits": reconstructed.orbit_count,
        "atoms": reconstructed.atom_count,
        "total_budget": str(reconstructed.total_budget),
    }


def _mutation_controls(inventory: OrbitInventory) -> dict[str, bool]:
    """Execute every target-blind malformed-manifest class named by X-032."""
    points, thresholds = _synthetic_selections(inventory)
    base = selection_manifest_record(inventory, points, thresholds)
    rows = cast(list[dict[str, Any]], base["orbits"])
    threshold_index = next(
        index for index, row in enumerate(rows) if row["kind"] == "threshold"
    )
    noncanonical_d4 = next(
        member
        for member in inventory.point_orbits[0].members
        if member != inventory.point_orbits[0].representative
    )

    mutations: dict[str, dict[str, Any]] = {}
    for name in (
        "duplicate",
        "missing",
        "off_support",
        "wrong_type",
        "wrong_threshold",
        "non_d4",
        "negative",
        "nonrational",
    ):
        mutations[name] = deepcopy(base)

    duplicate_rows = cast(list[dict[str, Any]], mutations["duplicate"]["orbits"])
    duplicate_rows.append(deepcopy(duplicate_rows[0]))
    missing_rows = cast(list[dict[str, Any]], mutations["missing"]["orbits"])
    del missing_rows[0]["weight"]
    off_support_rows = cast(list[dict[str, Any]], mutations["off_support"]["orbits"])
    off_support_rows[0]["representative"] = ["1/7", "1/11"]
    wrong_type_rows = cast(list[dict[str, Any]], mutations["wrong_type"]["orbits"])
    wrong_type_rows[0]["kind"] = "threshold"
    wrong_threshold_rows = cast(
        list[dict[str, Any]], mutations["wrong_threshold"]["orbits"]
    )
    wrong_threshold_rep = cast(
        dict[str, Any], wrong_threshold_rows[threshold_index]["representative"]
    )
    wrong_threshold_rep["threshold"] = 1
    non_d4_rows = cast(list[dict[str, Any]], mutations["non_d4"]["orbits"])
    non_d4_rows[0]["representative"] = [str(value) for value in noncanonical_d4]
    negative_rows = cast(list[dict[str, Any]], mutations["negative"]["orbits"])
    negative_rows[0]["weight"] = str(-SYNTHETIC_WEIGHT)
    nonrational_rows = cast(list[dict[str, Any]], mutations["nonrational"]["orbits"])
    nonrational_rows[0]["weight"] = "sqrt(2)"

    outcomes: dict[str, bool] = {}
    for name, record in mutations.items():
        try:
            parse_selection_manifest(_canonical_json(record), inventory)
        except SelectionManifestError:
            outcomes[name] = True
        else:
            raise AdmissionError(f"X-032 {name.replace('_', '-')} mutation was accepted")
    return outcomes


def _policy_boundary_check(inventory: OrbitInventory) -> dict[str, Any]:
    """Accept 23 selected orbits and refuse 24 before any coverage code can run."""
    selections = tuple(
        PointOrbitSelection(orbit.representative, SYNTHETIC_WEIGHT)
        for orbit in inventory.point_orbits[:24]
    )
    points, thresholds, manifest = _manifest_roundtrip(inventory, selections, ())
    metrics = measure_selection(inventory, points, thresholds)
    if metrics.selected_orbits != 24 or metrics.satisfies_policy:
        raise AdmissionError("the 24-orbit boundary does not violate the frozen policy")
    try:
        decompress_selection(inventory, points, thresholds)
    except ValueError:
        refused = True
    else:
        raise AdmissionError("the decompressor accepted a 24-orbit manifest")
    return {
        "accepted_orbits": 23,
        "rejected_orbits": metrics.selected_orbits,
        "rejected_manifest_sha256": _sha256(manifest),
        "rejected_before_decompression": refused,
        "coverage_ran": False,
    }


def _authenticate_inventory(
    *, path: Path, label: str, byte_sha256: str, catalog_digest: str
) -> OrbitInventory:
    certificate, certificate_bytes = _load_certificate(path, label=label)
    actual_digest = _sha256(certificate_bytes)
    if actual_digest != byte_sha256:
        raise AdmissionError(f"{label} differs from its checker-owned byte anchor")
    inventory = inventory_certificate(certificate)  # type: ignore[arg-type]
    if catalog_sha256(inventory) != catalog_digest:
        raise AdmissionError(f"{label} differs from its checker-owned catalogue anchor")
    return inventory


def _authenticate_sentinel(anchor: SentinelAnchor) -> OrbitInventory:
    """Authenticate one T-026 corollary, source, net size, and catalogue independently."""
    record_path = _repo_path(anchor.path, expected=anchor.path, label="sentinel path")
    source_path = _repo_path(
        anchor.source_path, expected=anchor.source_path, label="sentinel source path"
    )
    record, record_bytes = load_json(
        record_path, label=f"T-026 net-{anchor.direction_steps} limit record"
    )
    if _sha256(record_bytes) != anchor.sha256:
        raise AdmissionError(
            f"T-026 net-{anchor.direction_steps} record differs from its checker-owned anchor"
        )
    inventory = _authenticate_inventory(
        path=source_path,
        label=f"T-026 net-{anchor.direction_steps} source certificate",
        byte_sha256=anchor.source_sha256,
        catalog_digest=anchor.catalog_sha256,
    )
    source = _keys(
        record.get("source"),
        {
            "accepted_conditions",
            "certificate",
            "coarse_containment",
            "half_gap_tangent",
            "minimum_cell_charge",
            "n",
            "outer_side",
            "point_atoms",
            "sha256",
            "square_side",
            "threshold_atoms",
            "total_budget",
            "variant",
        },
        f"T-026 net-{anchor.direction_steps} source",
    )
    _repo_path(
        source["certificate"],
        expected=anchor.source_path,
        label=f"T-026 net-{anchor.direction_steps} source.certificate",
    )
    if (
        _digest(source["sha256"], label=f"T-026 net-{anchor.direction_steps} source.sha256")
        != anchor.source_sha256
    ):
        raise AdmissionError(
            f"T-026 net-{anchor.direction_steps} record does not bind its source anchor"
        )
    if len(inventory.half_tangents) - 1 != anchor.direction_steps:
        raise AdmissionError(
            f"T-026 net-{anchor.direction_steps} certificate has the wrong direction net"
        )
    return inventory


def build_receipt(admission_path: Path = ADMISSION) -> dict[str, Any]:
    """Recompute the complete admission receipt without any scientific target work."""
    admission, admission_bytes = load_json(admission_path, label="admission record")
    top = _keys(
        admission,
        {
            "schema",
            "control",
            "sentinels",
            "family",
            "quantization_control",
            "execution_boundary",
        },
        "admission",
    )
    if not isinstance(top["control"], dict) or not isinstance(top["sentinels"], list):
        raise AdmissionError("control must be an object and sentinels must be an array")
    control = cast(dict[str, Any], top["control"])
    _validate_paths_and_digests(admission)
    source_path = _repo_path(control.get("path"), expected=SOURCE_PATH, label="control.path")
    source_inventory = _authenticate_inventory(
        path=source_path,
        label="T-025 certificate",
        byte_sha256=T025_CERTIFICATE_SHA256,
        catalog_digest=T025_CATALOG_SHA256,
    )
    sentinel_inventories = tuple(_authenticate_sentinel(anchor) for anchor in SENTINELS)
    source_support = ordered_support(source_inventory)
    if len(source_support) != source_inventory.orbit_count:
        raise AdmissionError("ordered source support does not cover every orbit once")
    expected = _expected_admission(
        source_inventory=source_inventory,
        sentinel_inventories=sentinel_inventories,
    )
    if admission != expected:
        raise AdmissionError("admission record differs from its exact derived contract")
    rounded_budget = quantized_inventory_budget(source_inventory, QUANTIZATION_DENOMINATOR)
    sentinel_receipts: list[dict[str, Any]] = []
    for anchor, inventory in zip(SENTINELS, sentinel_inventories, strict=True):
        relation = compare_scaled_support(source_inventory, inventory)
        sentinel_receipts.append(
            {
                "direction_steps": anchor.direction_steps,
                "path": anchor.path,
                "sha256": anchor.sha256,
                "source_path": anchor.source_path,
                "source_sha256": anchor.source_sha256,
                "catalog_sha256": anchor.catalog_sha256,
                "point_support_equal": relation.point_support_equal,
                "threshold_support_equal": relation.threshold_support_equal,
                "support_equal": relation.support_equal,
                "common_weight_scale": str(relation.common_weight_scale),
                "weights_have_common_scale": relation.weights_have_common_scale,
                "reproduced": relation.matches,
            }
        )
    return {
        "schema": RECEIPT_SCHEMA,
        "status": "admitted",
        "admission_blockers": [],
        "admission": {
            "path": ADMISSION_PATH,
            "sha256": _sha256(admission_bytes),
        },
        "control": {
            "path": SOURCE_PATH,
            "sha256": T025_CERTIFICATE_SHA256,
            "catalog_sha256": T025_CATALOG_SHA256,
            "support_keys": len(source_support),
            "orbits": source_inventory.orbit_count,
            "atoms": source_inventory.atom_count,
            "total_budget": str(source_inventory.total_budget),
            "reproduced": True,
            "decompressor_roundtrip": _full_control_roundtrip(source_inventory),
        },
        "sentinels": sentinel_receipts,
        "quantization_control": {
            "denominator": QUANTIZATION_DENOMINATOR,
            "rounded_budget": str(rounded_budget),
            "budget_below_n": rounded_budget < source_inventory.n,
            "support_changed": False,
            "research_success": False,
        },
        "synthetic_decompressor": _synthetic_decompressor_check(source_inventory),
        "policy_boundary": _policy_boundary_check(source_inventory),
        "mutation_controls": _mutation_controls(source_inventory),
        "target_ran": False,
        "optimizer_ran": False,
        "coverage_ran": False,
        "candidate_created": False,
        "experiment_created": False,
        "scope": (
            "Target-blind instrument admitted after source-distinct review. No coverage, "
            "optimizer, candidate certificate, compression verdict, or improved n=11 "
            "bound is established."
        ),
    }


def _check_receipt(path: Path, encoded: bytes) -> None:
    retained = _bounded_regular_bytes(path, limit=MAX_JSON_BYTES, label="retained receipt")
    if retained != encoded:
        raise AdmissionError("retained Route S compression admission receipt is stale")


def _write_receipt(output: Path, encoded: bytes, *, admission: Path) -> None:
    protected = {
        admission.resolve(),
        (REPOSITORY / SOURCE_PATH).resolve(),
    }
    protected.update((REPOSITORY / anchor.path).resolve() for anchor in SENTINELS)
    protected.update((REPOSITORY / anchor.source_path).resolve() for anchor in SENTINELS)
    if output.resolve() in protected:
        raise AdmissionError("receipt output may not overwrite an input")
    with atomic_output_file(output) as temporary:
        temporary.write_bytes(encoded)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    command.add_argument("--admission", type=Path, default=ADMISSION)
    command.add_argument("--receipt", type=Path, default=RECEIPT)
    mode = command.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path, help="write the recomputed receipt here")
    mode.add_argument("--check", action="store_true", help="compare with the retained receipt")
    return command


def main(argv: Sequence[str] | None = None) -> int:
    options = parser().parse_args(argv)
    try:
        receipt = build_receipt(options.admission)
        encoded = _canonical_json(receipt)
        if options.check:
            _check_receipt(options.receipt, encoded)
            print("Route S compression checkpoint check passed")
        else:
            output = cast(Path, options.output)
            _write_receipt(output, encoded, admission=options.admission)
            print(f"Route S compression admission receipt written: {output}")
    except (OSError, ValueError) as error:
        print(f"Route S compression admission refused: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
