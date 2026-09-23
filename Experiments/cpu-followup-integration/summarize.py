"""Summarize retained adjacent full-solver control/candidate timing batches."""

from __future__ import annotations

import json
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def describe(values: list[float]) -> dict[str, float]:
    return {
        "min": min(values),
        "median": stats.median(values),
        "max": max(values),
        "cv": stats.stdev(values) / stats.mean(values),
    }


def main() -> None:
    output: dict[str, object] = {}
    for variant in ("vectorized", "prefix"):
        for workers in (1, 16):
            paths = {
                mode: [ROOT / "raw" / f"{variant}-{mode}-w{workers}-s{i}.json"
                       for i in (1, 2, 3)]
                for mode in ("reference", "candidate")
            }
            if not all(path.exists() for series in paths.values() for path in series):
                continue
            samples = {mode: [json.loads(path.read_text()) for path in series]
                       for mode, series in paths.items()}
            metric = {}
            for mode, records in samples.items():
                metric[mode] = {
                    "wall_per_solve_seconds": describe(
                        [x["normalized_wall_seconds"] for x in records]
                    ),
                    "separation_per_solve_seconds": describe([
                        sum(run["separation_seconds"] for run in x["solves"]) / x["repeats"]
                        for x in records
                    ]),
                    "lp_per_solve_seconds": describe([
                        sum(run["lp_seconds"] for run in x["solves"]) / x["repeats"]
                        for x in records
                    ]),
                    "batch_wall_seconds": describe([x["batch_wall_seconds"] for x in records]),
                    "repeats": [x["repeats"] for x in records],
                    "raw": [str(path.relative_to(ROOT)) for path in paths[mode]],
                }
            saved = [a["normalized_wall_seconds"] - b["normalized_wall_seconds"]
                     for a, b in zip(samples["reference"], samples["candidate"], strict=True)]
            metric["paired_saved_seconds"] = describe(saved)
            metric["paired_saved_samples_seconds"] = saved
            output[f"{variant}-w{workers}"] = metric
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
