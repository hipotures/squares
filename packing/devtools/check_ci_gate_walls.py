#!/usr/bin/env python3
"""Clock a CI gate's hosted jobs against `devtools/gate-budgets.yaml`, as a tier is clocked.

`OR-17` exists because of a number nothing read. `deep-gate.yml` and
`test_deep_gate_workflow.py` price the exhaustive tier at 1943.05s -- the figure that
refused its promotion into `--fast` -- and on 2026-09-21 the job that runs it cost 2674s
on two complete runs of PR 208. That is 1.38x, under the 1.5x that fails a local tier,
and nobody saw it: `sqpack.gate_budgets` judges `packing-validate`'s own wall, and a
hosted job's wall was judged by nothing at all. A tier does not become unbounded by being
deferred.

So this is the same register and the same four rules, pointed at a workflow run instead
of a subprocess. It reads one run's jobs from the GitHub API and reports, per job:

* **the wall** the reviewer waits for, from the job starting to the job completing;
* **the queue** before it, which the gate's wall includes and the job's does not;
* **the split** of that wall into setup and work, by the same `setup_steps` patterns
  `check_pr_wall` classifies a pull-request job's steps with. This is what makes a
  verdict actionable rather than a complaint: on run 35579234418 `exhaustive-tier` spent
  22s of its 2674s on checkout and toolchain, so its gap against the declared step time
  is the step, not the runner.

Each wall then goes through `gate_budgets.judge_ci_job`, which is `judge`'s own
`band_findings` -- ceiling, drift, stale -- with the gate's declared `drift_ratio` in
place of the policy's. The gate's entry says what spread that band was chosen against.

**Reporting is the default and it is deliberate.** A gate declared `enforcement:
reporting` measures, diagnoses and prints every failure and still exits 0, because a
false red on a 45-minute pre-merge gate costs another 45 minutes to clear and teaches
people to stop reading it. `--enforce` is the switch, and the gate's `tracking_bead` is
the work that earns it.

From `packing/`:
    uv run --frozen --all-extras --group dev python -m devtools.check_ci_gate_walls \
        --gate deep-gate --run-id 35579234418

To record a baseline, measure several runs at once and paste the block it prints:
    ... check_ci_gate_walls --gate deep-gate --sample --recent 6
    ... check_ci_gate_walls --gate deep-gate --sample --run-id A --run-id B

In CI, the run and repository come from the environment:
    uv run --frozen --all-extras --group dev python -m devtools.check_ci_gate_walls \
        --gate deep-gate

`--dump` prints the trimmed API payload a verdict was computed from.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from devtools.check_pr_wall import (
    Client,
    WallError,
    WallPolicy,
    github_token,
    load_walls,
    trim,
)
from sqpack.gate_budgets import (
    BUDGETS,
    BudgetError,
    CiGate,
    Register,
    Verdict,
    ci_declaration_problems,
    judge_ci_job,
    load,
    render,
)


class GateWallError(Exception):
    """The API cannot supply what a verdict needs."""


@dataclass(frozen=True)
class JobWall:
    """One hosted job's wall, with the queue before it and its setup/work split."""

    name: str
    runner: str
    conclusion: str | None
    queue_seconds: float | None
    setup_seconds: float
    work_seconds: float
    wall_seconds: float | None
    steps: tuple[tuple[str, float], ...]

    @property
    def overhead_seconds(self) -> float | None:
        """Wall that is neither the work steps nor the queue: setup, teardown, finalise."""
        if self.wall_seconds is None:
            return None
        return self.wall_seconds - self.work_seconds


@dataclass(frozen=True)
class GateRun:
    """One workflow run of a gate: its jobs, and the wall a reviewer waited through."""

    run_id: int
    head_sha: str
    conclusion: str | None
    jobs: tuple[JobWall, ...]
    wall_seconds: float | None
    critical_job: str | None

    def job(self, name: str) -> JobWall | None:
        return next((job for job in self.jobs if job.name == name), None)


def _instant(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return datetime.fromisoformat(value)


def _span(start: object, end: object) -> float | None:
    begun, finished = _instant(start), _instant(end)
    if begun is None or finished is None or finished < begun:
        return None
    return (finished - begun).total_seconds()


def _runner(job: dict[str, Any]) -> str:
    """The label the job asked for, which is the only shape the jobs API reports."""
    labels = [str(label) for label in job.get("labels") or []]
    return labels[0] if labels else "unknown"


def job_wall(job: dict[str, Any], policy: WallPolicy) -> JobWall:
    """One job's wall and its split, classified by the register's own setup patterns."""
    setup = work = 0.0
    steps: list[tuple[str, float]] = []
    for step in job.get("steps") or []:
        name = str(step.get("name", ""))
        seconds = _span(step.get("started_at"), step.get("completed_at")) or 0.0
        if policy.is_setup(name):
            setup += seconds
        else:
            work += seconds
            steps.append((name, seconds))
    return JobWall(
        name=str(job["name"]),
        runner=_runner(job),
        conclusion=job.get("conclusion"),
        queue_seconds=_span(job.get("created_at"), job.get("started_at")),
        setup_seconds=setup,
        work_seconds=work,
        wall_seconds=_span(job.get("started_at"), job.get("completed_at"))
        if job.get("status") == "completed"
        else None,
        steps=tuple(steps),
    )


def measure(
    run: dict[str, Any], jobs: Sequence[dict[str, Any]], gate: CiGate, policy: WallPolicy
) -> GateRun:
    """The gate's wall, from the run starting to its last gating job completing.

    The aggregate is excluded from the wall's endpoint for the reason it has no ceiling:
    it is four seconds of `test` that cannot move, and a wall measured to it would credit
    the gate's cost to the wrong job. It is measured and printed all the same, because a
    step added to an aggregate is exactly how a cheap job stops being cheap.
    """
    walls = [job_wall(job, policy) for job in jobs]
    gating = [job for job in walls if job.name != gate.aggregate]
    start = _instant(run.get("run_started_at") or run.get("created_at"))
    ends = [
        _instant(job.get("completed_at"))
        for job in jobs
        if str(job["name"]) != gate.aggregate and job.get("completed_at")
    ]
    finished = [end for end in ends if end is not None]
    wall = (max(finished) - start).total_seconds() if start and finished else None
    longest = max(
        (job for job in gating if job.wall_seconds is not None),
        key=lambda job: job.wall_seconds or 0.0,
        default=None,
    )
    return GateRun(
        run_id=int(run["id"]),
        head_sha=str(run.get("head_sha", ""))[:8],
        conclusion=run.get("conclusion"),
        jobs=tuple(walls),
        wall_seconds=wall,
        critical_job=longest.name if longest else None,
    )


def verdicts(
    register: Register, gate: CiGate, measured: GateRun, *, enforce: bool = False
) -> list[Verdict]:
    """One verdict per declared job, plus the gate's whole wall.

    Driven by the register rather than by the run, so a job that stopped reporting is a
    verdict saying its wall is unmeasurable rather than a silently missing row.
    """
    found: list[Verdict] = []
    for budget in gate.jobs:
        job = measured.job(budget.id)
        if job is None or job.wall_seconds is None:
            found.append(
                Verdict(
                    tier=budget.id,
                    wall_seconds=0.0,
                    status="unknown",
                    ceiling_seconds=budget.ceiling_seconds,
                    measured_seconds=budget.measured_seconds,
                    notes=(
                        (
                            f"run {measured.run_id} reports no finished {budget.id!r} "
                            "job, so its band was not applied"
                        ),
                    ),
                )
            )
            continue
        found.append(
            judge_ci_job(
                register,
                gate.id,
                budget.id,
                wall_seconds=job.wall_seconds,
                steps=job.steps,
                runner=job.runner,
                enforce=enforce,
            )
        )
    if measured.wall_seconds is not None:
        found.append(
            judge_ci_job(
                register,
                gate.id,
                "wall",
                wall_seconds=measured.wall_seconds,
                steps=tuple(
                    (job.name, job.wall_seconds)
                    for job in measured.jobs
                    if job.wall_seconds is not None
                ),
                runner=gate.reference.runner,
                enforce=enforce,
            )
        )
    return found


def _seconds(value: float | None) -> str:
    return "  --  " if value is None else f"{value:6.0f}s"


def render_run(gate: CiGate, measured: GateRun, found: Sequence[Verdict]) -> list[str]:
    """The per-job table, then each verdict's own lines from `gate_budgets.render`."""
    headline = (
        f"== the {gate.id} gate on run {measured.run_id} ({measured.head_sha}, "
        f"{measured.conclusion}) =="
    )
    lines = [headline, f"{'job':24}{'wall':>8}{'queue':>8}{'setup':>8}{'work':>8}"]
    # Slowest first, because the top row is the one that set the gate's wall.
    lines.extend(
        f"{job.name:24}{_seconds(job.wall_seconds)}{_seconds(job.queue_seconds)}"
        f"{_seconds(job.setup_seconds)}{_seconds(job.work_seconds)}"
        for job in sorted(measured.jobs, key=lambda item: -(item.wall_seconds or 0.0))
    )
    lines.append(
        f"{'-- the gate wall':24}{_seconds(measured.wall_seconds)}"
        f"  run start to the last gating job, critical: {measured.critical_job}"
    )
    for verdict in found:
        lines.append(f"  {verdict.tier}:")
        lines.extend(f"  {line}" for line in render(verdict))
    if gate.reports_only:
        lines.append(
            f"  note: this gate reports rather than enforces under {gate.tracking_bead}"
        )
    return lines


def _geometric_mean(values: Sequence[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def render_sample(gate: CiGate, runs: Sequence[GateRun], *, today: str) -> list[str]:
    """The register block to paste, as the geometric mean of the readings and the spread.

    The mean rather than the maximum for the reason `policy.drift_ratio` gives: a record
    at the top of its band starves the stale rule by as much as it feeds the drift rule,
    and `D-472` is the entry. The spread is printed beside it because a hosted band has
    to be argued against the runner's own variance rather than a local tier's.
    """
    where = ", ".join(f"run {run.run_id} ({run.head_sha})" for run in runs)
    lines = [f"# {gate.id}: {len(runs)} readings, {where}"]
    for name in (*gate.ids, "wall"):
        present = [
            reading
            for reading in (_reading(run, name) for run in runs)
            if reading is not None and reading > 0
        ]
        if not present:
            lines.append(f"  {name}: no finished reading in these runs")
            continue
        mean = _geometric_mean(present)
        spread = max(present) / min(present)
        lines.extend(
            [
                f"- id: {name}",
                f"  measured_seconds: {mean:.1f}",
                f"  measured_on: {today}",
                f"  spread: {spread:.2f}",
                f"  # readings: {', '.join(f'{value:.0f}' for value in present)}",
            ]
        )
    return lines


def _reading(run: GateRun, name: str) -> float | None:
    """One run's wall for one declared name, where `wall` means the gate's own."""
    if name == "wall":
        return run.wall_seconds
    job = run.job(name)
    return job.wall_seconds if job else None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Hold a CI gate's hosted jobs to the ceilings in gate-budgets.yaml."
    )
    parser.add_argument("--gate", default="deep-gate", help="the gate's id in the register")
    parser.add_argument("--run-id", type=int, action="append", default=[])
    parser.add_argument("--recent", type=int, default=0, help="sample this many recent runs")
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "jlevy/squares"))
    parser.add_argument("--register", type=Path, default=BUDGETS)
    parser.add_argument("--sample", action="store_true", help="print a record from many runs")
    parser.add_argument("--dump", action="store_true", help="print the API payload read")
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="fail on a band the register's `enforcement: reporting` would merely print",
    )
    return parser


def _run_ids(arguments: argparse.Namespace, client: Client, gate: CiGate) -> list[int]:
    if arguments.run_id:
        return [int(value) for value in arguments.run_id]
    if arguments.recent:
        runs = client.recent_runs(gate.file, int(arguments.recent))
        return [int(run["id"]) for run in runs]
    live = os.environ.get("GITHUB_RUN_ID")
    if live:
        return [int(live)]
    raise GateWallError(
        "no run to measure: pass --run-id, or --recent N, or run inside a workflow"
    )


def _selected(arguments: argparse.Namespace) -> tuple[Register, CiGate]:
    """The register and the gate asked for, or the reason neither can be had."""
    try:
        register = load(arguments.register)
    except BudgetError as error:
        raise GateWallError(str(error)) from error
    gate = register.ci_gate(str(arguments.gate))
    if gate is None:
        known = ", ".join(entry.id for entry in register.ci_gates) or "none"
        raise GateWallError(f"no gate {arguments.gate!r} ({known})")
    return register, gate


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        register, gate = _selected(arguments)
    except GateWallError as error:
        print(f"check_ci_gate_walls: {error}", file=sys.stderr)
        return 2
    problems = ci_declaration_problems(register)
    for problem in problems:
        print(f"  DECLARATION: {problem}")
    client = Client(str(arguments.repo), github_token())
    try:
        policy = load_walls().policy
        identifiers = _run_ids(arguments, client, gate)
        payloads = [(client.run(run_id), client.jobs(run_id)) for run_id in identifiers]
    except (GateWallError, WallError, OSError) as error:
        print(f"check_ci_gate_walls: {error}", file=sys.stderr)
        return 2
    if arguments.dump:
        for run, jobs in payloads:
            print(json.dumps(trim(run, jobs), indent=2))
        return 0
    measured = [measure(run, jobs, gate, policy) for run, jobs in payloads]
    if arguments.sample:
        today = datetime.now(UTC).date().isoformat()
        print("\n".join(render_sample(gate, measured, today=today)))
        return 0
    failed = False
    for run in measured:
        found = verdicts(register, gate, run, enforce=bool(arguments.enforce))
        print("\n".join(render_run(gate, run, found)))
        failed = failed or any(verdict.failed for verdict in found)
    if problems:
        return 2
    return 1 if failed and arguments.enforce else 0


if __name__ == "__main__":
    raise SystemExit(main())
