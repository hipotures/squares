# Shared repair queue

This replaces the **multi-boost repair loop** with one completion-driven CPU pool.
It is enabled automatically for a repair family with more than one proposed boost.
The ordinary command and `--resume` are unchanged:

```bash
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search --resume
```

Stop the old controller gracefully before updating executable code. Keep the whole
experiment root. A one-boost diagnostic repair still uses the direct verifier path.

## Scheduling and dispatcher cost

A task describes a boost index and a small tuple of direction indices. Exact input
parsing, uniform-family checks, coordinate enclosures, and rotation preparation
happen before dispatch. Read-only arrays are installed once in each worker, not
pickled afresh for every direction. There is no multiprocessing Manager server.

The one pool is capped by `PACK_JOBS`, visible CPUs, and the existing interval
memory budget. With a 16-CPU budget there are at most **16 submitted batches in
flight**, not thousands of pending futures. Completion of any batch frees a slot;
the scheduler does not wait for earlier submitted directions to finish. Round-robin
selection across pending boosts is dynamic, not a permanent 2x8 or 4x4 allocation.

Batch size starts at one direction and grows to at most eight for cheap directions,
targeting about 0.5 seconds of work. Growth is bounded, an expensive direction
reduces later batch sizes, and the tail returns to small batches. A direction that
takes a second normally remains its own task. The intent is to amortise dispatch
without hiding many long directions in one indivisible batch.

The hot path consumes compact results and refills workers **before** checkpoint
I/O. Checkpoints are throttled to two seconds, plus job completion and errors;
there is no fsync, JSON file read, candidate preparation, or console line for every
task submission. Work completed since the last durable checkpoint may be repeated
after a hard crash. That is preferable to making every worker wait for disk sync.

Each report records coordinator CPU time, dispatch time, checkpoint time, worker
CPU/wall totals, batch sizes, in-flight peak, completed direction count, and observed
completion-to-refill latency. These measurements distinguish dispatcher starvation
from a genuine remaining tail. They are not inferred from `load average`.

## Cancellation and proof boundary

A boost is screened over the full doubled net using the unchanged interval
arithmetic and branch-and-bound method. One direction that cannot pass the interval
gate resolves the screen negatively; unscheduled work for that boost is dropped.
Running tasks poll a shared cancellation byte between bounded box batches.
Cancellation is an exception/control state, **never a certified/refuted outcome**.

A rigorous coverage refutation can also rule out lighter candidates only after
checking exact uniform scaling of every atom weight, identical geometry and net,
and a valid direction outcome with an admissible witness and an upper mass below
one. An interval stall, resolution limit, or generic quick refusal does **not**
prove that a different boost is impossible. Such events never prune other boosts.

A `QUICK_ACCEPTED` result needs every direction to finish with the requisite lower
bound; an empty or partial checkpoint cannot establish it. This is still only
screening. The pool is fully drained before the controller runs the existing full
exact two-route retention gate on surviving proposals, starting with the lightest.
There is no overlap with another 16-worker full-verifier pool. Only a successful
full gate can create VERIFIED or the lower-bound improvement banner.

The quick-first single-boost path also normalises an intentionally absent
`least_cell_mass` into a separate input file. The old `null` value was rejected by
the strict gate's parser before interval work; the original candidate is preserved,
and this normalisation does not replace the full verification requirement.

## Durability and limits

Each family has an immutable manifest, source hashes, code fingerprint, a checksummed
`queue-checkpoint.json`, compact `report.json`, and ordinary supervisor artifacts.
The existing job supervisor provides bounded retries, orphan recovery, memory and
wall-time guards. A queue lock prevents duplicate jobs. On recovery the scheduler
reconstructs status from saved direction evidence, not from a saved `QUICK_ACCEPTED`
string. Changed source, broken checkpoints, and missing worker results are errors,
not mathematical failures. Completed full-gate outcomes and partially applied
screens remain usable after controller interruption.

After upgrading, a queue with a different executable fingerprint is a new job;
it does not reinterpret older direction receipts as if they used the new code.
Prior rejected attempts remain historical evidence, not mathematical impossibility
claims. This change does not erase the campaign or retroactively mark them verified.

The final indivisible direction can still leave a tail. This implementation does
not split a direction's branch-and-bound tree across processes. Diagnosis and full
retention gates remain separate bounded phases. No constant 100% utilisation or
particular mathematical-search speedup is promised.

## Validation and reproduction

```bash
uv run --frozen pytest tests/test_frontier_boost_queue.py \
  tests/test_frontier_repair_batch.py -q

uv run --frozen python -m devtools.bench_frontier_dispatch \
  --workers 16 --samples 3 --target-seconds 12 \
  --output ../Experiments/repair-dispatch-service.json
```

The benchmark is explicitly **synthetic**: workers sleep, isolating IPC and
scheduler service rate rather than pretending a small CI host is a 16-core numeric
server. The one-second task control tests the requested ~16 task completions per
second. The paired barrier/shared control performs the same item durations and
aggregates repetitions into long samples. Neither result predicts a packing-solver
speedup. Use `--task-seconds 0.01 --service-only` to exercise cheaper work and batching.

Local service-control samples used 192 one-second items with 16 process workers:
13.213, 12.052, and 12.083 seconds; coordinator CPU was 0.0954, 0.0781, and 0.0935
seconds respectively. Median service rate was about 15.9 items/second, with under
1% of one CPU spent in the coordinator. A deliberately constructed four-group
long-tail control measured roughly 48-49 seconds with barriers versus 12.1 seconds
with the shared queue. These are scheduler controls, not real search benchmarks.
All timed samples in that experiment exceeded ten seconds and were below one minute.

Correctness coverage includes real serial/parallel direction comparison on retained
small geometry, full-net screening, crash/checkpoint recovery, partial application,
short-task batching, long-tail overlap, cooperative cancellation, strict input and
checksum checks, no cross-boost pruning from stalls, and a real full two-route gate
for a candidate whose initial minimum declaration is null. Synthetic receipts are
used only for controller branch tests and are identified as such in the tests.
