import assert from "node:assert/strict";
import { test } from "node:test";
import type { AtlasLaw } from "../src/api/workbench-api.ts";
import type { CorpusFrame, CorpusPair } from "../src/data/corpus.ts";
import {
  buildTrajectory,
  sampleTrajectoryPose,
  sampleTrajectorySide,
  type TrajectoryRequest,
  trajectoryByteLength,
} from "../src/simulation/trajectory.ts";

const source: CorpusFrame = {
  side: 2,
  ident: [1, 2],
  squares: [
    [0.5, 0.5, 0, "#000000", 2],
    [1.5, 0.5, 0, "#000000", 2],
  ],
};
const target: CorpusFrame = {
  side: 2,
  ident: [1, 2, 3],
  squares: [
    [0.5, 0.5, 0, "#000000", 2],
    [1.5, 0.5, 0, "#000000", 2],
    [1, 1.5, 0, "#000000", 2],
  ],
};
const pair: CorpusPair = {
  n: 2,
  kind: "matched",
  map: [0, 1],
  new: 2,
  new_rule: "test",
  new_tied: 0,
  blocks: [
    {
      members: [0, 1],
      riders: [],
      cluster: 0,
      turn: 0,
      from: [1, 0.5],
      to: [1, 0.5],
      drift_max: 0,
    },
  ],
  block_of: [0, 0],
  prev_new: null,
  stats: {},
};
const law: AtlasLaw = { rigidity: 0.15, repulsion: 2_500, attraction: 0, range: 0 };
const rigidLaw: AtlasLaw = { rigidity: 0.01, repulsion: 4_000, attraction: 0, range: 0 };

function request(overrides: Partial<TrajectoryRequest> = {}): TrajectoryRequest {
  return {
    pairIndex: 0,
    pair,
    source,
    target,
    steps: 24,
    style: "physics",
    mode: "snap",
    effectiveSeed: 17,
    pairLaw: law,
    wallLaw: law,
    relatedMask: null,
    anneal: { level: 3, amplitude: 1, decayPower: 1.5, span: 1 },
    physics: {
      omega: 10,
      zeta: 0.85,
      springRamp: 0.25,
      contactDamping: 20,
      contactTorque: 0.15,
      lockIn: 0.7,
      open: 0.3,
      openBy: 0.3,
      shutFrom: 0.62,
      tighten: 16,
      tightenFrom: 0.68,
      grow: 0.5,
      jiggle: 20,
      jiggleTorque: 12,
      bodiesJiggle: 40,
      bodiesJiggleTorque: 24,
      jiggleHz: [2.5, 4],
      drop: 0,
      appear: 0.15,
      inflateFrom: 0.3,
      blend: 0.12,
      maxSpeed: 40,
      maxSpin: 20,
      cell: 1.5,
    },
    blind: {
      inflate: 1.12,
      hold: 0.2,
      close: 0.9,
      overlapTolerance: 0.08,
      gridStep: 0.25,
    },
    ...overrides,
  };
}

interface TrajectoryKinetics {
  maxStep: number;
  maxSecondDifference: number;
  reversalRatio: number;
  meanStep: number;
}

function trajectoryStateAt(trajectory: ReturnType<typeof buildTrajectory>, offset: number): number {
  const value = trajectory.states[offset];
  if (value === undefined) {
    throw new RangeError("trajectory state is incomplete");
  }
  return value;
}

function trajectoryKinetics(trajectory: ReturnType<typeof buildTrajectory>): TrajectoryKinetics {
  const squareCount = trajectory.n + 1;
  let maxStep = 0;
  let maxSecondDifference = 0;
  let reversals = 0;
  let reversalOpportunities = 0;
  let distance = 0;
  let displacementCount = 0;
  for (let index = 0; index < squareCount; index++) {
    let previousX = 0;
    let previousY = 0;
    let hasPrevious = false;
    for (let step = 1; step <= trajectory.steps; step++) {
      const previousOffset = ((step - 1) * squareCount + index) * 3;
      const offset = (step * squareCount + index) * 3;
      const dx =
        trajectoryStateAt(trajectory, offset) - trajectoryStateAt(trajectory, previousOffset);
      const dy =
        trajectoryStateAt(trajectory, offset + 1) -
        trajectoryStateAt(trajectory, previousOffset + 1);
      const length = Math.hypot(dx, dy);
      maxStep = Math.max(maxStep, length);
      distance += length;
      displacementCount++;
      if (hasPrevious) {
        maxSecondDifference = Math.max(
          maxSecondDifference,
          Math.hypot(dx - previousX, dy - previousY),
        );
        const previousLength = Math.hypot(previousX, previousY);
        if (length > 1e-4 && previousLength > 1e-4) {
          reversalOpportunities++;
          if (dx * previousX + dy * previousY < 0) {
            reversals++;
          }
        }
      }
      previousX = dx;
      previousY = dy;
      hasPrevious = true;
    }
  }
  return {
    maxStep,
    maxSecondDifference,
    reversalRatio: reversalOpportunities === 0 ? 0 : reversals / reversalOpportunities,
    meanStep: distance / displacementCount,
  };
}

function gridFrame(count: number, columns: number): CorpusFrame {
  const rows = Math.ceil(count / columns);
  return {
    side: Math.max(columns, rows),
    ident: Array.from({ length: count }, (_, index) => index + 1),
    squares: Array.from({ length: count }, (_, index) => [
      (index % columns) + 0.5,
      Math.floor(index / columns) + 0.5,
      0,
      "#000000",
      2,
    ]),
  };
}

function crowdedRequest(count: 16 | 89): TrajectoryRequest {
  const columns = count === 16 ? 4 : 10;
  const source = gridFrame(count, columns);
  const target = gridFrame(count + 1, columns);
  source.side = target.side;
  const blocks = Array.from({ length: Math.ceil(count / columns) }, (_, row) => {
    const members = Array.from(
      { length: Math.min(columns, count - row * columns) },
      (_unused, column) => row * columns + column,
    );
    return {
      members,
      riders: [],
      cluster: row,
      turn: 0,
      from: [(members.length + 1) / 2, row + 0.5] as [number, number],
      to: [(members.length + 1) / 2, row + 0.5] as [number, number],
      drift_max: 0,
    };
  });
  return request({
    pairIndex: count,
    pair: {
      n: count,
      kind: "matched",
      map: Array.from({ length: count }, (_, index) => index),
      new: count,
      new_rule: "kinetics fixture",
      new_tied: 0,
      blocks,
      block_of: Array.from({ length: count }, (_, index) => Math.floor(index / columns)),
      prev_new: null,
      stats: {},
    },
    source,
    target,
    steps: 192,
    style: "physics",
    mode: "free",
    pairLaw: rigidLaw,
    wallLaw: rigidLaw,
    anneal: { level: 9, amplitude: 19 / 7, decayPower: 0.35, span: 1.6 },
    physics: { ...request().physics, bodiesJiggle: 20, bodiesJiggleTorque: 12 },
  });
}

test("snap trajectories are deterministic, exact at both ends, and openly step-limited", () => {
  const first = buildTrajectory(request());
  const replay = buildTrajectory(request());
  assert.deepEqual(first.states, replay.states);
  assert.deepEqual(first.rawStates, replay.rawStates);
  assert.notDeepEqual(first.rawStates, first.states);
  assert.deepEqual(first.receipt, replay.receipt);
  assert.deepEqual(sampleTrajectoryPose(first, 0, 0), [0.5, 0.5, 0]);
  assert.deepEqual(sampleTrajectoryPose(first, 2, 1), [1, 1.5, 0]);
  assert.equal(sampleTrajectorySide(first, 0), source.side);
  assert.equal(sampleTrajectorySide(first, 1), target.side);
  assert.equal(first.receipt.termination.reason, "step-limit");
  assert.equal(first.receipt.termination.converged, false);
  assert.equal(first.receipt.feasibility.valid, true);
  assert.deepEqual(first.receipt.configuration.integration, {
    requested: "adaptive",
    effective: 6,
    recommended: 6,
    warning: null,
  });
  assert.equal(
    first.receipt.work.steps,
    first.steps * first.receipt.configuration.integration.effective,
  );
  assert.equal(first.receipt.storedTimestep, 1 / 24);
  assert.equal(
    first.receipt.timestep * first.receipt.configuration.integration.effective,
    first.receipt.storedTimestep,
  );
});

test("body trajectories share rigid members while square trajectories keep separate bodies", () => {
  const squares = buildTrajectory(request({ style: "physics", mode: "free" }));
  const bodies = buildTrajectory(request({ style: "bodies", mode: "free" }));
  assert.equal(squares.rawStates, squares.states);
  assert.equal(bodies.rawStates, bodies.states);
  assert.equal(squares.bodies, 3);
  assert.equal(bodies.bodies, 2);
  assert.notDeepEqual(squares.states, bodies.states);
  for (const trajectory of [squares, bodies]) {
    assert(trajectory.receipt.residual.maxLinearSpeed >= 0);
    assert(trajectory.receipt.residual.maxAngularSpeed >= 0);
    assert.equal(trajectory.receipt.configuration.mode, "free");
  }
});

test("an arriving square starts inside the old container before the container opens", () => {
  const expandedSquares = target.squares.slice();
  expandedSquares[2] = [2.8, 2.8, 0, "#000000", 0];
  const expandedTarget: CorpusFrame = {
    ...target,
    side: 3,
    squares: expandedSquares,
  };
  const trajectory = buildTrajectory(request({ target: expandedTarget }));
  const initialRadius = request().physics.inflateFrom / 2;
  const arrivingOffset = pair.n * 3;
  assert.equal(trajectoryStateAt(trajectory, arrivingOffset), source.side - initialRadius);
  assert.equal(trajectoryStateAt(trajectory, arrivingOffset + 1), source.side - initialRadius);
  assert.deepEqual(sampleTrajectoryPose(trajectory, pair.n, 1), [2.8, 2.8, 0]);
});

test("blind trajectories disclose the squeeze result and never claim guided convergence", () => {
  const trajectory = buildTrajectory(request({ mode: "blind", style: "physics" }));
  assert.equal(trajectory.receipt.configuration.guided, false);
  assert.equal(trajectory.receipt.termination.converged, false);
  assert(trajectory.squeeze >= 0 && trajectory.squeeze <= 1);
  assert.equal(trajectory.sides.length, trajectory.steps + 1);
  assert.equal(trajectory.newSizes.length, trajectory.steps + 1);
  assert.equal(trajectory.allPens.length, trajectory.steps + 1);
  assert.equal(trajectory.pens.length, trajectory.steps + 1);
  assert.equal(trajectory.nears.length, trajectory.steps + 1);
  assert.equal(trajectory.newSizes[0], request().physics.inflateFrom);
  assert.equal(trajectory.newSizes.at(-1), 1);
});

test("bad counts, step budgets and nonfinite inputs are rejected", () => {
  assert.throws(() => buildTrajectory(request({ steps: 0 })), /step budget/);
  assert.throws(() => buildTrajectory(request({ integrationSubsteps: 0 })), /substeps/);
  assert.throws(() => buildTrajectory(request({ integrationSubsteps: 1.5 })), /substeps/);
  assert.throws(() => buildTrajectory(request({ integrationSubsteps: 13 })), /substeps/);
  assert.throws(
    () => buildTrajectory(request({ source: { ...source, squares: source.squares.slice(0, 1) } })),
    /source frame/,
  );
  assert.throws(
    () => buildTrajectory(request({ physics: { ...request().physics, omega: Number.NaN } })),
    /omega/,
  );
});

test("annealing level zero is an unforced run, not an invalid request", () => {
  const unforced = buildTrajectory(
    request({ mode: "free", anneal: { level: 0, amplitude: 0, decayPower: 1.5, span: 1 } }),
  );
  assert.equal(unforced.receipt.forcing.active, false);
  assert.equal(
    unforced.receipt.work.steps,
    unforced.steps * unforced.receipt.configuration.integration.effective,
  );
  assert.throws(
    () =>
      buildTrajectory(request({ anneal: { level: 0, amplitude: -0.1, decayPower: 1.5, span: 1 } })),
    /annealAmplitude/,
  );
});

test("zero contact damping is a supported un-damped experiment", () => {
  const undamped = buildTrajectory({
    ...request(),
    physics: { ...request().physics, contactDamping: 0 },
  });
  assert.equal(undamped.states.length, (undamped.steps + 1) * (undamped.n + 1) * 3);
  assert.ok(undamped.receipt.work.steps > 0);
});

test("stiff crowded trajectories stay continuous at stored-frame resolution", () => {
  for (const count of [16, 89] as const) {
    for (const style of ["physics", "bodies"] as const) {
      const configured = crowdedRequest(count);
      configured.style = style;
      const trajectory = buildTrajectory(configured);
      const replay = buildTrajectory(configured);
      const kinetics = trajectoryKinetics(trajectory);
      assert.deepEqual(trajectory.states, replay.states);
      assert.equal(trajectory.states.length, (trajectory.steps + 1) * (count + 1) * 3);
      assert.equal(trajectory.sides.length, trajectory.steps + 1);
      assert.equal(trajectory.newSizes.length, trajectory.steps + 1);
      assert.equal(trajectory.allPens.length, trajectory.steps + 1);
      assert(kinetics.maxStep <= 0.15, `n=${count} ${style} max step ${kinetics.maxStep}`);
      assert(
        kinetics.maxSecondDifference <= 0.15,
        `n=${count} ${style} max second difference ${kinetics.maxSecondDifference}`,
      );
      assert(
        kinetics.reversalRatio <= 0.05,
        `n=${count} ${style} reversal ratio ${kinetics.reversalRatio}`,
      );
      assert(
        trajectory.maxPenetration <= 0.1,
        `n=${count} ${style} penetration ${trajectory.maxPenetration}`,
      );
      assert(kinetics.meanStep > 0.001, `n=${count} ${style} should retain visible motion`);
      assert(trajectory.receipt.work.steps > trajectory.steps);
      assert.equal(trajectory.receipt.work.steps % trajectory.steps, 0);
      assert.equal(trajectory.receipt.penetration.growthEpoch, trajectory.maxPenetrationGrowth);
      assert.equal(trajectory.receipt.penetration.activeFullSize, trajectory.maxPenetration);
      assert.equal(trajectory.receipt.penetration.lateFullSize, trajectory.maxPenetrationLate);
    }
  }
});

test("trajectory stability accounts for both pair and wall laws", () => {
  const pairStiff = crowdedRequest(16);
  pairStiff.wallLaw = law;
  const wallStiff = crowdedRequest(16);
  wallStiff.pairLaw = law;
  for (const configured of [pairStiff, wallStiff]) {
    const trajectory = buildTrajectory(configured);
    assert.equal(trajectory.receipt.configuration.integration.effective, 4);
    assert.equal(trajectory.receipt.work.steps, trajectory.steps * 4);
  }
});

test("manual substeps expose an unstable control without misreporting it", () => {
  const configured = crowdedRequest(16);
  configured.integrationSubsteps = 1;
  const control = buildTrajectory(configured);
  const kinetics = trajectoryKinetics(control);
  assert.deepEqual(control.receipt.configuration.integration, {
    requested: 1,
    effective: 1,
    recommended: 4,
    warning: "below-adaptive-stability-bound",
  });
  assert.equal(control.receipt.work.steps, control.steps);
  assert(kinetics.maxStep > 0.15);
  assert(kinetics.maxSecondDifference > 0.15);
  assert(kinetics.reversalRatio > 0.05);
  assert(control.maxPenetration > 0.1);
});

test("adaptive integration reports when the bounded implementation is underresolved", () => {
  const capped = buildTrajectory(request({ steps: 1 }));
  assert.equal(capped.receipt.configuration.integration.requested, "adaptive");
  assert.equal(capped.receipt.configuration.integration.effective, 12);
  assert.ok(capped.receipt.configuration.integration.recommended > 12);
  assert.equal(capped.receipt.configuration.integration.warning, "below-adaptive-stability-bound");
});

test("trajectory byte size counts retained buffers once, including the snap source path", () => {
  const snapped = buildTrajectory(request({ mode: "snap" }));
  const free = buildTrajectory(request({ mode: "free" }));
  const auxiliaries = (trajectory: typeof snapped) =>
    trajectory.sides.byteLength +
    trajectory.newSizes.byteLength +
    trajectory.allPens.byteLength +
    trajectory.pens.byteLength +
    trajectory.nears.byteLength;
  assert.equal(trajectoryByteLength(snapped), snapped.states.byteLength * 2 + auxiliaries(snapped));
  assert.equal(trajectoryByteLength(free), free.states.byteLength + auxiliaries(free));
  assert.equal(snapped.rawStates === snapped.states, false);
  assert.equal(free.rawStates === free.states, true);
});

test("snap correction approaches every target monotonically through the landing interval", () => {
  const configured = crowdedRequest(16);
  configured.mode = "snap";
  configured.physics = { ...configured.physics, maxSpeed: 10 };
  const trajectory = buildTrajectory(configured);
  const landingStep = Math.floor(configured.physics.tightenFrom * configured.steps);
  const squareCount = trajectory.n + 1;
  for (let square = 0; square < squareCount; square++) {
    const targetSquare = configured.target.squares[square];
    assert(targetSquare !== undefined);
    let previousError = Number.POSITIVE_INFINITY;
    for (let step = landingStep; step <= trajectory.steps; step++) {
      const offset = (step * squareCount + square) * 3;
      const error = Math.hypot(
        trajectoryStateAt(trajectory, offset) - targetSquare[0],
        trajectoryStateAt(trajectory, offset + 1) - targetSquare[1],
      );
      assert(
        error <= previousError + 1e-12,
        `square ${square} moved away from its target at correction step ${step}`,
      );
      previousError = error;
    }
  }
});
