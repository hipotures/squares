"""Wait for one artifact from a producer running beside the current job.

GitHub Actions normally expresses an artifact dependency with ``needs:``, but that
serializes all of the consumer's setup after the producer. Browser provisioning for the
certificate page takes longer than page preparation and does not read the page. Those
jobs can start together after the scope decision, then wait at the first step that
actually needs the artifact.

This tool makes that join explicit and bounded. It polls only the named workflow run,
accepts only a non-expired artifact with the exact name, and fails immediately when the
named producer completes without success. API failures and timeouts are errors. A
consumer therefore cannot continue on a missing, stale, or failed producer artifact.

Usage, from ``packing/``::

    python -m devtools.wait_for_run_artifact \
        --repository "$GITHUB_REPOSITORY" --run-id "$GITHUB_RUN_ID" \
        --run-attempt "$GITHUB_RUN_ATTEMPT" --name prepared-page \
        --producer prepare --github-output "$GITHUB_OUTPUT" --timeout 600
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

type Api = Callable[[str], Any]
type Clock = Callable[[], float]
type Sleep = Callable[[float], None]


@dataclass(frozen=True)
class Ready:
    """The exact artifact and how many observations made it available."""

    attempts: int
    artifact_id: int


def _artifacts_path(repository: str, run_id: int) -> str:
    return f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100"


def _jobs_path(repository: str, run_id: int, run_attempt: int) -> str:
    return f"repos/{repository}/actions/runs/{run_id}/attempts/{run_attempt}/jobs?per_page=100"


def _timestamp(value: object, *, what: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError(f"{what} has no timestamp")
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise RuntimeError(f"{what} has invalid timestamp {value!r}") from error


def _artifact_from_attempt(
    document: Mapping[str, Any], *, name: str, producer_started_at: str
) -> int | None:
    started = _timestamp(producer_started_at, what="producer")
    candidates: list[int] = []
    for artifact in document.get("artifacts", []):
        if artifact.get("name") != name or artifact.get("expired") is not False:
            continue
        created = _timestamp(artifact.get("created_at"), what=f"artifact {name!r}")
        artifact_id = artifact.get("id")
        if not isinstance(artifact_id, int) or artifact_id <= 0:
            raise RuntimeError(f"artifact {name!r} has invalid id {artifact_id!r}")
        # GitHub timestamps have one-second precision.  Strictly newer avoids accepting
        # an artifact from a prior attempt that finished in the same displayed second
        # this attempt's producer started; this producer renders for many seconds, so its
        # own artifact cannot legitimately share the start timestamp.
        if created > started:
            candidates.append(artifact_id)
    if len(candidates) > 1:
        raise RuntimeError(
            f"artifact {name!r} is ambiguous in this attempt: ids {sorted(candidates)}"
        )
    return candidates[0] if candidates else None


def _producer_job(document: Mapping[str, Any], *, producer: str) -> Mapping[str, Any] | None:
    producers = [job for job in document.get("jobs", []) if job.get("name") == producer]
    if len(producers) > 1:
        raise RuntimeError(f"producer {producer!r} is ambiguous in this attempt")
    return producers[0] if producers else None


def _producer_failure(job: Mapping[str, Any] | None, *, producer: str) -> str | None:
    if job is None or job.get("status") != "completed" or job.get("conclusion") == "success":
        return None
    return f"producer {producer!r} completed without success ({job.get('conclusion')!r})"


def wait_for_artifact(
    *,
    repository: str,
    run_id: int,
    run_attempt: int,
    name: str,
    producer: str,
    timeout: float,
    interval: float,
    api: Api,
    clock: Clock = time.monotonic,
    sleep: Sleep = time.sleep,
) -> Ready:
    """Return when ``name`` is finalized, or raise on a failed or bounded-out join."""
    if timeout < 0:
        raise ValueError("timeout must be non-negative")
    if interval <= 0:
        raise ValueError("interval must be positive")
    if run_attempt < 1:
        raise ValueError("run_attempt must be positive")
    deadline = clock() + timeout
    attempts = 0
    while True:
        attempts += 1
        jobs = api(_jobs_path(repository, run_id, run_attempt))
        job = _producer_job(jobs, producer=producer)
        failure = _producer_failure(job, producer=producer)
        if failure is not None:
            raise RuntimeError(failure)
        started_at = None if job is None else job.get("started_at")
        if started_at is not None:
            artifacts = api(_artifacts_path(repository, run_id))
            artifact_id = _artifact_from_attempt(
                artifacts, name=name, producer_started_at=str(started_at)
            )
            if artifact_id is not None:
                return Ready(attempts, artifact_id)

        now = clock()
        if now >= deadline:
            raise TimeoutError(
                f"artifact {name!r} was not available from {producer!r} "
                f"after {timeout:g} seconds"
            )
        sleep(min(interval, deadline - now))


def _gh_api(path: str) -> Any:
    completed = subprocess.run(
        ("gh", "api", path), capture_output=True, text=True, check=False, timeout=60
    )
    if completed.returncode != 0:
        raise OSError(
            completed.stderr.strip() or f"gh api {path} exited {completed.returncode}"
        )
    return json.loads(completed.stdout)


def main(argv: Sequence[str] | None = None, *, api: Api = _gh_api) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m devtools.wait_for_run_artifact",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    _ = parser.add_argument("--repository", required=True, help="OWNER/NAME")
    _ = parser.add_argument("--run-id", required=True, type=int)
    _ = parser.add_argument("--run-attempt", required=True, type=int)
    _ = parser.add_argument("--name", required=True)
    _ = parser.add_argument("--producer", required=True)
    _ = parser.add_argument("--github-output", type=Path)
    _ = parser.add_argument("--timeout", type=float, default=600)
    _ = parser.add_argument("--interval", type=float, default=5)
    arguments = parser.parse_args(argv)
    try:
        ready = wait_for_artifact(
            repository=str(arguments.repository),
            run_id=int(arguments.run_id),
            run_attempt=int(arguments.run_attempt),
            name=str(arguments.name),
            producer=str(arguments.producer),
            timeout=float(arguments.timeout),
            interval=float(arguments.interval),
            api=api,
        )
    except (OSError, TypeError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"artifact join failed: {error}", file=sys.stderr)
        return 1
    if arguments.github_output is not None:
        with arguments.github_output.open("a", encoding="utf-8") as output:
            _ = output.write(f"artifact_id={ready.artifact_id}\n")
    print(
        f"artifact {arguments.name!r} id {ready.artifact_id} is ready after "
        f"{ready.attempts} observation(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
