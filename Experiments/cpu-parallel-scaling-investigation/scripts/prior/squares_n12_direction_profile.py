"""Time n=12 separation calls without changing repository source."""

from __future__ import annotations

import json
import time
from fractions import Fraction
from pathlib import Path

from devtools import bench_colgen
from sqpack.fractional import colgen, generate

OUTPUT = Path('/tmp/squares_n12_direction_timings.json')
CASE = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
N_DIRECTIONS = len(CASE.half_tangents())
ARGS = ['rounds', '--n', '12', '--side', '99/25']

original_placement_cells = colgen.placement_cells
original_event_grid = generate.event_grid
records: list[dict[str, int | float]] = []
active_call: int | None = None


def timed_event_grid(*args: object, **kwargs: object) -> object:
    started = time.perf_counter()
    try:
        return original_event_grid(*args, **kwargs)
    finally:
        elapsed = time.perf_counter() - started
        if active_call is not None:
            record = records[active_call]
            record['event_grid_s'] += elapsed
            record['event_grid_calls'] += 1


def timed_placement_cells(*args: object, **kwargs: object) -> object:
    global active_call
    call_index = len(records)
    round_index, direction_index = divmod(call_index, N_DIRECTIONS)
    records.append({
        'round_index': round_index,
        'direction_index': direction_index,
        'placement_cells_s': 0.0,
        'event_grid_s': 0.0,
        'event_grid_calls': 0,
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
    generate.event_grid = timed_event_grid
    try:
        return bench_colgen.main(ARGS)
    finally:
        colgen.placement_cells = original_placement_cells
        generate.event_grid = original_event_grid
        OUTPUT.write_text(json.dumps({
            'case': CASE.label(),
            'directions_per_round': N_DIRECTIONS,
            'calls': len(records),
            'complete_rounds': len(records) // N_DIRECTIONS,
            'records': records,
        }, indent=2) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
