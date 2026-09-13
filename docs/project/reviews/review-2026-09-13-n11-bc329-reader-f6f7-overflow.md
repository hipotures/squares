# BC329 Reader F6/F7: Exact-Commit Admission Review

**Disposition: REFUSE calibration admission at
`406009647223c9f53c828d5d29707897f12535b1`.** F6a, F6c, and F7 are accepted at their
stated scope. The finite-arithmetic schedule repair for F6b is sound, but F6b remains
open because summing individually finite phase durations can overflow and pass both
lifetime checks. This finding is tracked as `think-px86`; the independent review is
tracked as `think-25un`.

This bounded review inherits the parent workflow and covers the reader repair and its
maintained tests in `/private/tmp/squares-n11-reader-f6f7-7e4d`. The prior refusal is
[the exact-commit rereview](review-2026-09-13-n11-bc329-reader-rereview.md) at
`7e4d2487f586e4200b1261cfa286f37ebda99c49`. All supplemental artifacts are synthetic and
temporary. No producer calibration profile, minimizer, interval search, dilation
execution, or BC329 target ran.
The only producer function called was `validate_document`, which checks the receipt
schema.

## Reviewed Identity

The repair is a direct child of the prior reviewed commit.
Its tree is `32719cfb39eb3ac1da8231552b9ab283737dc0d9`.

| Repository-relative path | Git blob at `40600964` | Bytes |
| --- | --- | ---: |
| `packing/devtools/read_fixed_core_calibration_profile.py` | `fc67e3d14b14ca749ce39fadb31040c4624d7aaf` | 80,410 |
| `packing/tests/test_read_fixed_core_calibration_profile.py` | `0ba8793b6ca3193edc012dca0290403fbd12890d` | 73,426 |
| `packing/devtools/calibrate_fixed_core_packet.py` | `d63d4ec57038539b5bb57b8673c4e2eaaa79da3d` | 175,859 |

Only the reader and test files change in the repair: 245 insertions and one deletion.
Their on-disk Git object identities matched the reviewed blobs before and after the
checks. The checkout remained clean.
The synthetic fixture declares execution commit
`faa4085db8fb4cf42154afec0022a0585f59196d`; its source manifest is reconstructed from
that commit’s Git objects.
Full supplemental readbacks use that execution identity and the actual reader commit
without mocking `_bind_revisions`.

After the checks and their source-identity verification completed, another lane advanced
the isolated checkout to `9bc76b322096c2f12f01def71ca125a892a486c3` while this report
was being finalized.
That later repair changes both blobs.
This report covers only `406009647223c9f53c828d5d29707897f12535b1` and supplies no
verdict on the later repair.

## Disposition by Obligation

| Obligation | Verdict | Evidence and scope |
| --- | --- | --- |
| F6a: nested preflight, launch, and cleanup clocks | **ACCEPT** | Source loading is bounded by preflight; launch is bounded by observed worker exit; cumulative cleanup is bounded by the post-exit lifetime. Independent violations refuse and equality controls pass through the real binder. |
| F6b: sequential raw/exact task positions | **REFUSE** | The new earliest-start propagation correctly rejects the prior three position contradictions and a supplemental delayed-raw contradiction. An internally infinite cumulative phase duration nevertheless receives full acceptance; see R1. |
| F6c: parent cycle and process identity | **ACCEPT** | Every route task and child PID must differ from both the coordinator PID and its PPID. Coherently rebound cycles using the first or second route child refuse. Legal one-child, two-child, and touching-task cases pass. |
| F7: execution identity must be a Git commit | **ACCEPT** | The actual binder requires `git cat-file -t` to return `commit`. Full controls supplying coherently rebound tree and blob identities refuse, and the commit baseline passes. |

The prior F1–F5 dispositions are retained at their recorded scope.
Their ordinary regression controls pass in this review’s focused selection.
R1 identifies a distinct gap in arithmetic over finite clock inputs; it does not dispute
F4’s rejection of nonfinite or oversized numeric inputs at conversion.

## R1 — High: Finite Phase Durations Overflow Into an Accepted Lifetime

**Location:** `packing/devtools/read_fixed_core_calibration_profile.py:1260`, with
reachable callers at lines 1534 and 1904. **Tracking:** `think-px86`.

`_not_later` permits eight ULPs of measured-clock roundoff:

```python
return first <= second or first - second <= 8 * max(math.ulp(first), math.ulp(second))
```

When `first` is positive infinity and `second` is finite, both the difference and the
ULP allowance are infinity.
The second comparison is true.
Individually finite JSON inputs can reach this case through the existing phase sum and
the newly added sequential schedule.

The independent control starts from a fully accepted serial synthetic profile and makes
these changes:

| Field or group | Value |
| --- | ---: |
| Each of `preflight_seconds`, `raw_seconds`, `normalization_publication_seconds`, `exact_seconds`, `interval_seconds`, `dilation_seconds`, `full_readback_seconds` | `4e307` |
| `worker_elapsed_seconds` | `5e307` |
| `worker_exit_seconds` | `6e307` |
| `external_lifetime_seconds` | `7e307` |
| Calibration allowance and matching invocation-identity allowance/deadline | `6e307` |
| External allowance and matching invocation-identity allowance/deadline | `8e307` |
| RSS observation lifetime and rebuilt unobserved trailing duration | `7e307` |

The invocation origin stays `10.0`; adding it to these allowances leaves the displayed
floating-point deadline values unchanged.
The other clocks retain their baseline values.
The receipt inventory and receipt-size fixed point are rebuilt.
There is no `Infinity` or `NaN` token in the input, and the artifacts, complete source
manifest, mathematical rows, and reader binding remain valid.

The exact sum of the seven retained phase durations is greater than the finite worker
lifetime. Floating-point addition returns `inf`, however, and `_not_later(inf, 5e307)`
returns `True`. The cumulative earliest-start calculation also becomes `inf` and passes
its final comparison.
Full `read_profile` returns `status: accepted` in **3.44 seconds**. An ordinary
excessive finite phase sum refuses with
`worker phase durations contradict worker lifetime`, so the control distinguishes
overflow from a generally inactive check.

The producer schema admits these inputs.
Direct calls to `validate_document` accept both the serial baseline and the mutated
receipt. The schema requires finite ordered allowances at producer lines 1638–1657 and
finite nonnegative clock fields at lines 1669–1699; it imposes no upper cap that
excludes the control.
The schema code is unchanged between the synthetic execution commit and the reviewed
commit. Their producer-file difference only adds task/worker-lifetime binding outside
this schema.

This is a malformed-artifact admission defect, not a plausible elapsed-time measurement.
The contract permits finite numeric inputs and claims consistency of the retained
lifetime; an overflow cannot establish that consistency.
It does not change the fixture’s exact geometric arithmetic or establish that any real
profile was incorrectly accepted.

**Fix:** make `_not_later` reject nonfinite operands before performing either
comparison, or explicitly reject nonfinite cumulative durations at both callers.
Preserve the small finite roundoff allowance.
Add a maintained full real-binder control with finite input values whose phase total
overflows, alongside a valid baseline and the ordinary excessive-duration refusal.
The repair remains within F6b and needs no new schema, dependency, or arbitrary maximum
lifetime.

## Mathematical and Operational Assessment

For finite arithmetic, the new schedule recurrence gives a sufficient and necessary
feasibility check for the recorded sequential durations and task spans, apart from its
stated roundoff tolerance.
Let a phase have duration `d`, previous earliest completion `e`, and observed task span
`[a, b]`. Its start must be at least `e`, at least `b - d`, and at most `a`. Therefore
`s = max(e, b - d)` is its earliest feasible start; refusing when `s > a` detects an
impossible phase, and carrying `s + d` forward preserves the strongest earliest bound.
A phase without task observations needs only the predecessor bound.
Ending this recurrence within the worker lifetime provides one possible schedule; any
actual schedule must end at least that late.

This handles more than separate lower and upper route-position bounds.
The supplemental control shifts raw tasks later by `0.5` seconds and exact tasks later
by `0.2` seconds.
Raw observations still finish before exact observations, and both spans
fit their individual durations, but normalization cannot fit between them.
The reader refuses. Shifting exact by `0.4` seconds instead provides a feasible schedule
and receives acceptance.
All six maintained phase-position controls also pass, including the preflight,
preceding-phase, and final-tail equality boundaries.

The F6a checks preserve the producer’s overlaps.
Source loading is nested inside preflight.
Parent launch may overlap worker execution; its duration need only finish before the
parent’s exit observation.
Cleanup comprises the first process-group cleanup after worker exit and a second cleanup
already inside parent final readback.
Adding launch to worker durations, or adding all cleanup to parent readback, would
reject allowed observations.
A supplemental control simultaneously sets launch to `1.05`, cleanup to `0.15`, and
parent final readback to `0.15`, with worker exit `1.05` and external lifetime `1.2`; it
passes. The one-ULP nested-bound control passes, while the 32-ULP violation refuses.

F6c closes the retained two-process cycle.
Each route child has the coordinator as its parent, so it cannot also be that
coordinator’s live parent.
The guards apply to tasks and reconstructed child records, and the coordinator’s
identity still binds to both sidecars and supervision.
They do not establish the truth of recorded operating-system identities or the ancestry
of unobserved processes.

F7 checks the exact object type before loading the execution source closure.
A 40-character tree ID no longer gains admission merely because `ls-tree` and `show` can
read the same source bytes through it.
The existing exact-reader HEAD, entry-file, and byte checks continue to apply.
No broader redesign is needed for these obligations; the earliest-bound method is small
and matches the necessary schedule constraints.
R1 can be fixed in the shared comparison without changing that design.

## Validation and Retained Artifacts

The completed focused selection ran with **CPython 3.14.7** from
`/Users/levy/.codex/worktrees/88e2/squares/packing/.venv/bin/python3`. The isolated
checkout has no virtual environment, so its `packing` and `packing/src` directories were
placed first on `PYTHONPATH`; the imported reader path was verified to be inside the
isolated checkout. Bytecode and pytest cache writes were disabled.

From the isolated checkout’s `packing/` directory:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/private/tmp/squares-n11-reader-f6f7-7e4d/packing:/private/tmp/squares-n11-reader-f6f7-7e4d/packing/src \
/Users/levy/.codex/worktrees/88e2/squares/packing/.venv/bin/python3 \
  -m pytest -q -p no:cacheprovider \
  --basetemp /private/tmp/bc329-reader-f6f7-review-pytest \
  -k 'not running_reader_origin_and_cli_copy_refusal' \
  --durations=20 \
  --junitxml=/private/tmp/bc329-reader-f6f7-review-pytest.xml \
  tests/test_read_fixed_core_calibration_profile.py
```

Result: **109 passed, one deselected in 244.03 seconds**. The deselected origin-binding
test deliberately writes and restores the repository reader.
It was excluded before execution to honor this review’s no-source-write scope.
Its preexisting F2 evidence remains in the prior report; this selection supplies no new
execution evidence for that test.
The new F6/F7 controls are included and use the real binder.

The independent script ran **15 full real-binder controls**. Fourteen produced their
expected outcomes; the finite phase-overflow control unexpectedly returned acceptance.
It checks exact source identity, creates a fresh synthetic profile, refuses reused work
paths, rebuilds affected receipt bindings, restores the baseline, and records each
outcome and duration.
It exits 1 because of the observed admission defect.

Local review artifacts (outside this PR):

- `/private/tmp/bc329-reader-f6f7-independent-controls.py`,
  `/private/tmp/bc329-reader-f6f7-independent-controls.json`, and
  `/private/tmp/bc329-reader-f6f7-independent-controls.log`.
- `/private/tmp/bc329-reader-f6f7-producer-schema-control.py` and
  `/private/tmp/bc329-reader-f6f7-producer-schema-control.json`.
- `/private/tmp/bc329-reader-f6f7-review-pytest.log` and
  `/private/tmp/bc329-reader-f6f7-review-pytest.xml`.
- Restored baseline directory:
  `/private/tmp/bc329-reader-f6f7-independent-controls/synthetic-profile`.

To reproduce the independent controls, use the project interpreter and pass
`--repository` with a disposable checkout at the exact reviewed commit, a new `--work`
directory, and a new `--result` JSON path to the retained script.
The original checkout has advanced, so the script now correctly refuses it until the
requested old source identity is available in another checkout.
The producer schema script calls only the schema validator against a copied receipt in
memory.
No repository source, bead, PR, or research registry was edited by this reviewer.

## Transfer to PR 156 and Remaining Checks

There is **no aggregate acceptance to transfer** to a cherry-picked PR 156 head.
Cherry-picking identical reader and test blobs transfers R1 as well.
The positive F6a, F6c, and F7 source-review conclusions, and the finite-arithmetic F6b
reasoning, remain reusable if the complete reader/test blobs and relevant runtime
assumptions match. Git commit identity alone is insufficient when cherry-picking changes
the parent and resulting commit ID.

After fixing R1, freeze the integrated reader commit and recheck its exact diff and blob
identities. Full acceptance requires the following remaining evidence:

1. A maintained full real-binder finite-overflow refusal, the accepted baseline, and
   retained F6/F7 violation and equality controls on the final integrated source.
2. Real binder readbacks naming the integrated reader HEAD and the separately frozen
   expected execution commit, with its complete Git-derived source manifest.
   A passing readback with the old reader-commit argument cannot certify the new HEAD.
3. Origin/changed-byte binding controls in a disposable checkout where their intentional
   write/restore is permitted, with restored source identity verified afterward.
4. The applicable change-reachable and PR checks, followed by the project’s final full
   checkpoint on matching source and base.
   This bounded review did not run or certify the full project gate.
5. An updated admission disposition naming `think-px86` and its evidence before any
   positive calibration execution.
   The current report grants no permission to run the three-profile calibration or BC329
   target.

The reader’s accepted baseline reconstructs synthetic rows and recorded metadata.
It does not prove kernel execution, exhaustively fuzz all parser inputs, verify live
host observations, or certify a later source revision.
Documentation should retain the refusal and its tracked remedy in the owning
review/admission record; this repair does not require a change to the mathematical
claims or the reader-facing tutorial.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
