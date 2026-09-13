# BC329 Coordinator Arithmetic Repair: Exact-Head Review

**Verdict: ACCEPT the arithmetic repair at `775c71d5734b118e66d76f670567957af066bfd7`
for strict receipt admission.** The two arithmetic findings in the
[preceding coordinator review](review-2026-09-13-n11-bc329-coordinator-final.md) no
longer reproduce as admission or refusal-classification failures.
I found no new finding in the reviewed arithmetic paths.
This is a verdict on synthetic retained bytes and the focused producer/coordinator
surfaces; it does not establish a positive calibration or a BC329 target result.

The review used commit `775c71d5` as the exact source and test target.
The shared checkout later advanced to a documentation commit, but `git hash-object`
confirmed that the five live Python files used for every probe matched these blobs from
`775c71d5`:

| Path | Git blob |
| --- | --- |
| `packing/devtools/calibrate_fixed_core_packet.py` | `b61adebc9167a40059c581e20ce760cf1fe3982f` |
| `packing/devtools/run_fixed_core_calibration_profiles.py` | `2e98fd58e81b266b21c64bfa0109b5a2b056e801` |
| `packing/devtools/fixed_core_packet.py` | `baaeace549c917bd541f4bf88f7c38d2dba14ef3` |
| `packing/tests/test_fixed_core_packet_calibration.py` | `3ddc7e7bac67eab156e7224423e3bc65f5a5ad82` |
| `packing/tests/test_fixed_core_calibration_profiles.py` | `10e897d9702a42e6208910494a5c98732541bdcc` |

## Arithmetic Admission

**Finite phase-sum overflow.** A synthetic terminal document and a digest-consistent
synthetic coordinator receipt each set `raw_seconds=1e308`, `exact_seconds=1e308`, and
`worker_elapsed_seconds=1e308`. The two phase helpers now catch `math.fsum`’s
`OverflowError` and raise `CalibrationError` or `ProfileCoordinatorError` with
`worker phase durations exceed worker elapsed`
(`calibrate_fixed_core_packet.py:1062-1079`;
`run_fixed_core_calibration_profiles.py:208-232`). Direct calls through
`validate_document` and `inventory_profile` returned those domain errors.
With the producer test module’s fake worker, readback process, and clock, the real
`supervise_worker` returned status code `2` and retained `status=invalid`,
`phase=metrics-refused`, `disposition=calibration-refused`, and
`error='metrics admission refused: worker phase durations exceed worker elapsed'`. It
did not leave a partial operational-failure receipt or propagate a raw `OverflowError`.

**Exponent-overflow deadlines.** I used finite `monotonic_origin=1e308`,
`calibration_seconds=1e308`, and `external_seconds=1.1e308`. Their derived deadlines
overflow to infinity.
Both retained deadline fields were the valid JSON numeral `1e999`, which the production
strict readers parse as positive infinity.
The producer’s terminal `validate_document` refused with
`CalibrationError: derived invocation deadlines are not finite`
(`calibrate_fixed_core_packet.py:879-908,1694-1707`). Its `initial_document` also
refused the overflowing derived deadlines before seeding a receipt.
The coordinator’s real `inventory_profile` refused the complete synthetic profile with
`ProfileCoordinatorError: receipt invocation deadlines are not finite`
(`run_fixed_core_calibration_profiles.py:765-771,867-876`); the separate
`_validate_profile_identity` path refused the parsed retained identity with
`ProfileCoordinatorError: profile invocation deadlines are not finite` (`:1622-1628`).
For the inventory probe, the fake receipt’s self-referential byte count was republished
before each six-byte placeholder was replaced with a six-byte `1e999 ` field value; the
resulting receipt length remained bound to its artifact count.

**Finite boundary.** The producer accepted finite deadlines from `origin=1e308`,
calibration allowance `1e307`, and external allowance `2e307`. Both helpers accepted a
finite phase total of `1e308 + 7e307` against elapsed `1.7e308`. The coordinator’s
complete synthetic receipt with those finite near-limit deadlines was accepted by its
focused test. Existing rounding controls still accepted a `5e-10` excess and refused a
`5e-7` excess in both helpers.
These checks show that the repair does not reject all large finite values or collapse
the declared rounding margin.

## Prior Mutation Controls

The three original admission controls remained effective on fresh temporary synthetic
profiles. Each topology sidecar mutation was republished with its matching SHA-256
summary, and each receipt mutation used the fixture’s self-referential byte-count
publisher.

| Control | Producer | Coordinator |
| --- | --- | --- |
| Coherent raw-before-exact child chronology | Accepted | Accepted |
| All raw/exact task and child times exchanged, sidecar digests updated | `CalibrationError: raw tasks finish after normalized exact tasks start` | `ProfileCoordinatorError` with the same reason |
| Coherent terminal phase baseline | Accepted | Accepted |
| Single raw phase changed to `100.0` beyond worker elapsed | `CalibrationError` for phase durations | `ProfileCoordinatorError` for phase durations |
| Two finite phases summing beyond float range | `CalibrationError` for phase durations | `ProfileCoordinatorError` for phase durations |

For the receipt replacement control, a symlink swapped between `lstat` and open raised
`ProfileCoordinatorError` from the no-follow open; a FIFO at that point raised
`ProfileCoordinatorError` from the regular-file check without blocking.
A symlink or FIFO swapped immediately after the first safe read was refused at the later
artifact-type check.
A different, valid, same-size regular receipt swapped immediately after that read
yielded an inventory bound to the original read bytes: `inventory.receipt` and the
calibration-receipt artifact agreed on their original SHA-256 digest and byte count.
This is snapshot binding, not a claim that the mutable path still held those bytes at
return. A guard against a second `Path.read_bytes(result.json)` did not fire.

## Validation, Design, and Limits

The two complete focused test modules passed under the project’s Python 3.14 virtual
environment: **141 passed**. The narrower arithmetic, chronology, terminal-admission,
and receipt-replacement selection passed **26 tests**. The independent temporary probes
are `/private/tmp/bc329-exact-review-probes.py` and
`/private/tmp/bc329-coordinator-arithmetic-final-probes.py`. No repository source or
test file was edited during this review.

The repair is limited to two domain boundaries: validating a completed phase sum and
validating deadlines derived from finite invocation inputs.
It keeps retained-byte refusal in both the producer and independent coordinator reader,
and the supervised producer publishes the existing `metrics-refused` state.
The reviewed behavior needs no additional interface or documentation change beyond
superseding the prior arithmetic refusal verdict.
The fake worker and small synthetic profile exercise admission logic but do not
substitute for a full producer execution, a positive calibration profile, or a BC329
target run.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
