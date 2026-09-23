#!/usr/bin/env python3
"""Capture real NumPy operation inputs from n=12 without editing source files."""
from __future__ import annotations

import inspect
import json
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, '/home/user/DEV/squares/packing')
from devtools import bench_colgen
from sqpack.fractional import colgen, generate

OUT = Path('/tmp/squares-numpy-capture-20260923')
OUT.mkdir(exist_ok=True)
N_DIRECTIONS = 181
ROUND0 = {0, 17, 26, 27, 62, 64, 140}
active = None
records = []
calls = []


def meta(array):
    return {
        'shape': list(array.shape), 'dtype': str(array.dtype),
        'elements': int(array.size), 'nbytes': int(array.nbytes),
        'strides': list(array.strides),
        'c_contiguous': bool(array.flags.c_contiguous),
        'f_contiguous': bool(array.flags.f_contiguous),
    }


def wanted():
    return active is not None and (active['round'] == 18 or
                                   (active['round'] == 0 and active['direction'] in ROUND0))


def save_array(kind, array, **extra):
    if not wanted():
        return
    name = f"r{active['round']:02d}_d{active['direction']:03d}_{kind}.npy"
    np.save(OUT / name, array)
    records.append({**active, 'operation_input': kind, 'file': name, **meta(array), **extra})


def capture_grid(grid):
    save_array('grid', grid)


def capture_flat(flat, take):
    save_array('flat', flat, take=int(take))


def transform(function, old, new):
    source = inspect.getsource(function)
    if source.count(old) != 1:
        raise RuntimeError(f'{function.__name__}: expected one insertion point')
    namespace = {}
    exec(source.replace(old, new), function.__globals__, namespace)
    return namespace[function.__name__]


def main():
    global active
    original_event_grid = generate.event_grid
    original_colgen_placement = colgen.placement_cells
    transformed_event_grid = transform(
        original_event_grid,
        '    mass = np.cumsum(np.cumsum(grid, axis=1), axis=0)[:-1, :-1]',
        '    _CAPTURE_GRID(grid)\n    mass = np.cumsum(np.cumsum(grid, axis=1), axis=0)[:-1, :-1]',
    )
    transformed_placement = transform(
        generate.placement_cells,
        '    order = np.argpartition(flat, take)[: take + 1]',
        '    _CAPTURE_FLAT(flat, take)\n    order = np.argpartition(flat, take)[: take + 1]',
    )

    def wrapped_placement(points, weights, direction, outer, side, *, keep, clip=None):
        global active
        round_index, direction_index = divmod(len(calls), N_DIRECTIONS)
        active = {'round': round_index, 'direction': direction_index,
                  'support': int(np.count_nonzero(weights))}
        start = time.perf_counter()
        try:
            return transformed_placement(points, weights, direction, outer, side,
                                         keep=keep, clip=clip)
        finally:
            calls.append({'round': round_index, 'direction': direction_index,
                          'support': active['support'], 'seconds': time.perf_counter()-start})
            active = None

    generate.__dict__['_CAPTURE_GRID'] = capture_grid
    generate.__dict__['_CAPTURE_FLAT'] = capture_flat
    generate.event_grid = transformed_event_grid
    colgen.placement_cells = wrapped_placement
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                                   inset=case.inset)
        report = bench_colgen.bench_rounds(case, grids)
    finally:
        generate.event_grid = original_event_grid
        colgen.placement_cells = original_colgen_placement
        del generate.__dict__['_CAPTURE_GRID']
        del generate.__dict__['_CAPTURE_FLAT']

    result = {'capture_records': records, 'calls': calls,
              'solver': report, 'python': sys.version, 'numpy': np.__version__}
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    row = report['row_run']
    print(json.dumps({'out': str(OUT), 'captured_arrays': len(records),
                      'rounds': row['rounds'], 'rows': row['rows'],
                      'objective': row['objective'], 'stopped': row['stopped'],
                      'wall': row['seconds'], 'separation': row['separation_seconds'],
                      'lp': row['lp_seconds']}))
    assert len(records) == 2*(181+len(ROUND0))
    assert (row['rounds'], row['rows']) == (23, 5481)
    assert abs(row['objective'] - 12.217676366606284) < 1e-12
    assert row['stopped'] == 'converged: every placement covers mass 1'


if __name__ == '__main__':
    main()
