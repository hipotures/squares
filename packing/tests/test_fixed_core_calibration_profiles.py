"""Small-fixture and mutation controls for the calibration profile coordinator."""

# The test constructs retained-byte fixtures against independent inventory internals.
# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001

from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import cast

import pytest

from devtools import run_fixed_core_calibration_profiles as profiles

REVISION = "a" * 40
SMALL_SPEC = profiles.InventorySpec(
    raw=("0.json", "1.json"),
    normalized_exact=("0.json", "1.json"),
    normalized_interval=("0.json", "1.json", "1'.json"),
    dilation=("0.json", "1.json"),
)


def _argument(argv: tuple[str, ...], name: str) -> str:
    return argv[argv.index(name) + 1]


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=1, allow_nan=False) + "\n", encoding="utf-8")


def _fake_receipt(output: Path, run_order: int, *, status: str = "complete") -> None:
    directions = {
        "raw-directions": SMALL_SPEC.raw,
        "normalized-exact-directions": SMALL_SPEC.normalized_exact,
        "normalized-interval-directions": SMALL_SPEC.normalized_interval,
        "dilation-directions": SMALL_SPEC.dilation,
    }
    for directory, names in directions.items():
        for index, name in enumerate(names):
            label = name.removesuffix(".json")
            if directory == "raw-directions":
                row: dict[str, object] = {
                    "direction": index,
                    "charge": "2",
                    "witness": ["1", "1"],
                }
            elif directory == "normalized-exact-directions":
                row = {
                    "direction": index,
                    "dense": "1",
                    "slab": "1",
                    "agree": True,
                    "witness": ["1", "1"],
                    "slab_witness": ["1", "1"],
                }
            elif directory == "normalized-interval-directions":
                row = {
                    "label": label,
                    "status": "certified",
                    "lower": 8,
                    "upper": 8,
                    "witness": [1.0, 1.0],
                    "boxes": 1,
                    "stalled": 0,
                    "budget_exhausted": False,
                }
            else:
                row = {"direction": index, "label": label, "minimum": "1"}
            _write_json(output / directory / name, row)
    for name in ("candidate.json", "dilation.json", "rss-samples.json"):
        _write_json(output / name, {"fixture": name})

    direction_digests = {
        directory: profiles._direction_digest(
            tuple(output / directory / name for name in names)
        )
        for directory, names in directions.items()
    }
    identity: dict[str, object] = {
        "implementation_revision": REVISION,
        "requested_workers": 4,
        "calibration_seconds": 5_400.0,
        "external_seconds": 7_200.0,
        "termination_grace_seconds": 2.0,
        "monotonic_origin": float(run_order),
        "calibration_deadline_monotonic": 5_400.0 + run_order,
        "external_deadline_monotonic": 7_200.0 + run_order,
        "run_order": run_order,
        "cache_observation": f"cache-{run_order}",
        "background_load": f"load-{run_order}",
    }
    clock_names = {name: float(run_order) for name in profiles._CLOCK_METRICS}
    receipt: dict[str, object] = {
        "schema": profiles.CALIBRATION_SCHEMA,
        "status": status,
        "sources": {"implementation_revision": REVISION},
        "invocation": {"run_order": run_order, "identity": identity},
        "settings": {
            "requested_workers": 4,
            "effective_workers": {
                "raw": 4,
                "normalized_exact": 4,
                "reflected_interval": 1,
                "dilation": 1,
            },
            "calibration_seconds": 5_400.0,
            "external_seconds": 7_200.0,
            "termination_grace_seconds": 2.0,
            "expected_direction_rows": SMALL_SPEC.total_direction_rows,
        },
        "clocks": clock_names,
        "resources": {
            "coordinator_process_seconds": float(run_order),
            "reaped_direct_children_user_seconds": float(run_order),
            "reaped_direct_children_system_seconds": float(run_order),
            "rss": {
                "sample_count": 2,
                "positive_sample_count": 2,
                "maximum_actual_gap_seconds": 0.1,
                "peak_sampled_rss_bytes": 1000 * run_order,
                "unobserved_leading_seconds": 0.01,
                "unobserved_trailing_seconds": 0.01,
                "observer_errors": [],
                "samples_sha256": profiles._sha256((output / "rss-samples.json").read_bytes()),
            },
        },
        "raw": {"directions_sha256": direction_digests["raw-directions"]},
        "normalized": {"sha256": profiles._sha256((output / "candidate.json").read_bytes())},
        "routes": {
            "normalized_exact": {
                "directions_sha256": direction_digests["normalized-exact-directions"]
            },
            "reflected_interval": {
                "directions_sha256": direction_digests["normalized-interval-directions"],
                "boxes_observed": 10 * run_order,
            },
            "dilation": {
                "directions_sha256": direction_digests["dilation-directions"],
                "record_sha256": profiles._sha256((output / "dilation.json").read_bytes()),
            },
        },
        "artifacts": [],
        "supervision": {
            "status": "observed-exit",
            "worker_exit_status": 0,
            "process_group_reaped": True,
            "supervisor_signal": None,
        },
        "disposition": "calibration-passed" if status == "complete" else "incomplete",
        "phase": "complete" if status == "complete" else "readback",
        "error": None if status == "complete" else "fixture interruption",
    }
    size = 0
    for _attempt in range(10):
        rows = []
        for role, relative, *_rest in profiles._DIRECTION_ROLES:
            files = tuple(output / relative / name for name in directions[relative])
            rows.append(
                {
                    "role": role,
                    "path": relative,
                    "count": len(files),
                    "bytes": sum(path.stat().st_size for path in files),
                }
            )
        rows.extend(
            {
                "role": role,
                "path": relative,
                "count": 1,
                "bytes": size
                if relative == "result.json"
                else (output / relative).stat().st_size,
            }
            for role, relative in profiles._SINGLE_FILE_ROLES
        )
        receipt["artifacts"] = rows
        encoded = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
        next_size = len(encoded.encode())
        if next_size == size:
            (output / "result.json").write_text(encoded, encoding="utf-8")
            return
        size = next_size
    raise AssertionError("fake receipt size did not converge")


class FakeRunner:
    def __init__(
        self,
        *,
        partial_order: int | None = None,
        failed_readback: str | None = None,
        bad_identity: bool = False,
    ) -> None:
        self.partial_order = partial_order
        self.failed_readback = failed_readback
        self.bad_identity = bad_identity
        self.calibration_orders: list[int] = []
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, arguments: profiles.Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        argv = tuple(arguments)
        self.calls.append(argv)
        mode = argv[3] if argv[2] == "devtools.run_fixed_core_calibration_profiles" else "run"
        output = Path(_argument(argv, "--output-dir"))
        order = int(_argument(argv, "--run-order"))
        if mode == "run":
            self.calibration_orders.append(order)
            _fake_receipt(
                output,
                order,
                status="partial" if order == self.partial_order else "complete",
            )
            if self.bad_identity:
                receipt = profiles._strict_json(output / "result.json", "receipt")
                invocation = cast(dict[str, object], receipt["invocation"])
                identity = cast(dict[str, object], invocation["identity"])
                identity["implementation_revision"] = "b" * 40
                (output / "result.json").write_text(
                    json.dumps(receipt, indent=2, allow_nan=False) + "\n",
                    encoding="utf-8",
                )
            return subprocess.CompletedProcess(argv, 0, f"profile {order}\r\n".encode(), b"")
        if mode == self.failed_readback:
            return subprocess.CompletedProcess(
                argv,
                7,
                f"{mode} stdout\r\n".encode(),
                f"{mode} failed\r\n".encode(),
            )
        receipt, identity = profiles._read_calibration_identity(output, REVISION, order)
        data = (output / "result.json").read_bytes()
        binding = {
            "path": "result.json",
            "bytes": len(data),
            "sha256": profiles._sha256(data),
        }
        if mode == "producer-readback":
            proof = {
                "schema": "fixed-core-calibration-producer-readback/v1",
                "execution_revision": REVISION,
                "run_order": order,
                "profile_directory": str(output.resolve()),
                "invocation_identity": identity,
                "receipt": binding,
            }
        else:
            assert receipt["status"] == "complete"
            proof = profiles.inventory_profile(
                output,
                execution_revision=REVISION,
                run_order=order,
                spec=SMALL_SPEC,
            )
        return subprocess.CompletedProcess(
            argv, 0, (json.dumps(proof, allow_nan=False) + "\n").encode(), b""
        )


class LaunchFailureRunner:
    def __call__(self, arguments: profiles.Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        del arguments
        raise OSError("fixture launch failure")


def test_three_profiles_are_sequentially_bound_and_summarized(tmp_path: Path) -> None:
    runner = FakeRunner()
    ticks = iter((10.0, 12.0, 20.0, 23.0, 30.0, 34.0))
    run_root = tmp_path / "profiles"
    summary = profiles.coordinate_profiles(
        repository=tmp_path / "repository",
        execution_revision=REVISION,
        run_root=run_root,
        workers=4,
        calibration_seconds=5_400.0,
        external_seconds=7_200.0,
        grace_seconds=2.0,
        cache_observations=("cache-1", "cache-2", "cache-3"),
        background_loads=("load-1", "load-2", "load-3"),
        runner=runner,
        clock=lambda: next(ticks),
        inventory_spec=SMALL_SPEC,
    )

    assert runner.calibration_orders == [1, 2, 3]
    assert len(runner.calls) == 9
    assert (run_root / "profile-1.stdout.log").read_bytes() == b"profile 1\r\n"
    assert cast(dict[str, object], summary["metrics"])["command_wall_seconds"] == {
        "observations": [2.0, 3.0, 4.0],
        "median": 3.0,
        "minimum": 2.0,
        "maximum": 4.0,
    }
    assert [
        cast(dict[str, object], row)["direction_rows"]
        for row in (
            cast(dict[str, object], run)["inventory"]
            for run in cast(list[object], summary["runs"])
        )
    ] == [SMALL_SPEC.total_direction_rows] * 3
    profiles.validate_summary(summary, expected_direction_rows=SMALL_SPEC.total_direction_rows)
    assert profiles._strict_json(run_root / "three-profile-summary.json", "summary") == summary


def test_first_noncomplete_profile_stops_the_series(tmp_path: Path) -> None:
    runner = FakeRunner(partial_order=2)
    ticks = iter((1.0, 2.0, 3.0, 4.0))
    run_root = tmp_path / "profiles"
    with pytest.raises(profiles.ProfileCoordinatorError, match="profile 2 refused"):
        profiles.coordinate_profiles(
            repository=tmp_path / "repository",
            execution_revision=REVISION,
            run_root=run_root,
            workers=4,
            calibration_seconds=5_400.0,
            external_seconds=7_200.0,
            grace_seconds=2.0,
            cache_observations=("cache-1", "cache-2", "cache-3"),
            background_loads=("load-1", "load-2", "load-3"),
            runner=runner,
            clock=lambda: next(ticks),
            inventory_spec=SMALL_SPEC,
        )

    assert runner.calibration_orders == [1, 2]
    refused = profiles._strict_json(run_root / "profile-2-run.json", "refused run")
    assert refused["status"] == "refused"
    assert refused["invocation_identity"] is not None
    assert refused["calibration_receipt"] is not None
    assert not (run_root / "profile-3").exists()
    assert not (run_root / "three-profile-summary.json").exists()


def test_launch_failure_retains_the_attempt_and_measured_wall_time(tmp_path: Path) -> None:
    run_root = tmp_path / "profiles"
    with pytest.raises(profiles.ProfileCoordinatorError, match="fixture launch failure"):
        profiles.coordinate_profiles(
            repository=tmp_path / "repository",
            execution_revision=REVISION,
            run_root=run_root,
            workers=4,
            calibration_seconds=5_400.0,
            external_seconds=7_200.0,
            grace_seconds=2.0,
            cache_observations=("cache-1", "cache-2", "cache-3"),
            background_loads=("load-1", "load-2", "load-3"),
            runner=LaunchFailureRunner(),
            clock=iter((10.0, 12.5)).__next__,
            inventory_spec=SMALL_SPEC,
        )

    record = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    command = cast(dict[str, object], record["calibration_command"])
    assert cast(list[str], command["argv"])[2] == profiles.CALIBRATION_MODULE
    assert command["exit_status"] is None
    assert command["stdout"] is None
    assert command["stderr"] is None
    assert command["command_wall_seconds"] == 2.5
    profiles.validate_profile_record(record, run_root=run_root)


def test_log_write_failure_retains_returned_streams_inline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    run_root = tmp_path / "profiles"

    def fail_log_write(path: Path, data: bytes) -> None:
        del path, data
        raise OSError("fixture log failure")

    monkeypatch.setattr(profiles, "atomic_write_bytes", fail_log_write)
    with pytest.raises(profiles.ProfileCoordinatorError, match="fixture log failure"):
        profiles.coordinate_profiles(
            repository=tmp_path / "repository",
            execution_revision=REVISION,
            run_root=run_root,
            workers=4,
            calibration_seconds=5_400.0,
            external_seconds=7_200.0,
            grace_seconds=2.0,
            cache_observations=("cache-1", "cache-2", "cache-3"),
            background_loads=("load-1", "load-2", "load-3"),
            runner=FakeRunner(),
            clock=iter((4.0, 7.0)).__next__,
            inventory_spec=SMALL_SPEC,
        )

    record = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    command = cast(dict[str, object], record["calibration_command"])
    stdout = cast(dict[str, object], command["stdout"])
    assert command["exit_status"] == 0
    assert command["command_wall_seconds"] == 3.0
    assert stdout["base64"] == "cHJvZmlsZSAxDQo="
    assert stdout["bytes"] == len(b"profile 1\r\n")
    assert stdout["sha256"] == profiles._sha256(b"profile 1\r\n")
    profiles.validate_profile_record(record, run_root=run_root)

    damaged = deepcopy(record)
    damaged_stdout = cast(
        dict[str, object],
        cast(dict[str, object], damaged["calibration_command"])["stdout"],
    )
    damaged_stdout["base64"] = "Y2hhbmdlZAo="
    with pytest.raises(profiles.ProfileCoordinatorError, match="does not reconstruct"):
        profiles.validate_profile_record(damaged, run_root=run_root)


def test_malformed_invocation_still_retains_the_receipt_binding(tmp_path: Path) -> None:
    runner = FakeRunner(bad_identity=True)
    run_root = tmp_path / "profiles"
    with pytest.raises(profiles.ProfileCoordinatorError, match="profile 1 refused"):
        profiles.coordinate_profiles(
            repository=tmp_path / "repository",
            execution_revision=REVISION,
            run_root=run_root,
            workers=4,
            calibration_seconds=5_400.0,
            external_seconds=7_200.0,
            grace_seconds=2.0,
            cache_observations=("cache-1", "cache-2", "cache-3"),
            background_loads=("load-1", "load-2", "load-3"),
            runner=runner,
            clock=iter((1.0, 2.0)).__next__,
            inventory_spec=SMALL_SPEC,
        )

    record = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    binding = cast(dict[str, object], record["calibration_receipt"])
    retained = (run_root / "profile-1/result.json").read_bytes()
    assert binding == {
        "path": "result.json",
        "bytes": len(retained),
        "sha256": profiles._sha256(retained),
    }
    assert (
        cast(dict[str, object], record["invocation_identity"])["implementation_revision"]
        == "b" * 40
    )
    profiles.validate_profile_record(record, run_root=run_root)


@pytest.mark.parametrize("failed_readback", ["producer-readback", "inventory-readback"])
def test_failed_readback_retains_exact_command_streams_and_status(
    tmp_path: Path, failed_readback: str
) -> None:
    runner = FakeRunner(failed_readback=failed_readback)
    run_root = tmp_path / "profiles"
    with pytest.raises(profiles.ProfileCoordinatorError, match="profile 1 refused"):
        profiles.coordinate_profiles(
            repository=tmp_path / "repository",
            execution_revision=REVISION,
            run_root=run_root,
            workers=4,
            calibration_seconds=5_400.0,
            external_seconds=7_200.0,
            grace_seconds=2.0,
            cache_observations=("cache-1", "cache-2", "cache-3"),
            background_loads=("load-1", "load-2", "load-3"),
            runner=runner,
            clock=iter((1.0, 2.0)).__next__,
            inventory_spec=SMALL_SPEC,
        )

    record = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    command = cast(dict[str, object], record[failed_readback.replace("-", "_")])
    assert command["exit_status"] == 7
    assert (run_root / f"profile-1-{failed_readback}.stdout.log").read_bytes() == (
        f"{failed_readback} stdout\r\n".encode()
    )
    assert (run_root / f"profile-1-{failed_readback}.stderr.log").read_bytes() == (
        f"{failed_readback} failed\r\n".encode()
    )
    profiles.validate_profile_record(record, run_root=run_root)

    (run_root / f"profile-1-{failed_readback}.stderr.log").write_bytes(b"changed\n")
    with pytest.raises(profiles.ProfileCoordinatorError, match="retained log"):
        profiles.validate_profile_record(record, run_root=run_root)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "digest"])
def test_inventory_mutations_are_refused(tmp_path: Path, mutation: str) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    if mutation == "duplicate":
        (output / "candidate.json").write_text('{"x":1,"x":2}\n', encoding="utf-8")
    elif mutation == "missing":
        (output / "raw-directions/1.json").unlink()
    else:
        receipt = profiles._strict_json(output / "result.json", "receipt")
        cast(dict[str, object], receipt["raw"])["directions_sha256"] = "0" * 64
        _write_json(output / "result.json", receipt)
    with pytest.raises(profiles.ProfileCoordinatorError):
        profiles.inventory_profile(
            output,
            execution_revision=REVISION,
            run_order=1,
            spec=SMALL_SPEC,
        )


def test_inventory_refuses_a_coherently_rehashed_wrong_known_answer(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    raw_path = output / "raw-directions/1.json"
    raw = profiles._strict_json(raw_path, "raw row")
    raw["charge"] = "3"
    _write_json(raw_path, raw)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    raw_receipt = cast(dict[str, object], receipt["raw"])
    raw_receipt["directions_sha256"] = profiles._direction_digest(
        tuple(output / "raw-directions" / name for name in SMALL_SPEC.raw)
    )
    (output / "result.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    with pytest.raises(profiles.ProfileCoordinatorError, match="known-answer"):
        profiles.inventory_profile(
            output,
            execution_revision=REVISION,
            run_order=1,
            spec=SMALL_SPEC,
        )


def test_inventory_proof_refuses_relabelled_artifacts_and_unbound_route_digest(
    tmp_path: Path,
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    inventory = profiles.inventory_profile(
        output,
        execution_revision=REVISION,
        run_order=1,
        spec=SMALL_SPEC,
    )
    identity = cast(dict[str, object], inventory["invocation_identity"])
    receipt = cast(dict[str, object], inventory["receipt"])

    relabelled = deepcopy(inventory)
    artifacts = cast(list[dict[str, object]], relabelled["artifacts"])
    artifacts[0]["path"] = "other-directions"
    with pytest.raises(profiles.ProfileCoordinatorError, match="artifact path or count"):
        profiles._validate_inventory_proof(
            relabelled,
            execution_revision=REVISION,
            run_order=1,
            output_dir=output,
            identity=identity,
            receipt_binding=receipt,
            spec=SMALL_SPEC,
        )

    unbound = deepcopy(inventory)
    route_digests = cast(dict[str, object], unbound["route_digests"])
    route_digests["raw"] = "0" * 64
    with pytest.raises(profiles.ProfileCoordinatorError, match="route digest"):
        profiles._validate_inventory_proof(
            unbound,
            execution_revision=REVISION,
            run_order=1,
            output_dir=output,
            identity=identity,
            receipt_binding=receipt,
            spec=SMALL_SPEC,
        )


def test_summary_readback_refuses_duplicate_key_and_bad_reduction(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema":"x","schema":"y"}\n', encoding="utf-8")
    with pytest.raises(profiles.ProfileCoordinatorError, match="duplicate"):
        profiles._strict_json(duplicate, "summary")

    runner = FakeRunner()
    ticks = iter((1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
    summary = profiles.coordinate_profiles(
        repository=tmp_path / "repository",
        execution_revision=REVISION,
        run_root=tmp_path / "profiles",
        workers=4,
        calibration_seconds=5_400.0,
        external_seconds=7_200.0,
        grace_seconds=2.0,
        cache_observations=("cache-1", "cache-2", "cache-3"),
        background_loads=("load-1", "load-2", "load-3"),
        runner=runner,
        clock=lambda: next(ticks),
        inventory_spec=SMALL_SPEC,
    )
    damaged = deepcopy(summary)
    wall = cast(
        dict[str, object], cast(dict[str, object], damaged["metrics"])["command_wall_seconds"]
    )
    wall["median"] = 99.0
    with pytest.raises(profiles.ProfileCoordinatorError, match="does not reconstruct"):
        profiles.validate_summary(
            damaged, expected_direction_rows=SMALL_SPEC.total_direction_rows
        )

    coherent = deepcopy(summary)
    coherent_runs = cast(list[dict[str, object]], coherent["runs"])
    for run in coherent_runs:
        run["command_wall_seconds"] = 9.0
    coherent_metrics = cast(dict[str, object], coherent["metrics"])
    coherent_metrics["command_wall_seconds"] = {
        "observations": [9.0, 9.0, 9.0],
        "median": 9.0,
        "minimum": 9.0,
        "maximum": 9.0,
    }
    with pytest.raises(profiles.ProfileCoordinatorError, match="retained records"):
        profiles.validate_summary(
            coherent,
            expected_direction_rows=SMALL_SPEC.total_direction_rows,
            run_root=tmp_path / "profiles",
        )


def test_profile_record_refuses_argv_and_log_mutations(tmp_path: Path) -> None:
    runner = FakeRunner()
    ticks = iter((1.0, 2.0, 3.0, 4.0, 5.0, 6.0))
    run_root = tmp_path / "profiles"
    profiles.coordinate_profiles(
        repository=tmp_path / "repository",
        execution_revision=REVISION,
        run_root=run_root,
        workers=4,
        calibration_seconds=5_400.0,
        external_seconds=7_200.0,
        grace_seconds=2.0,
        cache_observations=("cache-1", "cache-2", "cache-3"),
        background_loads=("load-1", "load-2", "load-3"),
        runner=runner,
        clock=lambda: next(ticks),
        inventory_spec=SMALL_SPEC,
    )
    record = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    damaged = deepcopy(record)
    command = cast(dict[str, object], damaged["calibration_command"])
    argv = cast(list[str], command["argv"])
    argv[argv.index("--workers") + 1] = "3"
    with pytest.raises(profiles.ProfileCoordinatorError, match="invocation identity"):
        profiles.validate_profile_record(damaged, run_root=run_root)

    (run_root / "profile-1.stdout.log").write_text("changed\n", encoding="utf-8")
    with pytest.raises(profiles.ProfileCoordinatorError, match="retained log"):
        profiles.validate_profile_record(record, run_root=run_root)
