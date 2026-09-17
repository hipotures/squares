"""The pull-request wall budget, on recorded runs of the surface it is meant to bound.

`OR-14` names one number -- two to two and a half minutes, three at the outer edge -- and
until 2026-09-15 nothing measured it. Every tier stayed inside its own ceiling while the
required wall went from a 154 s median on 2026-09-06 to 288 s on 2026-09-15, because the
wall is the longest job with its queue, checkout and toolchain and no tier sees that.

So the fixtures here are four real runs of that spiral, recorded from the GitHub API with
`check_pr_wall --dump`:

* `34023121156`, 2026-09-06, the day the jobs split and the surface was in band;
* `34921505934`, 2026-09-15, the same workflow at 295 s;
* `34993754160`, the certificate page at 543 s, from before its `pr-wall` job existed;
* `34996541230`, a run superseded by the next push, which is the case a wall check must
  refuse to judge rather than pass.

The budgets a test needs to bind are fabricated in `tmp_path`, so a test never pins a
figure the live register is free to re-measure. The two things read from the live register
are its own shape and its own rules, which is what `check_gate_budgets` enforces.
"""

# The private readers are the unit under test; a public duplicate would drift from CI.
# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from devtools import check_pr_wall
from devtools.check_gate_budgets import wall_problems
from devtools.check_pr_wall import (
    WallError,
    WorkflowWall,
    exit_status,
    judge,
    kind_of,
    load_walls,
    measure,
    render,
    summary_markdown,
)
from sqpack.yamlio import safe_load

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pr-wall"
IN_BAND = 34023121156
OVER_BUDGET = 34921505934
PAGES = 34993754160
SUPERSEDED = 34996541230


def recorded(run_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    document = json.loads((FIXTURES / f"run-{run_id}.json").read_text(encoding="utf-8"))
    return document["run"], document["jobs"]


def register(
    tmp_path: Path,
    *,
    budget: float = 180.0,
    median: float | None = None,
    samples: int = 15,
    ratio: float = 1.2,
    minimum: int = 15,
    enforcement: str | None = None,
    tracking_bead: str | None = None,
    reason: str | None = None,
) -> Path:
    """A whole wall register in `tmp_path`, so a test can declare what it needs to fail.

    `enforcement`, `tracking_bead` and `reason` are written only when given, so the
    default register is the one with no enforcement declared at all.
    """
    declared = "".join(
        f"    {key}: {value}\n"
        for key, value in (
            ("enforcement", enforcement),
            ("tracking_bead", tracking_bead),
            ("advisory_reason", reason),
        )
        if value is not None
    )
    kinds = ""
    if median is not None:
        rows = "\n".join(
            f"      - {{run: {index + 1}, seconds: {median}}}" for index in range(samples)
        )
        kinds = f"""    kinds:
    - kind: main
      median_seconds: {median}
      measured_on: '2026-09-15'
      samples:
{rows}
"""
    path = tmp_path / "gate-budgets.yaml"
    path.write_text(
        "pull_request_walls:\n"
        "  policy:\n"
        f"    regression_ratio: {ratio}\n"
        f"    min_samples: {minimum}\n"
        "    main_branch: main\n"
        "    setup_steps: ['^(Set up job|Complete job)$', '^Post ', '^Check out ', "
        "'^Install ', '^Synchroni[sz]e ', '^Cache ', '^(Preserve|Retain|Upload) ', "
        "'^(Use|Share) the prepared ']\n"
        "  workflows:\n"
        "  - id: packing-validation\n"
        "    file: .github/workflows/packing-validation.yml\n"
        "    aggregator: packing-required\n"
        "    not_gating: [macos-portability]\n"
        f"    budget_seconds: {budget}\n"
        f"{declared}"
        "    argument: a fabricated register\n"
        f"{kinds}",
        encoding="utf-8",
    )
    return path


#: The fabricated advisory tracker. Whether it is live is `check_gate_budgets`'s question,
#: asked of a fixture store in `test_gate_budgets`; the standalone checker reads its shape.
TRACKER = "think-aaaa"


def advisory_register(tmp_path: Path, *, budget: float = 180.0) -> Path:
    """The fabricated register with its wall declared advisory under `TRACKER`."""
    return register(
        tmp_path,
        budget=budget,
        enforcement="advisory",
        tracking_bead=TRACKER,
        reason="a fabricated owner decision",
    )


def verdict_of(
    path: Path, run_id: int, *, workflow: str = "packing-validation", kind: str | None = "main"
):
    walls = load_walls(path)
    entry = walls.workflow(workflow)
    run, jobs = recorded(run_id)
    measurement = measure(run, jobs, entry, walls.policy, kind=kind)
    return measurement, judge(measurement, entry, walls.policy)


def test_a_run_inside_the_budget_passes_and_names_no_failure(tmp_path: Path) -> None:
    """2026-09-06, the shape the split was measured at: four jobs, and in band."""
    measurement, verdict = verdict_of(register(tmp_path), IN_BAND)
    assert verdict.status == "passed"
    assert verdict.failures == ()
    assert measurement.wall_seconds is not None
    assert measurement.wall_seconds < 180.0
    assert {job.name for job in measurement.jobs} == {"validate", "geometry", "suite", "sweeps"}


def test_a_run_over_the_budget_fails_and_names_the_job_that_set_the_wall(
    tmp_path: Path,
) -> None:
    """The failure has to be actionable, which means naming the job and its split.

    "CI is slow" is not actionable; "`suite` finished last, setup 35s, work 250s" is, and
    it is the sentence that would have started the conversation on 2026-09-08 rather than
    on 2026-09-15.
    """
    measurement, verdict = verdict_of(register(tmp_path), OVER_BUDGET)
    assert verdict.status == "failed"
    assert measurement.critical_job == "suite"
    assert any("suite" in failure and "180s budget" in failure for failure in verdict.failures)
    assert any("work" in failure for failure in verdict.failures)


def test_a_run_inside_the_budget_still_fails_a_regression_against_the_record(
    tmp_path: Path,
) -> None:
    """The budget is `OR-14`'s edge; this is the rule around what was measured.

    The drift that was missed was about ten per cent a day for eight days, every day of it
    inside whatever the ceiling was. A ratio against the recorded median fails the second
    day of that, long before the absolute budget does.
    """
    path = register(tmp_path, budget=180.0, median=110.0)
    measurement, verdict = verdict_of(path, IN_BAND)
    assert measurement.wall_seconds is not None
    assert measurement.wall_seconds <= 180.0
    assert verdict.status == "failed"
    assert any("110s median" in failure for failure in verdict.failures)


def test_a_cancelled_run_is_not_judged_and_says_so(tmp_path: Path) -> None:
    """A superseded push is routine here, and its wall is not the surface's wall.

    Passing it silently would be worse than not checking: the run that replaced it is the
    one with something to say, and a check that reports green on a cancelled run teaches a
    reader that green means nothing.
    """
    _, verdict = verdict_of(register(tmp_path, median=110.0), SUPERSEDED)
    assert verdict.status == "unmeasurable"
    assert verdict.failures == ()
    assert any("cancelled" in note for note in verdict.unjudged)
    assert any(
        "neither the budget nor the regression rule" in note for note in verdict.unjudged
    )
    assert exit_status(verdict) == 1


def test_only_a_measured_passing_verdict_exits_successfully(tmp_path: Path) -> None:
    _, passed = verdict_of(register(tmp_path), IN_BAND)
    _, failed = verdict_of(register(tmp_path), OVER_BUDGET)
    assert exit_status(passed) == 0
    assert exit_status(failed) == 1


def test_too_few_recorded_runs_leaves_the_regression_rule_unapplied(tmp_path: Path) -> None:
    """Runner speed here is bimodal, so a median over a handful of runs is not a median.

    About seventy per cent of `suite` jobs land on the slow class, so a small sample can
    put the record in the fast mode and fail every ordinary run afterwards. Below
    `min_samples` the rule reports that it did not run, which is the honest answer.
    """
    path = register(tmp_path, median=110.0, samples=3)
    _, verdict = verdict_of(path, IN_BAND)
    assert verdict.status == "passed"
    assert any("3 run(s)" in note and "not applied" in note for note in verdict.unjudged)


def test_a_kind_with_no_record_is_reported_rather_than_skipped(tmp_path: Path) -> None:
    _, verdict = verdict_of(register(tmp_path), IN_BAND, kind="stacked")
    assert any("`stacked`" in note for note in verdict.unjudged)
    _, unknown = verdict_of(register(tmp_path), IN_BAND, kind=None)
    assert any("base branch is unknown" in note for note in unknown.unjudged)


def test_the_wall_ends_where_the_wall_check_starts(tmp_path: Path) -> None:
    """The wall includes aggregator checkout and setup, but not the check itself.

    The same rule applies afterwards, so a run measured live and the same run measured a
    day later agree. A run whose workflow had no aggregator yet -- every certificate-page
    run before 2026-09-15 -- ends at its last job instead and says which it used.
    """
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    aggregator = next(job for job in jobs if job["name"] == "packing-required")
    aggregator["steps"].insert(
        -1,
        {
            "name": check_pr_wall.WALL_STEP,
            "conclusion": "success",
            "started_at": aggregator["completed_at"],
            "completed_at": aggregator["completed_at"],
        },
    )
    live = deepcopy(jobs)
    for job in live:
        if job["name"] == "packing-required":
            job["status"], job["conclusion"], job["completed_at"] = "in_progress", None, None
    measured_live = measure(run, live, entry, walls.policy, kind="main")
    measured_after = measure(run, jobs, entry, walls.policy, kind="main")
    assert measured_live.wall_seconds == measured_after.wall_seconds
    assert measured_after.ends_at == f"the start of `{check_pr_wall.WALL_STEP}`"
    assert aggregator["started_at"] > max(
        str(job["completed_at"]) for job in jobs if job["name"] != "packing-required"
    )


def test_a_prerequisite_still_running_is_unmeasurable(tmp_path: Path) -> None:
    """The API can lag the `needs` graph, and a wall taken then would be a wall of less."""
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    pending = deepcopy(jobs)
    for job in pending:
        if job["name"] == "suite":
            job["status"], job["conclusion"], job["completed_at"] = "in_progress", None, None
    verdict = judge(
        measure(run, pending, entry, walls.policy, kind="main"), entry, walls.policy
    )
    assert verdict.status == "unmeasurable"
    assert any("`suite` has not completed" in note for note in verdict.unjudged)


def test_a_partial_rerun_cannot_reuse_old_jobs_to_report_a_near_zero_wall(
    tmp_path: Path,
) -> None:
    """GitHub's latest-job view may mix carried successes into a later attempt."""
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    partial = deepcopy(run)
    aggregator = next(job for job in jobs if job["name"] == "packing-required")
    partial["run_attempt"] = 2
    partial["run_started_at"] = aggregator["started_at"]
    measurement = measure(partial, jobs, entry, walls.policy, kind="main")
    verdict = judge(measurement, entry, walls.policy)
    assert verdict.status == "unmeasurable"
    assert any("partial rerun" in note for note in verdict.unjudged)
    assert exit_status(verdict) == 1


def test_a_partial_rerun_cannot_reuse_an_old_wall_endpoint(tmp_path: Path) -> None:
    """The aggregator can lag onto a new attempt after its prerequisites settle."""
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    mixed = deepcopy(jobs)
    aggregator = next(job for job in mixed if job["name"] == "packing-required")
    prior_attempt = "2000-01-01T00:00:00+00:00"
    aggregator["started_at"] = prior_attempt
    aggregator["steps"].insert(
        -1,
        {
            "name": check_pr_wall.WALL_STEP,
            "conclusion": "success",
            "started_at": prior_attempt,
            "completed_at": prior_attempt,
        },
    )

    measurement = measure(run, mixed, entry, walls.policy, kind="main")
    verdict = judge(measurement, entry, walls.policy)

    assert measurement.wall_seconds is None
    assert verdict.status == "unmeasurable"
    assert any(
        "packing-required" in note and "partial rerun" in note for note in verdict.unjudged
    )
    assert any(check_pr_wall.WALL_STEP in note for note in verdict.unjudged)
    assert exit_status(verdict) == 1


def test_reversed_job_and_step_timestamps_are_unmeasurable(tmp_path: Path) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    corrupted = deepcopy(jobs)
    suite = next(job for job in corrupted if job["name"] == "suite")
    suite["completed_at"] = "2000-01-01T00:00:00+00:00"
    first_step = suite["steps"][0]
    first_step["completed_at"] = "2000-01-01T00:00:00+00:00"

    measurement = measure(run, corrupted, entry, walls.policy, kind="main")
    verdict = judge(measurement, entry, walls.policy)

    assert verdict.status == "unmeasurable"
    assert any("`suite` completed before it started" in note for note in verdict.unjudged)
    assert any(
        "`suite` step" in note and "completed before it started" in note
        for note in verdict.unjudged
    )
    suite_timing = next(timing for timing in measurement.jobs if timing.name == "suite")
    assert suite_timing.wall_seconds is None


def test_a_reported_aggregator_without_a_start_is_not_historical_fallback(
    tmp_path: Path,
) -> None:
    """Only an absent aggregator identifies an older workflow topology."""
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    pending = deepcopy(jobs)
    aggregator = next(job for job in pending if job["name"] == "packing-required")
    aggregator["status"], aggregator["completed_at"] = "in_progress", None
    measurement = measure(run, pending, entry, walls.policy, kind="main")
    assert measurement.wall_seconds is None
    assert measurement.ends_at == f"nowhere: `{check_pr_wall.WALL_STEP}` has not started"
    assert f"`{check_pr_wall.WALL_STEP}` has not started" in measurement.unmeasurable


class _JobsClient:
    def __init__(self, responses: list[list[dict[str, Any]]]) -> None:
        self.responses = responses
        self.calls = 0

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        _ = run_id
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def test_the_jobs_reader_paginates_past_the_first_hundred(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = check_pr_wall.Client("jlevy/squares", None)
    first = [{"name": f"job-{index}"} for index in range(100)]
    second = [{"name": "job-100"}]
    paths: list[str] = []

    def get(path: str) -> dict[str, object]:
        paths.append(path)
        return {"total_count": 101, "jobs": first if path.endswith("page=1") else second}

    monkeypatch.setattr(client, "get", get)
    assert len(client.jobs(IN_BAND)) == 101
    assert paths == [
        f"actions/runs/{IN_BAND}/jobs?filter=latest&per_page=100&page=1",
        f"actions/runs/{IN_BAND}/jobs?filter=latest&per_page=100&page=2",
    ]


def test_the_live_reader_waits_for_the_aggregator_it_is_running_in(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    _, jobs = recorded(IN_BAND)
    aggregate = next(job for job in jobs if job["name"] == "packing-required")
    aggregate["steps"].append(
        {
            "name": check_pr_wall.WALL_STEP,
            "started_at": aggregate["completed_at"],
            "completed_at": None,
            "conclusion": None,
        }
    )
    without = [job for job in jobs if job["name"] != "packing-required"]
    client = _JobsClient([without, jobs])
    monkeypatch.setattr(check_pr_wall.time, "sleep", lambda _seconds: None)
    expected = check_pr_wall._reported_job_ids(jobs, entry)
    settled = check_pr_wall._settled_jobs(client, IN_BAND, entry, expected)
    assert client.calls == 2
    assert any(job["name"] == "packing-required" for job in settled)


@pytest.mark.parametrize("failure", ["missing", "not-started"])
def test_the_live_reader_refuses_a_stale_aggregator_view(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    _, jobs = recorded(IN_BAND)
    if failure == "missing":
        jobs = [job for job in jobs if job["name"] != "packing-required"]
    else:
        jobs = deepcopy(jobs)
        next(job for job in jobs if job["name"] == "packing-required")["started_at"] = None
    client = _JobsClient([jobs])
    monkeypatch.setattr(check_pr_wall.time, "sleep", lambda _seconds: None)
    with pytest.raises(WallError, match="live aggregator"):
        check_pr_wall._settled_jobs(
            client, IN_BAND, entry, check_pr_wall._reported_job_ids(jobs, entry)
        )
    assert client.calls == check_pr_wall.SETTLE_ATTEMPTS


def test_the_live_reader_refuses_a_missing_prerequisite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    _, jobs = recorded(IN_BAND)
    aggregate = next(job for job in jobs if job["name"] == "packing-required")
    aggregate["steps"].append(
        {"name": check_pr_wall.WALL_STEP, "started_at": aggregate["completed_at"]}
    )
    expected = check_pr_wall._reported_job_ids(jobs, entry)
    jobs = [job for job in jobs if job["name"] != "suite"]
    client = _JobsClient([jobs])
    monkeypatch.setattr(check_pr_wall.time, "sleep", lambda _seconds: None)
    with pytest.raises(WallError, match="required prerequisite set"):
        check_pr_wall._settled_jobs(client, IN_BAND, entry, expected)


def test_the_live_reader_allows_extra_skipped_jobs_but_not_extra_work(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    _, jobs = recorded(IN_BAND)
    aggregate = next(job for job in jobs if job["name"] == "packing-required")
    aggregate["steps"].append(
        {"name": check_pr_wall.WALL_STEP, "started_at": aggregate["completed_at"]}
    )
    expected = check_pr_wall._reported_job_ids(jobs, entry)
    skipped = {
        "name": "deploy",
        "status": "completed",
        "conclusion": "skipped",
        "created_at": aggregate["created_at"],
        "started_at": aggregate["started_at"],
        "completed_at": aggregate["completed_at"],
        "steps": [],
    }
    monkeypatch.setattr(check_pr_wall.time, "sleep", lambda _seconds: None)
    settled = check_pr_wall._settled_jobs(
        _JobsClient([[*jobs, skipped]]), IN_BAND, entry, expected
    )
    assert settled[-1]["name"] == "deploy"

    extra_work = {**skipped, "name": "undeclared-work", "conclusion": "success"}
    with pytest.raises(WallError, match="unexpected non-skipped jobs: undeclared-work"):
        check_pr_wall._settled_jobs(
            _JobsClient([[*jobs, extra_work]]), IN_BAND, entry, expected
        )


def test_a_successful_job_without_timestamps_is_unmeasurable(tmp_path: Path) -> None:
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(IN_BAND)
    damaged = deepcopy(jobs)
    suite = next(job for job in damaged if job["name"] == "suite")
    suite["started_at"] = None
    suite["completed_at"] = None
    measurement = measure(run, damaged, entry, walls.policy, kind="main")
    verdict = judge(measurement, entry, walls.policy)
    assert verdict.status == "unmeasurable"
    assert any("no start time" in note for note in verdict.unjudged)


def test_the_macos_job_is_declared_aside_and_not_waited_on(tmp_path: Path) -> None:
    """`packing-required` does not wait on it, so it must not be part of the wall."""
    measurement, _ = verdict_of(register(tmp_path), OVER_BUDGET)
    assert "macos-portability" not in {job.name for job in measurement.jobs}
    _, jobs = recorded(OVER_BUDGET)
    assert "macos-portability" in {str(job["name"]) for job in jobs}


def test_every_job_of_the_run_is_measured_rather_than_a_list_of_names(tmp_path: Path) -> None:
    """The jobs come from the run, so a job added to the surface is waited on at once.

    The surface has been four jobs, then five; the certificate page's is being split as
    this lands. A hard-coded list would have to be edited by whoever changes the graph,
    which is exactly the step that was skipped every time the wall grew.
    """
    walls = load_walls(register(tmp_path))
    entry = walls.workflow("packing-validation")
    run, jobs = recorded(OVER_BUDGET)
    invented = [
        *deepcopy(jobs),
        {
            "name": "a job nobody told the register about",
            "status": "completed",
            "conclusion": "success",
            "created_at": run["run_started_at"],
            "started_at": run["run_started_at"],
            "completed_at": "2026-09-15T02:40:00Z",
            "steps": [],
        },
    ]
    measurement = measure(run, invented, entry, walls.policy, kind="main")
    assert measurement.critical_job == "a job nobody told the register about"
    still_running = deepcopy(invented)
    still_running[-1]["status"], still_running[-1]["completed_at"] = "in_progress", None
    waiting = judge(
        measure(run, still_running, entry, walls.policy, kind="main"), entry, walls.policy
    )
    assert waiting.status == "unmeasurable"
    assert any("nobody told the register about" in note for note in waiting.unjudged)


def test_a_matrix_job_is_measured_and_a_pages_run_reports_its_own_end(tmp_path: Path) -> None:
    """The certificate page's two `font-loading` jobs are one matrix, reported as two."""
    walls = load_walls(register(tmp_path))
    entry = WorkflowWall(
        id="certificate-page",
        file=".github/workflows/pages.yml",
        aggregator="pr-wall",
        not_gating=(),
        budget_seconds=180.0,
        kinds=(),
    )
    run, jobs = recorded(PAGES)
    measurement = measure(run, jobs, entry, walls.policy, kind="stacked")
    verdict = judge(measurement, entry, walls.policy)
    assert {job.name for job in measurement.jobs} == {
        "prepare",
        "build",
        "font-loading (webkit)",
        "font-loading (firefox)",
    }
    assert measurement.ends_at.endswith("(this run has no `pr-wall`)")
    assert verdict.status == "failed"


def test_each_job_is_split_into_queue_setup_and_work(tmp_path: Path) -> None:
    """`OR-14` asks for queue, setup and execution apart, and the split is where it went.

    Setup was 180 of 874 Linux job-seconds on a stack run of 2026-09-15 and no budget
    covered any of it, which is how checkout doubling from 8 s to 16 s went unremarked.
    """
    measurement, _ = verdict_of(register(tmp_path), OVER_BUDGET)
    suite = next(job for job in measurement.jobs if job.name == "suite")
    assert suite.wall_seconds is not None
    assert suite.queue_seconds is not None
    assert suite.setup_seconds > 0
    assert suite.work_seconds > suite.setup_seconds
    assert suite.setup_seconds + suite.work_seconds <= suite.wall_seconds + 1


def test_the_verdict_renders_the_table_and_the_step_summary(tmp_path: Path) -> None:
    measurement, verdict = verdict_of(register(tmp_path), OVER_BUDGET)
    lines = render(measurement, verdict)
    assert any("suite" in line for line in lines)
    assert lines[-1] == "  verdict: failed"
    summary = summary_markdown(measurement, verdict)
    assert "| Job | Queue | Setup | Work | Wall |" in summary
    assert "**Fail:**" in summary


def test_the_kind_of_a_pull_request_is_its_base() -> None:
    assert kind_of("main", "main") == "main"
    assert kind_of("claude/no-js-spike-tools", "main") == "stacked"
    assert kind_of(None, "main") is None


def test_a_median_that_disagrees_with_its_own_samples_is_refused(tmp_path: Path) -> None:
    """The figure is read from the runs it names, not typed beside them."""
    path = register(tmp_path, median=110.0)
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "median_seconds: 110.0", "median_seconds: 90.0"
        ),
        encoding="utf-8",
    )
    with pytest.raises(WallError, match="median"):
        load_walls(path)


@pytest.mark.parametrize("value", [".nan", ".inf", "-.inf"])
@pytest.mark.parametrize(
    ("declaration", "number", "field"),
    [
        ("regression_ratio: 1.2", "1.2", "policy.regression_ratio"),
        ("min_samples: 15", "15", "policy.min_samples"),
        ("budget_seconds: 180.0", "180.0", ".budget_seconds"),
        ("median_seconds: 110.0", "110.0", ".median_seconds"),
        ("run: 1, seconds: 110.0", "110.0", "kinds[0] seconds"),
        ("run: 1, seconds", "1", "kinds[0] run"),
    ],
)
def test_nonfinite_wall_numbers_are_refused(
    tmp_path: Path, declaration: str, number: str, field: str, value: str
) -> None:
    """A NaN compares false with every bound, so no later range check would catch one."""
    path = register(tmp_path, median=110.0)
    document = path.read_text(encoding="utf-8")
    assert declaration in document
    path.write_text(
        document.replace(declaration, declaration.replace(number, value), 1),
        encoding="utf-8",
    )
    with pytest.raises(WallError, match=rf"{re.escape(field)} must be a positive number"):
        load_walls(path)


@pytest.mark.parametrize("value", [".nan", ".inf"])
def test_a_nonfinite_budget_fails_the_static_wall_check(tmp_path: Path, value: str) -> None:
    """The static check compares a budget with `OR-14`'s edge, and `nan > 180` is false."""
    path = register(tmp_path)
    document = path.read_text(encoding="utf-8")
    path.write_text(
        document.replace("budget_seconds: 180.0", f"budget_seconds: {value}"),
        encoding="utf-8",
    )
    problems = wall_problems(path)
    assert len(problems) == 1, problems
    assert problems[0].startswith("pull_request_walls: "), problems
    assert ".budget_seconds must be a positive number" in problems[0], problems


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("min_samples: 15", "min_samples: 1.5", "policy.min_samples"),
        ("run: 1, seconds:", "run: 1.5, seconds:", "run"),
    ],
)
def test_fractional_integer_fields_are_refused(
    tmp_path: Path, old: str, new: str, field: str
) -> None:
    path = register(tmp_path, median=110.0)
    document = path.read_text(encoding="utf-8")
    assert old in document
    path.write_text(document.replace(old, new, 1), encoding="utf-8")
    with pytest.raises(WallError, match=rf"{field}.*positive integer"):
        load_walls(path)


@pytest.mark.parametrize(
    "declaration",
    ["    regression_ratio: 1.2\n", "    budget_seconds: 180.0\n"],
)
def test_duplicate_wall_fields_are_refused(tmp_path: Path, declaration: str) -> None:
    path = register(tmp_path)
    document = path.read_text(encoding="utf-8")
    assert declaration in document
    path.write_text(
        document.replace(declaration, declaration + declaration, 1), encoding="utf-8"
    )

    with pytest.raises(WallError, match="duplicate key"):
        load_walls(path)


# --- advisory enforcement, the owner's 2026-09-17 decision under think-g4n9 ---------------


class _RecordedClient:
    """The API reads `main` makes, answered from one recorded run."""

    def __init__(self, run: dict[str, Any], jobs: list[dict[str, Any]]) -> None:
        self._run = run
        self._jobs = jobs

    def run(self, run_id: int) -> dict[str, Any]:
        _ = run_id
        return self._run

    def jobs(self, run_id: int) -> list[dict[str, Any]]:
        _ = run_id
        return self._jobs


def run_main(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    argv: list[str],
    run: dict[str, Any],
    jobs: list[dict[str, Any]],
) -> tuple[int, str]:
    """`main` inside a simulated Actions job: its exit status and its step summary."""
    client = _RecordedClient(run, jobs)
    summary = tmp_path / "step-summary.md"
    monkeypatch.setattr(check_pr_wall, "Client", lambda _repository, _token: client)
    monkeypatch.setattr(check_pr_wall, "github_token", lambda: None)
    monkeypatch.setattr(check_pr_wall.time, "sleep", lambda _seconds: None)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    status = check_pr_wall.main(["--workflow", "packing-validation", *argv])
    return status, summary.read_text(encoding="utf-8") if summary.exists() else ""


def historical(path: Path, run_id: int) -> list[str]:
    """The arguments that judge one recorded run afterwards, against `path`."""
    return ["--register", str(path), "--run-id", str(run_id), "--base-ref", "main"]


def test_an_advisory_wall_over_its_budget_warns_names_its_bead_and_exits_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Five hosted walls read 194, 189, 178, 166 and 216 s on identical code.

    The owner's answer was to keep measuring and reporting the wall and to stop failing
    the aggregator on its size until `think-g4n9` brings it under 180 s. The diagnosis is
    the enforcing one word for word, so nothing a reader needs is hidden: only the exit
    status and the annotation's level change, and the warning names the bead.
    """
    _, enforcing = verdict_of(register(tmp_path), OVER_BUDGET)
    path = advisory_register(tmp_path)
    measurement, verdict = verdict_of(path, OVER_BUDGET)
    assert verdict.status == "advisory"
    assert verdict.failures == enforcing.failures
    assert exit_status(verdict) == 0
    assert render(measurement, verdict)[-1] == "  verdict: advisory"

    run, jobs = recorded(OVER_BUDGET)
    status, summary = run_main(tmp_path, monkeypatch, historical(path, OVER_BUDGET), run, jobs)
    printed = capsys.readouterr().out.splitlines()
    assert status == 0
    assert not any(line.startswith("::error") for line in printed)
    warnings = [
        line
        for line in printed
        if line.startswith(f"::warning title=Pull-request wall (advisory under {TRACKER})::")
    ]
    assert len(warnings) == len(enforcing.failures)
    assert any("180s budget" in warning for warning in warnings)
    assert all(f"Not enforced until {TRACKER}" in warning for warning in warnings)
    assert any(
        line.startswith("  FAIL (advisory, not enforced): the pull request waited")
        for line in printed
    )
    assert any(
        line.startswith(f"  enforcement: the wall is advisory under {TRACKER}")
        for line in printed
    )
    assert "  verdict: advisory" in printed
    assert summary.startswith(
        f"### Pull-request wall: advisory (failed, not enforced under `{TRACKER}`)"
    )
    assert "- **Fail (advisory, not enforced):** the pull request waited" in summary
    assert f"- **Enforcement:** the wall is advisory under {TRACKER}" in summary


@pytest.mark.parametrize("evidence", ["cancelled", "partial rerun", "prerequisite running"])
def test_an_advisory_wall_still_fails_a_run_it_cannot_measure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    evidence: str,
) -> None:
    """Advisory relaxes the wall's size, never the evidence the size is read from.

    Otherwise a broken measurement would read as a wall that merely ran long, and an
    advisory wall would become the way to stop seeing the wall at all.
    """
    path = advisory_register(tmp_path)
    run_id = SUPERSEDED if evidence == "cancelled" else OVER_BUDGET
    run, jobs = recorded(run_id)
    if evidence == "partial rerun":
        aggregator = next(job for job in jobs if job["name"] == "packing-required")
        run["run_attempt"], run["run_started_at"] = 2, aggregator["started_at"]
    elif evidence == "prerequisite running":
        suite = next(job for job in jobs if job["name"] == "suite")
        suite["status"], suite["conclusion"], suite["completed_at"] = "in_progress", None, None

    status, summary = run_main(tmp_path, monkeypatch, historical(path, run_id), run, jobs)
    printed = capsys.readouterr().out.splitlines()
    assert status == 1
    assert "  verdict: unmeasurable" in printed
    assert not any(
        line.startswith("::warning title=Pull-request wall (advisory") for line in printed
    )
    assert any("an unmeasurable run still fails" in line for line in printed)
    assert summary.startswith("### Pull-request wall: unmeasurable\n")


@pytest.mark.parametrize(
    ("fault", "refusal"),
    [
        ("no prerequisites", "EXPECTED_PREREQUISITES is not set"),
        ("stale aggregator", "did not report live aggregator `packing-required`"),
        ("nonfinite budget", ".budget_seconds must be a positive number"),
    ],
)
def test_an_advisory_wall_still_refuses_what_the_live_check_cannot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fault: str,
    refusal: str,
) -> None:
    """A missing prerequisite set, a stale jobs view and a malformed register exit 2."""
    path = advisory_register(tmp_path)
    run, jobs = recorded(OVER_BUDGET)
    argv = ["--register", str(path)]
    monkeypatch.setenv("GITHUB_RUN_ID", str(OVER_BUDGET))
    monkeypatch.setenv("GITHUB_JOB", "packing-required")
    monkeypatch.setenv("GITHUB_BASE_REF", "main")
    monkeypatch.setenv("EXPECTED_PREREQUISITES", json.dumps({"validate": {}, "suite": {}}))
    if fault == "no prerequisites":
        monkeypatch.delenv("EXPECTED_PREREQUISITES")
    elif fault == "stale aggregator":
        jobs = [job for job in jobs if job["name"] != "packing-required"]
    else:
        document = path.read_text(encoding="utf-8")
        path.write_text(
            document.replace("budget_seconds: 180.0", "budget_seconds: .nan"), encoding="utf-8"
        )
    status, _ = run_main(tmp_path, monkeypatch, argv, run, jobs)
    assert status == 2
    assert refusal in capsys.readouterr().err


@pytest.mark.parametrize("enforcement", [None, "enforcing"])
def test_an_enforcing_wall_fails_exactly_as_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    enforcement: str | None,
) -> None:
    """No declaration and `enforcement: enforcing` are the same wall check as before."""
    path = register(tmp_path, enforcement=enforcement)
    assert load_walls(path).workflow("packing-validation").advisory is None
    run, jobs = recorded(OVER_BUDGET)
    status, summary = run_main(tmp_path, monkeypatch, historical(path, OVER_BUDGET), run, jobs)
    printed = capsys.readouterr().out
    assert status == 1
    assert "::error title=Pull-request wall::the pull request waited" in printed
    assert "  FAIL: the pull request waited" in printed
    assert "advisory" not in printed
    assert "  verdict: failed" in printed.splitlines()
    assert summary.startswith("### Pull-request wall: failed\n")
    assert "- **Fail:** the pull request waited" in summary
    assert "advisory" not in summary


@pytest.mark.parametrize(
    ("bead", "reason", "match"),
    [
        (None, "a reason", "tracking_bead: think-xxxx"),
        ("gn49", "a reason", "tracking_bead: think-xxxx"),
        ("think-g4n9 and think-aaaa", "a reason", "tracking_bead: think-xxxx"),
        (TRACKER, None, "a non-empty advisory_reason"),
        (TRACKER, "''", "a non-empty advisory_reason"),
    ],
)
def test_an_advisory_wall_must_name_its_tracking_bead_and_its_reason(
    tmp_path: Path, bead: str | None, reason: str | None, match: str
) -> None:
    """The ratchet a relaxed `tsconfig` flag is held to: name the bead that removes it."""
    path = register(tmp_path, enforcement="advisory", tracking_bead=bead, reason=reason)
    with pytest.raises(WallError, match=re.escape(match)):
        load_walls(path)


@pytest.mark.parametrize("value", ["lenient", "Advisory", "null", "false"])
def test_an_unknown_enforcement_is_refused(tmp_path: Path, value: str) -> None:
    """A misspelt enforcement would otherwise be a third mode nobody defined."""
    path = register(tmp_path, enforcement=value, tracking_bead=TRACKER, reason="a reason")
    with pytest.raises(WallError, match="enforcement must be one of enforcing, advisory"):
        load_walls(path)


@pytest.mark.parametrize(
    ("enforcement", "bead", "reason", "stale"),
    [
        ("enforcing", TRACKER, None, "tracking_bead"),
        (None, None, "a reason", "advisory_reason"),
    ],
)
def test_an_enforcing_wall_names_no_tracker(
    tmp_path: Path, enforcement: str | None, bead: str | None, reason: str | None, stale: str
) -> None:
    """Re-enforcing a wall removes its tracker, so none reads as a relaxation in force."""
    path = register(tmp_path, enforcement=enforcement, tracking_bead=bead, reason=reason)
    with pytest.raises(WallError, match=f"is enforcing but declares {stale}"):
        load_walls(path)


def test_the_live_register_declares_a_wall_for_both_workflows() -> None:
    """Read from the register rather than asserted here, because both are measurements.

    What is pinned is that they exist, that each names a workflow file that exists, and
    that no budget is looser than `OR-14`'s outer edge -- the rule
    `devtools.check_gate_budgets` enforces and this repeats as a live check.
    """
    walls = load_walls(check_pr_wall.REGISTER)
    assert {workflow.id for workflow in walls.workflows} == {
        "packing-validation",
        "certificate-page",
    }
    repository = Path(__file__).resolve().parents[2]
    for workflow in walls.workflows:
        assert (repository / workflow.file).is_file()
        assert workflow.budget_seconds <= 180.0
        for record in workflow.kinds:
            assert len(record.samples) >= 1
            assert record.median_seconds > 0


def test_wall_jobs_pin_the_interpreter_and_their_only_dependency() -> None:
    repository = Path(__file__).resolve().parents[2]
    jobs = []
    for path, name in (
        (repository / ".github/workflows/pages.yml", "pages-required"),
        (repository / ".github/workflows/packing-validation.yml", "packing-required"),
    ):
        document = safe_load(path.read_text(encoding="utf-8"))
        jobs.append(document["jobs"][name])

    for job in jobs:
        assert job["permissions"]["actions"] == "read"
        steps = job["steps"]
        wall_steps = [
            step
            for step in steps
            if step.get("name")
            in {
                "Check out the wall budget and its register",
                "Install uv and Python 3.14",
                "Hold the pull request's wall to its budget",
            }
        ]
        assert len(wall_steps) == 3
        assert all(
            step.get("if") == "always() && github.event_name == 'pull_request'"
            for step in wall_steps
        )
        checkout = next(
            step
            for step in steps
            if step.get("name") == "Check out the wall budget and its register"
        )
        assert checkout["with"]["filter"] == "blob:none"
        setup = next(step for step in steps if step.get("name") == "Install uv and Python 3.14")
        assert setup["with"] == {
            "version": "0.12.8",
            "python-version": "3.14.7",
            "enable-cache": False,
        }
        command = next(
            step
            for step in steps
            if step.get("name") == "Hold the pull request's wall to its budget"
        )
        assert command["env"]["EXPECTED_PREREQUISITES"] == "${{ toJSON(needs) }}"
        assert command["run"].startswith(
            "uv run --no-project --python 3.14.7 --with PyYAML==6.0.3 python "
        )
        assert "python3 " not in command["run"]
