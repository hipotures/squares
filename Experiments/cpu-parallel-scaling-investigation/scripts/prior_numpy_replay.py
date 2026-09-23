#!/usr/bin/env python3
"""Replay captured real NumPy inputs; no solver inside timed regions."""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import resource
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

CAPTURE = Path(__file__).resolve().parents[1] / 'raw/squares-numpy-capture-20260923'
OPS = ('argpartition', 'axis1', 'axis0', 'double')


def rss_bytes():
    return int(Path('/proc/self/statm').read_text().split()[1]) * os.sysconf('SC_PAGE_SIZE')


def run_one(op, flat, take, grid, tmp):
    if op == 'argpartition':
        out = np.argpartition(flat, take)
    elif op == 'axis1':
        out = np.cumsum(grid, axis=1)
    elif op == 'axis0':
        out = np.cumsum(tmp, axis=0)
    elif op == 'double':
        out = np.cumsum(np.cumsum(grid, axis=1), axis=0)
    else:
        raise ValueError(op)
    scalar = out.flat[0]
    del out
    return float(scalar)


def load_items(indices, records):
    items = []
    for index in indices:
        flat_rec = records[(index, 'flat')]
        grid_rec = records[(index, 'grid')]
        flat = np.load(CAPTURE / flat_rec['file'], allow_pickle=False)
        grid = np.load(CAPTURE / grid_rec['file'], allow_pickle=False)
        assert list(flat.strides) == flat_rec['strides']
        assert list(grid.strides) == grid_rec['strides']
        tmp = np.cumsum(grid, axis=1)
        items.append((flat, flat_rec['take'], grid, tmp))
    return items


def execute(op, repeat, items, start_at, cpu_timer):
    if start_at is not None:
        time.sleep(max(0.0, start_at - time.perf_counter()))
    usage_scope = resource.RUSAGE_THREAD if cpu_timer is time.thread_time else resource.RUSAGE_SELF
    before_fault = resource.getrusage(usage_scope).ru_minflt
    before_rss = rss_bytes()
    cpu_start = cpu_timer()
    wall_start = time.perf_counter()
    checksum = 0.0
    for _ in range(repeat):
        for flat, take, grid, tmp in items:
            checksum += run_one(op, flat, take, grid, tmp)
    wall = time.perf_counter() - wall_start
    cpu = cpu_timer() - cpu_start
    return {'cpu': cpu, 'worker_wall': wall, 'calls': repeat * len(items),
            'checksum': checksum, 'minor_faults': resource.getrusage(usage_scope).ru_minflt - before_fault,
            'rss_before': before_rss, 'rss_after': rss_bytes(),
            'peak_rss': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}


def process_child(conn, indices, records):
    items = load_items(indices, records)
    conn.send({'ready': True, 'pid': os.getpid(), 'rss': rss_bytes()})
    while True:
        cmd = conn.recv()
        if cmd is None:
            return
        op, repeat, start_at = cmd
        conn.send(execute(op, repeat, items, start_at, time.process_time))


class ProcessGroup:
    def __init__(self, workers, records):
        context = mp.get_context('forkserver')
        self.conns = []
        self.procs = []
        for worker in range(workers):
            parent, child = context.Pipe()
            indices = list(range(worker, 181, workers))
            proc = context.Process(target=process_child, args=(child, indices, records))
            proc.start()
            child.close()
            self.conns.append(parent)
            self.procs.append(proc)
        self.ready = [conn.recv() for conn in self.conns]

    def run(self, op, repeat, warm=False):
        start_at = time.perf_counter() + (0.05 if warm else 0.1)
        for conn in self.conns:
            conn.send((op, repeat, start_at))
        results = [conn.recv() for conn in self.conns]
        wall = time.perf_counter() - start_at
        return summarize(results, wall)

    def close(self):
        for conn in self.conns:
            conn.send(None)
        for proc in self.procs:
            proc.join()


class ThreadGroup:
    def __init__(self, workers, records):
        self.items = [load_items(list(range(i, 181, workers)), records)
                      for i in range(workers)]
        self.pool = ThreadPoolExecutor(max_workers=workers)

    def run(self, op, repeat, warm=False):
        start_at = time.perf_counter() + (0.05 if warm else 0.1)
        futures = [self.pool.submit(execute, op, repeat, items, start_at, time.thread_time)
                   for items in self.items]
        results = [future.result() for future in futures]
        wall = time.perf_counter() - start_at
        return summarize(results, wall)

    def close(self):
        self.pool.shutdown()


def summarize(results, wall):
    return {'wall': wall, 'worker_cpu': sum(r['cpu'] for r in results),
            'worker_wall_sum': sum(r['worker_wall'] for r in results),
            'calls': sum(r['calls'] for r in results),
            'checksum': sum(r['checksum'] for r in results),
            'minor_faults': sum(r['minor_faults'] for r in results),
            'rss_before_sum': sum(r['rss_before'] for r in results),
            'rss_after_sum': sum(r['rss_after'] for r in results),
            'peak_rss_sum': sum(r['peak_rss'] for r in results),
            'per_worker': results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('samples', 'process', 'thread'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--repeat', type=int, default=5)
    parser.add_argument('--trials', type=int, default=3)
    parser.add_argument('--ops', default=','.join(OPS))
    parser.add_argument('--workers', default='1,2,4,8,16')
    args = parser.parse_args()
    selected_ops = tuple(args.ops.split(','))
    selected_workers = tuple(int(value) for value in args.workers.split(','))
    assert set(selected_ops) <= set(OPS)
    assert set(selected_workers) <= {1, 2, 4, 8, 16}
    manifest = json.loads((CAPTURE / 'manifest.json').read_text())
    records = {(r['direction'], r['operation_input']): r for r in manifest['capture_records']
               if r['round'] == 18}
    assert len(records) == 362
    results = {'mode': args.mode, 'repeat': args.repeat, 'trials': args.trials,
               'method': '181 real round-18 direction inputs, disjoint per worker, preloaded and warmed',
               'numpy': np.__version__, 'start_method': 'forkserver', 'runs': []}
    if args.mode == 'samples':
        for round_index, directions in ((0, (0, 17, 26, 27, 62, 64, 140)),
                                        (18, (0, 1, 91, 92, 110, 150, 177))):
            bykey = {(r['direction'], r['operation_input']): r for r in manifest['capture_records']
                     if r['round'] == round_index}
            for direction in directions:
                items = load_items([direction], bykey)
                flat, take, grid, tmp = items[0]
                for op in OPS:
                    for _ in range(2):
                        run_one(op, flat, take, grid, tmp)
                    times = []
                    for _ in range(7):
                        t = time.perf_counter()
                        run_one(op, flat, take, grid, tmp)
                        times.append(time.perf_counter() - t)
                    input_array = flat if op == 'argpartition' else tmp if op == 'axis0' else grid
                    results['runs'].append({'round': round_index, 'direction': direction,
                        'op': op, 'input_shape': list(input_array.shape), 'dtype': str(input_array.dtype),
                        'input_bytes': input_array.nbytes, 'elements': input_array.size,
                        'times': times, 'median': statistics.median(times),
                        'min': min(times), 'max': max(times),
                        'elements_per_s': input_array.size/statistics.median(times),
                        'input_bytes_per_s': input_array.nbytes/statistics.median(times),
                        'min_byte_traffic_per_s': (2 if op != 'double' else 4)*input_array.nbytes/statistics.median(times),
                        'output_bytes': input_array.size*8})
    else:
        group_class = ProcessGroup if args.mode == 'process' else ThreadGroup
        total_elements = sum(records[(i, 'grid')]['elements'] for i in range(181))
        total_flat_elements = sum(records[(i, 'flat')]['elements'] for i in range(181))
        results['elements_per_sweep'] = {'argpartition': total_flat_elements,
                                          'axis1': total_elements, 'axis0': total_elements,
                                          'double': total_elements}
        for workers in selected_workers:
            group = group_class(workers, records)
            try:
                for op in selected_ops:
                    group.run(op, 1, warm=True)
                for trial in range(args.trials):
                    order = selected_ops if trial % 2 == 0 else tuple(reversed(selected_ops))
                    for op in order:
                        result = group.run(op, args.repeat)
                        result.update({'workers': workers, 'op': op, 'trial': trial,
                                       'elements_per_s': args.repeat*results['elements_per_sweep'][op]/result['wall'],
                                       'input_bytes_per_s': args.repeat*results['elements_per_sweep'][op]*8/result['wall'],
                                       'effective_cores': result['worker_cpu']/result['wall']})
                        results['runs'].append(result)
                        args.out.write_text(json.dumps(results, indent=2) + '\n')
            finally:
                group.close()
    args.out.write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({'mode': args.mode, 'runs': len(results['runs']),
                      'output': str(args.out)}))


if __name__ == '__main__':
    main()
