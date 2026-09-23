# Sequential CPU optimization integration

The integration starts from main commit `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. Each accepted production change receives its own checkpoint commit. The operator's pre-existing `.agents`, `.claude`, `.codex`, `AGENTS.md`, and `CLAUDE.md` deletions and the untracked scaling investigation are outside these commits. Main is local; it has not been pushed. GPU work is outside this study.

The primary case is `n=12`, outer side `99/25`, square side `9977/10000`, with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`. [`environment.json`](environment.json) records Python, NumPy, SciPy, platform and CPU count. Each [`raw/`](raw/) timing file contains the complete per-round search trajectory, stop reason, objective, least-covered value and split times. `results.json` contains the machine-readable medians and source/checkpoint commits.

| Checkpoint | Optimization | Input baseline | Worker 1 wall, min/median/max | Worker 16 wall, min/median/max | Separation median, 1/16 | LP median, 1/16 | Round 0 median, 1/16 | Verdict |
|---|---|---|---:|---:|---:|---:|---:|---|
| M0 | Current main | — | 44.162 / **44.253** / 44.444 s | unavailable in production | 34.153 / — s | 10.097 / — s | 3.118 / — s | control |
| M1 | Parallel directions | M0 | 44.052 / **44.217** / 44.642 s | 17.431 / **17.641** / 17.718 s | 34.175 / 7.340 s | 10.115 / 10.289 s | 3.141 / 1.023 s | **ACCEPT** |

## M0: current main control

Main had no production direction worker setting, so a production 16-worker M0 endpoint is unavailable. The separately preserved 16-process research harness measured 17.568 s historically, but it is not substituted for this production control. Three fresh, unprofiled worker-1 runs converged in 22 rounds and 5,643 rows, with objective `12.21767636660579`, least covered `0.9999999999995074`, and stop reason `converged: every placement covers mass 1`. All three per-round decision trajectories match.

M0 command, from `packing/` (repeated with `run=1,2,3`):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python benchmarks/round0_selector/solver_benchmark.py --workers 1 --out ../Experiments/cpu-optimization-integration/raw/m0-w1-r${run}.json
```

## M1: production parallel directions

Source: `exp/cpu-parallel-directions` at `9fca9e8c66a5d05a71803e3e0796531568c7c850`. Input baseline: M0 at `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. Production integration commit: `accd54aad5a003540d59adbeb3f84facb058b561`. Changed production files: `packing/src/sqpack/fractional/colgen.py` and the focused `packing/tests/test_colgen_parallel_directions.py`. No dependency change.

**Correctness: TRAJECTORY IDENTICAL.** Worker 1 and worker 16 both reproduce M0's 22 rounds, 5,643 rows, per-round rows held/added, violations, support and objective, final objective, least-covered value, and convergence reason. [`raw/m1-full-row-equivalence.json`](raw/m1-full-row-equivalence.json) also checks the complete row direction order, centres, coefficient matrix, weights and duals between production worker paths; every check passes, with equal matrix SHA-256. The focused tests passed (2 tests). The [exact retained-row diagnostic](raw/m1-exact-rows.json) checked all 5,643 rows: no centre outside the exact domain, and all 79 boundary coefficient discrepancies had a nearby exact witness.

M1 worker 16 saves **26.612 s**, or **60.1% wall time**, against the measured M0 serial median. M1 worker 1 is within run-to-run variation of M0, so there is no claimed serial gain. The production worker 16 median is also close to the old research-harness 16-process result. Parent peak RSS was 350,936–359,076 KiB at worker 1 and 356,260–358,136 KiB at worker 16; aggregate child RSS was not measured. `PACK_JOBS` is a per-step cap, not a cross-process semaphore, so nested callers should request one worker.

M1 commands, from `packing/` (each endpoint repeated with `run=1,2,3`, alternating 1 and 16):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/bench.py --workers "$jobs" --out "../Experiments/cpu-optimization-integration/raw/m1-w${jobs}-r${run}.json"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev --with pytest python -m pytest tests/test_colgen_parallel_directions.py -q
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/verify_parallel_rows.py --out ../Experiments/cpu-optimization-integration/raw/m1-full-row-equivalence.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=1 PYTHONPATH=. uv run --frozen --no-dev python benchmarks/round0_selector/exact_row_check.py --out ../Experiments/cpu-optimization-integration/raw/m1-exact-rows.json
```

The checkpoint is **M1**. Subsequent candidates must be compared with M1 or later accepted checkpoints under the same production worker path.
