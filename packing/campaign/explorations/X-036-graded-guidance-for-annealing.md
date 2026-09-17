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
    Plan a measured ladder from ordinary pair stickiness through touching-component,
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

Today the axes are one control: the kernel’s `relatedMask` restricts ordinary pair-law
attraction to masked pairs, Search accepts `related_mask`, and the page builds masks
from blocks and contact graphs, so the only guidance strength is the pair law’s
attraction. `think-8ocb` moves that path into the target and application contracts, and
registered cohorts refuse `related_mask` until `think-os1n` adds a separate guidance
force.

## Target and Application Contracts

One JSON-safe `GuidanceTarget/v1` describes *what is known*. A separate application
configuration describes *how a run uses it*. Keeping them separate lets one target run
under several force laws and schedules without rewriting or relabelling the target.

The target has four admitted information tiers:

1. `none`: no target relationships;
2. `touching-component-partition`: square membership in touching components, without
   edges inside a component; at a label-agnostic start only the component-size profile
   is usable;
3. `contact-graph`: selected square pairs, without a prescribed pose; and
4. `oriented-face-pairs`: selected square pairs plus the two contacting features and,
   for edge-edge contacts, their face alignment.

The annealing plan’s
[tier table](../../../docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md#one-target-contract-separate-application-policy)
is the naming table for these tiers and their strategy rungs.

The oriented tier stores relative features and alignment, not absolute position or
angle, and it may not pin either square to the record pose.
It can still determine the record: where the contact equations are rigid, a complete
target fixes the poses locally up to congruence, so each target reports the degrees of
freedom it leaves. Corner-edge and corner-corner contacts carry their feature incidence
and no alignment. Square identities, symmetry handling, ambiguous feature assignments,
source tolerances and typed refusals belong in the target contract under `think-rey9`;
the existing contact-atlas feature vocabulary (`contact`, `left_feature` and
`right_feature`) should be reused rather than translated into a second face notation.

The application configuration records, for each use:

- the use made of the target, such as start construction, attraction, alignment, weld or
  release;
- where the use has a strength, that strength in units fixed before measurement, with a
  time or progress schedule including constant, decay and release forms; and
- the policy for pairs absent from the target.

Attraction and alignment take a continuous strength.
Start construction, welds and per-body shake are discrete, so each names its unguided
control: the unguided proposal at the same seed, no weld, and uniform shake.

`think-8ocb` owns the format and capability declarations; `think-os1n` owns the kernel
mechanics and schedule composition.
Unsupported tiers or uses are refused before a run.

Strength zero is the identity control, tested at the receipt and in the kernel.
The requested configuration, zero strengths included, is kept in a requested-guidance
record beside the receipt.
The canonical effective receipt omits inert uses, so a zero-strength run’s canonical
receipt is byte-for-byte the unguided receipt.
That identity only tests canonicalization, so the kernel also runs un-normalized with
the target loaded and every strength exactly zero, and must reproduce the unguided
trajectory, validity and outcome exactly.
A numerically close result is a failed guard.
That exactness needs the guidance force in its own pass, so it cannot widen the
broad-phase cell or reorder the pair-law sums.
Along a declared descending ladder of small strengths, the short-horizon pose difference
from the unguided trajectory must not increase and must end within a declared bound.

## One Nonvisual Instrument

The browser and command line use the same deterministic TypeScript kernel, target
decoder, application configuration, seed handling, trajectory generator and receipt
encoder. Browser code may draw target edges, components, oriented faces and force
strength, but the overlay is a view of the run rather than the source of its behavior.

The headless path must make every comparison possible without pixels:

- run one configuration or a fixed seed block;
- emit raw, corrected and presentation trajectories where applicable;
- retain the requested-guidance record, the canonical effective receipt and exact work;
- recompute outcome, guard, cost and mechanism metrics from the retained trace; and
- replay the same receipt through command-line and browser adapters in Node and the
  pinned Chromium build; other browsers are not claimed to replay bit for bit.

`think-qx88` owns the shared evaluation and metric surface, `think-gfqt` the bounded
multi-run scheduler and its Node command, `think-10yz` the guided configuration and
receipts that scheduler carries, and `think-czav` the workbench controls and overlays.
`think-05o4` freezes the partition and `think-9hdg` runs the unguided stickiness curve.
The application may add no browser-only force path.

## Experiment Ladder

The program advances one information increment at a time.
The controls, eligible cells, work currency, deciding statistic and selection rule below
are the planned defaults in the annealing plan’s
[registration defaults](../../../docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md#planned-registration-defaults),
which `think-gdkd` freezes or revises before the first measured round.

1. **Measure the unguided response** (`think-9hdg`). Sweep ordinary stickiness across a
   fixed range with no structural target, through Search’s Pack runner in Node.
   This round needs no guidance contract.
   It waits for registration (`think-gdkd`), the frozen partition (`think-05o4`), the
   base scheduler with its Node command (`think-gfqt`), checkable ledgers (`think-i5pg`)
   and the successor series (`think-i08r`). It has no kinetic guard: Pack keeps no
   trajectory that Animate could replay.
2. **Add components.** Search’s `grid` start is unseeded and places square `i` in cell
   `i`, so every structural arm at `grid` or `random` first relabels its target by a
   permutation drawn from the slot’s seed, shared by every arm on that seed.
   After that relabelling a partition carries only its component-size profile, so
   compare the true touching-component partition with the unguided arm and with a
   split-merge partition that changes that profile at a near-equal count of
   within-component pairs.
   A size-preserving membership shuffle is a control only at a label-dependent start,
   which in Search is `record-append`. A record that is one touching component, as
   `n = 11` and 29 both are, gives a partition that carries nothing beyond `n`, so its
   cells are excluded.
3. **Add graph edges.** Compare the true contact graph with the unguided arm and a
   rewired graph of the same edge count, and a thinned true graph with its rewired twin:
   the same kept edges, with the same fraction moved as the full rewired control.
   That way “more forces” is not confused with “correct structure.”
4. **Add oriented faces.** Compare typed face-pair guidance with the unguided arm, with
   a wrong-feature assignment that permutes features within each contact kind at the
   same torque strength, range and schedule, and with the untyped graph under a
   label-free nearest-face torque.
   The wrong-feature arm isolates the feature information; the torque arm keeps the new
   torque from being credited to it.
   All three comparators decide.
5. **Vary the schedule.** Compare constant guidance with predeclared decay and release
   schedules at fixed work.

Every stage retains the unguided arm.
After stage 1 it runs at the stickiness level `think-9hdg` confirmed on held-out cells,
or at zero attraction if it confirmed none.

A later tier cannot replace an earlier negative result, and a stage does not advance
merely because it reconstructs more of the target.
The unguided stickiness curve is its own task; `think-0epc` owns the guided sweep after
the contracts and instrument pass their guards and the curve has fixed the stickiness
level that guided arms use.

## Calibration, Controls and Work

A headless partition freeze (`think-05o4`) fixes known-answer calibration cells and
held-out cells in the campaign manifest before the first measured round.
Search’s presets (`think-3yma`) can load that partition but neither define it nor wait
for it. The freeze uses `think-rey9`’s per-tier coverage, which today is thin: typed
features exist only for `n = 11` and 29, whose 66 pair contacts are 35 edge-edge, 25
corner-edge and 6 corner-corner, and both records are single touching components.
Parameter choices use only the calibration side, under a selection rule frozen with the
contrasts; held-out confirmation is the only decision gate.
True structures come from known records under the frozen extractor, so each result
states how much of the answer the run received.

Configuration arms use paired seed blocks and execute in an interleaved order.
They share the enforced Search budget: physics steps, proposal attempts and repair
iterations per slot, and the same base slots per block on the same paired seeds.
Guidance work is charged rather than exempt.
Each slot reports pair candidates, guidance-force evaluations and repair pair tests.
When two arms differ in pair-level work, the lighter arm, candidate or comparator, also
runs compensation slots from a reserved seed range disjoint from every other seed, in a
number fixed per contrast, arm and setting by a work-only pilot that runs on every
frozen cell before calibration and reads no outcome.
Reports state the realized work ratio for calibration and held-out cells; a comparison
outside the declared band is invalid and is not re-tuned, any invalid held-out
comparison makes its stage invalid rather than accepted or rejected, and a win that
holds only at equal steps is not accepted.
No guided-versus-unguided comparison is admissible until `think-gdkd` has declared this
currency. Registered cohorts leave `timeoutMs` unset, and receipt identity hashes the
canonical trial value rather than the Search outcome that carries `elapsedMs`. CPU time,
measured in Node only, and wall time are operational context beside the receipt; they
never enter receipt identity, the budget or the zero-strength comparison.

Required controls are:

- unguided execution and the zero-strength canonical-receipt, un-normalized and
  small-strength controls;
- seed-derived target relabelling at `grid` and `random` starts;
- true versus split-merge component partitions, and true versus shuffled membership at
  `record-append` starts only;
- true versus rewired contact graphs at equal edge count, and thinned true graphs versus
  their rewired twins;
- oriented face pairs versus a wrong-feature assignment and versus the untyped graph
  under a nearest-face torque;
- constant versus decay and release schedules; and
- deterministic replay, nonfinite and malformed-target mutations.

The X-035 continuity budgets are not a guard here.
They are defined on Animate’s presentation samples of a corpus transition, while a
Search trial runs through Pack, keeps no trajectory, and integrates with Pack’s own
stability bound. Kinetic metrics for Search trials would need a retained Pack trajectory
resampled at presentation rate, an instrument that does not exist and would be
registered under H-215.

`think-gdkd` freezes each directional hypothesis, the full contrast list, metric
mapping, selection rule, work currency and accept rule before measurement.
No post-result threshold or preferred seed block may enter the same round.

## Metric Vector and Verdict Boundary

The planned guided-search vector has five roles:

| Role | Required measurements |
| --- | --- |
| outcome | valid success count per seed block; block-best valid side and gap to the declared comparator |
| guard | independent geometry validity, finiteness, deterministic replay and the zero-strength controls |
| cost | the enforced Search budget (physics steps, proposal attempts, repair iterations) and charged pair-level work (pair candidates, guidance-force evaluations, repair pair tests); CPU time from Node and wall time as operational context only |
| mechanism | component recovery, contact precision and recall, false contacts, oriented-face recovery, contacts and gaps; no trajectory kinetics until Search retains a Pack trajectory |
| spread | paired differences over predeclared, interleaved seed blocks, reported but not deciding; calibration and held-out results reported separately |

Target recovery is explanatory.
Better component recovery, contact recall or face-assignment recovery cannot accept a
search claim unless the candidate also improves the preregistered valid-side outcome
under equal work and all guards pass.
A smooth or visually convincing trace has the same limitation.
The planned deciding statistic is the search-proposer accept rule’s clause 1 on held-out
cells, with seed blocks in place of seeds and block-best valid side in place of
`best_side`: a lower median than each deciding comparator and non-overlapping ranges,
where a block with no valid state counts as +∞ and ranges that share an endpoint
overlap.

## Record and Ownership

The first measured round must open a truthful successor series under `think-i08r`.
Guidance targets, new work accounting and the shared trajectory/receipt contract change
the regime enough that appending these rounds to `series-000` would imply false
comparability. Until the work currency, instrument, partition and hypotheses are frozen,
and for a guided round also the target contract and strength units, there is no
experiment artifact to allocate.

The tracked program is:

- `think-c0rm`: graded-guidance program and strategy comparisons;
- `think-8ocb`: `GuidanceTarget/v1`, application configuration, the `relatedMask`
  migration, registered controls and capabilities;
- `think-rey9`: component, graph and oriented-feature extraction with ambiguity and
  refusal semantics, per-record component counts, feature coverage and remaining degrees
  of freedom;
- `think-os1n`: a separate guidance force, attraction, alignment, weld, decay and
  release mechanics;
- `think-qx88`: shared command-line evaluation, trajectories and target metrics;
- `think-10yz`, guided Search receipts: the same configuration and canonical receipt
  through the base scheduler;
- `think-gdkd`: preregistered metric vector, hypotheses, contrasts, selection rule and
  work currency;
- `think-05o4`, the headless partition freeze: calibration and held-out cells, which
  `think-3yma`’s Search presets later read;
- `think-gfqt`: bounded scheduling, the Node command that runs a Search plan, hashes and
  replay parity;
- `think-czav`: workbench controls, overlays and replay;
- `think-9hdg`, the unguided stickiness curve: the first measured round;
- `think-0epc`: the systematic guided sweep after admission; and
- `think-o4wo` and `think-5tyy`: the physical-response work, which the rounds and guided
  receipts reach only through the base scheduler’s wait for Pack/Animate merge
  readiness.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
