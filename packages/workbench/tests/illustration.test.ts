import assert from "node:assert/strict";
import { test } from "node:test";
import {
  type IllustrationInput,
  illustrationFrame,
  interpolateBlockPose,
  type MotionTrack,
} from "../src/animation/illustration.ts";
import { pairSchedule, type TimelineConfiguration } from "../src/animation/timeline.ts";
import { captureIllustration, captureTimes } from "../src/app/capture.ts";
import type { PaintedSceneFrame } from "../src/view/scene-types.js";
import {
  type AttributeTarget,
  renderStage,
  type StageTargets,
  sceneSvg,
} from "../src/view/stage-renderer.ts";

const track: MotionTrack = {
  ident: 1,
  a: [0.5, 0.5, 0],
  b: [1.5, 0.5, 90],
  turn: 90,
  block: null,
  dx: 0,
  dy: 0,
  rx: 0,
  ry: 0,
};
const input: IllustrationInput = {
  pairIndex: 0,
  n: 2,
  fromSide: 1,
  toSide: 2,
  tracks: [track],
  arriving: { identity: 2, pose: [0.5, 1.5, 0] },
  previousIndex: 0,
  phase: "move-then-add",
  schedule: {
    moveStart: 1,
    moveEnd: 4,
    end: 5,
    arrive: 3,
    arrived: 4,
    containerStart: 3.2,
    containerEnd: 4,
    blocksStart: 1,
    blocksEnd: 3,
    roll: 0.4,
  },
  seconds: 0,
  moveSeconds: 3,
  padding: 0.045,
  drain: 0,
  resting: 1,
  links: true,
  tint: 1,
  mark: { wide: 4, thin: 2, fade: 0.15 },
};

function seek(seconds: number): PaintedSceneFrame {
  return { scene: illustrationFrame({ ...input, seconds }), fills: ["#123456", "#abcdef"] };
}

class Target implements AttributeTarget {
  readonly attributes = new Map<string, string>();
  setAttribute(name: string, value: string): void {
    this.attributes.set(name, value);
  }
}

function stage(): StageTargets & { svg: Target } {
  return {
    svg: new Target(),
    containerRect: new Target(),
    squares: new Map(
      [1, 2, 3].map((identity) => [identity, { node: new Target(), shape: new Target() }]),
    ),
    mark: new Target(),
    markShape: new Target(),
    links: new Target(),
    ghost: new Target(),
  };
}

test("an illustration presents the arriving square before the delayed container resize", () => {
  const before = seek(0).scene;
  const moving = seek(2).scene;
  const squareFirst = seek(3.1).scene;
  const resizing = seek(3.3).scene;
  const arrived = seek(4).scene;
  const end = seek(5).scene;
  assert.equal(before.containerSide, 1);
  assert.equal(before.squares[1]?.opacity, 0);
  assert.equal(moving.squares[0]?.angleDegrees, 45);
  assert.equal(moving.containerSide, 1);
  assert.equal(moving.squares[1]?.opacity, 0);
  assert.ok((squareFirst.squares[1]?.opacity ?? 0) > 0);
  assert.equal(squareFirst.containerSide, 1);
  assert.ok(resizing.containerSide > 1);
  assert.equal(arrived.squares[1]?.opacity, 1);
  assert.equal(arrived.containerSide, 2);
  assert.deepEqual(
    end.squares.map(({ x, y, angleDegrees }) => [x, y, angleDegrees]),
    [
      [1.5, 0.5, 90],
      [0.5, 1.5, 0],
    ],
  );
  assert.equal(end.presentation.newTint, 0);
  assert.equal(end.motion, "direct-illustration");
  assert.deepEqual(seek(2), seek(2));
});

test("a resize delayed to the move boundary remains continuous through settle", () => {
  const delayed = (seconds: number) =>
    illustrationFrame({
      ...input,
      seconds,
      schedule: {
        ...input.schedule,
        containerStart: input.schedule.moveEnd,
        containerEnd: 4.5,
      },
    });
  assert.equal(delayed(4).containerSide, 1);
  assert.ok(delayed(4 + Number.EPSILON * 4).containerSide >= 1);
  assert.ok(delayed(4.25).containerSide > 1);
  assert.ok(delayed(4.25).containerSide < 2);
  assert.equal(delayed(4.5).containerSide, 2);
});

test("adjacent late delay settings retain the same smooth 60 Hz resize", () => {
  const timing = { dwell: 0, move: 0.55, correct: 0.25, settle: 0.8 };
  const configuration: TimelineConfiguration = {
    pairs: [{ n: 2, kind: "matched" }],
    timing,
    continuous: { on: false, fullBeat: false, beat: timing, staticBeat: timing },
    anneal: 3,
    phase: "move-then-add",
    arrivalFraction: 0.3,
    newFraction: 1 / 3,
    rollMax: 0.4,
  };
  const maximumSteps: number[] = [];
  for (const delay of [0.25, 0.3]) {
    configuration.containerDelay = delay;
    const schedule = pairSchedule(configuration, 0, "tween");
    const sides: number[] = [];
    for (
      let seconds = schedule.containerStart;
      seconds < schedule.containerEnd;
      seconds += 1 / 60
    ) {
      sides.push(illustrationFrame({ ...input, schedule, seconds }).containerSide);
    }
    sides.push(
      illustrationFrame({ ...input, schedule, seconds: schedule.containerEnd }).containerSide,
    );
    maximumSteps.push(
      Math.max(...sides.slice(1).map((side, index) => side - (sides[index] ?? side))),
    );
  }
  const first = maximumSteps[0];
  const second = maximumSteps[1];
  assert.ok(first !== undefined && second !== undefined);
  assert.ok(first < 0.22);
  assert.ok(second < 0.22);
  assert.ok(Math.abs(first - second) < 1e-12);

  configuration.timing.settle = 0;
  configuration.continuous.beat.settle = 0;
  configuration.continuous.staticBeat.settle = 0;
  const noSettle = pairSchedule(configuration, 0, "tween");
  assert.ok(noSettle.containerEnd > noSettle.moveEnd);
  const start = illustrationFrame({
    ...input,
    schedule: noSettle,
    seconds: noSettle.containerStart,
  }).containerSide;
  const firstFrame = illustrationFrame({
    ...input,
    schedule: noSettle,
    seconds: noSettle.containerStart + 1 / 60,
  }).containerSide;
  assert.equal(start, input.fromSide);
  assert.ok(firstFrame > start && firstFrame - start < 0.22);
});

test("block members follow a common pivot with their own target residual", () => {
  const member: MotionTrack = {
    ...track,
    a: [2, 1, 0],
    b: [3.1, 4, 90],
    block: { from: [1, 1], to: [3, 3], turn: 90 },
    dx: 1,
    rx: 0.1,
  };
  assert.deepEqual(interpolateBlockPose(member, { rot: 0, slide: 0 }), [2, 1, 0]);
  assert.deepEqual(interpolateBlockPose(member, { rot: 1, slide: 1 }), [3.1, 4, 90]);
  const middle = interpolateBlockPose(member, { rot: 0.5, slide: 0.5 });
  assert.ok(Math.abs(middle[0] - (2 + Math.SQRT1_2 + 0.05)) < 1e-12);
  assert.ok(Math.abs(middle[1] - (2 + Math.SQRT1_2)) < 1e-12);
});

test("zero duration arrival is a deterministic step and the previous mark disappears", () => {
  const sampled = illustrationFrame({
    ...input,
    seconds: 1,
    moveSeconds: 0,
    schedule: {
      moveStart: 1,
      moveEnd: 1,
      end: 1,
      arrive: 1,
      arrived: 1,
      containerStart: 1,
      containerEnd: 1,
      blocksStart: 1,
      blocksEnd: 1,
      roll: 0,
    },
  });
  assert.equal(sampled.squares[1]?.opacity, 1);
  assert.equal(sampled.presentation.mark?.x, 0.5);
  assert.equal(sampled.presentation.newTint, 0);
});

test("DOM and standalone SVG use the same transforms and reject bad input before painting", () => {
  const targets = stage();
  const frame = seek(2);
  renderStage(targets, frame);
  const view = targets.svg.attributes.get("viewBox")?.split(" ").map(Number);
  assert.ok(view !== undefined);
  for (const [index, expected] of [-0.045, -1.045, 1.09, 1.09].entries()) {
    const observed = view[index];
    assert.ok(observed !== undefined && Math.abs(observed - expected) < 1e-12);
  }
  const output = sceneSvg(frame);
  assert.match(output, /transform="translate\(1 0\.5\) rotate\(45\)"/);
  assert.match(output, /data-identity="2".*opacity="0"/);
  assert.doesNotMatch(output, /numerically-checked|certified/);
  const blank = stage();
  assert.throws(() => renderStage(blank, { ...frame, fills: ["#fff000"] }), /every scene square/);
  assert.equal(blank.svg.attributes.size, 0);
  assert.throws(() => sceneSvg({ ...frame, fills: ['" onload="evil', "#ffffff"] }), /hex colour/);
});

const timing = {
  startSeconds: 1,
  durationSeconds: 1,
  framesPerSecond: 4,
  includeEndpoint: true,
  maxFrames: 5,
};
const source = { commit: "a".repeat(40), inputId: "fixture-1-to-2", configurationId: "direct-v1" };

test("capture clock is bounded, has an explicit endpoint and never accumulates tick error", () => {
  assert.deepEqual(captureTimes(timing), [1, 1.25, 1.5, 1.75, 2]);
  assert.deepEqual(captureTimes({ ...timing, includeEndpoint: false }), [1, 1.25, 1.5, 1.75]);
  assert.deepEqual(captureTimes({ ...timing, durationSeconds: 0 }), [1]);
  assert.deepEqual(
    captureTimes({
      ...timing,
      startSeconds: 0,
      durationSeconds: 0.14,
      framesPerSecond: 100,
      maxFrames: 15,
    }).slice(-2),
    [0.13, 0.14],
  );
  assert.throws(() => captureTimes({ ...timing, maxFrames: 4 }), /frame budget/);
  assert.throws(() => captureTimes({ ...timing, framesPerSecond: Number.NaN }), /capture requires/);
});

test("capture and interactive seek agree at every frame with no simulation dependency", async () => {
  const written: string[] = [];
  const receipt = await captureIllustration({
    source,
    timing,
    seek,
    cancelled: () => false,
    writeFrame: async (frame) => {
      written.push(frame.svg);
    },
  });
  assert.equal(receipt.status, "completed");
  assert.equal(receipt.scheduledFrames, 5);
  assert.deepEqual(
    written,
    captureTimes(timing).map((seconds) => sceneSvg(seek(seconds))),
  );
  assert.equal(receipt.frames.length, 5);
  assert.deepEqual(receipt.source, source);
});

test("capture cancellation preserves exactly the frames already written", async () => {
  let written = 0;
  const receipt = await captureIllustration({
    source,
    timing,
    seek,
    cancelled: () => written === 2,
    writeFrame: async () => {
      written++;
    },
  });
  assert.equal(receipt.status, "cancelled");
  assert.equal(receipt.scheduledFrames, 5);
  assert.deepEqual(
    receipt.frames.map((frame) => frame.seconds),
    [1, 1.25],
  );
});

test("a failed frame write retains the completed prefix and records the failure", async () => {
  let writes = 0;
  const receipt = await captureIllustration({
    source,
    timing,
    seek,
    cancelled: () => false,
    writeFrame: async () => {
      if (writes++ === 1) {
        throw new Error("capture storage full");
      }
    },
  });
  assert.equal(receipt.status, "failed");
  assert.equal(receipt.error, "capture storage full");
  assert.equal(receipt.frames.length, 1);
  assert.equal(receipt.scheduledFrames, 5);
});
