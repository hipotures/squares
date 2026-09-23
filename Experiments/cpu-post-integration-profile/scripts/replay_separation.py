"""Long, in-memory replay of all 23 current-main separation rounds."""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.colgen import Rows, _direction_task
from sqpack.fractional.generate import direction_net

ROOT = Path(__file__).resolve().parents[1]
CLOCK_TICKS = os.sysconf("SC_CLK_TCK")


def proc_cpu(pid: int) -> tuple[float, int, int]:
    """User+system CPU, minor faults, resident pages from Linux procfs."""
    stat = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    # The remaining fields start at field 3 (state).
    return (
        (int(stat[11]) + int(stat[12])) / CLOCK_TICKS,
        int(stat[7]),
        int(stat[21]),
    )


def load() -> dict[str, object]:
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "loadavg": os.getloadavg(),
        "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
    }


def replay(
    weights: np.ndarray, points: np.ndarray, membership: np.ndarray,
    directions: tuple, outer: float, side: float,
    pool: ProcessPoolExecutor | None,
    *, task_function=_direction_task, profiled: bool = False,
) -> dict[str, object]:
    rows = Rows()
    worker_wait = parent_process = dispatch = weight_setup = 0.0
    round_times: list[dict[str, float | int]] = []
    worker_metrics: dict[str, float] = {}
    worker_tasks: dict[str, int] = {}
    whole_start = time.perf_counter()
    for round_index, orbit_weights in enumerate(weights):
        round_start = time.perf_counter()
        wait_at_start, process_at_start, dispatch_at_start = (
            worker_wait, parent_process, dispatch
        )
        task_records: list[dict[str, float | int]] = []
        t = time.perf_counter()
        site_weights = orbit_weights[membership]
        weight_setup += time.perf_counter() - t
        if pool is None:
            found = (
                task_function((points, site_weights, direction, outer, side, 3, None))
                for direction in directions
            )
        else:
            tasks = (
                (points, site_weights, direction, outer, side, 3, None)
                for direction in directions
            )
            t = time.perf_counter()
            found = pool.map(task_function, tasks)
            dispatch += time.perf_counter() - t
        iterator = iter(found)
        added = 0
        violated = 0
        for index in range(len(directions)):
            t = time.perf_counter()
            returned = next(iterator)
            worker_wait += time.perf_counter() - t
            if profiled:
                placements, metrics = returned
                for name, value in metrics.items():
                    if name not in ("pid", "task_start_at", "task_end_at"):
                        worker_metrics[name] = worker_metrics.get(name, 0.0) + value
                pid = str(metrics["pid"])
                worker_tasks[pid] = worker_tasks.get(pid, 0) + 1
                task_records.append({
                    "direction": index,
                    "pid": metrics["pid"],
                    "start_at": metrics["task_start_at"],
                    "end_at": metrics["task_end_at"],
                    "wall_seconds": metrics["total_wall"],
                    "cpu_seconds": metrics["total_cpu"],
                    "phases": {
                        key: metrics[key] for key in (
                            "event_grid", "projection_domain", "support_events",
                            "difference_scatter", "prefix_accumulate", "domain_bounds",
                            "reachable_compaction", "top13_selection",
                            "candidate_reconstruction",
                        ) if key in metrics
                    },
                })
            else:
                placements = returned
            t = time.perf_counter()
            for mass, cu, cv, covers in placements:
                if mass >= 1 - 1e-9:
                    break
                row = np.zeros(weights.shape[1])
                np.add.at(row, membership[covers], 1.0)
                violated += 1
                added += rows.add(index, (cu, cv), row)
            parent_process += time.perf_counter() - t
        round_summary = {
            "round": round_index, "wall_seconds": time.perf_counter() - round_start,
            "rows_held": len(rows), "added": added, "violated": violated,
            "parent_wait_seconds": worker_wait - wait_at_start,
            "parent_process_seconds": parent_process - process_at_start,
            "parent_dispatch_seconds": dispatch - dispatch_at_start,
        }
        if profiled:
            busy = sum(record["wall_seconds"] for record in task_records)
            last_pid = max(task_records, key=lambda item: item["end_at"])["pid"]
            critical_tasks = [record for record in task_records if record["pid"] == last_pid]
            round_summary.update({
                "worker_busy_seconds": busy,
                "worker_cpu_seconds": sum(record["cpu_seconds"] for record in task_records),
                "worker_active_span_seconds": max(record["end_at"] for record in task_records)
                - min(record["start_at"] for record in task_records),
                "task_max_seconds": max(record["wall_seconds"] for record in task_records),
                "task_min_seconds": min(record["wall_seconds"] for record in task_records),
                "worker_task_counts": {
                    str(pid): sum(record["pid"] == pid for record in task_records)
                    for pid in {record["pid"] for record in task_records}
                },
                "last_worker_pid": last_pid,
                "last_worker_busy_seconds": sum(
                    record["wall_seconds"] for record in critical_tasks
                ),
                "last_worker_phase_seconds": {
                    name: sum(record["phases"].get(name, 0.0)
                              for record in critical_tasks)
                    for name in (
                        "event_grid", "projection_domain", "support_events",
                        "difference_scatter", "prefix_accumulate", "domain_bounds",
                        "reachable_compaction", "top13_selection",
                        "candidate_reconstruction",
                    )
                },
            })
        round_times.append(round_summary)
    wall = time.perf_counter() - whole_start
    assert len(rows) == 5842 and len(round_times) == 23, (len(rows), len(round_times))
    return {
        "wall_seconds": wall, "worker_wait_seconds": worker_wait,
        "parent_process_seconds": parent_process,
        "dispatch_seconds": dispatch, "site_weights_seconds": weight_setup,
        "other_seconds": wall - worker_wait - parent_process - dispatch - weight_setup,
        "worker_metrics": worker_metrics, "worker_tasks": worker_tasks,
        "rounds": round_times,
        "row_directions": np.asarray(rows.directions, dtype=np.int16),
        "row_centres": np.asarray(rows.centres, dtype=float),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=20)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    assert args.workers >= 1
    stored = np.load(ROOT / "raw/current-states.npz")
    weights, points, membership = (
        stored[name] for name in ("weights", "points", "membership")
    )
    expected_directions = stored["directions"]
    expected_centres = stored["centres"]
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    pool = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else None
    try:
        params = (weights, points, membership, directions,
                  float(case.outer_side), float(case.square_side), pool)
        warm = replay(*params)
        assert np.array_equal(warm.pop("row_directions"), expected_directions)
        assert np.array_equal(warm.pop("row_centres"), expected_centres)
        repeats = max(1, math.ceil(args.target_seconds / warm["wall_seconds"]))
        if repeats * warm["wall_seconds"] > 60:
            repeats = max(1, int(60 / warm["wall_seconds"]))
        pids = [p.pid for p in pool._processes.values()] if pool else []  # noqa: SLF001
        for sample in range(1, args.samples + 1):
            load_before = load()
            before_p = proc_cpu(os.getpid())
            before_w = {pid: proc_cpu(pid) for pid in pids}
            start = time.perf_counter()
            replays = [replay(*params) for _ in range(repeats)]
            batch_wall = time.perf_counter() - start
            after_p = proc_cpu(os.getpid())
            after_w = {pid: proc_cpu(pid) for pid in pids}
            assert batch_wall >= 10, (args.workers, sample, batch_wall)
            for item in replays:
                assert np.array_equal(item.pop("row_directions"), expected_directions)
                assert np.array_equal(item.pop("row_centres"), expected_centres)
            parent_cpu = after_p[0] - before_p[0]
            child_cpu = sum(after_w[pid][0] - before_w[pid][0] for pid in pids)
            data = {
                "workers": args.workers, "sample": sample, "repeats": repeats,
                "load_before": load_before, "warmup_seconds": warm["wall_seconds"],
                "batch_wall_seconds": batch_wall,
                "normalized_wall_seconds": batch_wall / repeats,
                "parent_cpu_seconds": parent_cpu,
                "worker_cpu_seconds": child_cpu if pids else parent_cpu,
                "aggregate_cpu_seconds": parent_cpu + child_cpu,
                "worker_cpu_by_pid_seconds": {
                    str(pid): after_w[pid][0] - before_w[pid][0] for pid in pids
                },
                "worker_minor_faults": sum(
                    after_w[pid][1] - before_w[pid][1] for pid in pids
                ),
                "worker_rss_pages": {str(pid): after_w[pid][2] for pid in pids},
                "peak_parent_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                "replays": replays,
            }
            path = ROOT / "raw" / f"separation-w{args.workers}{args.tag}-s{sample}.json"
            path.write_text(json.dumps(data, indent=2) + "\n")
            print(json.dumps({
                "workers": args.workers, "sample": sample,
                "batch_wall": round(batch_wall, 3),
                "per_replay": round(batch_wall / repeats, 3),
                "worker_cpu": round(data["worker_cpu_seconds"] / repeats, 3),
                "parent_cpu": round(parent_cpu / repeats, 3),
            }), flush=True)
    finally:
        if pool is not None:
            pool.shutdown()


if __name__ == "__main__":
    main()
