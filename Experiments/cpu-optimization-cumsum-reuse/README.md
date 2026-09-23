# In-place cumsum on the current selector-fixed solver

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. This branch changes only the two prefix passes in `event_grid`: `np.add.accumulate` writes into the difference grid in place, which no subsequent code needs in its unaccumulated form. No dependency is added.

**READY TO CONSIDER FOR MERGE.** Correctness is **TRAJECTORY IDENTICAL**. The 22-round, 5,643-row objective 12.21767636660579 and least covered mass 0.9999999999995074 match the controlled base. Every round's held rows, added rows, violation count, support, and objective match the base reports in serial and 16-process runs. A captured real 980×980 grid produced bitwise equal mass values for nested and in-place prefix sums.

| Mode | Base wall | Candidate median wall (min–max) | Saved | Separation | LP | Round 0 |
|---|---:|---:|---:|---:|---:|---:|
| Serial | 43.679 s | 43.389 s (43.338–43.412) | 0.290 s (0.7%) | 33.330 s vs 33.664 s base | 10.056 s | 3.154 s |
| 16-process research harness | 17.568 s | 16.248 s (16.093–16.257) | 1.320 s (7.5%) | 5.897 s vs 7.266 s base | 10.190 s | 0.742 s |

Three unprofiled solver runs per mode are preserved in `full-w{1,16}-{1,2,3}.json`. The 16-process path is the existing research harness; this branch does not productionize parallel directions. Serial end-to-end gain is small, so the main merge case is the 16-process setting.

On a captured late-round grid, isolated nested cumsum averaged 5.578 ms serial and 12.322 ms per worker at 16, versus 4.222 and 5.973 ms for a conservative copy-plus-in-place call. Peak extra tracked allocation was 15,367,262 bytes nested and 7,683,624 bytes for copy-plus-in-place. Production does not need the copy, so it avoids both full-grid output arrays. This measurement is in `operation.json`; full solver peak RSS was not recorded in the controlled baseline, so no comparable peak-RSS delta is claimed. The prior `cpu-parallel-scaling-investigation` reported a similarly favorable isolated operation but modest original-solver gain, so this branch relies on fresh end-to-end measurements after the selector fix.

## Reproduce

From `packing/`, set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`:

```bash
uv run --frozen --no-dev python ../Experiments/cpu-optimization-cumsum-reuse/bench_cumsum.py --out /tmp/cumsum-operation.json
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 1 --out /tmp/cumsum-serial.json
uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 16 --out /tmp/cumsum-parallel.json
```

The microbenchmark extracts the already committed real grid from `Experiments/cpu-parallel-scaling-investigation/workloads/` into a temporary directory; no binary data is duplicated here. `environment.json` records versions and machine metadata.
