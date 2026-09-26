# Native kernel A/B laboratory

## Purpose and isolation

This is an experimental fork, `work/frontier-native-ab`, starting at
`840f574fa2e22fd965163427f0b2d95f42f91d45` on `work/frontier-autonomy`.
Issue #5 tracks acceptance. Neither the source branch nor `main` is changed.
No optimization is permanently accepted by the existence of this branch.

The workflow is manual: run a reference session, stop gracefully, change one
switch, and run another session. A real campaign keeps searching and retaining
certificates through the existing full gate. A separate replay mode repeatedly
executes captured real kernel inputs without advancing the campaign.

**Different campaign hours are not controlled A/B measurements.** Strategy,
side length, support size, LP degeneracy, integer bit lengths and the fraction
of time spent verifying change as the search progresses. Completed work rates
are useful observations, not automatic speedup proofs. The sealed replay is
provided to answer the harder question: does a switch do the same work faster?

## Analysis of the computational path

The unit of optimization is a kernel, not a file extension. HiGHS already runs
native C++; NumPy executes compiled loops and sometimes BLAS. Moving the Python
wrapper around either one to C++ would not remove their underlying work.

| Component | Existing implementation | Experiment and reason | Important limit |
| --- | --- | --- | --- |
| Axis-0 prefix pass | Accepted row-major C helper, NumPy reference | `prefix` selects the accepted helper independently | Mostly memory traversal; no promise of linear multicore scaling |
| Small stable top-k | Accepted C helper, NumPy reference | `topk` selects the accepted helper independently | Preserve ties, non-finite exclusions and the special zero-grid spatial rule |
| Difference scatter | Four `np.add.at` calls | `scatter` uses four ordered C passes without generic indexed-ufunc machinery | Never interleave the four passes: repeated cells change floating-point addition order |
| Reachable slab compaction | Python loop assigning NumPy row slices | `compact` uses strided C copies | The compact array still exists; eliminating it previously failed to show a material 16-worker gain |
| Arrangement vertices | Python list of every pair, index arrays, several large NumPy temporaries | `vertices` counts and fills valid intersections in C, retaining pair order and the reference return shape | It is still quadratic in line count and performs a second sizing pass |
| Exact prepared depth | Python loops over integer slabs and Fraction weights | `exact-depth` prepares arbitrary-precision C++ slabs/weight scale once and evaluates exact queries | Conversion and FFI overhead remain; small families may not benefit |
| Floating depth survey | Chunked NumPy matrix products and masks | Instrumented, not replaced in this experiment | Fusing it can alter summation order and near-threshold rankings |
| LP | Persistent HiGHS model, serial managed solve | Instrumented, not rewritten | Optimize model/basis reuse separately; a C++ wrapper is not a new LP algorithm |
| Exact sweep / interval certificate verifier | Exact geometry and interval branch-and-bound with independent checks | Unchanged | A native port requires a separate soundness review, especially outward rounding and overflow |
| Scheduler/checkpoints | Python process broker and durable receipts | Unchanged CPU budget and four-direction task size | Higher load alone is not useful-work speedup |

This is deliberately smaller and more falsifiable than a full fused C++
`placement_cells` rewrite. The reference functions remain in the same codebase,
and each selected component can be removed or integrated independently after
real measurements. No GPU work, nested OpenMP pool, new search strategy or
relaxed proof tolerance is introduced.

### Exact arithmetic and floating-point contracts

`exact-depth` uses Boost.Multiprecision `cpp_int`, not int64/int128 masquerading
as arbitrary precision. Slabs and query points retain positive common
denominators; closed-boundary comparisons are integer inequalities. Signed and
duplicate weights are preserved in controls, and the result is reduced to an
exact Fraction. A context is immutable after construction, process-local, and
freed with the matching C++ destructor. Native exceptions are returned as
operational errors rather than crossing the C ABI.

The floating kernels build with `-O3 -fno-fast-math -ffp-contract=off`. No
architecture-specific `-march=native` flag or internal worker count is enabled.
The C scatter intentionally preserves the original four update passes. Prefix
addition order, source-pair order, candidate tie ordering and zero-grid behavior
are regression-tested. The original certificate proof gate remains independent
of these search kernels.

Relevant implementation documentation:

- [GCC floating-point optimization options](https://gcc.gnu.org/onlinedocs/gcc/Optimize-Options.html)
- [Boost.Multiprecision cpp_int](https://www.boost.org/latest/libs/multiprecision/doc/html/boost_multiprecision/tut/ref/cpp_int_ref.html)
- [Python ctypes](https://docs.python.org/3/library/ctypes.html)

## Production profile and reference semantics

The accepted production profile is now the default:

```text
production = prefix,topk,scatter,compact
```

A normal `campaign`, `replay`, or `doctor` command therefore uses these four
native kernels without an explicit `--native` argument. The previous Python/NumPy
path is no longer the production workflow.

`--native none` is retained only as an explicit differential/reference oracle for
regression tests, corpus sealing, and diagnostic A/B work. It disables all six
optional paths; NumPy and HiGHS themselves still execute native code.

Each name independently enables one native path:

```text
prefix
topk
scatter
compact
vertices
exact-depth
```

Aliases:

```text
none                      all switches off
production                prefix,topk,scatter,compact (accepted default)
all                       all six switches on
prefix,topk,compact        an explicit cumulative combination
```

There is no silent fallback when a requested native library is missing, stale,
unloadable or violates the ABI. Startup preflight fails before search begins.
The special zero-weight top-k rule remains the reference algorithm and is
reported as `py-zero`; it is not silently counted as C work.

## Installation and first reference hour

Do not switch the checkout while the old runner is calculating. First send
Ctrl-C to that runner and wait for its saved-state summary. Preserve the
experiment root and `state.json`.

```bash
cd ~/DEV/squares
git fetch origin
git switch work/frontier-native-ab
git submodule update --init --recursive
cd packing
uv sync --frozen
uv run --frozen python -m devtools.native_ab build
uv run --frozen python -m devtools.native_ab doctor --native all
```

The explicit build needs a C compiler, a C++17 compiler and Boost headers. On
Ubuntu/Debian an administrator can install `build-essential libboost-dev`.
`build --core-only` builds all switches except `exact-depth`; the Python
reference requires no additional compiler. Binaries live in a source-keyed
`~/.cache/squares-native-ab/` directory, not in Git. Compiler commands, versions,
source and binary hashes are included in session metadata. Re-run `build` after
pulling changes to native sources. Do not rebuild libraries during a session.

First reference hour, continuing the existing campaign and sampling real inputs:

```bash
uv run --frozen python -m devtools.native_ab campaign \
  --root ../Experiments/n12-frontier-search --resume \
  --native none --workers 16 --generation-trials 3 \
  --minutes 60 --label reference \
  --capture ../Experiments/n12-native-corpus
```

The ordinary timestamped frontier output remains visible. After 60 minutes the
wrapper requests the same graceful stop as Ctrl-C. It finishes **only the
already-running bounded stage/wave**, adopts and interprets that completed result,
and leaves any later normal/deep/maximum escalation resumable for the next
session. It does not start a fresh escalation merely to "finish the cycle".
The final elapsed time can therefore exceed 60 minutes by the remaining time of
one already-running stage/wave, but not by the whole escalation ladder.
`--minutes 0` disables the timer for entirely manual control. A stop during
startup is deferred until the controller has installed its signal handlers.
Repeated Ctrl-C does not silently escalate to destructive termination.

When draining is actually finished and the final throughput report has been written,
the wrapper emits a terminal BEL plus a visible completion message. Errors emit a
double BEL and a visible error message; if cleanup/draining continues after an error,
a second completion/error notification is emitted when that cleanup has really ended.
Terminal bell behavior still depends on the user's terminal emulator settings.

For historical/diagnostic A/B work, one switch can still be selected explicitly:

```bash
uv run --frozen python -m devtools.native_ab campaign \
  --root ../Experiments/n12-frontier-search --resume \
  --native compact --workers 16 --generation-trials 3 \
  --minutes 60 --label compact-only
```

Use the same command with `scatter`, `vertices`, `exact-depth`, `prefix`, or
`topk`. For causal isolation, return to `none` between independent experiments.
Use cumulative combinations only after individual switches have evidence.
The production profile has been accepted from the measured campaign/replay results;
single-switch modes remain available only for diagnostics and regression work.

A job recovered from an already-owned specification keeps its original native
choice. Its actual backend is reported. Completed reused artifacts get no new
kernel-work credit. A session with more than one direction profile is marked
mixed, not presented as a clean experiment. Never run two campaigns on the
same root; the existing campaign lock remains authoritative.

## Throughput, not just duration

Each session prints and saves a final table with rates computed over the
**measurement window ending when the timed/interactive stop was requested**, not
over the later drain. The final session and drain durations and final cumulative
counts remain in JSON separately. This prevents a long drain from diluting an
otherwise valid one-hour baseline.

The table includes:

- completed calls per wall second;
- logical units per wall second;
- logical units per kernel CPU second;
- the raw counts, worker-time totals and workload-size bins.

A direction call is one completed direction. `event_cells` is the number of
mass-grid cells constructed. `corner_updates` is four updates per scattered
site. `copied_values` counts compacted doubles. `line_pairs` counts the logical
pairs considered, regardless of the implementation's internal number of
passes. `point_square_queries` counts exact or surveyed membership questions.
LP records include solves, matrix-size descriptors and simplex iterations.
These are algorithmic work units, **not CPU instruction counts**.

The report additionally records new completed stages/hour, new verified bound
improvements/hour, initial/final exact bounds, compiler/profile/CPU affinity,
and software versions. These campaign outcome rates are workload-dependent.
A selected kernel that was not exercised is explicitly listed as such.

Worker CPU and wall times are inclusive. For example, a direction includes
prefix and compaction work. Never sum all kernel rows to infer total CPU time.
For fair kernel comparisons use matching workload bins; for robust causal
comparisons use the sealed corpus. Integer bit lengths and LP conditioning can
still differ inside a size bin.

The first-hour snapshot and the drain are separated in JSON. The first snapshot
can lag completed work by approximately one second; the final normal-shutdown
report flushes all process counters. Reports are stored alongside the campaign:

```text
Experiments/n12-frontier-search-native-runs/<epoch>-<session>/
    session.json
    progress.json
    stop-window.json
    processes/*.json
    performance.json
    performance.txt
```

Workers update independent cumulative snapshots; the reader sums each once.
There is no shared counter lock, per-cell IPC, or global logging manager.
Periodic writes are throttled and normal process finalization flushes counters.
An abnormal kill can lose approximately the last second of completed work per
process; incomplete reports say so. Existing snapshots survive a reboot.

Read an old or interrupted measurement without launching computation:

```bash
uv run --frozen python -m devtools.native_ab report \
  --session ../Experiments/n12-frontier-search-native-runs/<session-directory>
```

## Matched real-input replay

Capture is bounded across all processes: at most 64 direction inputs, 16 vertex
families and 16 exact-depth inputs. It saves input data, not full dense grids,
and uploads nothing. This is a sample, not an exhaustive or unbiased trace.
Generate another corpus later when the workload changes substantially.

After the capture session has stopped, freeze the corpus and calculate reference
signatures with every switch off:

```bash
uv run --frozen python -m devtools.native_ab seal \
  --corpus ../Experiments/n12-native-corpus
```

Sealing stops further capture into that directory. Replay refuses modified input
files or a changed manifest. The manifest ID identifies the exact workload.

Run the same real inputs for an hour in reference mode:

```bash
uv run --frozen python -m devtools.native_ab replay \
  --corpus ../Experiments/n12-native-corpus \
  --output ../Experiments/n12-native-replays \
  --native none --workers 16 --minutes 60 --label reference
```

Then repeat with exactly one switch:

```bash
uv run --frozen python -m devtools.native_ab replay \
  --corpus ../Experiments/n12-native-corpus \
  --output ../Experiments/n12-native-replays \
  --native compact --workers 16 --minutes 60 --label compact-only
```

Each replay checks its result against the independent reference signature.
Mismatch is an error, not a performance result. The pool remains bounded by the
requested worker count; workers cache the bounded input corpus and kernels do
not create nested pools. Replay produces no new packing bound. Its throughput
is kernel-replay throughput, not a prediction of full-solver speedup.

## Acceptance protocol

Retain the JSON/text summary and corpus ID for each hour. Compare the same
hardware, worker count, profile, input mix and source revision. Alternate order
(A/B then B/A) and repeat promising results. Check both throughput and CPU cost
per unit. Require correct results, no new operational errors, no unacceptable
memory increase, and a real campaign benefit after a kernel win.

A faster isolated kernel may not help the whole program because another phase,
memory bandwidth or a serial tail dominates. An apparently faster next campaign
hour may simply be easier. Only accepted experiments should later lose their
switches and be merged permanently; unpromising ones remain removable.

The independent certificate sweep and interval verifier are intentionally not
ported in this first experiment. Their native ports need their own soundness,
overflow and outward-rounding analysis rather than being hidden inside a broad
performance change.
