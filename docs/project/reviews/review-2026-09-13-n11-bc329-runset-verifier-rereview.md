# BC329 Run-Set Verifier: Exact-Head Rereview

**Disposition: REFUSE integrated admission at `0874e912e6282c8b6f09f838a6f0e5a267e19533`
(September 13, 2026).**

This review covers the verifier and focused-test changes from `878e18d0` to `0874e912`,
plus read-only inspection of the coordinator output contract.
The [prior exact-head refusal](review-2026-09-13-n11-bc329-runset-verifier.md) recorded
six defects. All mutation roots in this rereview were temporary and synthetic; no
positive calibration profile or BC329 target ran.
Findings N1 and N2 are tracked as `think-q6by` and `think-eepr`.

## Verdict

Overall: REFUSE integrated operational admission at 0874e912. R2: Targeted verifier
repair ACCEPT at the synthetic join/proof boundary (F1 and F4 controls now refuse).
Operational R2 admission remains REFUSE because the required R3 snapshot rejects a
correctly shaped coordinator root before any reader can run.
The scientific reader’s separate review remains an independent gate.
R3: REFUSE. New critical producer/verifier output-set mismatch blocks every successful
real coordinator root.
A second avoidable coordinator.status check/copy race still permits retention of a
nonzero status after the first status check.
R4: Targeted precommit repair ACCEPT for the static staged-helper/restored-working-file
mutation (F3 now refuses).
Full operational R4 admission remains REFUSE pending the integrated R3 gate and the
later actual evidence-commit OID check; this review did not create an evidence commit.

## Exact Objects and Validation

At the reviewed head, verifier Git blob feb3fac71df9e6accac4e29d764007f035d50482 and
focused-test blob a13ed76b2860e440a6de62309b3111c957b7034a. Both working-file git
hash-object results matched those blobs, and both also matched isolated repair commit
3c1d47f2. Python was packing/.venv/bin/python3 (3.14.7). Focused pytest run, without
cache/bytecode writes: 12 passed in 5.34 seconds.
Independent synthetic positive join and retention returned accepted and copied all
review-whitelist bytes exactly.
That fixture omits the coordinator’s 18 top-level command logs, which is why it is not
an integrated positive control.

## Original Six Findings: Temporary Independent Controls

F1 shared-invalid invocation identity: changed summary requested_workers to JSON true,
removed old inventory, and attempted snapshot.
REFUSED: coordinator invocation identity requested workers must be a positive integer.
Separately resealed a proof with requested_workers true after a valid snapshot/read
sequence; join REFUSED: reader 1 identity requested workers must be a positive integer.
Source: verifier _identity 157-188, summary call 372-374, proof call 667-669. F2 fourth
coordinator run record: added profile-4-run.json before snapshot.
REFUSED: run root top-level files differ from the coordinator output set.
Source: verifier 417-429. F3 staged helper masked by restored worktree: constructed a
temporary Git source repository, staged a changed packing/devtools/helper.py, restored
its working bytes to the execution revision, confirmed git write-tree differs from the
old candidate, then supplied that old tree.
Source-closure REFUSED: candidate tree differs from the current staged index.
Source: verifier 1043-1051. The unchanged candidate tree had accepted immediately before
staging. F4 changed proof at copy boundary: after copying admission, changed only the
source review-root profile-1-source-distinct.stdout.json to ‘{}\n’. Retention REFUSED:
review artifact changed during retention: profile-1-source-distinct.stdout.json.
A second control resealed both proof and command and likewise refused.
Source: verifier 852-905. F5 coordinator.status changed before retention: changed 0\n to
2\n. Retention REFUSED: coordinator status changed after snapshot.
Source: verifier 850-855. F6 oversized JSON integer CLI: resealed first proof as a valid
JSON object with a 5,000-digit integer, called main(join ...). Returned status 2,
emitted ‘REFUSED: reader 1 proof …’ on stderr, and created no admission record.
Source: verifier _json_bytes 215-227 and main 1173-1175.

## N1: Valid Coordinator Output Is Refused (R3)

The coordinator’s
[command-output writer](../../../packing/devtools/run_fixed_core_calibration_profiles.py#L935)
writes `{stem}.stdout.log` and `{stem}.stderr.log` directly in `run_root`. Its three
call sites for each order are the calibration command (lines 2170–2174), producer
readback (2219–2224), and inventory readback (2258–2263). Therefore each of the three
successful runs adds six top-level logs.
The successful root has exactly 22 top-level files under the observed call contract:
three run records, summary, and these 18 logs.
The verifier’s
[inventory check](../../../packing/devtools/verify_fixed_core_calibration_runset.py#L417)
instead requires the top-level set to equal only three run records plus summary.
In a temporary fixture, the reviewer invoked the coordinator’s actual writer with
synthetic zero-status `CompletedProcess` values for all nine call stems and then called
`snapshot_run_root`. It refused:
`run root top-level files differ from the coordinator output set`. The focused positive
fixture creates none of these logs and misses the failure.
Expected top-level file set from the coordinator: profile-1-run.json
profile-1.stdout.log profile-1.stderr.log profile-1-producer-readback.stdout.log
profile-1-producer-readback.stderr.log profile-1-inventory-readback.stdout.log
profile-1-inventory-readback.stderr.log profile-2-run.json profile-2.stdout.log
profile-2.stderr.log profile-2-producer-readback.stdout.log
profile-2-producer-readback.stderr.log profile-2-inventory-readback.stdout.log
profile-2-inventory-readback.stderr.log profile-3-run.json profile-3.stdout.log
profile-3.stderr.log profile-3-producer-readback.stdout.log
profile-3-producer-readback.stderr.log profile-3-inventory-readback.stdout.log
profile-3-inventory-readback.stderr.log three-profile-summary.json Repair needs an exact
producer-derived whitelist including these 18 logs and a positive synthetic root built
with the producer’s command-output writer.
Continue rejecting a fourth run record and unknown top-level artifacts.

## N2: Coordinator Status Check/Copy Race Remains (R3)

At verifier line 850, retain reads coordinator.status and requires 0\n. It then
separately snapshots digests for all review artifacts (852-855). There is no final
semantic check that the copied status is 0\n. A temp-only deterministic injection
changed the source file to 2\n immediately after the first _regular_bytes call returned
0\n and before the digest snapshot.
The digest snapshot and final source/copy digest comparisons all saw 2\n, so
retain_run_root returned status accepted and evidence_root/coordinator.status contained
b'2\n'. This is the same check/copy boundary class as prior F4, applied to the semantic
status invariant. The F5 test only mutates before retain starts.
Bind the snapshot to expected 0\n and verify both current and copied status at the final
boundary; add this mutation control.

Review limits: The analysis establishes the source/test behavior at the named Git
objects. It does not attest a later branch head, real calibration output bytes,
scientific reader acceptance, or the postcommit source-closure check.
Any branch advance requires checking the new exact head before admission.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
