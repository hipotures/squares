"""Small-fixture and mutation controls for the calibration profile coordinator."""

# The test constructs retained-byte fixtures against independent inventory internals.
# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001

from __future__ import annotations

import json
import os
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


def _fake_topology_route(
    *, phase: str, coordinator_pid: int, first_child_pid: int, start: float
) -> dict[str, object]:
    tasks = [
        {
            "direction": 0,
            "pid": first_child_pid,
            "ppid": coordinator_pid,
            "pgid": coordinator_pid,
            "started_seconds": start,
            "finished_seconds": start + 0.3,
        },
        {
            "direction": 1,
            "pid": first_child_pid + 1,
            "ppid": coordinator_pid,
            "pgid": coordinator_pid,
            "started_seconds": start + 0.1,
            "finished_seconds": start + 0.4,
        },
    ]
    children = [
        {
            "role": "route-worker",
            "phase": phase,
            "pid": task["pid"],
            "ppid": coordinator_pid,
            "pgid": coordinator_pid,
            "tasks_completed": 1,
            "first_task_started_seconds": task["started_seconds"],
            "last_task_finished_seconds": task["finished_seconds"],
        }
        for task in tasks
    ]
    return {
        "phase": phase,
        "execution_model": "process-pool",
        "configured_workers": 4,
        "directions_expected": 2,
        "directions_completed": 2,
        "child_tasks_observed": 2,
        "observed_child_count": 2,
        "maximum_simultaneous_children": 2,
        "tasks": tasks,
        "children": children,
    }


def _publish_fake_receipt(output: Path, receipt: dict[str, object]) -> None:
    directions = {
        "raw-directions": SMALL_SPEC.raw,
        "normalized-exact-directions": SMALL_SPEC.normalized_exact,
        "normalized-interval-directions": SMALL_SPEC.normalized_interval,
        "dilation-directions": SMALL_SPEC.dilation,
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


def _rewrite_receipt_with_retained_artifacts(output: Path, receipt: dict[str, object]) -> None:
    artifacts = cast(list[dict[str, object]], receipt["artifacts"])
    result_row = next(row for row in artifacts if row["role"] == "calibration-receipt")
    size = 0
    for _attempt in range(10):
        result_row["bytes"] = size
        encoded = json.dumps(receipt, indent=2, allow_nan=False) + "\n"
        next_size = len(encoded.encode())
        if next_size == size:
            (output / "result.json").write_text(encoded, encoding="utf-8")
            return
        size = next_size
    raise AssertionError("mutated receipt size did not converge")


def _republish_topology_sidecar(output: Path, route: str, sidecar: dict[str, object]) -> None:
    filename = f"{route.replace('_', '-')}-worker-topology.json"
    _write_json(output / filename, sidecar)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    resources = cast(dict[str, object], receipt["resources"])
    topology = cast(dict[str, object], resources["worker_topology"])
    summaries = cast(dict[str, object], topology["routes"])
    summary = cast(dict[str, object], summaries[route])
    summary["record_sha256"] = profiles._sha256((output / filename).read_bytes())
    _publish_fake_receipt(output, receipt)


def _replace_receipt_with_special(output: Path, kind: str, target: Path) -> None:
    receipt_path = output / "result.json"
    retained = receipt_path.read_bytes()
    receipt_path.unlink()
    if kind == "symlink":
        target.write_bytes(retained)
        receipt_path.symlink_to(target)
    else:
        os.mkfifo(receipt_path)


def _fake_receipt(
    output: Path,
    run_order: int,
    *,
    status: str = "complete",
    platform_name: str = "macOS-test",
) -> None:
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

    coordinator_pid = 10_000 + run_order
    coordinator = {
        "role": "coordinator",
        "pid": coordinator_pid,
        "ppid": 9_999,
        "pgid": coordinator_pid,
    }
    topology_routes = {
        "raw": _fake_topology_route(
            phase="raw-sweep",
            coordinator_pid=coordinator_pid,
            first_child_pid=20_000 + 10 * run_order,
            start=0.1,
        ),
        "normalized_exact": _fake_topology_route(
            phase="normalized-exact",
            coordinator_pid=coordinator_pid,
            first_child_pid=30_000 + 10 * run_order,
            start=0.6,
        ),
    }
    topology_summaries: dict[str, object] = {}
    for route, filename in (
        ("raw", "raw-worker-topology.json"),
        ("normalized_exact", "normalized-exact-worker-topology.json"),
    ):
        detail = cast(dict[str, object], topology_routes[route])
        _write_json(
            output / filename,
            {
                "schema": profiles.WORKER_TOPOLOGY_ROUTE_SCHEMA,
                "scope": profiles.WORKER_TOPOLOGY_SCOPE,
                "coordinator": coordinator,
                "route": detail,
            },
        )
        topology_summaries[route] = {
            "configured_workers": detail["configured_workers"],
            "execution_model": detail["execution_model"],
            "observed_child_count": detail["observed_child_count"],
            "maximum_simultaneous_children": detail["maximum_simultaneous_children"],
            "record_path": filename,
            "record_sha256": profiles._sha256((output / filename).read_bytes()),
        }

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
    clock_names = dict.fromkeys(profiles._CLOCK_METRICS, 0.1)
    clock_names["worker_elapsed_seconds"] = 1.0
    receipt: dict[str, object] = {
        "schema": profiles.CALIBRATION_SCHEMA,
        "status": status,
        "sources": {"implementation_revision": REVISION},
        "invocation": {
            "run_order": run_order,
            "platform": platform_name,
            "identity": identity,
        },
        "settings": {
            "requested_workers": 4,
            "effective_workers": {
                "raw": 4,
                "normalized_exact": 4,
                "reflected_interval": 4 if platform_name.startswith("Linux") else 1,
                "dilation": 4 if platform_name.startswith("Linux") else 1,
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
            "worker_topology": {
                "schema": profiles.WORKER_TOPOLOGY_SCHEMA,
                "scope": profiles.WORKER_TOPOLOGY_SCOPE,
                "coordinator": coordinator,
                "routes": topology_summaries,
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
            "coordinator_pid": coordinator_pid,
            "coordinator_process_group_id": coordinator_pid,
        },
        "disposition": "calibration-passed" if status == "complete" else "incomplete",
        "phase": "complete" if status == "complete" else "readback",
        "error": None if status == "complete" else "fixture interruption",
    }
    _publish_fake_receipt(output, receipt)


class FakeRunner:
    def __init__(
        self,
        *,
        partial_order: int | None = None,
        failed_readback: str | None = None,
        bad_identity: bool = False,
        platform_name: str = "macOS-test",
    ) -> None:
        self.partial_order = partial_order
        self.failed_readback = failed_readback
        self.bad_identity = bad_identity
        self.platform_name = platform_name
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
                platform_name=self.platform_name,
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


def test_linux_worker_shape_is_retained_in_inventory_and_summary(tmp_path: Path) -> None:
    runner = FakeRunner(platform_name="Linux-test")
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
        clock=iter((1.0, 2.0, 3.0, 4.0, 5.0, 6.0)).__next__,
        inventory_spec=SMALL_SPEC,
    )
    profiles.validate_summary(summary, expected_direction_rows=SMALL_SPEC.total_direction_rows)
    settings = cast(dict[str, object], summary["settings"])
    effective = cast(dict[str, object], settings["effective_workers"])
    assert effective["reflected_interval"] == effective["dilation"] == 4

    output = tmp_path / "profiles/profile-1"
    receipt = profiles._strict_json(output / "result.json", "receipt")
    configured = cast(
        dict[str, object], cast(dict[str, object], receipt["settings"])["effective_workers"]
    )
    configured["dilation"] = 1
    _publish_fake_receipt(output, receipt)
    with pytest.raises(profiles.ProfileCoordinatorError, match="worker settings changed"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )


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


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_result_receipt_special_file_is_refused_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    _replace_receipt_with_special(output, kind, tmp_path / "receipt-target.json")

    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.name == "result.json" and (path.is_symlink() or not path.is_file()):
            raise AssertionError("special receipt content was read")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    with pytest.raises(profiles.ProfileCoordinatorError, match="not a regular file"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_coordinator_refuses_special_result_before_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    fake = FakeRunner()
    original_read_bytes = Path.read_bytes

    def guarded_read_bytes(path: Path) -> bytes:
        if path.name == "result.json" and (path.is_symlink() or not path.is_file()):
            raise AssertionError("special receipt content was read")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)

    def runner(arguments: profiles.Sequence[str]) -> subprocess.CompletedProcess[bytes]:
        result = fake(arguments)
        if arguments[2] == profiles.CALIBRATION_MODULE:
            output = Path(_argument(tuple(arguments), "--output-dir"))
            _replace_receipt_with_special(output, kind, tmp_path / "receipt-target.json")
        return result

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
    refused = profiles._strict_json(run_root / "profile-1-run.json", "profile record")
    assert refused["status"] == "refused"
    assert "not a regular file" in cast(str, refused["error"])


def test_inventory_binds_topology_sidecars_as_exact_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)

    inventory = profiles.inventory_profile(
        output,
        execution_revision=REVISION,
        run_order=1,
        spec=SMALL_SPEC,
    )
    by_role = {
        cast(str, row["role"]): row
        for row in cast(list[dict[str, object]], inventory["artifacts"])
    }
    for role, filename in (
        ("raw-worker-topology", "raw-worker-topology.json"),
        ("normalized-exact-worker-topology", "normalized-exact-worker-topology.json"),
    ):
        retained = (output / filename).read_bytes()
        assert by_role[role] == {
            "role": role,
            "path": filename,
            "count": 1,
            "bytes": len(retained),
            "sha256": profiles._sha256(retained),
        }


def test_inventory_binds_receipt_artifact_to_first_safe_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt_path = output / "result.json"
    retained = receipt_path.read_bytes()
    replacement = retained.replace(b'"cache-1"', b'"cache-x"')
    assert replacement != retained
    assert len(replacement) == len(retained)
    original_read = profiles._read_regular_file

    def replace_after_read(path: Path, label: str) -> bytes:
        data = original_read(path, label)
        if path == receipt_path:
            receipt_path.write_bytes(replacement)
        return data

    monkeypatch.setattr(profiles, "_read_regular_file", replace_after_read)
    inventory = profiles.inventory_profile(
        output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
    )
    receipt_binding = cast(dict[str, object], inventory["receipt"])
    artifact = next(
        row
        for row in cast(list[dict[str, object]], inventory["artifacts"])
        if row["role"] == "calibration-receipt"
    )
    assert receipt_binding["sha256"] == profiles._sha256(retained)
    assert artifact["sha256"] == receipt_binding["sha256"]
    assert artifact["bytes"] == receipt_binding["bytes"] == len(retained)
    assert profiles._sha256(receipt_path.read_bytes()) != receipt_binding["sha256"]


@pytest.mark.parametrize("replacement", ["symlink", "fifo"])
def test_inventory_refuses_special_receipt_replaced_after_safe_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, replacement: str
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt_path = output / "result.json"
    original_read = profiles._read_regular_file

    def replace_after_read(path: Path, label: str) -> bytes:
        data = original_read(path, label)
        if path == receipt_path:
            _replace_receipt_with_special(output, replacement, tmp_path / "receipt-target.json")
        return data

    monkeypatch.setattr(profiles, "_read_regular_file", replace_after_read)
    with pytest.raises(profiles.ProfileCoordinatorError, match="not a real file"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )


@pytest.mark.parametrize("mutation", ["single", "combined", "finite-sum-overflow"])
def test_inventory_refuses_worker_phase_durations_beyond_elapsed(
    tmp_path: Path, mutation: str
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    profiles.inventory_profile(
        output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
    )
    receipt = profiles._strict_json(output / "result.json", "receipt")
    clocks = cast(dict[str, object], receipt["clocks"])
    if mutation == "single":
        clocks["raw_seconds"] = 100.0
    elif mutation == "combined":
        for phase in (
            "preflight_seconds",
            "raw_seconds",
            "normalization_publication_seconds",
            "exact_seconds",
            "interval_seconds",
            "dilation_seconds",
            "full_readback_seconds",
        ):
            clocks[phase] = 0.2
    else:
        clocks["raw_seconds"] = clocks["exact_seconds"] = 1e308
        clocks["worker_elapsed_seconds"] = 1e308
    _publish_fake_receipt(output, receipt)
    with pytest.raises(profiles.ProfileCoordinatorError, match="phase durations"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )


def test_inventory_phase_rounding_tolerance_has_a_small_boundary() -> None:
    clocks: dict[str, object] = dict.fromkeys(profiles._WORKER_DISJOINT_PHASES, 0.1)
    clocks["worker_elapsed_seconds"] = 0.7 - 5e-10
    profiles._validate_worker_phase_durations(clocks)
    clocks["worker_elapsed_seconds"] = 0.7 - 5e-7
    with pytest.raises(profiles.ProfileCoordinatorError, match="phase durations"):
        profiles._validate_worker_phase_durations(clocks)


def test_inventory_accepts_finite_phase_total_near_float_limit() -> None:
    clocks: dict[str, object] = dict.fromkeys(profiles._WORKER_DISJOINT_PHASES, 0.0)
    clocks.update(raw_seconds=1e308, exact_seconds=7e307, worker_elapsed_seconds=1.7e308)
    profiles._validate_worker_phase_durations(clocks)


def test_inventory_refuses_nonfinite_derived_deadlines(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    settings = cast(dict[str, object], receipt["settings"])
    settings.update(calibration_seconds=1e308, external_seconds=1.1e308)
    identity = cast(
        dict[str, object], cast(dict[str, object], receipt["invocation"])["identity"]
    )
    identity.update(
        monotonic_origin=1e308,
        calibration_seconds=1e308,
        external_seconds=1.1e308,
        calibration_deadline_monotonic=1e307,
        external_deadline_monotonic=1e307,
    )
    _publish_fake_receipt(output, receipt)
    receipt_path = output / "result.json"
    encoded = receipt_path.read_text(encoding="utf-8")
    for field in ("calibration_deadline_monotonic", "external_deadline_monotonic"):
        placeholder = f'"{field}": 1e+307'
        assert placeholder in encoded
        encoded = encoded.replace(placeholder, f'"{field}": 1e999 ', 1)
    receipt_path.write_text(encoded, encoding="utf-8")
    with pytest.raises(profiles.ProfileCoordinatorError, match="deadline"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )
    parsed = profiles._strict_json(receipt_path, "receipt")
    parsed_identity = cast(
        dict[str, object], cast(dict[str, object], parsed["invocation"])["identity"]
    )
    with pytest.raises(profiles.ProfileCoordinatorError, match="deadline"):
        profiles._validate_profile_identity(parsed_identity, revision=REVISION, run_order=1)


def test_inventory_accepts_finite_derived_deadlines_near_float_limit(
    tmp_path: Path,
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    calibration_seconds = 1e307
    external_seconds = 2e307
    origin = 1e308
    settings = cast(dict[str, object], receipt["settings"])
    settings.update(calibration_seconds=calibration_seconds, external_seconds=external_seconds)
    identity = cast(
        dict[str, object], cast(dict[str, object], receipt["invocation"])["identity"]
    )
    identity.update(
        monotonic_origin=origin,
        calibration_seconds=calibration_seconds,
        external_seconds=external_seconds,
        calibration_deadline_monotonic=origin + calibration_seconds,
        external_deadline_monotonic=origin + external_seconds,
    )
    _publish_fake_receipt(output, receipt)
    profiles.inventory_profile(
        output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
    )
    profiles._validate_profile_identity(identity, revision=REVISION, run_order=1)


def test_inventory_refuses_retired_four_field_supervision(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    supervision = cast(dict[str, object], receipt["supervision"])
    del supervision["coordinator_pid"]
    del supervision["coordinator_process_group_id"]
    _publish_fake_receipt(output, receipt)

    with pytest.raises(profiles.ProfileCoordinatorError, match="reaped successful worker"):
        profiles.inventory_profile(
            output,
            execution_revision=REVISION,
            run_order=1,
            spec=SMALL_SPEC,
        )


@pytest.mark.parametrize("mutation", ["missing", "digest", "count", "bytes"])
def test_inventory_refuses_unbound_topology_artifacts(tmp_path: Path, mutation: str) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    if mutation == "missing":
        (output / "raw-worker-topology.json").unlink()
    else:
        receipt = profiles._strict_json(output / "result.json", "receipt")
        if mutation == "digest":
            resources = cast(dict[str, object], receipt["resources"])
            topology = cast(dict[str, object], resources["worker_topology"])
            routes = cast(dict[str, object], topology["routes"])
            raw = cast(dict[str, object], routes["raw"])
            raw["record_sha256"] = "0" * 64
            _publish_fake_receipt(output, receipt)
        else:
            artifacts = cast(list[dict[str, object]], receipt["artifacts"])
            row = next(row for row in artifacts if row["role"] == "raw-worker-topology")
            if mutation == "count":
                row["count"] = 2
            else:
                row["bytes"] = cast(int, row["bytes"]) + 1
            _rewrite_receipt_with_retained_artifacts(output, receipt)

    with pytest.raises(profiles.ProfileCoordinatorError):
        profiles.inventory_profile(
            output,
            execution_revision=REVISION,
            run_order=1,
            spec=SMALL_SPEC,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "schema",
        "configured",
        "task-parent",
        "task-lifetime",
        "task-after-worker-elapsed",
        "task-overlap",
        "simultaneous",
        "child-summary",
    ],
)
def test_inventory_reconstructs_topology_observations(tmp_path: Path, mutation: str) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    sidecar = profiles._strict_json(output / "raw-worker-topology.json", "raw worker topology")
    detail = cast(dict[str, object], sidecar["route"])
    tasks = cast(list[dict[str, object]], detail["tasks"])
    children = cast(list[dict[str, object]], detail["children"])
    if mutation == "schema":
        sidecar["schema"] = "fixed-core-packet-calibration-worker-route/v0"
    elif mutation == "configured":
        detail["configured_workers"] = 3
    elif mutation == "task-parent":
        tasks[0]["ppid"] = cast(int, tasks[0]["ppid"]) + 1
    elif mutation == "task-lifetime":
        tasks[0]["finished_seconds"] = tasks[0]["started_seconds"]
    elif mutation == "task-after-worker-elapsed":
        for task in tasks:
            task["started_seconds"] = cast(float, task["started_seconds"]) + 100.0
            task["finished_seconds"] = cast(float, task["finished_seconds"]) + 100.0
        for child in children:
            child["first_task_started_seconds"] = (
                cast(float, child["first_task_started_seconds"]) + 100.0
            )
            child["last_task_finished_seconds"] = (
                cast(float, child["last_task_finished_seconds"]) + 100.0
            )
    elif mutation == "task-overlap":
        tasks[1]["pid"] = tasks[0]["pid"]
    elif mutation == "simultaneous":
        detail["maximum_simultaneous_children"] = 1
    else:
        children[0]["tasks_completed"] = 2
    _republish_topology_sidecar(output, "raw", sidecar)

    with pytest.raises(profiles.ProfileCoordinatorError):
        profiles.inventory_profile(
            output,
            execution_revision=REVISION,
            run_order=1,
            spec=SMALL_SPEC,
        )


def test_inventory_refuses_digest_consistent_reversed_route_chronology(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    profiles.inventory_profile(
        output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
    )
    raw = profiles._strict_json(output / "raw-worker-topology.json", "raw topology")
    exact = profiles._strict_json(
        output / "normalized-exact-worker-topology.json", "exact topology"
    )
    raw_route = cast(dict[str, object], raw["route"])
    exact_route = cast(dict[str, object], exact["route"])
    for key, fields in (
        ("tasks", ("started_seconds", "finished_seconds")),
        (
            "children",
            ("first_task_started_seconds", "last_task_finished_seconds"),
        ),
    ):
        raw_rows = cast(list[dict[str, object]], raw_route[key])
        exact_rows = cast(list[dict[str, object]], exact_route[key])
        for raw_row, exact_row in zip(raw_rows, exact_rows, strict=True):
            for field in fields:
                raw_row[field], exact_row[field] = exact_row[field], raw_row[field]
    _republish_topology_sidecar(output, "raw", raw)
    _republish_topology_sidecar(output, "normalized_exact", exact)

    with pytest.raises(profiles.ProfileCoordinatorError, match="raw tasks finish after"):
        profiles.inventory_profile(
            output, execution_revision=REVISION, run_order=1, spec=SMALL_SPEC
        )


def test_inventory_accepts_coordinator_serial_topology(tmp_path: Path) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    settings = cast(dict[str, object], receipt["settings"])
    settings["requested_workers"] = 1
    effective = cast(dict[str, object], settings["effective_workers"])
    effective["raw"] = 1
    effective["normalized_exact"] = 1
    invocation = cast(dict[str, object], receipt["invocation"])
    identity = cast(dict[str, object], invocation["identity"])
    identity["requested_workers"] = 1
    resources = cast(dict[str, object], receipt["resources"])
    topology = cast(dict[str, object], resources["worker_topology"])
    summaries = cast(dict[str, object], topology["routes"])
    for route, filename in (
        ("raw", "raw-worker-topology.json"),
        ("normalized_exact", "normalized-exact-worker-topology.json"),
    ):
        sidecar = profiles._strict_json(output / filename, filename)
        detail = cast(dict[str, object], sidecar["route"])
        detail.update(
            {
                "execution_model": "coordinator-serial",
                "configured_workers": 1,
                "child_tasks_observed": 0,
                "observed_child_count": 0,
                "maximum_simultaneous_children": 0,
                "tasks": [],
                "children": [],
            }
        )
        _write_json(output / filename, sidecar)
        summaries[route] = {
            "configured_workers": 1,
            "execution_model": "coordinator-serial",
            "observed_child_count": 0,
            "maximum_simultaneous_children": 0,
            "record_path": filename,
            "record_sha256": profiles._sha256((output / filename).read_bytes()),
        }
    _publish_fake_receipt(output, receipt)

    profiles.inventory_profile(
        output,
        execution_revision=REVISION,
        run_order=1,
        spec=SMALL_SPEC,
    )


@pytest.mark.parametrize("mutation", ["route-summary", "supervisor-binding"])
def test_inventory_reconstructs_topology_receipt_bindings(
    tmp_path: Path, mutation: str
) -> None:
    output = tmp_path / "profile"
    _fake_receipt(output, 1)
    receipt = profiles._strict_json(output / "result.json", "receipt")
    if mutation == "route-summary":
        resources = cast(dict[str, object], receipt["resources"])
        topology = cast(dict[str, object], resources["worker_topology"])
        routes = cast(dict[str, object], topology["routes"])
        raw = cast(dict[str, object], routes["raw"])
        raw["observed_child_count"] = 3
    else:
        supervision = cast(dict[str, object], receipt["supervision"])
        supervised_pid = cast(int, supervision["coordinator_pid"]) + 1
        supervision["coordinator_pid"] = supervised_pid
        supervision["coordinator_process_group_id"] = supervised_pid
    _publish_fake_receipt(output, receipt)

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
