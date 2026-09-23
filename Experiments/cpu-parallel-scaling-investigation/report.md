# CPU parallel scaling investigation — n=12 square packing

Date: 2026-09-23 UTC. Project: `packing`, project-pinned Python 3.14.7, NumPy 2.5.2. All Python commands used `uv run --frozen` from `/home/user/DEV/squares/packing`. GPU work was excluded. The prior `/tmp` capture and JSON files were copied into the persistent local research directory before new experiments; this repository copy stores the captured array bytes as lossless archives under [`workloads/`](workloads/) with restoration instructions in [README.md](README.md). The report distinguishes whole-program time from separation time and from isolated NumPy operations.

## 1. Executive conclusion

The high-concurrency separation shortfall has **two demonstrated causes**. Large NumPy working sets exceed effective cache capacity and compete for shared memory bandwidth: standalone workers reproduce ~1.9–2.0× aggregate CPU inflation at 16 workers, large memory-streaming backgrounds roughly double one pinned target's latency while register-only backgrounds cost ~7–10%, small arrays scale much better, and sharing input pages removes much of argpartition's 16-worker penalty. Separately, round 0 hits a specific NumPy SIMD argselection pivot pathology on the ordered zero/infinity array. A six-element value-preserving swap changes 171 ms to 7.3 ms; disabling optional NumPy sort dispatch changes it to about 2.5 ms. DDR bandwidth versus LLC capacity cannot be assigned a unique percentage inside this VM without physical counters; both are implicated. Serial LP remains the main whole-program Amdahl limit.

### Baseline and scope

For context, the known original serial solver is 71.19 s (59.41 s separation, 11.78 s LP), while the reproduced original 16-process solver is 21.34 s (9.36 s separation, 11.96 s LP). Perfect 16-way separation with unchanged LP would still take about 15.49 s, and perfect 2-way separation would give only about 1.72× whole-program speedup. Thus the CPU-efficiency claims below refer to separation or isolated operations, not to raw whole-program speedup.

## 2. Hypothesis matrix

| Hypothesis | Status | Strongest evidence | Confidence |
|---|---|---|---|
| H1. ProcessPool/parent/task feed | **REFUTED** | 16 independently launched pinned executables, no task queue or per-call IPC, still inflate aggregate CPU ~1.9–2.0×. | High |
| H2. All-core frequency/VM CPU capacity | **CONFIRMED** | Fixed register loop slows 0.819→0.874 s with 14 compute backgrounds (6.7%); NumPy targets slow ~6–10% under the same background. Far below the ~100% loss under large streaming backgrounds. | High for magnitude in this VM |
| H3. Shared bandwidth contention | **STRONGLY SUPPORTED** | 14 independent 64 MB-per-array streamers raise argpartition 6.80→13.60 ms/call and double cumsum 6.12→12.69 ms/call. Nominal streaming throughput plateaus near 50–54 GiB/s at 4–16 workers. Exact DDR traffic was not counter-measured. | High for shared memory-system pressure; medium for DDR specifically |
| H4. Shared cache/capacity contention | **CONFIRMED** | Small arrays scale far better; shared read-only mapping cuts 16-worker argpartition 10.43→7.68 ms. At the same 48–128 MB virtual/page footprint, dense cache-line pointer chasing costs ~80–115 ns/access versus ~25–32 ns when only one line/page is touched. Exact cache level remains unknown. | High for capacity effect; medium for exact cache level |
| H5. Allocation/page faults | **CONFIRMED** | Reusing `out=` buffers cuts double-cumsum minor faults from ~58k–70k per 60 calls/worker to ~1 and latency 6.50→4.31 ms serial, 12.24→7.74 ms at 16. Relative inflation remains ~1.8×; full solver barely improves. | High |
| H6. NumPy algorithm behavior | **CONFIRMED** | Default SIMD argselection ~171 ms; AVX-512 disabled ~33 ms; all optional sort dispatch disabled ~2.5 ms on identical data. Matching NumPy/x86-simd-sort source shows sampled pivots, repeated partition, and fallback. | High |
| H7. Input distribution/order | **CONFIRMED** | Actual and sorted zero/inf ~172 ms; histogram-preserving shuffle ~9 ms; three sample-position swaps (six array entries) ~7.3 ms; all-zero ~5 ms. The trigger is ordered minimum-value/inf placement at SIMD pivot sample positions, not ties or infinities alone. | High |
| H8. Decomposition/array layout | **POSSIBLE** | C/F layout moves cost between cumsum axes; double-cumsum changes only ~4%. Pinned/unpinned and four guest vCPU groups differ only a few percent. Sharing input pages helps a duplicated-input diagnostic, but real direction grids are distinct. No solver-level decomposition replacement was validated. | Medium |
| H9. Other: diagnostic library threads | **CONFIRMED** | Fresh tiny-array processes had 16 NumPy/library threads and process CPU ~0.76 s against main-thread/wall ~0.36 s. With `OPENBLAS_NUM_THREADS=1` there is one thread and CPU≈wall. Independent large-array slowdown persists after this control. | High |

“Confirmed” is used for controlled interventions and is qualified where the effect is secondary. The exact physical division of LLC traffic, DDR traffic, and VM host effects remains unresolved.

## 3. Independent-process result — no supervisor feed

[`scripts/independent.py`](scripts/independent.py) launches separate Python executables from the shell. Each loads a captured real round-18 direction-26 array, pins to a distinct guest vCPU, performs a warm call, writes a ready file, waits for an atomic start timestamp, executes its fixed share of **160 total calls**, and writes its own result. There is no ProcessPool, parent work queue, futures, array transfer, or per-operation IPC in the timed region. Results below are means of two trials with `OPENBLAS_NUM_THREADS=1`; [raw JSON](raw/independent.json).

| Workers | Argpartition wall s | Argpartition CPU sum s | Double cumsum wall s | Double cumsum CPU sum s |
|---:|---:|---:|---:|---:|
| 1 | 1.062 | 1.061 | 1.002 | 1.002 |
| 2 | 0.548 | 1.087 | 0.562 | 1.084 |
| 4 | 0.324 | 1.259 | 0.321 | 1.236 |
| 8 | 0.222 | 1.725 | 0.217 | 1.657 |
| 16 | 0.157 | 1.994 | 0.159 | 1.976 |

At 16, speedup is ~6.76× for argpartition and ~6.30× for double cumsum, with ~1.88× and ~1.97× aggregate CPU inflation. This causally refutes a central task feeder as the main explanation for the isolated operation slowdown. It does not imply the full solver has no serial parent work.

## 4. One pinned target core under background load

[`scripts/target_stress.py`](scripts/target_stress.py) pins the target to guest vCPU 0 and backgrounds to disjoint vCPUs 1…N; the N=14 row leaves vCPU 15 free. The target executes 160 real late-round argpartition calls, 80 double-cumsum calls, or 500 million fixed register-loop iterations. Backgrounds are independent sleeping processes, compiled register loops, compiled STREAM-like loops with two 64 MB arrays per process, independent argpartition loops, or independent double-cumsum loops. The target loads and warms its input before timing. The table is the controlled one-thread sweep; [raw JSON](raw/target_stress.json). A prior sweep with default library threads is retained as [replication](raw/target_stress_default_threads.json).

| Background | Count | Register target s | Argpartition ms/call | Double cumsum ms/call |
|---|---:|---:|---:|---:|
| None | 0 | 0.819 | 6.80 | 6.12 |
| Sleeping processes | 14 | 0.819 | 6.62 | 5.59 |
| Register compute | 4 | 0.822 | 6.88 | 6.42 |
| Register compute | 8 | 0.892 | 7.43 | 6.76 |
| Register compute | 14 | 0.874 | 7.20 | 6.74 |
| Large memory stream | 4 | 0.844 | 15.72 | 11.91 |
| Large memory stream | 8 | 0.910 | 9.50 | 6.56 |
| Large memory stream | 14 | 0.967 | 13.60 | 12.69 |
| Argpartition | 4 | 0.837 | 8.37 | 7.70 |
| Argpartition | 8 | 0.879 | 11.12 | 10.06 |
| Argpartition | 14 | 0.886 | 11.71 | 10.83 |
| Double cumsum | 4 | 0.844 | 7.63 | 8.55 |
| Double cumsum | 8 | 0.901 | 7.61 | 6.92 |
| Double cumsum | 14 | 0.918 | 8.01 | 8.61 |

Memory-stream count 8 is nonmonotone across the two sweeps; no physical topology claim is based on that row. The controlled contrast at 14 is robust: compute-only load moves argpartition ~6% and double cumsum ~10%, while large independent memory streams roughly double both. Merely creating sleeping processes has no penalty. [`scripts/affinity_stress.py`](scripts/affinity_stress.py) further varied streamer buffer size and vCPU placement; 0.25 MB buffers barely affect the target, 2–64 MB buffers do. Near/far guest groups did not show a stable separation.

## 5. All-core/turbo and bandwidth contribution

The fixed C loop uses xorshift/multiply state in registers and verifies a deterministic checksum. On target vCPU 0 it took 0.819 s alone and 0.874 s with 14 register-only workers: **6.7% longer elapsed time (~6.3% throughput loss)**. Under 14 large streamers it took 0.967 s: **18.1% longer elapsed time**. Neither accounts for the ~100% NumPy latency increases under those streamers. Reported guest MHz was not used.

The independent [`stream_bandwidth.py`](scripts/stream_bandwidth.py) control calculates **nominal cache-line traffic**, not hardware-measured DDR bytes, for buffers of different sizes. [Raw data](raw/stream_bandwidth.json):

| MB per array, two arrays/process | 1 worker | 2 | 4 | 8 | 16 | Interpretation |
|---:|---:|---:|---:|---:|---:|---|
| 0.25 | 207 | 423 | 823 | 1,639 | 3,132 | Mostly private-cache sized, scales near linearly |
| 2 | 187 | 382 | 748 | 760 | 1,696 | Cache hierarchy changes with concurrency |
| 8 | 158 | 160 | 108 | 101 | 155 | Shared hierarchy pressure |
| 64 | 40.6 | 51.1 | 53.9 | 53.0 | 49.1 | Large-buffer throughput ceiling by 4 workers |

Numbers are GiB/s of nominal read/read/write traffic. This controlled size trend supports a shared bandwidth/capacity ceiling. No guest-visible hardware counter can assign exact bytes to DDR versus LLC (`perf_event_paranoid=4`).

## 6. Working-set size and cache test

[`scripts/working_set.py`](scripts/working_set.py) samples the same real late-round distribution at controlled sizes, including infinity density, and generates corresponding float64 grids. The same operation and per-worker call count are used at 1/2/4/8/16 workers; table shows main-thread CPU per call. The NumPy-library thread pool is fixed at one. [Raw data](raw/working_set.json).

| Elements | Approximate input size | Argpartition 1→16 ms/call | Inflation | Double cumsum 1→16 ms/call | Inflation |
|---:|---:|---:|---:|---:|---:|
| 4,096 | 32 KiB | 0.036→0.042 | 1.17× | 0.030→0.031 | 1.03× |
| 32,761 | 256 KiB | 0.218→0.244 | 1.12× | 0.296→0.351 | 1.18× |
| 262,144 | 2 MiB | 1.636→1.744 | 1.07× | 4.473→4.928 | 1.10× |
| 958,441 | 7.3 MiB | 9.083→14.850 | 1.63× | 6.334→12.280 | 1.94× |
| 1,555,009 | 11.9 MiB | 9.334→24.001 | 2.57× | 9.708→26.010 | 2.68× |

A paired input-page control used identical real round-18 values and converted a read-only `np.memmap` to a plain `ndarray` view, preserving the NumPy algorithm path. At 1 worker, argpartition is 6.71 ms private versus 6.73 ms shared. At 16, it is **10.43 ms private versus 7.68 ms shared** (26% reduction). Double cumsum changes 12.38→11.52 ms at 16 (7%). See [`mmap_paired.json`](raw/mmap_paired.json). This demonstrates a causal input-footprint effect; mmap is a diagnostic because real direction arrays are distinct.

A separate dependent-read control kept the **same allocated bytes and same number of mapped pages** but changed how many cache lines it touched. [`cache_stride.py`](scripts/cache_stride.py) followed a randomized pointer cycle at 64-byte stride (every cache line) or 4,096-byte stride (one line per page), pinned to vCPU 0 or 8, twice each. Median latencies on either vCPU were approximately:

| Virtual allocation | Every line, 64 B stride | One line/page, 4,096 B stride |
|---:|---:|---:|
| 8 MB | 10–11 ns/access | 7–8 ns/access |
| 16 MB | 17–20 ns/access | 19–23 ns/access |
| 24 MB | 28–33 ns/access | 22–25 ns/access |
| 32 MB | ~48–50 ns/access (one 85 ns outlier) | 22–25 ns/access |
| 48 MB | 79–87 ns/access | 23–27 ns/access |
| 64 MB | 95–99 ns/access | 24–28 ns/access |
| 128 MB | 112–117 ns/access | 30–32 ns/access |

[Raw dense/sparse results](raw/cache_stride.json); [initial dense sweep](raw/cache_latency.json). Sparse accesses still visit the same pages and have the same potential TLB footprint, so page count alone cannot explain the dense working-set knee. The change tracks cache-line footprint and eventual memory misses. The knee is around a few tens of MB in this VM, but guest L3 size/CCD labels cannot identify a physical cache boundary reliably.

## 7. Round-0 argpartition diagnosis

The captured direction-26 flat array has 1,555,009 float64 entries: 1,013,715 finite entries, **all exactly zero**, and the rest positive infinity. Its ordered spatial regions put many zeros at the SIMD selector's pivot sample positions. On the same shape, serial medians were: actual 172.8 ms; random distinct finite 14.7 ms; random finite values at the same finite positions plus infinity 10.5 ms; all zeros 5.0 ms; four repeated finite values plus infinity 8.2 ms; shuffled original histogram 8.9 ms; sorted zero/inf 171.6 ms; reversed zero/inf 175.7 ms. [Distribution data](raw/distribution.json).

The decisive minimal intervention swaps three zero sample positions with three infinity positions, preserving **every value count** and changing only six entries. The SIMD pivot sample changes from zero to infinity and the seven-call median changes **171.9→7.3 ms**. [Script](scripts/pivot_swap.py), [raw result](raw/pivot_swap.json). Randomized-pivot samples are also retained in [`pivot_sample_test.json`](raw/pivot_sample_test.json).

Matching upstream NumPy 2.5.2 [`selection.cpp`](raw/numpy-selection-2.5.2.cpp) dispatches single-k float64 argselection to x86 SIMD; its [`x86_simd_argsort.dispatch.cpp`](raw/numpy-x86_simd_argsort-2.5.2.cpp) calls Intel x86-simd-sort `argselect`. The pinned submodule source [`xss-common-argsort.h`](raw/x86simdsort-xss-common-argsort-fa944e.h) samples a median pivot, partitions indices, recurses with a `2*log2(n)` progress limit, and falls back to `std::sort`. A zero pivot on this zero/inf input can leave the active range essentially unchanged, so repeated full-array gather/partition work dominates; changing only pivot samples causes the observed recovery. This mechanism is an inference from source plus the controlled swaps, not a direct internal counter trace. The generic introselect path alone does not explain the default timing.

A direct dispatch intervention confirms the software path: four calls on the **identical array** take 0.679 s default (~170 ms/call), 0.130 s when AVX-512 variants are disabled (~33 ms/call), and 0.010 s when `NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4,AVX512_ICL` selects the generic path (~2.5 ms/call). Tied candidate indices change, but all chosen values are zero. The generic path still has large-array concurrency inflation: round-0 ~2.43→10.80 ms/call and late-round ~2.32→6.40 ms/call at 1→16 workers ([raw](raw/dispatch_scaling_generic.json)); therefore algorithm repair alone does not remove the shared-memory limit.

## 8. Cumsum diagnosis: layout, allocation, reuse, concurrency

The production expression `np.cumsum(np.cumsum(grid, axis=1), axis=0)` materializes two ~7.7 MB output arrays for a real 980×980 late-round grid. The separately written two-call form has the same cost. In [`cumsum_buffers.py`](scripts/cumsum_buffers.py), 60 repeated real-grid calls per worker gave ([raw](raw/cumsum_buffers.json)):

| Form | 1-worker ms/call | 16-worker ms/call | Minor faults/worker over 60 calls | Peak RSS/worker | 16/1 inflation |
|---|---:|---:|---:|---:|---:|
| Nested cumsum | 6.50 | 12.24 | ~58k–70k | ~61 MB | 1.88× |
| Separate cumsums | 6.41 | 12.27 | ~55k–70k | ~61 MB | 1.91× |
| Two reused `out=` buffers | 4.31 | 7.74 | ~1 | ~62 MB | 1.80× |
| Reused `np.add.accumulate` buffers | 4.35 | 7.80 | ~1 | ~62 MB | 1.79× |
| Copy to one reused buffer, then in-place add.accumulate on axes 1 and 0 | 4.45 | 6.02 | ~1 | ~54 MB | 1.35× |

The in-place variant uses NumPy's documented safe overlapping `ufunc.accumulate` operation ([NumPy release notes](https://numpy.org/doc/1.15/release.html), [ufunc API](https://numpy.org/doc/stable/reference/generated/numpy.ufunc.accumulate.html)). Both passes matched the nested result **bit for bit** on captured round-0 and late grids. The research-only full solver retained the original 23 rounds, 5,481 rows, objective, and convergence with the in-place path. Its 16-process wall improved only 21.34→21.12 s; two-buffer reuse alone was 21.49 s. The per-operation gain does not dominate full solver time.

C layout: axis-1 2.10→3.04 ms and axis-0 2.25→3.64 ms at 1→16 workers. F layout: axis-1 2.17→3.66 ms and axis-0 2.11→2.87 ms. Double cumsum changes 12.30→11.76 ms at 16; two-buffer `out=` changes 7.73→7.80 ms. Layout shifts which pass is strided but does not restore scaling. [Layout data](raw/layout_compare.json). `tracemalloc` measured ~15.37 MB peak extra allocation for nested real-grid cumsum against <2 KB extra during reused-buffer calls, after the buffers had been allocated ([allocation data](raw/allocation_peaks.json)).

## 9. Software alternatives actually benchmarked

Selection timings are serial medians on real captured inputs; “candidate semantics” means thirteen lowest **values**, with tied indices permitted to differ. [Raw latency and candidate comparisons](raw/alternatives.json), [parallel scaling](raw/selection_scaling.json), [allocation peaks](raw/allocation_peaks.json).

| Method | Round-0 ms | Late ms | Peak extra bytes round 0 | Candidate semantics / result |
|---|---:|---:|---:|---|
| Current `np.argpartition` SIMD | 172.8 | 6.60 | 12.45 MB | Baseline tie choices; 16-worker round-0 ~323 ms/call. |
| Finite-index compaction then argpartition | 5.17 | 4.27 | 24.34 MB | Exact thirteen lowest values, different zero ties. Round-0 16-worker ~27.0 ms/call. Full solver validated below. Apply only to special case; late 16-worker 17.7 ms is worse than baseline 10.2 ms. |
| `np.partition` threshold then index recovery | 155.0 | 4.76 | 12.44 MB | Late-round thirteen values **not equivalent** under threshold ties; rejected. |
| First thirteen finite indices | 0.72 | 0.39 | 9.67 MB | Valid minimum values only on all-zero/inf round 0; invalid late-round. Not full-solver tested. |
| Shuffle indices, argpartition, map back | 32.9 | 14.0 | 38.20 MB | Exact thirteen lowest values, different ties; extra traffic makes late round worse. |
| `argpartition(kth=2)` for three only | 171.1 | 6.60 | Similar to baseline | Only three candidates; does not preserve the required 13-candidate survey. Rejected. |
| Generic NumPy argselection dispatch | ~2.5 | ~2.3 | ~12.45 MB index output | NumPy's exact selection contract with different tie choices; full solver validated below. 16-worker ~10.8 ms round 0, ~6.4 ms late. |

The finite-only research patch changed **only** all-zero/inf arrays larger than one million entries. It converged in 22 rounds and 5,782 rows with objective 12.217676366607032 versus baseline 12.217676366606284 (difference 7.5×10⁻¹³), all placements covering mass 1. The changed rows/rounds are legitimate consequences of choosing different equal-zero cells; every chosen value remains a minimum and the exact placement/cover check remains active. Its 16-process wall was 18.04 s, separation 7.66 s. [Full solver JSON](raw/full_solver_finite.json).

The global dispatch control is faster on this solver but can affect other NumPy operations, so it is an **experiment/workaround**, not a production recommendation without targeted regression work. It converged in 22 rounds and 5,517 rows with objective 12.217676366623763 (difference 1.75×10⁻¹¹ from baseline) and the same exact convergence condition. A serial generic-dispatch run followed the **same** 22-round, 5,517-row trajectory and objective: 31.67 s whole, 21.65 s separation, 10.01 s LP ([serial JSON](raw/full_solver_generic_serial.json)). Its 16-process result was 16.19 s whole and 6.16 s separation ([parallel JSON](raw/full_solver_generic.json)): 3.52× separation-only speedup for the same trajectory. Thus high-concurrency separation remains far from linear after removing the round-0 SIMD pathology.

## 10. Best CPU result discovered

The fastest observed **research-only** 16-process solver combined generic NumPy argselection dispatch with one reused scratch array and in-place `np.add.accumulate`:

| Measure | Original 16-process | Research variant | Change |
|---|---:|---:|---:|
| Whole solver wall | 21.341 s | **15.646 s** | 1.36× speedup |
| Separation | 9.361 s | **5.563 s** | 1.68× speedup |
| LP | 11.964 s | 10.062 s | Changed 22-round trajectory |
| Rounds / rows | 23 / 5,481 | 22 / 5,517 | Equal-mass tie choices differ |
| Objective | 12.217676366606284 | 12.217676366623763 | Difference 1.75×10⁻¹¹ |
| Stopping result | Every placement covers mass 1 | Same | No mathematical weakening found |

[Baseline JSON](raw/full_solver_baseline.json); [best-run JSON](raw/full_solver_generic_inplace.json). Both ran `OPENBLAS_NUM_THREADS=1`. In-place alone kept the exact baseline trajectory and objective. The incremental 0.54 s gain from in-place on top of generic dispatch is from one full-solver run per variant and should be treated as a measured observation, not a precise stable percentage. The large default→generic improvement was reproduced by isolated operation controls and the full solver.

## 11. Proven, refuted, unresolved

**PROVEN**

- Parent task feeding is not required for the isolated operation slowdown: independent processes show it.
- Large shared-memory pressure causes a large target-core penalty; compute-only and sleeping controls do not.
- Large working sets suffer much more than cache-sized ones. Sharing identical physical input pages recovers a substantial part of 16-worker argpartition latency. Holding page footprint fixed while reducing touched cache lines removes most of the dependent-read latency knee.
- Round-0 ordered zero/inf data triggers an optional NumPy SIMD argselection path; six value-preserving entry changes or disabling dispatch recover tens-fold operation speed. The round-0 bottleneck is algorithmic and data-order dependent.
- Cumsum output allocation causes many minor faults and real single-call cost; reuse removes faults but not the full concurrency penalty.
- A CPU-only workaround reproduces full-solver recovery and convergence, with tie-dependent trajectory and tiny numerical objective difference.

**REFUTED as dominant explanations**

- ProcessPool supervisor/task feeder for the isolated NumPy operations.
- A uniform all-core frequency/VM capacity drop of the observed magnitude.
- Merely creating 14 sleeping processes.
- Guest vCPU pinning or C/F layout as a large general remedy.
- Allocation/page faults as the sole source of high-concurrency slowdown.

**UNRESOLVED**

- The quantitative split between physical DDR bandwidth, LLC traffic/capacity, and VM host interference. Guest cache topology reports one 256 MB L3 group for an AMD 7950X3D/KVM VM and cannot be treated as physical CCD mapping. Hardware counters are blocked (`perf_event_paranoid=4`), and no kernel setting was changed.
- Whether a targeted production selector can retain the exact original 23-round/5,481-row trajectory while avoiding the NumPy SIMD pathology; mathematical minima and final convergence were preserved, but tied indices changed.
- Small full-solver timing differences among the cumsum buffer variants under host variability.

The single most useful next physical experiment is a **host-side or bare-metal repeat with memory-controller and LLC miss/traffic counters**, while running the same pinned target against cache-sized and DRAM-sized streamers. That would assign the currently combined shared-memory penalty to DDR versus LLC.

## 12. Recommendation and reproducibility

For CPU work, isolate the round-0 all-zero/inf selection as a targeted exact-minimum selector with an explicit tie policy and full trajectory/convergence regression checks; benchmark it under high concurrency. Separately, use a safe reusable cumsum scratch buffer if it improves a representative full solver on repeated runs. Preserve the distinction between mathematical validity and bit-identical tie trajectory. Use host counters before claiming a specific DDR or CCD remedy. Keep the global `NPY_DISABLE_CPU_FEATURES` setting as a diagnostic/workaround because it changes NumPy dispatch for other operations.

Representative commands, from `packing/` in the repository, after extracting the captured and synthetic workloads as described in [README.md](README.md):

```bash
OPENBLAS_NUM_THREADS=1 uv run --frozen python ../Experiments/cpu-parallel-scaling-investigation/scripts/independent.py
OPENBLAS_NUM_THREADS=1 uv run --frozen python ../Experiments/cpu-parallel-scaling-investigation/scripts/target_stress.py
OPENBLAS_NUM_THREADS=1 uv run --frozen python ../Experiments/cpu-parallel-scaling-investigation/scripts/working_set.py
OPENBLAS_NUM_THREADS=1 uv run --frozen python ../Experiments/cpu-parallel-scaling-investigation/scripts/distribution.py
OPENBLAS_NUM_THREADS=1 NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4,AVX512_ICL uv run --frozen python ../Experiments/cpu-parallel-scaling-investigation/scripts/dispatch_scaling.py
```

Compile the diagnostic C source from the repository root with `cc -O3 -std=c11 -o Experiments/cpu-parallel-scaling-investigation/scripts/stress Experiments/cpu-parallel-scaling-investigation/scripts/stress.c`; no project dependency change is needed. [`raw/environment.json`](raw/environment.json), [`lscpu.txt`](raw/lscpu.txt), [`lscpu-e.txt`](raw/lscpu-e.txt), [`lscpu-C.txt`](raw/lscpu-C.txt), [`numactl-hardware.txt`](raw/numactl-hardware.txt), and [`sys-cpu0-topology.txt`](raw/sys-cpu0-topology.txt) record the environment; `numactl` was unavailable. All important scripts, captures, source snapshots, and raw JSON reside in this repository experiment directory. No GPU benchmark ran.

**Investigation state:** Production source files were never modified and remain as found. `pyproject.toml` and `uv.lock` were left unchanged. The pre-existing unrelated local deletions shown by `git status` at the start of the investigation were not touched. This report was subsequently copied into the public fork as an experiment record.
