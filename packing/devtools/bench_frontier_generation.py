"""Paired real-generator work comparison, including broker CPU and startup.

This benchmark uses identical jobs in the sequential and shared schedules, not
sleep tasks. It reports generation results only, never a mathematical proof.
Run from packing/; all artifacts remain under the explicitly supplied root.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

from devtools.frontier_generation_queue import run_jobs
from devtools.frontier_io import atomic_json, read_json


def make_jobs(root: Path, groups: int, grids: str, steps: int, rows: int) -> list[dict]:
    jobs = []
    for number in range(groups):
        for strategy in ("baseline", "centre", "pricing"):
            directory = root / f"trial-{number:03d}-{strategy}"
            directory.mkdir(parents=True)
            command = [sys.executable, "-m", "devtools.run_fractional_colgen",
                       "--n", "12", "--side", "99/25", "--grid-counts", grids,
                       "--direction-steps", str(steps), "--column-rounds", "1",
                       "--max-rounds", str(rows), "--scale", "1600000",
                       "--seed-map", "centre" if strategy == "centre" else "scale",
                       "--support-cap", "128" if strategy == "pricing" else "32",
                       "--json", str(directory / "result.json"),
                       "--freeze", str(directory / "candidate.unverified.json"),
                       "--raw-weights", str(directory / "raw-lp.json"),
                       "--log", str(directory / "column.log"),
                       "--row-log", str(directory / "rows.log"),
                       "--phase-log", str(directory / "phase.log")]
            jobs.append({"id": directory.name, "command": command,
                         "output": str(directory / "stdout.log")})
    return jobs


def result_signature(job: dict) -> dict:
    result = read_json(Path(job["output"]).parent / "result.json")
    return {key: result.get(key) for key in ("converged", "stopped", "objective", "least_covered", "total_mass", "atoms")} | {
        "rounds": [{k: v for k, v in row.items() if k != "seconds"} for row in result["rounds"]]}


def run_mode(root: Path, shared: bool, groups: int, args) -> dict:
    jobs = make_jobs(root, groups, args.grid_counts, args.steps, args.row_rounds)
    reports = []
    started = time.monotonic()
    if shared:
        # Keep exactly three independent strategies admitted at once. A large
        # benchmark job list must not hide serial phases by over-admitting LPs.
        for offset in range(0, len(jobs), 3):
            reports.append(run_jobs(jobs[offset:offset + 3], root / f"broker-{offset}", slots=args.workers,
                                    stage_seconds=args.stage_seconds, no_progress_seconds=0))
    else:
        for number, job in enumerate(jobs):
            reports.append(run_jobs([job], root / f"broker-{number}", slots=args.workers,
                                    stage_seconds=args.stage_seconds, no_progress_seconds=0))
    elapsed = time.monotonic() - started
    if any(job["returncode"] for report in reports for job in report["jobs"].values()):
        raise RuntimeError("a benchmark generation job failed; inspect its durable receipt")
    cpu = sum(report["metrics"]["coordinator_cpu_seconds"] for report in reports)
    result = {"wall_seconds": elapsed, "coordinator_cpu_seconds": cpu,
              "coordinator_core_percent": cpu / elapsed * 100,
              "worker_cpu_seconds": sum(r["metrics"]["worker_cpu_seconds"] for r in reports),
              "driver_cpu_seconds": sum(r["metrics"]["driver_cpu_seconds"] for r in reports),
              "round_requests": sum(r["metrics"]["round_requests"] for r in reports),
              "chunks_completed": sum(r["metrics"]["chunks_completed"] for r in reports),
              "max_busy": max(r["metrics"]["max_busy"] for r in reports),
              "jobs": len(jobs), "signatures": [result_signature(job) for job in jobs]}
    atomic_json(root / "measurement.json", result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=12)
    parser.add_argument("--grid-counts", default="7,9,11")
    parser.add_argument("--steps", type=int, default=48)
    parser.add_argument("--row-rounds", type=int, default=6)
    parser.add_argument("--stage-seconds", type=float, default=60)
    args = parser.parse_args(argv)
    if args.root.exists() or args.workers < 1 or args.samples < 1 or args.target_seconds < 10:
        parser.error("use a fresh root, positive workers/samples and target-seconds >=10")
    args.root.mkdir(parents=True)
    pilot = run_mode(args.root / "pilot", True, 1, args)
    groups = max(1, int(args.target_seconds / max(pilot["wall_seconds"], 0.01)) + 1)
    pairs = []
    for sample in range(args.samples):
        pair = {}
        for mode in (("sequential", "shared") if sample % 2 == 0 else ("shared", "sequential")):
            pair[mode] = run_mode(args.root / f"sample-{sample + 1}-{mode}", mode == "shared", groups, args)
        if pair["shared"]["signatures"] != pair["sequential"]["signatures"]:
            raise RuntimeError("schedule changed a real generator result")
        pair["speedup"] = pair["sequential"]["wall_seconds"] / pair["shared"]["wall_seconds"]
        pairs.append(pair)
        print(f"[{int(time.time())}] sample={sample + 1} sequential={pair['sequential']['wall_seconds']:.3f}s "
              f"shared={pair['shared']['wall_seconds']:.3f}s speedup={pair['speedup']:.3f} "
              f"coordinator={pair['shared']['coordinator_core_percent']:.2f}%", flush=True)
    result = {"scope": "real bounded generator jobs; includes process startup; not a live campaign benchmark",
              "workers": args.workers, "groups_per_sample": groups, "pairs": pairs,
              "median_speedup": statistics.median(p["speedup"] for p in pairs),
              "minimum_sample_seconds": min(p[m]["wall_seconds"] for p in pairs for m in ("shared", "sequential")),
              "correctness": "identical per-job mathematical summaries and ordered round decisions"}
    atomic_json(args.root / "results.json", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
