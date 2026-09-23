# Persistent HiGHS LP experiment

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. This branch changes no production code or project dependency. Its prototype is activated only by the scripts here. It uses `highspy` 1.15.1 from an isolated `uv --with` invocation.

## Result

**PROMISING BUT NEEDS MORE WORK.** The three unprofiled solver medians were 34.461 s serial and 7.786 s with the existing 16-process direction research harness, against controlled base medians of 43.679 s and 17.568 s. The gain is 9.218 s (21.1%) serial and 9.782 s (55.7%) at 16 processes. LP time fell from 10.089 to 1.160 s serial and from 10.249 to 1.250 s at 16 processes. The persistent simplex model itself took 0.049 s to append rows and 0.907 s to solve on the base row sequence, versus 9.968 s for fresh SciPy calls.

The solver converged in 23 rounds and 5,842 rows at objective 12.217676366606236 and least covered mass 0.9999999999998309. The base had 22 rounds, 5,643 rows, objective 12.21767636660579. **Correctness: SEMANTICALLY EQUIVALENT, DIFFERENT TRAJECTORY.** Different optimal bases change weights and duals; the resulting row choices are valid. The existing exact row diagnostic checked all 5,842 retained rows: zero centres outside the exact domain and zero rows without an exact nearby witness. Of 92 boundary-centre coefficient discrepancies, all 92 had exact nearby witnesses. The loop stopped by coverage, and every persistent LP point met its held constraints to at least 0.9999999998901166 in the same-row comparison.

## LP comparison on identical rows

| Method | Total LP s | Update s | Solve s | Result |
|---|---:|---:|---:|---|
| SciPy fresh `linprog(method="highs")` | 9.968 | included | included | Base trajectory |
| Persistent `highspy` simplex, automatic retained basis | 0.956 | 0.049 | 0.907 | Feasible, objective within 4.4e-9 each round |
| Persistent interior point | 41.482 | 0.051 | 41.431 | Slower |
| Persistent simplex, presolve off | 0.981 | 0.049 | 0.932 | Slightly slower |

The basis is retained by `highspy` after `addRows`: a direct API probe showed `getBasis().valid` remains true as rows are appended. Explicitly resetting this retained basis would reproduce the same state; no separate warm-start transfer is needed. SciPy's public `linprog` call used here has no append-row model lifecycle. Its bundled HiGHS wrapper is private, so production integration would introduce a direct `highspy` dependency and a new model-owner lifecycle. This branch leaves that decision for the operator.

Peak parent RSS across the prototype runs was 505–587 MiB serial and 544–580 MiB at 16 processes. The controlled base did not record comparable RSS, so the memory delta is unmeasured. The 16-process result uses the existing research direction pool and does not imply this branch productionizes that pool.

## Reproduce

From `packing/`, set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1` and `PYTHONPATH=.:../Experiments/cpu-optimization-highs-incremental`:

```bash
uv run --frozen --no-dev --with highspy==1.15.1 python ../Experiments/cpu-optimization-highs-incremental/bench_lp.py --out /tmp/highs-comparison.json
uv run --frozen --no-dev --with highspy==1.15.1 python ../Experiments/cpu-optimization-highs-incremental/run_highs.py --out /tmp/highs-serial.json
uv run --frozen --no-dev --with highspy==1.15.1 python ../Experiments/cpu-optimization-highs-incremental/run_highs.py --workers 16 --out /tmp/highs-parallel.json
uv run --frozen --no-dev --with highspy==1.15.1 python ../Experiments/cpu-optimization-highs-incremental/verify_rows.py --out /tmp/highs-exact-rows.json
```

`comparison.json` contains each individual LP round, update and solve time, objective/weight/dual difference, and feasibility. `integrated-{1,2,3}.json` and `integrated-w16-{1,2,3}.json` contain complete per-round trajectories and timings. `exact-rows.json` is the exact witness check. `environment.json` records the local environment. No binary workload is duplicated; the solver regenerates its rows.
