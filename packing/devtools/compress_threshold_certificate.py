#!/usr/bin/env python3
"""Produce a Route S T-025 compression receipt for exp-161.

This command authenticates the frozen T-025 source, inventories U025, and replays the
admitted 23-orbit accept / 24-orbit reject policy.  It does not run a coverage verifier
and does not emit a candidate certificate.  ``--authorize-target exp-161`` is the only
flag that may later permit a search; without it the receipt records ``target_ran:
false`` after the controls.  A cardinality-and-budget HiGHS MIP is formulated only as an
incomplete sketch: it does not encode closed-core coverage, so this producer never
treats a feasible N+ from that program as an H-163 result.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Final, cast

from strif import atomic_output_file

from devtools.admit_threshold_compression import (
    MAX_CERTIFICATE_BYTES,
    REVISION_LENGTH,
    SENTINELS,
    SHA256_LENGTH,
    SOURCE_PATH,
    SOURCE_REVISION,
    AdmissionError,
    _full_control_roundtrip,
    _policy_boundary_check,
    _synthetic_decompressor_check,
)
from devtools.decide_threshold_certificate import load as load_threshold_certificate
from sqpack.fractional.threshold import ThresholdCertificate
from sqpack.fractional.threshold_compression import (
    OrbitInventory,
    catalog_sha256,
    inventory_certificate,
)

PACKING = Path(__file__).resolve().parent.parent
REPOSITORY = PACKING.parent
FROZEN_SOURCE_PACKING: Final = Path("cases/n11_threshold_certificate/certificate.json")
FROZEN_CATALOG_SHA256: Final = (
    "8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75"
)
FROZEN_MAX_ORBITS: Final = 23
FROZEN_BUDGET_BELOW: Final = 11
FROZEN_LEAST_CHARGE: Final = 1
AUTHORIZED_TARGET: Final = "exp-161"
RECEIPT_SCHEMA: Final = "packing.squares:ThresholdCompressionProducerReceipt/v1"


class CompressionError(ValueError):
    """The producer refused a source, catalog, policy, or authorization guard."""


def _git_content(revision: str, path: str, *, label: str) -> bytes:
    try:
        return subprocess.run(
            ["git", "show", f"{revision}:{path}"],
            cwd=REPOSITORY,
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode(errors="replace").strip() or "git show failed"
        raise CompressionError(f"cannot read {label} at {revision}: {detail}") from error


def _bounded_regular_bytes(path: Path, *, limit: int, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise CompressionError(f"{label} must be a regular file")
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise CompressionError(f"{label} exceeds the {limit}-byte limit")
    return data


def _revision(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != REVISION_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise CompressionError(f"{label} must be a full lowercase Git revision")
    return value


def _digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != SHA256_LENGTH
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise CompressionError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _bind_repository_source(path: Path, revision: str, *, label: str) -> bytes:
    """Return the complete bytes after comparing them with one Git revision and path."""
    _revision(revision, label="source revision")
    try:
        relative = path.resolve().relative_to(REPOSITORY.resolve()).as_posix()
    except ValueError as error:
        raise CompressionError(f"{label} is outside the repository") from error
    current = _bounded_regular_bytes(path, limit=MAX_CERTIFICATE_BYTES, label=label)
    reviewed = _git_content(revision, relative, label=label)
    if current != reviewed:
        raise CompressionError(f"{label} differs from its declared Git revision and path")
    return current


def _load_certificate_bytes(data: bytes, *, label: str) -> ThresholdCertificate:
    try:
        certificate, _ = load_threshold_certificate(data)
    except (TypeError, ValueError, RecursionError) as error:
        raise CompressionError(f"cannot load {label}: {error}") from None
    return certificate


def _require_frozen_policy(*, max_orbits: int, budget_below: int, least_charge: int) -> None:
    if max_orbits != FROZEN_MAX_ORBITS:
        raise CompressionError(
            f"--max-orbits must be the frozen H-163 ceiling {FROZEN_MAX_ORBITS}"
        )
    if budget_below != FROZEN_BUDGET_BELOW:
        raise CompressionError(
            f"--budget-below must be the frozen H-163 budget bound {FROZEN_BUDGET_BELOW}"
        )
    if least_charge != FROZEN_LEAST_CHARGE:
        raise CompressionError(
            f"--least-charge must be the frozen H-163 least charge {FROZEN_LEAST_CHARGE}"
        )


def _require_authorization(authorize_target: str | None) -> str | None:
    if authorize_target is None:
        return None
    if authorize_target != AUTHORIZED_TARGET:
        raise CompressionError(
            f"--authorize-target {authorize_target!r} is not {AUTHORIZED_TARGET}; "
            "refusing to construct a candidate"
        )
    return authorize_target


def resolve_source(source: Path | None) -> Path:
    """Accept only the frozen T-025 certificate, as a packing- or repository-relative path."""
    expected = (REPOSITORY / SOURCE_PATH).resolve()
    if source is None:
        path = expected
    elif source.is_absolute():
        path = source
    else:
        spelling = source.as_posix()
        if spelling == SOURCE_PATH:
            path = REPOSITORY / SOURCE_PATH
        elif spelling == FROZEN_SOURCE_PACKING.as_posix():
            path = PACKING / FROZEN_SOURCE_PACKING
        else:
            raise CompressionError(
                f"source path is {spelling!r}; expected frozen T-025 certificate"
            )
    absolute = path.absolute()
    resolved = path.resolve()
    if not resolved.is_relative_to(REPOSITORY.resolve()):
        raise CompressionError("source path escapes the repository")
    if resolved != expected:
        raise CompressionError(
            f"source path is {resolved.as_posix()!r}; expected frozen path {SOURCE_PATH!r}"
        )
    if resolved != absolute:
        raise CompressionError("source path resolves through a symlink")
    return resolved


def authenticate_source(
    *, path: Path, revision: str, expect_catalog_sha256: str
) -> OrbitInventory:
    """Bind the source bytes, inventory U025, and refuse a catalog digest mismatch."""
    data = _bind_repository_source(path, revision, label="T-025 certificate")
    certificate = _load_certificate_bytes(data, label="T-025 certificate")
    inventory = inventory_certificate(certificate)
    digest = catalog_sha256(inventory)
    expected = _digest(expect_catalog_sha256, label="expected catalog SHA-256")
    if digest != expected:
        raise CompressionError(f"U025 catalog SHA-256 is {digest}; expected {expected}")
    return inventory


def _admitted_control(name: str, inventory: OrbitInventory) -> dict[str, Any]:
    try:
        if name == "policy_boundary":
            return cast(dict[str, Any], _policy_boundary_check(inventory))
        if name == "synthetic_decompressor":
            return cast(dict[str, Any], _synthetic_decompressor_check(inventory))
        return cast(dict[str, Any], _full_control_roundtrip(inventory))
    except AdmissionError as error:
        raise CompressionError(str(error)) from error


def run_selftest_controls(inventory: OrbitInventory) -> dict[str, Any]:
    """Replay the admitted 23/24 policy and full T-025 manifest without coverage."""
    policy_boundary = _admitted_control("policy_boundary", inventory)
    synthetic = _admitted_control("synthetic_decompressor", inventory)
    full = _admitted_control("full_manifest_roundtrip", inventory)
    if policy_boundary.get("coverage_ran") is not False:
        raise CompressionError("policy-boundary control must not run coverage")
    if catalog_sha256(inventory) != full.get("catalog_sha256"):
        raise CompressionError("full T-025 decompression lost catalog identity")
    return {
        "source_bound": True,
        "catalog_matched": True,
        "source_orbits": inventory.orbit_count,
        "source_atoms": inventory.atom_count,
        "source_budget": str(inventory.total_budget),
        "policy_boundary": policy_boundary,
        "synthetic_decompressor": synthetic,
        "full_manifest_roundtrip": full,
        "coverage_ran": False,
        "selftest_ran": True,
    }


def cardinality_budget_sketch(inventory: OrbitInventory) -> dict[str, Any]:
    """Describe the coverage-free HiGHS MIP.  Do not solve it.

    Nonnegative reweighting of U025 with N+ <= 23 and budget < 11 is feasible by putting
    a tiny positive weight on any 23 orbits.  Closed-core coverage is not a linear
    constraint on those weights.  Solving this program, or reporting its N+, would be a
    lying scientific result.
    """
    coefficients = [
        orbit.budget_coefficient
        for orbit in (*inventory.point_orbits, *inventory.threshold_orbits)
    ]
    return {
        "kind": "highs_mip_nonnegative_orbit_weights",
        "orbit_count": inventory.orbit_count,
        "binary_indicators": inventory.orbit_count,
        "max_orbits": FROZEN_MAX_ORBITS,
        "budget_below": FROZEN_BUDGET_BELOW,
        "budget_coefficients": coefficients,
        "constraints": [
            "sum_i budget_coefficient_i * w_i < 11",
            "sum_i z_i <= 23",
            "w_i >= 0",
            "z_i in {0, 1}",
            "w_i = 0 when z_i = 0",
        ],
        "includes_coverage": False,
        "solver": "highs",
        "search_status": "instrument_incomplete",
        "optimizer_ran": False,
        "reason": (
            "Coverage of T-025 closed cores is not a linear function of orbit weights, "
            "so this MIP cannot certify H-163. Budget-and-cardinality feasibility is "
            "trivial for positive weights and would be a lying N+ if reported."
        ),
    }


def build_receipt(
    *,
    source: Path | None = None,
    expect_source_revision: str = SOURCE_REVISION,
    expect_catalog_sha256: str = FROZEN_CATALOG_SHA256,
    max_orbits: int = FROZEN_MAX_ORBITS,
    budget_below: int = FROZEN_BUDGET_BELOW,
    least_charge: int = FROZEN_LEAST_CHARGE,
    authorize_target: str | None = None,
) -> dict[str, Any]:
    """Run source, catalog, and policy controls; never emit a candidate in this producer."""
    authorization = _require_authorization(authorize_target)
    _require_frozen_policy(
        max_orbits=max_orbits, budget_below=budget_below, least_charge=least_charge
    )
    revision = _revision(expect_source_revision, label="source revision")
    if revision != SOURCE_REVISION:
        raise CompressionError(
            f"source revision is {revision}; expected frozen revision {SOURCE_REVISION}"
        )
    path = resolve_source(source)
    inventory = authenticate_source(
        path=path,
        revision=revision,
        expect_catalog_sha256=expect_catalog_sha256,
    )
    controls = run_selftest_controls(inventory)
    search: dict[str, Any] | None = None
    search_status = "not_run"
    if authorization == AUTHORIZED_TARGET:
        search = cardinality_budget_sketch(inventory)
        search_status = cast(str, search["search_status"])
    return {
        "schema": RECEIPT_SCHEMA,
        "source_revision": SOURCE_REVISION,
        "catalog_sha256": catalog_sha256(inventory),
        "target_ran": False,
        "optimizer_ran": False,
        "candidate_created": False,
        "coverage_ran": False,
        "n_plus": None,
        "search_status": search_status,
        "authorization": authorization,
        "max_orbits": FROZEN_MAX_ORBITS,
        "budget_below": FROZEN_BUDGET_BELOW,
        "least_charge": FROZEN_LEAST_CHARGE,
        "search": search,
        "controls": controls,
        "scope": (
            "Source authentication, U025 catalog identity, and the admitted 23/24-orbit "
            "policy boundary. No coverage route, optimizer solve, candidate certificate, "
            "or H-163 verdict is established."
        ),
    }


def _protected_paths() -> set[Path]:
    protected = {(REPOSITORY / SOURCE_PATH).resolve()}
    protected.update((REPOSITORY / anchor.path).resolve() for anchor in SENTINELS)
    protected.update((REPOSITORY / anchor.source_path).resolve() for anchor in SENTINELS)
    return protected


def _refuse_protected_output(output: Path) -> None:
    if output.resolve() in _protected_paths():
        raise CompressionError("receipt output may not overwrite a bound input")


def _write_receipt(output: Path, encoded: bytes) -> None:
    _refuse_protected_output(output)
    with atomic_output_file(output, make_parents=True) as temporary:
        temporary.write_bytes(encoded)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    command.add_argument(
        "--source",
        type=Path,
        default=FROZEN_SOURCE_PACKING,
        help="packing-relative T-025 certificate (frozen path only)",
    )
    command.add_argument(
        "--expect-source-revision",
        default=SOURCE_REVISION,
        help="full lowercase Git revision of the frozen T-025 certificate",
    )
    command.add_argument(
        "--expect-catalog-sha256",
        default=FROZEN_CATALOG_SHA256,
        help="lowercase SHA-256 of the canonical U025 catalog",
    )
    command.add_argument("--max-orbits", type=int, default=FROZEN_MAX_ORBITS)
    command.add_argument("--budget-below", type=int, default=FROZEN_BUDGET_BELOW)
    command.add_argument("--least-charge", type=int, default=FROZEN_LEAST_CHARGE)
    command.add_argument(
        "--authorize-target",
        default=None,
        help="must be exp-161 to permit a later search; this producer still emits no candidate",
    )
    command.add_argument(
        "--selftest",
        action="store_true",
        help="replay source, catalog, and 23/24 policy controls without coverage",
    )
    command.add_argument(
        "--output",
        type=Path,
        default=None,
        help="write the producer receipt here; omitted output defaults to --selftest",
    )
    return command


def main(argv: Sequence[str] | None = None) -> int:
    options = parser().parse_args(argv)
    try:
        if options.output is not None:
            _refuse_protected_output(cast(Path, options.output))
        receipt = build_receipt(
            source=options.source,
            expect_source_revision=options.expect_source_revision,
            expect_catalog_sha256=options.expect_catalog_sha256,
            max_orbits=options.max_orbits,
            budget_below=options.budget_below,
            least_charge=options.least_charge,
            authorize_target=options.authorize_target,
        )
        encoded = _canonical_json(receipt)
        if options.output is not None:
            output = cast(Path, options.output)
            _write_receipt(output, encoded)
            print(f"Route S compression producer receipt written: {output}")
        if options.selftest or options.output is None:
            print("Route S compression producer selftest passed")
    except (OSError, ValueError) as error:
        print(f"Route S compression producer refused: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
