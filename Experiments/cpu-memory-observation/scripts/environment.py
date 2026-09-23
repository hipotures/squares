#!/usr/bin/env python3
"""Record guest-visible machine and perf-event access state without changing it."""
import json, os, pathlib, platform, subprocess
root=pathlib.Path(__file__).resolve().parents[1]
def read(path):
    try:return pathlib.Path(path).read_text().strip()
    except OSError as e:return f"unavailable: {e}"
perf=subprocess.run(['perf','stat','-e','cycles,instructions,cache-misses','--','true'],text=True,capture_output=True)
data={'captured_utc':subprocess.run(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True,capture_output=True).stdout.strip(),
      'kernel':platform.release(),'platform':platform.platform(),'cpu_count':os.cpu_count(),
      'affinity':sorted(os.sched_getaffinity(0)),'cpuinfo':read('/proc/cpuinfo').splitlines()[4:6],
      'meminfo':read('/proc/meminfo').splitlines()[:5], 'cgroup':read('/proc/self/cgroup'),
      'perf_event_paranoid':read('/proc/sys/kernel/perf_event_paranoid'),
      'perf_stat_returncode':perf.returncode,'perf_stat_stdout':perf.stdout,'perf_stat_stderr':perf.stderr,
      'notes':'Read-only inspection; no kernel or perf security settings changed.'}
(root/'raw/environment.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
