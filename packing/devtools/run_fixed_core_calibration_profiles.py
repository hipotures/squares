"""Run and validate three sequential target-free fixed-core calibration profiles."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import math
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from strif import atomic_write_bytes, atomic_write_text

PROFILE_SCHEMA = "fixed-core-calibration-profile-run/v1"
INVENTORY_SCHEMA = "fixed-core-calibration-profile-inventory/v1"
SUMMARY_SCHEMA = "fixed-core-calibration-three-profile-summary/v1"
CALIBRATION_SCHEMA = "fixed-core-packet-calibration/v1"
EVIDENCE_SCOPE = (
    "target-free n=2 full-shape operational calibration; no scientific-target inference"
)
CALIBRATION_MODULE = "devtools.calibrate_fixed_core_packet"
PROFILE_COUNT = 3


class ProfileCoordinatorError(ValueError):
    """A run-set input, subprocess, retained artifact, or summary violated the contract."""


@dataclass(frozen=True)
class InventorySpec:
    """Exact direction filenames required by one calibration profile."""

    raw: tuple[str, ...]
    normalized_exact: tuple[str, ...]
    normalized_interval: tuple[str, ...]
    dilation: tuple[str, ...]

    @property
    def total_direction_rows(self) -> int:
        return sum(
            len(names)
            for names in (
                self.raw,
                self.normalized_exact,
                self.normalized_interval,
                self.dilation,
            )
        )


FULL_INVENTORY_SPEC = InventorySpec(
    raw=tuple(f"{index}.json" for index in range(2_881)),
    normalized_exact=tuple(f"{index}.json" for index in range(2_881)),
    normalized_interval=tuple(f"{index}.json" for index in range(2_881))
    + tuple(f"{index}'.json" for index in range(1, 2_881)),
    dilation=tuple(f"{index}.json" for index in range(2_881)),
)

_DIRECTION_ROLES = (
    ("raw-directions", "raw-directions", "raw", "directions_sha256"),
    (
        "normalized-exact-directions",
        "normalized-exact-directions",
        "normalized_exact",
        "directions_sha256",
    ),
    (
        "normalized-interval-directions",
        "normalized-interval-directions",
        "reflected_interval",
        "directions_sha256",
    ),
    ("dilation-directions", "dilation-directions", "dilation", "directions_sha256"),
)
_SINGLE_FILE_ROLES = (
    ("normalized-candidate", "candidate.json"),
    ("generic-dilation-record", "dilation.json"),
    ("rss-observations", "rss-samples.json"),
    ("calibration-receipt", "result.json"),
)
_CLOCK_METRICS = (
    "preflight_seconds",
    "launch_seconds",
    "source_loading_seconds",
    "raw_seconds",
    "normalization_publication_seconds",
    "exact_seconds",
    "interval_seconds",
    "dilation_seconds",
    "full_readback_seconds",
    "parent_final_readback_seconds",
    "terminal_admission_seconds",
    "worker_elapsed_seconds",
    "worker_exit_seconds",
    "supervisor_cleanup_seconds",
    "external_lifetime_seconds",
)
_CPU_METRICS = (
    "coordinator_process_seconds",
    "reaped_direct_children_user_seconds",
    "reaped_direct_children_system_seconds",
)
_RSS_METRICS = (
    "sample_count",
    "positive_sample_count",
    "maximum_actual_gap_seconds",
    "peak_sampled_rss_bytes",
    "unobserved_leading_seconds",
    "unobserved_trailing_seconds",
)

CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[bytes]]
Clock = Callable[[], float]


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ProfileCoordinatorError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ProfileCoordinatorError(f"non-finite JSON constant {value!r}")


def _strict_json_bytes(data: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            data,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProfileCoordinatorError(f"{label} is not strict JSON: {error}") from error
    if not isinstance(value, dict):
        raise ProfileCoordinatorError(f"{label} must be a JSON object")
    return value


def _strict_json(path: Path, label: str) -> dict[str, object]:
    try:
        return _strict_json_bytes(path.read_bytes(), label)
    except OSError as error:
        raise ProfileCoordinatorError(f"could not read {label}: {error}") from error


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _direction_digest(paths: Sequence[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        data = path.read_bytes()
        name = path.name.encode()
        digest.update(len(name).to_bytes(4, "big"))
        digest.update(name)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _finite_nonnegative(value: object, label: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ProfileCoordinatorError(f"{label} is not a finite nonnegative number")
    return float(value)


def _dict(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ProfileCoordinatorError(f"{label} must be an object")
    return cast(dict[str, object], value)


def _list(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ProfileCoordinatorError(f"{label} must be an array")
    return cast(list[object], value)


def _digest(value: object, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ProfileCoordinatorError(f"{label} is not a SHA-256 digest")
    return value


def _validate_revision(value: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise ProfileCoordinatorError(
            "execution revision must be 40 lowercase hexadecimal digits"
        )


def _artifact_row(
    role: str, relative: str, files: Sequence[Path], *, direction_set: bool = False
) -> dict[str, object]:
    return {
        "role": role,
        "path": relative,
        "count": len(files),
        "bytes": sum(path.stat().st_size for path in files),
        "sha256": _direction_digest(files) if direction_set else _sha256(files[0].read_bytes()),
    }


def _expected_names(spec: InventorySpec, key: str) -> tuple[str, ...]:
    return cast(tuple[str, ...], getattr(spec, key))


def _string_pair(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(item, str) for item in value)
    )


def _known_answer_row(role: str, path: Path, row: dict[str, object]) -> None:
    label = path.name.removesuffix(".json")
    if role == "raw-directions":
        expected = {"direction", "charge", "witness"}
        valid = (
            label.isascii()
            and label.isdigit()
            and str(int(label)) == label
            and type(row.get("direction")) is int
            and row.get("direction") == int(label)
            and row.get("charge") == "2"
            and _string_pair(row.get("witness"))
        )
    elif role == "normalized-exact-directions":
        expected = {
            "direction",
            "dense",
            "slab",
            "agree",
            "witness",
            "slab_witness",
        }
        valid = (
            label.isascii()
            and label.isdigit()
            and str(int(label)) == label
            and type(row.get("direction")) is int
            and row.get("direction") == int(label)
            and row.get("dense") == "1"
            and row.get("slab") == "1"
            and row.get("agree") is True
            and _string_pair(row.get("witness"))
            and row.get("slab_witness") == row.get("witness")
        )
    elif role == "normalized-interval-directions":
        expected = {
            "label",
            "status",
            "lower",
            "upper",
            "witness",
            "boxes",
            "stalled",
            "budget_exhausted",
        }
        witness = row.get("witness")
        valid = (
            row.get("label") == label
            and row.get("status") == "certified"
            and row.get("lower") == 8
            and row.get("upper") == 8
            and isinstance(witness, list)
            and len(witness) == 2
            and all(type(item) in (int, float) and math.isfinite(item) for item in witness)
            and type(row.get("boxes")) is int
            and cast(int, row["boxes"]) > 0
            and type(row.get("stalled")) is int
            and row.get("stalled") == 0
            and row.get("budget_exhausted") is False
        )
    else:
        expected = {"direction", "label", "minimum"}
        valid = (
            label.isascii()
            and label.isdigit()
            and str(int(label)) == label
            and type(row.get("direction")) is int
            and row == {"direction": int(label), "label": label, "minimum": "1"}
        )
    if set(row) != expected or not valid:
        raise ProfileCoordinatorError(f"{role} known-answer row failed at {path.name}")


def _validate_inventory_receipt(
    receipt: dict[str, object],
    *,
    execution_revision: str,
    run_order: int,
    spec: InventorySpec,
) -> dict[str, object]:
    if (
        receipt.get("schema") != CALIBRATION_SCHEMA
        or receipt.get("status") != "complete"
        or receipt.get("disposition") != "calibration-passed"
        or receipt.get("phase") != "complete"
        or receipt.get("error") is not None
    ):
        raise ProfileCoordinatorError("inventory requires a terminal calibration pass")
    sources = _dict(receipt.get("sources"), "receipt sources")
    if sources.get("implementation_revision") != execution_revision:
        raise ProfileCoordinatorError(
            "receipt execution revision differs from inventory request"
        )
    invocation = _dict(receipt.get("invocation"), "receipt invocation")
    identity = _dict(invocation.get("identity"), "receipt invocation identity")
    settings = _dict(receipt.get("settings"), "receipt settings")
    requested = settings.get("requested_workers")
    if (
        invocation.get("run_order") != run_order
        or type(requested) is not int
        or not 1 <= cast(int, requested) <= 4
        or settings.get("effective_workers")
        != {
            "raw": requested,
            "normalized_exact": requested,
            "reflected_interval": 1,
            "dilation": 1,
        }
        or settings.get("expected_direction_rows") != spec.total_direction_rows
    ):
        raise ProfileCoordinatorError("receipt run order or worker settings changed")
    calibration = _finite_nonnegative(
        settings.get("calibration_seconds"), "calibration allowance"
    )
    external = _finite_nonnegative(settings.get("external_seconds"), "external allowance")
    grace = _finite_nonnegative(settings.get("termination_grace_seconds"), "termination grace")
    expected_identity_fields = {
        "implementation_revision",
        "requested_workers",
        "calibration_seconds",
        "external_seconds",
        "termination_grace_seconds",
        "monotonic_origin",
        "calibration_deadline_monotonic",
        "external_deadline_monotonic",
        "run_order",
        "cache_observation",
        "background_load",
    }
    origin = _finite_nonnegative(identity.get("monotonic_origin"), "monotonic origin")
    if (
        calibration == 0
        or external <= calibration
        or grace == 0
        or set(identity) != expected_identity_fields
        or identity.get("implementation_revision") != execution_revision
        or identity.get("requested_workers") != requested
        or identity.get("calibration_seconds") != calibration
        or identity.get("external_seconds") != external
        or identity.get("termination_grace_seconds") != grace
        or identity.get("calibration_deadline_monotonic") != origin + calibration
        or identity.get("external_deadline_monotonic") != origin + external
        or identity.get("run_order") != run_order
        or not isinstance(identity.get("cache_observation"), str)
        or not cast(str, identity["cache_observation"]).strip()
        or not isinstance(identity.get("background_load"), str)
        or not cast(str, identity["background_load"]).strip()
    ):
        raise ProfileCoordinatorError("receipt invocation identity changed")
    supervision = _dict(receipt.get("supervision"), "receipt supervision")
    if supervision != {
        "status": "observed-exit",
        "worker_exit_status": 0,
        "process_group_reaped": True,
        "supervisor_signal": None,
    }:
        raise ProfileCoordinatorError("receipt does not prove a reaped successful worker")
    clocks = _dict(receipt.get("clocks"), "receipt clocks")
    for name in _CLOCK_METRICS:
        _finite_nonnegative(clocks.get(name), f"clock {name}")
    if (
        cast(float, clocks["worker_elapsed_seconds"]) >= calibration
        or cast(float, clocks["external_lifetime_seconds"])
        + cast(float, clocks["terminal_admission_seconds"])
        >= external
    ):
        raise ProfileCoordinatorError("receipt exhausted a calibration deadline")
    resources = _dict(receipt.get("resources"), "receipt resources")
    for name in _CPU_METRICS:
        _finite_nonnegative(resources.get(name), f"CPU {name}")
    rss = _dict(resources.get("rss"), "RSS receipt")
    if (
        type(rss.get("sample_count")) is not int
        or cast(int, rss["sample_count"]) < 2
        or type(rss.get("positive_sample_count")) is not int
        or cast(int, rss["positive_sample_count"]) < 2
        or rss.get("observer_errors") != []
    ):
        raise ProfileCoordinatorError("receipt lacks error-free RSS observations")
    for name in _RSS_METRICS[2:]:
        _finite_nonnegative(rss.get(name), f"RSS {name}")
    return identity


def inventory_profile(
    output_dir: Path,
    *,
    execution_revision: str,
    run_order: int,
    spec: InventorySpec = FULL_INVENTORY_SPEC,
) -> dict[str, object]:
    """Independently reconstruct the closed retained-file inventory and byte digests."""

    if output_dir.is_symlink() or not output_dir.is_dir():
        raise ProfileCoordinatorError("profile directory is missing or is a symbolic link")
    output_dir = output_dir.resolve()
    expected_top = {
        "result.json",
        "candidate.json",
        "dilation.json",
        "rss-samples.json",
        "raw-directions",
        "normalized-exact-directions",
        "normalized-interval-directions",
        "dilation-directions",
    }
    actual_top = {path.name for path in output_dir.iterdir()}
    if actual_top != expected_top:
        raise ProfileCoordinatorError("profile top-level artifact set is not exact")

    receipt_path = output_dir / "result.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = _strict_json_bytes(receipt_bytes, "calibration receipt")
    identity = _validate_inventory_receipt(
        receipt,
        execution_revision=execution_revision,
        run_order=run_order,
        spec=spec,
    )

    artifacts: list[dict[str, object]] = []
    route_digests: dict[str, str] = {}
    for role, relative, receipt_route, digest_key in _DIRECTION_ROLES:
        directory = output_dir / relative
        if directory.is_symlink() or not directory.is_dir():
            raise ProfileCoordinatorError(f"{relative} is not a real directory")
        names = _expected_names(
            spec,
            receipt_route if receipt_route != "reflected_interval" else "normalized_interval",
        )
        expected = set(names)
        children = tuple(directory.iterdir())
        if any(path.is_symlink() or not path.is_file() for path in children):
            raise ProfileCoordinatorError(f"{relative} contains a non-regular file")
        actual = {path.name for path in children}
        if actual != expected or len(children) != len(expected):
            raise ProfileCoordinatorError(f"{relative} filename set is not exact")
        ordered = tuple(directory / name for name in names)
        for path in ordered:
            _known_answer_row(
                role,
                path,
                _strict_json(path, f"direction row {relative}/{path.name}"),
            )
        row = _artifact_row(role, relative, ordered, direction_set=True)
        artifacts.append(row)
        route_digests[receipt_route] = cast(str, row["sha256"])
        route = (
            _dict(receipt.get("raw"), "raw receipt")
            if receipt_route == "raw"
            else _dict(
                _dict(receipt.get("routes"), "route receipts").get(receipt_route),
                f"{receipt_route} receipt",
            )
        )
        if route.get(digest_key) != row["sha256"]:
            raise ProfileCoordinatorError(f"{relative} digest does not reconstruct")

    for role, relative in _SINGLE_FILE_ROLES:
        path = output_dir / relative
        if path.is_symlink() or not path.is_file():
            raise ProfileCoordinatorError(f"{relative} is not a real file")
        if relative != "result.json":
            _strict_json(path, relative)
        artifacts.append(_artifact_row(role, relative, (path,)))

    by_role = {cast(str, row["role"]): row for row in artifacts}
    normalized = _dict(receipt.get("normalized"), "normalized receipt")
    routes = _dict(receipt.get("routes"), "route receipts")
    dilation = _dict(routes.get("dilation"), "dilation receipt")
    resources = _dict(receipt.get("resources"), "resources")
    rss = _dict(resources.get("rss"), "RSS receipt")
    expected_single_digests = {
        "normalized-candidate": normalized.get("sha256"),
        "generic-dilation-record": dilation.get("record_sha256"),
        "rss-observations": rss.get("samples_sha256"),
    }
    for role, expected_digest in expected_single_digests.items():
        if by_role[role]["sha256"] != expected_digest:
            raise ProfileCoordinatorError(f"{role} digest does not reconstruct")

    receipt_artifacts = _list(receipt.get("artifacts"), "receipt artifact inventory")
    independent_counts = {
        cast(str, row["role"]): (row["path"], row["count"], row["bytes"]) for row in artifacts
    }
    retained_counts: dict[str, tuple[object, object, object]] = {}
    for value in receipt_artifacts:
        row = _dict(value, "receipt artifact row")
        if set(row) != {"role", "path", "count", "bytes"} or not isinstance(
            row.get("role"), str
        ):
            raise ProfileCoordinatorError("receipt artifact row fields changed")
        role = cast(str, row["role"])
        if role in retained_counts:
            raise ProfileCoordinatorError("receipt artifact roles are duplicated")
        retained_counts[role] = (row.get("path"), row.get("count"), row.get("bytes"))
    if retained_counts != independent_counts:
        raise ProfileCoordinatorError("receipt artifact counts or bytes do not reconstruct")
    if spec.total_direction_rows != sum(
        cast(int, by_role[role]["count"]) for role, *_rest in _DIRECTION_ROLES
    ):
        raise ProfileCoordinatorError("direction-row total does not reconstruct")

    return {
        "schema": INVENTORY_SCHEMA,
        "execution_revision": execution_revision,
        "run_order": run_order,
        "profile_directory": str(output_dir),
        "invocation_identity": identity,
        "receipt": {
            "path": "result.json",
            "bytes": len(receipt_bytes),
            "sha256": _sha256(receipt_bytes),
        },
        "direction_rows": spec.total_direction_rows,
        "artifacts": artifacts,
        "route_digests": route_digests,
    }


def _default_runner(argv: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        tuple(argv),
        check=False,
        capture_output=True,
    )


def _write_command_output(
    run_root: Path,
    stem: str,
    argv: Sequence[str],
    result: subprocess.CompletedProcess[bytes],
) -> dict[str, object]:
    stdout_path = run_root / f"{stem}.stdout.log"
    stderr_path = run_root / f"{stem}.stderr.log"
    atomic_write_bytes(stdout_path, result.stdout)
    atomic_write_bytes(stderr_path, result.stderr)
    return {
        "argv": list(argv),
        "exit_status": result.returncode,
        "stdout": {
            "path": stdout_path.name,
            "bytes": len(result.stdout),
            "sha256": _sha256(result.stdout),
        },
        "stderr": {
            "path": stderr_path.name,
            "bytes": len(result.stderr),
            "sha256": _sha256(result.stderr),
        },
    }


def _pending_command(argv: Sequence[str], *, wall_required: bool) -> dict[str, object]:
    command: dict[str, object] = {
        "argv": list(argv),
        "exit_status": None,
        "stdout": None,
        "stderr": None,
    }
    if wall_required:
        command["command_wall_seconds"] = None
    return command


def _inline_stream_binding(data: bytes) -> dict[str, object]:
    return {
        "base64": base64.b64encode(data).decode("ascii"),
        "bytes": len(data),
        "sha256": _sha256(data),
    }


def _inline_command_output(
    argv: Sequence[str],
    result: subprocess.CompletedProcess[bytes],
    *,
    command_wall_seconds: float | None = None,
) -> dict[str, object]:
    command: dict[str, object] = {
        "argv": list(argv),
        "exit_status": result.returncode,
        "stdout": _inline_stream_binding(result.stdout),
        "stderr": _inline_stream_binding(result.stderr),
    }
    if command_wall_seconds is not None:
        command["command_wall_seconds"] = command_wall_seconds
    return command


def _read_calibration_identity(
    output_dir: Path, execution_revision: str, run_order: int
) -> tuple[dict[str, object], dict[str, object]]:
    receipt = _strict_json(output_dir / "result.json", "calibration receipt")
    if receipt.get("schema") != CALIBRATION_SCHEMA:
        raise ProfileCoordinatorError("calibration receipt schema changed")
    sources = _dict(receipt.get("sources"), "receipt sources")
    invocation = _dict(receipt.get("invocation"), "receipt invocation")
    identity = _dict(invocation.get("identity"), "receipt invocation identity")
    if sources.get("implementation_revision") != execution_revision:
        raise ProfileCoordinatorError("calibration receipt has the wrong execution revision")
    if invocation.get("run_order") != run_order or identity.get("run_order") != run_order:
        raise ProfileCoordinatorError("calibration receipt has the wrong run order")
    _validate_profile_identity(identity, revision=execution_revision, run_order=run_order)
    return receipt, identity


def producer_readback(
    output_dir: Path, *, repository: Path, execution_revision: str, run_order: int
) -> dict[str, object]:
    """Call the producer's strict reader and return its invocation/digest binding."""

    # Keep inventory-readback import-distinct from the producer process.
    from devtools.calibrate_fixed_core_packet import load_result  # noqa: PLC0415

    receipt, identity = _read_calibration_identity(output_dir, execution_revision, run_order)
    loaded = load_result(
        output_dir,
        repository=repository,
        expected_revision=execution_revision,
        require_supervision=True,
        require_complete_candidate=True,
        expected_invocation=identity,
    )
    if loaded != receipt:
        raise ProfileCoordinatorError("producer readback changed the retained receipt")
    data = (output_dir / "result.json").read_bytes()
    return {
        "schema": "fixed-core-calibration-producer-readback/v1",
        "execution_revision": execution_revision,
        "run_order": run_order,
        "profile_directory": str(output_dir.resolve()),
        "invocation_identity": identity,
        "receipt": {"path": "result.json", "bytes": len(data), "sha256": _sha256(data)},
    }


def _validate_readback_binding(
    proof: dict[str, object],
    *,
    schema: str,
    execution_revision: str,
    run_order: int,
    output_dir: Path,
    identity: dict[str, object],
    receipt_binding: dict[str, object],
) -> None:
    expected = {
        "schema",
        "execution_revision",
        "run_order",
        "profile_directory",
        "invocation_identity",
        "receipt",
    }
    if (
        set(proof) != expected
        or proof.get("schema") != schema
        or proof.get("execution_revision") != execution_revision
        or proof.get("run_order") != run_order
        or proof.get("profile_directory") != str(output_dir.resolve())
        or proof.get("invocation_identity") != identity
        or proof.get("receipt") != receipt_binding
    ):
        raise ProfileCoordinatorError("readback proof binding is malformed")


def _validate_receipt_binding(value: object, label: str) -> dict[str, object]:
    binding = _dict(value, label)
    if (
        set(binding) != {"path", "bytes", "sha256"}
        or binding.get("path") != "result.json"
        or type(binding.get("bytes")) is not int
        or cast(int, binding["bytes"]) <= 0
    ):
        raise ProfileCoordinatorError(f"{label} is malformed")
    _digest(binding.get("sha256"), f"{label} digest")
    return binding


def _validate_inventory_proof(
    inventory: dict[str, object],
    *,
    execution_revision: str,
    run_order: int,
    output_dir: Path,
    identity: dict[str, object],
    receipt_binding: dict[str, object],
    spec: InventorySpec | None,
) -> None:
    expected = {
        "schema",
        "execution_revision",
        "run_order",
        "profile_directory",
        "invocation_identity",
        "receipt",
        "direction_rows",
        "artifacts",
        "route_digests",
    }
    if set(inventory) != expected:
        raise ProfileCoordinatorError("inventory proof fields changed")
    _validate_receipt_binding(inventory.get("receipt"), "inventory receipt binding")
    binding = {
        key: inventory[key]
        for key in expected
        if key not in {"direction_rows", "artifacts", "route_digests"}
    }
    _validate_readback_binding(
        binding,
        schema=INVENTORY_SCHEMA,
        execution_revision=execution_revision,
        run_order=run_order,
        output_dir=output_dir,
        identity=identity,
        receipt_binding=receipt_binding,
    )
    expected_direction_rows = (
        spec.total_direction_rows if spec is not None else inventory.get("direction_rows")
    )
    if type(expected_direction_rows) is not int or cast(int, expected_direction_rows) <= 0:
        raise ProfileCoordinatorError("inventory direction-row count is malformed")
    if inventory.get("direction_rows") != expected_direction_rows:
        raise ProfileCoordinatorError("inventory direction-row count changed")
    artifacts = _list(inventory.get("artifacts"), "inventory artifacts")
    expected_rows: dict[str, tuple[str, int | None]] = {}
    for role, relative, receipt_route, _digest_key in _DIRECTION_ROLES:
        expected_count = None
        if spec is not None:
            expected_count = len(
                _expected_names(
                    spec,
                    "normalized_interval"
                    if receipt_route == "reflected_interval"
                    else receipt_route,
                )
            )
        expected_rows[role] = (relative, expected_count)
    expected_rows.update({role: (relative, 1) for role, relative in _SINGLE_FILE_ROLES})
    expected_roles = set(expected_rows)
    observed_roles: set[str] = set()
    artifact_digests: dict[str, str] = {}
    direction_total = 0
    for value in artifacts:
        row = _dict(value, "inventory artifact")
        if set(row) != {"role", "path", "count", "bytes", "sha256"}:
            raise ProfileCoordinatorError("inventory artifact fields changed")
        role = row.get("role")
        if (
            not isinstance(role, str)
            or role in observed_roles
            or role not in expected_roles
            or not isinstance(row.get("path"), str)
            or type(row.get("count")) is not int
            or cast(int, row["count"]) < 0
            or type(row.get("bytes")) is not int
            or cast(int, row["bytes"]) < 0
        ):
            raise ProfileCoordinatorError("inventory artifact is malformed")
        _digest(row.get("sha256"), "inventory artifact digest")
        expected_path, expected_count = expected_rows[role]
        if row.get("path") != expected_path or (
            expected_count is not None and row.get("count") != expected_count
        ):
            raise ProfileCoordinatorError("inventory artifact path or count changed")
        observed_roles.add(role)
        artifact_digests[role] = cast(str, row["sha256"])
        if role.endswith("-directions"):
            direction_total += cast(int, row["count"])
    if observed_roles != expected_roles or direction_total != expected_direction_rows:
        raise ProfileCoordinatorError("inventory artifact role or direction count changed")
    route_digests = _dict(inventory.get("route_digests"), "route digests")
    if set(route_digests) != {"raw", "normalized_exact", "reflected_interval", "dilation"}:
        raise ProfileCoordinatorError("inventory route digest set changed")
    expected_route_digests = {
        receipt_route: artifact_digests[role]
        for role, _relative, receipt_route, _digest_key in _DIRECTION_ROLES
    }
    for name, digest in route_digests.items():
        _digest(digest, f"{name} route digest")
    if route_digests != expected_route_digests:
        raise ProfileCoordinatorError("inventory route digest is not bound to its artifact")


def _readback_argv(
    mode: str,
    *,
    repository: Path,
    execution_revision: str,
    output_dir: Path,
    run_order: int,
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        "devtools.run_fixed_core_calibration_profiles",
        mode,
        "--repository",
        str(repository),
        "--expect-implementation-revision",
        execution_revision,
        "--output-dir",
        str(output_dir),
        "--run-order",
        str(run_order),
    )


def _calibration_argv(
    *,
    repository: Path,
    execution_revision: str,
    output_dir: Path,
    workers: int,
    calibration_seconds: float,
    external_seconds: float,
    grace_seconds: float,
    run_order: int,
    cache_observation: str,
    background_load: str,
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-m",
        CALIBRATION_MODULE,
        "--repository",
        str(repository),
        "--expect-implementation-revision",
        execution_revision,
        "--output-dir",
        str(output_dir),
        "--workers",
        str(workers),
        "--calibration-seconds",
        str(calibration_seconds),
        "--external-seconds",
        str(external_seconds),
        "--grace-seconds",
        str(grace_seconds),
        "--run-order",
        str(run_order),
        "--cache-observation",
        cache_observation,
        "--background-load",
        background_load,
    )


def _describe(values: Sequence[float]) -> dict[str, object]:
    if len(values) != PROFILE_COUNT:
        raise ProfileCoordinatorError("summary metrics require exactly three observations")
    checked = [_finite_nonnegative(value, "summary observation") for value in values]
    return {
        "observations": checked,
        "median": statistics.median(checked),
        "minimum": min(checked),
        "maximum": max(checked),
    }


def build_summary(run_records: Sequence[dict[str, object]]) -> dict[str, object]:
    """Build the closed three-profile summary from validated run records and receipts."""

    if len(run_records) != PROFILE_COUNT:
        raise ProfileCoordinatorError("summary requires exactly three profile records")
    receipts: list[dict[str, object]] = []
    inventories: list[dict[str, object]] = []
    execution_revision: str | None = None
    settings_key: str | None = None
    run_bindings: list[dict[str, object]] = []
    for expected_order, record in enumerate(run_records, 1):
        validate_profile_record(record)
        if record["status"] != "complete" or record["run_order"] != expected_order:
            raise ProfileCoordinatorError("profile sequence is incomplete or out of order")
        profile_dir = Path(cast(str, record["profile_directory"]))
        receipt = _strict_json(profile_dir / "result.json", "calibration receipt")
        inventory = _dict(record.get("inventory"), "profile inventory")
        receipt_bytes = (profile_dir / "result.json").read_bytes()
        receipt_binding = _dict(record.get("calibration_receipt"), "receipt binding")
        if receipt_binding.get("sha256") != _sha256(receipt_bytes) or receipt_binding.get(
            "bytes"
        ) != len(receipt_bytes):
            raise ProfileCoordinatorError("profile receipt binding changed before summary")
        revision = cast(str, record["execution_revision"])
        if execution_revision is None:
            execution_revision = revision
        elif revision != execution_revision:
            raise ProfileCoordinatorError("profile execution revisions differ")
        settings = _dict(receipt.get("settings"), "calibration settings")
        current_settings_key = json.dumps(settings, sort_keys=True, allow_nan=False)
        if settings_key is None:
            settings_key = current_settings_key
        elif current_settings_key != settings_key:
            raise ProfileCoordinatorError("profile settings differ")
        receipts.append(receipt)
        inventories.append(inventory)
        run_bindings.append(
            {
                "run_order": expected_order,
                "profile_directory": str(profile_dir),
                "invocation_identity": record["invocation_identity"],
                "calibration_receipt": receipt_binding,
                "command_wall_seconds": _finite_nonnegative(
                    _dict(record["calibration_command"], "calibration command").get(
                        "command_wall_seconds"
                    ),
                    "command wall duration",
                ),
                "inventory": {
                    "direction_rows": inventory["direction_rows"],
                    "artifacts": inventory["artifacts"],
                },
            }
        )
    if execution_revision is None:
        raise ProfileCoordinatorError("summary has no execution revision")

    metrics: dict[str, object] = {
        "command_wall_seconds": _describe(
            [
                _finite_nonnegative(
                    _dict(record["calibration_command"], "calibration command").get(
                        "command_wall_seconds"
                    ),
                    "command wall duration",
                )
                for record in run_records
            ]
        )
    }
    for name in _CLOCK_METRICS:
        metrics[f"clock.{name}"] = _describe(
            [
                _finite_nonnegative(
                    _dict(receipt.get("clocks"), "receipt clocks").get(name),
                    f"clock {name}",
                )
                for receipt in receipts
            ]
        )
    for name in _CPU_METRICS:
        metrics[f"cpu.{name}"] = _describe(
            [
                _finite_nonnegative(
                    _dict(receipt.get("resources"), "receipt resources").get(name),
                    f"CPU {name}",
                )
                for receipt in receipts
            ]
        )
    for name in _RSS_METRICS:
        metrics[f"rss.{name}"] = _describe(
            [
                _finite_nonnegative(
                    _dict(
                        _dict(receipt.get("resources"), "receipt resources").get("rss"),
                        "RSS receipt",
                    ).get(name),
                    f"RSS {name}",
                )
                for receipt in receipts
            ]
        )
    metrics["interval.boxes_observed"] = _describe(
        [
            _finite_nonnegative(
                _dict(
                    _dict(receipt.get("routes"), "route receipts").get("reflected_interval"),
                    "interval receipt",
                ).get("boxes_observed"),
                "interval boxes observed",
            )
            for receipt in receipts
        ]
    )
    artifact_totals = [
        sum(
            cast(int, _dict(row, "inventory artifact")["bytes"])
            for row in _list(inventory.get("artifacts"), "inventory artifacts")
        )
        for inventory in inventories
    ]
    metrics["artifacts.total_bytes"] = _describe(artifact_totals)
    metrics["deadline.internal_headroom_seconds"] = _describe(
        [
            _finite_nonnegative(
                _dict(receipt.get("settings"), "settings")["calibration_seconds"],
                "calibration allowance",
            )
            - _finite_nonnegative(
                _dict(receipt.get("clocks"), "clocks")["worker_elapsed_seconds"],
                "worker elapsed",
            )
            for receipt in receipts
        ]
    )
    metrics["deadline.scoped_external_headroom_seconds"] = _describe(
        [
            _finite_nonnegative(
                _dict(receipt.get("settings"), "settings")["external_seconds"],
                "external allowance",
            )
            - _finite_nonnegative(
                _dict(receipt.get("clocks"), "clocks")["external_lifetime_seconds"],
                "external lifetime",
            )
            - _finite_nonnegative(
                _dict(receipt.get("clocks"), "clocks")["terminal_admission_seconds"],
                "terminal admission",
            )
            for receipt in receipts
        ]
    )
    settings = _dict(receipts[0]["settings"], "calibration settings")
    return {
        "schema": SUMMARY_SCHEMA,
        "evidence_scope": EVIDENCE_SCOPE,
        "execution_revision": execution_revision,
        "frozen_tuple": {
            "workers": settings["requested_workers"],
            "calibration_seconds": settings["calibration_seconds"],
            "external_seconds": settings["external_seconds"],
            "grace_seconds": settings["termination_grace_seconds"],
        },
        "settings": settings,
        "runs": run_bindings,
        "metrics": metrics,
    }


def _validate_stream_binding(value: object, label: str, run_root: Path | None) -> str:
    binding = _dict(value, label)
    if set(binding) == {"base64", "bytes", "sha256"}:
        encoded = binding.get("base64")
        if not isinstance(encoded, str):
            raise ProfileCoordinatorError(f"{label} inline content is malformed")
        try:
            data = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise ProfileCoordinatorError(f"{label} inline content is malformed") from error
        if base64.b64encode(data).decode("ascii") != encoded:
            raise ProfileCoordinatorError(f"{label} inline content is not canonical")
        if (
            type(binding.get("bytes")) is not int
            or binding["bytes"] != len(data)
            or _digest(binding.get("sha256"), f"{label} digest") != _sha256(data)
        ):
            raise ProfileCoordinatorError(f"{label} inline content does not reconstruct")
        return "inline"
    if set(binding) != {"path", "bytes", "sha256"}:
        raise ProfileCoordinatorError(f"{label} fields changed")
    relative = binding.get("path")
    if (
        not isinstance(relative, str)
        or Path(relative).is_absolute()
        or len(Path(relative).parts) != 1
        or relative in {".", ".."}
        or type(binding.get("bytes")) is not int
        or cast(int, binding["bytes"]) < 0
    ):
        raise ProfileCoordinatorError(f"{label} is malformed")
    digest = _digest(binding.get("sha256"), f"{label} digest")
    if run_root is not None:
        data = (run_root / relative).read_bytes()
        if len(data) != binding["bytes"] or _sha256(data) != digest:
            raise ProfileCoordinatorError(f"{label} no longer matches its retained log")
    return "log"


def _validate_command_record(
    value: object,
    label: str,
    *,
    wall_required: bool,
    require_success: bool,
    require_logs: bool,
    run_root: Path | None,
) -> dict[str, object]:
    command = _dict(value, label)
    expected = {"argv", "exit_status", "stdout", "stderr"}
    if wall_required:
        expected.add("command_wall_seconds")
    if set(command) != expected:
        raise ProfileCoordinatorError(f"{label} fields changed")
    argv = _list(command.get("argv"), f"{label} argv")
    if not argv or any(not isinstance(item, str) for item in argv):
        raise ProfileCoordinatorError(f"{label} argv is malformed")
    exit_status = command.get("exit_status")
    if exit_status is None:
        if command.get("stdout") is not None or command.get("stderr") is not None:
            raise ProfileCoordinatorError(f"{label} has streams without a returned command")
        if require_success or require_logs:
            raise ProfileCoordinatorError(f"{label} did not return")
        if wall_required and command.get("command_wall_seconds") is not None:
            _finite_nonnegative(command["command_wall_seconds"], f"{label} wall duration")
        return command
    if type(exit_status) is not int:
        raise ProfileCoordinatorError(f"{label} exit status is malformed")
    if require_success and exit_status != 0:
        raise ProfileCoordinatorError(f"{label} did not succeed")
    if wall_required:
        _finite_nonnegative(command.get("command_wall_seconds"), f"{label} wall duration")
    stdout_storage = _validate_stream_binding(
        command.get("stdout"), f"{label} stdout", run_root
    )
    stderr_storage = _validate_stream_binding(
        command.get("stderr"), f"{label} stderr", run_root
    )
    if require_logs and (stdout_storage != "log" or stderr_storage != "log"):
        raise ProfileCoordinatorError(f"{label} does not bind retained logs")
    return command


def _command_option(command: dict[str, object], option: str, label: str) -> str:
    argv = _list(command.get("argv"), f"{label} argv")
    if argv.count(option) != 1:
        raise ProfileCoordinatorError(f"{label} does not contain exactly one {option}")
    index = argv.index(option)
    if index + 1 == len(argv) or not isinstance(argv[index + 1], str):
        raise ProfileCoordinatorError(f"{label} has no value for {option}")
    return cast(str, argv[index + 1])


def _validate_profile_identity(
    value: object, *, revision: str, run_order: int
) -> dict[str, object]:
    identity = _dict(value, "invocation identity")
    expected = {
        "implementation_revision",
        "requested_workers",
        "calibration_seconds",
        "external_seconds",
        "termination_grace_seconds",
        "monotonic_origin",
        "calibration_deadline_monotonic",
        "external_deadline_monotonic",
        "run_order",
        "cache_observation",
        "background_load",
    }
    workers = identity.get("requested_workers")
    calibration = _finite_nonnegative(
        identity.get("calibration_seconds"), "calibration allowance"
    )
    external = _finite_nonnegative(identity.get("external_seconds"), "external allowance")
    grace = _finite_nonnegative(identity.get("termination_grace_seconds"), "termination grace")
    origin = _finite_nonnegative(identity.get("monotonic_origin"), "monotonic origin")
    if (
        set(identity) != expected
        or identity.get("implementation_revision") != revision
        or identity.get("run_order") != run_order
        or type(workers) is not int
        or not 1 <= cast(int, workers) <= 4
        or calibration == 0
        or external <= calibration
        or grace == 0
        or identity.get("calibration_deadline_monotonic") != origin + calibration
        or identity.get("external_deadline_monotonic") != origin + external
        or not isinstance(identity.get("cache_observation"), str)
        or not cast(str, identity["cache_observation"]).strip()
        or not isinstance(identity.get("background_load"), str)
        or not cast(str, identity["background_load"]).strip()
    ):
        raise ProfileCoordinatorError("profile invocation identity is malformed")
    return identity


def validate_profile_record(record: dict[str, object], *, run_root: Path | None = None) -> None:
    """Validate one retained coordinator record, including its console-log bindings."""

    expected = {
        "schema",
        "status",
        "execution_revision",
        "run_order",
        "profile_directory",
        "invocation_identity",
        "calibration_receipt",
        "calibration_command",
        "producer_readback",
        "inventory_readback",
        "inventory",
        "error",
    }
    if set(record) != expected or record.get("schema") != PROFILE_SCHEMA:
        raise ProfileCoordinatorError("profile coordinator record fields changed")
    if record.get("status") not in {"complete", "refused"}:
        raise ProfileCoordinatorError("profile coordinator status is malformed")
    if type(record.get("run_order")) is not int or not 1 <= cast(int, record["run_order"]) <= 3:
        raise ProfileCoordinatorError("profile run order is malformed")
    revision = record.get("execution_revision")
    if not isinstance(revision, str):
        raise ProfileCoordinatorError("profile execution revision is malformed")
    _validate_revision(revision)
    if not isinstance(record.get("profile_directory"), str):
        raise ProfileCoordinatorError("profile directory is malformed")
    calibration_command = _validate_command_record(
        record.get("calibration_command"),
        "calibration command",
        wall_required=True,
        require_success=record["status"] == "complete",
        require_logs=record["status"] == "complete",
        run_root=run_root,
    )
    if record["status"] == "complete":
        if record.get("error") is not None:
            raise ProfileCoordinatorError("complete profile carries an error")
        for field in (
            "invocation_identity",
            "calibration_receipt",
            "producer_readback",
            "inventory_readback",
            "inventory",
        ):
            _dict(record.get(field), field)
        identity = _validate_profile_identity(
            record["invocation_identity"],
            revision=revision,
            run_order=cast(int, record["run_order"]),
        )
        profile_dir = Path(cast(str, record["profile_directory"]))
        expected_calibration = _calibration_argv(
            repository=Path(
                _command_option(calibration_command, "--repository", "calibration command")
            ),
            execution_revision=revision,
            output_dir=profile_dir,
            workers=cast(int, identity["requested_workers"]),
            calibration_seconds=_finite_nonnegative(
                identity.get("calibration_seconds"), "calibration allowance"
            ),
            external_seconds=_finite_nonnegative(
                identity.get("external_seconds"), "external allowance"
            ),
            grace_seconds=_finite_nonnegative(
                identity.get("termination_grace_seconds"), "termination grace"
            ),
            run_order=cast(int, record["run_order"]),
            cache_observation=cast(str, identity["cache_observation"]),
            background_load=cast(str, identity["background_load"]),
        )
        if calibration_command["argv"] != list(expected_calibration):
            raise ProfileCoordinatorError(
                "calibration command differs from invocation identity"
            )
        producer_command = _validate_command_record(
            record["producer_readback"],
            "producer readback command",
            wall_required=False,
            require_success=True,
            require_logs=True,
            run_root=run_root,
        )
        inventory_command = _validate_command_record(
            record["inventory_readback"],
            "inventory readback command",
            wall_required=False,
            require_success=True,
            require_logs=True,
            run_root=run_root,
        )
        repository = Path(cast(str, expected_calibration[4]))
        if producer_command["argv"] != list(
            _readback_argv(
                "producer-readback",
                repository=repository,
                execution_revision=revision,
                output_dir=profile_dir,
                run_order=cast(int, record["run_order"]),
            )
        ) or inventory_command["argv"] != list(
            _readback_argv(
                "inventory-readback",
                repository=repository,
                execution_revision=revision,
                output_dir=profile_dir,
                run_order=cast(int, record["run_order"]),
            )
        ):
            raise ProfileCoordinatorError("readback command differs from profile binding")
        receipt_binding = _validate_receipt_binding(
            record["calibration_receipt"], "receipt binding"
        )
        inventory = _dict(record["inventory"], "inventory")
        if (
            inventory.get("schema") != INVENTORY_SCHEMA
            or inventory.get("execution_revision") != revision
            or inventory.get("run_order") != record["run_order"]
            or inventory.get("profile_directory") != str(profile_dir.resolve())
            or inventory.get("invocation_identity") != identity
            or inventory.get("receipt") != receipt_binding
        ):
            raise ProfileCoordinatorError("profile inventory binding is malformed")
        if run_root is not None:
            resolved_root = run_root.resolve()
            if (
                profile_dir.resolve().parent != resolved_root
                or profile_dir.name != f"profile-{record['run_order']}"
            ):
                raise ProfileCoordinatorError("profile directory is outside its run-set root")
            receipt_bytes = (profile_dir / "result.json").read_bytes()
            if receipt_binding["bytes"] != len(receipt_bytes) or receipt_binding[
                "sha256"
            ] != _sha256(receipt_bytes):
                raise ProfileCoordinatorError("receipt binding no longer matches result.json")
            producer_stdout = _dict(producer_command["stdout"], "producer readback stdout")
            producer_proof = _strict_json_bytes(
                (resolved_root / cast(str, producer_stdout["path"])).read_bytes(),
                "producer readback output",
            )
            _validate_readback_binding(
                producer_proof,
                schema="fixed-core-calibration-producer-readback/v1",
                execution_revision=revision,
                run_order=cast(int, record["run_order"]),
                output_dir=profile_dir,
                identity=identity,
                receipt_binding=receipt_binding,
            )
            inventory_stdout = _dict(inventory_command["stdout"], "inventory readback stdout")
            inventory_proof = _strict_json_bytes(
                (resolved_root / cast(str, inventory_stdout["path"])).read_bytes(),
                "inventory readback output",
            )
            if inventory_proof != inventory:
                raise ProfileCoordinatorError(
                    "inventory record differs from retained readback output"
                )
            _validate_inventory_proof(
                inventory_proof,
                execution_revision=revision,
                run_order=cast(int, record["run_order"]),
                output_dir=profile_dir,
                identity=identity,
                receipt_binding=receipt_binding,
                spec=None,
            )
    else:
        if not isinstance(record.get("error"), str):
            raise ProfileCoordinatorError("refused profile lacks an error")
        identity_value = record.get("invocation_identity")
        receipt_value = record.get("calibration_receipt")
        if receipt_value is None and identity_value is not None:
            raise ProfileCoordinatorError("refused profile identity lacks a receipt binding")
        if identity_value is not None:
            _dict(identity_value, "observed invocation identity")
        if receipt_value is not None:
            receipt_binding = _validate_receipt_binding(receipt_value, "receipt binding")
            if run_root is not None:
                profile_dir = Path(cast(str, record["profile_directory"]))
                if (
                    profile_dir.resolve().parent != run_root.resolve()
                    or profile_dir.name != f"profile-{record['run_order']}"
                ):
                    raise ProfileCoordinatorError(
                        "profile directory is outside its run-set root"
                    )
                receipt_bytes = (profile_dir / "result.json").read_bytes()
                if receipt_binding["bytes"] != len(receipt_bytes) or receipt_binding[
                    "sha256"
                ] != _sha256(receipt_bytes):
                    raise ProfileCoordinatorError(
                        "receipt binding no longer matches result.json"
                    )
        producer_value = record.get("producer_readback")
        inventory_command_value = record.get("inventory_readback")
        inventory_value = record.get("inventory")
        if producer_value is not None:
            if identity_value is None:
                raise ProfileCoordinatorError("producer readback lacks an invocation identity")
            identity = _validate_profile_identity(
                identity_value,
                revision=revision,
                run_order=cast(int, record["run_order"]),
            )
            profile_dir = Path(cast(str, record["profile_directory"]))
            expected_calibration = _calibration_argv(
                repository=Path(
                    _command_option(calibration_command, "--repository", "calibration command")
                ),
                execution_revision=revision,
                output_dir=profile_dir,
                workers=cast(int, identity["requested_workers"]),
                calibration_seconds=cast(float, identity["calibration_seconds"]),
                external_seconds=cast(float, identity["external_seconds"]),
                grace_seconds=cast(float, identity["termination_grace_seconds"]),
                run_order=cast(int, record["run_order"]),
                cache_observation=cast(str, identity["cache_observation"]),
                background_load=cast(str, identity["background_load"]),
            )
            if calibration_command["argv"] != list(expected_calibration):
                raise ProfileCoordinatorError(
                    "calibration command differs from invocation identity"
                )
        if producer_value is None and (
            inventory_command_value is not None or inventory_value is not None
        ):
            raise ProfileCoordinatorError(
                "inventory readback appeared before producer readback"
            )
        if producer_value is not None:
            producer_command = _validate_command_record(
                producer_value,
                "producer readback command",
                wall_required=False,
                require_success=inventory_command_value is not None,
                require_logs=False,
                run_root=run_root,
            )
            expected_producer = _readback_argv(
                "producer-readback",
                repository=Path(
                    _command_option(calibration_command, "--repository", "calibration command")
                ),
                execution_revision=revision,
                output_dir=Path(cast(str, record["profile_directory"])),
                run_order=cast(int, record["run_order"]),
            )
            if producer_command["argv"] != list(expected_producer):
                raise ProfileCoordinatorError(
                    "producer readback command differs from profile binding"
                )
        if inventory_command_value is not None:
            inventory_command = _validate_command_record(
                inventory_command_value,
                "inventory readback command",
                wall_required=False,
                require_success=inventory_value is not None,
                require_logs=False,
                run_root=run_root,
            )
            expected_inventory = _readback_argv(
                "inventory-readback",
                repository=Path(
                    _command_option(calibration_command, "--repository", "calibration command")
                ),
                execution_revision=revision,
                output_dir=Path(cast(str, record["profile_directory"])),
                run_order=cast(int, record["run_order"]),
            )
            if inventory_command["argv"] != list(expected_inventory):
                raise ProfileCoordinatorError(
                    "inventory readback command differs from profile binding"
                )
        if inventory_value is not None:
            raise ProfileCoordinatorError("refused profile carries admitted inventory")


def validate_summary(
    summary: dict[str, object],
    *,
    expected_direction_rows: int = FULL_INVENTORY_SPEC.total_direction_rows,
    run_root: Path | None = None,
) -> None:
    """Validate the closed summary schema and all observation reductions."""

    expected = {
        "schema",
        "evidence_scope",
        "execution_revision",
        "frozen_tuple",
        "settings",
        "runs",
        "metrics",
    }
    if (
        set(summary) != expected
        or summary.get("schema") != SUMMARY_SCHEMA
        or summary.get("evidence_scope") != EVIDENCE_SCOPE
    ):
        raise ProfileCoordinatorError("three-profile summary fields changed")
    revision = summary.get("execution_revision")
    if not isinstance(revision, str):
        raise ProfileCoordinatorError("summary execution revision is malformed")
    _validate_revision(revision)
    settings = _dict(summary.get("settings"), "summary settings")
    frozen = _dict(summary.get("frozen_tuple"), "summary frozen tuple")
    workers = settings.get("requested_workers")
    calibration = _finite_nonnegative(
        settings.get("calibration_seconds"), "summary calibration allowance"
    )
    external = _finite_nonnegative(
        settings.get("external_seconds"), "summary external allowance"
    )
    grace = _finite_nonnegative(
        settings.get("termination_grace_seconds"), "summary termination grace"
    )
    if (
        type(workers) is not int
        or not 1 <= cast(int, workers) <= 4
        or calibration == 0
        or external <= calibration
        or grace == 0
        or settings.get("effective_workers")
        != {
            "raw": workers,
            "normalized_exact": workers,
            "reflected_interval": 1,
            "dilation": 1,
        }
        or settings.get("expected_direction_rows") != expected_direction_rows
    ):
        raise ProfileCoordinatorError("summary settings are malformed")
    if frozen != {
        "workers": workers,
        "calibration_seconds": calibration,
        "external_seconds": external,
        "grace_seconds": grace,
    }:
        raise ProfileCoordinatorError("summary frozen tuple differs from its settings")
    runs = _list(summary.get("runs"), "summary runs")
    if len(runs) != PROFILE_COUNT:
        raise ProfileCoordinatorError("summary must bind exactly three runs")
    profile_directories: set[str] = set()
    command_walls: list[float] = []
    artifact_totals: list[float] = []
    for order, value in enumerate(runs, 1):
        run = _dict(value, "summary run")
        if (
            set(run)
            != {
                "run_order",
                "profile_directory",
                "invocation_identity",
                "calibration_receipt",
                "command_wall_seconds",
                "inventory",
            }
            or run.get("run_order") != order
        ):
            raise ProfileCoordinatorError("summary run binding is malformed")
        profile_directory = run.get("profile_directory")
        if not isinstance(profile_directory, str) or profile_directory in profile_directories:
            raise ProfileCoordinatorError("summary profile directories are malformed")
        profile_directories.add(profile_directory)
        command_walls.append(
            _finite_nonnegative(
                run.get("command_wall_seconds"), "summary command wall duration"
            )
        )
        identity = _validate_profile_identity(
            run.get("invocation_identity"), revision=revision, run_order=order
        )
        if (
            identity.get("implementation_revision") != revision
            or identity.get("run_order") != order
            or identity.get("requested_workers") != frozen.get("workers")
            or identity.get("calibration_seconds") != frozen.get("calibration_seconds")
            or identity.get("external_seconds") != frozen.get("external_seconds")
            or identity.get("termination_grace_seconds") != frozen.get("grace_seconds")
        ):
            raise ProfileCoordinatorError("summary invocation differs from the frozen tuple")
        _validate_receipt_binding(run.get("calibration_receipt"), "summary receipt binding")
        inventory = _dict(run.get("inventory"), "summary inventory")
        if (
            set(inventory) != {"direction_rows", "artifacts"}
            or inventory.get("direction_rows") != expected_direction_rows
        ):
            raise ProfileCoordinatorError("summary does not bind the exact direction-row count")
        artifacts = _list(inventory.get("artifacts"), "summary inventory artifacts")
        roles: set[str] = set()
        direction_rows = 0
        total_bytes = 0
        expected_paths = {
            role: relative
            for role, relative, *_rest in (*_DIRECTION_ROLES, *_SINGLE_FILE_ROLES)
        }
        for artifact_value in artifacts:
            artifact = _dict(artifact_value, "summary inventory artifact")
            role = artifact.get("role")
            if (
                set(artifact) != {"role", "path", "count", "bytes", "sha256"}
                or not isinstance(role, str)
                or role in roles
                or role not in expected_paths
                or artifact.get("path") != expected_paths[role]
                or type(artifact.get("count")) is not int
                or cast(int, artifact["count"]) < 0
                or type(artifact.get("bytes")) is not int
                or cast(int, artifact["bytes"]) < 0
            ):
                raise ProfileCoordinatorError("summary inventory artifact is malformed")
            _digest(artifact.get("sha256"), "summary inventory artifact digest")
            roles.add(role)
            total_bytes += cast(int, artifact["bytes"])
            if role.endswith("-directions"):
                direction_rows += cast(int, artifact["count"])
            elif artifact["count"] != 1:
                raise ProfileCoordinatorError("summary single-file artifact count changed")
        if set(expected_paths) != roles or direction_rows != expected_direction_rows:
            raise ProfileCoordinatorError("summary inventory artifact set changed")
        artifact_totals.append(float(total_bytes))
    metrics = _dict(summary.get("metrics"), "summary metrics")
    expected_metrics = {
        "command_wall_seconds",
        "interval.boxes_observed",
        "artifacts.total_bytes",
        "deadline.internal_headroom_seconds",
        "deadline.scoped_external_headroom_seconds",
        *(f"clock.{name}" for name in _CLOCK_METRICS),
        *(f"cpu.{name}" for name in _CPU_METRICS),
        *(f"rss.{name}" for name in _RSS_METRICS),
    }
    if set(metrics) != expected_metrics:
        raise ProfileCoordinatorError("summary metric set is not exact")
    for name, value in metrics.items():
        metric = _dict(value, f"summary metric {name}")
        if set(metric) != {"observations", "median", "minimum", "maximum"}:
            raise ProfileCoordinatorError(f"summary metric {name} fields changed")
        observations = [
            _finite_nonnegative(item, f"summary metric {name}")
            for item in _list(metric.get("observations"), f"summary metric {name}")
        ]
        if metric != _describe(observations):
            raise ProfileCoordinatorError(f"summary metric {name} does not reconstruct")
    if metrics["command_wall_seconds"] != _describe(command_walls):
        raise ProfileCoordinatorError("summary command wall metric is not bound to its runs")
    if metrics["artifacts.total_bytes"] != _describe(artifact_totals):
        raise ProfileCoordinatorError("summary artifact bytes are not bound to its runs")
    if run_root is not None:
        records: list[dict[str, object]] = []
        for order in range(1, PROFILE_COUNT + 1):
            record = _strict_json(
                run_root / f"profile-{order}-run.json", "profile coordinator record"
            )
            validate_profile_record(record, run_root=run_root)
            records.append(record)
        if build_summary(records) != summary:
            raise ProfileCoordinatorError(
                "three-profile summary does not reconstruct from its retained records"
            )


def _publish_profile_record(path: Path, record: dict[str, object]) -> None:
    validate_profile_record(record, run_root=path.parent)
    atomic_write_text(path, json.dumps(record, indent=2, allow_nan=False) + "\n")
    validate_profile_record(
        _strict_json(path, "profile coordinator record"), run_root=path.parent
    )


def _publish_summary(
    path: Path, summary: dict[str, object], *, expected_direction_rows: int
) -> None:
    validate_summary(
        summary,
        expected_direction_rows=expected_direction_rows,
        run_root=path.parent,
    )
    atomic_write_text(path, json.dumps(summary, indent=2, allow_nan=False) + "\n")
    validate_summary(
        _strict_json(path, "three-profile summary"),
        expected_direction_rows=expected_direction_rows,
        run_root=path.parent,
    )


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ProfileCoordinatorError(message)


def coordinate_profiles(
    *,
    repository: Path,
    execution_revision: str,
    run_root: Path,
    workers: int,
    calibration_seconds: float,
    external_seconds: float,
    grace_seconds: float,
    cache_observations: Sequence[str],
    background_loads: Sequence[str],
    runner: CommandRunner = _default_runner,
    clock: Clock = time.perf_counter,
    inventory_spec: InventorySpec = FULL_INVENTORY_SPEC,
) -> dict[str, object]:
    """Run three fresh profiles sequentially and publish their validated summary."""

    repository = repository.resolve()
    run_root = run_root.resolve()
    _validate_revision(execution_revision)
    if type(workers) is not int or not 1 <= workers <= 4:
        raise ProfileCoordinatorError("workers must be an integer from 1 through 4")
    for value, label in (
        (calibration_seconds, "calibration allowance"),
        (external_seconds, "external allowance"),
        (grace_seconds, "termination grace"),
    ):
        if _finite_nonnegative(value, label) == 0:
            raise ProfileCoordinatorError(f"{label} must be positive")
    if external_seconds <= calibration_seconds:
        raise ProfileCoordinatorError("external allowance must exceed calibration allowance")
    if run_root.is_relative_to(repository):
        raise ProfileCoordinatorError("run-set root must be outside the repository")
    if run_root.exists():
        raise ProfileCoordinatorError("run-set root must be fresh")
    if len(cache_observations) != PROFILE_COUNT or len(background_loads) != PROFILE_COUNT:
        raise ProfileCoordinatorError(
            "exactly three cache and background-load observations are required"
        )
    run_root.mkdir(parents=False)

    records: list[dict[str, object]] = []
    for run_order in range(1, PROFILE_COUNT + 1):
        output_dir = run_root / f"profile-{run_order}"
        record_path = run_root / f"profile-{run_order}-run.json"
        argv = _calibration_argv(
            repository=repository,
            execution_revision=execution_revision,
            output_dir=output_dir,
            workers=workers,
            calibration_seconds=calibration_seconds,
            external_seconds=external_seconds,
            grace_seconds=grace_seconds,
            run_order=run_order,
            cache_observation=cache_observations[run_order - 1],
            background_load=background_loads[run_order - 1],
        )
        record: dict[str, object] = {
            "schema": PROFILE_SCHEMA,
            "status": "refused",
            "execution_revision": execution_revision,
            "run_order": run_order,
            "profile_directory": str(output_dir),
            "invocation_identity": None,
            "calibration_receipt": None,
            "calibration_command": _pending_command(argv, wall_required=True),
            "producer_readback": None,
            "inventory_readback": None,
            "inventory": None,
            "error": "calibration command has not returned",
        }
        _publish_profile_record(record_path, record)
        started = clock()
        try:
            result = runner(argv)
        except OSError as error:
            command_wall_seconds = clock() - started
            calibration_command = _dict(record["calibration_command"], "calibration command")
            calibration_command["command_wall_seconds"] = command_wall_seconds
            record["error"] = f"calibration launch failed: {error}"
            _publish_profile_record(record_path, record)
            raise ProfileCoordinatorError(
                f"profile {run_order} refused; the series stopped: {record['error']}"
            ) from error
        command_wall_seconds = clock() - started
        record["calibration_command"] = _inline_command_output(
            argv, result, command_wall_seconds=command_wall_seconds
        )
        record["error"] = "calibration command returned; log publication is pending"
        _publish_profile_record(record_path, record)
        try:
            calibration_command = _write_command_output(
                run_root, f"profile-{run_order}", argv, result
            )
            calibration_command["command_wall_seconds"] = command_wall_seconds
            record["calibration_command"] = calibration_command
            record["error"] = "calibration evidence readback is pending"
            _publish_profile_record(record_path, record)
            receipt_bytes = (output_dir / "result.json").read_bytes()
            receipt_binding = {
                "path": "result.json",
                "bytes": len(receipt_bytes),
                "sha256": _sha256(receipt_bytes),
            }
            record["calibration_receipt"] = receipt_binding
            observed_receipt = _strict_json_bytes(receipt_bytes, "calibration receipt")
            observed_invocation = observed_receipt.get("invocation")
            if isinstance(observed_invocation, dict) and isinstance(
                observed_invocation.get("identity"), dict
            ):
                record["invocation_identity"] = observed_invocation["identity"]
            receipt, identity = _read_calibration_identity(
                output_dir, execution_revision, run_order
            )
            record["invocation_identity"] = identity
            _require(
                result.returncode == 0,
                f"calibration subprocess exited with status {result.returncode}",
            )
            _require(
                receipt.get("status") == "complete",
                "calibration subprocess returned noncomplete",
            )

            producer_argv = _readback_argv(
                "producer-readback",
                repository=repository,
                execution_revision=execution_revision,
                output_dir=output_dir,
                run_order=run_order,
            )
            record["producer_readback"] = _pending_command(producer_argv, wall_required=False)
            record["error"] = "producer readback command has not returned"
            _publish_profile_record(record_path, record)
            producer_result = runner(producer_argv)
            record["producer_readback"] = _inline_command_output(producer_argv, producer_result)
            record["error"] = "producer readback log publication is pending"
            _publish_profile_record(record_path, record)
            producer_command = _write_command_output(
                run_root,
                f"profile-{run_order}-producer-readback",
                producer_argv,
                producer_result,
            )
            record["producer_readback"] = producer_command
            record["error"] = "producer readback validation is pending"
            _publish_profile_record(record_path, record)
            _require(producer_result.returncode == 0, "strict producer readback failed")
            producer_proof = _strict_json_bytes(
                producer_result.stdout, "producer readback output"
            )
            _validate_readback_binding(
                producer_proof,
                schema="fixed-core-calibration-producer-readback/v1",
                execution_revision=execution_revision,
                run_order=run_order,
                output_dir=output_dir,
                identity=identity,
                receipt_binding=receipt_binding,
            )

            inventory_argv = _readback_argv(
                "inventory-readback",
                repository=repository,
                execution_revision=execution_revision,
                output_dir=output_dir,
                run_order=run_order,
            )
            record["inventory_readback"] = _pending_command(inventory_argv, wall_required=False)
            record["error"] = "inventory readback command has not returned"
            _publish_profile_record(record_path, record)
            inventory_result = runner(inventory_argv)
            record["inventory_readback"] = _inline_command_output(
                inventory_argv, inventory_result
            )
            record["error"] = "inventory readback log publication is pending"
            _publish_profile_record(record_path, record)
            inventory_command = _write_command_output(
                run_root,
                f"profile-{run_order}-inventory-readback",
                inventory_argv,
                inventory_result,
            )
            record["inventory_readback"] = inventory_command
            record["error"] = "inventory readback validation is pending"
            _publish_profile_record(record_path, record)
            _require(
                inventory_result.returncode == 0,
                "independent inventory readback failed",
            )
            inventory = _strict_json_bytes(inventory_result.stdout, "inventory readback output")
            _validate_inventory_proof(
                inventory,
                execution_revision=execution_revision,
                run_order=run_order,
                output_dir=output_dir,
                identity=identity,
                receipt_binding=receipt_binding,
                spec=inventory_spec,
            )
            record["inventory"] = inventory
            record["status"] = "complete"
            record["error"] = None
        except (OSError, ProfileCoordinatorError) as error:
            record["error"] = str(error)
            _publish_profile_record(record_path, record)
            raise ProfileCoordinatorError(
                f"profile {run_order} refused; the series stopped: {error}"
            ) from error
        _publish_profile_record(record_path, record)
        records.append(_strict_json(record_path, "profile coordinator record"))

    summary = build_summary(records)
    summary_path = run_root / "three-profile-summary.json"
    _publish_summary(
        summary_path,
        summary,
        expected_direction_rows=inventory_spec.total_direction_rows,
    )
    return summary


def _common_readback_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--expect-implementation-revision", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-order", type=int, required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--repository", type=Path, required=True)
    run.add_argument("--expect-implementation-revision", required=True)
    run.add_argument("--run-root", type=Path, required=True)
    run.add_argument("--workers", type=int, required=True)
    run.add_argument("--calibration-seconds", type=float, required=True)
    run.add_argument("--external-seconds", type=float, required=True)
    run.add_argument("--grace-seconds", type=float, required=True)
    run.add_argument("--cache-observation", action="append", required=True)
    run.add_argument("--background-load", action="append", required=True)
    _common_readback_arguments(subparsers.add_parser("producer-readback"))
    _common_readback_arguments(subparsers.add_parser("inventory-readback"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command not in {"producer-readback", "inventory-readback", "run"}:
        return 2
    try:
        if args.command == "producer-readback":
            proof = producer_readback(
                args.output_dir,
                repository=args.repository,
                execution_revision=args.expect_implementation_revision,
                run_order=args.run_order,
            )
            print(json.dumps(proof, allow_nan=False))
        elif args.command == "inventory-readback":
            inventory = inventory_profile(
                args.output_dir,
                execution_revision=args.expect_implementation_revision,
                run_order=args.run_order,
            )
            print(json.dumps(inventory, allow_nan=False))
        elif args.command == "run":
            coordinate_profiles(
                repository=args.repository,
                execution_revision=args.expect_implementation_revision,
                run_root=args.run_root,
                workers=args.workers,
                calibration_seconds=args.calibration_seconds,
                external_seconds=args.external_seconds,
                grace_seconds=args.grace_seconds,
                cache_observations=args.cache_observation,
                background_loads=args.background_load,
            )
            print(str((args.run_root / "three-profile-summary.json").resolve()))
    except (OSError, ProfileCoordinatorError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
