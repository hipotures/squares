# BC329 Run-Set Verifier: Independent Exact-Head R3 Review

**Verdict: ACCEPT the R3 verifier repair at PR 156 head
`e3d74d07e73f555e8c40a749b5474fc0f7f9cd10` (September 13, 2026).** The repaired snapshot
accepts the coordinator’s successful 22-file top-level output set, and the retained
status remains bound to `0\n` across the tested check, digest, copy, and final
verification boundaries.
No new blocker was found in the reviewed verifier or focused tests.
This is acceptance of the target-free evidence-plumbing code, not a calibration result
or operational admission of a future run.

## Review Boundary and Exact Objects

The workflow entry point was an independent, read-only review of the R3 repair and its
interaction with the prior R2 and R4 fixes.
The reviewed verifier and test files are unchanged from repair commit `2ea77405`; their
Git blobs at the final observed PR head are respectively
`cd17583c410043367b1a85707617a68df095f74e` and
`5fd914cbd58bcd6cec38e63aae2e6191862817d1`. Working-file `git hash-object` matched both
objects. The head advanced from `5a890a1b` while other agents updated documentation; the
two reviewed source blobs did not change.
No shared source, documentation, bead, PR, positive profile, or BC329 target was changed
by this review.

The comparator was the coordinator’s actual command-output writer,
`packing/devtools/run_fixed_core_calibration_profiles.py:996-1005`, and its three
successful call sites per profile: calibration, producer readback, and inventory
readback. The verifier’s exact whitelist at
`packing/devtools/verify_fixed_core_calibration_runset.py:38-49` matches those nine
stdout/stderr pairs, three run records, and one summary.
The top-level inventory check at lines 429-440 requires equality, so it also rejects
additions and omissions.

Python was the repository’s `packing/.venv/bin/python3` (3.14.7). The focused suite ran
without bytecode or pytest cache writes: **15 passed in 4.27 seconds**. Independent
controls ran in synthetic, target-free directories under `/private/tmp` and used the
coordinator’s writer with synthetic zero-status `CompletedProcess` values.
The fixture deliberately used placeholder profile run-record content and synthetic
reader proofs; it tested the verifier’s output-set, join, retention, and source-closure
boundaries, not the coordinator’s scientific or receipt validators.

## Independent Control Results

| Boundary | Observation |
| --- | --- |
| Valid coordinator-shaped root | Snapshot accepted exactly 22 top-level files. Three synthetic readers joined to one admission. Retention accepted; all 19 whitelisted review artifacts were copied byte-for-byte, and all 28 archived file bytes and SHA-256 digests matched the first inventory. |
| Missing or extra coordinator output | Removing `profile-2-run.json` or `profile-2-inventory-readback.stderr.log`, adding `profile-4-run.json`, or adding `unexpected.log` each refused with `run root top-level files differ from the coordinator output set`. |
| Missing or extra reader record | Removing profile 2’s stdout proof or adding a profile 4 stdout proof each refused at the reader-record set check before admission. |
| N2 status after first check | Changing source `coordinator.status` from `0\n` to `2\n` after the first status read and before digest capture refused before evidence-root creation: `coordinator status changed before retention copy`. |
| N2 status after digest | Changing source status immediately after its digest read and before copying refused: `review artifact changed during retention: coordinator.status`. |
| N2 status at final boundary | Changing either copied or source status after the archive digest file was published refused: `coordinator status changed during retention`. |

The status controls exercise the three new semantic bindings at verifier lines 861-868
and 928-933, plus the existing per-artifact digest check at lines 872-876. The final
source/copy digest comparison at lines 902-907 and the copied admission reconstruction
at lines 910-918 also keep the retained proof and admission joined.
These are deterministic boundary injections, not a claim of atomic filesystem isolation
against a continuously adversarial writer.

## Original Six Findings Rechecked

| Earlier finding | Independent result at the reviewed blobs |
| --- | --- |
| F1: shared-invalid identity | `requested_workers: true` in the summary refused at snapshot. A separately resealed proof carrying `true` against a valid summary refused at join. The type validation is in `_identity` (verifier lines 167-189) and is applied to both records. |
| F2: fourth run record | A fourth top-level run record refused at snapshot, as did an unknown log. The valid 22-file root passed with the actual coordinator writer. |
| F3: stale candidate tree | A temporary Git repository with nine manifest paths accepted its unchanged staged tree. After staging a modified helper and restoring its working bytes, supplying the old tree or old commit refused because the candidate differed from `git write-tree`; supplying the modified staged tree refused on the helper blob. The index binding is at verifier lines 1058-1070. |
| F4: changed proof during copy | Changing the source profile 1 stdout proof immediately after admission copy refused at the next per-artifact digest check. The retained copy was not accepted. |
| F5: changed coordinator status before retain | Changing the review-root status to `2\n` before retention refused. The additional N2 injections above cover the narrower later seams. |
| F6: oversized JSON integer | A resealed 5,000-digit integer proof passed to `main(join ...)` returned exit 2, emitted `REFUSED: reader 1 proof is not one UTF-8 JSON object`, and created no admission record. |

The focused suite also covers the broader proof, inventory, archive, and source-closure
mutations listed in `packing/tests/test_verify_fixed_core_calibration_runset.py`. The
independent controls above were written separately from those tests, while using the
same public verifier entry points and the production coordinator log writer.

## Disposition and Limits

**R2:** The original join and copy-boundary failures now refuse in the synthetic
controls. The verifier checks exact reader argv, exit status, stream bindings, proof
identity, receipt bytes, and copied admission; accepting the reader’s scientific
implementation remains a separate review gate.

**R3:** ACCEPT this repair.
The producer/verifier top-level output-set mismatch from the `0874e912` rereview is
closed. Both previously reported status check/copy races refuse under deterministic
injections. Run-root bytes are inventoried before readers and compared through archive,
reread, and retention.
The verifier’s own contract acknowledges that scans cannot prove a writer did not
briefly change and restore bytes between observations.

**R4:** The precommit source-closure control accepts an unchanged staged tree and
rejects a stale supplied OID even when working source bytes were restored.
This review did not create an evidence commit or check its actual OID; that later check
remains required by the maintained contract.
The independent source fixture covered a nine-path local import closure; it did not
execute a calibration profile.

The review does not attest full edit/push/fast or session-close validation tiers, actual
coordinator/reader output from a positive run, scientific acceptance, host-load
conditions, an evidence commit, or a later PR head if either reviewed blob changes.
The run sheet and separate integrated-head reviews must discharge those operational
gates before any positive calibration.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
