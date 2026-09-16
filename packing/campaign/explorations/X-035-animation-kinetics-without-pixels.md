---
title: X-035 — animation kinetics without pixels
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-035
  title: Animation Kinetics Without Pixels
  date: '2026-09-16'
  author: Codex
  campaign: packing.squares
  brief: >-
    Diagnose the Animate tab's jumping and misleading rigid, soft and sticky controls;
    define a deterministic headless trajectory and metric surface that can select safe
    defaults, compare approaches and later provide mechanism measurements for Search.
  sources:
  - packages/workbench/src/simulation/force-law.ts
  - packages/workbench/src/simulation/kernel.ts
  - packages/workbench/src/simulation/trajectory.ts
  - packages/workbench/src/motion-settings.ts
  - packages/workbench/src/application.js
  - packages/workbench/tools/measure-kinetics.ts
  - docs/project/specs/active/plan-2026-09-11-workbench-from-spike-to-product.md
  - packing/campaign/explorations/X-034-the-workbench-physics-as-a-search.md
  proposes: [H-213, H-214, H-215]
---
# X-035: Animation Kinetics Without Pixels

## Finding

The reported Animate jump was a numerical path defect rather than a drawing defect.
The physical and body solvers stored one simulation state per animation step.
Stiff contacts could drive the velocity clamp from one extreme to the other on
consecutive steps. Playback interpolated between those stored states, but interpolation
could not remove the alternating path.

The committed repair derives integration substeps from the selected law, retains raw and
corrected states separately, and gives staged physical motion its full solver interval
rather than compressing it behind the new-square arrival.
[Exp-211](../series/series-000-smoke-and-calibration/experiments/exp-211-h213-adaptive-animate-integration.md)
shows that this fixes much of the raw ringing but does not yet satisfy the full 60 Hz
presentation criterion.
A one-off reproduction on current `main` measured the following diagnostic values before
the instrument in this report existed:

| transition and law | largest stored displacement | direction reversals | deepest penetration |
| --- | ---: | ---: | ---: |
| `16 → 17`, rigid, one step | 0.3699 | 945 | 0.6484 |
| `16 → 17`, rigid, two substeps | 0.1617 | 0 | 0.0558 |
| `89 → 90`, rigid, one step | — | 7,832 | 0.7787 |
| `89 → 90`, rigid, two substeps | — | 3 | 0.0786 |

The 0.3699 displacement equals the configured speed limit times the step duration.
The corresponding second difference is 0.7399, which is the same capped motion reversing
direction. These values locate the failure in the integrator and clamp.
They are not a campaign result: the earlier reproduction script was not retained.
H-213 requires the new command to remeasure the control and candidate.

The repair also makes control scope explicit.
Animate opens on tween, where force-law and annealing values have no effect, so those
controls are disabled.
The value formerly presented as rigidity is a penetration tolerance whose direction is
opposite that label: a smaller value makes contact harder and increases the derived
slope. The interface now exposes literal parameter descriptions and restarts a changed
trajectory from the beginning instead of splicing it at the existing playhead.

## Headless Contract

The trajectory generator is the authority.
The browser and a Node command use the same corpus, named settings, preset definitions
and generator. The command can write the full pose trace or a compact summary.
Its summary carries:

- distance per raw kernel step, corrected stored step and deterministic 60 Hz
  presentation sample, with mean, percentiles and maximum in square-side units
- velocity change and acceleration or jerk, including a direction-reversal count and
  ratio
- deepest pair and wall penetration, contact-count summaries and neighbour gaps
- distance and angle from the requested endpoint
- deterministic replay, nonfinite-value and identity guards
- requested and effective timestep, substeps, kernel work and elapsed runtime

The command reports physical metrics as not applicable for tween instead of filling them
with plausible zeroes.
A synthetic cap-to-cap trace is the negative control for the reversal and acceleration
detector. A static trace is its positive control.
Tests mutate each control so a detector that stops running cannot pass silently.

The metrics have distinct roles.
Deterministic 60 Hz displacement and reversal ratio decide presentation smoothness.
Raw and corrected stored-step metrics localize a failure to the integrator, correction
path or presentation schedule; a stable raw path alone cannot pass a visibly
discontinuous presentation.
Penetration, endpoint error, finiteness and determinism are guards.
Contacts, gaps and work explain the mechanism and cost.
A Search experiment may use those mechanism values, but it still ranks only
independently valid packings by its declared objective.

## Controls and Defaults

The user selects an approach before its parameters:

- **Tween** is a deterministic illustration between records.
  Physical controls are disabled because they do not participate.
- **Physics** simulates individual squares with the selected contact law and annealing
  schedule.
- **Bodies** uses the same physical kernel while preserving selected rigid groups.
  Any different perturbation scale is part of the effective configuration, not a hidden
  multiplier.

Physical settings separate contact give, repulsion, attraction and attraction range from
perturbation. Balanced, rigid, soft and sticky are named starting points, not special
code paths. A setting change pauses playback, rebuilds the path and restarts the step at
zero so the old and new paths are never spliced at an arbitrary playhead.

The default physical path must keep mean movement within 20% of the current 0.017 square
sides per displayed frame.
Its largest deterministic 60 Hz displacement must be at most 0.1 and its presentation
reversal ratio at most 0.03. The rigid preset may use 0.15 and 0.05. The same rule is
tested on `16 → 17` and the crowded `89 → 90` transition over at least three seeds per
condition. A setting is rejected if a validity guard fails, regardless of how smooth it
looks.

## Measured Disposition

The headless command is ready and its deterministic replay guard passes.
The frozen-commit parameter defaults and preset claims are not accepted.

- [Exp-211](../series/series-000-smoke-and-calibration/experiments/exp-211-h213-adaptive-animate-integration.md)
  rejects the current end-to-end adaptive path.
  Raw balanced Physics at `n = 90` stays under `0.1` maximum displacement and `0.03`
  reversal ratio, but its 60 Hz presentation reaches median `0.20534` and `0.04181`. No
  balanced or rigid solver-transition group meets every presentation budget over all
  three seeds.
- [Exp-212](../series/series-000-smoke-and-calibration/experiments/exp-212-h214-preset-signatures.md)
  rejects the claimed preset ordering.
  Rigid has less penetration than soft only in two of four solver-transition cells;
  sticky has more mean contacts than balanced at `n = 17` and fewer at `n = 90`.

The next tuning control should address rotational or Bodies-member response, or
normalize perturbation torque and frequency.
The same frozen 24-cell matrix must decide it.
Smoothing or filtering would conceal the path rather than repair it.
Both retained experiments were rerun against frozen commit
`9cca493c17ab61d5efb3e1032f32c54a9b87320e`. The instrument is ready, but `think-o4wo`
and `think-5tyy` remain open because the default budgets and preset claims are rejected.

## Registered Questions

- H-213 tested whether adaptive integration removes clamp ringing without removing the
  intended perturbation; exp-211 rejected the current end-to-end path.
- H-214 tested whether the named force-law presets have distinct, correctly ordered
  kinetic effects while staying within continuity budgets; exp-212 rejected the stated
  universal ordering.
- H-215 asks whether the same kinetic measurements explain which annealing settings
  produce better valid Search outcomes.
  It is an open question; attractive motion is not evidence of a better packing.

**Continuation, 2026-09-16.** [X-036](X-036-graded-guidance-for-annealing.md) carries
that open question into a planned response curve for unguided stickiness and a separate
ladder of structural guidance.
Its first measurements wait for stable physical response under `think-o4wo` and
`think-5tyy`, a frozen guidance contract, and a new comparable campaign series.

## Limits

This investigation covers deterministic raw, corrected and 60 Hz presentation
trajectories.
Browser scheduling and painting can add latency, but they do not change the
positions the presentation sampler supplies and cannot explain the measured cap-to-cap
path. The two experiments are exploratory and cover two transitions with three seeds
each; they do not establish behavior over the whole atlas.
They reject the current claims but do not finish the tuning phase.
Search correlations require a separate fixed-budget seed-block experiment after the
trajectory instrument is stable.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
