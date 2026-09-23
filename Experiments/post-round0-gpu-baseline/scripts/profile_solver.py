#!/usr/bin/env python3
"""Instrument the installed solver in memory; never edit production modules."""
from __future__ import annotations

import argparse
import inspect
import json
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packing"))
from devtools import bench_colgen  # noqa: E402
from sqpack.fractional import colgen, generate  # noqa: E402


class Recorder:
    def __init__(self):
        self.parts: dict[str, int] = {}

    def reset(self):
        self.parts = {}
        self.meta = {}

    def measure(self, key, fn):
        start = time.thread_time_ns()
        result = fn()
        self.parts[key] = self.parts.get(key, 0) + time.thread_time_ns() - start
        return result

    def add(self, key, elapsed):
        self.parts[key] = self.parts.get(key, 0) + elapsed

    def double_cumsum(self, grid):
        # Keep the inner temporary alive only through the outer cumsum, as in
        # the production nested expression. Holding it for the rest of
        # event_grid measurably changes round-zero allocation/cache behavior.
        first = self.measure("cumsum_1", lambda: np.cumsum(grid, axis=1))
        return self.measure("cumsum_2", lambda: np.cumsum(first, axis=0))


T = Recorder()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise RuntimeError(f"production source changed; expected one occurrence of {old!r}")
    return source.replace(old, new)


def install_profile():
    source = inspect.getsource(generate.event_grid)
    edits = [
        ("u = points[:, 0] * cosine + points[:, 1] * sine", "u = T.measure('project_u', lambda: points[:, 0] * cosine + points[:, 1] * sine)"),
        ("v = -points[:, 0] * sine + points[:, 1] * cosine", "v = T.measure('project_v', lambda: -points[:, 0] * sine + points[:, 1] * cosine)"),
        ("live = weights > 0", "live = T.measure('live_filter', lambda: weights > 0)"),
        ("live_u, live_v, live_w = u[live], v[live], weights[live]", "live_u, live_v, live_w = T.measure('live_gather', lambda: (u[live], v[live], weights[live]))"),
        ("np.concatenate([live_u - half, live_u + half, [domain.u_low, domain.u_high]])", "T.measure('event_construct_u', lambda: np.concatenate([live_u - half, live_u + half, [domain.u_low, domain.u_high]]))"),
        ("np.concatenate([live_v - half, live_v + half, [domain.v_low, domain.v_high]])", "T.measure('event_construct_v', lambda: np.concatenate([live_v - half, live_v + half, [domain.v_low, domain.v_high]]))"),
        ("u_events = np.unique(\n", "u_events = T.measure('unique_u', lambda: np.unique(\n"),
        ("v_events = np.unique(\n", "v_events = T.measure('unique_v', lambda: np.unique(\n"),
        ("    )\n    grid = np.zeros", "    ))\n    grid = np.zeros"),
        ("grid = np.zeros((u_events.size, v_events.size))", "grid = T.measure('grid_alloc', lambda: np.zeros((u_events.size, v_events.size)))\n    T.meta = {'grid_shape': grid.shape, 'live_count': int(live_w.size), 'points_count': int(points.shape[0])}"),
        ("left = np.searchsorted(u_events, live_u - half)", "left = T.measure('searchsorted', lambda: np.searchsorted(u_events, live_u - half))"),
        ("right = np.searchsorted(u_events, live_u + half)", "right = T.measure('searchsorted', lambda: np.searchsorted(u_events, live_u + half))"),
        ("bottom = np.searchsorted(v_events, live_v - half)", "bottom = T.measure('searchsorted', lambda: np.searchsorted(v_events, live_v - half))"),
        ("top = np.searchsorted(v_events, live_v + half)", "top = T.measure('searchsorted', lambda: np.searchsorted(v_events, live_v + half))"),
        ("np.add.at(grid, (left, bottom), live_w)", "T.measure('add_at', lambda: np.add.at(grid, (left, bottom), live_w))"),
        ("np.add.at(grid, (right, bottom), -live_w)", "T.measure('add_at', lambda: np.add.at(grid, (right, bottom), -live_w))"),
        ("np.add.at(grid, (left, top), -live_w)", "T.measure('add_at', lambda: np.add.at(grid, (left, top), -live_w))"),
        ("np.add.at(grid, (right, top), live_w)", "T.measure('add_at', lambda: np.add.at(grid, (right, top), live_w))"),
        ("mass = np.cumsum(np.cumsum(grid, axis=1), axis=0)[:-1, :-1]", "mass = T.double_cumsum(grid)[:-1, :-1]"),
        ("lows, highs = domain.v_range(u0, u1)", "lows, highs = T.measure('v_range', lambda: domain.v_range(u0, u1))"),
        ("reachable = (\n", "reachable = T.measure('reachable', lambda: (\n"),
        ("    )\n    return EventGrid", "    ))\n    return EventGrid"),
    ]
    # The two np.unique closing parentheses are intentionally treated together.
    for old, new in edits:
        if old == "    )\n    grid = np.zeros":
            # Only the second unique closes immediately before grid.
            source = replace_once(source, old, new)
        else:
            source = replace_once(source, old, new)
    # First unique closes immediately before the v assignment.
    source = replace_once(source, "    )\n    v_events =", "    ))\n    v_events =")
    scope = dict(generate.__dict__, T=T)
    exec(source, scope)
    generate.event_grid = scope["event_grid"]

    source = inspect.getsource(generate._least_finite_indices)
    edits = [
        ("np.all((flat == 0) | np.isposinf(flat))", "T.measure('zero_validate', lambda: np.all((flat == 0) | np.isposinf(flat)))"),
        ("zeros = np.flatnonzero(flat == 0)", "zeros = T.measure('zero_indices', lambda: np.flatnonzero(flat == 0))"),
        ("return zeros[np.linspace(0, zeros.size - 1, count, dtype=np.intp)]", "return T.measure('zero_spread', lambda: zeros[np.linspace(0, zeros.size - 1, count, dtype=np.intp)])"),
        ("partition = np.argpartition(flat, count - 1)[:count]", "partition = T.measure('argpartition', lambda: np.argpartition(flat, count - 1)[:count])"),
        ("finite = partition[np.isfinite(flat[partition])]", "finite = T.measure('selector_finite', lambda: partition[np.isfinite(flat[partition])])"),
        ("cutoff = np.max(flat[finite])", "cutoff = T.measure('selector_cutoff', lambda: np.max(flat[finite]))"),
        ("below = finite[flat[finite] < cutoff]", "below = T.measure('selector_below', lambda: finite[flat[finite] < cutoff])"),
        ("tied = np.flatnonzero(flat == cutoff)[: count - below.size]", "tied = T.measure('selector_ties', lambda: np.flatnonzero(flat == cutoff)[: count - below.size])"),
        ("selected = np.concatenate((below, tied))", "selected = T.measure('selector_concat', lambda: np.concatenate((below, tied)))"),
        ("return selected[np.lexsort((selected, flat[selected]))]", "return T.measure('selector_order', lambda: selected[np.lexsort((selected, flat[selected]))])"),
    ]
    for old, new in edits:
        source = replace_once(source, old, new)
    scope = dict(generate.__dict__, T=T)
    exec(source, scope)
    generate._least_finite_indices = scope["_least_finite_indices"]

    source = inspect.getsource(generate.placement_cells)
    edits = [
        ("cells = event_grid(points, weights, direction, outer_side, square_side, clip=clip)", "cells = T.measure('event_grid_total', lambda: event_grid(points, weights, direction, outer_side, square_side, clip=clip))"),
        ("scored = np.where(cells.reachable, cells.mass, np.inf)", "scored = T.measure('scored_where', lambda: np.where(cells.reachable, cells.mass, np.inf))"),
        ("order = _least_finite_indices(flat, 4 * keep + 1, zero_weight_grid=not np.any(weights))", "order = T.measure('selector_total', lambda: _least_finite_indices(flat, 4 * keep + 1, zero_weight_grid=not np.any(weights)))"),
        ("        va, vb = max(v_events[j], lows[i]), min(v_events[j + 1], highs[i])", "        _reconstruct_start = time.thread_time_ns()\n        va, vb = max(v_events[j], lows[i]), min(v_events[j + 1], highs[i])"),
        ("        covers = (np.abs(u - cu) <= half) & (np.abs(v - cv) <= half)", "        T.add('reconstruct', time.thread_time_ns() - _reconstruct_start)\n        covers = T.measure('coverage_mask', lambda: (np.abs(u - cu) <= half) & (np.abs(v - cv) <= half))"),
        ("cell_mass = float(weights[covers].sum())", "cell_mass = T.measure('weight_sum', lambda: float(weights[covers].sum()))"),
        ("found.sort(key=lambda entry: entry[0])", "T.measure('found_sort', lambda: found.sort(key=lambda entry: entry[0]))"),
    ]
    for old, new in edits:
        source = replace_once(source, old, new)
    scope = dict(generate.__dict__, T=T, time=time)
    exec(source, scope)
    generate.placement_cells = scope["placement_cells"]
    colgen.placement_cells = scope["placement_cells"]


def task(args):
    points, weights, direction, outer, side, keep, clip, round_index, direction_index = args
    T.reset()
    wall_start = time.perf_counter_ns()
    cpu_start = time.thread_time_ns()
    found = generate.placement_cells(points, weights, direction, outer, side, keep=keep, clip=clip)
    cpu_ns = time.thread_time_ns() - cpu_start
    wall_ns = time.perf_counter_ns() - wall_start
    result = dict(round=round_index, direction=direction_index, pid=os.getpid(),
                  start_ns=wall_start, end_ns=wall_start + wall_ns,
                  wall_ns=wall_ns, cpu_ns=cpu_ns, parts_ns=T.parts.copy(),
                  mass=found[0][0] if found else None,
                  meta=T.meta.copy())
    return found, result


def parallel_solve_rows():
    source = inspect.getsource(colgen.solve_rows)
    old = """        for index, direction in enumerate(directions):
            for mass, cu, cv, covers in placement_cells(
                points,
                site_weights,
                direction,
                outer,
                side,
                keep=rows_per_direction,
                clip=clip,
            ):
"""
    new = """        tasks = ((points, site_weights, direction, outer, side, rows_per_direction,
                  clip, round_index, index) for index, direction in enumerate(directions))
        for index, (found, profile) in enumerate(_DIRECTION_POOL.map(_profile_task, tasks)):
            _PROFILES.append(profile)
            for mass, cu, cv, covers in found:
"""
    source = replace_once(source, old, new)
    scope = {}
    exec(source, colgen.__dict__, scope)
    return scope["solve_rows"]


def serial_solve_rows():
    source = inspect.getsource(colgen.solve_rows)
    old = """            for mass, cu, cv, covers in placement_cells(
                points,
                site_weights,
                direction,
                outer,
                side,
                keep=rows_per_direction,
                clip=clip,
            ):
"""
    new = """            found, profile = _profile_task((points, site_weights, direction, outer,
                                      side, rows_per_direction, clip, round_index, index))
            _PROFILES.append(profile)
            for mass, cu, cv, covers in found:
"""
    source = replace_once(source, old, new)
    scope = {}
    exec(source, colgen.__dict__, scope)
    return scope["solve_rows"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, choices=(1, 16), required=True)
    parser.add_argument("--max-rounds", type=int, default=60)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    install_profile()
    original = bench_colgen.solve_rows
    colgen.__dict__["_PROFILES"] = []
    colgen.__dict__["_profile_task"] = task
    solver = serial_solve_rows() if args.workers == 1 else parallel_solve_rows()
    captured = {}

    def timed(*positional, **keywords):
        if args.workers == 1:
            solution = solver(*positional, **keywords)
        else:
            with ProcessPoolExecutor(max_workers=16, initializer=install_profile) as pool:
                colgen.__dict__["_DIRECTION_POOL"] = pool
                try:
                    solution = solver(*positional, **keywords)
                finally:
                    del colgen.__dict__["_DIRECTION_POOL"]
        captured["least_covered"] = solution.least_covered
        captured["round_timings_exact"] = [vars(t) if hasattr(t, "__dict__") else {
            key: getattr(t, key) for key in ("index", "separation_seconds", "lp_seconds",
            "rows_held", "rows_added", "violated", "support", "objective")
        } for t in keywords["timings"]]
        return solution

    bench_colgen.solve_rows = timed
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
        report = bench_colgen.bench_rounds(case, grids, max_rounds=args.max_rounds)
    finally:
        bench_colgen.solve_rows = original
    report.update(captured)
    report["workers"] = args.workers
    report["profiles"] = colgen.__dict__["_PROFILES"]
    report["start_method"] = mp.get_start_method()
    args.out.write_text(json.dumps(report) + "\n")
    print(f"{args.workers} workers: {report['row_run']['seconds']} s, {len(report['profiles'])} directions", flush=True)


if __name__ == "__main__":
    main()
