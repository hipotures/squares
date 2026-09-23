#!/usr/bin/env python3
"""Temporary /proc sampler for the n=12 ProcessPoolExecutor benchmark."""
from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--pid-file', type=Path, required=True)
p.add_argument('--markers', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--interval', type=float, default=0.05)
a = p.parse_args()
HZ = os.sysconf('SC_CLK_TCK')
PAGE = os.sysconf('SC_PAGE_SIZE')

def stat(pid: int):
    try:
        raw = Path(f'/proc/{pid}/stat').read_text()
        fields = raw[raw.rfind(')') + 2:].split()
        status = Path(f'/proc/{pid}/status').read_text()
        status_values = {}
        for line in status.splitlines():
            if line.startswith(('voluntary_ctxt_switches:', 'nonvoluntary_ctxt_switches:')):
                name, value = line.split(':', 1)
                status_values[name] = int(value.strip())
        try:
            sched = [int(value) for value in
                     Path(f'/proc/{pid}/schedstat').read_text().split()[:3]]
        except (OSError, ValueError):
            sched = [0, 0, 0]
        return {'pid': pid, 'state': fields[0], 'ppid': int(fields[1]),
                'ticks': int(fields[11]) + int(fields[12]),
                'start': int(fields[19]), 'rss': int(fields[21]) * PAGE,
                'minflt': int(fields[7]), 'majflt': int(fields[9]),
                'volcs': status_values.get('voluntary_ctxt_switches'),
                'nonvolcs': status_values.get('nonvoluntary_ctxt_switches'),
                'sched_runtime_ns': sched[0], 'sched_wait_ns': sched[1],
                'sched_timeslices': sched[2]}
    except (OSError, IndexError, ValueError):
        return None

def family(pid: int):
    found = {}
    pending = [pid]
    while pending:
        current = pending.pop()
        entry = stat(current)
        if entry is None:
            continue
        found[current] = entry
        try:
            children = Path(f'/proc/{current}/task/{current}/children').read_text()
            pending.extend(int(child) for child in children.split())
        except OSError:
            pass
    return found

while not a.pid_file.exists():
    time.sleep(0.01)
root = int(a.pid_file.read_text().strip())
samples = []
while True:
    now = time.perf_counter()
    members = family(root)
    if root not in members:
        break
    samples.append({'t': now, 'members': members})
    time.sleep(a.interval)

markers = []
if a.markers.exists():
    markers = [json.loads(line) for line in a.markers.read_text().splitlines() if line]

# Identify the 16 worker PIDs by aggregate CPU time. Exclude the parent, which
# performs all LP work and can have more CPU time than an individual worker.
first, last = {}, {}
for sample in samples:
    for pid_text, entry in sample['members'].items():
        key = (int(pid_text), entry['start'])
        first.setdefault(key, entry['ticks'])
        last[key] = entry['ticks']
ranked = sorted(((value - first[key], key) for key, value in last.items()
                 if key[0] != root), reverse=True)
workers = [key[0] for _, key in ranked[:16]]

windows = {}
starts = {}
for marker in markers:
    key = marker['round']
    if marker['event'] == 'separation_start':
        starts[key] = marker['t']
    elif marker['event'] == 'separation_end' and key in starts:
        windows[key] = (starts[key], marker['t'])

def summarize(rounds):
    intervals = [windows[i] for i in rounds if i in windows]
    wall = sum(end - start for start, end in intervals)
    worker_cpu = {pid: 0.0 for pid in workers}
    worker_activity = {pid: [] for pid in workers}
    counters = {pid: {name: 0.0 for name in
                      ('minflt', 'majflt', 'volcs', 'nonvolcs',
                       'sched_runtime_ns', 'sched_wait_ns', 'sched_timeslices')}
                for pid in workers}
    for prev, nxt in zip(samples, samples[1:]):
        t0, t1 = prev['t'], nxt['t']
        interval_s = t1 - t0
        overlap = sum(max(0.0, min(t1, end) - max(t0, start))
                      for start, end in intervals)
        if overlap <= 0:
            continue
        for pid in workers:
            before = prev['members'].get(pid)
            after = nxt['members'].get(pid)
            if before is None or after is None or before['start'] != after['start']:
                continue
            cpu_s = max(0, after['ticks'] - before['ticks']) / HZ
            share = overlap / interval_s
            worker_cpu[pid] += cpu_s * share
            for name in counters[pid]:
                if before[name] is not None and after[name] is not None:
                    counters[pid][name] += max(0, after[name] - before[name]) * share
            worker_activity[pid].append({'cpu_percent': 100 * cpu_s / interval_s,
                                         'active': cpu_s > 0, 'weight': overlap,
                                         'state': after['state']})
    per_worker = []
    for pid in workers:
        intervals = worker_activity[pid]
        total_weight = sum(item['weight'] for item in intervals)
        per_worker.append({'pid': pid,
                           'cpu_s': worker_cpu[pid],
                           'mean_cpu_percent': 100 * worker_cpu[pid] / wall if wall else None,
                           'median_sample_cpu_percent': statistics.median(
                               item['cpu_percent'] for item in intervals) if intervals else None,
                           'active_sample_fraction': sum(item['weight'] for item in intervals
                                                       if item['active']) / total_weight
                           if total_weight else None,
                           'running_state_fraction': sum(item['weight'] for item in intervals
                                                         if item['state'] == 'R') / total_weight
                           if total_weight else None,
                           'counters': counters[pid]})
    cpu = sum(worker_cpu.values())
    return {'rounds': [i for i in rounds if i in windows],
            'separation_wall_s': wall, 'sampled_worker_cpu_s': cpu,
            'effective_worker_cores': cpu / wall if wall else None,
            'counter_totals': {name: sum(counters[pid][name] for pid in workers)
                               for name in next(iter(counters.values()))},
            'workers': per_worker}

report = {'root_pid': root, 'sample_interval_s': a.interval,
          'worker_pids': workers, 'candidate_cpu_s':
          [{'pid': key[0], 'cpu_s': ticks / HZ} for ticks, key in ranked[:20]],
          'markers': markers,
          'round_0': summarize([0]),
          'late_18_21': summarize(range(18, 22)),
          'late_18_22': summarize(range(18, 23)),
          'all_separation': summarize(range(23)),
          'raw_samples': samples}
a.out.write_text(json.dumps(report) + '\n')
print(json.dumps({key: value for key, value in report.items()
                  if key not in ('raw_samples', 'markers')}))
