# Round-zero candidate selector for n=12 row generation

This branch changes only the candidate-index survey in
`sqpack.fractional.generate.placement_cells`. It does not change cumsum,
ProcessPool scheduling, LP construction, or certificate verification. All
measurements below use project-pinned Python 3.14.7 and NumPy 2.5.2 on the
16-vCPU KVM guest described in
[`Experiments/cpu-parallel-scaling-investigation/README.md`](../../../Experiments/cpu-parallel-scaling-investigation/README.md).

## Semantic contract

For each direction, `event_grid` gives a mass to every event cell and marks
cells whose open interior meets the admissible centre domain. The selector
scores unreachable cells as positive infinity. It surveys the lowest
`min(4 * keep + 1, grid_size)` **finite** scores, ascending by mass. A tied
cutoff may be resolved by any deterministic rule: the LP is constrained by
placement coverage, not by a cell's ordinal index. The selector must not skip
a strictly lower score to select a higher one. It must preserve the survey
count, so that cells which re-score at a neighbouring placement after float
rounding do not exhaust the `keep` slots. `placement_cells` then constructs an
admissible centre inside each surveyed cell, recomputes its actual coverage
mask and mass. It stops surveying once `keep` cells re-score within `1e-9` of
their grid mass, then returns at most `keep` rows sorted by their re-scored
mass. A mismatched cell may still contribute a valid row.

The survey's `4 * keep + 1` over-selection is a float-search heuristic, not an
exhaustive proof that no violated placement exists. A converged row-generation
run is a candidate LP point. Only the independent exact all-cell sweep in
`fractional.certificate.verify` can decide a proposed certificate. Row order
and equal-mass tie choice affect which valid rows are added, LP bases, and the
number of rounds; they are not certificate semantics. `Rows.add` deduplicates
by the complete coefficient vector, and `solve_rows` adds only violating rows
before re-solving the LP. A different choice among equal minimum cells can
therefore change the trajectory while preserving the search contract.

## Selector and tie rule

The old call enters NumPy's optional SIMD argselection on a real round-zero
array of 1,555,009 `float64` scores: 1,013,715 zeros and the rest positive
infinity. That ordered layout triggers a sampled-pivot pathology. The
preserved [CPU investigation](../../../Experiments/cpu-parallel-scaling-investigation/report.md)
isolated the input-order and dispatch dependence; it did not justify globally
disabling NumPy CPU features.

The new helper has two paths:

1. When all site weights are zero, the difference array and prefix sums must
   be exactly zero, so reachable scores are zero and unreachable scores are
   positive infinity. The helper checks that precondition and chooses evenly
   spaced zero-score flat indices in ascending order. With `m` zeros and `k`
   surveyed cells, their zero-index ranks are
   `floor(j * (m - 1) / (k - 1))` for `j = 0..k-1` (`k = 1` takes rank 0).
   Equal minima are spread over the placement domain. In a controlled
   first-round probe, taking the
   first 13 zero indices yielded 202 distinct rows across 181 directions;
   even spacing yielded 483. Both select only minimum-mass cells.
2. In all other rounds, NumPy partitions for the cutoff. The helper includes
   every score strictly below that cutoff and chooses the lowest flat indices
   among ties at the cutoff. The returned order is `(mass, flat_index)`. NaNs
   and infinities are ineligible. A rare negative-infinity diagnostic input
   takes a full finite sort to retain this contract.

This policy is deterministic for a fixed input. It does not rely on NumPy's
undocumented equal-key ordering or random shuffling. The captured zero/+inf
and late-round score bytes used by tests are in `tests/fixtures/`; their full
original workloads and hashes are retained in the CPU investigation.

The round-zero test fixture is a lossless `np.savez_compressed` copy of
`actual_flat.npy` (source SHA-256
`13d7cd57b509df97ed3c4d7db19d75c1fb8999a41da2fd20acae6f54985397d8`).
The late fixture copies captured `r18_d090_flat.npy` (source SHA-256
`3136eaa1ef5e34c21ead85ca14c6feb36702d14eef808adf41b118ba6b1b046d`).
Both source hashes match the preservation manifest. The compact fixtures are
committed so the property and regression tests do not depend on `/tmp`.

## Reproduce

From `packing/`, with no other CPU stress test running:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
uv run --frozen pytest tests/test_fractional_selector.py tests/test_fractional_generate.py
uv run --frozen python benchmarks/round0_selector/selector_benchmark.py \
  --repeats 20 --out benchmarks/round0_selector/results/selector_ops.json
uv run --frozen python benchmarks/round0_selector/solver_benchmark.py \
  --workers 1 --out benchmarks/round0_selector/results/serial_new.json
uv run --frozen python benchmarks/round0_selector/solver_benchmark.py \
  --workers 16 --out benchmarks/round0_selector/results/parallel_new.json
uv run --frozen python benchmarks/round0_selector/solver_benchmark.py \
  --workers 16 --selector baseline \
  --out benchmarks/round0_selector/results/parallel_old.json
uv run --frozen python benchmarks/round0_selector/exact_row_check.py \
  --out benchmarks/round0_selector/results/rows_exact.json
uv run --frozen python benchmarks/round0_selector/exact_row_check.py \
  --selector baseline --out benchmarks/round0_selector/results/rows_old_exact.json
```

`solver_benchmark.py` uses the original serial solver for one worker. In
16-process mode it parallelises the direction loop at runtime, using the same
ProcessPool mapping as the preserved CPU investigation. Its `baseline` option
restores the exact pre-change NumPy selection *inside every worker* for a
same-harness control, without editing production code. `row_run.timings`
records every round's rows added, violations, objective, separation and LP
time; `round_timings_exact` retains unrounded values. The JSON files under
`results/` are raw measurements, not profiler output.

## Measured result

The retained selector-input benchmark measured medians of **171.26 ms old
versus 1.10 ms new** for the pathological round-zero input (20 repetitions).
On a real round-18 input, the selector was **6.44 ms old versus 6.29 ms new**.
The 16-process same-harness baseline control reproduced the preserved
23-round, 5,481-row trajectory, objective `12.217676366606284`, and about
21.4 s wall / 9.4 s separation. The new selector converged in 22 rounds and
5,643 rows, objective `12.21767636660579`, least covered float mass
`0.9999999999995074`, with the same stop condition. The difference begins
with alternate equal-zero seed placements; every selected score in that round
is the global minimum zero. The exact n=12 retained-certificate gate cannot
be applied to this benchmark LP point as an n=12 certificate: its total mass
is **above 12** even before rationalisation. The relevant positive search-to-
proof control is the smaller `generate_adaptive(..., decide=True)` test, which
generates a candidate and submits it to the exact verifier.

**Trajectory classification: SEMANTICALLY EQUIVALENT BUT DIFFERENT
TRAJECTORY.** The old and new searches select minimum-score reachable cells
and use the same placement reconstruction, row deduplication, LP, convergence
check, and exact proof gate. The 22/23-round and 5,643/5,481-row difference
starts with deliberate alternative choices among equal-zero minimum cells.
Both runs reach the solver's float convergence condition; their LP
objectives differ by about `4.94e-13`. The old NumPy tie order is an
implementation detail, so reproducing its rows is not a correctness
requirement. Neither float convergence result alone certifies `s(12)`.

The current branch's three serial and three 16-process timings, along with
the baseline controls and their round trajectories, are in `results/`.
Medians of three full runs per configuration, with the same harness and
`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`:

| Solver | Wall | Separation | LP | Round-0 separation | Rounds | Rows |
|---|---:|---:|---:|---:|---:|---:|
| Serial, old | 71.639 s | 59.914 s | 11.803 s | 33.746 s | 23 | 5,481 |
| Serial, new | 44.268 s | 34.229 s | 10.055 s | 3.039 s | 22 | 5,643 |
| 16 process, old | 21.306 s | 9.363 s | 11.927 s | 4.914 s | 23 | 5,481 |
| 16 process, new | 17.550 s | 7.258 s | 10.280 s | 0.958 s | 22 | 5,643 |

The serial wall improvement is **1.62×** and the 16-process wall improvement
is **1.21×**. Separation improves **1.75×** and **1.29×**, respectively.
The round-zero separation improvement is **11.1×** serial and **5.13×** at
16 processes. Lower LP time in the new runs is a consequence of the changed
row trajectory; the selector does not alter LP code. The full per-round
`rows_added`, `violated`, `objective`, and `support` sequences are in
[`results/trajectory_compare.csv`](results/trajectory_compare.csv) and the
unrounded per-run JSON records.

`tie_policy_probe.py` and `results/tie_*.json` record first-round comparisons
of first-index, evenly spaced, and fixed-hash equal-zero surveys.
`results/serial_first_index_prototype.json` shows why simply taking the first
tied indices was rejected: it converged, but took 28 rounds and retained
6,124 rows. `serial_spread_*.json` and `parallel_spread_1.json` record the
intermediate implementation before removing one unnecessary later-round
array scan; they are not included in the final medians.

## Validation gates

The focused selector, fractional generator, certificate, and column-generation
test files passed together: **93 tests** (`results/relevant_pytest.stdout`).
That set includes the new candidate selector properties, a generated small
certificate accepted by the package exact verifier, the retained full n=12
certificate tests, and a two-direction independent-reviewer check. The
standalone retained n=12 gate accepted both its `19/5` and `99/25` rungs
(`results/retained_gate.stdout`). The independent reviewer's distinct full-net
route accepted the retained `77/20` rung with least exact cell mass 1
(`results/independent_replay.stdout`). These retained certificates are not the
output of this benchmark run; they check the downstream decision routes.

For the new full solver run, `exact_row_check.py` re-decided the container
domain and every site-cover coefficient using `Fraction` arithmetic. All
5,643 stored centres are exactly inside the domain. At 79 event boundaries,
the exact coverage at the stored binary-float centre differs from the float
row by one coefficient. Every one of those 79 vectors has an exact rational
placement witness after shifting one rotated centre coordinate by just
`10^-15`; the script verifies the **entire** coefficient vector at that
witness and reports zero rows without witnesses. Thus every retained new row
is a valid placement constraint, though a stored float centre is not always
itself its exact witness. The witness fractions and row IDs are retained in
`results/exact_row_check.json`.

The same exact-row check on the old selector found 82 such stored-centre
boundary differences among 5,481 rows, and exact nearby witnesses for all
82, with no centre outside the exact domain
(`results/exact_row_check_baseline.json`). The representation detail therefore
predates this selector change; neither run has a retained row lacking a real
placement witness.
