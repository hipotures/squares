# Test 3: independent fixed-share processes

`scripts/independent.py` launches one process per visible guest vCPU, pins each
to a distinct guest CPU, preloads and warms the captured current workload, then
synchronizes a common start. Each process repeatedly computes a predetermined
share of all 23 rounds × 181 directions. No ProcessPool, futures, task feed,
array transfer, or result transport occurs in the timed region. A barrier
marks the common end; checksums and small results are transferred only after
timing. The warm pass hashes placement mass, centre, and packed covering mask
for every direction/round pair. Sorting those hashes into canonical order
gives the same SHA-256 at every process count.

Optional `--perf` attaches counters to the warm worker PIDs before the timed
region. Raw JSON and perf CSV are retained. `scripts/summarize.py` verifies
one common checksum and reports min/median/max/CV.

This control isolates the direction computation. Its timed region excludes
the production pool's argument/result serialization and parent's row handling;
those differences are the intended diagnostic, not a replacement solver.
