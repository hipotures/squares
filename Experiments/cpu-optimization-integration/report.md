# Sequential CPU optimization integration

The integration starts from main commit `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. Each accepted production change receives its own checkpoint commit. The operator's pre-existing `.agents`, `.claude`, `.codex`, `AGENTS.md`, and `CLAUDE.md` deletions and the untracked scaling investigation are outside these commits. Main is local; it has not been pushed. GPU work is outside this study.

The primary case is `n=12`, outer side `99/25`, square side `9977/10000`, with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`. [`environment.json`](environment.json) records Python, NumPy, SciPy, platform and CPU count. Each [`raw/`](raw/) timing file contains the complete per-round search trajectory, stop reason, objective, least-covered value and split times. `results.json` contains the machine-readable medians and source/checkpoint commits.

| Checkpoint | Optimization | Input baseline | Worker 1 wall, min/median/max | Worker 16 wall, min/median/max | Separation median, 1/16 | LP median, 1/16 | Round 0 median, 1/16 | Verdict |
|---|---|---|---:|---:|---:|---:|---:|---|
| M0 | Current main | — | 44.162 / **44.253** / 44.444 s | unavailable in production | 34.153 / — s | 10.097 / — s | 3.118 / — s | control |
| M1 | Parallel directions | M0 | 44.052 / **44.217** / 44.642 s | 17.431 / **17.641** / 17.718 s | 34.175 / 7.340 s | 10.115 / 10.289 s | 3.141 / 1.023 s | **ACCEPT** |
| M2 | Persistent HiGHS LP | M1 | 34.076 / **34.448** / 34.987 s | 7.762 / **7.925** / 7.929 s | 33.265 / 6.666 s | 1.179 / 1.238 s | 3.072 / 1.026 s | **ACCEPT** |
| M3 | Maskless slab selection | M2 | 33.854 / **34.193** / 34.297 s | 6.155 / **6.409** / 6.570 s | 32.995 / 5.029 s | 1.213 / 1.258 s | 3.127 / 0.871 s | **ACCEPT** |
| M4 | In-place cumsum reuse | M3 | 31.132 / **31.404** / 31.738 s | 5.430 / **5.480** / 5.755 s | 30.225 / 4.220 s | 1.167 / 1.242 s | 2.104 / 0.646 s | **ACCEPT** |

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

M1 was recorded by checkpoint commit `4d8620adacb9d392471fdc401124df53e16a7569`.

## M2: persistent HiGHS LP

Source research: `exp/cpu-highs-incremental` at `d37e1c13d5566aea24794072784f94ad89d29054`. Input baseline: M1 at `4d8620adacb9d392471fdc401124df53e16a7569`. Production integration commit: `ee137447725930323858965cd36b463b6f177b26`. The production owner in `colgen.py` keeps one HiGHS model for each `solve_rows()` invocation, appends only new rows, and retains the valid simplex basis on reoptimization. The public standalone `solve_lp()` remains available to callers outside that lifecycle. `highspy==1.15.1` is an explicit runtime dependency in `pyproject.toml` and `uv.lock`; `uv lock --check` passed. The lock update removed obsolete `uv` option metadata while leaving all pre-existing package versions unchanged.

**Correctness: SEMANTICALLY EQUIVALENT, DIFFERENT TRAJECTORY.** M2 converges in 23 rounds and 5,842 rows, compared with M1's 22 and 5,643. Its objective `12.217676366606236` differs from M1 by `4.46e-13`, comfortably below a `1e-9` floating comparison tolerance. Its least-covered value is `0.9999999999998309`, and the normal stop reason is coverage convergence. All six timed runs had the same M2 per-round search decisions. The [LP audit](raw/m2-lp-feasibility.json) checked all 22 returned LP points: minimum held-row coverage `0.9999999999861181`, valid retained basis at every solve, matching dual length, and maximum objective recomputation residual `3.55e-15`. The [exact retained-row diagnostic](raw/m2-exact-rows.json) checked all 5,842 rows: no centre outside the exact domain, all 92 boundary coefficient discrepancies had exact nearby witnesses, and none remained unresolved. Thirty-three focused tests passed, including warm-start checkpoint behavior and the production direction pool.

The checkpoint test previously demanded bitwise equality of weights after rebuilding an LP model at a chunk boundary. The row matrix and direction ordering still match exactly; two weights differed by only `5.55e-17`, while the objective differed by `4.44e-16`. That test now uses `1e-12` absolute tolerance for the floating LP point and keeps exact row/checkpoint comparisons. This change records the solver-basis behavior rather than suppressing a row-generation difference.

Against M1, M2 saves **9.769 s (22.1%) serial** and **9.716 s (55.1%) at 16 workers**. The worker-16 LP median falls from 10.289 to 1.238 s; separation also moves from 7.340 to 6.666 s because the valid LP basis selects a different row path. This is an integrated end-to-end gain, not the old research branch estimate. Parent peak RSS median rises from 351,984 to 538,804 KiB serial and from 356,864 to 530,672 KiB at 16 workers; aggregate child RSS is unmeasured. The extra model memory is a material tradeoff. Independent speedups are not added together.

M2 commands, from `packing/` (each timed endpoint repeated with `run=1,2,3`, alternating 1 and 16):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/bench.py --workers "$jobs" --out "../Experiments/cpu-optimization-integration/raw/m2-w${jobs}-r${run}.json"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/verify_persistent_lp.py --out ../Experiments/cpu-optimization-integration/raw/m2-lp-feasibility.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=1 PYTHONPATH=. uv run --frozen --no-dev python benchmarks/round0_selector/exact_row_check.py --out ../Experiments/cpu-optimization-integration/raw/m2-exact-rows.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=1 PYTHONPATH=. uv run --frozen --no-dev --with pytest python -m pytest tests/test_colgen_persistent_lp.py tests/test_colgen_parallel_directions.py tests/test_colgen_checkpoint.py tests/test_fractional_cutting.py -q
uv lock --check
```

M2 was recorded by checkpoint commit `164cf7521c060355e87857bb392116b74ed2ea82`.

## M3: maskless slab interval selection

Source: `exp/cpu-maskless-selection` at `6d077b05ec6838d9f53fa9920ac440e36129c5fd`. Input baseline: M2 at `164cf7521c060355e87857bb392116b74ed2ea82`. Production integration commit: `039b6bba2c34614361589ad87d7d2370ba0ece17`. The only production file changed was `packing/src/sqpack/fractional/generate.py`; no dependency changed. The LP remained the same production HiGHS implementation for both M2 and M3.

**Correctness: TRAJECTORY IDENTICAL.** The [interval check](raw/m3-interval-equivalence.json) compared 96 real-geometry direction/weight/clip cases covering 57,897,422 reachable cells. Reachable cell sets, their masses bitwise, and ordered 13-candidate selections all matched the full-mask implementation. Sixty focused generate, selector and corner-clip tests passed. The [M2](raw/m2-full-state.json) and [M3](raw/m3-full-state.json) full solver state captures have identical SHA-256 values for complete row directions, centres, coefficient matrix, final weights and duals, along with identical per-round decisions, objective, least-covered value and stop reason. The M2 exact witness check therefore applies to the identical M3 retained rows.

Against M2, the five-run worker-16 median saves **1.516 s (19.1%)**: separation moves from 6.666 to 5.029 s, while LP is 1.238 versus 1.258 s. Worker-1 medians differ by 0.255 s, which is inside their run ranges; no serial gain is claimed. The worker-16 candidate had 2.99% CV, with variation concentrated in separation. Two extra runs were added: all five candidate runs fell between 6.155 and 6.570 s, still below M2's entire 7.762–7.929 s range, so the 16-worker gain remains material despite the scheduling variation.

The [isolated operation probe](raw/m3-operation.json) on a `1111×1111` real site geometry with 802,055 reachable cells measured 10.086 ms for full-mask score/selection and 7.667 ms for compaction. Tracked peak extra allocation fell from 20,984,809 to 13,662,623 bytes, saving 7,322,186 bytes per call. Full parent RSS did not shift consistently: serial medians were 538,804 KiB at M2 and 529,340 KiB at M3; worker-16 medians were 530,672 and 531,312 KiB. Aggregate child RSS was not measured.

M3 commands, from `packing/` (worker 1 repeated three times; worker 16 repeated five times after its initial spread):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/verify_maskless.py --out ../Experiments/cpu-optimization-integration/raw/m3-interval-equivalence.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev --with pytest python -m pytest tests/test_fractional_generate.py tests/test_fractional_selector.py tests/test_fractional_corner_clip.py -q
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/bench.py --workers "$jobs" --out "../Experiments/cpu-optimization-integration/raw/m3-w${jobs}-r${run}.json"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/measure_maskless_ops.py --out ../Experiments/cpu-optimization-integration/raw/m3-operation.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.:src uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/capture_state.py --workers 1 --label M3 --out ../Experiments/cpu-optimization-integration/raw/m3-full-state.json
```

For the M2 cross-check, a detached worktree at the M2 checkpoint was created with `git worktree add --detach /home/user/DEV/squares-worktrees/cpu-integration-m2-control 164cf7521c060355e87857bb392116b74ed2ea82`. The same `capture_state.py` was run with `PYTHONPATH` set to that worktree's `packing` and `packing/src` paths, using the main project's `.venv/bin/python`; the captured module paths in the JSON prove it loaded M2 code. This is a correctness diagnostic, not a timed candidate run.

M3 was recorded by checkpoint commit `b2338d64e1c2bb448f6f570af8923c1a3bdfe999`.

## M4: in-place cumsum reuse

Source: `exp/cpu-cumsum-reuse` at `10dcd18ef65eef51de5bee8532260a3f2e635241`. Input baseline: M3 at `b2338d64e1c2bb448f6f570af8923c1a3bdfe999`. Production integration commit: `be151a7fd069bebf314ef8482ea924981e00c4d2`. Only the two prefix passes in `packing/src/sqpack/fractional/generate.py` changed. No dependency changed.

**Correctness: TRAJECTORY IDENTICAL.** The retained real `980×980` round-18 grid produces bitwise equal mass under nested cumsum and in-place `np.add.accumulate`, as recorded in the [operation result](raw/m4-cumsum-operation.json). Sixty focused generate, selector and corner-clip tests passed. The [M3](raw/m3-full-state.json) and [M4](raw/m4-full-state.json) complete state captures match in row direction order, centres, coefficient matrix, weights, duals and per-round decisions. Both converge in 23 rounds and 5,842 rows at objective `12.217676366606236` and least covered `0.9999999999998309`. The earlier M2 exact retained-row diagnostic covers the identical M4 rows.

Against M3, M4 saves **2.789 s (8.2%) serial** and **0.929 s (14.5%) at 16 workers**. The composed serial gain is much larger than the old standalone experiment's 0.290 s; this interaction was measured, not extrapolated. The worker-16 candidate had 2.41% CV across five runs, with variation in separation. Its full 5.430–5.755 s range remained below M3's 6.155–6.570 s range. Two extra worker-16 runs were added before acceptance.

The isolated real-grid probe measured nested versus copy-plus-in-place cumsum at 6.181 versus 4.246 ms serial CPU per call and 12.068 versus 5.980 ms per worker under 16 processes. Tracked peak extra allocation dropped from 15,367,262 to 7,683,624 bytes even with the probe's conservative copy; production directly reuses the difference grid and needs no copy. Full parent RSS medians moved from 529,340 to 518,116 KiB serial and from 531,312 to 509,600 KiB at 16 workers, but the run ranges overlap, so the measured allocation reduction is stronger evidence than RSS for memory effect. Aggregate child RSS was not measured.

M4 commands, from `packing/` (worker 1 repeated three times; worker 16 repeated five times after its initial spread):

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/measure_cumsum.py --out ../Experiments/cpu-optimization-integration/raw/m4-cumsum-operation.json
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev --with pytest python -m pytest tests/test_fractional_generate.py tests/test_fractional_selector.py tests/test_fractional_corner_clip.py -q
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/bench.py --workers "$jobs" --out "../Experiments/cpu-optimization-integration/raw/m4-w${jobs}-r${run}.json"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.:src uv run --frozen --no-dev python ../Experiments/cpu-optimization-integration/capture_state.py --workers 1 --label M4 --out ../Experiments/cpu-optimization-integration/raw/m4-full-state.json
```

The current accepted production checkpoint is **M4**. The fixed-size top-13 selector is next; it must first beat this composed maskless selection path before native packaging is considered.
