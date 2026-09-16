import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { test } from "node:test";
import { analyzeMotionTrace, type MotionFrame } from "../tools/kinetics-metrics.ts";
import {
  assertKineticsPoseSampleBudget,
  MAX_KINETICS_POSE_SAMPLES,
  MAX_KINETICS_PRESENTATION_FRAMES,
  MAX_KINETICS_STORED_FRAMES,
} from "../tools/measure-kinetics.ts";

function frames(xs: readonly number[], secondsPerFrame = 1): MotionFrame[] {
  return xs.map((x, index) => ({
    timeSeconds: index * secondsPerFrame,
    containerSide: 10,
    poses: [{ x, y: 0, angleRadians: 0 }],
  }));
}

test("constant velocity is the smooth negative control", () => {
  const summary = analyzeMotionTrace({ frames: frames([0, 1, 2, 3, 4]) });
  assert.equal(summary.translation.displacement.maximum, 1);
  assert.equal(summary.translation.speed.maximum, 1);
  assert.equal(summary.translation.acceleration.maximum, 0);
  assert.equal(summary.translation.jerk.maximum, 0);
  assert.deepEqual(summary.translation.reversals, {
    count: 0,
    opportunities: 3,
    ratio: 0,
    minimumDisplacementUnits: 1e-6,
  });
});

test("a synthetic cap-to-cap trace makes every eligible turn reverse", () => {
  const summary = analyzeMotionTrace({
    frames: frames([0, 1, 0, 1, 0]),
    landingStartTimeSeconds: 3,
  });
  assert.equal(summary.translation.reversals.count, 3);
  assert.equal(summary.translation.reversals.opportunities, 3);
  assert.equal(summary.translation.reversals.ratio, 1);
  assert.equal(summary.translation.acceleration.maximum, 2);
  assert.equal(summary.translation.jerk.maximum, 4);
  assert.deepEqual(summary.translation.localization.largestDisplacement, {
    squareIndex: 0,
    endingFrameIndex: 1,
    endingTimeSeconds: 1,
    displacement: 1,
  });
  assert.deepEqual(summary.translation.localization.strongestReversal, {
    squareIndex: 0,
    endingFrameIndex: 2,
    endingTimeSeconds: 2,
    cosine: -1,
    previousDisplacement: 1,
    displacement: 1,
  });
  assert.equal(summary.translation.localization.preLanding?.displacement.count, 2);
  assert.equal(summary.translation.localization.preLanding?.reversals.count, 1);
  assert.equal(summary.translation.localization.landing?.displacement.count, 2);
  assert.equal(summary.translation.localization.landing?.reversals.count, 2);
  assert.equal(summary.translation.localization.finalInterval.displacement.maximum, 1);
  assert.equal(summary.translation.localization.finalInterval.reversals.count, 1);
});

test("invisible poses do not create fictitious displayed motion", () => {
  const summary = analyzeMotionTrace({
    frames: [
      {
        timeSeconds: 0,
        containerSide: 10,
        poses: [{ x: 9, y: 9, angleRadians: 0, active: false }],
      },
      {
        timeSeconds: 1,
        containerSide: 10,
        poses: [{ x: 1, y: 1, angleRadians: 0 }],
      },
      {
        timeSeconds: 2,
        containerSide: 10,
        poses: [{ x: 2, y: 1, angleRadians: 0 }],
      },
    ],
  });
  assert.equal(summary.translation.displacement.count, 1);
  assert.equal(summary.translation.displacement.maximum, 1);
  assert.equal(summary.translation.acceleration.count, 0);
  assert.equal(summary.translation.appearances.count, 1);
  assert.equal(summary.translation.appearances.reportedPoseDisplacement.maximum, 11.31370849898);
});

test("geometry metrics distinguish contact, separation, and penetration", () => {
  const summary = analyzeMotionTrace({
    frames: [
      {
        timeSeconds: 0,
        containerSide: 4,
        poses: [
          { x: 1, y: 1, angleRadians: 0 },
          { x: 2, y: 1, angleRadians: 0 },
        ],
      },
      {
        timeSeconds: 1,
        containerSide: 4,
        poses: [
          { x: 1, y: 1, angleRadians: 0 },
          { x: 2.2, y: 1, angleRadians: 0 },
        ],
      },
      {
        timeSeconds: 2,
        containerSide: 4,
        poses: [
          { x: 1, y: 1, angleRadians: 0 },
          { x: 1.8, y: 1, angleRadians: 0 },
        ],
      },
    ],
  });
  assert.deepEqual(summary.presentedGeometry.contactPairs, {
    maximum: 1,
    mean: 0.3333333333333,
    final: 0,
  });
  assert.equal(summary.presentedGeometry.nearestNeighborGap.minimum, -0.2);
  assert.equal(summary.presentedGeometry.nearestNeighborGap.maximum, 0.2);
  assert.equal(summary.presentedGeometry.pairPenetration.maximum, 0.2);
  assert.equal(summary.presentedGeometry.wallPenetration.maximum, 0);
});

test("endpoint error is measured in the trace square order", () => {
  const summary = analyzeMotionTrace({
    frames: frames([0, 0.5, 1]),
    target: [{ x: 1.25, y: 0, angleRadians: 0 }],
  });
  assert(summary.endpoint !== null);
  assert.equal(summary.endpoint.maximumCenterError, 0.25);
  assert.equal(summary.endpoint.rootMeanSquareCenterError, 0.25);
  assert.equal(summary.endpoint.maximumAngleErrorRadians, 0);
});

test("the CLI makes a static step's nonphysical behavior explicit", () => {
  const packageRoot = resolve(import.meta.dirname, "..");
  const stdout = execFileSync(
    process.execPath,
    [
      resolve(packageRoot, "tools/measure-kinetics.ts"),
      "--corpus",
      resolve(packageRoot, "tests/fixtures/corpus.json"),
      "--instance",
      "2",
      "--solver",
      "physics",
      "--law",
      "default",
      "--anneal",
      "3",
      "--timing",
      "0,0.2,0.1,0",
      "--steps-per-second",
      "1e308",
      "--seed",
      "17",
      "--frames",
    ],
    { encoding: "utf8" },
  );
  const report = JSON.parse(stdout);
  assert.equal(report.schema, "squares.workbench.kinetics/v1");
  assert.deepEqual(report.units, {
    position: "square-side",
    angle: "radian",
    time: "second",
    speed: "square-side/second",
    acceleration: "square-side/second^2",
    jerk: "square-side/second^3",
  });
  assert.deepEqual(report.configuration, {
    solver: "tween",
    requestedSolver: "physics",
    mode: "not_applicable",
    phase: "add-then-move",
    law: "not_applicable",
    wallLaw: "not_applicable",
    anneal: "not_applicable",
    timing: { dwell: 0, move: 0.2, correct: 0.1, settle: 0 },
    solverDurationSeconds: 0.3,
    presentationDurationSeconds: 0.3,
    instance: 2,
    transition: { from: 1, to: 2, pairIndex: 0 },
    seed: 17,
    effectiveSeed: "not_applicable",
    stepsPerSecond: "not_applicable",
    presentationSampleRate: 60,
    containerDelayFraction: 0.2,
    integrationSubsteps: "not_applicable",
    steps: "not_applicable",
    presentationSteps: 18,
  });
  assert.equal(report.frames.length, 19);
  assert.equal(report.frames[0].poses.length, 2);
  assert.equal(report.frames[0].poses[1].active, false);
  const firstVisible = report.frames.find(
    (frame: { poses: Array<{ active?: boolean; size: number }> }) =>
      frame.poses[1]?.active === true,
  );
  assert.ok(firstVisible !== undefined);
  const arriving = firstVisible.poses[1];
  assert.ok(arriving !== undefined);
  assert.ok(arriving.size >= 0.8 && arriving.size < 1);
  assert.equal(report.summary.samples.frames, 19);
  assert.equal(report.summary.translation.appearances.count, 1);
  assert.equal(report.summary.endpoint.maximumCenterError, 0);
  assert.equal(report.determinism.identical, true);
  assert.equal(report.determinism.comparedFrames, 19);
  assert.equal(report.work.storedSteps, "not_applicable");
  assert.equal(report.work.integrationSteps, 0);
  assert(report.runtime.wallMilliseconds >= 0);
  assert.deepEqual(
    JSON.parse(readFileSync(resolve(packageRoot, "tests/fixtures/corpus.json"), "utf8")).schema,
    "squares.workbench.corpus/v1",
  );
});

test("the CLI executes a matched physical trajectory and exposes integration work", () => {
  const packageRoot = resolve(import.meta.dirname, "..");
  const corpus = JSON.parse(
    readFileSync(resolve(packageRoot, "tests/fixtures/corpus.json"), "utf8"),
  );
  corpus.pairs[0].kind = "matched";
  corpus.frames["1"].squares[0][2] = 30;
  corpus.frames["2"].squares[corpus.pairs[0].map[0]][2] = 40;
  const directory = mkdtempSync(resolve(tmpdir(), "squares-kinetics-test-"));
  const corpusPath = resolve(directory, "corpus.json");
  try {
    writeFileSync(corpusPath, JSON.stringify(corpus));
    const report = JSON.parse(
      execFileSync(
        process.execPath,
        [
          resolve(packageRoot, "tools/measure-kinetics.ts"),
          "--corpus",
          corpusPath,
          "--instance",
          "2",
          "--solver",
          "physics",
          "--law",
          "rigid",
          "--anneal",
          "3",
          "--timing",
          "0,0.2,0.1,0",
          "--seed",
          "17",
          "--frames",
        ],
        { encoding: "utf8" },
      ),
    );
    assert.equal(report.configuration.solver, "physics");
    assert.equal(report.configuration.law, "rigid");
    assert.equal(report.configuration.integrationSubsteps, "adaptive");
    assert.equal(report.physical.applicable, true);
    assert.equal(report.work.applicable, true);
    assert(report.work.integrationSteps >= report.work.storedSteps);
    assert(report.work.substepsPerStoredStep >= 1);
    assert.deepEqual(report.work.integration, {
      requested: "adaptive",
      effective: report.work.substepsPerStoredStep,
      recommended: 13,
      warning: "below-adaptive-stability-bound",
    });
    const presentedAngles = report.frames
      .slice(1, -1)
      .map(
        (frame: { poses: [{ angleRadians: number }, ...{ angleRadians: number }[]] }) =>
          frame.poses[0].angleRadians,
      );
    assert(Math.max(...presentedAngles) > 0.1);
    assert(Math.max(...presentedAngles) < Math.PI);
  } finally {
    rmSync(directory, { recursive: true });
  }
});

test("the CLI rejects stored and presentation frame counts before allocating them", async (t) => {
  const packageRoot = resolve(import.meta.dirname, "..");
  const command = resolve(packageRoot, "tools/measure-kinetics.ts");
  const corpus = JSON.parse(
    readFileSync(resolve(packageRoot, "tests/fixtures/corpus.json"), "utf8"),
  );
  corpus.pairs[0].kind = "matched";
  const directory = mkdtempSync(resolve(tmpdir(), "squares-kinetics-budget-test-"));
  const corpusPath = resolve(directory, "corpus.json");
  writeFileSync(corpusPath, JSON.stringify(corpus));
  const common = [
    command,
    "--corpus",
    corpusPath,
    "--instance",
    "2",
    "--solver",
    "physics",
    "--timing",
    "0,1,0,0",
  ];
  try {
    await t.test("stored frame budget", () => {
      const result = spawnSync(
        process.execPath,
        [...common, "--steps-per-second", String(MAX_KINETICS_STORED_FRAMES)],
        { encoding: "utf8" },
      );
      assert.equal(result.status, 2);
      assert.match(
        result.stderr,
        new RegExp(`stored frame budget exceeded: .* maximum ${MAX_KINETICS_STORED_FRAMES}`),
      );
    });

    await t.test("unsafe stored frame count", () => {
      const result = spawnSync(process.execPath, [...common, "--steps-per-second", "1e308"], {
        encoding: "utf8",
      });
      assert.equal(result.status, 2);
      assert.match(result.stderr, /stored frame count is not a safe finite integer/);
    });

    await t.test("presentation frame budget", () => {
      const result = spawnSync(
        process.execPath,
        [...common, "--sample-rate", String(MAX_KINETICS_PRESENTATION_FRAMES)],
        { encoding: "utf8" },
      );
      assert.equal(result.status, 2);
      assert.match(
        result.stderr,
        new RegExp(
          `presentation frame budget exceeded: .* maximum ${MAX_KINETICS_PRESENTATION_FRAMES}`,
        ),
      );
    });

    await t.test("unsafe presentation frame count", () => {
      const result = spawnSync(process.execPath, [...common, "--sample-rate", "1e308"], {
        encoding: "utf8",
      });
      assert.equal(result.status, 2);
      assert.match(result.stderr, /presentation frame count is not a safe finite integer/);
    });
  } finally {
    rmSync(directory, { recursive: true });
  }
});

test("the CLI bounds combined trace pose samples at the maximum corpus size", () => {
  const squareCount = 325;
  const safeFrames = Math.floor(MAX_KINETICS_POSE_SAMPLES / squareCount);
  assert.doesNotThrow(() => assertKineticsPoseSampleBudget(squareCount, safeFrames, null));
  assert.throws(
    () => assertKineticsPoseSampleBudget(squareCount, safeFrames + 1, null),
    /kinetics pose-sample budget exceeded/,
  );
  assert.throws(
    () => assertKineticsPoseSampleBudget(squareCount, 2, Math.ceil(safeFrames / 2)),
    /kinetics pose-sample budget exceeded/,
  );
});

test("the CLI rejects finite timing spans whose computed frame count overflows", () => {
  const packageRoot = resolve(import.meta.dirname, "..");
  const result = spawnSync(
    process.execPath,
    [
      resolve(packageRoot, "tools/measure-kinetics.ts"),
      "--corpus",
      resolve(packageRoot, "tests/fixtures/corpus.json"),
      "--instance",
      "2",
      "--timing",
      "0,1e308,0,0",
    ],
    { encoding: "utf8" },
  );
  assert.equal(result.status, 2);
  assert.match(result.stderr, /presentation frame count is not a safe finite integer/);
});
