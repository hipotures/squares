"""Time NumPy argpartition and cumsum within n=12 placement calls."""

from __future__ import annotations

import json
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import colgen

OUTPUT = Path('/tmp/squares_n12_numpy_ops_timings.json')
CASE = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
N_DIRECTIONS = len(CASE.half_tangents())
ARGS = ['rounds', '--n', '12', '--side', '99/25']

original_placement_cells = colgen.placement_cells
original_argpartition = np.argpartition
original_cumsum = np.cumsum
records: list[dict[str, int | float]] = []
active_call: int | None = None


def timed_argpartition(*args: object, **kwargs: object) -> object:
    if active_call is None:
        return original_argpartition(*args, **kwargs)
    started = time.perf_counter()
    try:
        return original_argpartition(*args, **kwargs)
    finally:
        record = records[active_call]
        record['argpartition_s'] += time.perf_counter() - started
        record['argpartition_calls'] += 1


def timed_cumsum(*args: object, **kwargs: object) -> object:
    if active_call is None:
        return original_cumsum(*args, **kwargs)
    started = time.perf_counter()
    try:
        return original_cumsum(*args, **kwargs)
    finally:
        record = records[active_call]
        record['cumsum_s'] += time.perf_counter() - started
        record['cumsum_calls'] += 1


def timed_placement_cells(*args: object, **kwargs: object) -> object:
    global active_call
    call_index = len(records)
    round_index, direction_index = divmod(call_index, N_DIRECTIONS)
    records.append({
        'round_index': round_index,
        'direction_index': direction_index,
        'placement_cells_s': 0.0,
        'argpartition_s': 0.0,
        'argpartition_calls': 0,
        'cumsum_s': 0.0,
        'cumsum_calls': 0,
    })
    active_call = call_index
    started = time.perf_counter()
    try:
        return original_placement_cells(*args, **kwargs)
    finally:
        records[call_index]['placement_cells_s'] = time.perf_counter() - started
        active_call = None


def main() -> int:
    colgen.placement_cells = timed_placement_cells
    np.argpartition = timed_argpartition
    np.cumsum = timed_cumsum
    try:
        return bench_colgen.main(ARGS)
    finally:
        colgen.placement_cells = original_placement_cells
        np.argpartition = original_argpartition
        np.cumsum = original_cumsum
        rounds: list[dict[str, int | float]] = []
        for start in range(0, len(records), N_DIRECTIONS):
            calls = records[start:start + N_DIRECTIONS]
            rounds.append({
                'round_index': start // N_DIRECTIONS,
                'direction_calls': len(calls),
                'placement_cells_s': sum(r['placement_cells_s'] for r in calls),
                'argpartition_s': sum(r['argpartition_s'] for r in calls),
                'argpartition_calls': sum(r['argpartition_calls'] for r in calls),
                'cumsum_s': sum(r['cumsum_s'] for r in calls),
                'cumsum_calls': sum(r['cumsum_calls'] for r in calls),
            })
        OUTPUT.write_text(json.dumps({
            'case': CASE.label(),
            'directions_per_round': N_DIRECTIONS,
            'calls': len(records),
            'rounds': rounds,
            'records': records,
        }, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
