#!/usr/bin/env python3
"""Coarse-process scaling harness for the native sqtopology engine.

This script is orchestration only. It never generates, serializes, or scores individual
topology candidates. Each child receives one deterministic first-level shard and performs
all generation, canonicalization, and local deduplication in native code.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path


def parse_workers(raw: str) -> list[int]:
    values = [int(item) for item in raw.split(",") if item.strip()]
    if not values or any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("workers must be positive comma-separated integers")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--fixture", default="grid-4x4-minus-one")
    parser.add_argument("--workers", type=parse_workers, default=parse_workers("1,2,4,8,16"))
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--max-candidates", type=int, default=0)
    parser.add_argument("--max-unique", type=int, default=200_000)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--max-additions", type=int, default=256)
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args()


def run_width(args: argparse.Namespace, workers: int) -> dict[str, object]:
    processes: list[subprocess.Popen[str]] = []
    started = time.perf_counter()

    for shard in range(workers):
        command = [
            str(args.binary),
            "search",
            args.fixture,
            "--seconds",
            str(args.seconds),
            "--max-candidates",
            str(args.max_candidates),
            "--max-unique",
            str(args.max_unique),
            "--max-depth",
            str(args.max_depth),
            "--max-additions",
            str(args.max_additions),
            "--shard",
            f"{shard}/{workers}",
            "--json",
        ]
        processes.append(
            subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        )

    summaries: list[dict[str, object]] = []
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                f"sqtopology worker failed with {process.returncode}:\n{stderr}"
            )
        summaries.append(json.loads(stdout))

    external_wall = time.perf_counter() - started
    raw = sum(int(item["raw_candidates"]) for item in summaries)
    canonicalizations = sum(int(item["canonicalizations"]) for item in summaries)
    duplicates = sum(int(item["duplicates"]) for item in summaries)
    local_unique_sum = sum(int(item["unique_states"]) for item in summaries)
    max_worker_wall = max(float(item["wall_seconds"]) for item in summaries)

    return {
        "workers": workers,
        "external_wall_seconds": external_wall,
        "max_worker_wall_seconds": max_worker_wall,
        "raw_candidates": raw,
        "canonicalizations": canonicalizations,
        "duplicates": duplicates,
        "local_unique_sum": local_unique_sum,
        "candidates_per_second": raw / external_wall if external_wall else 0.0,
        "worker_summaries": summaries,
    }


def main() -> int:
    args = parse_args()
    if not args.binary.is_file():
        raise SystemExit(f"binary does not exist: {args.binary}")
    if args.seconds <= 0:
        raise SystemExit("--seconds must be positive for scaling measurements")

    rows: list[dict[str, object]] = []
    baseline: float | None = None

    print(
        f"{'workers':>7} {'cand/s':>14} {'speedup':>9} {'eff%':>8} "
        f"{'candidates':>12} {'wall_s':>9} {'local_unique':>13}"
    )
    for workers in args.workers:
        row = run_width(args, workers)
        rows.append(row)
        throughput = float(row["candidates_per_second"])
        if baseline is None:
            baseline = throughput
        speedup = throughput / baseline if baseline else 0.0
        efficiency = 100.0 * speedup / workers
        print(
            f"{workers:7d} {throughput:14.1f} {speedup:9.2f} {efficiency:8.1f} "
            f"{int(row['raw_candidates']):12d} "
            f"{float(row['external_wall_seconds']):9.3f} "
            f"{int(row['local_unique_sum']):13d}"
        )

    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps(
                {
                    "schema": "sqtopology.scaling-report.v1",
                    "fixture": args.fixture,
                    "seconds": args.seconds,
                    "rows": rows,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
