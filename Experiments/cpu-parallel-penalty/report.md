# Causal sources of the n=12 CPU parallel penalty

Research starting point: `897b722f2997fbf09b99b1700787a0052270de30`
on `main`; accepted production integration `011aa1b5` is an ancestor.
Phases A–C are complete. Test 8 and final synthesis remain pending.

## Phase A evidence so far

The table uses medians of three long complete-separation batches. All perf
events in this primary group ran at 100% enabled time. CPU, instructions,
cycles, and DRAM-origin fills are aggregate **worker** totals per replay;
wall is elapsed time per replay. Scheduler wait is aggregate guest runnable
wait from `/proc/<pid>/schedstat`.

| Workers | Wall (s) | Worker CPU (s) | Instructions (G) | Cycles (G) | IPC | Sched wait (s) | System CPU (s) | DRAM-origin fills (M) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10.655 | 10.650 | 94.99 | 58.83 | 1.615 | 0.009 | 0.550 | 20.48 |
| 2 | 6.223 | 12.232 | 98.96 | 66.30 | 1.493 | 0.006 | 0.835 | 108.49 |
| 4 | 3.799 | 14.530 | 98.30 | 77.03 | 1.276 | 0.006 | 0.740 | 312.11 |
| 8 | 2.837 | 21.054 | 99.49 | 106.98 | 0.930 | 0.006 | 1.516 | 478.13 |
| 16 | 1.819 | 23.500 | 99.32 | 114.79 | 0.865 | 0.513 | 2.090 | 342.15 |

Compared with one worker, the 16-worker execution uses 1.046× instructions,
1.951× cycles, 2.207× worker CPU, and 16.70× this DRAM-origin cache-fill
event. IPC falls to 0.536×. The guest schedstat wait increase is about
0.50 seconds aggregate, far smaller than the approximately 12.85 extra
worker CPU seconds; runnable wait is not counted as CPU execution. System CPU
does rise, so kernel/runtime work is a secondary contributor. The primary
classification from Test 1 is **MORE CYCLES FOR NEARLY THE SAME INSTRUCTIONS,
with mixed runtime effects**. A fill event is not a physical DDR byte or
bandwidth measurement.

Guest affinity covers vCPUs 0–15. Host snapshot identifies 16 physical cores
with SMT siblings 16–31; all 16 VM vCPU threads normally may run on host
CPUs 0–31. Guest and QEMU cgroups have `cpu.max = max 100000` and zero recorded
throttling. The host PMU device list lacks a working UMC/DF device, so
physical DDR saturation is currently unproven.

The Proxmox agent saved and verified every original `0-31` vCPU-thread
affinity, pinned vCPU `i` to physical host core `i` for the controlled window,
then restored and verified the original affinities. An independent eight-minute
auto-restore guard was active. The retained host script/logs contain timestamps,
all 16 TIDs, and affinity checks. Three adjacent 35-second replay batches in
each state gave:

| Host placement | VM separation wall/replay, median | Range | CV | Worker CPU/replay, median |
| --- | ---: | ---: | ---: | ---: |
| Unpinned before | 1.848 s | 1.826–1.894 | 1.53% | 24.033 s |
| Distinct physical cores | 1.764 s | 1.752–1.764 | 0.34% | 23.208 s |
| Restored unpinned | 1.873 s | 1.778–1.899 | 2.80% | 24.613 s |

The pinned median is 0.096 seconds (5.2%) below the midpoint of the two
unpinned medians. Its aggregate worker CPU is about 1.11 seconds lower.
This supports a **real but secondary** host placement contribution; it cannot
explain the approximately 12.85-second serial-to-16-worker CPU increase. The
restored control includes a fast first sample, so the exact percentage has
some VM-load uncertainty. The initially attempted pinned run was interrupted
before any complete timed sample when the operator clarified that `ready`
meant prepared, not active; it is documented and excluded.

Separate long event groups at 1 and 16 workers measured 15.9× growth in
`ls_dmnd_fills_from_sys.dram_io_near` and 20.2× in
`ls_hw_pf_dc_fills.dram_io_near`; both also ran at 100% enabled time. Generic
`cache-misses` grew only 1.22×, reflecting a different event definition.
The three DRAM-origin events agree on a large rise in system-origin fills;
none proves physical DDR saturation.

### Independent processes, no pool or timed result transfer

The control pins each process to a distinct guest vCPU, preloads the same
captured 23 × 181 direction/round workload, synchronizes one start, and gives
every process a fixed share. All 15 long samples have the same canonical
placement checksum
`db4b0ae1dc2f35de70c3094d90eff092c1a8bcf9fcbfe65f78606d2d1a57327c`.

| Processes | Wall (s) | Aggregate CPU (s) | CPU vs serial |
| ---: | ---: | ---: | ---: |
| 1 | 10.732 | 10.720 | 1.00× |
| 2 | 5.836 | 11.627 | 1.08× |
| 4 | 3.532 | 14.053 | 1.31× |
| 8 | 2.608 | 20.354 | 1.90× |
| 16 | 1.566 | 20.166 | 1.88× |

Thus most CPU inflation survives without ProcessPool, input/output transfer,
or a feeder during timing. At 16 processes perf measured 0.979× the serial
instructions, 1.641× cycles, and 15.88× DRAM-origin fills. The independent
16-process CPU time is about 3.33 seconds below the ProcessPool worker CPU
time, but this difference also includes pinned guest affinity and excludes
worker argument/result serialization. It is an upper bound on the pool's
attributable worker CPU overhead until an affinity-matched control is run.

Relative to the 12.85 extra worker CPU seconds in the ProcessPool replay,
approximately 9.45 seconds (74%) of the increase survives in independent
processes. Test 3 therefore **refutes ProcessPool/feeder activity as the
primary source**, while leaving a secondary runtime/serialization contribution
plausible. The independent perf control confirms the main Test 1 distinction:
0.979× instructions but 1.641× cycles at 16 versus one process.

See `test01-counters/processed/summary.json`,
`test03-independent/processed/summary.json`, and the raw JSON/CSV for all
sample distributions and load readings. No sample is discarded. The preliminary
independent one-process smoke sample and initial 16-worker control are retained
separately; the latter had a high first-sample wall and was followed by longer
adjacent controls instead of being silently dropped.

**Phase A checkpoint classification: MIXED, dominated by more cycles for
nearly the same instructions.** Concurrency increases DRAM-origin cache fills
and lowers IPC; host placement and runtime/kernel work contribute less.
Phase B below tests interference, working-set sensitivity, and translation
without treating the fill increase as proof of physical DDR saturation.

## Phase B: interference, active footprint, and translation

All screen cells have a timed region of at least 10.5 seconds. Every result
used quantitatively below has three independent 20-second samples. The
target and backgrounds are pinned to distinct visible guest vCPUs, input is
prepared and warmed before timing, and `perf` event running fractions are
at least 99.5%. Complete min/median/max/CV and raw counter receipts are in
the test directories. The table uses target CPU time per call; its ratio
to target wall time is close to one except for the heaviest streaming cases.

### Test 4: phase interference

The 90-cell screen covered five targets, six background types, and three
background counts. All 33 cells whose screen wall time increased at least
20% received three long repeats, as did the five idle controls. Four long
register-target controls and three different-input controls were also run.

| Target | Background, count | Idle median (ms/call) | Loaded median (ms/call) | Slowdown | Loaded CV | IPC idle → loaded |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Register | streaming, 14 | 1.605 | 1.852 | 1.15× | 1.5% | 1.44 → 1.42 |
| Prefix | streaming, 8 | 2.342 | 9.069 | 3.87× | 7.5% | 0.884 → 0.260 |
| Prefix | prefix, 8 | 2.342 | 4.450 | 1.90× | 7.9% | 0.884 → 0.514 |
| Slab | slab, 14 | 0.550 | 1.199 | 2.18× | 2.0% | 2.66 → 1.37 |
| Slab | prefix, 8 | 0.550 | 2.630 | 4.78× | 11.0% | 2.66 → 0.600 |
| Top-13 | streaming, 14 | 0.411 | 2.342 | 5.70× | 8.8% | 4.91 → 0.952 |
| Complete direction | prefix, 8 | 3.485 | 7.713 | 2.21× | 1.7% | 1.685 → 0.831 |

The compute-only register target increased only 13–17% under the four
14-worker memory backgrounds. That is an upper guide to generic all-core
frequency/throughput loss in this test, well below the 1.90–5.70× changes in
data-intensive targets. Target instructions per call remain close to their
idle values; the large differences are predominantly cycles/IPC and
system-origin cache fills. For example, prefix under eight streaming workers
rose from about 84 to 76,000 DRAM-origin fills per call. These are cache-fill
events, **not** measured physical DDR bytes or DDR saturation.

The first screen shared its read-only input pages through `fork` while each
worker had private output. With 14 *different real retained directions* in
the background, the prefix target took 5.51–5.82 ms/call (median 5.60), or
2.39× idle; the shared-input prefix control had median 2.89 ms (1.23× idle).
Thus shared input can hide interference. Different-input top-13 had median
0.480 ms (1.17× idle), about the same as the register control, while
different-input slab was variable (0.856–1.669 ms); no precise slab
different-input effect is claimed. Extremely loaded streaming/slab cases
also showed high CV or bimodal samples, so they establish susceptibility,
not a precise whole-solver contribution.

### Test 5: footprint and full-grid controls

The current prefix and native top-13 kernels were screened at nine active
sizes from 256 KiB to 32 MiB with 1, 4, 8, and 16 pinned workers. The
screen uses representative real values, with tiling/repetition of input
values only when a requested array exceeds the captured one. The following
working-set knees were repeated for three 20-second samples per endpoint:

| Kernel | Active bytes per worker | 1-worker CPU (ms/call) | 16-worker CPU (ms/call) | 16/1 inflation |
| --- | ---: | ---: | ---: | ---: |
| Prefix | 2 MiB | 0.633 | 0.743 | 1.17× |
| Prefix | 8 MiB | 2.568 | 5.801 | 2.26× |
| Prefix | 16 MiB | 6.700 | 25.96 | 3.88× |
| Top-13 | 4 MiB | 0.299 | 0.343 | 1.15× |
| Top-13 | 16 MiB | 1.181 | 2.870 | 2.43× |
| Top-13 | 32 MiB | 2.374 | 8.019 | 3.38× |

The full size screen shows the transition rather than a single threshold:
prefix inflation is 1.32× at 4 MiB, 2.25× at 8 MiB, and 4.42× at 32 MiB;
top-13 inflation is 1.23× at 8 MiB, 1.48× at 12 MiB, and 3.33× at 32 MiB.
Physical host topology reports two L3 domains totaling 128 MiB. The size
dependence is direct causal evidence for active working-set/shared-resource
pressure. It does not by itself distinguish last-level cache capacity from
physical memory throughput, and the two domains need not have equal size.

A research-only row-strip version of the *same full real grid* passed 3,620
bitwise comparisons over 905 captured grids and about 3.0 billion cells.
Its three long samples gave:

| Full-grid prefix | 1-worker CPU (ms/call) | 16-worker CPU (ms/call) | 16-worker change |
| --- | ---: | ---: | ---: |
| Current two-pass order | 2.309 | 4.701 | Control |
| 64-row strips | 2.345 | 4.153 | 0.548 ms/call faster (11.7%) |
| 32-row strips | 2.378 | 4.224 | 0.477 ms/call faster (10.1%) |

The 64-row variant is 1.6% slower serially. Its 16-worker kernel benefit
suggests a smaller active footprint helps, but no complete separation/solver
speedup is claimed at this checkpoint. Physical row-stride padding of 4, 32,
64, or 256 columns passed bitwise full-grid checks and gave no improvement in
the long screen: at 16 workers the baseline was 4.52 ms/call and every
padded variant was 4.80–5.78 ms/call. Padding is therefore not supported as
a next target; those negative comparisons are screens, not three-sample
effect estimates.

### Test 6: address translation

The normal-page control and `MADV_HUGEPAGE` variant used the same prefaulted
real full-grid copy and current prefix, with 2 MiB-aligned anonymous buffers.
Each worker's `smaps` showed 0 KiB `AnonHugePages` in the normal case and
at least 32 MiB in the huge-page case before timing. Full-grid SHA-256 and
output values matched; all event groups ran at 100% enabled time. Three
adjacent 20-second pairs at each worker count gave:

| Workers | Normal CPU (ms/call) | Huge-page CPU (ms/call) | Huge/normal | L1 DTLB misses that miss L2, normal → huge per call |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 2.355 | 2.310 | 0.981× | 5,657 → 1,220 |
| 16 | 4.640 | 4.816 | 1.038× | 4,731 → 1,832 |

The huge-page path lowers this DTLB event 78% serial and 61% at 16 workers,
and lowers DRAM-origin fills per call at 16 workers about 13%. It provides
**no 16-worker CPU-time saving** in any of the three paired samples. Cycles
per worker call fall about 2.8% while elapsed CPU time rises about 3.8%,
which may reflect host/guest frequency, placement, or other changed memory
behavior; these counters cannot isolate that. Minor faults during timing are
near 0.02/call in both 16-worker modes, so page allocation is not the
measured scaling mechanism in this prefaulted control. Address translation
has measurable event cost, but this experiment refutes huge pages as a
straightforward wall-time solution to the 16-worker penalty.

### Phase B causal ranking

| Mechanism | Interim evidence | Classification |
| --- | --- | --- |
| General all-core compute/frequency | Register target slows 13–17%, far less than memory targets | **WEAKLY SUPPORTED** as secondary |
| Shared cache / active working set | 1.17× → 3.88× prefix inflation as active data grows; bitwise row strips improve 16-worker kernel 11.7%; different input worsens prefix | **STRONGLY SUPPORTED** |
| Shared memory subsystem | Streaming backgrounds strongly raise cycles and DRAM-origin fills; complete direction 2.21× under prefix peers | **STRONGLY SUPPORTED**, precise DDR contribution unresolved |
| TLB/address translation | Verified huge pages reduce DTLB misses 61% at 16 workers but do not improve CPU time | **WEAKLY SUPPORTED** as a small/overlapping cost |
| Row layout/padding | No padded full-grid variant improved the long screen | **REFUTED** as an obvious gain for tested strides |
| Allocation/page churn | Prefaulted normal and huge buffers have similar small timed minor faults | **WEAKLY SUPPORTED** at most for this control; whole replay unresolved |

The shared-cache and memory-subsystem rows overlap; they are not additive
parts of the 12.85-second worker-CPU increase. Phase C below quantifies
scheduling tails before final attribution.

## Phase C: complete task timeline and scheduling controls

Test 7 replayed all 23 accepted rounds and 181 directions per round with the
production four-direction chunk shape. Its explicit-future control recorded
all 46 chunks each round: parent ready/submission, worker start/finish and
CPU, grid dimensions, future-ready callback, parent receive, and consume end.
The worker wraps `event_grid` only to observe grid dimensions and calls the
production function unchanged. All tested modes returned exactly 5,842
rows and the accepted direction, centre, and matrix SHA-256 hashes; the
balanced mode restores original direction order before row insertion.

Every final sample repeated whole 23-round replays for 19.88–22.61 seconds;
three independent samples were taken per endpoint. The first full replay in
each sample retains every chunk timestamp as compressed JSON. An adjacent
unmodified `pool.map` control quantifies the instrumentation difference:

| Mode | Wall/replay median (s) | Min–max (s) | CV | Worker CPU/replay (s) |
| --- | ---: | ---: | ---: | ---: |
| Production `pool.map` | 1.850 | 1.796–1.857 | 1.5% | 24.212 |
| Explicit futures, production order | 1.931 | 1.852–1.988 | 2.9% | 24.991 |
| Expensive chunks submitted first | 1.959 | 1.860–2.033 | 3.6% | 25.568 |

The explicit-future timeline costs about 0.081 s/replay (4.4%) versus the
production replay at the medians. Absolute timeline phase percentages are
therefore descriptive; scheduling candidates are compared to the similarly
instrumented control. Previous-round cell count predicted actual chunk
duration only moderately (median within-round correlation about 0.35).

Across the three 23-round control traces, workers were busy for 82.3–84.1%
of the aggregate first-start-to-last-finish span (median 83.5%). The summed
window from the point when half the workers had completed their last chunk
to the last worker finish was 0.167–0.221 s per replay (median 0.167 s),
roughly 8–11% of the traced wall. Round zero is the single largest round in
the representative trace (0.346 s, versus 1.999 s summed over 23 rounds);
its longest chunk ran 0.190 s. The full per-round active-worker histograms,
slowest chunks, tail windows, and parent time are in
`test07-timeline/processed/summary.json`.

For the same representative traces, parent `Future.result()` waits summed
to 1.75 s/replay, while row reconstruction took about 0.21 s. The median
future-ready-to-consume delay per chunk was 2.5 ms and its 95th percentile
was 31 ms. About 1.29 s of wait intervals overlapped with at least one
later chunk already ready. This is an **ordered-wait observation, not 1.29 s
of removable wall**: the unfinished earlier chunk still must complete, and
later row processing cannot be committed out of original order without
preserving the deduplication contract. These intervals overlap worker
computation, the tail window, and each other as causal explanations.

Two research-only scheduling variants were tested on three adjacent long
pairs each:

| Variant | Method | Paired savings vs ordered control (s/replay) | Median saving | Result |
| --- | --- | --- | ---: | --- |
| Cost-first | Same consecutive groups; submit larger prior-round grids first | −0.181, −0.028, +0.127 | −0.028 | No reproducible gain; ready-to-consume delay rose |
| Balanced | Pack directions by prior-round grid size into four-item groups; consume directions in original order | +0.053, −0.048, −0.032 | −0.032 | No reproducible gain |

In the balanced comparison, the observed tail-after-half window fell from
0.213 to 0.178 s median and worker-span utilization rose from 82.3% to
84.2%, yet total wall did not improve (ordered 1.822 s, balanced 1.852 s
medians). This directly shows why the tail window is only an upper bound on
a scheduling win. At this checkpoint **no positive wall saving from the
tested schedulers is established**. A perfect scheduler that removed the
entire 0.17–0.22 s tail window could at most affect about 9–12% of the
traced separation wall, and some of that window contains necessary final
computation. The measured recoverable share is approximately zero within
the 0.03–0.18 s pair-to-pair VM variation. Do not add the ordered-wait and
tail figures.
