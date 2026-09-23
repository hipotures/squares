# Profile trace format

The machine-readable full traces are in `../results/profile-serial.json` and `../results/profile-16.json`; the independent round-zero traces are `../results/profile-round0-w1.json` and `../results/profile-round0-w16.json`. They remain in `results/` because `scripts/analyze.py` reads them directly.

Each `profiles` entry identifies a round, direction and worker PID; records absolute worker start/end, total wall and thread CPU nanoseconds; lists exclusive operation CPU nanoseconds in `parts_ns`; and records grid shape, live-site count and point count in `meta`. `event_grid_total` and `selector_total` are inclusive parents of operation substeps and must not be added to those substeps. `scripts/analyze.py` converts them to exclusive categories, then merges overlapping worker intervals before attributing sixteen-process wall.

The source-clone timer splits the nested cumsum inside a short helper so the first temporary is released immediately after the second cumsum, as in production. The profiler leaves all solver values and the six-run row trajectory unchanged. Its overall overhead and the round-zero timing bias are documented in `../report.md`.
