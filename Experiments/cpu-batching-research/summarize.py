"""Summarize three long independent A/B/C replay samples per worker count."""

from __future__ import annotations

import json
import statistics as stats
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def describe(values: list[float]) -> dict[str, float]:
    mean = stats.mean(values)
    return {
        "min": min(values), "median": stats.median(values), "max": max(values),
        "cv": stats.stdev(values) / mean if mean else 0.0,
    }


def main() -> None:
    output: dict[str, object] = {
        "cpu_accepted_sha": "2a2efa39edb179128184f19d6a4235a6bbcaebcc",
        "profiles": {},
    }
    profiles = output["profiles"]
    assert isinstance(profiles, dict)
    for variant in ("A", "B", "C", "D"):
        for workers in (1, 2, 4, 8, 16):
            paths = [ROOT / "raw" / f"{variant}-w{workers}-s{sample}.json"
                     for sample in (1, 2, 3)]
            if not all(path.exists() for path in paths):
                continue
            records = [json.loads(path.read_text()) for path in paths]
            metrics = {}
            for metric in (
                "batch_wall_seconds", "separation_wall_seconds_per_replay",
                "worker_cpu_seconds_per_replay", "effective_cores",
                "worker_minor_faults_per_replay", "worker_major_faults_per_replay",
                "scratch_allocated_bytes_per_replay", "logical_grid_bytes_per_replay",
                "logical_compact_bytes_per_replay",
            ):
                metrics[metric] = describe([record[metric] for record in records])
            metrics["raw"] = [str(path.relative_to(ROOT)) for path in paths]
            metrics["repeats"] = [record["repeats"] for record in records]
            profiles[f"{variant}-w{workers}"] = metrics
    for variant, workers in (("B", 16), ("A", 8), ("B", 8), ("C", 8)):
        long_paths = [ROOT / "raw" / f"{variant}-w{workers}-long-s{sample}.json"
                      for sample in (1, 2, 3)]
        if not all(path.exists() for path in long_paths):
            continue
        records = [json.loads(path.read_text()) for path in long_paths]
        profiles[f"{variant}-long-w{workers}"] = {
            metric: describe([record[metric] for record in records])
            for metric in (
                "batch_wall_seconds", "separation_wall_seconds_per_replay",
                "worker_cpu_seconds_per_replay", "effective_cores",
                "worker_minor_faults_per_replay", "worker_major_faults_per_replay",
            )
        }
        profiles[f"{variant}-long-w{workers}"]["raw"] = [
            str(path.relative_to(ROOT)) for path in long_paths
        ]
    for variant in ("A", "B", "C", "D"):
        baseline = profiles.get(f"{variant}-w1")
        if baseline is None:
            continue
        serial_wall = baseline["separation_wall_seconds_per_replay"]["median"]
        serial_cpu = baseline["worker_cpu_seconds_per_replay"]["median"]
        for workers in (1, 2, 4, 8, 16):
            entry = profiles.get(f"{variant}-w{workers}")
            if entry is None:
                continue
            wall = entry["separation_wall_seconds_per_replay"]["median"]
            cpu = entry["worker_cpu_seconds_per_replay"]["median"]
            entry["speedup_vs_one"] = serial_wall / wall
            entry["parallel_efficiency"] = serial_wall / wall / workers
            entry["cpu_inflation"] = cpu / serial_cpu
    full_dir = ROOT / "raw/full-solver"
    full_output = {}
    for tag in ("", "-long"):
        full = {}
        for mode in ("reference", "candidate"):
            paths = [full_dir / f"{mode}{tag}-s{i}.json" for i in (1, 2, 3)]
            if not all(path.exists() for path in paths):
                continue
            records = [json.loads(path.read_text()) for path in paths]
            full[mode] = {
                metric: describe([record[metric] for record in records])
                for metric in ("batch_wall_seconds", "wall_per_solve_seconds",
                               "separation_per_solve_seconds", "lp_per_solve_seconds")
            }
            full[mode]["raw"] = [str(path.relative_to(ROOT)) for path in paths]
        if len(full) == 2:
            a = [json.loads((full_dir / f"reference{tag}-s{i}.json").read_text())
                 for i in (1, 2, 3)]
            b = [json.loads((full_dir / f"candidate{tag}-s{i}.json").read_text())
                 for i in (1, 2, 3)]
            full["paired_saved_seconds"] = describe([
                x["wall_per_solve_seconds"] - y["wall_per_solve_seconds"]
                for x, y in zip(a, b, strict=True)
            ])
            full["paired_saved_samples_seconds"] = [
                x["wall_per_solve_seconds"] - y["wall_per_solve_seconds"]
                for x, y in zip(a, b, strict=True)
            ]
            full_output["long" if tag else "initial"] = full
    output["full_solver_chunk_only"] = full_output
    (ROOT / "results.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
