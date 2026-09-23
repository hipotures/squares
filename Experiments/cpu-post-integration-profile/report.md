# Post-integration n=12 CPU profile

## Scope and method

The measured production input is main commit `14ba672d999fa34b77d422a4a3e1f43e14df572e` at `n=12`, outer side `99/25`, square side `9977/10000`. All controlled runs set `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`. [`environment.json`](environment.json) records the 16-vCPU KVM machine, AMD Ryzen 9 7950X3D model exposed by the VM, RAM, kernel, Python, NumPy, SciPy, HiGHS, compiler, native selector, and thread limits. Each important [raw sample](raw/) records load and CPU pressure before timing. [`README.md`](README.md) gives exact reproduction commands, and [`results.json`](results.json) is recalculated by [`scripts/summarize.py`](scripts/summarize.py).

Every retained timed batch lasted **19.1–49.2 seconds**. Three independent batches were taken for each endpoint. A batch repeats complete independent solves, or complete in-memory 23-round replays, until it exceeds 10 seconds; file loading and JSON writing are outside timed regions. The [audit](raw/final-audit.json) validates all 69 retained sample durations and solver outcomes. No sample was rejected. An initial 16-worker replay had 7% CV; its three samples remain saved, followed by three longer 37–41-second batches. The longer CV was still 5.5%, so VM variation is included in the ranges and paired controls are used for small candidate comparisons. The benchmark code does not include Python startup in batch wall, but complete-solve batches include normal site/model setup and process-pool creation. `results.json` gives min, median, max, and CV for every reported timing endpoint, including those summarized only by median in the tables below.

## 1. Robust current baseline

This is a **fresh measurement of integrated main**. Each entry is the median of three unprofiled batch samples. Min/max and raw per-round trajectories are in `results.json` and the linked raw files. `CV` is the coefficient of variation of normalized solver wall.

| Workers | Solves / batch | Batch wall median | Solver wall median (min–max) | Separation | LP | Round 0 | CV | Correctness |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 1 | 21.829 s | **21.829** (21.827–21.835) s | 20.679 s | 1.120 s | 2.111 s | 0.02% | Passed |
| 4 | 3 | 23.538 s | **7.846** (7.836–7.850) s | 6.643 s | 1.158 s | 0.979 s | 0.09% | Passed |
| 8 | 4 | 21.188 s | **5.297** (5.253–5.302) s | 4.135 s | 1.133 s | 0.636 s | 0.51% | Passed |
| 16 | 5 | 20.473 s | **4.095** (3.956–4.213) s | 2.863 s | 1.181 s | 0.444 s | 3.14% | Passed |

Sixteen workers remain fastest. The fresh [correctness solve](raw/baseline-correctness.json) at every worker count has **23 rounds, 5,842 rows, objective `12.217676366606236`, least covered `0.9999999999998309`**, and normal coverage convergence. Row ordering, centres, and the entire coefficient matrix match. The [fresh state hashes](raw/current-identity.json) match the accepted M5 record, so its [exact retained-row witness check](../cpu-optimization-integration/raw/m5-exact-rows.json) applies: no centre outside the exact domain, and all 92 boundary discrepancies have exact nearby witnesses. The baseline samples also retain every round's rows, violations, support, objective, separation, and LP time. Parent CPU time is retained; `RUSAGE_CHILDREN` does not capture forkserver grandchildren here, so worker CPU is measured separately through `/proc` in the replay.

## 2. End-to-end wall accounting

At 16 workers the production round timers explain **4.044 of 4.095 seconds, or 98.8%** of solver wall. The residual includes setup and round bookkeeping. The aggregate CPU column comes from the corresponding steady-state replay, so it is diagnostic and must not be added to wall time.

| Component | Wall contribution | Share of end-to-end | Aggregate CPU contribution | Confidence |
|---|---:|---:|---:|---|
| Separation, all 23 rounds | 2.863 s | 69.9% | 35.4 s worker CPU plus 1.08 s parent CPU in replay | High for wall; medium for CPU transfer to full solve |
| LP, 22 incremental solves | 1.181 s | 28.8% | 1.175 s parent CPU in direct LP replay | High |
| Setup and other round work | 0.049 s | 1.2% | Included in parent CPU; not isolated | Medium |

The explicit operation timers add 1.1% to serial separation replay wall and 4.7% to 16-worker replay wall relative to uninstrumented replay. The profiled LP replay is 1.3% *faster* than the reference replay, within run conditions; no profile percentage is adjusted by a speculative correction. Component rankings below are supported by both timed profiles and the full-solver control.

## 3. Current separation critical path

The unprofiled, warmed 16-worker replay of the **complete accepted 23-round, 181-direction-per-round sequence** takes a 2.697 s median, versus 2.863 s separation in the full solver. The 0.166 s difference includes pool startup, LP interleaving/cache effects, and different parent bookkeeping; the replay is used to resolve the separation path, not substituted for end-to-end wall. [`verify_profile_grid.py`](scripts/verify_profile_grid.py) established bitwise identity for the timed event-grid copy across 905 real cases and 695,327,309 mass cells.

| Worker operation | Serial aggregate time | 16-worker aggregate time | 16-worker last-finishing-worker path proxy | What it does |
|---|---:|---:|---:|---|
| Prefix accumulation | 11.507 s | 15.423 s | 0.985 s | Two in-place passes over the full difference grid |
| Reachable compaction | 7.075 s | 13.246 s | 0.847 s | Find each admissible slab interval and copy its masses into a compact array |
| Difference scatter | 0.700 s | 2.839 s | 0.186 s | Place weighted events at four grid corners |
| Native top-13 selection | 1.313 s | 2.829 s | 0.187 s | Stable finite top-k scan of compact masses |
| Candidate reconstruction | 0.290 s | 0.680 s | 0.042 s | Recover centres and covering masks for selected cells |
| Projection, event sorting, domain bounds | 0.367 s | 0.878 s | 0.057 s | Geometry and small arrays |

The path proxy sums operations performed by the worker whose last task completes each round. It identifies the wall-sensitive work, but is **not an exact causal wall attribution**: scheduling, ordered result collection, and work on other workers overlap. Parent replay wall is directly accounted as 2.386 s in `next(result)` (worker computation, transport, and deserialization together), 0.248 s processing rows, 0.051 s dispatching, and about 0.012 s other. Parent CPU is 1.079 s; it is not asleep for all 2.386 seconds inside `next`. Workers consume 35.4 CPU seconds over 2.697 wall seconds, or 13.1 effective cores. Worker task wall and CPU are close, but the remaining 2.9 core-equivalent gap cannot be assigned precisely among barriers, task dispatch, and other VM effects. Row processing is necessary to map masks to orbit coefficients and deduplicate rows, with only a 0.25 s measured wall opportunity even if removed entirely.

## 4. Current LP profile

An in-memory replay of the exact 22 captured row appends runs for 19.9–20.9 seconds per sample and reproduces the accepted objective and final held-row feasibility. The uninstrumented LP sequence is 1.174 s median; the explicit-timer sequence is 1.159 s batch-normalized. A separate [three-sample process CPU replay](raw/lp-cpu-s1.json) measured 1.175 s parent CPU per LP sequence (1.171–1.179 s). The operations inside the phase timer sum to about 1.145 s per sequence:

| LP operation | Time / sequence | Share of timed LP work |
|---|---:|---:|
| HiGHS simplex `run()` / reoptimization | 1.034 s | 90.3% |
| Dense held-row stacking | 0.056 s | 4.9% |
| HiGHS `addRows()` | 0.030 s | 2.6% |
| New-row CSR conversion and arrays | 0.020 s | 1.8% |
| Solution/dual extraction | 0.004 s | 0.3% |
| Model creation and residual Python work | <0.002 s | <0.2% |

The basis is retained inside HiGHS; production does not explicitly rebuild it. Eliminating all measured row stacking/conversion/interface work would save at most about 0.11 s of a 4.095 s solve, before implementation overhead and without touching the numerical solver. LP housekeeping is therefore a small current target. Changing solver options or the optimal basis risks a different row trajectory and has no measured case here.

## 5. Current worker scaling

These are unprofiled, in-memory separation replays with a persistent pool. `Worker CPU` is the sum of `/proc/<pid>/stat` CPU deltas over workers, excluding the separately measured parent CPU. At one worker it is the parent's CPU. Effective cores = worker CPU / wall; CPU inflation = worker CPU relative to the one-worker workload. All entries are medians of three long batches.

| Workers | Separation wall / replay | Worker CPU / replay | Effective cores | Speedup | Efficiency | CPU inflation | CV |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 21.129 s | 21.120 s | 1.00 | 1.00× | 100% | 1.00× | 0.59% |
| 2 | 11.864 s | 23.415 s | 1.97 | 1.78× | 89% | 1.11× | 0.41% |
| 4 | 6.562 s | 25.653 s | 3.91 | 3.22× | 81% | 1.21× | 0.30% |
| 8 | 3.894 s | 29.842 s | 7.66 | 5.43× | 68% | 1.41× | 1.11% |
| 16 | 2.697 s | 35.403 s | 13.12 | 7.83× | 49% | 1.68× | 5.53% |

The previous qualitative scaling penalty **still exists** after the five integrated optimizations: 16 workers do 1.68 times as much aggregate CPU work as serial on the same separation sequence. They nevertheless win on wall time. The 16-worker 40-second sample range is 2.656–2.939 s per replay; the original 20-second set, with 7% CV, remains in `raw/` and was not discarded. CPU pressure and per-replay spread are recorded. The data show inflation and variation, but do not identify DRAM bandwidth saturation as a cause.

## 6. Current hotspots

Ranked by **wall-critical-path proxy** and supported by aggregate worker CPU:

1. **HiGHS reoptimization, about 1.03 s / 25% of end-to-end wall.** This solves the changing LP basis after new rows; it scales with rows/columns and is mathematically required by the current search. Measured Python and model-update overhead is only ~0.11 s. No safe, material replacement was found.
2. **Full-grid prefix, about 0.99 s / 24% proxy; 15.42 s aggregate worker time.** It computes all cell masses from the event difference grid, scales with cells (2.61 billion grid cells over the full workload), and becomes more expensive per unit of work under concurrency. The row-major C prototype below demonstrates that the second pass has a cheaper bitwise-equivalent traversal. The full grid remains allocated.
3. **Reachable compaction, about 0.85 s / 21% proxy; 13.25 s aggregate worker time.** It scans slab geometry, performs many scalar `searchsorted` calls, and copies 1.89 billion selected values per solve. The vectorized prototype below removes most of the Python interval-search cost with identical scores and ordering. The compact array is still allocated.
4. **Parent row processing, about 0.25 s / 6% of end-to-end wall.** It builds and deduplicates held orbit rows from covering masks. It scales with surveyed placements and rows; the observed cost caps any standalone gain. Dispatch itself is ~0.05 s. Transport/deserialization is mixed with worker waiting and remains unresolved.

The native selector's path proxy is 0.187 s, about 4.6% of full wall and already far below its pre-integration cost. Event sorting, projection, domain bounds, and candidate reconstruction are smaller. The current priority is the two full-array operations, rather than another selector rewrite or LP interface cleanup.

These mechanisms have different scaling. Prefix time rises from 11.51 to 15.42 aggregate worker seconds at 16 workers (1.34× CPU inflation), while compaction rises from 7.08 to 13.25 seconds (1.87×); this is why serial savings cannot be projected directly onto parallel wall. The prefix is an in-place scan, so its grid allocation is necessary to the *current* algorithm but its column traversal is not: the bitwise C experiment is faster. Compaction's 15.13 GB of compact outputs are an avoidable representation in principle; this experiment only removes scalar search overhead, while a direct interval selector remains unmeasured. LP cost grows with retained rows and basis work, with no evidence that its simplex computation can be removed. Parent row processing allocates one 511-coefficient row per violation and checks its byte key; those operations are necessary to the current deduplication contract, and even eliminating the entire measured parent loop offers only 0.25 s. These are statements about this workload and implementation, not lower bounds on all CPU algorithms.

## 7. New research-only CPU experiments

Each prototype is independently applied to **current main**, never stacked with the other. All comparisons use three adjacent long control/candidate pairs; pair 2 reverses execution order. `Saved` and `reduction` are medians of paired differences, so they can differ slightly from subtracting the two marginal medians. All full solves keep the same 23-round/5,842-row trajectory, objective, least-covered value, row order, centres, and coefficient matrix. The existing exact witness evidence therefore applies. Neither prototype was merged.

| Prototype | Workers | Control wall median | Candidate wall median | Paired saved median (range) | Reduction | Timed batch range | Correctness | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|---|
| Vectorized slab intervals | 1 | 21.839 s | 16.413 s | **5.501** (5.421–5.547) s | 25.1% | 21.8–32.9 s | Identical complete state | Strong candidate |
| Vectorized slab intervals | 16 | 4.093 s | 3.731 s | **0.361** (0.348–0.364) s | 8.8% | 39.6–44.8 s | Identical complete state | Strong candidate |
| Row-major C prefix pass | 1 | 22.049 s | 16.567 s | **5.519** (5.282–5.542) s | 25.0% | 21.8–33.2 s | Bitwise grid and identical state | Promising research |
| Row-major C prefix pass | 16 | 4.216 s | 3.941 s | **0.233** (0.116–0.306) s | 5.6% | 41.3–49.2 s | Bitwise grid and identical state | Promising, less stable |

The vectorized prototype replaces the scalar per-slab searches with array `searchsorted`, while preserving the compact values, row IDs, interval starts, offsets, zero-weight survey rule, and stable selector. The [equivalence run](raw/vectorized-equivalence.json) compared all **4,163** direction calls and **1.89 billion** compact values, then checked full one- and 16-worker solves. It adds no dependency and does not remove the compact array. Its 16-worker paired gain is consistent across all three pairs, despite variation in absolute wall.

The prefix prototype changes only the second in-place prefix pass to a simple row-major C loop over the same grid; [`prefix_rows.c`](scripts/prefix_rows.c) and its exact build command are retained. It creates no new grid. The [bitwise equivalence run](raw/prefix-equivalence.json) checked **905** real event grids and **695 million** mass cells, then complete one- and 16-worker solves. Its 16-worker paired gain is positive in every pair but ranges widely; native packaging and a fresh composition test would be needed before integration. The 15,120-byte Linux research library is retained as `raw/libprefix_rows.so`, with compiler and SHA-256 in `environment.json`; the source is authoritative.

**No combined candidate was built or timed.** The two changes touch distinct operations but share the same large-grid memory subsystem. Their individual savings must not be added. Both prototypes are research-only and production source remains unchanged.

## 8. Memory and allocation after the accepted stack

The current full workload creates **20.88 GB of grid arrays** and **15.13 GB of compact float arrays** over its 4,163 direction calls (decimal bytes summed, not simultaneous resident memory). The grid has 2.61 billion cells in total. A representative round-18/direction-26 call uses a `979×979` mass grid (7.67 MB) and 5.90 MB compact values; traced peak allocation for `placement_cells` is 13.77 MB. A round-zero non-axis direction peaks near 29.82 MB. [`memory-probe.json`](raw/memory-probe.json) lists shapes and the 12 inspected cases. The 16 replay workers' resident sets sum to ~1.35 GiB at the last sample, **double-counting shared pages**; individual workers are about 79–95 MiB. Parent peak RSS during full solves was roughly 0.55–0.60 GiB and is a cumulative high-water mark, not independent per sample.

Current 16-worker replays incurred roughly 0.38 million minor worker page faults per complete replay in the median long sample, after pool warmup. They and the large array volumes show that allocation and memory traffic remain relevant. A single warmed late-round call often faults no new pages, so that diagnostic cannot substitute for the whole workload. No direct DRAM counter was available or used; **bandwidth saturation is unresolved**. The vectorized interval prototype retains the compact copy; the C prefix prototype retains the grid, so neither removes the major allocation volumes.

## 9. CPU optimization status

**MODERATE OPPORTUNITY.** The current 16-worker wall is 4.095 s. A simpler research-only change already demonstrates a paired **0.348–0.364 s**, or **8.5–8.9%**, end-to-end reduction on current main; its serial reduction is about 25%. A separate bitwise-equivalent prefix traversal demonstrates another **0.116–0.306 s** (2.8–7.2%) per pair, with more variance and native integration cost. The best measured standalone 16-worker wall is **3.731 s** for vectorized intervals. There is no measured combined wall.

Quantitatively, at least ~0.36 s / 8.8% is clearly removable software overhead in the current 16-worker path. LP is 1.181 s / 28.8% and is dominated by 1.034 s of simplex reoptimization. Explicit parent dispatch and row processing occupy ~0.30 s / 7.3% of separation replay wall, much of it necessary work; ordered result collection/IPC is not separately isolated. The remaining ~2.5 s of separation after the demonstrated vectorized saving includes necessary mass/search computation **and unresolved optimisation potential**. It is not justified to call all of it irreducible or to claim a theoretical CPU floor. The measured standalone 3.731 s is the supported attainable point today.

## 10. Proven, refuted, unresolved

**Proven:** current main's result and exact-witness-checked state are unchanged at 1/4/8/16 workers; 16 workers are fastest among tested counts; >98% of end-to-end wall is accounted for by separation and LP; prefix and compaction dominate separation; LP is mostly HiGHS reoptimization; both research changes preserve the full accepted state and save end-to-end wall independently.

**Refuted:** LP Python/highspy interface overhead is not the dominant current LP cost; a claim that CPU optimisation has reached diminishing returns is inconsistent with the paired prototype gains; a claim that current 16-worker scaling has no inflation is inconsistent with its 1.68× worker CPU inflation.

**Unresolved:** the interaction of the two research changes; the source of sustained 16-worker VM variability; the causal share of IPC inside ordered `next()` waits; hardware DRAM traffic/bandwidth; the gain from removing the compact array or full grid entirely; portability and maintenance cost of productionising the C prefix helper. None is assumed in the attainable wall estimate.

## 11. Recommendation

**Continue targeted CPU optimisation.** The next integration candidate is vectorized slab interval construction: it requires only Python/NumPy code, preserves the full state, and saves about **0.36 s (8.8%)** at 16 workers and **5.50 s (25%)** serial on current main. Integrate and gate it separately. Then rebase the row-major prefix idea onto that new baseline, package/fallback it deliberately if warranted, and rerun three paired long samples before deciding. Its independent 0.23 s median 16-worker gain is promising but cannot be added to the vectorized gain. Do not spend the next cycle on LP bookkeeping or the already-native selector without new evidence.

This study changed only research files under this directory. No production optimization was merged, and no push was performed.
