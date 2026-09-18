---
title: exp-161 — Route S T-025 fixed-support compression to at most 23 orbits
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-161
  series: series-000
  title: Route S T-025 fixed-support compression to at most 23 D4 orbits
  date: '2026-09-18'
  hypotheses: [H-163]
  tier: confirmatory
  subject:
    label: >-
      T-025 exact 119-orbit support universe U025 at L=191/50, B=9977/10000, 181
      directions, closed cores
    engine: >-
      sqpack.fractional.threshold_compression decompressor and
      devtools.compress_threshold_certificate producer; coverage by
      devtools.decide_threshold_certificate
    assurance: verified
    method: exact-algebraic
    host_system: Cloud agent; project Python 3.14; no target has run
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      Frozen T-025 certificate.json at Git revision
      5ce2839f17b2f5a337260dc3f649e05ab974bd25, inventory catalog SHA-256
      8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75, N+=119,
      exact budget 685457679/62500000. T-026 720- and 1440-step certificates are
      provenance sentinels only. Replay the admitted target-blind controls in
      packing/cases/n11_threshold_certificate/route-s-compression-admission-receipt.json
      before any optimizer. Refuse a changed source, catalog, or failed mutation
      control before constructing a candidate.
    candidate: >-
      A D4-symmetric nonnegative rational reweighting of U025 with N+ <= 23 strictly
      positive orbit representatives, produced only by the admitted deterministic
      decompressor from a canonical nonempty selection manifest. Weights may be zero
      by omission; every coordinate, threshold triple, symmetry image, domain
      parameter, and budget coefficient stays fixed. The all-zero family is outside
      the manifest language.
    runs_per_condition: 1
    interleaved: false
    operator: Cursor session-139 Lane C
    entry_point: packing/devtools/compress_threshold_certificate.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.compress_threshold_certificate
      --source cases/n11_threshold_certificate/certificate.json
      --expect-source-revision 5ce2839f17b2f5a337260dc3f649e05ab974bd25
      --expect-catalog-sha256 8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75
      --max-orbits 23 --budget-below 11 --least-charge 1
      --output campaign/series/series-000-smoke-and-calibration/results/agenda-036/exp-161-route-s-threshold-compression.json
    budget: >-
      One overnight target attempt after this registration, wall cap three hours once
      the producer exists. Independent source-distinct replay is inside the cap.
      No second attempt without a new experiment id.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-036/exp-161-route-s-threshold-compression.json
  lease:
    expires: '2026-09-18T13:33:00Z'
    host: cursor
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-163 only at N+ <= 23 with total budget < 11, least charge >= 1 from
      agreeing exact event-cell and interval routes, and source-distinct manifest
      replay; refute only by exact infeasibility of those constraints for every
      N+ <= 23 family member
    reason: >-
      The round is registered and leased; no optimizer, candidate, or coverage route
      has run.
---
# Exp-161: Route S Fixed-Support Compression Target

This is the first scientific round of
[H-163](../../../hypotheses/H-163-route-s-threshold-compression.md).
[X-032](../../../explorations/X-032-route-s-threshold-compression.md) froze the family;
Sessions [134](../../../agent-sessions/session-134-n11-route-s-admission.md) and
[135](../../../agent-sessions/session-135-n11-route-s-guard-discharge.md) admitted the
target-blind instrument; PR 182 merged it as `1d9c49c4` from reviewed head `609d7d62`.
Until this artifact existed, no optimizer, candidate, or coverage target was allowed.

## Source

The control is
[`certificate.json`](../../../../cases/n11_threshold_certificate/certificate.json) at
revision `5ce2839f17b2f5a337260dc3f649e05ab974bd25`. The admitted inventory catalog
SHA-256 is `8de1d9646efef5c49367b679a78ff20961f7f5c1d43b11ff28b5f9a6b41f0e75` (119
orbits, 904 atoms, budget `685457679/62500000`). T-026’s 720- and 1440-step certificates
check support identity and the documented uniform rescaling only.
They are not controls, targets, or a promise that a compressed certificate keeps the
dilation-limit bound.

## Target

Search the frozen U025 reweighting family for one nonempty canonical selection with
`N+ <= 23` that decompresses to a certificate the existing two coverage routes both
accept at least charge one, with exact budget strictly below eleven.
The producer may not move sites, change threshold triples, add atom classes, or change
the net or shrink.

## Accept, stop, refuse

- **Accept H-163** only when all five X-032 confirmation clauses hold, including
  source-distinct replay of the manifest, reconstructed certificate, and both coverage
  routes. Smaller files, simpler denominators, or fewer distinct weights do not meet
  `N+`.
- **Refute H-163** only with an exact infeasibility certificate that no family member
  with `N+ <= 23` meets the frozen budget and coverage constraints.
- **Unresolved** if the timebox expires, the search saturates without a candidate, or a
  coverage route disagrees.
  Park only this frozen family.
- **Invalid / no scientific verdict** if the source, catalog, mutation controls, or
  decompressor fail, or if a candidate is built by any path other than the admitted
  decompressor.

A bounded unsuccessful search is not a negative.

## Independent-review boundary

A source-distinct reader must reconstruct the candidate from its canonical manifest and
re-run both coverage routes without trusting the optimizer’s summary.
The reviewer may not share the producer’s working set.
T-025 and T-026 `verify_claim.py` are not this round’s reader and must not be edited.

## Retained evidence paths

- This experiment artifact.
- Producer receipt:
  `packing/campaign/series/series-000-smoke-and-calibration/results/agenda-036/exp-161-route-s-threshold-compression.json`
- Canonical selection manifest beside that receipt, once one exists.
- Admission receipt already retained at
  `packing/cases/n11_threshold_certificate/route-s-compression-admission-receipt.json`
  (historical: `experiment_created: false` at admission; this round is the later
  allocation).

The named producer `devtools.compress_threshold_certificate` is part of this round and
must exist before the command runs.
Building it is not a target.
Running it is.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
