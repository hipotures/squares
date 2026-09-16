import type { AtlasLaw } from "../api/workbench-api.js";

const LEGACY_RIGIDITY = 0.15;
const MAX_STEEPENING = 8;
const ASSUMED_CONTACTS = 4;
export const MAX_FORCE_LAW_SUBSTEPS = 12;

/** Extra slope past the repulsion knee; zero at the shipped law. */
export function forceLawSteep(law: AtlasLaw): number {
  return MAX_STEEPENING * Math.max(0, 1 - law.rigidity / LEGACY_RIGIDITY);
}

/** Whether the law reaches across a positive gap. */
export function forceLawAttracts(law: AtlasLaw): boolean {
  return law.attraction > 0 && law.range > 0;
}

/**
 * Evaluate the shared signed-gap law. Negative gaps are penetration and produce repulsion;
 * positive gaps may produce attraction. The pieces meet at zero and at the attraction range.
 */
export function forceAtGap(law: AtlasLaw, gap: number): number {
  if (gap <= 0) {
    const penetration = -gap;
    return (
      law.repulsion *
      (Math.min(penetration, law.rigidity) +
        forceLawSteep(law) * Math.max(0, penetration - law.rigidity))
    );
  }
  if (!forceLawAttracts(law) || gap >= law.range) {
    return 0;
  }
  const progress = gap / law.range;
  return -law.attraction * 4 * progress * (1 - progress);
}

/** Bound Pack's semi-implicit Euler substeps without changing its established search kernel. */
export function forceLawSubsteps(law: AtlasLaw, timestep: number): number {
  const slope = law.repulsion * Math.max(1, forceLawSteep(law));
  const angularFrequency = Math.sqrt(slope * ASSUMED_CONTACTS);
  const stabilityLimit = 2 / angularFrequency;
  return Math.max(1, Math.min(MAX_FORCE_LAW_SUBSTEPS, Math.ceil(timestep / stabilityLimit)));
}

/**
 * Bound Animate's integration cadence for the law's stiffest reachable slope.
 *
 * Pack's established search kernel intentionally keeps the marginal oscillator bound above.
 * Animate needs a visible-path guarantee: contacts are intermittent and nonlinear, so it stays
 * below one radian per integration step with a 25% margin and includes the attractive slope.
 */
export function forceLawAnimationSubsteps(law: AtlasLaw, timestep: number): number {
  return Math.min(MAX_FORCE_LAW_SUBSTEPS, forceLawAnimationRequiredSubsteps(law, timestep));
}

export interface ForceLawAnimationIntegration {
  requested: "adaptive" | number;
  effective: number;
  recommended: number;
  warning: "below-adaptive-stability-bound" | null;
}

/** Resolve the pair and wall laws into a receipt before any trajectory is cached. */
export function forceLawAnimationIntegration(
  pairLaw: AtlasLaw,
  wallLaw: AtlasLaw,
  timestep: number,
  requested: "adaptive" | number = "adaptive",
): ForceLawAnimationIntegration {
  const recommended = Math.max(
    forceLawAnimationRequiredSubsteps(pairLaw, timestep),
    forceLawAnimationRequiredSubsteps(wallLaw, timestep),
  );
  const effective =
    requested === "adaptive" ? Math.min(MAX_FORCE_LAW_SUBSTEPS, recommended) : requested;
  return {
    requested,
    effective,
    recommended,
    warning: effective < recommended ? "below-adaptive-stability-bound" : null,
  };
}

/** Uncapped integration count required by Animate's declared stability approximation. */
export function forceLawAnimationRequiredSubsteps(law: AtlasLaw, timestep: number): number {
  const repulsionSlope = law.repulsion * Math.max(1, forceLawSteep(law));
  const attractionSlope = forceLawAttracts(law) ? (4 * law.attraction) / law.range : 0;
  const slope = Math.max(repulsionSlope, attractionSlope);
  const angularFrequency = Math.sqrt(slope * ASSUMED_CONTACTS);
  const stabilityLimit = 0.75 / angularFrequency;
  const required = Math.ceil(timestep / stabilityLimit);
  return Number.isFinite(required) ? Math.max(1, required) : Number.MAX_SAFE_INTEGER;
}

export const forceLaw = Object.freeze({
  forceLawSteep,
  forceLawAttracts,
  forceAtGap,
  forceLawAnimationIntegration,
  forceLawAnimationSubsteps,
  forceLawAnimationRequiredSubsteps,
  forceLawSubsteps,
  MAX_FORCE_LAW_SUBSTEPS,
});

export type ForceLawModule = typeof forceLaw;
