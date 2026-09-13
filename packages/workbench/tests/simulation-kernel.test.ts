import assert from "node:assert/strict";
import { test } from "node:test";
import type { AtlasLaw } from "../src/api/workbench-api.ts";
import {
  advanceSimulation,
  createSimulationState,
  simulationSnapshot,
} from "../src/simulation/kernel.ts";

const repulsion: AtlasLaw = { rigidity: 0.15, repulsion: 2_500, attraction: 0, range: 0 };
const noForce: AtlasLaw = { rigidity: 0.15, repulsion: 0, attraction: 0, range: 0 };

function stepConfiguration(overrides: Record<string, unknown> = {}) {
  return {
    timestep: 0.01,
    container: { originX: 0, originY: 0, side: 3 },
    pairLaw: repulsion,
    wallLaw: noForce,
    baseCell: 1.5,
    contactDamping: 0,
    contactScale: 1,
    spring: { stiffness: 0, damping: 0, quarterTurn: false },
    forcing: { linear: 0, angular: 0, time: 0 },
    maxSpeed: 40,
    maxSpin: 20,
    ...overrides,
  };
}

test("one shared step separates a pair symmetrically and reports exact work", () => {
  const state = createSimulationState({
    squares: [
      { x: 0.7, y: 1.5, angle: 0, size: 1 },
      { x: 1.5, y: 1.5, angle: 0, size: 1 },
    ],
    bodies: [
      { members: [0], angle: 0, target: { x: 0.7, y: 1.5, angle: 0 }, torqueFactor: 0.15 },
      { members: [1], angle: 0, target: { x: 1.5, y: 1.5, angle: 0 }, torqueFactor: 0.15 },
    ],
    container: { originX: 0, originY: 0, side: 3 },
    seed: 0,
    frequencyRange: [2.5, 4],
  });

  const receipt = advanceSimulation(state, stepConfiguration());
  const snapshot = simulationSnapshot(state);

  assert.equal(receipt.work.steps, 1);
  assert.equal(receipt.work.pairCandidates, 1);
  assert.equal(receipt.work.pairForces, 1);
  assert(Math.abs(receipt.deepestPairPenetration - 0.2) < 1e-12);
  assert.deepEqual(
    snapshot.poses.map(({ x, y, angle }) => [x, y, angle]),
    [
      [0.6625, 1.5, 0.016875],
      [1.5375, 1.5, -0.016875],
    ],
  );
  assert.equal(snapshot.container.side, 3);
});

test("the same kernel handles wall forces, pins, and rigid members", () => {
  const wallState = createSimulationState({
    squares: [{ x: -0.1, y: 1.5, angle: 0, size: 1 }],
    bodies: [{ members: [0], angle: 0, target: { x: -0.1, y: 1.5, angle: 0 }, torqueFactor: 0.15 }],
    container: { originX: 0, originY: 0, side: 3 },
    seed: 1,
    frequencyRange: [2.5, 4],
  });
  const wallReceipt = advanceSimulation(
    wallState,
    stepConfiguration({ pairLaw: noForce, wallLaw: repulsion }),
  );
  assert.equal(wallReceipt.work.wallForces, 2);
  assert(Math.abs((simulationSnapshot(wallState).poses[0]?.x ?? 0) + 0.025) < 1e-12);

  const rigid = createSimulationState({
    squares: [
      { x: 1, y: 1.5, angle: 0, size: 1 },
      { x: 2, y: 1.5, angle: 0, size: 1 },
    ],
    bodies: [{ members: [0, 1], angle: 0, target: { x: 1.5, y: 1.5, angle: 0 }, torqueFactor: 1 }],
    container: { originX: 0, originY: 0, side: 3 },
    seed: 2,
    frequencyRange: [2.5, 4],
  });
  const rigidReceipt = advanceSimulation(
    rigid,
    stepConfiguration({
      pinned: { body: 0, x: 1.5, y: 2, angle: Math.PI / 2 },
    }),
  );
  const rigidPoses = simulationSnapshot(rigid).poses;
  assert.equal(rigidReceipt.work.pairCandidates, 0);
  assert(Math.abs((rigidPoses[0]?.x ?? 0) - 1.5) < 1e-12);
  assert(Math.abs((rigidPoses[0]?.y ?? 0) - 1.5) < 1e-12);
  assert(Math.abs((rigidPoses[1]?.x ?? 0) - 1.5) < 1e-12);
  assert(Math.abs((rigidPoses[1]?.y ?? 0) - 2.5) < 1e-12);
});

test("attraction follows the declared relationship mask and forcing is repeatable", () => {
  const definition = {
    squares: [
      { x: 0.7, y: 1.5, angle: 0, size: 1 },
      { x: 1.8, y: 1.5, angle: 0, size: 1 },
    ],
    bodies: [
      { members: [0], angle: 0, target: { x: 0.7, y: 1.5, angle: 0 }, torqueFactor: 0.15 },
      { members: [1], angle: 0, target: { x: 1.8, y: 1.5, angle: 0 }, torqueFactor: 0.15 },
    ],
    container: { originX: 0, originY: 0, side: 3 },
    seed: 17,
    frequencyRange: [2.5, 4] as const,
  };
  const sticky: AtlasLaw = { rigidity: 0.15, repulsion: 2_500, attraction: 120, range: 0.25 };
  const excluded = createSimulationState(definition);
  const included = createSimulationState(definition);
  const mask = new Uint8Array(4);
  advanceSimulation(
    excluded,
    stepConfiguration({
      pairLaw: sticky,
      relatedMask: mask,
      forcing: { linear: 3, angular: 2, time: 0.4 },
    }),
  );
  mask[1] = 1;
  const attracted = advanceSimulation(
    included,
    stepConfiguration({
      pairLaw: sticky,
      relatedMask: mask,
      forcing: { linear: 3, angular: 2, time: 0.4 },
    }),
  );
  assert.equal(attracted.nearPairs, 1);
  assert.notDeepEqual(simulationSnapshot(excluded).poses, simulationSnapshot(included).poses);

  const replay = createSimulationState(definition);
  advanceSimulation(
    replay,
    stepConfiguration({
      pairLaw: sticky,
      relatedMask: mask,
      forcing: { linear: 3, angular: 2, time: 0.4 },
    }),
  );
  assert.deepEqual(simulationSnapshot(replay).poses, simulationSnapshot(included).poses);
  assert.equal(replay.seed, 17);
});

test("invalid definitions and nonfinite step inputs fail before mutation", () => {
  assert.throws(
    () =>
      createSimulationState({
        squares: [{ x: 0, y: 0, angle: 0, size: 1 }],
        bodies: [],
        container: { originX: 0, originY: 0, side: 3 },
        seed: 0,
        frequencyRange: [2.5, 4],
      }),
    /requires squares and bodies/,
  );
  const state = createSimulationState({
    squares: [{ x: 1, y: 1, angle: 0, size: 1 }],
    bodies: [{ members: [0], angle: 0, target: { x: 1, y: 1, angle: 0 }, torqueFactor: 0.15 }],
    container: { originX: 0, originY: 0, side: 3 },
    seed: 0,
    frequencyRange: [2.5, 4],
  });
  const before = simulationSnapshot(state);
  assert.throws(
    () => advanceSimulation(state, stepConfiguration({ timestep: Number.NaN })),
    /timestep/,
  );
  assert.deepEqual(simulationSnapshot(state), before);
});
