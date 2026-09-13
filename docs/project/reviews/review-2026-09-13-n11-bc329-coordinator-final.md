# BC329 Coordinator and Producer Exact-Head Review

**Verdict: REFUSE strict receipt admission at
`dbbf8495082137e4b26a8531ff21e14d2cce5678`.** The three findings in
[prior coordinator rereview](review-2026-09-13-n11-bc329-coordinator-rereview.md) have
effective repairs on the synthetic paths tested here.
A separate finite-input overflow admits a nonfinite invocation deadline, and another
overflow escapes controlled phase refusal.
No positive calibration or BC329 target run was performed.

The review scope is the committed producer, coordinator, and two focused test modules.
Their exact blobs at `dbbf8495` are:

| Path | Git blob |
| --- | --- |
| `packing/devtools/calibrate_fixed_core_packet.py` | `43047250e53f85a7105ffde5e16f2882553d2e42` |
| `packing/devtools/run_fixed_core_calibration_profiles.py` | `b53ff8216a1fc2bde8fa0d0c5c24e77affab8b48` |
| `packing/tests/test_fixed_core_packet_calibration.py` | `d889e8004c3455e97d167d06fa21fb8f9817673e` |
| `packing/tests/test_fixed_core_calibration_profiles.py` | `4844dc07bacf072e4cd632855a6ae73f0bd5def7` |

The shared JSON reader used by the producer is `packing/devtools/fixed_core_packet.py`
at blob `baaeace549c917bd541f4bf88f7c38d2dba14ef3`. During report preparation, checkout
HEAD advanced through `2ea7740521584b3a088f0954bf12ba7d01834726` to
`5a890a1b864386c53a30a72896e6ae9a28e705b9`; all five listed blobs remained identical.
Source and test files were not edited.

## Findings

1. **High — Derived infinite deadlines pass finite-input identity checks.** The
   coordinator’s strict JSON reader rejects the literal `Infinity` via `parse_constant`,
   but Python parses the valid JSON numeral `1e999` as `float('inf')`
   (`run_fixed_core_calibration_profiles.py:160-168`). The identity check compares
   retained deadline fields directly to `origin + allowance` without checking the
   deadlines’ finiteness (`:770-771`; repeated in `_validate_profile_identity` at
   `:1622-1623`). Two finite inputs can make that sum infinite.
   In a complete, count- and digest-consistent synthetic profile, I set
   `monotonic_origin=1e308`, `calibration_seconds=1e308`, and
   `external_seconds=1.1e308`; both retained deadline fields were JSON numerals `1e999`.
   The real `inventory_profile` accepted the profile and returned a receipt binding.
   A terminal producer document with the same finite origin and allowances also passed
   `validate_document` with both expected identity deadlines equal to infinity;
   `_invocation_identity` creates those expected values at
   `calibrate_fixed_core_packet.py:898-899`, and `validate_document` compares the
   identity to that derived object at `:1697-1705`. This is an admitted malformed
   identity on retained bytes, even though a normal bounded calibration cannot generate
   these values. **Fix:** Require each retained and derived deadline to be finite before
   equality comparison, and reject exponent-overflow numerals at the JSON boundary or
   validate all numeric identity fields after parsing.
   Add the finite-input, exponent-overflow receipt as a refusal control in both readers.

2. **Medium — Finite phase clocks can escape the controlled refusal path.** Both new
   helpers validate each phase as finite and then call `math.fsum` without handling its
   `OverflowError` (`calibrate_fixed_core_packet.py:1058-1066`;
   `run_fixed_core_calibration_profiles.py:208-220`). In synthetic terminal documents
   with `preflight_seconds=1e308` and `exact_seconds=1e308`, the producer’s
   `validate_document` and the coordinator’s `inventory_profile` raise
   `OverflowError: intermediate overflow in fsum`, rather than their domain errors.
   A synthetic supervised terminal run with those same values re-raised `OverflowError`
   and retained `status=partial`, `phase=operational-failure`, `disposition=incomplete`,
   `error='supervisor interrupted by OverflowError'`; it missed the `metrics-refused`
   branch that catches only `CalibrationError`
   (`calibrate_fixed_core_packet.py:3880-3903`). The coordinator’s outer run and CLI
   handlers likewise omit `OverflowError`
   (`run_fixed_core_calibration_profiles.py:2335-2340,2412-2414`). No successful false
   admission was observed in this case; the defect is an unstructured and misclassified
   refusal. **Fix:** Convert `math.fsum` overflow to the respective domain error, or
   reject a phase as soon as it exceeds remaining worker elapsed.
   Keep the normal rounding boundary intact and add a two-large-finite-phases control.

## Prior-Finding Controls

I ran direct controls through the real private producer validator and public coordinator
inventory on fresh temporary synthetic profiles.
Every sidecar mutation was republished with its matching SHA-256 summary, and every
receipt mutation had its self-referential byte count republished.
The controls did not use the BC329 target.

| Control | Producer | Coordinator |
| --- | --- | --- |
| Coherent raw-then-exact child chronology | Accepted | Accepted |
| All raw and exact task and child times exchanged, with both sidecar digests updated | `CalibrationError: raw tasks finish after normalized exact tasks start` | `ProfileCoordinatorError` with the same reason |
| Coherent terminal phase baseline | Accepted | Accepted |
| `raw_seconds=100.0`, `worker_elapsed_seconds=0.2` producer or `1.0` coordinator | Domain-error refusal for phase durations | Domain-error refusal for phase durations |
| Sum exceeds worker elapsed by `5e-10` | Accepted as roundoff | Accepted as roundoff |
| Sum exceeds worker elapsed by `5e-7` | Domain-error refusal | Domain-error refusal |

For the receipt race, the coordinator’s first read uses `lstat`,
`O_NOFOLLOW | O_NONBLOCK`, and `fstat`
(`run_fixed_core_calibration_profiles.py:245-264`). Replacing `result.json` with a
symlink between `lstat` and `open` produced a domain error from `O_NOFOLLOW`;
substituting a FIFO produced a domain error from `fstat` without blocking.
Replacing it with a symlink or FIFO immediately after the first safe read was refused at
the later artifact-type check (`:905-908`). Replacing it immediately after the first
safe read with a different, valid, same-size regular JSON file was accepted as a
snapshot of the original bytes: the returned `inventory.receipt` and calibration-receipt
artifact had the same original digest and byte count (`:909-917`), while the current
path had a different digest.
A guard that raised on any later `Path.read_bytes(result.json)` did not fire.
This confirms the repaired binding; it does not promise that a mutable path still names
those bytes after inventory returns.

The focused repository tests passed: **18 passed, 115 deselected** from the two named
modules under the project’s Python 3.14 virtual environment.
The temporary probe source is `/private/tmp/bc329-exact-review-probes.py`. The
supervised overflow control also used the test module’s fake process and clock, then
called the real `supervise_worker`.

## Arithmetic Scan and Limits

I searched derived arithmetic in the two reviewed modules, then inspected the clock and
identity admission paths, deadline comparisons, RSS gap and lifetime differences, and
summary headroom calculations.
The new `math.fsum` calls are the only reviewed finite-float arithmetic that raised
`OverflowError`. The origin-plus-allowance calculations instead produce infinity
silently and admit an infinite retained identity as shown above.
External-lifetime-plus-terminal-admission overflowing to infinity leads to a deadline
refusal against a finite allowance.
The inspected nonnegative timestamp differences are bounded by their larger operand, and
artifact-byte totals use arbitrary-precision integers.
This was a targeted arithmetic review, not an audit of every scientific calculation or
JSON field in the repository.
The fake process and small retained profile are not a substitute for a full producer
execution or a positive calibration.

The two findings are scoped to receipt admission and refusal classification.
They do not change the frozen fixture mathematics or establish any outcome for a BC329
run.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
