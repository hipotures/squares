# Interval reachability without full mask or scored matrix

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. This branch keeps the existing difference-grid and double-cumsum mass calculation. It changes only reachability and candidate selection. `event_grid()` retains its full reachable-matrix default for callers that request it; production `placement_cells()` asks for interval compaction instead. Per u-slab, strict event bounds and `_REACH_SLACK` become `[first,last)` v-index intervals. Reachable masses are packed into one float64 array; small interval metadata maps the selected compact indices back to original cell coordinates. No full boolean reachable matrix, full float64 `np.where` scored array, or full reachable-index array is made in production selection.

**READY TO CONSIDER FOR MERGE. Correctness: TRAJECTORY IDENTICAL.** The interval check compared all reachable flat indices, their masses, and ordered 13 candidates against the original implementation over 48 directions across zero, sparse, and denser weight patterns. It found exact equality. The full solver matched all 22 rounds' held rows, additions, violations, support, and objective at one and 16 workers. The final result is 5,643 rows, objective 12.21767636660579, least covered 0.9999999999995074. The existing exact retained-row witness gate for that identical trajectory remains applicable. Focused fractional selector and generator tests passed (21 tests); Ruff passed.

| Mode | Base wall | Candidate median wall (min–max) | Saved | Base separation | Candidate separation | Candidate LP |
|---|---:|---:|---:|---:|---:|---:|
| Serial | 43.679 s | 43.524 s (42.442–43.583) | 0.155 s (0.4%) | 33.664 s | 33.315 s | 10.098 s |
| 16-process research harness | 17.568 s | 15.457 s (15.411–15.588) | 2.111 s (12.0%) | 7.266 s | 5.255 s | 10.199 s |

Serial spread exceeds the 0.155 s difference, so this branch makes **no serial end-to-end speed claim**. The 16-process result is stable across three unprofiled full runs. On a 1,111×1,111 real site geometry with 802,055 reachable cells, the isolated scoring/selection path took 10.038 ms and 20,984,809 tracked peak extra bytes in the base form, versus 7.215 ms and 13,662,623 bytes with interval compaction. That is 7.32 MB less tracked per-call allocation. The microbenchmark starts after the event grid is built, so it does not credit the branch for avoiding reachable-matrix construction; it is conservative on that point. Full solver peak RSS was not recorded in the controlled base, so no RSS delta is claimed. Complexity is moderate: interval endpoints and index remapping must retain exact strict comparison semantics. No dependency is added.

## Reproduce

From `packing/`, set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` and `PYTHONPATH=.`:

```bash
uv run --frozen --no-dev python ../Experiments/cpu-optimization-maskless-selection/check_intervals.py
uv run --frozen --no-dev python ../Experiments/cpu-optimization-maskless-selection/bench_maskless.py
uv run --frozen --no-dev --with pytest python -m pytest tests/test_fractional_selector.py tests/test_fractional_generate.py -q
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 1 --out /tmp/maskless-serial.json
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 16 --out /tmp/maskless-parallel.json
```

`interval_check.json`, `operation.json`, `trajectory-check.json`, and `full-w{1,16}-{1,2,3}.json` hold correctness and timing evidence. `environment.json` records machine and version metadata. No binary workload is duplicated.
