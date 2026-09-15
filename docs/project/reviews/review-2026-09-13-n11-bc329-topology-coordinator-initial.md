# BC329 Topology Coordinator Exact-Head Review

**Verdict: REFUSE** for topology-coordinator admission at exact stack HEAD
`212e0dfc9f7b2e48743cb84ea21b3803822e50b8`. This review covers the producer’s
worker-topology and supervision contract in
`packing/devtools/calibrate_fixed_core_packet.py`, the coordinator repair in commit
`0cc0311a48e813a2d72029c51e349793cc7df514`, and their matching focused tests.
The working tree contained concurrent documentation edits; none were part of this review
or changed by it.

## Findings

1. **P1 — Linux profiles with two to four requested workers cannot pass the
   coordinator.** The producer derives `reflected_interval` and `dilation` effective
   workers from the requested count on Linux (`calibrate_fixed_core_packet.py:834-840`).
   The coordinator requires both counts to equal one in `_validate_inventory_receipt()`
   (`run_fixed_core_calibration_profiles.py:645-659`) and again in `validate_summary()`
   (`run_fixed_core_calibration_profiles.py:1855-1868`). Thus a successful Linux
   producer receipt with `--workers 4` is refused before inventory reconstruction, and a
   corresponding summary cannot validate.
   The coordinator test fixture fixes these two counts at one for four requested workers
   (`test_fixed_core_calibration_profiles.py:265-276`), so its green tests do not
   exercise the producer’s Linux shape.
   Derive the expected counts from the retained execution platform and requested count
   in both coordinator checks; add Linux four-worker acceptance and mismatched-count
   refusal controls. A small synthetic receipt with the producer’s Linux count of four
   was refused as a worker-settings mismatch.

2. **P2 — Coherently false task times can be admitted as observed topology.** The
   producer writes task and child times relative to the invocation’s monotonic origin
   (`calibrate_fixed_core_packet.py:1413-1435`), but both the producer validator
   (`calibrate_fixed_core_packet.py:2677-2699`) and coordinator reconstruction
   (`run_fixed_core_calibration_profiles.py:367-541`) check only local nonnegativity,
   order, overlap, and child reductions.
   Neither binds the final task time to the retained `clocks.worker_elapsed_seconds`. In
   a synthetic retained profile, shifting every raw task and child time by 100 seconds,
   updating the sidecar digest and artifact inventory, still made `inventory_profile()`
   return an accepted inventory with a last task at 100.5 seconds and
   `worker_elapsed_seconds` at 1.0 second.
   Reject task finishes after worker elapsed time, and test a coherent time-and-digest
   mutation. The raw and normalized-exact routes are sequential in the producer, so their
   cross-route order can also be checked when both have task observations.

3. **P2 — The inventory reader opens `result.json` before checking that it is a regular
   file.** `inventory_profile()` checks exact top-level names, then calls `read_bytes()`
   at `run_fixed_core_calibration_profiles.py:774-776`; its symlink/file check is
   deferred to lines 823-829 after row reading.
   The coordinator also opens the result directly after its subprocess returns (line
   2128). A `result.json` FIFO can block readback, and a link is followed before
   eventual refusal. Preflight file types with `lstat` before any content read in the
   public inventory and coordinator paths, with link and nonregular-file refusal
   controls.

## Contract Checks That Held

The repair requires the six-field successful supervision object, including a positive
coordinator PID and equal process-group ID. It binds that identity to the topology
summary and both sidecars, requires both sidecars in the exact ten-artifact set, and
checks their byte digests and receipt counts.
For each parallel route, it checks one task per expected direction, positive child IDs,
matching task `ppid` and `pgid`, nonoverlap per child, exact child summaries, and an
independently recomputed maximum simultaneous-child count.
Serial routes correctly require no child tasks.
The coordinator calls strict producer readback before admitting its separate inventory;
CPU and RSS claims remain scoped to the producer’s observations rather than inferred
from configured worker counts.
Positive `ppid` and agreement across retained records do not by themselves prove the
historical OS parent; the receipt presents them as observations.

## Validation and Limits

- `test_fixed_core_calibration_profiles.py`: 30 passed
- `test_fixed_core_packet_calibration.py -k 'topology or supervision or rss'`: 10
  passed, 74 deselected
- Two temporary synthetic readback probes reproduced findings 1 and 2 without launching
  a calibration profile

No positive calibration profile or BC329 target run was performed.
This report is a source and synthetic-retained-byte review of the named exact HEAD, not
a measurement of runtime throughput, CPU, or RSS.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
