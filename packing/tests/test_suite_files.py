"""The quick lane's shard partition and its per-file cost report (`devtools.suite_files`)."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from devtools import suite_files
from devtools.suite_files import RecordedCosts, Shard, SuiteFilesError
from sqpack.cli import validate

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO = PROJECT_ROOT.parent
TEST_ROOTS = (PROJECT_ROOT / "tests", REPO / "packages/workbench/tests")


def _test_files() -> set[str]:
    """Every file in either behavioural root, repository-relative."""
    return {
        suite_files.repository_path(path)
        for root in TEST_ROOTS
        for path in root.rglob("test_*.py")
        if "__pycache__" not in path.parts
    }


def test_the_suite_shards_partition_every_test_file() -> None:
    """Each test file on disk is in exactly one shard, and every shard has files.

    This is the property that lets two runners divide the lane without a test running
    twice or not at all. It holds by construction -- a file's shard is a function of its
    path -- so what this checks is the construction against the real tree and the real
    record: that the recorded count is the one the CLI and the register use, and that
    the files each shard would collect are disjoint and add up to the whole lane.
    """
    costs = suite_files.load_costs()
    assert costs.shards == validate.SUITE_SHARDS
    packed = suite_files.pack(costs)
    files = _test_files()
    assert any(name.startswith("packages/workbench/tests/") for name in files)
    shards = [
        {name for name in files if suite_files.shard_of(name, costs, packed) == index}
        for index in range(1, costs.shards + 1)
    ]
    assert set().union(*shards) == files
    assert sum(len(shard) for shard in shards) == len(files)
    assert all(shards)


def test_the_record_names_only_files_under_the_behavioural_roots() -> None:
    """A recorded path outside both roots matches no collected file and still takes weight.

    Schema-v1 reports derived the file from a nodeid relative to `packing/`, so the
    workbench tests were recorded as `packing/test_*.py`: sixteen entries and 15.05
    recorded seconds that the packing balanced while the real files fell back to their
    path hash. A rename or a deletion may still leave a stale row, which the design
    tolerates; a row under no behavioural root is a mislabelled report.
    """
    roots = tuple(f"{suite_files.repository_path(root)}/" for root in TEST_ROOTS)
    costs = suite_files.load_costs()
    assert sorted(name for name in costs.seconds if not name.startswith(roots)) == []


def test_the_packing_depends_only_on_the_record() -> None:
    """The same record in any order packs the same way, and a new file moves nothing."""
    costs = suite_files.load_costs()
    items = list(costs.seconds.items())
    random.Random(20260915).shuffle(items)
    shuffled = RecordedCosts(shards=costs.shards, seconds=dict(items))
    assert suite_files.pack(shuffled) == suite_files.pack(costs)

    packed = suite_files.pack(costs)
    arrival = "packing/tests/test_a_file_nobody_has_recorded_yet.py"
    assert arrival not in costs.seconds
    shard = suite_files.shard_of(arrival, costs, packed)
    assert shard == suite_files.unrecorded_shard(arrival, costs.shards)
    assert 1 <= shard <= costs.shards
    # Nothing recorded changes shard because a file arrived.
    assert {name: suite_files.shard_of(name, costs, packed) for name in costs.seconds} == packed


def test_the_greedy_packing_balances_within_its_largest_file() -> None:
    costs = RecordedCosts(
        shards=2, seconds={"a.py": 9.0, "b.py": 5.0, "c.py": 4.0, "d.py": 3.0, "e.py": 1.0}
    )
    assert suite_files.pack(costs) == {"a.py": 1, "b.py": 2, "c.py": 2, "d.py": 1, "e.py": 2}
    totals = suite_files.shard_totals(costs)
    assert totals == [12.0, 10.0]
    assert max(totals) - min(totals) <= max(costs.seconds.values())


@pytest.mark.parametrize("text", ["2", "0/2", "3/2", "a/b", "1/"])
def test_a_shard_is_written_k_of_n(text: str) -> None:
    with pytest.raises(SuiteFilesError):
        _ = Shard.parse(text)
    assert str(Shard.parse("2/2")) == "2/2"


def test_record_takes_each_files_geometric_mean_and_names_its_sources() -> None:
    reports = [
        suite_files.report_document(
            {"packing/tests/test_a.py": (3, 2.0), "packing/tests/test_b.py": (1, 0.0)},
            shard=None,
            environment={"GITHUB_RUN_ID": "1", "GITHUB_JOB": "suite-1-of-2"},
            exit_status=0,
        ),
        suite_files.report_document(
            {"packing/tests/test_a.py": (3, 8.0), "packing/tests/test_b.py": (1, 0.0)},
            shard=None,
            environment={},
            exit_status=0,
        ),
    ]
    document = suite_files.record(reports, shards=2)
    assert document["files"] == {
        "packing/tests/test_a.py": 4.0,
        "packing/tests/test_b.py": 0.0,
    }
    assert document["recorded_from"] == [
        "the whole lane: GITHUB_JOB=suite-1-of-2, GITHUB_RUN_ID=1",
        "the whole lane: no CI provenance",
    ]
    assert reports[0]["tests"] == 4
    assert reports[0]["seconds"] == 2.0


def _shard_report(
    index: int,
    *,
    run: str = "1",
    attempt: str = "1",
    sha: str = "abc",
    seconds: float | None = None,
    exit_status: int = 0,
    file: str | None = None,
    count: int = 2,
) -> dict[str, object]:
    return suite_files.report_document(
        {
            file or f"packing/tests/test_{index}.py": (
                1,
                float(index) if seconds is None else seconds,
            )
        },
        shard=Shard(index, count),
        environment={
            "GITHUB_RUN_ID": run,
            "GITHUB_RUN_ATTEMPT": attempt,
            "GITHUB_JOB": f"suite-{index}",
            "GITHUB_SHA": sha,
        },
        exit_status=exit_status,
    )


def test_record_requires_one_complete_coherent_shard_cohort() -> None:
    complete = [_shard_report(1), _shard_report(2)]
    assert suite_files.record(complete, shards=2)["files"] == {
        "packing/tests/test_1.py": 1.0,
        "packing/tests/test_2.py": 2.0,
    }
    with pytest.raises(SuiteFilesError, match="each shard exactly once"):
        suite_files.record(complete[:1], shards=2)
    with pytest.raises(SuiteFilesError, match="each shard exactly once"):
        suite_files.record([complete[0], complete[0]], shards=2)
    with pytest.raises(SuiteFilesError, match="each sharded cohort"):
        suite_files.record([complete[0], _shard_report(2, run="2")], shards=2)
    with pytest.raises(SuiteFilesError, match="each sharded cohort"):
        suite_files.record([complete[0], _shard_report(2, attempt="2")], shards=2)
    with pytest.raises(SuiteFilesError, match="each sharded cohort"):
        suite_files.record([complete[0], _shard_report(2, sha="def")], shards=2)


def test_record_refuses_reports_cut_for_another_shard_count() -> None:
    """Shards `1/2` and `2/3` would otherwise pass as one complete cohort of two."""
    complete = [_shard_report(1), _shard_report(2)]
    with pytest.raises(SuiteFilesError, match=r"shard count\(s\) \[2\], not the requested 3"):
        suite_files.record(complete, shards=3)
    mixed = [_shard_report(1), _shard_report(2, count=3)]
    with pytest.raises(
        SuiteFilesError, match=r"shard count\(s\) \[2, 3\], not the requested 2"
    ):
        suite_files.record(mixed, shards=2)


def test_record_combines_complete_sharded_cohorts() -> None:
    reports = [
        _shard_report(1, run="1", seconds=2.0),
        _shard_report(2, run="1", seconds=8.0),
        _shard_report(1, run="2", seconds=8.0),
        _shard_report(2, run="2", seconds=2.0),
    ]
    document = suite_files.record(reports, shards=2)
    assert document["files"] == {
        "packing/tests/test_1.py": 4.0,
        "packing/tests/test_2.py": 4.0,
    }
    assert len(document["recorded_from"]) == 4


def test_record_refuses_an_incomplete_second_sharded_cohort() -> None:
    reports = [_shard_report(1), _shard_report(2), _shard_report(1, run="2", sha="def")]
    with pytest.raises(SuiteFilesError, match="each sharded cohort"):
        suite_files.record(reports, shards=2)


def test_record_refuses_complete_cohorts_from_different_source_revisions() -> None:
    reports = [
        _shard_report(1, run="1", sha="abc"),
        _shard_report(2, run="1", sha="abc"),
        _shard_report(1, run="2", sha="def"),
        _shard_report(2, run="2", sha="def"),
    ]
    with pytest.raises(SuiteFilesError, match="one GITHUB_SHA"):
        suite_files.record(reports, shards=2)


def test_record_refuses_unsuccessful_or_legacy_reports() -> None:
    unsuccessful = _shard_report(1, exit_status=int(pytest.ExitCode.TESTS_FAILED))
    with pytest.raises(SuiteFilesError, match="not successful"):
        suite_files.record([unsuccessful, _shard_report(2)], shards=2)

    legacy = _shard_report(1)
    del legacy["exit_status"]
    with pytest.raises(SuiteFilesError, match="exit_status"):
        suite_files.record([legacy, _shard_report(2)], shards=2)


def test_record_refuses_malformed_file_rows_and_totals() -> None:
    duplicate = _shard_report(1)
    duplicate["files"] = [*duplicate["files"], *duplicate["files"]]  # type: ignore[index]
    duplicate["tests"] = 2
    duplicate["seconds"] = 2.0
    with pytest.raises(SuiteFilesError, match="duplicate file"):
        suite_files.record([duplicate, _shard_report(2)], shards=2)

    invalid_seconds = _shard_report(1)
    invalid_seconds["files"][0]["seconds"] = -1.0  # type: ignore[index]
    with pytest.raises(SuiteFilesError, match="not finite seconds"):
        suite_files.record([invalid_seconds, _shard_report(2)], shards=2)

    wrong_total = _shard_report(1)
    wrong_total["tests"] = 2
    with pytest.raises(SuiteFilesError, match="rows total"):
        suite_files.record([wrong_total, _shard_report(2)], shards=2)


def test_record_refuses_overlapping_shards_and_inconsistent_cohort_coverage() -> None:
    overlap = [
        _shard_report(1, file="packing/tests/test_shared.py"),
        _shard_report(2, file="packing/tests/test_shared.py"),
    ]
    with pytest.raises(SuiteFilesError, match="more than one shard"):
        suite_files.record(overlap, shards=2)

    inconsistent = [
        _shard_report(1),
        _shard_report(2),
        _shard_report(1, run="2"),
        _shard_report(2, run="2", file="packing/tests/test_3.py"),
    ]
    with pytest.raises(SuiteFilesError, match="same file coverage"):
        suite_files.record(inconsistent, shards=2)


def test_record_refuses_mixed_whole_lane_and_sharded_reports() -> None:
    whole = suite_files.report_document(
        {"packing/tests/test_whole.py": (1, 1.0)},
        shard=None,
        environment={},
        exit_status=0,
    )
    with pytest.raises(SuiteFilesError, match="cannot mix"):
        suite_files.record([whole, _shard_report(1)], shards=2)


_PROBE_FILES = {
    "test_alpha.py": "def test_one():\n    pass\n\ndef test_two():\n    pass\n",
    "test_beta.py": "def test_one():\n    pass\n",
    "test_gamma.py": "import time\n\ndef test_sleeps():\n    time.sleep(0.05)\n",
    "test_delta.py": "def test_one():\n    pass\n",
    "sub/test_epsilon.py": "def test_one():\n    pass\n",
}


def _probe(
    tmp_path: Path,
    *arguments: str,
    rootdir: Path | None = None,
    test_root: Path | None = None,
) -> subprocess.Popen[str]:
    """Start one pytest run under the plugin; the three runs below overlap to stay cheap."""
    rootdir = tmp_path if rootdir is None else rootdir
    test_root = tmp_path / "suite" if test_root is None else test_root
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "devtools.suite_files",
            "--rootdir",
            str(rootdir),
            "-c",
            os.devnull,
            str(test_root),
            *arguments,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )


def _finish(process: subprocess.Popen[str]) -> tuple[int, str]:
    output, _ = process.communicate(timeout=60)
    return process.returncode, output


def test_the_plugin_collects_each_file_in_exactly_one_shard_and_reports_its_cost(
    tmp_path: Path,
) -> None:
    """End to end through pytest: collection filtered per shard, and the report written.

    Two of the five files are recorded, so the run exercises both rules at once: the
    packing for recorded files and the path hash for the rest.
    """
    suite = tmp_path / "suite"
    for name, body in _PROBE_FILES.items():
        (suite / name).parent.mkdir(parents=True, exist_ok=True)
        (suite / name).write_text(body, encoding="utf-8")
    record = tmp_path / "costs.json"
    alpha = suite_files.repository_path(suite / "test_alpha.py")
    gamma = suite_files.repository_path(suite / "test_gamma.py")
    record.write_text(
        json.dumps(
            {
                "schema": suite_files.COSTS_SCHEMA,
                "shards": 2,
                "files": {alpha: 10.0, gamma: 9.0},
            }
        ),
        encoding="utf-8",
    )
    reports = [tmp_path / f"report-{index}.json" for index in (1, 2)]
    runs = [
        _probe(
            tmp_path,
            f"--suite-shard={index}/2",
            f"--suite-file-costs={record}",
            f"--test-file-costs={report}",
        )
        for index, report in zip((1, 2), reports, strict=True)
    ]
    refused = _probe(tmp_path, "--suite-shard=1/3", f"--suite-file-costs={record}")
    collected: list[set[str]] = []
    for index, (run, report) in enumerate(zip(runs, reports, strict=True), start=1):
        status, output = _finish(run)
        assert status == 0, output
        document = json.loads(report.read_text(encoding="utf-8"))
        assert document["schema"] == suite_files.REPORT_SCHEMA
        assert document["shard"] == f"{index}/2"
        assert document["exit_status"] == 0
        collected.append({row["file"] for row in document["files"]})
        for row in document["files"]:
            assert set(row) == {"file", "tests", "seconds"}
    everything = {suite_files.repository_path(suite / name) for name in _PROBE_FILES}
    assert collected[0] | collected[1] == everything
    assert not collected[0] & collected[1]
    # The two recorded files pack into different shards, longest first.
    assert alpha in collected[0]
    assert gamma in collected[1]

    status, output = _finish(refused)
    assert status != 0
    assert "re-record" in output


def test_the_report_uses_the_actual_location_for_a_test_outside_rootdir(tmp_path: Path) -> None:
    rootdir = tmp_path / "root"
    rootdir.mkdir()
    external = tmp_path / "external/test_external.py"
    external.parent.mkdir()
    external.write_text("def test_external():\n    pass\n", encoding="utf-8")
    report = tmp_path / "external-report.json"

    run = _probe(
        tmp_path,
        f"--test-file-costs={report}",
        rootdir=rootdir,
        test_root=external,
    )
    status, output = _finish(run)

    assert status == 0, output
    document = json.loads(report.read_text(encoding="utf-8"))
    assert document["exit_status"] == 0
    assert [row["file"] for row in document["files"]] == [suite_files.repository_path(external)]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["--suite-a", "--suite-b"], "seven parts"),
        (["--checks", "--typecheck"], "seven parts"),
    ],
)
def test_the_cli_refuses_more_than_one_public_fast_part(
    arguments: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert validate.main([*arguments, "--list"]) == 2
    assert message in capsys.readouterr().err
