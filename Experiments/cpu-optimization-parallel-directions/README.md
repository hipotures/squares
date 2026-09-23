# Production parallel directions

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`.

**READY TO CONSIDER FOR MERGE.** `solve_rows()` now accepts `workers`; with no explicit argument it remains serial unless the repository's existing `PACK_JOBS` cap is set. Explicit counts are capped by `PACK_JOBS` and available CPUs through `worker_count()`. One process pool lives for the complete `solve_rows()` call. `map()` returns direction results in index order, so row insertion and LP decisions remain serial and deterministic. The worker only runs `placement_cells()`; LP and its HiGHS call stay in the parent. No GPU path or dependency was added. Controlled runs set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`; the worker's placement calculation itself has no BLAS call.

**Correctness: TRAJECTORY IDENTICAL.** Workers 1 and 16 matched the controlled base in all 22 per-round held rows, additions, violations, support, and objective, as well as 5,643 final rows, objective 12.21767636660579, and least covered 0.9999999999995074. The focused test compares complete row order, centres, coefficient matrix, primal weights and duals at workers 1 and 2; it also rejects a nonpositive worker count. Both tests pass.

| Workers | Production wall | Separation | LP | Round 0 |
|---:|---:|---:|---:|---:|
| 1 | 44.093 s median (43.798–44.268) | 34.070 s | 10.025 s | 3.210 s |
| 4 | 23.524 s | 13.332 s | 10.184 s | 1.256 s |
| 8 | 19.862 s | 9.689 s | 10.163 s | 1.079 s |
| 16 | 17.648 s median (17.591–17.669) | 7.336 s | 10.241 s | 0.954 s |

Production workers 1→16 saved 26.445 s (60.0% wall reduction, 2.50× throughput). The controlled research-harness 16-process baseline was 17.568 s; production integration is 0.080 s slower, within the small run-to-run and machine variation. The primary win is making the previously measured direction pool available through the real solver API. Three unprofiled end-to-end runs were made at workers 1 and 16, one at 4 and 8. Complete per-round trajectories are in `full-w*-*.json`.

Parent peak RSS was 350–352 MiB at one worker and 357–359 MiB at 16. Aggregate child RSS was not measured; the pool necessarily adds worker processes and copies task arguments per direction. The major operating risk is using this pool inside another process pool: `PACK_JOBS` is only a per-step cap, not a cross-process semaphore. `workers=1` remains available to callers that already parallelize outside this solver.

## Reproduce

From `packing/`, with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` and `PYTHONPATH=.`:

```bash
uv run --frozen --no-dev --with pytest python -m pytest tests/test_colgen_parallel_directions.py -q
uv run --frozen --no-dev python ../Experiments/cpu-optimization-parallel-directions/run_production.py --workers 1 --out /tmp/parallel-production-w1.json
uv run --frozen --no-dev python ../Experiments/cpu-optimization-parallel-directions/run_production.py --workers 4 --out /tmp/parallel-production-w4.json
uv run --frozen --no-dev python ../Experiments/cpu-optimization-parallel-directions/run_production.py --workers 8 --out /tmp/parallel-production-w8.json
uv run --frozen --no-dev python ../Experiments/cpu-optimization-parallel-directions/run_production.py --workers 16 --out /tmp/parallel-production-w16.json
```

`environment.json` records the machine and version metadata. No captured workload is duplicated.
