"""Known-answer and lifecycle controls for the fixed-core packet calibration."""

# The calibration deliberately reuses private generic row/readback primitives while
# keeping a closed outer state machine. These tests exercise that integration seam.
# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001

from __future__ import annotations

import ast
import hashlib
import json
import sys
import time
from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from devtools import calibrate_fixed_core_packet as calibration
from devtools.dilation_corollary import (
    THRESHOLD_LIMIT_RECORD_SCHEMA,
    build_limit_record,
)
from devtools.fixed_core_packet import (
    PacketError,
    RawMinimum,
    _direction_digest,
    _reconstruct_raw_directions,
    run_exact_route,
    run_interval_route,
    run_raw_sweep,
)
from devtools.fixed_core_packet import load_result as load_scientific_result
from sqpack.fractional.threshold import (
    ThresholdCertificate,
    exact_charge,
    expansion_terms,
)

REPOSITORY = Path(__file__).resolve().parents[2]
FIXTURE = REPOSITORY / calibration.FIXTURE_PATH
REVISION = "a" * 40


def _fixture() -> tuple[ThresholdCertificate, dict[str, object]]:
    return calibration.load_fixture(FIXTURE.read_bytes())


def _normalized(certificate: ThresholdCertificate) -> ThresholdCertificate:
    return replace(
        certificate,
        atoms=tuple(
            replace(atom, weight=atom.weight * calibration.NORMALIZATION_ALPHA)
            for atom in certificate.atoms
        ),
        threshold_atoms=tuple(
            replace(atom, weight=atom.weight * calibration.NORMALIZATION_ALPHA)
            for atom in certificate.threshold_atoms
        ),
    )


def _small(
    certificate: ThresholdCertificate, *, normalized: bool = False
) -> ThresholdCertificate:
    reduced = replace(
        certificate,
        half_tangents=(Fraction(0), calibration.FIXTURE_HALF_GAP),
    )
    return _normalized(reduced) if normalized else reduced


def _seed(output: Path) -> dict[str, object]:
    document = calibration.initial_document(
        REVISION,
        workers=1,
        calibration_seconds=1.0,
        external_seconds=2.0,
        grace_seconds=0.05,
        invocation_started=time.perf_counter(),
        run_order=1,
        cache_observation="test process; cache state unmeasured",
        background_load="test host; background load unmeasured",
    )
    calibration.write_result(output, document)
    return document


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, allow_nan=False) + "\n", encoding="utf-8")


def _run_small_raw(
    tmp_path: Path, certificate: ThresholdCertificate
) -> tuple[Path, RawMinimum]:
    directory = tmp_path / "raw"
    result = run_raw_sweep(
        certificate,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=directory,
    )
    return directory, result


def _dilation_oracle() -> dict[str, object]:
    return {
        "schema": THRESHOLD_LIMIT_RECORD_SCHEMA,
        "source": {
            "certificate": "candidate.json",
            "sha256": "b" * 64,
            "n": 2,
            "total_budget": "1",
            "minimum_cell_charge": "1",
        },
        "sharpened_containment": {
            "strict_factor_test_left_multiplier": str(calibration.EXPECTED_STRICT_LEFT),
            "strict_factor_test_right": str(calibration.EXPECTED_STRICT_RIGHT),
        },
        "strict_dilation_family": {
            "factor_supremum": "2*sqrt(33177601)/5761",
            "factor_supremum_squared": str(calibration.EXPECTED_FACTOR_SQUARED),
        },
        "conclusion": {
            "bounded_side": "3*sqrt(33177601)/11522",
            "bounded_side_squared": str(calibration.EXPECTED_SIDE_SQUARED),
            "relation": ">=",
            "endpoint_certificate": False,
        },
        "proof": {"requires_compactness": False},
    }


def test_frozen_cross_fixture_and_normalization_have_the_reviewed_answers() -> None:
    certificate, source = _fixture()
    normalized, record = calibration.load_normalized(calibration.normalized_bytes(source))

    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == calibration.FIXTURE_SHA256
    assert len(FIXTURE.read_bytes()) == calibration.FIXTURE_BYTES
    assert certificate.total_budget == calibration.RAW_BUDGET == 2
    assert len(certificate.directions) == calibration.RAW_DIRECTIONS == 2_881
    assert calibration._interval_labels()[0::2_880] == ("0", "2880", "2880'")
    assert calibration.TOTAL_DIRECTION_ROWS == 14_404
    assert normalized.total_budget == calibration.NORMALIZED_BUDGET == 1
    assert record["point_mass"] == "1/4"
    assert record["threshold_budget"] == "3/4"
    assert record["least_cell_charge"] == "1"


def test_real_generic_raw_exact_and_reflected_interval_kernels_run_on_reduced_net(
    tmp_path: Path,
) -> None:
    certificate, _source = _fixture()
    raw_directory, raw = _run_small_raw(tmp_path, _small(certificate))
    normalized = _small(certificate, normalized=True)
    exact_directory = tmp_path / "exact"
    interval_directory = tmp_path / "interval"

    exact = run_exact_route(
        normalized,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=exact_directory,
    )
    interval = run_interval_route(
        normalized,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=interval_directory,
    )

    assert raw.minimum == 2
    assert raw.direction == 0
    assert raw.completed == 2
    assert {path.name for path in raw_directory.iterdir()} == {"0.json", "1.json"}
    assert exact.minimum == 1
    assert exact.direction == 0
    assert exact.completed == 2
    assert exact.disagreements == 0
    assert (interval.lower, interval.upper) == (Fraction(1), Fraction(1))
    assert interval.completed == 3
    assert interval.stalled == interval.budget_exhausted == 0
    assert {path.name for path in interval_directory.iterdir()} == {
        "0.json",
        "1.json",
        "1'.json",
    }


def test_strict_raw_comparison_refuses_the_n1_equality_control() -> None:
    assert calibration.raw_decision(Fraction(2), n=1) == "refused"
    assert calibration.raw_decision(Fraction(2), n=2) == "passed"


def test_underweight_control_fails_exact_interval_and_dilation(
    tmp_path: Path,
) -> None:
    certificate, source = _fixture()
    underweight = replace(
        _small(certificate, normalized=True),
        atoms=(replace(certificate.atoms[0], weight=Fraction(1, 8)),),
    )
    exact = run_exact_route(
        underweight,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=tmp_path / "underweight-exact",
    )
    interval = run_interval_route(
        underweight,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=tmp_path / "underweight-interval",
    )
    assert exact.minimum == Fraction(7, 8)
    assert (interval.lower, interval.upper) == (Fraction(7, 8), Fraction(7, 8))
    assert not interval.accepted

    record = calibration._normalized_record(source)
    cast(list[list[str]], record["atoms"])[0][2] = "1/8"
    record.update(
        {
            "point_mass": "1/8",
            "total_budget": "7/8",
            "least_cell_charge": "7/8",
        }
    )
    path = tmp_path / "underweight.json"
    _write_json(path, record)
    with pytest.raises(ValueError, match="not accepted on all five conditions"):
        build_limit_record(path, source_name="underweight.json", workers=1)


def test_threshold_semantics_and_inclusion_exclusion_anchors() -> None:
    certificate, _source = _fixture()
    witness = (Fraction(9, 32), Fraction(9, 32))
    contains = calibration._placement_membership(certificate, 0, witness)
    counts = tuple(atom.trace_count(contains) for atom in certificate.threshold_atoms)
    all_three_charge = sum(
        (
            atom.weight
            for atom, count in zip(certificate.threshold_atoms, counts, strict=True)
            if count > 2
        ),
        start=certificate.atoms[0].weight,
    )

    assert counts == (2, 2)
    assert (
        exact_charge(certificate.atoms, certificate.threshold_atoms, contains)
        == calibration.RAW_MINIMUM
    )
    assert all_three_charge == Fraction(1, 2)
    assert expansion_terms(3, 2) == ((2, 1), (3, -2))
    assert 3 * 1 != 1


def test_larger_domain_control_reaches_zero_at_an_admissible_witness() -> None:
    assert calibration.larger_domain_zero_control() == (Fraction(0), True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update({"id": "other"}),
        lambda row: cast(list[list[str]], row["atoms"])[0].__setitem__(0, "1/4"),
        lambda row: cast(list[list[str]], row["atoms"])[0].__setitem__(2, "1/4"),
        lambda row: cast(list[dict[str, object]], row["threshold_atoms"])[0].update(
            {"threshold": 3}
        ),
        lambda row: cast(list[dict[str, object]], row["threshold_atoms"]).reverse(),
        lambda row: row.update({"provenance": {"kind": "substituted"}}),
    ],
)
def test_fixture_freeze_refuses_identity_geometry_weight_threshold_order_and_source(
    mutation: Callable[[dict[str, object]], object],
) -> None:
    record = cast(dict[str, object], json.loads(FIXTURE.read_bytes()))
    mutation(record)
    raw = (json.dumps(record, indent=1, allow_nan=False) + "\n").encode()
    with pytest.raises(calibration.CalibrationError, match="fixture bytes"):
        calibration.load_fixture(raw)


def test_normalization_refuses_a_substituted_source_identity() -> None:
    _certificate, source = _fixture()
    source["id"] = "substituted"
    with pytest.raises(calibration.CalibrationError, match="frozen calibration fixture"):
        calibration.normalized_bytes(source)


def test_nonargmin_charge_mutation_is_refused_even_when_the_minimum_survives(
    tmp_path: Path,
) -> None:
    certificate, _source = _fixture()
    directory, _result = _run_small_raw(tmp_path, _small(certificate))
    row = cast(dict[str, object], json.loads((directory / "1.json").read_bytes()))
    row["charge"] = "3"
    _write_json(directory / "1.json", row)

    with pytest.raises(calibration.CalibrationError, match="known-answer"):
        calibration._check_raw_rows(directory, _small(certificate), expected=2)


@pytest.mark.parametrize("mutation", ["delete", "add", "mislabel", "numeric-alias"])
def test_row_set_and_label_mutations_are_refused(tmp_path: Path, mutation: str) -> None:
    certificate, _source = _fixture()
    small = _small(certificate)
    directory, _result = _run_small_raw(tmp_path, small)
    if mutation == "delete":
        (directory / "1.json").unlink()
    elif mutation == "add":
        _write_json(directory / "2.json", json.loads((directory / "1.json").read_bytes()))
    elif mutation == "mislabel":
        row = cast(dict[str, object], json.loads((directory / "1.json").read_bytes()))
        row["direction"] = 0
        _write_json(directory / "1.json", row)
    else:
        _write_json(directory / "01.json", json.loads((directory / "1.json").read_bytes()))

    with pytest.raises((calibration.CalibrationError, PacketError)):
        calibration._check_raw_rows(directory, small, expected=2)


def test_witness_byte_binding_and_coherently_inadmissible_witness_are_refused(
    tmp_path: Path,
) -> None:
    certificate, _source = _fixture()
    small = _small(certificate)
    directory, result = _run_small_raw(tmp_path, small)
    paths = tuple(directory / f"{index}.json" for index in range(2))
    receipt: dict[str, object] = {
        "directions_expected": 2,
        "directions_completed": 2,
        "completed_directions": [0, 1],
        "observed_minimum_upper_bound": str(result.minimum),
        "observed_argmin": result.direction,
        "observed_witness": [str(result.witness[0]), str(result.witness[1])],
        "raw_minimum": str(result.minimum),
        "directions_sha256": _direction_digest(paths),
    }
    row = cast(dict[str, object], json.loads(paths[1].read_bytes()))
    row["witness"] = ["0", "0"]
    _write_json(paths[1], row)
    with pytest.raises(PacketError, match="digest"):
        _reconstruct_raw_directions(directory, receipt, expected=2, complete=True)

    receipt["directions_sha256"] = _direction_digest(paths)
    _reconstruct_raw_directions(directory, receipt, expected=2, complete=True)
    with pytest.raises(calibration.CalibrationError, match="known-answer"):
        calibration._check_raw_rows(directory, small, expected=2)


def test_interval_scale_is_semantic_while_box_count_is_observational(
    tmp_path: Path,
) -> None:
    certificate, _source = _fixture()
    normalized = _small(certificate, normalized=True)
    directory = tmp_path / "interval"
    run_interval_route(
        normalized,
        workers=1,
        deadline=10.0,
        clock=lambda: 0.0,
        progress=lambda *_args: None,
        log=directory,
    )
    labels = ("0", "1", "1'")
    row = cast(dict[str, object], json.loads((directory / "1.json").read_bytes()))
    row["boxes"] = cast(int, row["boxes"]) + 17
    _write_json(directory / "1.json", row)
    readback, boxes = calibration._check_interval_rows(directory, normalized, labels=labels)
    assert readback.enclosure == (Fraction(1), Fraction(1))
    assert boxes > 17

    row["lower"] = row["upper"] = 1
    _write_json(directory / "1.json", row)
    with pytest.raises(calibration.CalibrationError, match="known-answer"):
        calibration._check_interval_rows(directory, normalized, labels=labels)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("strict_dilation_family", "factor_supremum_squared"), "4"),
        (("conclusion", "bounded_side_squared"), "3"),
        (("conclusion", "endpoint_certificate"), True),
        (("proof", "requires_compactness"), True),
    ],
)
def test_dilation_surd_endpoint_and_compactness_mutations_are_refused(
    path: tuple[str, str], value: object
) -> None:
    certificate, _source = _fixture()
    normalized = _normalized(certificate)
    record = _dilation_oracle()
    calibration._check_dilation_record(record, normalized, "b" * 64)
    cast(dict[str, object], record[path[0]])[path[1]] = value
    with pytest.raises(calibration.CalibrationError, match="dilation record"):
        calibration._check_dilation_record(record, normalized, "b" * 64)


def test_calibration_wrapper_is_closed_and_cross_schema_readers_refuse(
    tmp_path: Path,
) -> None:
    output = tmp_path / "receipt"
    output.mkdir()
    document = _seed(output)
    calibration.validate_document(document)

    scientific = deepcopy(document)
    scientific["schema"] = "fixed-core-packet-result/v1"
    with pytest.raises(calibration.CalibrationError, match="calibration/v1"):
        calibration.validate_document(scientific)

    extra = deepcopy(document)
    extra["scientific_decision"] = "accepted"
    with pytest.raises(calibration.CalibrationError, match="calibration/v1"):
        calibration.validate_document(extra)

    forbidden = deepcopy(document)
    cast(dict[str, object], forbidden["sources"])["packet"] = "packet-accepted"
    with pytest.raises(calibration.CalibrationError, match="forbidden"):
        calibration.validate_document(forbidden)

    with pytest.raises(PacketError, match="schema"):
        load_scientific_result(
            output,
            repository=REPOSITORY,
            expected_revision=REVISION,
            require_supervision=False,
        )


def test_partial_route_receipts_bind_the_exact_published_direction_set() -> None:
    document = calibration.initial_document(
        REVISION,
        workers=1,
        calibration_seconds=1.0,
        external_seconds=2.0,
        grace_seconds=0.05,
        invocation_started=0.0,
        run_order=1,
        cache_observation="unmeasured",
        background_load="unmeasured",
    )
    routes = cast(dict[str, object], document["routes"])
    routes["reflected_interval"] = {
        "status": "partial",
        "source_sha256": "b" * 64,
        "directions_expected": calibration.INTERVAL_DIRECTIONS,
        "directions_completed": 2,
        "completed_directions": ["0", "2'"],
        "last": {"label": "2'"},
    }
    calibration.validate_document(document)
    cast(dict[str, object], routes["reflected_interval"])["completed_directions"] = ["0"]
    with pytest.raises(calibration.CalibrationError, match="progress"):
        calibration.validate_document(document)


def test_receipt_parser_refuses_duplicate_keys(tmp_path: Path) -> None:
    output = tmp_path / "duplicate"
    output.mkdir()
    (output / "result.json").write_text(
        '{"schema":"fixed-core-packet-calibration/v1","schema":"forged"}\n',
        encoding="utf-8",
    )
    with pytest.raises(PacketError, match="duplicate"):
        calibration.load_result(
            output,
            repository=REPOSITORY,
            expected_revision=REVISION,
        )


def test_source_closure_calls_real_generic_kernels_without_target_entry_points() -> None:
    source = (REPOSITORY / "packing/devtools/calibrate_fixed_core_packet.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    defaults = calibration.RouteKernels()
    paths = calibration.discover_implementation_paths(REPOSITORY)

    assert defaults.raw is run_raw_sweep
    assert defaults.exact is run_exact_route
    assert defaults.interval is run_interval_route
    assert defaults.dilation is calibration.run_dilation_replay
    assert (
        not {
            "execute_packet",
            "normalized_record",
            "load_packet_source",
        }
        & calls
    )
    assert calibration.FIXTURE_PATH in paths
    assert "packing/devtools/calibrate_fixed_core_packet.py" in paths


def test_output_must_be_fresh_and_outside_the_repository(tmp_path: Path) -> None:
    with pytest.raises(calibration.CalibrationError, match="outside"):
        calibration.prepare_output_dir(REPOSITORY / "packing/calibration-result", REPOSITORY)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(calibration.CalibrationError, match="fresh"):
        calibration.prepare_output_dir(existing, REPOSITORY)


def test_rss_summary_is_byte_bound_but_not_a_semantic_answer(tmp_path: Path) -> None:
    samples: list[dict[str, object]] = [
        {
            "elapsed_seconds": 0.1,
            "phase": "raw-sweep",
            "pids": [101, 102],
            "rss_bytes": 4_096,
            "error": None,
        },
        {
            "elapsed_seconds": 0.25,
            "phase": "normalized-exact",
            "pids": [101],
            "rss_bytes": 2_048,
            "error": None,
        },
    ]
    summary = calibration._write_rss_samples(tmp_path, samples)
    resources = {
        "cpu_scope": calibration.CPU_SCOPE,
        "coordinator_process_seconds": None,
        "reaped_direct_children_user_seconds": None,
        "reaped_direct_children_system_seconds": None,
        "rss": summary,
    }
    calibration._validate_rss_observations(tmp_path, resources, required=True)
    record = cast(
        dict[str, object],
        json.loads((tmp_path / "rss-samples.json").read_bytes()),
    )
    cast(list[dict[str, object]], record["samples"])[0]["rss_bytes"] = 1
    _write_json(tmp_path / "rss-samples.json", record)
    with pytest.raises(calibration.CalibrationError, match="byte binding"):
        calibration._validate_rss_observations(tmp_path, resources, required=True)


def test_launch_oserror_is_an_operational_unresolved_receipt(
    tmp_path: Path,
) -> None:
    output = tmp_path / "launch"
    output.mkdir()
    _seed(output)
    with patch(
        "devtools.calibrate_fixed_core_packet.subprocess.Popen",
        side_effect=OSError("temporary launch failure"),
    ):
        status = calibration.supervise_worker(
            (sys.executable, "-c", "raise SystemExit"),
            output,
            repository=REPOSITORY,
            expected_revision=REVISION,
            external_seconds=2.0,
            grace_seconds=0.05,
            invocation_started=time.perf_counter(),
            external_deadline=time.perf_counter() + 1.0,
        )
    receipt = json.loads((output / "result.json").read_bytes())
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "operational-failure"
    assert receipt["supervision"]["status"] == "launch-failed"


def test_supervisor_recomputes_deadline_after_process_launch(tmp_path: Path) -> None:
    output = tmp_path / "launch-boundary"
    output.mkdir()
    _seed(output)

    class Process:
        pid = 123

        @staticmethod
        def poll() -> None:
            return None

    times = iter((0.0, 0.1, 0.9, 0.91, 1.01, 1.02, 1.025, 1.03))
    with (
        patch(
            "devtools.calibrate_fixed_core_packet.time.perf_counter",
            side_effect=lambda: next(times),
        ),
        patch(
            "devtools.calibrate_fixed_core_packet.subprocess.Popen",
            return_value=Process(),
        ),
        patch(
            "devtools.calibrate_fixed_core_packet._sample_process_group",
            return_value={
                "elapsed_seconds": 0.91,
                "phase": "preflight",
                "pids": [123],
                "rss_bytes": 1,
                "error": None,
            },
        ),
        patch(
            "devtools.calibrate_fixed_core_packet._reap_process_group",
            return_value=(-9, 0.01),
        ),
        patch(
            "devtools.calibrate_fixed_core_packet._record_supervision",
            return_value={},
        ) as record,
    ):
        status = calibration.supervise_worker(
            ("worker",),
            output,
            repository=REPOSITORY,
            expected_revision=REVISION,
            external_seconds=1.0,
            grace_seconds=0.05,
            invocation_started=0.0,
            external_deadline=1.0,
        )

    assert status == 1
    assert record.call_args.kwargs["status"] == "deadline-terminated"
    assert record.call_args.kwargs["launch_seconds"] == pytest.approx(0.8)


@pytest.mark.parametrize(
    "phase",
    [
        "raw-sweep",
        "normalized-exact",
        "reflected-interval",
        "dilation-replay",
        "readback",
    ],
)
def test_each_execution_checkpoint_remains_partial_when_terminated(
    tmp_path: Path, phase: str
) -> None:
    output = tmp_path / phase
    output.mkdir()
    document = _seed(output)
    document["phase"] = phase
    document["error"] = f"{phase} is incomplete"
    calibration.write_result(output, document)
    started = time.perf_counter()
    status = calibration.supervise_worker(
        (sys.executable, "-c", "import time; time.sleep(60)"),
        output,
        repository=REPOSITORY,
        expected_revision=REVISION,
        external_seconds=0.08,
        grace_seconds=0.03,
        invocation_started=started,
        external_deadline=started + 0.08,
    )
    receipt = json.loads((output / "result.json").read_bytes())
    rss = cast(dict[str, object], cast(dict[str, object], receipt["resources"])["rss"])
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "timeout"
    assert phase in cast(dict[str, object], rss["pids_by_phase"])


def test_timeout_kills_and_reaps_a_termination_resistant_process_group(
    tmp_path: Path,
) -> None:
    output = tmp_path / "timeout"
    output.mkdir()
    _seed(output)
    grandchild = (
        "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)"
    )
    leader = (
        "import signal,subprocess,sys,time;"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
        f"subprocess.Popen([sys.executable,'-c',{grandchild!r}]);"
        "time.sleep(60)"
    )
    started = time.perf_counter()
    status = calibration.supervise_worker(
        (sys.executable, "-c", leader),
        output,
        repository=REPOSITORY,
        expected_revision=REVISION,
        external_seconds=0.2,
        grace_seconds=0.05,
        invocation_started=started,
        external_deadline=started + 0.2,
    )
    receipt = json.loads((output / "result.json").read_bytes())
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "timeout"
    assert receipt["supervision"] == {
        "status": "deadline-terminated",
        "worker_exit_status": -9,
        "process_group_reaped": True,
    }


def test_nonzero_exit_revokes_a_stale_complete_candidate_phase(
    tmp_path: Path,
) -> None:
    output = tmp_path / "nonzero"
    output.mkdir()
    document = _seed(output)
    document["phase"] = "awaiting-worker-exit"
    document["error"] = "parent has not observed worker exit"
    calibration.write_result(output, document)
    started = time.perf_counter()
    status = calibration.supervise_worker(
        (sys.executable, "-c", "raise SystemExit(7)"),
        output,
        repository=REPOSITORY,
        expected_revision=REVISION,
        external_seconds=2.0,
        grace_seconds=0.05,
        invocation_started=started,
        external_deadline=started + 2.0,
    )
    receipt = json.loads((output / "result.json").read_bytes())
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "operational-failure"
    assert receipt["supervision"]["worker_exit_status"] == 7


def test_parent_readback_that_finishes_after_deadline_revokes_admission(
    tmp_path: Path,
) -> None:
    output = tmp_path / "late-readback"
    output.mkdir()
    document = _seed(output)
    document["phase"] = "awaiting-worker-exit"
    document["error"] = "parent has not observed worker exit"
    calibration.write_result(output, document)
    started = time.perf_counter()

    def late_readback(*_args: object, **_kwargs: object) -> dict[str, object]:
        time.sleep(0.12)
        return document

    with patch(
        "devtools.calibrate_fixed_core_packet.load_result",
        side_effect=late_readback,
    ):
        status = calibration.supervise_worker(
            (sys.executable, "-c", "import time; time.sleep(0.02)"),
            output,
            repository=REPOSITORY,
            expected_revision=REVISION,
            external_seconds=0.15,
            grace_seconds=0.05,
            invocation_started=started,
            external_deadline=started + 0.15,
        )
    receipt = json.loads((output / "result.json").read_bytes())
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "timeout"
    assert "parent final readback" in receipt["error"]


def test_worker_git_oserror_remains_operationally_unresolved(
    tmp_path: Path,
) -> None:
    output = tmp_path / "worker-oserror"
    output.mkdir()
    _seed(output)
    started = time.perf_counter()
    with patch(
        "devtools.calibrate_fixed_core_packet.source_manifest",
        side_effect=OSError("transient Git failure"),
    ):
        status = calibration.run_worker(
            REPOSITORY,
            REVISION,
            output,
            workers=1,
            calibration_seconds=1.0,
            external_seconds=2.0,
            grace_seconds=0.05,
            invocation_started=started,
            calibration_deadline=started + 1.0,
            external_deadline=started + 2.0,
        )
    receipt = json.loads((output / "result.json").read_bytes())
    assert status == 1
    assert receipt["status"] == "partial"
    assert receipt["phase"] == "operational-failure"
    assert "transient Git failure" in receipt["error"]
