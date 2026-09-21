---
title: agenda-040 — overnight lower-bound loop after X-040
softschema:
  contract: packing.squares:ExperimentAgenda/v1
  schema: ../schemas/agenda.schema.yaml
  envelope: agenda
  status: enforced
agenda:
  id: agenda-040
  title: Overnight Lower-Bound Loop After X-040
  updated: '2026-09-20'
  status: active
  objective: >-
    Run the hypotheses X-040 adapted from the Session 143 review as an overnight loop
    of about eight hours in one- to two-hour chunks, each chunk a fresh session record
    and a stacked pull request on the previous head. Stock-instrument determinations
    at n=13, n=17, and n=26 run first; the n=21 and n=32 one-spare lemma runs as a
    mathematical lane beside them; the n=11 octagon class follows once its convex
    domain predicate is admitted; the tilted-anchor, wedge-conflict, and unshrunk
    n=12 items stay blocked on instruments. Mathematics is delegated to Fable and
    mechanical work to Opus, with a Fable review of every chunk.
  items:
  - id: BC-361
    purpose: research
    owner_focus: insight
    instances: [13, 17, 26]
    state: ready
    priority: 0
    question: >-
      What do the stock column-generation and ceiling-family instruments decide at
      n=13 (399/100), n=17 (23/5), and n=26 (53/10): a calibration rung, a ceiling
      family that closes the fixed-shrink point route at n=17, and a first-party
      n=26 floor?
    hypotheses: [H-223, H-224, H-225]
    budget: >-
      Session 144, about two hours of wall on four CPUs: one run each at n=13 and
      n=17 with freeze and freeze-family, one seeded n=26 run with a 3600 s deadline,
      then the gate or the two ceiling readers, each under its own experiment id.
    entry: >-
      X-040 is retained, the hypotheses are registered, and the branch is stacked on
      PR 204's head.
    exit: >-
      Each hypothesis has a decided experiment record or an explicit unresolved
      verdict with its stop reason; any RETAINABLE freeze is registered as a result
      only after both routes agree.
    bead: think-pogj
    depends_on: []
    next_evidence: >-
      exp-213, exp-214, and exp-215 receipts under results/agenda-040.
    workflows: [research-loop]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: overnight-chunk-1
    note: >-
      H-223 is calibration under a proved value. H-224's confirm is a negative about
      the method, not a bound. H-225 is the one item here that can move a floor.
  - id: BC-362
    purpose: research
    owner_focus: insight
    instances: [21, 32]
    state: ready
    priority: 1
    question: >-
      Does Bentz 2016's Theorem 11 replay exactly at the printed constant
      sqrt(2) - 1/2, and does the one-spare wall-charge lemma close n=21 and n=32
      after a finite enumeration of exceptional structures?
    hypotheses: [H-226, H-227]
    budget: >-
      A Fable mathematical lane of two to four hours beside BC-361, building the
      enumeration as a retained devtools tool with the Theorem 11 chord replay as its
      control; casework beyond the inventory is a later chunk.
    entry: >-
      D-505 corrected the transcription and X-040 records review R3's structure
      count.
    exit: >-
      The replay passes or fails at the printed constant, and the exceptional
      structure inventory at n=21 is enumerated with each structure classified as
      forced, needs-geometry, or kill.
    bead: think-89i1
    depends_on: []
    next_evidence: >-
      The replay receipt and the structure inventory under results/agenda-040.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: overnight-math-lane
    note: >-
      n=45 and n=44 were dropped: the m = 7 height budget 6.8925 < 7 blocks the 0.1
      slide.
  - id: BC-363
    purpose: research
    owner_focus: insight
    instances: [11]
    state: ready
    priority: 1
    question: >-
      Is the restricted covering value of the all-free corner class at 96/25,
      d = 1/2, below 11, or does a depth-one family avoiding all four corner
      triangles reach 11 and close every corner-conditioned point route?
    hypotheses: [H-222]
    budget: >-
      Sessions 145 and 146: six to ten hours to admit a convex corner-clip domain
      predicate with an independent reader and a T-023-branch replay control (Opus
      build, Fable review), then runs of about thirty minutes each.
    entry: >-
      BC-361 is closed or running unattended, and the domain predicate is designed.
    exit: >-
      A decided experiment record for H-222 in either direction, or the predicate
      refused by its independent reader with the reason recorded.
    bead: think-ni3v
    depends_on: []
    next_evidence: >-
      The admitted predicate, its controls, and the H-222 experiment receipt.
    workflows: [pipeline-improvement, research-loop]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: overnight-chunk-2
    note: >-
      Review R1 killed the deep branches at the target side; the all-free class is
      the only corner branch with headroom and its kill is decisive for the whole
      corner-conditioned point language at this B.
  - id: BC-364
    purpose: research
    owner_focus: insight
    instances: [11]
    state: blocked
    priority: 2
    question: >-
      Can the tilted-anchor case or a gap-g wedge conflict edge cut the retained
      n=11 families at 96/25 and 153/40?
    hypotheses: [H-229, H-230]
    budget: >-
      A Fable derivation lane of two to three hours for the gap-g lemma; the anchor
      case waits on the non-convex domain instrument.
    entry: >-
      The BC-363 predicate exists, or the gap-g derivation is scheduled in a later
      chunk.
    exit: >-
      Either a reviewed gap-g lemma with an exact pair violation on the 64-family, or
      a recorded reason the extension cannot reach the family's 7.11° orbit at gap
      0.016; the anchor case either runs on the BC-204 instrument or stays blocked.
    bead: think-z20r
    depends_on: [BC-363]
    blocked_on: >-
      The non-convex box-avoidance domain predicate (BC-204) and a conflict-edge atom
      class in the relational reader.
    next_evidence: >-
      The gap-g derivation note and the pairwise check receipt.
    workflows: [insight-iteration]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: overnight-later
  - id: BC-365
    purpose: research
    owner_focus: insight
    instances: [12]
    state: blocked
    priority: 3
    question: >-
      Does an unshrunk covering of mass below 12 exist at side exactly 4?
    hypotheses: [H-228]
    budget: >-
      One to two weeks of verifier tooling before the single decisive LP; not an
      overnight item.
    entry: An unshrunk exact-orientation verifier is admitted.
    exit: The H-228 LP decided in either direction by two unshrunk routes.
    bead: think-mmd5
    depends_on: []
    blocked_on: >-
      An unshrunk exact-orientation verifier generalised from
      cases/green17/interval_audit.py and an unshrunk column generator.
    next_evidence: >-
      A verifier admission receipt, or a certified dual of value at least 12 below
      side 4 from the existing ceiling readers.
    workflows: [pipeline-improvement, research-loop]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: overnight-later
  - id: BC-366
    purpose: research
    owner_focus: insight
    instances: [11, 45]
    state: stopped
    priority: 4
    question: >-
      Should the corner-penetration deep branches, the theta screen, the stressed
      contact-graph theorem, the uniform m^2 - 3 test at m = 5 and 6, or the n=45
      one-spare case run as lanes?
    hypotheses: [H-231]
    budget: None. Retired or parked by the Session 143 adversarial reviews without a measurement.
    entry: The three reviews are complete.
    exit: Each retired item has a recorded reason and a reopening condition.
    bead: think-srln
    depends_on: []
    next_evidence: None; reopen an item only when its stated reopening condition holds.
    workflows: [review-planning-oversight]
    program: n11-strategy-reset
    artifacts:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    parallel_group: retired-after-review
    outcomes:
    - scope: The corner-penetration deep branches as point-certificate cases at 96/25 and 77/20.
      classification: bounded-negative
      result: >-
        Transported to the target sides, the retained families make every deep branch
        exactly neutral, so the all-four-deep class is obstructed for every site set
        and threshold vector; only the all-free class survives as H-222. Reopen only
        with threshold or clique atoms inside the deep classes.
      evidence:
      - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
      disposition: retire-negative
      follow_up: null
    - scope: The theta-prime screen on the retained supports and a theta certificate on uniform pose cells.
      classification: bounded-negative
      result: >-
        The screen cannot discriminate because floor atoms already take the
        88-support to 10 and the 64-support's clique LP is 9; the dual matrix is
        dense (44% edge density at 3.83) and the uniform cell count exceeds the
        lane's own kill line. Recorded as open question H-231; X-037's retirement
        stands.
      evidence:
      - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
      disposition: retire-negative
      follow_up: null
    - scope: The stressed contact-graph theorem in its four-wall form.
      classification: bounded-negative
      result: >-
        False as stated: the two-square side-by-side minimiser has a horizontal
        stress chain only; X-021 already records the "or" form. The surviving
        statement adds the word stressed to X-021's spanning lemma and tests nothing
        new.
      evidence:
      - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
      disposition: retire-negative
      follow_up: null
    - scope: The uniform s(m^2 - 3) = m test by shrunk column generation at m = 5 and m = 6.
      classification: bounded-negative
      result: >-
        Sides 4.99 and 5.99 lie above the shrunk grid ceilings 4.9885 and 5.9862, so
        the LP locks at the exact-integer artefact the record already shows; only
        m = 4 is testable and it is H-223.
      evidence:
      - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
      disposition: retire-negative
      follow_up: null
    - scope: The n=45 and n=44 one-spare cases.
      classification: bounded-negative
      result: >-
        n=45 is a (0, 1) case, not one-spare, and the m = 7 height budget 6.8925 < 7
        blocks Bentz's 0.1 slide; a smaller slide fails Lemma 7. Reopen only with an
        alternative m = 7 layout that restores the slide.
      evidence:
      - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
      disposition: retire-negative
      follow_up: null
---
# Overnight Lower-Bound Loop After X-040

This agenda carries the queue that
[X-040](../explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md)
handed to the overnight loop the owner requested on 2026-09-20.
[Session 143](../agent-sessions/session-143-lower-bound-math-review.md) ran the review;
each later chunk gets its own session record and stacked pull request.

## Relation to Agenda-037

[agenda-037](agenda-037-n11-relational-certificate-program.md) keeps its queue:
`think-qqzs` / H-216 stays the registered n=6 calibration entry, and BC-358 stays
blocked on the relational tooling.
This agenda adds the items X-040 ranked above them for tonight and records the five
retirements the reviews made.

## Queue

- **BC-361 (ready, chunk 1).** Stock-instrument determinations at n=13, n=17, n=26.
- **BC-362 (ready, math lane).** Bentz 2016 replay at the printed constants, then the
  n=21 and n=32 one-spare structures.
- **BC-363 (ready, chunk 2).** The convex corner-clip predicate and the n=11 octagon
  class at 96/25.
- **BC-364 (blocked).** Tilted anchor and gap-g wedge conflicts.
- **BC-365 (blocked).** The unshrunk n=12 LP at side 4.
- **BC-366 (stopped).** Five retirements with reopening conditions.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
