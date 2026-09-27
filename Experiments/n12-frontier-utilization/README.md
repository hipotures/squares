# Frontier utilization correction

## Observations and scope

Base: c704fe1c5627895673c74e12e5dc1c351b11f65b on work/frontier-native-ab.
The supplied live log contains waves of 496.789 and 990.074 seconds, with one
of two jobs already completed while the remaining driver repeatedly executes
serial work. This is a straggler plus a wave barrier; it is not evidence that
both drivers synchronize their phases. The supplied production-candidate
measurement attributes 2379.617 CPU seconds to depth-survey/numpy in its
3600.148-second measurement window. These inclusive observations are not a
controlled full-solver speedup measurement.

Code review found resume-only cohort refill, delayed interpretation of cheap
rationalisation outputs, and a serial float depth survey even while the shared
direction pool was idle. The exact certificate gates and numerical algorithms
are not replaced.

## Changes

- Large float depth surveys in managed generation borrow the existing broker
  and process pool. The driver releases its CPU lease and reacquires it before
  continuing. Depth and direction tasks share the same global slot budget.
- Tasks group consecutive complete 4,000,000-cell oracle blocks. They never
  partition the square reduction for a point. The original colgen._depths body
  computes every block, and output slices are reassembled in their original
  order. Small surveys and calls outside managed generation remain serial.
- Native/BLAS workers are single-threaded. There is no second executor or GPU
  backend. Context arrays are read-only mmap files under the generation wave;
  only bounded in-flight task handles are dispatched, and cleanup removes the
  context files on success or failure.
- A completed rationalisation is adopted immediately, including its required
  gate, before unrelated generation is launched. Scale retries no longer wait
  for another strategy's whole wave.
- Partial cohorts refill at safe pre-wave boundaries after adoption/retirement,
  not only at resume. Existing cycles and artifacts are preserved. Each
  strategy is admitted at most once per portfolio invocation, retaining a
  finite cohort and an opportunity for the outer repair/exhaustion policy.
- Stop checks precede refill and the launch of a new stage. An already-running
  wave still drains before its results are adopted. No speculative proof gate
  is run concurrently with a live generation wave.
- Filesystem progress probes run at 2 Hz rather than the 200 Hz dispatch rate.
  Deadlines are still checked in the dispatch loop.
- The native runtime formatting error that blocked the previous Native A/B CI
  run is corrected without changing native selection or compiled kernels.

## Telemetry

Generation reports add depth_requests, depth_chunks_completed,
depth_worker_cpu_seconds, depth_worker_wall_seconds, depth_tasks,
leased_slot_seconds, mean_leased_slots and solo_serial_seconds. Leases are
scheduler occupancy, not measured OS CPU utilization. Existing worker_cpu_seconds
continues to mean direction service, so depth service is not silently mixed in.
The generation-wave completion line prints direction and depth CPU separately.
The queue's own stdout.log shows directions and depths separately. The legacy
parent heartbeat still displays direction tasks only; generation-progress.json
contains the complete task breakdown.

The performance table distinguishes depth-survey/numpy (serial calls),
depth-survey/numpy-worker (completed parallel task chunks), and
depth-survey/shared (whole surveys including waiting). The shared row records
zero CPU service, hence CPU throughput is unavailable rather than incorrectly
crediting all work to a waiting driver. Do not add these inclusive work rows.

## Validation

The Frontier utilization workflow runs 15 focused cases, plus existing
stop/recovery/policy regressions. Numerical controls cover original block
boundaries and tails, signed/cancelling weights, ordered results, 1/2/4-slot
broker runs, failed task isolation, immutable receipt reuse, and a real
full-generator comparison with serial versus borrowed depth execution.
Controller fixtures cover between-wave refill, finite admission/cycle limits,
immediate scale-result adoption, and stopping during rationalisation.

Reproduce from packing/ after stopping the current runner:

```bash
uv sync --frozen
uv run --frozen pytest tests/test_frontier_utilization.py -q -s
```

PACK_DEPTH_PARALLEL=0 is an explicit diagnostic control for managed generation,
not required for ordinary runs. No extra native build or switch is needed.
CI observations are not a 16-core user-host speedup claim. In particular, LP and
other serial work remain; the wave barrier itself is retained for gate safety.
