"""Check raw integration evidence against the published numerical summary."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DECISION_KEYS = ("index", "rows_held", "rows_added", "violated", "support", "objective")
STATE_KEYS = (
    "rounds", "rows", "objective", "least_covered", "stopped",
    "directions_sha256", "centres_sha256", "matrix_sha256",
    "weights_sha256", "duals_sha256", "round_decisions",
)


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def decisions(data: dict) -> list[tuple]:
    return [
        tuple(entry[key] for key in DECISION_KEYS)
        for entry in data["round_timings_exact"]
    ]


def check_endpoint(endpoint: dict) -> tuple[dict, dict]:
    runs = [read(ROOT / name) for name in endpoint["files"]]
    assert len(runs) == endpoint["runs"]
    metrics = {
        "wall_seconds": [run["row_run"]["seconds"] for run in runs],
        "separation_seconds": [run["row_run"]["separation_seconds"] for run in runs],
        "lp_seconds": [run["row_run"]["lp_seconds"] for run in runs],
        "round0_seconds": [
            run["round_timings_exact"][0]["separation_seconds"]
            + run["round_timings_exact"][0]["lp_seconds"]
            for run in runs
        ],
    }
    if endpoint["peak_parent_rss_kib"] is not None:
        metrics["peak_parent_rss_kib"] = [run["peak_parent_rss_kib"] for run in runs]
    for name, values in metrics.items():
        expected = endpoint[name]
        assert expected == {
            "min": min(values), "median": statistics.median(values), "max": max(values)
        }, name
    for run in runs:
        row = run["row_run"]
        for key in ("rounds", "rows", "objective"):
            assert row[key] == endpoint[key]
        assert row["stopped"] == endpoint["stop_reason"]
        assert run["least_covered"] == endpoint["least_covered"]
        assert decisions(run) == decisions(runs[0])
    return runs[0], {"runs": len(runs), "wall_median": endpoint["wall_seconds"]["median"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = read(ROOT / "results.json")
    checks: dict[str, bool] = {}
    stage_first: dict[int, dict] = {}
    endpoint_summary: dict[str, dict] = {}
    for stage in data["stages"]:
        index = stage["stage"]
        for workers in (1, 16):
            endpoint = stage[f"workers_{workers}"]
            if endpoint is None:
                continue
            first, summary = check_endpoint(endpoint)
            endpoint_summary[f"M{index}-w{workers}"] = summary
            if workers == 1:
                stage_first[index] = first
            else:
                checks[f"M{index}_parallel_decisions"] = (
                    decisions(first) == decisions(stage_first[index])
                )
    for index in (1, 3, 4, 5):
        checks[f"M{index}_incremental_trajectory"] = (
            decisions(stage_first[index]) == decisions(stage_first[index - 1])
        )
    states = [read(ROOT / "raw" / f"m{index}-full-state.json") for index in (2, 3, 4, 5)]
    for left, right, index in zip(states[:-1], states[1:], (3, 4, 5), strict=True):
        checks[f"M{index}_complete_state"] = all(left[key] == right[key] for key in STATE_KEYS)
    row_pair = read(ROOT / "raw/m1-full-row-equivalence.json")
    checks["M1_complete_row_comparison"] = all(row_pair["checks"].values())
    for index in (1, 2, 5):
        exact = read(ROOT / "raw" / f"m{index}-exact-rows.json")
        checks[f"M{index}_exact_rows"] = (
            exact["rows_checked"] == exact["rows"]
            and exact["centres_outside_exact_domain"] == 0
            and exact["rows_without_exact_witness"] == 0
        )
    intervals = read(ROOT / "raw/m3-interval-equivalence.json")
    checks["M3_intervals"] = all(
        intervals[key] for key in (
            "reachable_cell_sets_equal", "masses_bitwise_equal", "ordered_candidates_equal"
        )
    )
    checks["M4_cumsum_bitwise"] = read(ROOT / "raw/m4-cumsum-operation.json")["bitwise_equal"]
    selection = read(ROOT / "raw/m5-production-selector.json")
    checks["M5_stable_selector"] = selection["native_exact"] and selection["fallback_exact"]
    packaging = read(ROOT / "raw/m5-packaging.json")
    checks["M5_packaging"] = all(packaging["validation"].values())
    for workers in (1, 16):
        endpoint = data["final_validation"][f"workers_{workers}"]
        first, summary = check_endpoint(endpoint)
        endpoint_summary[f"final-w{workers}"] = summary
        checks[f"final_w{workers}_decisions"] = decisions(first) == decisions(stage_first[5])
    report = {"checks": checks, "endpoints": endpoint_summary, "passed": all(checks.values())}
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": checks}, indent=2))  # noqa: T201
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
