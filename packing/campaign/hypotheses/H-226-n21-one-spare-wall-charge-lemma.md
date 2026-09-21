---
title: H-226 — the one-spare wall-charge lemma at n=21
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-226
  kind: hypothesis
  claim: >-
    In every packing of 21 boxes (open squares of side above 1) in [0, 5]^2, some
    wall-parallel line at distance sqrt(2) - 1/2 from a wall is charged more than 1
    by five distinct boxes, so s(21) = 5; the proof is Bentz 2016's Theorem 8
    deformation on the 22 red and 23 blue points with one spare red and two spare
    blue points and a finite enumeration of the exceptional structures.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:7', 'proof:6', 'proof:10']
  criterion:
    shape: determination
    metric: >-
      An exact enumeration, by a retained devtools tool, of every assignment of
      stationary and doubly-covered points to the rows of the red and blue
      configurations modulo the dihedral symmetry, reporting for each whether the
      surviving row movements force five boxes charging more than 1 on at least one
      of the four wall lines, with the chord minima of Theorem 11 replayed at the
      printed constants first
    direction: >-
      Confirm when every exceptional structure forces five charging boxes on some
      wall line and each geometric step is replayed exactly. Kill when a structure
      leaves at most four charges on every wall line with no forced partial-box
      point; that names the case that needs new geometry and does not by itself
      produce a packing. A replay of Theorem 11 that fails at the printed constants
      stops the lane and files a defect.
    threshold: 5
  instrument: >-
    A new exact enumeration tool under packing/devtools with the Theorem 11 chord
    replay as its control; cases/bentz13 style exact escape checks for any structure
    that needs a geometric argument
  instrument_ready: true
  regime: >-
    Boxes of side above 1 in [0, 5]^2; red set {0.5..4.5 step 1} x {0.9, 1.7, 2.5,
    3.3, 4.1} and blue set on the interleaved half-integers per Bentz 2016 Figure 3;
    wall lines at sqrt(2) - 1/2 from each wall; exact arithmetic
  instance: {axis: n, point: 21}
  priority: 1
  cost_estimate: >-
    A Fable mathematical lane of two to four hours for the replay and the structure
    inventory, then days of casework if the inventory is large
  prereqs: [think-89i1]
  replication: false
  registered: '2026-09-20'
  notes: >-
    Review R3 found that the archived Bentz 2016 transcription printed the finishing
    line at (sqrt(2) - 1)/2 where the PDF prints sqrt(2) - 1/2; the proof closes
    only with the printed constant (D-505). R3 also corrected lane 3's structure
    count: doubly-covered boxes fix two points, so up to six stationary points and
    about 38 red by 1,200 blue exceptional structures modulo D2 must be handled, and
    a red double merges two of the five boxes. The register lists n=21 as open with
    verified floor 97/20 (T-021). 2026-09-20 Session 144 exp-216: Theorem 11 replays exactly at the printed constants (24 rows); the inventory tool devtools.bentz2016.one_spare_inventory enumerates 42,124 D2 orbits at n=21, and after the reviewer's merge propagation 3,461 are kills (at most four charges on every vertical wall line, no confined partial box) and 22,603 need the claim Q(i, j). Rejected as stated by the Fable review; s(21) = 5 untouched.
---
# H-226: The One-Spare Wall-Charge Lemma at n=21

Lane 3 identified `n = 21` as the integer case one spare point past Bentz 2016’s proved
`n = 22`, and review R3 corrected both the constant the finishing line needs and the
size of the case tree.
This claim is the lemma that would close the case.
Its first output is the exact replay of Theorem 11 at the printed constants; only then
does the enumeration start.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
