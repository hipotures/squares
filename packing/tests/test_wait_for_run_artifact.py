"""The concurrent Actions artifact join is exact, bounded, and fail-closed."""

from __future__ import annotations

from typing import Any

import pytest

from devtools import wait_for_run_artifact as tool

REPOSITORY = "jlevy/squares"
RUN_ID = 77


def _artifact(*, name: str = "prepared-page", expired: bool = False) -> dict[str, Any]:
    return {"name": name, "expired": expired}


def _job(
    *, name: str = "prepare", status: str = "in_progress", conclusion: str | None = None
) -> dict[str, Any]:
    return {"name": name, "status": status, "conclusion": conclusion}


class Responses:
    def __init__(
        self,
        artifacts: list[list[dict[str, Any]]],
        jobs: list[list[dict[str, Any]]] | None = None,
    ) -> None:
        self.artifacts = iter(artifacts)
        self.jobs = iter(jobs or [[_job()] for _ in artifacts])
        self.paths: list[str] = []

    def __call__(self, path: str) -> dict[str, Any]:
        self.paths.append(path)
        if "/artifacts?" in path:
            return {"artifacts": next(self.artifacts)}
        assert "/jobs?" in path
        return {"jobs": next(self.jobs)}


def wait(api: tool.Api, **overrides: Any) -> tool.Ready:
    clock_values = iter(overrides.pop("clock_values", [0.0, 0.0]))
    arguments = {"timeout": 10, "interval": 1, **overrides}
    return tool.wait_for_artifact(
        repository=REPOSITORY,
        run_id=RUN_ID,
        name="prepared-page",
        producer="prepare",
        api=api,
        clock=lambda: next(clock_values),
        sleep=lambda _seconds: None,
        **arguments,
    )


def test_an_exact_nonexpired_artifact_is_ready_without_reading_the_jobs() -> None:
    api = Responses([[_artifact()]])
    assert wait(api).attempts == 1
    assert api.paths == [f"repos/{REPOSITORY}/actions/runs/{RUN_ID}/artifacts?per_page=100"]


def test_an_expired_or_differently_named_artifact_is_not_accepted() -> None:
    api = Responses(
        [[_artifact(expired=True), _artifact(name="another")]],
        [[_job(status="completed", conclusion="failure")]],
    )
    with pytest.raises(RuntimeError, match="completed without success"):
        wait(api)


def test_the_join_polls_until_the_artifact_is_finalized() -> None:
    api = Responses([[], [_artifact()]])
    assert wait(api, clock_values=[0.0, 0.0, 1.0]).attempts == 2
    assert sum("/artifacts?" in path for path in api.paths) == 2
    assert sum("/jobs?" in path for path in api.paths) == 1


def test_a_failed_producer_refuses_immediately() -> None:
    api = Responses([[]], [[_job(status="completed", conclusion="cancelled")]])
    with pytest.raises(RuntimeError, match="'cancelled'"):
        wait(api)


def test_a_missing_artifact_times_out_at_the_declared_boundary() -> None:
    api = Responses([[], []])
    with pytest.raises(TimeoutError, match="after 10 seconds"):
        wait(api, clock_values=[0.0, 0.0, 10.0])


def test_api_errors_and_invalid_bounds_fail_closed() -> None:
    def broken(_path: str) -> Any:
        raise OSError("HTTP 403")

    with pytest.raises(OSError, match="403"):
        wait(broken)
    with pytest.raises(ValueError, match="timeout"):
        wait(broken, timeout=-1)
    with pytest.raises(ValueError, match="interval"):
        wait(broken, interval=0)


def test_main_reports_api_failure_as_a_failed_join(capsys: pytest.CaptureFixture[str]) -> None:
    def broken(_path: str) -> Any:
        raise OSError("API unavailable")

    assert (
        tool.main(
            [
                "--repository",
                REPOSITORY,
                "--run-id",
                str(RUN_ID),
                "--name",
                "prepared-page",
                "--producer",
                "prepare",
                "--timeout",
                "0",
            ],
            api=broken,
        )
        == 1
    )
    assert "artifact join failed: API unavailable" in capsys.readouterr().err
