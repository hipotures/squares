"""Admission controls for the target-blind Route S compression surface."""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest

from devtools import admit_threshold_compression as admission
from sqpack.cli import validate


def _record() -> dict[str, object]:
    return json.loads(admission.ADMISSION.read_text(encoding="utf-8"))


def _write(path: Path, record: object) -> Path:
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def test_retained_admission_replays_without_running_a_target() -> None:
    receipt = admission.build_receipt()

    assert receipt["status"] == "admitted"
    assert receipt["admission_blockers"] == []
    assert receipt["control"]["orbits"] == 119
    assert receipt["control"]["atoms"] == 904
    assert receipt["control"]["decompressor_roundtrip"] == {
        "role": "full authenticated T-025 manifest and decompressor control",
        "canonical_equivalent": True,
        "manifest_schema": "packing.squares:ThresholdOrbitSelection/v1",
        "manifest_sha256": "53fbe28bd6dd022600515663ea1e3609ed2bd36a83e69e350b4bb3b45d7b7176",
        "manifest_bytes": 100_270,
        "manifest_roundtrip": True,
        "certificate_loader_roundtrip": True,
        "catalog_sha256": receipt["control"]["catalog_sha256"],
        "orbits": 119,
        "atoms": 904,
        "total_budget": "685457679/62500000",
    }
    assert [sentinel["direction_steps"] for sentinel in receipt["sentinels"]] == [720, 1440]
    assert all(sentinel["reproduced"] for sentinel in receipt["sentinels"])
    assert all(
        sentinel["common_weight_scale"] == "500000000/498684619"
        for sentinel in receipt["sentinels"]
    )
    assert receipt["quantization_control"] == {
        "denominator": 30_000,
        "rounded_budget": "82373/7500",
        "budget_below_n": True,
        "support_changed": False,
        "research_success": False,
    }
    assert receipt["synthetic_decompressor"]["selected_orbits"] == 23
    assert receipt["synthetic_decompressor"]["compression_factor"] == "119/23"
    assert receipt["synthetic_decompressor"]["satisfies_policy"] is True
    assert receipt["synthetic_decompressor"]["manifest_roundtrip"] is True
    assert receipt["synthetic_decompressor"]["certificate_loader_roundtrip"] is True
    assert receipt["policy_boundary"] == {
        "accepted_orbits": 23,
        "rejected_orbits": 24,
        "rejected_manifest_sha256": (
            "194f1f9f47fc94e7f945920c38a4efdb43476719eba025ea446a1d7b91fde27e"
        ),
        "rejected_before_decompression": True,
        "coverage_ran": False,
    }
    assert receipt["mutation_controls"] == {
        "duplicate": True,
        "missing": True,
        "negative": True,
        "non_d4": True,
        "nonrational": True,
        "off_support": True,
        "wrong_threshold": True,
        "wrong_type": True,
    }
    for field in (
        "target_ran",
        "optimizer_ran",
        "coverage_ran",
        "candidate_created",
        "experiment_created",
    ):
        assert receipt[field] is False


def test_output_is_byte_identical_to_the_retained_receipt(tmp_path: Path) -> None:
    output = tmp_path / "receipt.json"

    assert admission.main(["--output", str(output)]) == 0
    assert output.read_bytes() == admission.RECEIPT.read_bytes()
    assert admission.main(["--check"]) == 0


@pytest.mark.parametrize(
    ("keys", "value"),
    [
        (("source_revision",), "0" * 40),
        (("control", "path"), "../certificate.json"),
        (("control", "catalog_sha256"), "a" * 64),
        (("sentinels", 0, "path"), "/tmp/corollary.json"),
        (("sentinels", 0, "direction_steps"), 1440),
        (("sentinels", 0, "source_path"), "/tmp/certificate.json"),
        (("family", "max_orbits"), 24),
        (("execution_boundary", "target_ran"), True),
        (("quantization_control", "denominator"), 29_999),
    ],
)
def test_contract_mutations_are_refused(
    tmp_path: Path, keys: tuple[str | int, ...], value: object
) -> None:
    record = _record()
    nested: object = record
    for key in keys[:-1]:
        if isinstance(key, int):
            assert isinstance(nested, list)
            nested = cast(list[object], nested)[key]
        else:
            assert isinstance(nested, dict)
            nested = nested[key]
    final = keys[-1]
    assert isinstance(final, str)
    assert isinstance(nested, dict)
    nested[final] = value

    with pytest.raises(admission.AdmissionError):
        admission.build_receipt(_write(tmp_path / "mutated.json", record))


def test_sentinel_order_is_frozen(tmp_path: Path) -> None:
    record = _record()
    sentinels = record["sentinels"]
    assert isinstance(sentinels, list)
    sentinels.reverse()

    with pytest.raises(admission.AdmissionError, match="order"):
        admission.build_receipt(_write(tmp_path / "swapped.json", record))

    sentinels.pop()
    with pytest.raises(admission.AdmissionError, match="ordered"):
        admission.build_receipt(_write(tmp_path / "missing.json", record))


def test_bound_input_path_cannot_resolve_through_a_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.json"
    target.write_text("{}\n", encoding="utf-8")
    alias = tmp_path / "alias.json"
    alias.symlink_to(target)
    monkeypatch.setattr(admission, "REPOSITORY", tmp_path)

    with pytest.raises(admission.AdmissionError, match="resolves through a symlink"):
        admission._repo_path(  # noqa: SLF001
            "alias.json", expected="alias.json", label="bound input"
        )


def test_all_repository_sources_match_the_declared_git_revision() -> None:
    paths = [
        admission.SOURCE_PATH,
        *(anchor.path for anchor in admission.SENTINELS),
        *(anchor.source_path for anchor in admission.SENTINELS),
    ]

    for relative in paths:
        admission._bind_repository_source(  # noqa: SLF001
            admission.REPOSITORY / relative,
            admission.SOURCE_REVISION,
            label=relative,
        )


def test_missing_historical_git_path_is_refused() -> None:
    with pytest.raises(admission.AdmissionError, match="cannot read missing source"):
        admission._git_content(  # noqa: SLF001
            admission.SOURCE_REVISION,
            "packing/cases/n11_threshold_certificate/does-not-exist.json",
            label="missing source",
        )


def test_current_source_drift_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"reviewed\nchanged\n")
    monkeypatch.setattr(admission, "REPOSITORY", tmp_path)
    monkeypatch.setattr(
        admission,
        "_git_content",
        lambda _revision, _path, *, label: b"reviewed\n" if label else b"",
    )

    with pytest.raises(admission.AdmissionError, match="declared Git revision"):
        admission._bind_repository_source(  # noqa: SLF001
            source, admission.SOURCE_REVISION, label="changed source"
        )


def test_historical_source_mismatch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.json"
    source.write_bytes(b"current\n")
    monkeypatch.setattr(admission, "REPOSITORY", tmp_path)
    monkeypatch.setattr(
        admission,
        "_git_content",
        lambda _revision, _path, *, label: b"other historical content\n" if label else b"",
    )

    with pytest.raises(admission.AdmissionError, match="declared Git revision"):
        admission._bind_repository_source(  # noqa: SLF001
            source, admission.SOURCE_REVISION, label="mismatched source"
        )


def test_duplicate_keys_and_floating_numbers_are_refused(tmp_path: Path) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"schema":"one","schema":"two"}\n', encoding="utf-8")
    floating = tmp_path / "floating.json"
    floating.write_text('{"max_orbits":23.0}\n', encoding="utf-8")

    with pytest.raises(admission.AdmissionError, match="duplicate"):
        admission.load_json(duplicate, label="control")
    with pytest.raises(admission.AdmissionError, match="floating"):
        admission.load_json(floating, label="control")


def test_byte_and_depth_limits_are_enforced_before_contract_parsing(tmp_path: Path) -> None:
    too_large = tmp_path / "large.json"
    too_large.write_text('{"x":"' + "x" * 64 + '"}\n', encoding="utf-8")
    too_deep = tmp_path / "deep.json"
    too_deep.write_text("[" * 17 + "0" + "]" * 17, encoding="utf-8")

    with pytest.raises(admission.AdmissionError, match="byte"):
        admission.load_json(too_large, label="control", limit=32)
    with pytest.raises(admission.AdmissionError, match="depth"):
        admission.load_json(too_deep, label="control")


@pytest.mark.parametrize(
    "path",
    [
        admission.ADMISSION,
        admission.REPOSITORY / admission.SOURCE_PATH,
        *(admission.REPOSITORY / anchor.path for anchor in admission.SENTINELS),
        *(admission.REPOSITORY / anchor.source_path for anchor in admission.SENTINELS),
    ],
)
def test_output_cannot_overwrite_a_bound_input(path: Path) -> None:
    assert admission.main(["--output", str(path)]) == 2


def test_validation_step_runs_the_retained_check(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: tuple[str, ...] | None = None

    def capture(_context: validate.Context, module: str, *arguments: str) -> str:
        nonlocal observed
        observed = (module, *arguments)
        return "Route S compression checkpoint check passed"

    monkeypatch.setattr(validate, "_module", capture)
    context = validate.Context(
        deep=False,
        strict=False,
        jobs=1,
        inner_jobs=1,
        environment={},
    )

    assert "check passed" in validate._threshold_compression_admission(context)  # noqa: SLF001
    assert observed == ("devtools.admit_threshold_compression", "--check")
    step = next(
        step
        for step in validate.STEPS
        if step.name == "Route S compression admission checkpoint is consistent"
    )
    assert step.fast
    assert step.records
    assert not step.broad
    assert {
        "packing/cases/n11_threshold_certificate/certificate-191-50-net720.json",
        "packing/cases/n11_threshold_certificate/t-026-net720-dilation-limit-corollary.json",
        "packing/cases/n11_threshold_certificate/certificate-191-50-net1440.json",
        "packing/cases/n11_threshold_certificate/t-026-dilation-limit-corollary.json",
    }.issubset(step.touches)
