# Test 6: address translation / transparent huge pages

`scripts/bench.py` creates two anonymous `mmap` buffers per worker, aligns
the NumPy views to 2 MiB boundaries, and applies either `MADV_NOHUGEPAGE` or
`MADV_HUGEPAGE` to both. It prefaults the input and output, performs the same
copy plus production prefix on the complete real round-18 grid, and checks
its full output SHA-256 against the reference. All workers are pinned to
distinct guest vCPUs.

Every sample retains `/proc/<pid>/smaps` receipts for both mappings before
and after timing, including `KernelPageSize`, `MMUPageSize`, and
`AnonHugePages`. The script records whether at least 8 MiB of transparent
huge pages were actually obtained per worker. A successful `madvise` call
alone is not treated as proof. Perf instructions/cycles/DRAM-origin fills,
the guest-executable L1 DTLB miss/L2 miss event, worker CPU, minor faults,
and long-sample wall are retained. No system-wide
transparent huge-page setting is changed.

`scripts/run_pairs.py` ran three adjacent 20-second normal/huge pairs at
each worker count. `scripts/summarize.py` preserves min/median/max/CV and
per-call perf counters in `processed/summary.json`. `AnonHugePages` was 0
KiB for normal mappings and at least 32 MiB per huge-page worker before
every timed pair.
