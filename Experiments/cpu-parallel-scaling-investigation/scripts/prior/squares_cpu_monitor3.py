"""Sample CPU core use and RSS for a process tree, retaining exited workers' CPU time."""
import argparse
import json
import os
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--pid', type=int, required=True)
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--interval', type=float, default=0.25)
args = parser.parse_args()
hz = os.sysconf('SC_CLK_TCK')
page = os.sysconf('SC_PAGE_SIZE')

def processes():
    out = {}
    for entry in os.scandir('/proc'):
        if not entry.name.isdecimal():
            continue
        try:
            raw = Path(entry.path, 'stat').read_text()
            fields = raw[raw.rfind(')') + 2:].split()
            out[int(entry.name)] = (int(fields[1]), int(fields[11]) + int(fields[12]), int(fields[21]) * page)
        except (OSError, ValueError, IndexError):
            pass
    return out

def tree(data, root):
    members = {root}
    previous = -1
    while previous != len(members):
        previous = len(members)
        members.update(pid for pid, (ppid, _, _) in data.items() if ppid in members)
    return {pid: data[pid] for pid in members if pid in data}

samples = []
last_ticks = {}
previous_time = None
while True:
    now = time.monotonic()
    data = processes()
    if args.pid not in data:
        break
    members = tree(data, args.pid)
    if previous_time is not None:
        ticks_delta = sum(max(0, entry[1] - last_ticks.get(pid, 0)) for pid, entry in members.items())
        elapsed = now - previous_time
        samples.append({'t': now, 'cores': ticks_delta / hz / elapsed, 'elapsed_s': elapsed, 'cpu_s': ticks_delta / hz,
                        'rss_bytes': sum(entry[2] for entry in members.values()),
                        'processes': len(members)})
    last_ticks.update({pid: entry[1] for pid, entry in members.items()})
    previous_time = now
    time.sleep(args.interval)
args.out.write_text(json.dumps({'root_pid': args.pid, 'samples': samples}, indent=2) + '\n')
if samples:
    cores = [x['cores'] for x in samples]
    print(json.dumps({'samples': len(samples), 'average_cores': sum(x['cpu_s'] for x in samples)/sum(x['elapsed_s'] for x in samples),
        'peak_cores': max(cores), 'peak_rss_gib': max(x['rss_bytes'] for x in samples)/2**30,
        'peak_processes': max(x['processes'] for x in samples)}))
