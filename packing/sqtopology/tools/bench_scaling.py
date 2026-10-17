#!/usr/bin/env python3
"""Coarse-process scaling harness for the native sqtopology engine.

This script is orchestration only. It never generates, serializes, or scores individual
topology candidates. Each child receives one deterministic first-level shard and performs
all generation, canonicalization, and local deduplication in native code.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


BACKENDS = ("dense-nauty", "sparse-nauty", "traces")


def parse_workers(raw: str) -> list[int]:
    values = [int(item) for item in raw.split(",") if item.strip()]
    if not values or any(value < 1 for value in values):
        raise argparse.ArgumentTypeError("workers must be positive comma-separated integers")
    return values


def parse_cpus(raw: str) -> list[int]:
    values = [int(item) for item in raw.split(",") if item.strip()]
    if not values or any(value < 0 for value in values) or len(set(values)) != len(values):
        raise argparse.ArgumentTypeError("cpus must be distinct non-negative comma-separated integers")
    return values


def parse_backends(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("backends must not be empty")
    unknown = [value for value in values if value not in BACKENDS]
    if unknown:
        raise argparse.ArgumentTypeError(
            "unknown backend(s): "
            + ", ".join(unknown)
            + "; expected dense-nauty,sparse-nauty,traces"
        )
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--fixture", default="grid-4x4-minus-one")
    parser.add_argument("--workers", type=parse_workers, default=parse_workers("1,2,4,8,16"))
    parser.add_argument(
        "--backends",
        type=parse_backends,
        default=parse_backends("traces"),
        help="comma-separated canonical backends: dense-nauty,sparse-nauty,traces",
    )
    parser.add_argument("--seconds", type=float, default=10.0)
    parser.add_argument("--pin-workers", action="store_true", help="pin shards to available CPUs in order")
    parser.add_argument("--cpus", type=parse_cpus, help="CPU order for pinning; implies --pin-workers")
    parser.add_argument("--max-candidates", type=int, default=0)
    parser.add_argument("--max-unique", type=int, default=200_000)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--max-additions", type=int, default=256)
    parser.add_argument(
        "--profile-canonical",
        action="store_true",
        help="microprofile the internal canonicalization stages in native workers",
    )
    parser.add_argument("--json-report", type=Path)
    return parser.parse_args()


def summed(summaries: list[dict[str, object]], key: str) -> float:
    return sum(float(item.get(key, 0.0)) for item in summaries)


def run_width(
    args: argparse.Namespace,
    backend: str,
    workers: int,
) -> dict[str, object]:
    processes: list[subprocess.Popen[str]] = []
    cpus = None
    if args.pin_workers or args.cpus is not None:
        available = sorted(os.sched_getaffinity(0))
        cpus = args.cpus if args.cpus is not None else available
        if any(cpu not in available for cpu in cpus):
            raise ValueError(f"requested CPU outside allowed affinity: {available}")
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
            "--canonical-backend",
            backend,
            "--shard",
            f"{shard}/{workers}",
            "--json",
        ]
        if args.profile_canonical:
            command.append("--profile-canonical")

        processes.append(
            subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=(lambda cpu=cpus[shard % len(cpus)]: os.sched_setaffinity(0, {cpu}))
                if cpus is not None else None,
            )
        )

    summaries: list[dict[str, object]] = []
    for process in processes:
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(
                f"sqtopology worker failed with {process.returncode} "
                f"for backend {backend}:\n{stderr}"
            )
        summary = json.loads(stdout)
        if summary.get("canonical_backend") != backend:
            raise RuntimeError(
                "worker reported unexpected canonical backend: "
                f"{summary.get('canonical_backend')!r}, expected {backend!r}"
            )
        summaries.append(summary)

    external_wall = time.perf_counter() - started
    raw = sum(int(item["raw_candidates"]) for item in summaries)
    valid = sum(int(item["valid_candidates"]) for item in summaries)
    canonicalizations = sum(int(item["canonicalizations"]) for item in summaries)
    duplicates = sum(int(item["duplicates"]) for item in summaries)
    local_unique_sum = sum(int(item["unique_states"]) for item in summaries)
    max_worker_wall = max(float(item["wall_seconds"]) for item in summaries)

    return {
        "backend": backend,
        "workers": workers,
        "cpu_affinity": [cpus[shard % len(cpus)] for shard in range(workers)] if cpus is not None else None,
        "external_wall_seconds": external_wall,
        "max_worker_wall_seconds": max_worker_wall,
        "min_worker_wall_seconds": min(float(item["wall_seconds"]) for item in summaries),
        "raw_candidates": raw,
        "valid_candidates": valid,
        "canonicalizations": canonicalizations,
        "duplicates": duplicates,
        "local_unique_sum": local_unique_sum,
        "candidates_per_second": raw / external_wall if external_wall else 0.0,
        "canonical_profiled_calls": sum(
            int(item.get("canonical_profiled_calls", 0)) for item in summaries
        ),
        "total_canonical_key_bytes": sum(
            int(item.get("total_canonical_key_bytes", 0)) for item in summaries
        ),
        "stored_canonical_key_bytes": sum(
            int(item.get("stored_canonical_key_bytes", 0)) for item in summaries
        ),
        **{
            key: summed(summaries, key)
            for key in (
                "wall_seconds", "generation_seconds", "validation_seconds",
                "graph_conversion_seconds", "canonicalization_seconds",
                "dedup_seconds", "unattributed_seconds", "first_level_selected",
                "total_candidate_contacts", "total_incidence_vertices",
                "total_incidence_edges", "user_cpu_seconds", "system_cpu_seconds",
                "minor_page_faults", "major_page_faults", "voluntary_context_switches",
                "involuntary_context_switches",
            )
        },
        "canonical_input_build_seconds": summed(
            summaries, "canonical_input_build_seconds"
        ),
        "canonical_partition_seconds": summed(
            summaries, "canonical_partition_seconds"
        ),
        "canonical_engine_seconds": summed(
            summaries, "canonical_engine_seconds"
        ),
        "canonical_output_prepare_seconds": summed(
            summaries, "canonical_output_prepare_seconds"
        ),
        "canonical_key_build_seconds": summed(
            summaries, "canonical_key_build_seconds"
        ),
        "canonical_extraction_seconds": summed(
            summaries, "canonical_extraction_seconds"
        ),
        "canonical_encoding_seconds": summed(
            summaries, "canonical_encoding_seconds"
        ),
        "canonical_hash_seconds": summed(summaries, "canonical_hash_seconds"),
        "canonical_profile_other_seconds": summed(
            summaries, "canonical_profile_other_seconds"
        ),
        "sum_worker_peak_rss_kib": summed(summaries, "peak_rss_kib"),
        "max_worker_peak_rss_kib": max(int(item.get("peak_rss_kib", 0)) for item in summaries),
        "sum_peak_frontier_states": summed(summaries, "peak_frontier_states"),
        "max_worker_cpu_gap_seconds": max(
            max(0.0, float(item["wall_seconds"]) - float(item.get("user_cpu_seconds", 0.0))
                - float(item.get("system_cpu_seconds", 0.0)))
            for item in summaries
        ) if any("user_cpu_seconds" in item for item in summaries) else None,
        "worker_summaries": summaries,
    }


def print_scaling_table(rows: list[dict[str, object]]) -> None:
    baseline: float | None = None

    print(
        f"{'workers':>7} {'cand/s':>14} {'speedup':>9} {'eff%':>8} "
        f"{'candidates':>12} {'wall_s':>9} {'local_unique':>13}"
    )
    for row in rows:
        throughput = float(row["candidates_per_second"])
        workers = int(row["workers"])
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


def print_stage_profile(rows: list[dict[str, object]]) -> None:
    print()
    print("search stages (microseconds per raw candidate; summed worker time)")
    fields = (
        ("generation", "generation_seconds"),
        ("validation", "validation_seconds"),
        ("graph", "graph_conversion_seconds"),
        ("canonical", "canonicalization_seconds"),
        ("dedup", "dedup_seconds"),
        ("other", "unattributed_seconds"),
    )
    print(f"{'workers':>7}" + "".join(f"{label:>12}" for label, _ in fields) + f"{'cpu/wall%':>12}")
    for row in rows:
        scale = 1_000_000.0 / int(row["raw_candidates"]) if row["raw_candidates"] else 0.0
        cpu = float(row.get("user_cpu_seconds", 0.0)) + float(row.get("system_cpu_seconds", 0.0))
        cpu_text = f"{100.0 * cpu / float(row['wall_seconds']):12.1f}" if cpu else f"{'n/a':>12}"
        print(f"{int(row['workers']):7d}" + "".join(
            f"{float(row[key]) * scale:12.2f}" for _, key in fields
        ) + cpu_text)


def print_canonical_profile(rows: list[dict[str, object]]) -> None:
    print()
    print("canonical microprofile (microseconds per profiled canonicalization)")
    print(
        f"{'workers':>7} {'input':>9} {'partition':>10} {'engine':>9} "
        f"{'output':>9} {'keybuild':>10} {'hash':>8} {'other':>8} {'total':>9}"
    )

    for row in rows:
        calls = int(row["canonical_profiled_calls"])
        if calls == 0:
            continue

        scale = 1_000_000.0 / calls
        input_build = float(row["canonical_input_build_seconds"]) * scale
        partition = float(row["canonical_partition_seconds"]) * scale
        engine = float(row["canonical_engine_seconds"]) * scale
        output = float(row["canonical_output_prepare_seconds"]) * scale
        key_build = float(row["canonical_key_build_seconds"]) * scale
        hash_time = float(row["canonical_hash_seconds"]) * scale
        other = float(row["canonical_profile_other_seconds"]) * scale
        total = float(row["canonicalization_seconds"]) * scale

        print(
            f"{int(row['workers']):7d} {input_build:9.2f} {partition:10.2f} "
            f"{engine:9.2f} {output:9.2f} {key_build:10.2f} "
            f"{hash_time:8.2f} {other:8.2f} {total:9.2f}"
        )


def print_key_footprint(rows: list[dict[str, object]]) -> None:
    print()
    print("exact canonical-key footprint")
    print(
        f"{'workers':>7} {'avg_key_B':>12} {'stored_MiB':>12} "
        f"{'unique':>12} {'RSS_sum_MiB':>13}"
    )
    for row in rows:
        valid = int(row["valid_candidates"])
        total_bytes = int(row["total_canonical_key_bytes"])
        stored_bytes = int(row["stored_canonical_key_bytes"])
        avg_key = total_bytes / valid if valid else 0.0
        stored_mib = stored_bytes / (1024.0 * 1024.0)
        print(
            f"{int(row['workers']):7d} {avg_key:12.1f} {stored_mib:12.1f} "
            f"{int(row['local_unique_sum']):12d} "
            f"{float(row['sum_worker_peak_rss_kib']) / 1024.0:13.1f}"
        )


def print_backend_comparison(rows: list[dict[str, object]]) -> None:
    if len({str(row["backend"]) for row in rows}) < 2:
        return

    dense_by_workers = {
        int(row["workers"]): float(row["candidates_per_second"])
        for row in rows
        if row["backend"] == "dense-nauty"
    }

    print()
    print("backend comparison")
    print(
        f"{'backend':>13} {'workers':>7} {'cand/s':>14} {'vs-dense':>10}"
    )
    for row in rows:
        workers = int(row["workers"])
        throughput = float(row["candidates_per_second"])
        dense = dense_by_workers.get(workers)
        relative = throughput / dense if dense else 0.0
        relative_text = f"{relative:9.3f}x" if dense else "       n/a"
        print(
            f"{str(row['backend']):>13} {workers:7d} "
            f"{throughput:14.1f} {relative_text:>10}"
        )


def main() -> int:
    args = parse_args()
    if not args.binary.is_file():
        raise SystemExit(f"binary does not exist: {args.binary}")
    if args.seconds <= 0:
        raise SystemExit("--seconds must be positive for scaling measurements")

    rows: list[dict[str, object]] = []

    for backend in args.backends:
        print()
        print(f"backend: {backend}")
        backend_rows: list[dict[str, object]] = []
        for workers in args.workers:
            row = run_width(args, backend, workers)
            backend_rows.append(row)
            rows.append(row)

        print_scaling_table(backend_rows)
        print_stage_profile(backend_rows)
        print_key_footprint(backend_rows)
        if args.profile_canonical:
            print_canonical_profile(backend_rows)

    print_backend_comparison(rows)

    if args.json_report is not None:
        args.json_report.parent.mkdir(parents=True, exist_ok=True)
        args.json_report.write_text(
            json.dumps(
                {
                    "schema": "sqtopology.scaling-report.v6",
                    "fixture": args.fixture,
                    "seconds": args.seconds,
                    "profile_canonical": args.profile_canonical,
                    "max_candidates": args.max_candidates,
                    "max_unique": args.max_unique,
                    "max_depth": args.max_depth,
                    "max_additions": args.max_additions,
                    "pin_workers": args.pin_workers or args.cpus is not None,
                    "cpus": args.cpus,
                    "backends": args.backends,
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
