---
title: X-036 — graded guidance for annealing
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-036
  title: Graded Guidance for Annealing
  date: '2026-09-16'
  author: Codex
  campaign: packing.squares
  brief: >-
    Plan a measured ladder from ordinary pair stickiness through connected-component,
    contact-graph and oriented face-pair guidance, using one headless simulation kernel,
    known-answer calibration, held-out cells and matched structural controls.
  sources:
  - docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md
  - docs/project/specs/active/plan-2026-09-11-workbench-from-spike-to-product.md
  - packing/campaign/explorations/X-034-the-workbench-physics-as-a-search.md
  - packing/campaign/explorations/X-035-animation-kinetics-without-pixels.md
  - packing/campaign/README.md
  - packing/campaign/ideas.md
  - packing/atlas/known-best/contact-structure.schema.yaml
  proposes: []
---
# X-036: Graded Guidance for Annealing

**Status: planning only.** This report defines an implementation and experiment order.
It records no run, measurement, scientific claim, or experiment artifact.
The target format, force units and application schedule are not frozen, so a result
written now would describe a moving instrument.

## Two Axes, Not One Stickiness Dial

Ordinary stickiness and structural guidance answer different questions.

- **Ordinary stickiness** changes the pair law for every eligible pair without knowing a
  target structure. Its response curve asks whether more or longer-range attraction
  improves valid outcomes, merely increases contacts, or produces clumps that repair
  badly.
- **Structural guidance** identifies selected relationships from a known packing and
  applies a declared force or staging rule to them.
  It can reveal which kinds of prior information help annealing, but it cannot support a
  claim about unguided discovery.

The workbench must expose both axes independently.
A sticky preset cannot silently carry a contact graph, and a structurally guided run
must record the ordinary pair law it used.
Animate, Pack, Search and the command line must resolve the same effective
configuration.

## Target and Application Contracts

One JSON-safe `GuidanceTarget/v1` describes *what is known*. A separate application
configuration describes *how a run uses it*. Keeping them separate lets one target run
under several force laws and schedules without rewriting or relabelling the target.

The target has four admitted information tiers:

1. `none`: no target relationships;
2. `touching-component-partition`: square membership in touching components, without
   edges inside a component;
3. `contact-graph`: selected square pairs, without a prescribed pose; and
4. `oriented-face-pairs`: selected square pairs plus the two contacting features and
   their relative face alignment.

The oriented tier constrains relative features and alignment, not absolute position or
angle. It may attract and turn two squares toward a declared face-to-face relation, but
it may not pin either square to the record pose.
Square identities, symmetry handling, ambiguous feature assignments, source tolerances
and typed refusals belong in the target contract under `think-rey9`; the existing
contact-atlas feature vocabulary (`contact`, `left_feature` and `right_feature`) should
be reused rather than translated into a second face notation.

The application configuration records at least:

- guidance strength, in units fixed before measurement;
- a time or progress schedule, including constant, decay and release forms;
- the use made of the target, such as start construction, attraction, alignment, weld or
  release; and
- the policy for pairs absent from the target.

`think-8ocb` owns the format and capability declarations; `think-os1n` owns the kernel
mechanics and schedule composition.
Unsupported tiers or uses are refused before a run.

Strength zero is the identity control.
Canonicalization must erase an inert target before execution identity is computed, so
zero-strength guidance produces exactly the unguided trajectory, counters, outcome and
canonical receipt for the same effective configuration and seed.
A numerically close result is a failed guard.

## One Nonvisual Instrument

The browser and command line use the same deterministic TypeScript kernel, target
decoder, application configuration, seed handling, trajectory generator and receipt
encoder. Browser code may draw target edges, components, oriented faces and force
strength, but the overlay is a view of the run rather than the source of its behavior.

The headless path must make every comparison possible without pixels:

- run one configuration or a fixed seed block;
- emit raw, corrected and presentation trajectories where applicable;
- retain the target content hash, effective application configuration and exact work;
- recompute outcome, guard, cost and mechanism metrics from the retained trace; and
- replay the same receipt through browser and command-line adapters.

`think-qx88` owns the shared evaluation and metric surface, `think-gfqt` the bounded
multi-run scheduler and replayable receipts, and `think-czav` the workbench controls and
overlays. The application may add no browser-only force path.

## Experiment Ladder

The program advances one information increment at a time:

1. **Stabilize the unguided response.** Close the physical-response prerequisites
   `think-o4wo` and `think-5tyy`; then measure ordinary stickiness across a fixed range
   with no structural target.
2. **Add components.** Compare a true touching-component partition with no target and
   with shuffled partitions that preserve component sizes.
3. **Add graph edges.** Compare the true contact graph with matched thinned and rewired
   graphs. Controls preserve declared edge-count or degree properties so “more forces” is
   not confused with “correct structure.”
4. **Add oriented faces.** Compare typed face-pair guidance with the same graph stripped
   to untyped edges. The contrast measures the added alignment information.
5. **Vary the schedule.** Compare constant guidance with predeclared decay and release
   schedules at fixed work.

Every stage retains the unguided arm.
A later tier cannot replace an earlier negative result, and a stage does not advance
merely because it reconstructs more of the target.
`think-0epc` owns the sweep after the contracts and instrument pass their guards.

## Calibration, Controls and Work

The campaign manifest freezes known-answer calibration cells and held-out cells before
the first target run (`think-3yma`). Parameter choices use only the calibration side;
the held-out side decides whether a setting transfers.
True structures come from known records under the frozen extractor, so each result
states how much of the answer the run received.

Configuration arms use paired seed blocks and execute in an interleaved order.
They receive the same declared work budget.
Pair tests remain the primary cross-proposer currency once enforcement exists; the
receipt also reports candidates, kernel steps and guidance-force work.
CPU time and wall time are recorded beside the receipt, as Search outcomes already carry
`elapsedMs`, so they never enter receipt identity or the zero-strength comparison.
A comparison with unequal effective work is invalid rather than suggestive.

Required controls are:

- unguided execution and the exact zero-strength identity;
- true versus shuffled component partitions;
- true versus thinned and rewired contact graphs;
- oriented face pairs versus the same untyped graph;
- constant versus decay and release schedules;
- deterministic replay, nonfinite and malformed-target mutations; and
- the X-035 trajectory continuity and penetration guards.

`think-gdkd` freezes each directional hypothesis, metric mapping and accept rule before
measurement. No post-result threshold or preferred seed block may enter the same round.

## Metric Vector and Verdict Boundary

The planned guided-search vector has five roles:

| Role | Required measurements |
| --- | --- |
| outcome | valid success count per seed block; block-best valid side and gap to the declared comparator |
| guard | independent geometry validity, finiteness, deterministic replay, exact zero-strength equivalence and X-035 continuity budgets |
| cost | pair tests, candidates, kernel steps, guidance-force work, CPU time and wall time |
| mechanism | component recovery, contact precision and recall, false contacts, oriented-face recovery, contacts, gaps and trajectory kinetics |
| spread | paired differences over predeclared, interleaved seed blocks; calibration and held-out results reported separately |

Target recovery is explanatory.
Better component recovery, contact recall or face-assignment recovery cannot accept a
search claim unless the candidate also improves the preregistered valid-side outcome
under equal work and all guards pass.
A smooth or visually convincing trace has the same limitation.

## Record and Ownership

The first measured round must open a truthful successor series under `think-i08r`.
Guidance targets, new work accounting and the shared trajectory/receipt contract change
the regime enough that appending these rounds to `series-000` would imply false
comparability. Until the contract, strength units, instrument and hypotheses are frozen,
there is no experiment artifact to allocate.

The tracked program is:

- `think-c0rm`: graded-guidance program and strategy comparisons;
- `think-8ocb`: `GuidanceTarget/v1`, application configuration and capabilities;
- `think-rey9`: component, graph and oriented-feature extraction with ambiguity and
  refusal semantics;
- `think-os1n`: attraction, alignment, weld, decay and release mechanics;
- `think-qx88`: shared command-line evaluation, trajectories and target metrics;
- `think-gdkd`: preregistered metric vector and hypotheses;
- `think-3yma`: calibration and held-out split;
- `think-gfqt`: bounded scheduling, hashes and replay parity;
- `think-czav`: workbench controls, overlays and replay;
- `think-0epc`: the systematic sweep after admission; and
- `think-o4wo` and `think-5tyy`: stable physical-response prerequisites.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
