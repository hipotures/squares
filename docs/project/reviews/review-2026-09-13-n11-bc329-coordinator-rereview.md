# BC329 Coordinator Exact-Head Review

**Verdict: REFUSE** for observed-topology and receipt admission at commit
fc3e314daaeb1cb07705ce4a44ae682e80eafa6a. The three defects in the
[preceding exact-head review](review-2026-09-13-n11-bc329-topology-coordinator-initial.md)
have direct repairs, but controlled retained-byte probes found three remaining admission
failures. This review covers the committed calibration producer, coordinator, and their
focused tests. Concurrent working-tree changes outside those files were neither reviewed
nor edited.

## Admission Findings

1. **P2 — Cross-route task chronology is not checked.** The producer completes the raw
   route and its checkpoint before starting normalization and then the normalized-exact
   route (packing/devtools/calibrate_fixed_core_packet.py:2218-2233,2323-2332). Producer
   validation checks each route separately at lines 2713-2810; the coordinator also
   reconstructs the sidecars separately at
   packing/devtools/run_fixed_core_calibration_profiles.py:612-660. In a temporary
   synthetic profile, I exchanged all raw and normalized-exact task and child times,
   then republished both sidecars, their digests, and receipt counts.
   Every normalized-exact task finished by 0.5 seconds, while every raw task began at or
   after 0.6 seconds; worker elapsed was 1.0 second.
   Both producer topology validation and coordinator inventory accepted the impossible
   chronology. **Fix:** Once both route records are loaded, require the latest raw task
   finish to be no later than the earliest normalized-exact task start when both routes
   have child tasks. Add a digest-consistent inverted-order mutation control to both
   readers. Serial routes have no child-task times and need no such comparison.

2. **P2 — Sequential phase durations can exceed worker lifetime.** The producer measures
   preflight, raw, normalization publication, exact, interval, dilation, and full
   readback in sequence, then sets worker elapsed from the same invocation origin
   (packing/devtools/calibrate_fixed_core_packet.py:2113-2139,2227,2257,2332,2399,2468,4082,4153).
   The receipt parser checks these clocks only for finite nonnegative values (lines
   1674-1696); the coordinator does the same at
   packing/devtools/run_fixed_core_calibration_profiles.py:760-768. Changing only
   raw_seconds to 100.0 in a synthetic terminal receipt with worker_elapsed_seconds of
   1.0, then republishing its byte count, still made inventory_profile return an
   accepted inventory. The summary publishes the impossible phase observation.
   **Fix:** At terminal producer admission and independent inventory, require the sum of
   those disjoint worker phases to fit within worker elapsed, allowing only a small
   floating-point rounding tolerance.
   Do not add source_loading_seconds, which is inside preflight.
   Give the test fixture coherent baseline clocks and add single-phase and
   combined-duration refusal controls.

3. **P2 — Inventory reopens result.json without the safe reader.** The new preflight at
   packing/devtools/run_fixed_core_calibration_profiles.py:815-817 uses lstat,
   O_NOFOLLOW, O_NONBLOCK, and fstat.
   Later, the calibration-receipt artifact row calls _artifact_row, which calls
   Path.read_bytes directly (lines 257-265, 861-869). Replacing result.json with a
   symlink immediately before that second read produced an accepted inventory whose
   result.json was a symlink at return.
   Replacing it with a different same-size regular JSON receipt produced an accepted
   inventory where inventory.receipt.sha256 differed from the calibration-receipt
   artifact sha256. A FIFO at the second open could block.
   **Fix:** Build the calibration-receipt artifact row from the already checked
   receipt_bytes; bind its digest and byte count to inventory.receipt.
   Keep nonblocking, no-follow behavior for any remaining read of that path and add a
   controlled replacement-between-reads test.

## Confirmed Repairs

- The producer requests four effective generic workers on Linux, and the coordinator now
  derives that shape from the retained platform string
  (packing/devtools/calibrate_fixed_core_packet.py:834-841;
  packing/devtools/run_fixed_core_calibration_profiles.py:240-247,683-700). The Linux
  four-worker test accepts, then rejects a mismatched dilation count.
  Summary validation admits either platform shape because its standalone form does not
  carry platform; publication with a run root reconstructs from the retained profile
  records.
- Both producer and coordinator now reject child task finishes after retained worker
  elapsed (packing/devtools/calibrate_fixed_core_packet.py:2605-2612;
  packing/devtools/run_fixed_core_calibration_profiles.py:452-467). The
  digest-consistent shifted-task tests pass.
- Direct temporary probes confirmed an initial result.json symlink and FIFO are refused
  before read. The coordinator uses the safe reader immediately after the calibration
  subprocess returns (lines 2174-2184).

## Validation and Limits

The coordinator test module passed 36 tests.
The producer topology, supervision, and RSS selection passed 11 tests, with 74
deselected. All probes used temporary synthetic profiles and Python 3.14.7; no positive
calibration profile or BC329 target run was launched.
The tests’ fake producer readback is not a substitute for a full producer execution; the
remaining chronology and clock findings are supported by the named producer validation
paths and independent inventory probes.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
