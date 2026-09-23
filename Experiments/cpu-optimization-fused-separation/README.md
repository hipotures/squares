# Row-streamed separation prototype

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`.

**RESEARCH RESULT ONLY. Correctness: TRAJECTORY IDENTICAL.** This prototype computes each difference-grid row's horizontal prefix in place, adds the prior row's vertical prefix, derives its reachable v interval from the original strict geometry comparisons and `_REACH_SLACK`, and retains only that row's 13 best candidate indices. A final small merge produces the global ordered survey. It reuses the difference grid for mass and does not materialize separate full mass, reachable, scored, or argpartition-index arrays. Round zero uses the merged evenly spaced zero tie policy across all reachable intervals. The default `event_grid()` path stays materialized for callers that request it; `placement_cells()` uses the stream path on this branch.

Forty-eight direction/weight cases matched the base's prefix masses bit for bit and ordered candidates exactly, including zero weights. The full solver matched all 22 per-round row counts, additions, violations, support, and objectives at one and 16 workers, as well as 5,643 final rows, objective 12.21767636660579, and least covered 0.9999999999995074. The existing exact retained-row witness gate applies to this identical trajectory. The focused selector and generator tests passed (21 tests), and Ruff passed.

| Mode | Base wall | Candidate median wall (min–max) | Effect | Base separation | Candidate separation | Candidate LP |
|---|---:|---:|---:|---:|---:|---:|
| Serial | 43.679 s | 58.904 s (58.705–59.122) | **15.225 s slower (34.9%)** | 33.664 s | 48.742 s | 10.159 s |
| 16-process research harness | 17.568 s | 14.881 s (14.853–14.928) | **2.687 s saved (15.3%)** | 7.266 s | 4.646 s | 10.211 s |

Three unprofiled complete solver runs per mode are in `full-w{1,16}-{1,2,3}.json` with per-round trajectories. The 16-process path is the existing research harness; production `solve_rows()` remains serial in this branch. The large serial regression makes the implementation unsuitable for merge as written, despite its 16-worker gain.

On archived real 980×980 grids, the one-process row-streamed probe took about 16.8–16.9 ms versus 13.2–14.2 ms for the materialized baseline, while tracked peak extra allocation fell from about 24.0 MB to 8.3 MB. A separate 16-worker replay of direction 8 measured 31.119 ms baseline versus 18.983 ms streaming CPU per call, and aggregate worker CPU of 9.958 versus 6.075 s over 400 calls. Peak worker RSS fell from 92,396 KiB to 76,504 KiB; the maximum worker wall for 20 calls fell from 0.741 to 0.410 s. The full solver benchmark did not record aggregate worker RSS. These archived grids predate the selector fix; the full solver runs above validate the current trajectory.

The branch has high implementation complexity. The geometric interval calculation, in-place prefix order, per-row tie policy, and reconstruction must all stay aligned with the exact search contract. It adds no package dependency. A future version would need to eliminate the Python per-row overhead or enable this path only where a process pool justifies it; neither change is implemented here.

## Reproduce

From `packing/`, set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` and `PYTHONPATH=.`:

```bash
uv run --frozen --no-dev python ../Experiments/cpu-optimization-fused-separation/check_stream.py
uv run --frozen --no-dev python ../Experiments/cpu-optimization-fused-separation/streaming_probe.py --out /tmp/streaming-probe.json
PYTHONPATH=.:../Experiments/cpu-optimization-fused-separation uv run --frozen --no-dev python ../Experiments/cpu-optimization-fused-separation/parallel_probe.py
uv run --frozen --no-dev --with pytest python -m pytest tests/test_fractional_selector.py tests/test_fractional_generate.py -q
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 1 --out /tmp/fused-serial.json
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 16 --out /tmp/fused-parallel.json
```

`stream_check.json`, `probe.json`, `parallel.json`, `trajectory-check.json`, and the full-run JSONs hold the evidence. Both probes read the already committed lossless round-18 archives from `Experiments/cpu-parallel-scaling-investigation/workloads/`; no binary workload is duplicated. `environment.json` records machine and version metadata.
