# Shared generation scheduling and timestamped phases

The frontier controller can overlap independent generation strategies as well as
repair directions. This is a bounded portfolio of real solver jobs, not a change
to any certificate theorem condition or an attempt to parallelise one simplex pivot.

## Run

Stop the old controller gracefully before pulling new source. Keep the existing
experiment root and all its certificates.

```bash
cd ~/DEV/squares
git switch work/frontier-autonomy
git pull --ff-only
cd packing
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search --resume --generation-trials 3
```

`--generation-trials` defaults to 3 and admits at most six distinct useful
strategies at one exact side. The count is also capped by the CPU budget and an
explicit remaining cycle limit. `--generation-trials 1` retains sequential
strategy selection; each generator still reuses its direction pool across column
rounds. `--strategies` continues to restrict the available mathematical methods.
A useful same-side precision refinement is not delayed by speculative siblings.
An already-active older single cycle finishes before new cohorts are admitted.

## CPU ownership

During a generation wave, one long-lived direction pool serves every admitted
strategy. A solver driver holds one CPU lease while doing setup, LP, pricing,
exact ceiling analysis, rationalisation or output serialization. At a separation
barrier it releases its lease and waits. Ready four-direction production chunks
from different drivers are scheduled fairly in completion order, under:

```text
serial solver leases + submitted direction chunks <= PACK_JOBS
```

A driver must reacquire a lease before it consumes its ordered results and starts
the next LP. The driver cannot create a nested direction pool, and managed HiGHS
instances explicitly use one thread with parallel mode disabled. Result reduction
and row insertion retain the production direction order; scheduler completion
order is not a tie-breaker for numerical decisions.

The coordinator receives one request per separation round. Immutable point and
weight arrays are stored once per round and opened read-only through NumPy memory
maps, with a bounded worker cache. Subsequent chunk dispatch uses small context
handles, not repeated full arrays. Four directions remain one task, preserving the
previously accepted production granularity instead of issuing a callback per cell.
Coordinator, process startup, operating-system work and watchdog CPU are overhead;
the lease invariant bounds computational jobs, not every background kernel task.

## Deliberate boundaries

This implementation overlaps independent strategies inside a generation wave.
It is not an unlimited scheduler across arbitrary sides or every proof procedure.
Full certificate verification is performed only after the generation wave has
drained, using the existing verifier's CPU budget. Further stages use a new wave.
There may still be a serial tail if all other admitted jobs finish, or low CPU use
if all remaining useful work consists of a few serial LP/pricing owners. A fixed
portfolio of three strategies cannot occupy sixteen CPUs when all three are in
indivisible serial phases. No 100% CPU utilisation or 16x speedup is promised.

The goal is lower wall time for useful, comparable work, not a high load-average
number. Concurrent strategies can do more total search work than a lucky sequential
strategy that finds a proof first. Admission is bounded to avoid speculative work
growing without limit. A measured objective plateau now stops escalation after the
normal stage when it matches the screen result, rather than unnecessarily running
the deep stage before recognizing the same plateau.

## Timestamps and timings

Each controller console line, including multi-line findings and the shutdown
summary, starts with an integer Unix timestamp. Ordinary output remains concise.
For example (illustrative values):

```text
[1790350000] [portfolio] admitted=3 slots=16 strategies=centre,pricing,windows L=3.961968474
[1790350060] [running] generation-queue elapsed_s=60.0 serial=1 directions=15 slots=16 jobs=0/3 coordinator_cpu=0.420s
[1790350140] [generation-wave] completed wall=140.123s coordinator_cpu=0.932s driver_cpu=74.221s direction_cpu=825.123s max_busy=16/16
[1790350160] [stage] ... time=138s verify_s=19.811 stage_wall_s=160.021 -> UNRESOLVED
```

`time` remains the generator's wall duration; `verify_s` is the separate verifier
elapsed duration; `stage_wall_s` includes scheduling/wait time since the stage was
prepared and can include a restart gap. Unix timestamps provide clock alignment;
phase and CPU durations use monotonic/process clocks where appropriate.

Each stage additionally writes `phase.log` with start/end timestamps and elapsed
seconds for `site_setup`, `lp`, `separation`, `pricing`, `ceiling`, and
`rationalisation`. Its `result.json` includes `phase_timings`. Separation elapsed
time includes the driver's shared-queue wait; it is not pure worker CPU time.
`generation-progress.json` and the wave report separately record coordinator CPU,
worker CPU, serial leases, in-flight direction tasks, and completed jobs. These
measurements distinguish LP, exact ceiling work, queue wait, and verification
instead of guessing the active bottleneck from a CPU screenshot.

## Recovery and stop

The authoritative campaign state records the admitted cycle indices and wave
manifest before launch. The existing detached supervisor owns the broker and its
children, retaining CPU/memory/disk/wall watchdogs and process-identity protection.
Per-job receipts bind completed output hashes, the command, source fingerprint and
seed bytes. Changed inputs or outputs are refused rather than reused.

`--resume` first adopts any already-completed wave. Valid completed jobs are not
recomputed. Partial unknown outputs are archived before an unfinished stage is
retried; no LP-internal checkpoint is claimed. An individual failed driver is an
operational error, not SEARCH_FAILED, and does not prevent independent jobs from
finishing. A wave-level supervisor failure uses the existing bounded recovery.

The first Ctrl-C requests a stop. The currently admitted bounded cohort finishes
its cycle classifications and proof checks; no new cohort is admitted afterward.
This can take longer than one stage because an admitted cycle may escalate.
Repeated signals do not silently turn into destructive termination. Power loss
can discard unfinished computation, but not completed atomically saved evidence.

## Validation and measured scope

The implementation passed 121 dedicated frontier/generation tests and 40 generator
regressions in the integration run. Controls include real serial/shared generator
comparisons, bounded CPU leases, independent-driver failure, deadlines, receipt
reuse, full controller Ctrl-C, and a crash between completed job receipts and wave
adoption. Positive certificate promotion continues through the full two-route gate.

Integration evidence:
https://github.com/hipotures/squares/actions/runs/36160449658

A paired benchmark of the same small real generator jobs, including startup,
measured these three samples with a two-worker budget on GitHub Actions:

| Sample | Sequential wall | Shared wall | Ratio | Coordinator use of one core |
| --- | ---: | ---: | ---: | ---: |
| 1 | 19.841 s | 12.809 s | 1.549x | 7.62% |
| 2 | 19.757 s | 12.785 s | 1.545x | 7.41% |
| 3 | 19.830 s | 12.675 s | 1.565x | 7.49% |

All paired mathematical summaries and ordered round decisions matched. These are
small, bounded generator workloads on two workers, not the user's live frontier
state, a sixteen-core scaling measurement, or evidence of a new packing bound.
Startup contributes to the measured gain. They demonstrate working overlap and
measured dispatcher cost, not a promised speedup of the production campaign.

Reproduce on a fresh persistent path:

```bash
uv run --frozen python -m devtools.bench_frontier_generation \
  --root ../Experiments/generation-scheduler-benchmark \
  --workers 16 --samples 3 --target-seconds 18
```

The benchmark also accepts `--grid-counts`, `--steps`, `--row-rounds`, and
`--stage-seconds` for larger representative work. Use the saved phase timings of
the actual campaign before choosing further kernel or pricing optimisations.
