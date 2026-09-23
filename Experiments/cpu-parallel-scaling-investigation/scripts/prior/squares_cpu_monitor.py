"""Sample aggregate CPU and memory for a benchmark process tree via /proc."""
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
            pid = int(entry.name)
            out[pid] = (int(fields[1]), int(fields[11]) + int(fields[12]), int(fields[21]) * page)
        except (OSError, ValueError, IndexError):
            continue
    return out


def tree(data, root):
    members = {root}
    previous = -1
    while previous != len(members):
        previous = len(members)
        members.update(pid for pid, (ppid, _, _) in data.items() if ppid in members)
    return [data[pid] for pid in members if pid in data]

samples = []
previous = None
while True:
    now = time.monotonic()
    data = processes()
    if args.pid not in data:
        break
    members = tree(data, args.pid)
    ticks = sum(item[1] for item in members)
    rss = sum(item[2] for item in members)
    if previous is not None:
        elapsed = now - previous[0]
        cores = (ticks - previous[1]) / hz / elapsed
        samples.append({'t': now, 'cores': cores, 'rss_bytes': rss, 'processes': len(members)})
    previous = (now, ticks)
    time.sleep(args.interval)
args.out.write_text(json.dumps({'root_pid': args.pid, 'samples': samples}, indent=2) + '\n')
if samples:
    cs = [x['cores'] for x in samples]
    ms = [x['rss_bytes'] for x in samples]
    print(json.dumps({'samples': len(samples), 'average_cores': sum(cs)/len(cs), 'peak_cores': max(cs), 'peak_rss_gib': max(ms)/2**30, 'peak_processes': max(x['processes'] for x in samples)}))
