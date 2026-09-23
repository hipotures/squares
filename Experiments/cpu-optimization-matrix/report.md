# Independent n=12 CPU optimization matrix

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659` (fetched `origin/main` on 2026-09-23 UTC). Every branch below was created directly from this commit in a separate worktree. `git merge-base <branch> <BASE_SHA>` returned exactly this SHA for all six. No branch was merged, and this matrix branch contains no production solver change. GPU work was excluded.

All controlled runs set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`. The common post-selector baseline was 43.679 s serial (33.664 s separation, 10.089 s LP) and 17.568 s in the 16-process research harness (7.266 s separation, 10.249 s LP), with 22 rounds, 5,643 rows, objective 12.21767636660579, and least covered 0.9999999999995074. Each candidate's final full-solver timing used three unprofiled runs per reported 1/16-worker endpoint. Medians, min/max, exact round timings, file lists, and paths to each branch's evidence are in [results.json](results.json).

## End-to-end comparison

All times are seconds. The parallel-directions row compares its **production workers=1 against production workers=16**; all other rows compare the candidate 16-process research-harness run with the common controlled 16-process baseline. Thus the parallel row answers a different, explicitly labelled integration question. “Speedup” is wall reduction, not a sum of independent gains.

| Experiment | Branch / commit | Correctness | Baseline wall | Candidate wall | Seconds saved | Speedup | Separation effect | LP effect | Memory effect | Complexity | Dependency impact | Verdict |
|---|---|---|---:|---:|---:|---:|---|---|---|---|---|---|
| Production parallel directions | [`exp/cpu-parallel-directions`](https://github.com/hipotures/squares/tree/exp/cpu-parallel-directions) `9fca9e8c` | TRAJECTORY IDENTICAL | 44.093 | 17.648 | 26.445 | 60.0% | 34.070→7.336 | 10.025→10.241 | Parent peak 350,336–352,404→357,280–358,680 KiB; child sum unmeasured | Low–moderate | None | **READY TO CONSIDER FOR MERGE** |
| Persistent HiGHS LP | [`exp/cpu-highs-incremental`](https://github.com/hipotures/squares/tree/exp/cpu-highs-incremental) `114c9949` | SEMANTICALLY EQUIVALENT, DIFFERENT TRAJECTORY | 17.568 | 7.786 | 9.782 | 55.7% | 7.266→6.520 | 10.249→1.250 | Parent peak 543,552–579,832 KiB at 16; base unmeasured | Moderate | `highspy` needed for production | **PROMISING BUT NEEDS MORE WORK** |
| Compiled top-13 selector | [`exp/cpu-top13-selector`](https://github.com/hipotures/squares/tree/exp/cpu-top13-selector) `4172e760` | TRAJECTORY IDENTICAL | 17.568 | 15.616 | 1.952 | 11.1% | 7.266→5.193 | 10.249→10.418 | Per-call allocation 9.94 MB→1.7 KB; full RSS unmeasured | Moderate–high | Native build/package | **PROMISING BUT NEEDS MORE WORK** |
| Slab interval selection | [`exp/cpu-maskless-selection`](https://github.com/hipotures/squares/tree/exp/cpu-maskless-selection) `6d077b05` | TRAJECTORY IDENTICAL | 17.568 | 15.457 | 2.111 | 12.0% | 7.266→5.255 | 10.249→10.199 | Per-call allocation 20.98→13.66 MB; full RSS unmeasured | Moderate | None | **READY TO CONSIDER FOR MERGE** |
| Fused row streaming | [`exp/cpu-fused-separation`](https://github.com/hipotures/squares/tree/exp/cpu-fused-separation) `7ef9fd75` | TRAJECTORY IDENTICAL | 17.568 | 14.881 | 2.687 | 15.3% | 7.266→4.646 | 10.249→10.211 | Late-grid peak worker RSS 92,396→76,504 KiB | High | None | **RESEARCH RESULT ONLY** |
| In-place cumsum | [`exp/cpu-cumsum-reuse`](https://github.com/hipotures/squares/tree/exp/cpu-cumsum-reuse) `10dcd18e` | TRAJECTORY IDENTICAL | 17.568 | 16.248 | 1.320 | 7.5% | 7.266→5.897 | 10.249→10.190 | Captured-grid extra allocation 15.37→7.68 MB with a conservative copy | Low | None | **READY TO CONSIDER FOR MERGE** |

The serial medians expose the tradeoffs hidden by the 16-process table: incremental LP 34.461 s (9.218 s saved), top-13 30.011 s (13.668 s saved), cumsum 43.389 s (0.290 s saved), maskless 43.524 s (0.155 s saved, smaller than its run spread), and fused 58.904 s (**15.225 s slower**). Production parallel's measured serial reference was 44.093 s; its 16-process time, 17.648 s, is within 0.080 s of the prior research harness's 17.568 s. The fused branch's serial regression blocks a merge recommendation despite its 16-process gain.

The four unchanged-trajectory separation branches and production parallel finish at 22 rounds, 5,643 rows, and the same objective and least coverage as the base. The LP branch takes a different valid optimum/basis sequence: 23 rounds, 5,842 rows, objective 12.217676366606236, least covered 0.9999999999998309. Its exact diagnostic checked all 5,842 retained rows; no centre was outside the exact domain, and every float boundary-row discrepancy had an exact nearby witness. Each experiment branch preserves complete per-round trajectories and commands in its own report and JSON results.

## Interaction map

- **Largely independent:** retained LP model versus direction-level separation; a production direction pool versus a faster per-direction selector; LP versus cumsum or reachability changes. They can plausibly compose but have no measured combined result.
- **Potentially composable with shared memory effects:** cumsum reuse and interval selection operate at different steps, but both reduce memory traffic. Their individual savings must be remeasured together, especially at 16 workers.
- **Overlapping:** top-13 and maskless both change candidate selection input and allocation. The heap's benefit on compacted reachable values is unmeasured.
- **Subsumed or effectively mutually exclusive as implemented:** fused streaming already performs in-place prefix accumulation, interval reachability, and small-k selection. It overlaps cumsum reuse and maskless selection, and its selection path overlaps the top-13 branch. Merging those implementations directly would destroy attribution.

**Independent speedups are not additive.** No combined branch or combined timing was made.

## Operator recommendation

1. Consider merging production parallel directions first. It makes the previously proven worker path available without changing the deterministic trajectory.
2. Rebase and retest interval selection and then in-place cumsum independently on the new main, or in the reverse order if implementation simplicity is preferred. Keep both only if their combined run remains favorable.
3. Decide whether a direct `highspy` runtime dependency and persistent model lifecycle are acceptable; if so, integrate and exact-check the LP prototype against the then-current branch. It is the largest measured residual gain.
4. Package the C top-13 selector as a portable native component before considering a merge. Retest it on the compacted or fused candidate path if either is selected.
5. Retain fused streaming as research. Its 16-worker memory and wall results are useful, but its serial regression requires a different implementation or an explicitly parallel-only route.

The matrix is a read-only comparison. It changes no production code, dependency, or main branch.
