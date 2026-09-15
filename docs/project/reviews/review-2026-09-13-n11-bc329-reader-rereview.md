# BC329 Reader Repair: Exact-Commit Rereview

**Disposition: REFUSE calibration admission at
`7e4d2487f586e4200b1261cfa286f37ebda99c49`.** The original F1–F5 repairs are accepted at
their stated scope. F6 remains open: full source-distinct readback admits records whose
phase durations, task positions, or parent identities cannot describe the producer’s
execution.

This is a bounded, independent review under bead `think-62lq`, inheriting the parent
workflow. It reviews the target-free reader repair and its maintained tests; it does not
admit an executed calibration, authorize a three-profile run, or establish a scientific
result. No producer calibration profile, minimizer, interval search, dilation execution,
or BC329 target ran.

The reviewed repository is `/private/tmp/squares-n11-bc329-stack`. The reader and tests
matched these Git objects before and after the supplemental controls:

| Source at the reviewed commit | Git blob | Bytes |
| --- | --- | ---: |
| `packing/devtools/read_fixed_core_calibration_profile.py` | `f4895ff1172d6a1ef827e61e4845b05a1607e713` | 78,677 |
| `packing/tests/test_read_fixed_core_calibration_profile.py` | `0c1a3ec071a67184c13f77ad32974d514e4615dd` | 65,593 |

The prior refusal is
`docs/project/reviews/review-2026-09-13-n11-bc329-source-distinct-reader.md`, reviewed
at `212e0dfc9f7b2e48743cb84ea21b3803822e50b8`. The synthetic fixture declares execution
commit `faa4085db8fb4cf42154afec0022a0585f59196d`. Supplemental full readbacks use that
execution identity and the actual reader commit, with no revision-binder mock.

## Disposition by Original Finding

| Class | Verdict | Evidence and retained scope |
| --- | --- | --- |
| F1: complete source manifest | **ACCEPT** | `_execution_source_paths` reads the execution revision’s Git objects, parses imports without executing them, includes enclosing initializers and runtime declarations, and requires the sorted complete manifest. All 23 omission controls and unexpected, duplicate, alias, blob, digest, and other-revision controls pass. Reader code remains independent of producer helpers. |
| F2: running-reader binding | **ACCEPT** | The binder requires resolved `__file__` to equal the repository reader path, requires exact reader HEAD, and compares on-disk bytes with the committed blob. Supplemental baseline and mutation calls use the real binder. Maintained controls cover outside and other-checkout copies, changed source, and script invocation. See the test-isolation disclosure below. |
| F3: dense/slab agreement | **ACCEPT** | Canonical dense/slab witness equality is required alongside equal charges and separate exact replay. The two distinct valid witnesses with charge 1 refuse; the closed-boundary positive remains accepted. |
| F4: scalar schema and exceptional numbers | **ACCEPT** | Fixed integer/Boolean structures use recursive typed comparison; measured real numbers explicitly permit finite integer/float values. Candidate counts are checked before rational budget arithmetic. Rebound row/route, nested receipt, resource, and supervision substitutions refuse. Oversized number conversion and integer-limit JSON failures follow the refusal path. |
| F5: complete dilation record | **ACCEPT** | The reader independently derives reduced squares, positive surds, irrationality, polynomials, and 15-place half-up decimal presentations, and checks fixed containment, domain, invariant, relation, and endpoint statements with types. Rebound mathematical and scalar mutations refuse. |
| F6: lifecycle/topology consistency | **REFUSE** | Original overlong worker phases, exit ordering, out-of-lifetime tasks, reversed raw/exact tasks, route-span violations, and direct self-parent controls now refuse. The remaining contradictions below still receive full `status: accepted` proofs. |

The exact arithmetic continues to support the frozen fixture’s raw minimum and budget 2,
normalized minimum and budget 1, integer scale 8, and 14,404 retained direction rows.
The factor and side squares are respectively `132710404/33189121` and
`298598409/132756484`; their positive-root polynomials and decimal presentations agree
with the repaired record.
The endpoint remains a non-strict supremum conclusion with no individual endpoint
certificate. These mathematical checks do not verify that a synthetic row collection
resulted from kernel execution.

## Remaining F6 Findings

### R1 — High: enclosing phase and supervisor durations remain unchecked

Reader lines 1846–1872 check worker elapsed/exit ordering and a selected sum of disjoint
worker phases. They do not bind source loading to its enclosing preflight, launch to
observed worker exit, or accumulated cleanup to the post-exit lifetime.

Each following mutation is independent.
All other baseline clocks retain `preflight_seconds = 0.1`,
`worker_elapsed_seconds = 1.0`, `worker_exit_seconds = 1.05`,
`external_lifetime_seconds = 1.2`, and `parent_final_readback_seconds = 0.1`. The
receipt inventory and receipt-size fixed point are rebuilt before the real
`read_profile` entry point is called.

| Mutation | Required contradiction check | Observed |
| --- | --- | --- |
| `source_loading_seconds = 0.9` | Source loading occurs inside the 0.1-second preflight. | Accepted |
| `launch_seconds = 1000000.0` | Launch finishes before the 1.05-second worker-exit observation. | Accepted |
| `supervisor_cleanup_seconds = 1000000.0` | Both cleanup calls finish inside the 0.15 seconds between worker exit and external readback completion. | Accepted |

The producer’s source-loading block is nested within preflight at
`packing/devtools/calibrate_fixed_core_packet.py:4014`; launch is timed at line 3647;
worker cleanup follows observed exit at line 3703; readback cleanup is accumulated
before final lifetime publication at lines 3808–3834. These checks follow that execution
order and do not assume launch is disjoint from worker work.
Cleanup during final readback also overlaps that readback duration.

**Fix:** enforce the three necessary bounds independently, using a documented tolerance
for measured-clock subtraction.
Retain equality controls and independent violations.
Do not add overlapping supervisor durations to the sum of worker phases.

### R2 — High: task intervals need not fit the sequential phase schedule

Reader lines 1320–1332 constrain tasks to the worker lifetime; lines 1414–1427 constrain
each route’s span to its phase duration; lines 1504–1510 order raw completion before
exact work. Those checks still permit a task to precede the phases that must come before
it, or to leave insufficient time for phases that follow it.

The maintained pooled fixture is used with two configured workers, one observed child,
all 2,881 tasks in each route, and `worker_elapsed_seconds = 2.0`. Its phase durations
are preflight 0.1, raw 0.5, normalization 0.1, exact 0.5, interval 0.1, dilation 0.1,
and worker readback 0.1 seconds.
Each control shifts only one route’s task times, rebuilds child summaries, both affected
record bindings and the inventory, then invokes full real-binder readback.

| Control | Contradiction | Observed |
| --- | --- | --- |
| Shift raw tasks by `-0.19` seconds | First raw task starts at approximately 0.01, before the 0.1-second preflight can finish. | Accepted |
| Shift exact tasks by `-0.3` seconds | First exact task starts at 0.5; preflight, raw, and normalization already require at least 0.7 seconds. Raw task observations nevertheless finish before exact task observations. | Accepted |
| Shift exact tasks by `+0.8` seconds | Last exact task finishes at approximately 1.88805; the subsequent interval, dilation, and worker readback require another 0.3 seconds, beyond worker elapsed 2.0. | Accepted |

The sequence is explicit in producer `run_worker` and `execute_calibration`: preflight
finishes before raw begins; normalization follows raw; exact precedes interval,
dilation, and the worker readback.

**Fix:** verify that route observations can fit a sequential schedule with the retained
phase durations. At minimum, route starts must follow the summed preceding disjoint
durations, and route finishes must leave the summed following durations before worker
elapsed. Preserve the existing route-span and cross-route ordering checks, and cover
allowed boundary equality.
More generally, propagate feasible phase start/end bounds through the sequence so
durations and observations describe one possible schedule.
Do not infer that child task starts must follow the parent’s launch-duration endpoint:
parent launch timing can overlap worker execution.

### R3 — High: a two-process parent cycle is accepted

The pooled control reports coordinator `pid = 101, ppid = 201, pgid = 101` and route
child `pid = 201, ppid = 101, pgid = 101`. Both route sidecars and the coordinator
summary carry matching identities, all task/child summaries are rebuilt, and full
readback accepts.

Reader lines 1326–1327, 1383–1384, and 1453 reject direct self-parenting but not this
cycle. The recorded supervisor is the live parent of the calibration worker; it cannot
simultaneously be one of that worker’s route children.

**Fix:** require every route child/task PID to differ from the retained coordinator PPID
as well as its PID. Retain an independent, coherently rebound cycle control and the
legal one-child/two-configured-workers positive.

## Additional Scoped Follow-Up

**R4 — Medium: execution identity accepts a Git tree object.** Changing the receipt’s
source and invocation execution identity, and the separately supplied expected execution
argument, to tree `bb203b4df4ad2d4e65d45c2c3feee479911b6681` receives full acceptance.
This is the tree of the synthetic execution commit; every source byte still binds.
The control checks with `git cat-file -t` that the identifier denotes a tree.

The producer requires its declared execution revision to equal Git HEAD, so a tree
object is not a possible producer execution commit.
The reader’s binder checks only the execution identifier’s hexadecimal shape before
source discovery.
Require `git cat-file -t <execution>` to return `commit`. This does not
reopen F1’s repaired closure completeness: it is a separate object-type contract.
It also does not bypass an independently frozen, valid commit expectation; the control
deliberately supplies the tree ID as that expectation.

## Validation, Retained Controls, and Limits

The completed focused run used project CPython 3.14.7:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 -m pytest -q -p no:cacheprovider --basetemp /private/tmp/bc329-reader-rereview-exact-readonly -k 'not running_reader_origin_and_cli_copy_refusal' tests/test_read_fixed_core_calibration_profile.py
```

Result: **94 passed, 1 deselected in 225.11 seconds**. The suite creates synthetic row
artifacts; it does not run a producer calibration.
Most maintained full-read tests mock the revision binder, so the supplemental controls
use the actual binder and independently confirm a positive baseline first.

An initial unfiltered suite was interrupted after reporting 10 passed tests in 46.84
seconds.
Its origin-binding test includes a brief write/restore of the repository reader,
discovered while reviewing the test source.
That initial selection therefore cannot be described as free of transient repository
writes. The reader and test files were verified byte-identical to the reviewed Git blobs
afterward, and the completed rerun excluded that test.
No repository change from this review remains, and no bead or PR was edited.
All supplemental mutations operate on disposable copied artifacts.

The local `/private/tmp` controls below are review attachments, not files in this PR.
The discriminating cases must become maintained tests before a later admission verdict.

Retained review artifacts:

- `/private/tmp/bc329-reader-rereview-controls.py`: reproducible controls with exact
  source checks, refusal to reuse a work directory, baseline restoration, and
  per-control outcomes/timings.
  It imports maintained test helpers only for synthetic artifact bookkeeping; the reader
  imports no producer/helper code.
- `/private/tmp/bc329-reader-rereview-controls.json`: baseline, independent nested and
  supervisor clocks, parent-cycle, execution-tree, and malformed-JSON CLI outcomes.
- `/private/tmp/bc329-reader-rereview-phase-controls.json`: baseline and the three
  independent phase-position outcomes.
- `/private/tmp/bc329-reader-rereview-controls/synthetic-profile` and
  `/private/tmp/bc329-reader-rereview-phase-controls/synthetic-profile`: copied
  synthetic baselines, restored after controls.

Run the retained script with the project interpreter and new `--work` and `--result`
paths. Supply `--repository /private/tmp/squares-n11-bc329-stack` and
`--synthetic-fixture /private/tmp/bc329-reader-rereview-exact-pytest/source-distinct-profile0/profile-1`.
Add `--phase-positions-only` for the second group.
The script refuses source drift from the reviewed reader/test blobs.

The malformed-JSON CLI control returned exit 2, empty stdout, and a concise `REFUSED`
message. No new exceptional-parser finding is claimed from it.
The earlier symlink/special-file, strict JSON, deadline, sampled RSS, direction/digest,
typed-count, valid serial, valid overlapping pool, touching-task, and equal-witness
controls remain necessary and pass in the completed selection.

This review does not exhaustively fuzz parser depth, all future import syntaxes, every
scalar field, or every possible process schedule.
It does not attest the truth of host observations, rerun dense/slab minimization, replay
an interval subdivision tree, run the full project validation surface, or review later
repository edits. The confirmed F6 contradictions are sufficient to keep admission
refused. Repair them with maintained independent controls, freeze the new commit, and
request bounded rereview before any positive calibration execution.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
