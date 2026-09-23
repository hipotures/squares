# Post-round-zero CPU workload profile

Measured on current `main` at `9b9a529e9269fcbdd4fc1a27627b6f1d697ffb2a`, with `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, and `MKL_NUM_THREADS=1`. The case is `n=12`, outer side `99/25`, square side `9977/10000`, 181 directions, and the production selector. The sixteen-process runner is the existing persistent direction `ProcessPoolExecutor` benchmark. Solver wall below excludes the separately timed pricing step. [Run provenance](manifests/run.json), [all six baseline runs](results/), and [exact per-round medians](results/trajectory.json) are retained.

## 1. Current CPU baseline

| CPU | Solver wall median | Separation median | LP median | Round 0 separation median | Rounds | Rows | Objective | Least covered | Pricing median |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Serial | 43.679 s | 33.664 s | 10.089 s | 3.040 s | 22 | 5,643 | 12.21767636660579 | 0.9999999999995074 | 0.446 s |
| 16 processes | 17.568 s | 7.266 s | 10.249 s | 0.955 s | 22 | 5,643 | 12.21767636660579 | 0.9999999999995074 | 0.466 s |

The three serial wall runs were 43.657, 43.679, and 44.083 s; the sixteen-process runs were 17.568, 17.526, and 17.624 s. All six had the **same 22-round trajectory**, including per-round support, held and added rows, violations, and objective. Round 21 had zero violations and no LP call. The final result is numerically identical across runs. Medians are taken independently by field, so their sums need not exactly equal the median wall.

Representative per-round medians:

| Round | Support | Rows held | Added | Violated | Serial separation | Serial LP | 16-process separation | 16-process LP |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 0 | 483 | 483 | 543 | 3.040 s | 0.057 s | 0.955 s | 0.065 s |
| 10 | 537 | 3,804 | 281 | 543 | 1.958 s | 0.444 s | 0.369 s | 0.453 s |
| 18 | 617 | 5,546 | 86 | 198 | 2.546 s | 0.750 s | 0.616 s | 0.749 s |
| 19 | 649 | 5,621 | 75 | 177 | 2.889 s | 0.931 s | 0.701 s | 0.939 s |
| 21 | 581 | 5,643 | 0 | 0 | 2.539 s | 0 | 0.597 s | 0 |

Every round's exact values and medians are in [`trajectory.json`](results/trajectory.json).

## 2. Separation decomposition

The in-memory instrumented serial run took 44.859 s wall, 34.768 s separation, and 10.088 s LP; the corresponding sixteen-process run took 17.441, 7.305, and 10.124 s. Relative to unprofiled medians, the serial profile added 1.180 s wall (2.7%) and 1.104 s separation (3.3%); the parallel differences were -0.127 s wall and +0.039 s separation, within run variation. All profiled runs followed the exact baseline row trajectory. Serial seconds and percentages in this table are **direct profiled per-thread CPU measurements** divided by the profiled 34.768 s separation. Sixteen-process wall contributions are **estimates normalized to the new 7.266 s separation median**.

| Operation, exclusive categories | Serial CPU s | Serial % | Estimated 16-process wall s |
|---|---:|---:|---:|
| Candidate selection, including ties and ordering | 15.954 | 45.9% | 2.731 |
| First and second cumsum | 13.243 | 38.1% | 2.528 |
| Reachable-mask construction | 1.994 | 5.7% | 0.336 |
| `np.where` scored array | 1.895 | 5.5% | 0.686 |
| Four `np.searchsorted` calls | 0.285 | 0.8% | 0.031 |
| Grid allocation | 0.204 | 0.6% | 0.093 |
| Two `np.unique` calls | 0.188 | 0.5% | 0.032 |
| Other `event_grid` work | 0.183 | 0.5% | 0.049 |
| `domain.v_range` | 0.128 | 0.4% | 0.026 |
| Four `np.add.at` calls | 0.107 | 0.3% | 0.317 |
| u/v projection | 0.056 | 0.2% | 0.013 |
| Live-point filter and gather | 0.032 | 0.1% | 0.007 |
| Event arithmetic and concatenate | 0.029 | 0.1% | 0.006 |
| Placement reconstruction | 0.035 | 0.1% | 0.006 |
| Coverage-mask construction | 0.094 | 0.3% | 0.018 |
| `weights[covers].sum()` | 0.053 | 0.2% | 0.008 |
| Sorting returned candidates | 0.008 | <0.1% | 0.001 |
| Other placement loop work | 0.157 | 0.5% | 0.127 |
| Row generation/bookkeeping outside placements | 0.121 | 0.3% | included in parent gaps and residual |
| Parallel parent gaps and pool overhead | — | — | 0.251 |

`event_grid` totaled 16.45 s of serial CPU, including 13.24 s of cumulative sums. `placement_cells` after `event_grid` is dominated by candidate selection. Within selection, `np.argpartition` itself took 15.11 s serial; cutoff/tie handling and ordering took the remaining ~0.84 s. The selector's sixteen-process aggregate worker CPU was 39.51 s, of which `argpartition` was 34.23 s. The two cumulative sums used 36.76 s aggregate worker CPU. Small operation inflation factors are sensitive to scheduling and timer overhead; they are not GPU targets.

The first cumsum took 6.030 s serial CPU and 12.135 s aggregate worker CPU; the second took 7.213 s and 24.625 s. In non-zero rounds, the tie scan used 0.379 s serial CPU, cutoff/below/concatenate/finite checks together used ~0.055 s, and lexicographic ordering used 0.014 s. Candidate reconstruction, coverage masks, exact weight sums, and returned-candidate sorting are shown separately above. The new zero-weight selector has no `argpartition` call.

**Wall-estimation method.** Each direction task records its worker CPU time, operation CPU time, and absolute start/end. For each round, overlapping worker intervals are merged into one active wall interval. That active interval is allocated to operations by their fraction of aggregate worker CPU in the round; gaps outside worker activity are parent overhead. The resulting wall shares are scaled from the profiled run to the 7.266 s unprofiled median. This is a throughput attribution, not a counterfactual guarantee: overlapping worker CPU times are never added as wall time. The full per-direction trace and [reduction script](scripts/analyze.py) make the estimate reproducible.

| Dominant operation | Serial CPU | 16-process aggregate worker CPU | Concurrency inflation | Estimated 16-process wall |
|---|---:|---:|---:|---:|
| Candidate selection | 15.954 s | 39.513 s | 2.48× | 2.731 s |
| Double cumsum | 13.243 s | 36.760 s | 2.78× | 2.528 s |
| Scored `np.where` | 1.895 s | 10.031 s | 5.29× | 0.686 s |
| Reachable mask | 1.994 s | 4.842 s | 2.43× | 0.336 s |

LP is separate: its new sixteen-process median is 10.249 s and it is not part of the GPU target.

## 3. Round zero, profiled independently

The full unprofiled baseline has 3.040 s serial and 0.955 s sixteen-process round-zero separation. A fresh round-zero-only unprofiled serial control measured 2.990, 3.292, and 3.029 s. The full instrumented run measured 2.723 s for round zero, and a separate round-zero-only instrumented run measured 2.733 s. Thus the **round-zero instrumentation reads about 10% lower than the unprofiled control**, despite the same outputs; its operation split is diagnostic rather than a precise unprofiled absolute allocation.

Within the 2.723 s full serial profile: double cumsum 1.813 s; reachable mask 0.201 s; other `event_grid` 0.108 s; new zero-weight selector 0.287 s (`zero_validate` and zero-index extraction dominate); scored `np.where` 0.221 s; reconstruction, masks, weight sums and sorting 0.012 s; all remaining Python and row work 0.082 s. The sixteen-process profile attributes about 0.392 s wall to cumsum, 0.150 s to the selector, 0.097 s to `np.where`, 0.046 s to reachability, and 0.187 s to parent/pool startup within its 0.939 s normalized round-zero wall. The old pathological round-zero `argpartition` case is absent. Round zero is a secondary target after the steady-state work.

## 4. Steady state and representative late round

Rounds 1–21 consumed 32.046 s in the serial profile and an estimated 6.327 s of the new sixteen-process baseline. Serial CPU: selection 15.667 s (48.9%), double cumsum 11.430 s (35.7%), reachable construction 1.793 s (5.6%), and scored `np.where` 1.675 s (5.2%). Estimated sixteen-process wall: selection 2.581 s, cumsum 2.135 s, scored array 0.590 s, and reachable construction 0.290 s. Their combined 5.597 s is 88% of steady-state separation wall.

Current round 18 had support 617, 181 directions, and 5,546 held rows. Its median unprofiled separation was 2.546 s serial and 0.616 s with sixteen processes. The instrumented serial round spent 1.255 s in selection (`argpartition` 1.211 s), 0.921 s in double cumsum, 0.145 s in scoring, and 0.148 s constructing reachability. The sixteen-process trace measured 0.609 s separation; worker-active allocation estimates ~0.228 s wall each for selection and cumsum, ~0.059 s for scoring, and ~0.024 s for reachability. This is the relevant late-round workload, not the zero-weight selector.

## 5. Complete 181-direction CPU replay

The [replay](results/replay-round18.json) runs the **current merged selector** and current nested double cumsum on every archived real round-18 direction input. The archive was captured on an older trajectory, so its array shapes differ from the current full solver round 18; see the next section. Each worker pool is persistent during its timed passes. Inputs are memory mapped and warmed once. Each figure below is the median of three complete 181-direction passes, including task dispatch but excluding pool construction and archive extraction. The one- and sixteen-worker replay both use `fork` so mapped input pages are shared; the full solver's Python 3.14 default is `forkserver`.

| Operation | Archived input bytes | One-worker wall | Sixteen-worker wall | Sixteen-worker aggregate CPU | Sixteen-worker throughput |
|---|---:|---:|---:|---:|---:|
| Current 13-candidate finite selector | 1.380 GB | 1.150 s | **0.179 s** | 2.649 s | 1,010 directions/s |
| Double cumsum | 1.383 GB | 0.996 s | **0.160 s** | 2.287 s | 1,130 directions/s |

The archived selector inputs have 24,025–958,441 float64 cells per direction, versus the current round-18 solver's 26,569–1,104,601 cells. Selection and cumsum are the only individual operations exceeding 10% of serial separation; scoring and reachability are measured in the full solver because they are required to keep a fused pipeline resident.

## 6. GPU data contract, no GPU execution

From the **current** round-18 trace, 180 directions have a 1,052 × 1,052 float64 difference grid and one has a 164 × 164 grid. All have 3,737 point sites (`float64[3737,2]`) and 3,737 site weights (`float64[3737]`); 525 carry weight for these event grids. Points are 59,792 bytes and site weights 29,896 bytes once per round; two float64 direction coefficients add 2,896 bytes across all 181 directions. The common outer and square sides add 16 bytes. Repeating points and weights independently for every direction would move 16.234 MB.

| Current round-18 stage | Input bytes for 181 directions | Output bytes for 181 directions |
|---|---:|---:|
| `event_grid` from points/weights/direction, exact current return fields | ~0.090 MB shared plus direction scalars | 1.807 GB of projected coordinates, event axes, mass, reachable flags, and slab ranges |
| Double cumsum alone | 1.594 GB difference grids | 1.591 GB mass arrays |
| Candidate selection alone | 1.591 GB scored float64 arrays | 18,824 bytes for 13 int64 indices per direction |
| Current `placement_cells` return, up to 3 candidates/direction | event-grid arrays internally | 13,032 bytes of mass/coordinates plus up to 2,029,191 bytes of Boolean coverage masks |

A naive separate cumsum and selector port would send the 1.594 GB grids, return the 1.591 GB mass, send the 1.591 GB scored array, and return 18,824 bytes of indices: **4.776 GB** of transfer for this one round, before grid construction. Keeping cumsum, reachability, scoring, and selection resident can instead send 1.594 GB of grids plus ~6.062 MB of event axes and per-slab ranges, then return 18,824 bytes of selected indices. If reachability stays on CPU, its mask adds 198.855 MB of input. If grid construction also remains resident, the per-round point/weight input is only 89,688 bytes plus direction scalars; this requires GPU handling of variable event sets and is a later interface choice, not a speed claim.

The CPU solver can reconstruct the 13 surveyed cells from returned indices and its retained event axes, then build the actual coverage masks and exact candidate masses locally. If GPU reconstruction is included, a lower-bound result interface is three `(mass,u,v)` float64 triples per direction, **13,032 bytes** for all 181 directions; the CPU can rebuild Boolean masks from those coordinates. The exact current `placement_cells` return includes the masks and is about 2.042 MB at three candidates per direction. Not every direction actually yields three violated rows, so this is an upper bound for the row builder. At this round, 180 grids share a shape while direction zero differs; batching all 181 requires padding/masking or segmented variable-size handling. Shape and byte arithmetic are retained in [`data-contract.json`](results/data-contract.json).

## 7. Amdahl limits from the new sixteen-process baseline

Use 17.568 s solver wall, 7.266 s separation, and the measured non-separation remainder **10.302 s** (including 10.249 s LP and ~0.053 s overhead). The conservatively identified GPU-suitable group is **double cumsum + reachability + scored `np.where` + candidate selection**, measured at an estimated **6.281 s** of sixteen-process separation wall. Reconstruction, masks, row bookkeeping, LP, and the rest of event construction are excluded.

| Acceleration | Whole solver if all separation accelerated | Speedup | Whole solver if only measured GPU group accelerated | Speedup |
|---:|---:|---:|---:|---:|
| 2× | 13.935 s | 1.261× | 14.427 s | 1.218× |
| 5× | 11.755 s | 1.494× | 12.543 s | 1.401× |
| 10× | 11.029 s | 1.593× | 11.915 s | 1.474× |
| 20× | 10.665 s | 1.647× | 11.601 s | 1.514× |
| Infinite | **10.302 s** | **1.705×** | **11.287 s** | **1.557×** |

If round zero remains on CPU and only the steady-state 5.597 s group is accelerated, its infinite-speed floor is 11.971 s, a 1.468× whole-program limit. Thus a 1.5× whole-program gain needs some round-zero acceleration or more than this steady-state group. The 10.302 s absolute floor assumes unchanged LP and unchanged other non-separation work.

## 8. Explicit GPU threshold and first target

| Target versus 17.568 s CPU baseline | Maximum GPU separation wall, with 10.302 s non-separation unchanged |
|---|---:|
| Merely beat CPU | **<7.266 s** |
| 1.25× whole-program speedup | **<3.752 s** |
| 1.5× whole-program speedup | **<1.410 s** |
| 2× whole-program speedup | impossible: would require negative separation wall |

The absolute theoretical solver floor with LP and other non-separation work unchanged is **10.302 s**. Even making all separation infinitely fast yields only 1.705×, so 2× is mathematically impossible under that constraint.

**First prototype target:** benchmark one fused, direction-batched GPU path from the current CPU-built difference grid and event-axis/slab-range inputs through **double cumsum, reachable-mask construction, scored-array construction, and finite top-13 selection**, returning only selected indices. Keep the mass and scored grids resident. This targets the measured 6.281 s sixteen-process wall group (5.597 s in steady state) and avoids the 4.776 GB separate-operation round-trip. Do not start with the fixed round-zero selector or candidate reconstruction/masks. A future prototype must compare its *end-to-end transfer plus compute* against the 0.179 s selector and 0.160 s cumsum 181-direction CPU replay, and ultimately reduce full-solver separation below the thresholds above.

If all other measured work stays fixed, that 6.281 s group itself must fall below 2.768 s (about 2.27× faster) for a 1.25× whole-solver gain, and below 0.425 s (about 14.8× faster) for 1.5×. Those group figures include all rounds; leaving round zero on CPU cannot reach 1.5× with this group alone.

## 9. Verdict

**GPU MICROBENCHMARK JUSTIFIED.** The current CPU still spends most separation wall in two large-array kernels and the scoring/reachability steps needed between them. A fused resident path has enough measured wall to make a 1.25× whole-solver gain possible, while LP sets a hard ceiling. No GPU code or speed estimate was produced here.
