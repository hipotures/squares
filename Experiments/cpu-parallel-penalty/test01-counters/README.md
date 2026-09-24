# Test 1: instructions, cycles, scheduler wait, DRAM-origin fills

`scripts/bench_proc.py` replays the complete accepted 23-round separation
workload with a persistent four-direction ProcessPool. It reads worker CPU and
`/proc/<pid>/schedstat` only before and after each timed batch. The timed
region contains repeated complete in-memory replays. `scripts/bench_perf.py`
attaches perf to warm worker PIDs, then measures the same long batch. Perf is
detached afterward. `scripts/summarize.py` retains every sample and reports
min, median, max, and population CV in `processed/summary.json`.

All measured events in the primary group ran 100% of enabled time. Guest
`perf_event_paranoid` was initially 4; the operator made it -1, after which
instructions, cycles, and DRAM-origin fill events executed. No guest system
configuration was changed by these scripts.

`ls_any_fills_from_sys.all_dram_io` counts a cache-fill class, not physical
DDR bytes. No `fills × 64` number is labeled physical bandwidth.
