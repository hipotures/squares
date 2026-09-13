# PR 156 Integrated Source and BC329 Run-Sheet Review

**Verdict: ACCEPT the unchanged component source blobs for this scoped integration
check; REFUSE operational admission and execution from the current run sheet.** The
maintained verifier exists and its focused target-free suite passes, but the sheet never
invokes it. Thus the external reader proofs are not joined to the coordinator, the run
root is not inventoried at coordinator return or checked against retention, and the
complete source closure is not compared with an intended evidence tree or actual
evidence commit. This is a run-sheet wiring failure, not a new code defect found in the
reviewed source. No positive profile or BC329 target was run.

## Exact Boundary

The reviewed local head is clean `fbd915fc3b2fcdbb26d032dd67f43dffc3bec18d`. It advanced
from `e3d74d07e73f555e8c40a749b5474fc0f7f9cd10` only in documentation;
`git diff --name-only e3d74d07..HEAD -- packing/devtools packing/tests` is empty.
The run sheet at this head has Git blob `5d721a896b9c6c5d6eb715cb6945f191b750662a` and
SHA-256 `2ed9e9105e04dbccaef3e541f8b481e549f0e21f96027c099419c0e2c12ef5a7`. Line
references below apply to those bytes.
The live PR 156 head returned by `gh pr view` during review was
`52e4ab65ad4581421a1005a91d3f7d76e802acad`, so the local/remote identity gate is not yet
satisfied.

| Source or test path under `packing/` | Integrated Git blob |
| --- | --- |
| `devtools/calibrate_fixed_core_packet.py` | `b61adebc9167a40059c581e20ce760cf1fe3982f` |
| `devtools/run_fixed_core_calibration_profiles.py` | `2e98fd58e81b266b21c64bfa0109b5a2b056e801` |
| `devtools/read_fixed_core_calibration_profile.py` | `34d48ee0004aad26743d9b5ee9f035f8a8be662a` |
| `devtools/verify_fixed_core_calibration_runset.py` | `cd17583c410043367b1a85707617a68df095f74e` |
| `devtools/fixed_core_packet.py` | `baaeace549c917bd541f4bf88f7c38d2dba14ef3` |
| `tests/test_fixed_core_packet_calibration.py` | `3ddc7e7bac67eab156e7224423e3bc65f5a5ad82` |
| `tests/test_fixed_core_calibration_profiles.py` | `10e897d9702a42e6208910494a5c98732541bdcc` |
| `tests/test_read_fixed_core_calibration_profile.py` | `627df45c383dfecf1c37cb5839ea3495663fdff1` |
| `tests/test_verify_fixed_core_calibration_runset.py` | `5fd914cbd58bcd6cec38e63aae2e6191862817d1` |

These are the blobs accepted in the final reader F6/F7 review (`a5701e73`), coordinator
arithmetic review (`775c71d5`), and verifier R3 review (`2ea77405`), as applicable.
The earlier coordinator-final review’s `dbbf8495` REFUSE is superseded only for its two
repaired arithmetic findings.
The component reports are scoped synthetic-code verdicts.
They do not themselves admit this integrated execution head or a positive run.

## What Was Checked

- Concatenated Bash fences from the current sheet pass `bash -n`. The coordinator and
  reader literal flags at lines 169–184 and 213–255 match their Python 3.14 CLIs.
  The maintained verifier advertises `snapshot`, `read`, `join`, `retain`, and
  `source-closure`, with the flags in the verifier contract.
- The frozen command is exactly `4 / 5400 / 7200 / 2` at lines 173–176. The
  producer/coordinator route count is `2881 + 2881 + 5761 + 2881 = 14,404` direction
  rows per profile; dense/slab use the same normalized-exact rows.
  The fixture is 935 bytes and its measured SHA-256 equals the sheet’s
  `1aface38ab79526397b7b9f24325df844e2eb9717d3e29a094fcdefe8822f539`.
- The coordinator writer and verifier whitelist agree on 22 successful top-level
  run-root files: one summary, three run records, and 18 stdout/stderr logs for
  calibration, producer readback, and inventory readback.
  The verifier’s retention whitelist has 19 review-root files: five host/coordinator
  records, inventory and admission, and four reader records per profile.
- The integrated verifier test module passes `15/15` in 8.24 seconds using
  `packing/.venv/bin/python3` 3.14.7, `PYTHONDONTWRITEBYTECODE=1`, disabled pytest
  cache, and a temporary basetemp.
  Its controls are synthetic and target-free.
  This review did not rerun the longer producer/coordinator and full reader suites or
  the repository validation tiers; their exact-blob results are recorded in the named
  component reviews.

## Findings and Minimum Wiring

1. **Blocker — R2/R3 admission commands are absent** (`run sheet:188–189, 206–264`). A
   successful coordinator command only checks for a nonempty summary.
   The sheet directly invokes `devtools.read_fixed_core_calibration_profile` three
   times. It never calls verifier `snapshot`, so there is no first post-return byte/type
   baseline. It never calls verifier `read`, so no
   `profile-N-source-distinct.command.json` is retained, and root equality is not
   checked around each child.
   It never calls `join`, so three zero exits are not proof of matching reader
   revisions, argv, typed invocation identity, receipt byte counts and digests, and
   coordinator summary.
   **Fix:** Immediately after the successful coordinator status test, invoke
   `python -m devtools.verify_fixed_core_calibration_runset snapshot --run-root "$RUN_ROOT" --review-root "$REVIEW_ROOT" --expect-execution-revision "$EXECUTION_REV"`.
   Set `READER_REV="$EXECUTION_REV"`; replace each direct reader block with maintained
   `read --repository "$REPOSITORY" --run-root "$RUN_ROOT" --review-root "$REVIEW_ROOT" --expect-execution-revision "$EXECUTION_REV" --expect-reader-revision "$READER_REV" --run-order N`,
   testing each exit before launching the next.
   Then invoke `join` with the same roots and revisions.
   Require `run-root-inventory.json`, all three four-file reader sets, and
   `run-set-reader-admission.json` under `REVIEW_ROOT`. Keep any verifier CLI console
   redirection outside that root, since its whitelist is exact.
   Refuse and retain the external roots on any nonzero command.

2. **Blocker — retention bypasses the maintained archive comparison**
   (`run sheet:330–379`). The sheet creates `EVIDENCE_ROOT`, copies 14 review files,
   tars the current run root, and hashes that tar.
   The verifier requires a fresh nonexistent evidence root; it will reject this
   pre-created directory.
   The manual list also omits `run-root-inventory.json`,
   `run-set-reader-admission.json`, and the three
   `profile-N-source-distinct.command.json` files.
   The archive hash alone does not bind tar members to the coordinator-return baseline.
   **Fix:** Set the evidence path but do not create it; after `join`, invoke verifier
   `retain --run-root "$RUN_ROOT" --review-root "$REVIEW_ROOT" --evidence-root "$EVIDENCE_ROOT" --expect-execution-revision "$EXECUTION_REV"`.
   The maintained command copies all 19 review artifacts, the summary and revisions,
   creates the archive, checks every archived member against the inventory, rereads the
   archive digest, and refuses changed source or copied bytes.
   Remove the manual `find`/`cp`/`tar`/`shasum` publication block.

3. **Blocker — full source closure and evidence-commit identity are not executed**
   (`run sheet:375–385`). The three-path `git diff` misses packet helpers, package
   initializers, fixture, Python version, `pyproject.toml`, lockfile, and any newly
   imported local module.
   The text says to record two revisions but names no command that checks the intended
   staged tree and subsequent evidence commit.
   **Fix:** After `retain` and after all intended evidence/status files are staged,
   obtain `TREE_OID="$(git -C "$REPOSITORY" write-tree)"`; invoke verifier
   `source-closure --repository "$REPOSITORY" --run-root "$RUN_ROOT" --review-root "$REVIEW_ROOT" --expect-execution-revision "$EXECUTION_REV" --candidate-tree "$TREE_OID"`.
   Require accepted JSON and retain its stdout outside `REVIEW_ROOT`. This command
   requires all three receipt manifests to agree, reconstructs the complete import
   closure from `EXECUTION_REV`, and compares regular-file modes, Git blobs, SHA-256 and
   working bytes with the staged tree.
   After the evidence commit, set
   `EVIDENCE_COMMIT="$(git -C "$REPOSITORY" rev-parse HEAD)"` and rerun the same command
   with `--candidate-tree "$EVIDENCE_COMMIT"`; record the actual commit OID and accepted
   output. The postcommit invocation is necessary to bind the published evidence
   revision, and it requires the index to match that commit tree.
   Keep both closure outputs with external originals or retain their hashes in the
   disposition as the verifier contract requires.

No additional source defect was established.
The verifier’s exact 22-file root, 19-file review set, proof join, archive comparison,
and staged/committed source closure are available at the pinned blobs; the current sheet
simply does not call them.
Source acceptance and operational admission remain separate.

## Disposition

The sheet’s admission table correctly leaves its own review and remote identity pending.
Do not run the coordinator until a revised sheet, all implementation gates, and the
exact common clean live PR head are independently accepted.
A later positive three-profile result must still pass every readback, join, retention,
closure, host, and refusal gate.
Only after the evidence commit is pushed, hosted CI passes, and `think-1mma` records
admission may `think-17qa` register a BC329 scientific target.
Nothing in this review establishes a new mathematical claim or a BC329 performance
estimate.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
