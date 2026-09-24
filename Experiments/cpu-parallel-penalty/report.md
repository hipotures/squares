# Causal sources of the n=12 CPU parallel penalty

Research starting point: `897b722f2997fbf09b99b1700787a0052270de30`
on `main`; accepted production integration `011aa1b5` is an ancestor.
All four phases and eight tests are complete, including the physical PVE
control received after the original host-access-blocked checkpoint.

## Phase A: instructions, host placement, and independent processes

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

## Phase D: identical native workload on VM and physical PVE

The standalone package replays all 181 captured real round-18 directions. It performs production-order scatter, both in-place prefix passes, slab compaction, and stable finite top-13 selection. Every process verifies the full difference grid, mass grid, and selected indices/masses before timing. The source/data SHA-256 and `-O3 -std=c11 -fno-fast-math -march=x86-64-v3 -mtune=generic` flags match across VM and host. Their GCC versions differ (VM 15.2, PVE 14.2), but executed instructions per replay agree within 0.14% at all five worker counts. Both binaries were identical between their original and retest runs on the same machine. All 15 accepted host samples and 15 accepted VM samples have the fixed plan checksum, 100% enabled perf events, and batch durations of 15.27–57.05 s on PVE and 23.79–56.42 s in the VM.

The original PVE plan succeeded for workers 1/2/4. Its first 8-worker sample lasted **7.902868434 s**, below the required 10 s. That failed receipt (`host-results/console.log`, `failure-summary.txt`, and `perf-sample1-w8.csv`) is retained and excluded from performance conclusions. The revised fixed plan uses 350 complete 181-direction replays at 8 workers and 620 at 16 on **both** machines. Three valid samples per endpoint were collected. The exact plans, raw JSON/perf, package archive, source, and processed distributions are in `test08-host-vm/`; the combined machine-readable result is `processed/summary-complete.json`.

| Workers | VM batch median, range (s) | PVE batch median, range (s) | VM wall/replay (s) | PVE wall/replay (s) | VM CPU/replay (s) | PVE CPU/replay (s) | VM CPU inflation | PVE CPU inflation |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 25.53, 25.49–26.54 | 34.52, 34.51–34.53 | 0.1949 | 0.2635 | 0.1948 | 0.2635 | 1.00× | 1.00× |
| 2 | 24.66, 24.63–24.93 | 27.58, 27.58–27.59 | 0.1180 | 0.1320 | 0.2346 | 0.2634 | 1.20× | 1.00× |
| 4 | 24.45, 24.33–24.59 | 15.62, 15.60–15.63 | 0.1054 | 0.0673 | 0.4181 | 0.2691 | 2.15× | 1.02× |
| 8 | 51.52, 50.50–52.00 | 15.28, 15.27–15.30 | 0.1472 | 0.0437 | 1.1409 | 0.3358 | 5.86× | 1.27× |
| 16 | 53.07, 50.08–56.42 | 56.93, 56.66–57.05 | 0.0856 | 0.0918 | 0.9216 | 0.9974 | 4.73× | 3.79× |

The VM wall CV across the three samples is 1.88%, 0.53%, 0.44%, 1.22%, and 4.86% for 1/2/4/8/16 workers; PVE CV is 0.02%, 0.01%, 0.07%, 0.07%, and 0.29%. No sample is discarded. VM 16-worker variation makes the small 7% PVE-versus-VM median difference unsuitable for a precise causal claim; the large 8-worker difference remains far outside its sample spread.

| Workers | VM speedup / efficiency | PVE speedup / efficiency | VM instructions (G) | PVE instructions (G) | VM cycles (G) | PVE cycles (G) | VM IPC | PVE IPC | VM / PVE DRAM-origin fills (M) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1.00× / 100% | 1.00× / 100% | 2.656 | 2.658 | 1.074 | 1.311 | 2.474 | 2.028 | 0.021 / 0.001 |
| 2 | 1.65× / 82.6% | 2.00× / 99.8% | 2.656 | 2.657 | 1.262 | 1.297 | 2.104 | 2.048 | 2.920 / 0.001 |
| 4 | 1.85× / 46.2% | 3.91× / 97.8% | 2.657 | 2.657 | 2.254 | 1.283 | 1.179 | 2.072 | 15.903 / 0.108 |
| 8 | 1.32× / 16.6% | 6.04× / 75.4% | 2.661 | 2.657 | 5.998 | 1.597 | 0.444 | 1.664 | 32.031 / 4.806 |
| 16 | 2.28× / 14.2% | 2.87× / 17.9% | 2.660 | 2.663 | 4.620 | 5.161 | 0.576 | 0.516 | 19.613 / 17.740 |

**Physical-host reproduction:** at 16 workers the physical host needs 3.79× its serial aggregate CPU for essentially the same 2.66 billion instructions, with 3.94× the serial cycles. The VM is 4.73× its own serial CPU, but its 16-worker *absolute* wall, CPU, cycles, and DRAM-origin fills are similar to PVE. Thus a large 16-worker penalty exists without virtualization. The host/VM inflation-ratio difference is partly driven by the PVE serial baseline being 35% slower than the VM serial baseline; it must not be treated as a measured virtualization tax.

**Placement qualification:** host workers are pinned to physical CPUs 0–15. CPUs 0–7 share one recorded L3 domain; CPUs 8–15 are in the other. The 8-worker host endpoint therefore uses only the first domain, while the 16-worker endpoint spans both. Guest workers are pinned to guest vCPUs, but the QEMU vCPU threads were initially free to migrate among physical host CPUs. At 8 workers the initial VM run consumed 3.40× the PVE worker CPU and had 6.66× the PVE DRAM-origin fills per replay. This discrepancy motivated the placement-matched causal control below.

The host and guest expose the same AVX2-capable x86-64-v3 ISA target. Neither environment exposes a working AMD UMC/DF PMU device, so controller bandwidth and physical DDR saturation remain unproven. These native results are for one late round repeated, not the full 23-round production separation, and are used to identify mechanism rather than to substitute native wall for solver wall.

## Placement-matched causal control and full-solver transfer

The PVE agent repeated the earlier safe affinity protocol: it saved the exact original `0-31` affinity and thread identity of each of VM 207's 16 vCPU threads, pinned thread `i` to physical CPU `i`, verified all 16 mappings, installed an independent 8-minute auto-restore guard, then restored and verified every original affinity. The VM native replay ran entirely between the `PINNED` and `RESTORED` timestamps. The host affinity log and guest run receipts are under `test08-host-vm/native-placement-control/`; the processed audit is `native-placement-control/processed/summary.json`. Source/data/binary, x86-64-v3 flags, 350/620 repeat counts, and top-13 checksums are unchanged. All native samples lasted 14.96–57.10 seconds and perf events ran at 100% enabled time.

| Native late-round replay | VM unpinned | VM physically pinned | Physical PVE |
| --- | ---: | ---: | ---: |
| 8-worker wall/replay | 0.14720 s | **0.04284 s** | 0.04366 s |
| 8-worker worker CPU/replay | 1.14087 s | **0.33609 s** | 0.33580 s |
| 8-worker cycles/replay | 5.998 G | **1.576 G** | 1.597 G |
| 8-worker instructions/replay | 2.661 G | 2.656 G | 2.657 G |
| 8-worker DRAM-origin fills/replay | 32.03 M | 6.12 M | 4.81 M |
| 16-worker wall/replay | 0.08560 s | 0.09205 s | 0.09182 s |
| 16-worker worker CPU/replay | 0.92160 s | 0.99651 s | 0.99745 s |

The 8-worker VM native replay becomes **3.44× faster in wall** and uses **70.5% less worker CPU** when vCPUs 0–7 are placed on the same physical cores/L3 domain used by the host control. It then matches the physical host within about 2% in wall and 0.1% in worker CPU. Instructions remain essentially unchanged; cycles fall about 74%. This is direct causal evidence that physical vCPU placement, rather than intrinsic virtualization overhead, accounts for most of the initial 8-worker VM gap on this repeated late-round workload. At 16 workers, the physically pinned VM and physical host also match closely; the unpinned VM happens to be about 7% faster in this control. Placement is workload and worker-count dependent.

To test practical transfer, the production n=12 solver was measured in three independent batches per condition. Every batch lasted 18.81–21.11 seconds and every one of **66 complete solves** reached 23 rounds, 5,842 rows, objective `12.217676366606236`, and the accepted stop reason. All 66 had the same 23-round decision trajectory (SHA-256 `7b845729210d31c6b12f5510b8ec78d609307130cd6ef1df61f6e0ac1ff1a0a9`). The pin control restricted the whole VM solver process tree to guest vCPUs 0–7 while PVE mapped those vCPUs to physical CPUs 0–7. A guest-only `taskset -c 0-7` control after physical affinity restoration isolates the need for host placement. The same production source was used throughout.

| Full solver | Batch median (s) | Wall/solve median (s) | CV | Separation/solve (s) | LP/solve (s) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8 workers, default placement | 20.38 | 4.076 | 0.57% | 2.909 | 1.142 |
| 8 workers, guest affinity only | 21.10 | 4.220 | 0.34% | 3.038 | 1.145 |
| 8 workers, PVE + guest pinned to cores 0–7 | 20.26 | **3.376** | 0.28% | 2.155 | 1.193 |
| 16 workers, default placement | 19.18 | **3.197** | 1.55% | 1.925 | 1.220 |

Physical placement saves **0.700 s/solve (17.2%)** against default 8 workers and **0.845 s/solve (20.0%)** against guest affinity alone. The saving is in separation; LP is similar. Restricting only the guest process without physical PVE placement is slower than default, so a VM-side `taskset` command is not the solution. The physically placed 8-worker solver is still **0.179 s/solve (5.6%) slower** than the current 16-worker default. The late-round 3.44× gain therefore does not transfer proportionally to the heterogeneous 23-round solver. This control proves a real placement mechanism but does not justify changing the fastest current production worker configuration.

## Final synthesis: why 16 workers consume 2.2× CPU

The accepted production computation is unchanged. Test 1 compares the same 23-round, 4,163-direction separation replay at each worker count. At 16 workers it consumes 23.500 aggregate worker CPU-seconds versus 10.650 serial: **12.850 extra CPU-seconds, or 2.207×**. Instructions rise only 4.6% (94.99 → 99.32 billion); cycles rise 95.1% (58.83 → 114.79 billion), and IPC falls from 1.615 to 0.865. The extra CPU is predominantly less efficient execution of nearly the same instructions. Runnable scheduler wait adds about 0.504 seconds *outside* counted worker CPU; it cannot explain 12.850 extra worker CPU-seconds.

At the serial measured cycle rate, the extra 55.96 billion cycles correspond to about 10.13 CPU-seconds. The remaining roughly 2.72 seconds in this **arithmetic counterfactual** reflect a lower effective counted-cycle rate at 16 workers (about 11.6% lower). This is not an independent causal attribution to frequency: placement, core mix, and PMU behavior can affect it. The phase interference experiment independently finds only 13–17% slowdown of a small register-only target under heavy backgrounds, while the memory-intensive kernels slow much more.

### Cost decomposition

Estimates below are deliberately **non-additive**. The same lost cycle may appear as cache pressure, memory interference, lower IPC, and a longer tail. The primary dependent variable is the extra 12.850 aggregate worker CPU-seconds; wall-only costs are labeled separately.

| Cause | Evidence | Estimated contribution | Confidence |
| --- | --- | ---: | --- |
| Extra instructions / software work | 16-worker instructions 1.046× serial | About 0.5 CPU-s under equal per-instruction cost; small share | High for counter, low for causal conversion |
| ProcessPool / runtime / IPC | Independent pinned processes retain 9.45 of 12.85 extra CPU-s (74%) | Difference of 3.33 CPU-s is a confounded comparative envelope, not an isolated pool cost | High that it is not primary; low for amount |
| Guest scheduler wait | Runnable wait 0.009 → 0.513 s/replay | +0.504 s aggregate wait, outside worker CPU; wall contribution unresolved | High |
| Host throttling / mapping | No recorded cgroup throttle; 16-worker full replay pinning saves about 0.096 s separation wall; matched physical placement makes 8-worker native VM 3.44× faster and complete 8-worker solver 0.700 s faster | Strong at 8 workers, secondary at the current 16-worker setting; still no best-solver wall win | High for interventions; lower for extrapolation |
| All-core compute / frequency | Register-only target slows 13–17%; effective counted-cycle rate falls 11.6% | Roughly 2.72 CPU-s arithmetic counterfactual; attribution to frequency unresolved | Low–medium |
| Shared cache / active capacity | Prefix inflation rises 1.17× at 2 MiB to 3.88× at 16 MiB; strips cut 16-worker kernel CPU 11.7%; PVE's native 16-worker cycles rise 3.94× with constant instructions | Material part of extra cycles; cannot isolate seconds from memory effects | High for causality, low for absolute share |
| Shared memory subsystem / bandwidth | DRAM-origin fills rise 16.7× in full VM replay; memory backgrounds strongly reduce IPC; PVE native 16-worker fills also rise sharply | Material and overlapping with cache; physical DDR throughput unmeasured | High for interference, low for DDR saturation |
| TLB / address translation | Verified huge pages reduce DTLB misses 61% at 16 workers but CPU rises 3.8% | No measured positive 16-worker wall saving | High for negative intervention |
| Load imbalance / tails | Workers active 83.5%; final half-idle window 0.167–0.221 s/replay; two schedulers have no repeatable gain | Window is at most 0.17–0.22 s wall, not recoverable saving; observed gain ~0 | Medium |
| Other / unresolved | Physical host reproduces strong 16-worker native inflation; matched placement resolves most of the initial 8-worker host/VM difference; cache versus DDR cannot be separated by available counters | Unquantified residual; do not force a percentage | Explicitly unresolved |

### Same-replay scaling

All values are median per full 23-round separation replay. Instructions and cycles are billion events; fills are million DRAM-origin cache-fill events. Enabled/running fraction was 100% for the cited perf groups. Full min/median/max/CV and raw receipts are in Test 1.

| Workers | Wall (s) | Worker CPU (s) | Instructions (G) | Cycles (G) | IPC | Runnable wait (s) | DRAM fills (M) | Speedup | Efficiency | CPU inflation |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 10.655 | 10.650 | 94.99 | 58.83 | 1.615 | 0.009 | 20.48 | 1.00× | 100% | 1.00× |
| 2 | 6.223 | 12.232 | 98.96 | 66.30 | 1.493 | 0.006 | 108.49 | 1.71× | 85.6% | 1.15× |
| 4 | 3.799 | 14.530 | 98.30 | 77.03 | 1.276 | 0.006 | 312.11 | 2.80× | 70.1% | 1.36× |
| 8 | 2.837 | 21.054 | 99.49 | 106.98 | 0.930 | 0.006 | 478.13 | 3.76× | 46.9% | 1.98× |
| 16 | 1.819 | 23.500 | 99.32 | 114.79 | 0.865 | 0.513 | 342.15 | 5.86× | 36.6% | 2.21× |

### Eight test verdicts

| Test | Hypothesis | Result | Verdict | Confidence |
| ---: | --- | --- | --- | --- |
| 1 | Extra instructions versus slower execution | 4.6% more instructions, 95.1% more cycles, 2.21× worker CPU | **CONFIRMED:** slower execution dominates | High |
| 2 | Host/vCPU scheduling is primary | Distinct physical-core pinning saves ~0.096 s separation wall; no cgroup throttle | **WEAKLY SUPPORTED:** secondary placement cost | Medium |
| 3 | ProcessPool/feeder causes most inflation | 74% of extra CPU survives with independent pinned processes | **REFUTED:** not primary | High |
| 4 | Concurrent phase interference | Prefix 3.87× under streaming peers; complete direction 2.21× under prefix peers; register 1.15× | **STRONGLY SUPPORTED** | High |
| 5 | Active working set is causal | Size knees and 11.7% 16-worker bitwise row-strip kernel improvement | **STRONGLY SUPPORTED** | High |
| 6 | TLB translation is a large wall target | Huge pages lower DTLB misses 61% but increase 16-worker CPU 3.8% | **REFUTED** as a simple wall optimization | High |
| 7 | Tails / ordered waiting dominate | 0.17–0.22 s tail window, but cost-first and balanced schedules show no repeatable saving | **REFUTED** for tested schedules; some unavoidable tail remains | Medium |
| 8 | Native host-vs-VM scaling | PVE native 16-worker CPU inflation 3.79×; at 8 workers physical pinning makes VM 3.44× faster and match PVE within ~2% wall | **CONFIRMED:** physical penalty at 16 and placement cause of 8-worker gap | High for the native control |

### Answers to the ten causal questions

1. **Why 2.2× CPU?** The same work executes with almost the same instruction count but nearly twice the cycles, plus a lower effective cycle rate. Memory-sensitive phases interfere under concurrency, and larger active working sets amplify the penalty.
2. **Primary type?** More cycles per instruction from shared cache/memory pressure is the strongest explanation. Small software, host-placement, and general all-core effects coexist; scheduler wait is outside worker CPU.
3. **Independent processes?** They retain 9.45 of the 12.85 extra CPU-seconds (74%), even without a pool, feeder, queue, or timed result transport.
4. **Physical host?** Yes for the representative late-round native replay: 16 workers consume 3.79× PVE serial CPU with essentially constant instructions. PVE and VM have similar absolute 16-worker CPU and wall. At 8 workers, the VM's excess largely disappears when its vCPUs are physically matched to PVE's core/L3 placement.
5. **DRAM-origin fills?** Yes: 20.48 million → 342.15 million per identical full replay, a 16.7× rise at 16 workers.
6. **Physical DDR saturation?** Unproven. These fills indicate cache misses served from the memory system, not physical DDR bytes or controller utilization; no working UMC/DF PMU was exposed in the guest or host Phase A audit.
7. **Cache/working set?** Causal in the tested kernels: size-dependent inflation and a bitwise-equal smaller active row strip reduce 16-worker prefix CPU 11.7%.
8. **TLB?** It affects miss counts, but verified huge pages have no 16-worker wall/CPU gain in this control.
9. **Task imbalance?** It leaves a measurable tail window, but neither tested scheduler reliably lowers complete replay wall.
10. **Largest supported next target?** Physical affinity saves 0.700 s for the 8-worker full solver, but that variant remains 0.179 s slower than the current 16-worker default. For faster single solves, a 64-row prefix strip is the only small remaining code lead; its 11.7% kernel benefit is not a measured solver benefit.

### Next CPU action

**NO CLEAR MATERIAL CPU OPTIMIZATION REMAINS for the fastest current 16-worker
single solve.** A host-affinity policy gives a real 0.700-second gain versus
default **8-worker** solves, but the pinned 8-worker result remains 0.179
seconds slower than the contemporaneous default 16-worker solve. It may be
valuable when saving eight worker slots matters; that throughput/capacity
tradeoff was not measured. Guest affinity alone regresses wall. The following
is the only code lead worth a bounded end-to-end check if savings below 0.1
second matter to the operator.

The only implementation target supported by a positive semantically exact intervention is a **64-row strip for the row-major prefix**. It preserved bitwise output on 3,620 checks over 905 real grids and cut the 16-worker prefix kernel CPU from 4.701 to 4.153 ms/call. It regressed serial CPU 1.6%. The current solver's 16-worker prefix critical-path proxy is about 0.613 s, so the kernel percentage transferred unchanged would imply roughly 0.07 s, or 2–3% of a 3.052 s solver; that is an explicitly unmeasured projection. The absolute zero-cost prefix ceiling is 0.613 s. A separate small integration experiment should use paired long full-solver samples at workers 1 and 16 and retain only a reproducible end-to-end gain. Complexity is low-to-moderate; the risk is altered floating-point order or worse serial locality if the production implementation deviates from the bitwise prototype. No other tested intervention has a credible larger measured CPU gain.

The campaign narrows the penalty to **shared-resource-sensitive execution of essentially the same instructions**. The physical host reproduces a large 16-worker penalty, so virtualization is not required for it. At 8 workers, matching physical placement makes the VM's native wall and worker CPU agree closely with the host: physical vCPU placement is the dominant cause of that gap. The 8-worker full solver improves but remains slower than the current 16-worker default. Exact allocation between last-level cache capacity and memory-controller throughput remains unresolved because neither machine exposes physical DDR counters.
