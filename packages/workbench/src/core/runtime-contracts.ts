import {
  type GeometryBounds,
  type GeometryContainer,
  type GeometryPose,
  type GeometrySnapshot,
  measurePackingGeometry,
  packingBounds,
} from "./geometry.ts";

const UINT32_MAX = 0xffff_ffff;
const SEED_STRIDE = 0x9e37_79b1;
const GEOMETRY_TOLERANCE = 1e-9;

export type SquarePose = GeometryPose;
export type PackingContainer = GeometryContainer;
export type PackingSnapshot = GeometrySnapshot;
export type PackingBounds = GeometryBounds;

export interface PackingAssessment {
  snapshot: PackingSnapshot;
  valid: boolean;
  reason: string | null;
  requiredSide: number;
  bounds: PackingBounds;
  maxPairOverlap: number;
  maxWallOverlap: number;
}

export interface BestPacking extends PackingSnapshot {
  squareSide: 1;
  at: number;
  requiredSide: number;
  maxPairOverlap: number;
  maxWallOverlap: number;
}

/** Return an exact unsigned 32-bit seed, or refuse the value without coercion. */
export function parseUint32Seed(value: unknown): number | null {
  return typeof value === "number" && Number.isInteger(value) && value >= 0 && value <= UINT32_MAX
    ? value
    : null;
}

/** Fold an exact run seed into a generator base without losing low integer bits. */
export function mixUint32Seed(base: number, seed: number): number {
  const checkedBase = parseUint32Seed(base);
  const checkedSeed = parseUint32Seed(seed);
  if (checkedBase === null || checkedSeed === null) {
    throw new RangeError("seed mixing requires unsigned 32-bit integers");
  }
  return (checkedBase + Math.imul(checkedSeed, SEED_STRIDE)) >>> 0;
}

/** Create the workbench's deterministic linear congruential random stream. */
export function seededRandom(seedValue: number): () => number {
  const checkedSeed = parseUint32Seed(seedValue);
  if (checkedSeed === null) {
    throw new RangeError("the random generator requires an unsigned 32-bit seed");
  }
  let seed = (Math.imul(checkedSeed, 2_654_435_761) + 0x9e37_79b9) >>> 0;
  return () => {
    seed = (Math.imul(seed, 1_664_525) + 1_013_904_223) >>> 0;
    return seed / 4_294_967_296;
  };
}

function valueAt(values: ArrayLike<number>, index: number): number {
  const value = values[index];
  if (value === undefined) {
    throw new RangeError(`pose buffer has no value at index ${index}`);
  }
  return value;
}

/** Copy live numeric buffers into a snapshot with an explicit or tight container. */
export function packingSnapshot(
  x: ArrayLike<number>,
  y: ArrayLike<number>,
  angle: ArrayLike<number>,
  squareSide: number,
  container: PackingContainer | null,
): PackingSnapshot {
  if (x.length !== y.length || x.length !== angle.length) {
    throw new RangeError("pose buffers must have the same length");
  }
  const poses: SquarePose[] = [];
  for (let index = 0; index < x.length; index += 1) {
    poses.push({
      x: valueAt(x, index),
      y: valueAt(y, index),
      angle: valueAt(angle, index),
    });
  }
  if (container !== null) {
    return {
      squareSide,
      container: {
        originX: container.originX,
        originY: container.originY,
        side: container.side,
      },
      poses,
    };
  }
  const bounds = packingBounds(poses, squareSide);
  return {
    squareSide,
    container: {
      originX: bounds.minX,
      originY: bounds.minY,
      side: Math.max(bounds.maxX - bounds.minX, bounds.maxY - bounds.minY),
    },
    poses,
  };
}

/** Copy poses into their smallest axis-aligned square container. */
export function tightPackingSnapshot(
  x: ArrayLike<number>,
  y: ArrayLike<number>,
  angle: ArrayLike<number>,
  squareSide: number,
): PackingSnapshot {
  return packingSnapshot(x, y, angle, squareSide, null);
}

/** Recompute every packing-admission fact from the copied snapshot. */
export function assessPackingSnapshot(
  snapshot: PackingSnapshot,
  expectedCount: number,
): PackingAssessment {
  const unavailableBounds = { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity };
  const unavailable = {
    snapshot,
    requiredSide: Infinity,
    bounds: unavailableBounds,
    maxPairOverlap: 0,
    maxWallOverlap: 0,
  };
  if (
    !Number.isInteger(expectedCount) ||
    expectedCount < 1 ||
    snapshot.poses.length !== expectedCount
  ) {
    return { ...unavailable, valid: false, reason: "count" };
  }
  const numbers = [
    snapshot.squareSide,
    snapshot.container.originX,
    snapshot.container.originY,
    snapshot.container.side,
  ];
  for (const pose of snapshot.poses) {
    numbers.push(pose.x, pose.y, pose.angle);
  }
  if (!numbers.every(Number.isFinite)) {
    return { ...unavailable, valid: false, reason: "nonfinite" };
  }
  if (!(snapshot.squareSide > 0) || !(snapshot.container.side > 0)) {
    return { ...unavailable, valid: false, reason: "dimensions" };
  }
  const geometry = measurePackingGeometry(snapshot);
  const measured = {
    snapshot,
    requiredSide: geometry.requiredSide,
    bounds: geometry.bounds,
    maxPairOverlap: geometry.maxPairOverlap,
    maxWallOverlap: geometry.maxWallOverlap,
  };
  if (geometry.maxPairOverlap > GEOMETRY_TOLERANCE) {
    return { ...measured, valid: false, reason: "pair-overlap" };
  }
  if (geometry.maxWallOverlap > GEOMETRY_TOLERANCE) {
    return { ...measured, valid: false, reason: "wall-overlap" };
  }
  return { ...measured, valid: true, reason: null };
}

/** Admit and deep-copy a smaller valid unit-square packing snapshot. */
export function admitBestPacking(
  current: BestPacking | null,
  candidate: PackingAssessment,
  at: number,
): BestPacking | null {
  if (
    !candidate.valid ||
    candidate.snapshot.squareSide !== 1 ||
    !Number.isFinite(at) ||
    (current !== null && candidate.requiredSide >= current.requiredSide)
  ) {
    return current;
  }
  return {
    squareSide: 1,
    container: { ...candidate.snapshot.container },
    poses: candidate.snapshot.poses.map((pose) => ({ ...pose })),
    at,
    requiredSide: candidate.requiredSide,
    maxPairOverlap: candidate.maxPairOverlap,
    maxWallOverlap: candidate.maxWallOverlap,
  };
}

export const workbenchCore = Object.freeze({
  parseUint32Seed,
  mixUint32Seed,
  seededRandom,
  packingSnapshot,
  tightPackingSnapshot,
  assessPackingSnapshot,
  admitBestPacking,
});

export type WorkbenchCore = typeof workbenchCore;
