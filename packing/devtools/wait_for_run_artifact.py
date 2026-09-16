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
        --name prepared-page --producer prepare --timeout 600
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

type Api = Callable[[str], Any]
type Clock = Callable[[], float]
type Sleep = Callable[[float], None]


@dataclass(frozen=True)
class Ready:
    """How many API observations were needed before the artifact became available."""

    attempts: int


def _artifacts_path(repository: str, run_id: int) -> str:
    return f"repos/{repository}/actions/runs/{run_id}/artifacts?per_page=100"


def _jobs_path(repository: str, run_id: int) -> str:
    return f"repos/{repository}/actions/runs/{run_id}/jobs?per_page=100"


def _artifact_ready(document: Mapping[str, Any], *, name: str) -> bool:
    return any(
        artifact.get("name") == name and artifact.get("expired") is False
        for artifact in document.get("artifacts", [])
    )


def _producer_failure(document: Mapping[str, Any], *, producer: str) -> str | None:
    producers = [job for job in document.get("jobs", []) if job.get("name") == producer]
    failed = [
        job
        for job in producers
        if job.get("status") == "completed" and job.get("conclusion") != "success"
    ]
    if not failed:
        return None
    conclusions = ", ".join(repr(job.get("conclusion")) for job in failed)
    return f"producer {producer!r} completed without success ({conclusions})"


def wait_for_artifact(
    *,
    repository: str,
    run_id: int,
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
    deadline = clock() + timeout
    attempts = 0
    while True:
        attempts += 1
        artifacts = api(_artifacts_path(repository, run_id))
        if _artifact_ready(artifacts, name=name):
            return Ready(attempts)

        jobs = api(_jobs_path(repository, run_id))
        failure = _producer_failure(jobs, producer=producer)
        if failure is not None:
            raise RuntimeError(failure)

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
    _ = parser.add_argument("--name", required=True)
    _ = parser.add_argument("--producer", required=True)
    _ = parser.add_argument("--timeout", type=float, default=600)
    _ = parser.add_argument("--interval", type=float, default=5)
    arguments = parser.parse_args(argv)
    try:
        ready = wait_for_artifact(
            repository=str(arguments.repository),
            run_id=int(arguments.run_id),
            name=str(arguments.name),
            producer=str(arguments.producer),
            timeout=float(arguments.timeout),
            interval=float(arguments.interval),
            api=api,
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"artifact join failed: {error}", file=sys.stderr)
        return 1
    print(f"artifact {arguments.name!r} is ready after {ready.attempts} observation(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
