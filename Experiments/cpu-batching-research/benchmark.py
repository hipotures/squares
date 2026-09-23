"""Compare production tasks with worker scratch reuse and chunked reusable tasks.

Run from packing/ with OMP/OPENBLAS/MKL threads limited to one. Production
source is never edited. The complete accepted 23-round direction trajectory is
replayed from RAM; pool startup and fixture I/O are outside timed batches.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional import colgen, generate

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT.parent / "cpu-post-integration-profile"
TICKS = os.sysconf("SC_CLK_TCK")


class Scratch:
    def __init__(self) -> None:
        self.grid = np.empty(0, dtype=np.float64)
        self.values = np.empty(0, dtype=np.float64)
        self.allocated = 0
        self.grid_logical = 0
        self.compact_logical = 0

    def space(self, name: str, count: int) -> np.ndarray:
        buffer = getattr(self, name)
        if buffer.size < count:
            # One contiguous buffer serves every shape; a growing capacity
            # bounds the number of large allocations per worker.
            capacity = max(count, buffer.size * 2)
            buffer = np.empty(capacity, dtype=np.float64)
            setattr(self, name, buffer)
            self.allocated += buffer.nbytes
        return buffer[:count]

    def snapshot(self) -> tuple[int, int, int]:
        return self.allocated, self.grid_logical, self.compact_logical


_SCRATCH = Scratch()


def reusable_event_grid(
    points: np.ndarray, weights: np.ndarray, direction, outer_side: float,
    square_side: float, *, clip=None, build_reachable: bool = True,
) -> generate.EventGrid:
    """Production event grid with only the large grid allocation reused."""
    cosine, sine = float(direction.ux), float(direction.uy)
    half = square_side / 2
    u = points[:, 0] * cosine + points[:, 1] * sine
    v = -points[:, 0] * sine + points[:, 1] * cosine
    domain = generate._CentreDomain.at(direction, outer_side, square_side, clip)
    live = weights > 0
    if not live.any():
        live = np.zeros(points.shape[0], dtype=bool)
        live[:: max(1, points.shape[0] // 600)] = True
    live_u, live_v, live_w = u[live], v[live], weights[live]
    u_events = np.unique(np.concatenate([
        live_u - half, live_u + half, [domain.u_low, domain.u_high],
    ]))
    v_events = np.unique(np.concatenate([
        live_v - half, live_v + half, [domain.v_low, domain.v_high],
    ]))
    shape = (u_events.size, v_events.size)
    grid = _SCRATCH.space("grid", math.prod(shape)).reshape(shape)
    grid.fill(0)
    _SCRATCH.grid_logical += grid.nbytes
    left = np.searchsorted(u_events, live_u - half)
    right = np.searchsorted(u_events, live_u + half)
    bottom = np.searchsorted(v_events, live_v - half)
    top = np.searchsorted(v_events, live_v + half)
    np.add.at(grid, (left, bottom), live_w)
    np.add.at(grid, (right, bottom), -live_w)
    np.add.at(grid, (left, top), -live_w)
    np.add.at(grid, (right, top), live_w)
    np.add.accumulate(grid, axis=1, out=grid)
    generate.accumulate_axis0(grid)
    mass = grid[:-1, :-1]
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
    return generate.EventGrid(u, v, u_events, v_events, mass, reachable, lows, highs, domain)


def reusable_reachable_values(cells: generate.EventGrid):
    """Production P1 compaction with only its large values buffer reused."""
    ve = cells.v_events
    band_first = np.searchsorted(ve[1:], cells.domain.v_low, side="right")
    band_last = np.searchsorted(ve[:-1], cells.domain.v_high, side="left")
    slabs = ((cells.u_events[1:] > cells.domain.u_low)
             & (cells.u_events[:-1] < cells.domain.u_high))
    first_all = np.maximum(
        band_first,
        np.searchsorted(ve[1:], cells.lows - generate._REACH_SLACK, side="right"),
    )
    last_all = np.minimum(
        band_last,
        np.searchsorted(ve[:-1], cells.highs + generate._REACH_SLACK, side="left"),
    )
    valid = slabs & (first_all < last_all)
    row_ids = np.flatnonzero(valid)
    firsts = first_all[valid]
    widths = last_all[valid] - firsts
    offsets = np.empty(row_ids.size, dtype=np.intp)
    if offsets.size:
        offsets[0] = 0
        np.cumsum(widths[:-1], out=offsets[1:])
    values = _SCRATCH.space("values", int(widths.sum()))
    _SCRATCH.compact_logical += values.nbytes
    for row, first, width, offset in zip(row_ids, firsts, widths, offsets, strict=True):
        values[offset:offset + width] = cells.mass[row, first:first + width]
    return values, row_ids, firsts, offsets


def install_reuse() -> None:
    global _SCRATCH
    _SCRATCH = Scratch()
    generate.event_grid = reusable_event_grid
    generate._reachable_values = reusable_reachable_values


def direction_task(args):
    before = _SCRATCH.snapshot()
    placements = colgen._direction_task(args)
    after = _SCRATCH.snapshot()
    return placements, tuple(b - a for a, b in zip(before, after, strict=True))


def chunk_task(args):
    points, weights, directions, outer, side = args
    return [direction_task((points, weights, direction, outer, side, 3, None))
            for direction in directions]


def proc(pid: int) -> dict[str, int | float]:
    stat = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    return {
        "cpu": (int(stat[11]) + int(stat[12])) / TICKS,
        "minor_faults": int(stat[7]), "major_faults": int(stat[9]),
        "rss_pages": int(stat[21]),
    }


def load() -> dict[str, object]:
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "loadavg": os.getloadavg(),
        "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
    }


def replay(weights, points, membership, directions, outer, side,
           pool, variant: str, chunk_size: int, *, verify_matrix: bool = False):
    rows = colgen.Rows()
    rows.matrix = np.zeros((0, weights.shape[1]))
    allocation = grid_logical = compact_logical = 0
    for orbit_weights in weights:
        site_weights = orbit_weights[membership]
        if variant in ("C", "D"):
            chunks = [directions[i:i + chunk_size]
                      for i in range(0, len(directions), chunk_size)]
            tasks = [(points, site_weights, part, outer, side) for part in chunks]
            grouped = map(chunk_task, tasks) if pool is None else pool.map(chunk_task, tasks)
            outputs = (item for group in grouped for item in group)
        else:
            tasks = ((points, site_weights, direction, outer, side, 3, None)
                     for direction in directions)
            outputs = map(direction_task, tasks) if pool is None else pool.map(direction_task, tasks)
        for index, (placements, delta) in enumerate(outputs):
            allocation += delta[0]
            grid_logical += delta[1]
            compact_logical += delta[2]
            for mass, cu, cv, covers in placements:
                if mass >= 1 - 1e-9:
                    break
                row = np.zeros(weights.shape[1])
                np.add.at(row, membership[covers], 1.0)
                rows.add(index, (cu, cv), row)
    result = {
        "rows": len(rows),
        "directions": np.asarray(rows.directions, dtype=np.int16),
        "centres": np.asarray(rows.centres, dtype=float),
        "scratch_allocated_bytes": allocation,
        "logical_grid_bytes": grid_logical,
        "logical_compact_bytes": compact_logical,
    }
    if verify_matrix:
        result["matrix"] = rows.stacked()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=("A", "B", "C", "D"), required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--chunk-size", type=int, default=4)
    parser.add_argument("--target-seconds", type=float, default=20)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    assert args.workers >= 1 and args.chunk_size >= 1
    stored = np.load(PROFILE / "raw/current-states.npz")
    weights, points, membership = (stored[name] for name in
                                    ("weights", "points", "membership"))
    expected_directions, expected_centres = stored["directions"], stored["centres"]
    expected_matrix = load_npz(PROFILE / "raw/current-rows-csr.npz").toarray()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = generate.direction_net(case.half_tangents())
    reuse = args.variant in ("B", "C")
    if reuse and args.workers == 1:
        install_reuse()
    pool = (ProcessPoolExecutor(
        max_workers=args.workers,
        initializer=install_reuse if reuse else None,
    ) if args.workers > 1 else None)
    try:
        params = (weights, points, membership, directions,
                  float(case.outer_side), float(case.square_side),
                  pool, args.variant, args.chunk_size)
        warm_start = time.perf_counter()
        warm = replay(*params, verify_matrix=True)
        warm_wall = time.perf_counter() - warm_start
        assert warm["rows"] == 5842
        assert np.array_equal(warm.pop("directions"), expected_directions)
        assert np.array_equal(warm.pop("centres"), expected_centres)
        assert np.array_equal(warm.pop("matrix"), expected_matrix)
        if args.samples == 0:
            print(json.dumps({"warmup_seconds": warm_wall, "correct": True,
                              "scratch_allocated_bytes": warm["scratch_allocated_bytes"]}))
            return
        repeats = max(1, math.ceil(args.target_seconds / warm_wall))
        if repeats * warm_wall > 60:
            repeats = max(1, int(60 / warm_wall))
        pids = [p.pid for p in pool._processes.values()] if pool else [os.getpid()]
        output = ROOT / "raw"
        output.mkdir(parents=True, exist_ok=True)
        for sample in range(1, args.samples + 1):
            load_before = load()
            before = {pid: proc(pid) for pid in pids}
            start = time.perf_counter()
            replays = [replay(*params) for _ in range(repeats)]
            batch_wall = time.perf_counter() - start
            after = {pid: proc(pid) for pid in pids}
            assert 10 <= batch_wall <= 60, batch_wall
            for item in replays:
                assert item["rows"] == 5842
                assert np.array_equal(item.pop("directions"), expected_directions)
                assert np.array_equal(item.pop("centres"), expected_centres)
            worker_cpu = sum(after[pid]["cpu"] - before[pid]["cpu"] for pid in pids)
            data = {
                "variant": args.variant, "workers": args.workers,
                "chunk_size": args.chunk_size if args.variant in ("C", "D") else 1,
                "sample": sample, "repeats": repeats, "load_before": load_before,
                "warmup_wall_seconds": warm_wall,
                "batch_wall_seconds": batch_wall,
                "separation_wall_seconds_per_replay": batch_wall / repeats,
                "worker_cpu_seconds_per_replay": worker_cpu / repeats,
                "effective_cores": worker_cpu / batch_wall,
                "worker_minor_faults_per_replay": sum(
                    after[pid]["minor_faults"] - before[pid]["minor_faults"] for pid in pids
                ) / repeats,
                "worker_major_faults_per_replay": sum(
                    after[pid]["major_faults"] - before[pid]["major_faults"] for pid in pids
                ) / repeats,
                "worker_rss_pages": {str(pid): after[pid]["rss_pages"] for pid in pids},
                "scratch_allocated_bytes_per_replay": sum(
                    x["scratch_allocated_bytes"] for x in replays
                ) / repeats,
                "logical_grid_bytes_per_replay": sum(
                    x["logical_grid_bytes"] for x in replays
                ) / repeats,
                "logical_compact_bytes_per_replay": sum(
                    x["logical_compact_bytes"] for x in replays
                ) / repeats,
                "correctness": "warmup matrix and every replay row order/centres identical",
                "thread_limits": {key: os.environ.get(key) for key in
                                  ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
            }
            path = output / f"{args.variant}-w{args.workers}{args.tag}-s{sample}.json"
            path.write_text(json.dumps(data, indent=2) + "\n")
            print(json.dumps({"variant": args.variant, "workers": args.workers,
                              "sample": sample, "wall": batch_wall / repeats,
                              "cpu": worker_cpu / repeats,
                              "batch": batch_wall}), flush=True)
    finally:
        if pool is not None:
            pool.shutdown()


if __name__ == "__main__":
    main()
