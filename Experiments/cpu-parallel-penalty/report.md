# Causal sources of the n=12 CPU parallel penalty

Research starting point: `897b722f2997fbf09b99b1700787a0052270de30`
on `main`; accepted production integration `011aa1b5` is an ancestor.
The campaign is in Phase A. Tests 4–8 and final synthesis remain pending.

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
Tests 4–6 will test interference, working-set sensitivity, and translation
mechanisms before attributing the fill increase to a particular shared
resource.
