"""Per-operation worker timings on the complete accepted 23-round workload."""

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
from replay import load, replay

from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.generate import direction_net

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT.parent / "cpu-post-integration-profile" / "raw"
ORIGINAL_EVENT_GRID = generate.event_grid
ORIGINAL_REACHABLE = generate._reachable_values
ORIGINAL_SELECTOR = generate._least_finite_indices
PHASES: dict[str, float] = {}


def timed_event_grid(
    points, weights, direction, outer_side, square_side, *, clip=None,
    build_reachable=True,
):
    """Verbatim current event-grid arithmetic with research-only phase timers."""
    whole = time.perf_counter()
    t = whole
    cosine, sine = float(direction.ux), float(direction.uy)
    half = square_side / 2
    u = points[:, 0] * cosine + points[:, 1] * sine
    v = -points[:, 0] * sine + points[:, 1] * cosine
    domain = generate._CentreDomain.at(direction, outer_side, square_side, clip)
    PHASES["projection_domain"] = PHASES.get("projection_domain", 0.0) + time.perf_counter() - t

    t = time.perf_counter()
    live = weights > 0
    if not live.any():
        live = np.zeros(points.shape[0], dtype=bool)
        live[:: max(1, points.shape[0] // 600)] = True
    live_u, live_v, live_w = u[live], v[live], weights[live]
    PHASES["live_sites"] = PHASES.get("live_sites", 0.0) + live_u.size
    u_events = np.unique(
        np.concatenate([live_u - half, live_u + half, [domain.u_low, domain.u_high]])
    )
    v_events = np.unique(
        np.concatenate([live_v - half, live_v + half, [domain.v_low, domain.v_high]])
    )
    PHASES["support_events"] = PHASES.get("support_events", 0.0) + time.perf_counter() - t

    t = time.perf_counter()
    grid = np.zeros((u_events.size, v_events.size))
    PHASES["grid_cells"] = PHASES.get("grid_cells", 0.0) + grid.size
    PHASES["grid_bytes"] = PHASES.get("grid_bytes", 0.0) + grid.nbytes
    left = np.searchsorted(u_events, live_u - half)
    right = np.searchsorted(u_events, live_u + half)
    bottom = np.searchsorted(v_events, live_v - half)
    top = np.searchsorted(v_events, live_v + half)
    np.add.at(grid, (left, bottom), live_w)
    np.add.at(grid, (right, bottom), -live_w)
    np.add.at(grid, (left, top), -live_w)
    np.add.at(grid, (right, top), live_w)
    PHASES["difference_scatter"] = PHASES.get("difference_scatter", 0.0) + time.perf_counter() - t

    t = time.perf_counter()
    np.add.accumulate(grid, axis=1, out=grid)
    generate.accumulate_axis0(grid)
    mass = grid[:-1, :-1]
    PHASES["prefix_accumulate"] = PHASES.get("prefix_accumulate", 0.0) + time.perf_counter() - t

    t = time.perf_counter()
    u0, u1 = u_events[:-1], u_events[1:]
    slabs = (u1 > domain.u_low) & (u0 < domain.u_high)
    bands = (v_events[:-1] < domain.v_high) & (v_events[1:] > domain.v_low)
    lows, highs = domain.v_range(u0, u1)
    reachable = (
        slabs[:, None]
        & bands[None, :]
        & (v_events[None, :-1] < highs[:, None] + generate._REACH_SLACK)
        & (v_events[None, 1:] > lows[:, None] - generate._REACH_SLACK)
    ) if build_reachable else None
    PHASES["domain_bounds"] = PHASES.get("domain_bounds", 0.0) + time.perf_counter() - t
    PHASES["event_grid"] = PHASES.get("event_grid", 0.0) + time.perf_counter() - whole
    return generate.EventGrid(u, v, u_events, v_events, mass, reachable, lows, highs, domain)


def timed_reachable(*args, **kwargs):
    t = time.perf_counter()
    result = ORIGINAL_REACHABLE(*args, **kwargs)
    PHASES["compact_values"] = PHASES.get("compact_values", 0.0) + result[0].size
    PHASES["compact_bytes"] = PHASES.get("compact_bytes", 0.0) + result[0].nbytes
    PHASES["reachable_compaction"] = (
        PHASES.get("reachable_compaction", 0.0) + time.perf_counter() - t
    )
    return result


def timed_selector(*args, **kwargs):
    t = time.perf_counter()
    result = ORIGINAL_SELECTOR(*args, **kwargs)
    PHASES["top13_selection"] = PHASES.get("top13_selection", 0.0) + time.perf_counter() - t
    return result


def init_profile() -> None:
    generate.event_grid = timed_event_grid
    generate._reachable_values = timed_reachable
    generate._least_finite_indices = timed_selector


def profile_task(args):
    PHASES.clear()
    before = resource.getrusage(resource.RUSAGE_SELF)
    t = time.perf_counter()
    result = generate.placement_cells(
        args[0], args[1], args[2], args[3], args[4], keep=args[5], clip=args[6]
    )
    wall = time.perf_counter() - t
    after = resource.getrusage(resource.RUSAGE_SELF)
    phases = dict(PHASES)
    phases["candidate_reconstruction"] = wall - sum(
        phases.get(name, 0.0) for name in
        ("event_grid", "reachable_compaction", "top13_selection")
    )
    phases["total_wall"] = wall
    phases["total_cpu"] = (
        after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
    )
    phases["minor_faults"] = after.ru_minflt - before.ru_minflt
    phases["pid"] = os.getpid()
    phases["task_start_at"] = t
    phases["task_end_at"] = t + wall
    return result, phases


def profile_chunk_task(args):
    points, weights, directions, outer, side, keep, clip = args
    return [profile_task((points, weights, direction, outer, side, keep, clip))
            for direction in directions]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=20)
    args = parser.parse_args()
    assert args.workers in (1, 16)
    stored = np.load(PROFILE / "current-states.npz")
    weights, points, membership = (
        stored[name] for name in ("weights", "points", "membership")
    )
    expected_directions, expected_centres = stored["directions"], stored["centres"]
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    pool = (ProcessPoolExecutor(max_workers=args.workers, initializer=init_profile)
            if args.workers > 1 else None)
    if pool is None:
        init_profile()
    try:
        params = (weights, points, membership, directions,
                  float(case.outer_side), float(case.square_side), pool)
        warm = replay(*params, task_function=profile_task,
                      chunk_task_function=profile_chunk_task, profiled=True)
        assert np.array_equal(warm.pop("row_directions"), expected_directions)
        assert np.array_equal(warm.pop("row_centres"), expected_centres)
        repeats = max(1, math.ceil(args.target_seconds / warm["wall_seconds"]))
        if repeats * warm["wall_seconds"] > 60:
            repeats = max(1, int(60 / warm["wall_seconds"]))
        for sample in range(1, args.samples + 1):
            load_before = load()
            start = time.perf_counter()
            replays = [replay(*params, task_function=profile_task,
                              chunk_task_function=profile_chunk_task, profiled=True)
                       for _ in range(repeats)]
            batch_wall = time.perf_counter() - start
            assert batch_wall >= 10, (args.workers, sample, batch_wall)
            for entry in replays:
                assert np.array_equal(entry.pop("row_directions"), expected_directions)
                assert np.array_equal(entry.pop("row_centres"), expected_centres)
            data = {
                "workers": args.workers, "sample": sample, "repeats": repeats,
                "load_before": load_before, "warmup_seconds": warm["wall_seconds"],
                "batch_wall_seconds": batch_wall,
                "normalized_wall_seconds": batch_wall / repeats,
                "replays": replays,
            }
            (ROOT / "raw" / f"profile-separation-w{args.workers}-s{sample}.json").write_text(
                json.dumps(data, indent=2) + "\n"
            )
            names = ("event_grid", "reachable_compaction", "top13_selection",
                     "candidate_reconstruction")
            print(json.dumps({
                "workers": args.workers, "sample": sample,
                "batch_wall": round(batch_wall, 3),
                "per_replay": round(batch_wall / repeats, 3),
                **{name: round(sum(r["worker_metrics"].get(name, 0)
                                   for r in replays) / repeats, 3) for name in names},
            }), flush=True)
    finally:
        if pool is not None:
            pool.shutdown()


if __name__ == "__main__":
    main()
