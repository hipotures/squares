---
title: exp-220 — re-freeze of the exp-219 class certificate under the class claim strings
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-220
  series: series-000
  title: Re-freeze of the exp-219 class certificate under the class claim strings
  date: '2026-09-20'
  hypotheses: [H-222]
  tier: confirmatory
  subject:
    label: >-
      The exp-219 run repeated byte-for-byte in its parameters after the driver and
      the gate were corrected to write and expect a class claim and id under a corner
      clip (review defect D1), so the retained bytes declare what they prove; same
      n=11, side 96/25, B = 9977/10000, the 181 half-tangent folded net, auto grids
      plus a 5-per-window lattice, corner clip d = 1/2
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen --corner-clip 1/2;
      both routes of decide_certificate --corner-clip 1/2, and the same gate without
      the flag as the refusal control; the ceiling readers are not run because exp-219's
      family total 8.94 is below the kill line
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 146; project Python 3.14.7; four CPUs
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      exp-219's retained covering (sha256 5813d822...7040d) at mass 10868617/1000000
      with both routes agreeing at 2000013/2000000; the placements of the new freeze
      are compared with it as exact Fractions
    candidate: >-
      The same covering frozen with a class claim and id. Accept only when
      decide_certificate --corner-clip 1/2 prints RETAINABLE UNDER THE CORNER CLASS
      HYPOTHESIS from both routes on a freeze below 11 and the gate without the flag
      refuses the record naming variant class.
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-146 Opus lane
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 11 --side 96/25 --shrink 9977/10000 --direction-steps 180 --corner-clip 1/2
      --grid-counts auto --seed-windows 5 --support-cap 32 --column-rounds 1
      --max-rounds 60 --deadline-seconds 2400 --scale 4000000 --verify-serial
      --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-covering.json
      --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-family.json
      --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-run.json
      --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-rows.jsonl
      --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class.log
    budget: One run of at most 2400 s, then the gate twice; Session 146 wall.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  effort:
    timebox: 2400 s run, then the gate
    wall_seconds: 262.9
    stopped_by: criterion
  results:
  - shape: determination
    role: outcome
    question: >-
      Does the re-frozen covering carry the class claim and id, print RETAINABLE UNDER
      THE CORNER CLASS HYPOTHESIS from both routes below 11, and refuse without the
      flag?
    outcome: criterion_met
    checked_by: >-
      decide_certificate --corner-clip 1/2 printed "RETAINABLE UNDER THE CORNER CLASS
      HYPOTHESIS (no square meets x + y <= 1/2 in any corner frame): both routes accept
      and agree at 2000013/2000000; sha256
      876820dde8d55c727dec73c85f245db27661556bb3c7aa06ffb15b01ec97a461"; without the
      flag the gate printed "REFUSED: cannot load certificate: variant 'class' is
      declared" and exited 1; the run converged at round 0 in 262.9 s with mass
      10868617/1000000, and all 680 atoms equal exp-219's as exact Fractions in the
      same order, the bytes differing only in id and claim (receipt
      exp-220-n11-96-25-class-receipt.md)
  - shape: record
    role: outcome
    metric: frozen covering mass on the clipped domain (exact rational)
    direction: lower
    score: 10.868617
    standing_best: 10.868617
    standing_best_source: exp-219, the same covering under the unconditional claim string
    beat_record: false
    runs: 1
  verdict:
    decision: accepted
    primary_criterion: >-
      Accept only on RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS from both routes on a
      freeze below 11 with the class claim and id in the bytes, and a refusal naming
      variant class from the gate without the flag; a converged value at or above 11
      refutes this site set only.
    reason: >-
      The same 680-atom covering as exp-219, now frozen with the claim "corner class
      d = 1/2 excluded at s(11) >= 96/25" and the id C-n011-fractional-96-25-clip-1-2;
      both gate routes accept it under the flag and the gate refuses it without the
      flag, so the retained bytes declare what they prove. The corrected gate now
      refuses exp-219's bytes on their unconditional claim string, and exp-220
      supersedes exp-219 as the record of the exclusion; the registration of the
      reviewed statement remains BC-367.
---
# Exp-220: Re-Freeze of the exp-219 Class Certificate Under the Class Claim Strings

The registration review of [exp-219](exp-219-h222-n11-96-25-octagon-class.md) under
[agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-367 found
that the retained bytes carry the claim string of an unconditional certificate, with
only `variant: class` stopping the file from reading as a bound (review defect D1). This
round repeats the run after the driver and the gate were corrected, so the registered
bytes declare what they prove.
The receipt is
[exp-220-n11-96-25-class-receipt.md](../results/agenda-040/exp-220-n11-96-25-class-receipt.md).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
