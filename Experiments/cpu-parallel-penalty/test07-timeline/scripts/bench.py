"""Full 23-round chunk timeline and research-only prior-round cost ordering."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path[:0] = [str(ROOT / "packing"), str(ROOT / "Experiments/cpu-chunk-integration")]
from devtools import bench_colgen
from replay import replay as production_replay
from sqpack.fractional import generate
from sqpack.fractional.colgen import Rows
from sqpack.fractional.generate import direction_net

DATA = ROOT / "Experiments/cpu-post-integration-profile/raw/current-states.npz"
ACCEPTED = ROOT / "Experiments/cpu-chunk-integration/raw/correctness.json"
ORIGINAL_EVENT_GRID = generate.event_grid
LAST_GRID_SHAPE = None


def record_grid(*args, **kwargs):
    global LAST_GRID_SHAPE
    cells = ORIGINAL_EVENT_GRID(*args, **kwargs)
    LAST_GRID_SHAPE = tuple(int(x) for x in cells.mass.shape)
    return cells


def worker_init():
    generate.event_grid = record_grid


def timed_chunk(task):
    round_index, chunk_index, indices_or_first, points, weights, directions, outer, side = task
    begun = time.perf_counter()
    cpu_before = time.process_time()
    found = []
    detail = []
    for offset, direction in enumerate(directions):
        direction_index = (indices_or_first + offset if isinstance(indices_or_first, int)
                           else indices_or_first[offset])
        start = time.perf_counter()
        result = generate.placement_cells(points, weights, direction, outer, side,
                                          keep=3, clip=None)
        finish = time.perf_counter()
        assert LAST_GRID_SHAPE is not None
        rows, columns = LAST_GRID_SHAPE
        detail.append({"direction": direction_index,
                       "start": start, "finish": finish,
                       "grid_rows": rows, "grid_columns": columns,
                       "grid_cells": rows * columns})
        found.append(result)
    finished = time.perf_counter()
    cpu_seconds = time.process_time() - cpu_before
    return found, {"round": round_index, "chunk": chunk_index,
                   "worker_pid": os.getpid(), "worker_start": begun,
                   "worker_finish": finished, "worker_cpu": cpu_seconds,
                   "directions": detail}


def load_data():
    with np.load(DATA) as stored:
        weights, points, membership = (stored[name] for name in
                                       ("weights", "points", "membership"))
        expected_directions = stored["directions"]
        expected_centres = stored["centres"]
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = direction_net(case.half_tangents())
    accepted = json.loads(ACCEPTED.read_text())["results"][0]
    return weights, points, membership, expected_directions, expected_centres, \
        directions, float(case.outer_side), float(case.square_side), accepted


def proc_cpu(pid):
    parts = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    return (int(parts[11]) + int(parts[12])) / os.sysconf("SC_CLK_TCK")


def sha(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def check_rows(rows, expected_directions, expected_centres, accepted):
    directions = np.asarray(rows.directions, dtype=np.int16)
    centres = np.asarray(rows.centres, dtype=np.float64)
    matrix = np.asarray(rows.pending, dtype=np.float64)
    hashes = {"directions_sha256": sha(directions), "centres_sha256": sha(centres),
              "matrix_sha256": sha(matrix)}
    assert np.array_equal(directions, expected_directions)
    assert np.array_equal(centres, expected_centres)
    assert len(rows) == accepted["rows"]
    assert all(hashes[key] == accepted[key] for key in hashes), hashes
    return hashes


def balanced_chunks(predicted):
    """Largest prior-round grids first into the least-filled four-slot bin."""
    count = math.ceil(len(predicted) / 4)
    groups = [[] for _ in range(count)]
    totals = [0] * count
    for direction in sorted(range(len(predicted)), key=lambda i: (-predicted[i], i)):
        eligible = (i for i, group in enumerate(groups) if len(group) < 4)
        group_id = min(eligible, key=lambda i: (totals[i], i))
        groups[group_id].append(direction)
        totals[group_id] += predicted[direction]
    groups = [sorted(group) for group in groups]
    return sorted(groups, key=lambda group: group[0])


def timeline_replay(weights, points, membership, directions, outer, side, pool,
                    *, mode, retain_trace):
    assert mode in ("ordered", "cost-first", "balanced")
    rows = Rows()
    # Previous-round cell counts are the cheap predictor available at dispatch.
    predicted = [1] * len(directions)
    trace = []
    total_worker_cpu = 0.0
    started = time.perf_counter()
    for round_index, orbit_weights in enumerate(weights):
        round_start = time.perf_counter()
        site_weights = orbit_weights[membership]
        chunks = [list(range(first, min(first + 4, len(directions))))
                  for first in range(0, len(directions), 4)]
        if mode == "balanced" and round_index > 0:
            chunks = balanced_chunks(predicted)
        order = list(range(len(chunks)))
        if mode == "cost-first" and round_index > 0:
            order.sort(key=lambda i: (-sum(predicted[j] for j in chunks[i]), i))
        future_by_chunk = {}
        submission = {}
        ready = {}
        for chunk_id in order:
            indices = chunks[chunk_id]
            now = time.perf_counter()
            task_indices = tuple(indices) if mode == "balanced" else indices[0]
            task = (round_index, chunk_id, task_indices, points, site_weights,
                    tuple(directions[i] for i in indices), outer, side)
            future = pool.submit(timed_chunk, task)
            future_by_chunk[chunk_id] = future
            submission[chunk_id] = {"ready": now, "submitted": time.perf_counter(),
                                    "predicted_cells": sum(predicted[i] for i in indices)}
            future.add_done_callback(
                lambda _future, key=chunk_id: ready.__setitem__(key, time.perf_counter()))
        current_cells = [0] * len(directions)
        chunks_trace = []
        parent_process = 0.0
        parent_wait = 0.0
        if mode == "balanced":
            chunk_for_direction = {index: (chunk_id, offset)
                                   for chunk_id, indices in enumerate(chunks)
                                   for offset, index in enumerate(indices)}
            retrieved = {}
            traces_by_chunk = {}
            for index in range(len(directions)):
                chunk_id, offset = chunk_for_direction[index]
                if chunk_id not in retrieved:
                    wait_start = time.perf_counter()
                    found, worker = future_by_chunk[chunk_id].result()
                    received = time.perf_counter()
                    parent_wait += received - wait_start
                    total_worker_cpu += worker["worker_cpu"]
                    retrieved[chunk_id] = found
                    for detail in worker["directions"]:
                        current_cells[detail["direction"]] = detail["grid_cells"]
                    if retain_trace:
                        traces_by_chunk[chunk_id] = {**submission[chunk_id], **worker,
                            "result_ready": ready.get(chunk_id, received),
                            "wait_start": wait_start, "received": received}
                processing_start = time.perf_counter()
                for mass, cu, cv, covers in retrieved[chunk_id][offset]:
                    if mass >= 1 - 1e-9:
                        break
                    row = np.zeros(weights.shape[1])
                    np.add.at(row, membership[covers], 1.0)
                    rows.add(index, (cu, cv), row)
                processing_end = time.perf_counter()
                parent_process += processing_end - processing_start
                if retain_trace:
                    receipt = traces_by_chunk[chunk_id]
                    receipt.setdefault("consume_start", processing_start)
                    receipt["consume_end"] = processing_end
            if retain_trace:
                chunks_trace = [traces_by_chunk[i] for i in range(len(chunks))]
        else:
            for chunk_id in range(len(chunks)):
                wait_start = time.perf_counter()
                found, worker = future_by_chunk[chunk_id].result()
                received = time.perf_counter()
                parent_wait += received - wait_start
                total_worker_cpu += worker["worker_cpu"]
                for detail in worker["directions"]:
                    current_cells[detail["direction"]] = detail["grid_cells"]
                processing_start = time.perf_counter()
                for offset, found_one in enumerate(found):
                    index = chunks[chunk_id][offset]
                    for mass, cu, cv, covers in found_one:
                        if mass >= 1 - 1e-9:
                            break
                        row = np.zeros(weights.shape[1])
                        np.add.at(row, membership[covers], 1.0)
                        rows.add(index, (cu, cv), row)
                processing_end = time.perf_counter()
                parent_process += processing_end - processing_start
                if retain_trace:
                    chunks_trace.append({**submission[chunk_id], **worker,
                                         "result_ready": ready.get(chunk_id, received),
                                         "wait_start": wait_start, "received": received,
                                         "consume_start": processing_start,
                                         "consume_end": processing_end})
        assert all(current_cells)
        predicted = current_cells
        if retain_trace:
            trace.append({"round": round_index, "start": round_start,
                          "end": time.perf_counter(), "parent_wait": parent_wait,
                          "parent_process": parent_process,
                          "chunks": chunks_trace})
    elapsed = time.perf_counter() - started
    assert len(rows) == 5842 and len(trace) in (0, 23)
    return {"wall": elapsed, "worker_cpu": total_worker_cpu,
            "rows": rows, "trace": trace}


def load():
    return {"loadavg": os.getloadavg(),
            "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def run(args):
    (weights, points, membership, expected_directions, expected_centres,
     directions, outer, side, accepted) = load_data()
    workers = args.workers
    pool = ProcessPoolExecutor(max_workers=workers,
                               initializer=worker_init if args.mode != "production" else None)
    try:
        params = (weights, points, membership, directions, outer, side, pool)
        if args.mode == "production":
            def one(retain_trace=False):
                value = production_replay(*params, chunked=True)
                assert np.array_equal(value.pop("row_directions"), expected_directions)
                assert np.array_equal(value.pop("row_centres"), expected_centres)
                value["wall"] = value.pop("wall_seconds")
                return value
        else:
            def one(retain_trace=False):
                return timeline_replay(*params, mode=args.mode, retain_trace=retain_trace)
        warm = one()
        if args.mode != "production":
            hashes = check_rows(warm["rows"], expected_directions, expected_centres, accepted)
        else:
            hashes = {k: accepted[k] for k in
                      ("directions_sha256", "centres_sha256", "matrix_sha256")}
        repeats = max(1, math.ceil(args.target_seconds / warm["wall"]))
        if repeats * warm["wall"] > 60:
            repeats = max(1, int(60 / warm["wall"]))
        pids = [p.pid for p in pool._processes.values()]  # private, read-only benchmark probe
        for sample in range(1, args.samples + 1):
            load_before = load()
            parent_cpu_before = proc_cpu(os.getpid())
            worker_cpu_before = {pid: proc_cpu(pid) for pid in pids}
            t = time.perf_counter()
            last = None
            first_trace = None
            worker_cpu_chunk_sum = 0.0
            for replay_number in range(repeats):
                value = one(retain_trace=(args.mode != "production" and replay_number == 0))
                if args.mode != "production":
                    worker_cpu_chunk_sum += value["worker_cpu"]
                    if replay_number == 0:
                        first_trace = value["trace"]
                last = value
            batch_wall = time.perf_counter() - t
            assert 10 <= batch_wall <= 65, batch_wall
            parent_cpu = proc_cpu(os.getpid()) - parent_cpu_before
            worker_cpu = sum(proc_cpu(pid) - worker_cpu_before[pid] for pid in pids)
            if args.mode != "production":
                hashes = check_rows(last["rows"], expected_directions,
                                    expected_centres, accepted)
            result = {"mode": args.mode, "workers": workers, "sample": sample,
                      "target_seconds": args.target_seconds, "repeats": repeats,
                      "batch_wall": batch_wall, "wall_per_replay": batch_wall / repeats,
                      "parent_cpu_per_replay": parent_cpu / repeats,
                      "worker_cpu_per_replay": worker_cpu / repeats,
                      "chunk_cpu_per_replay": worker_cpu_chunk_sum / repeats if first_trace else None,
                      "warmup_wall": warm["wall"], "load_before": load_before,
                      "rows": 5842, "rounds": 23, "hashes": hashes,
                      "first_replay_trace": first_trace}
            raw = HERE.parent / "raw"
            raw.mkdir(parents=True, exist_ok=True)
            path = raw / f"{args.mode}-w{workers}-{args.tag}-s{sample}.json.gz"
            with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as handle:
                json.dump(result, handle, separators=(",", ":"))
            print(json.dumps({"mode": args.mode, "workers": workers,
                              "sample": sample, "replays": repeats,
                              "batch_wall": round(batch_wall, 3),
                              "per_replay": round(batch_wall / repeats, 3),
                              "worker_cpu": round(worker_cpu / repeats, 3)}), flush=True)
    finally:
        pool.shutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("production", "ordered", "cost-first", "balanced"), required=True)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--target-seconds", type=float, default=20)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--tag", default="final")
    run(parser.parse_args())
