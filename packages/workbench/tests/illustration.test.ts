import assert from "node:assert/strict";
import { test } from "node:test";
import {
  type IllustrationInput,
  illustrationFrame,
  interpolateBlockPose,
  type MotionTrack,
} from "../src/animation/illustration.ts";
import {
  type PairSchedule,
  pairSchedule,
  type TimelineConfiguration,
} from "../src/animation/timeline.ts";
import { captureIllustration, captureTimes } from "../src/app/capture.ts";
import {
  DEFAULT_ARRIVAL_DELAY_FRACTION,
  DEFAULT_STEP_TIMING,
  NEW_FRACTION,
} from "../src/motion-settings.ts";
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
    arrive: 3.2,
    arrived: 4,
    containerStart: 1,
    containerEnd: 1.6,
    blocksStart: 1,
    blocksEnd: 3,
    roll: 0.4,
  },
  seconds: 0,
  moveSeconds: 3,
  padding: 0.045,
  drain: 0,
  resting: 1,
  homeward: 0,
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

test("an illustration resizes the container, waits, then fades the square in at full size", () => {
  const before = seek(0).scene;
  const resizing = seek(1.3).scene;
  const moving = seek(2).scene;
  const waiting = seek(3.1).scene;
  const fading = seek(3.6).scene;
  const arrived = seek(4).scene;
  const end = seek(5).scene;
  assert.equal(before.containerSide, 1);
  assert.equal(before.squares[1]?.opacity, 0);
  assert.ok(resizing.containerSide > 1 && resizing.containerSide < 2);
  assert.equal(resizing.squares[1]?.opacity, 0);
  assert.equal(moving.squares[0]?.angleDegrees, 45);
  assert.equal(moving.containerSide, 2);
  assert.equal(moving.squares[1]?.opacity, 0);
  // The resize is over and the delay is not: the picture has shrunk and nothing has arrived.
  assert.equal(waiting.containerSide, 2);
  assert.equal(waiting.squares[1]?.opacity, 0);
  assert.equal(waiting.presentation.mark, null);
  const square = fading.squares[1];
  assert.ok(square !== undefined && square.opacity > 0 && square.opacity < 1);
  assert.deepEqual([square.x, square.y, square.angleDegrees, square.scale], [0.5, 1.5, 0, 1]);
  assert.equal(fading.presentation.mark?.scale, 1);
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

function defaultConfiguration(): TimelineConfiguration {
  return {
    pairs: [{ n: 2, kind: "matched" }],
    timing: { ...DEFAULT_STEP_TIMING },
    continuous: {
      on: false,
      fullBeat: false,
      beat: { ...DEFAULT_STEP_TIMING },
      staticBeat: { ...DEFAULT_STEP_TIMING },
    },
    anneal: 3,
    phase: "add-then-move",
    arrivalFraction: 0.3,
    newFraction: NEW_FRACTION,
    rollMax: 0.4,
    arrivalDelay: DEFAULT_ARRIVAL_DELAY_FRACTION,
  };
}

/** Every 60 Hz instant of a step, plus the schedule's own instants, in order. */
function instants(schedule: PairSchedule): number[] {
  const ticks = Array.from({ length: Math.floor(schedule.end * 60) + 1 }, (_, frame) => frame / 60);
  const named = Object.entries(schedule)
    .filter(([key]) => key !== "roll")
    .map(([, value]) => value);
  return [...ticks, ...named].sort((a, b) => a - b);
}

//: The largest opacity change the default fade may make between two 60 Hz frames. The ease's
//: steepest slope is 1.5 per fade, and the default fade is 0.4 of the moving span -- 0.24 s since
//: the move beat went from 0.5 s to 0.4 s on 2026-09-22 (it was 0.28 s, and 0.36 s before the
//: correct beat halved on 2026-09-17) -- so 1.5 / 0.24 / 60 = 0.1042 is what it takes; the cubic
//: ease-out it replaced jumped 0.17 on its first frame. Both bounds here are the arithmetic of
//: the beat, not a tolerance: shorten the span and they rise, which is why they are derived in
//: this comment rather than nudged until the test passes.
const LARGEST_OPACITY_STEP = 0.105;
//: The most the first visible 60 Hz frame may show: it lands at most 1/60 s into the 0.24 s fade,
//: 0.0694 of it, where the smoothstep is 0.0138. At the 0.28 s fade this bound was 0.011.
const FIRST_VISIBLE_OPACITY = 0.014;

test("in every phase the new square fades in smoothly, at full size and in place", () => {
  const configuration = defaultConfiguration();
  for (const phase of ["add-then-move", "move-then-add", "simultaneous"] as const) {
    configuration.phase = phase;
    const schedule = pairSchedule(configuration, 0, "tween");
    const frames = instants(schedule).map((seconds) => ({
      seconds,
      square: illustrationFrame({ ...input, phase, schedule, seconds }).squares[1],
    }));
    let previous = 0;
    let firstVisible: number | null = null;
    const ticks = frames.filter(
      ({ seconds }) => Math.abs(seconds * 60 - Math.round(seconds * 60)) < 1e-9,
    );
    for (const { seconds, square } of frames) {
      assert.ok(square !== undefined);
      assert.equal(square.scale, 1, `${phase}: scaled at ${seconds}`);
      assert.deepEqual([square.x, square.y, square.angleDegrees], [0.5, 1.5, 0]);
      assert.ok(square.opacity >= previous, `${phase}: opacity fell at ${seconds}`);
      if (seconds <= schedule.arrive) {
        assert.equal(square.opacity, 0, `${phase}: visible before the delay ended at ${seconds}`);
      }
      if (square.opacity > 0 && firstVisible === null) {
        firstVisible = square.opacity;
      }
      previous = square.opacity;
    }
    assert.equal(previous, 1);
    // A smooth start: the first visible frame is nearly transparent.
    assert.ok(
      firstVisible !== null && firstVisible < FIRST_VISIBLE_OPACITY,
      `${phase}: first ${firstVisible}`,
    );
    const steps = ticks
      .slice(1)
      .map(({ square }, index) => (square?.opacity ?? 0) - (ticks[index]?.square?.opacity ?? 0));
    assert.ok(Math.max(...steps) <= LARGEST_OPACITY_STEP, `${phase}: steps ${Math.max(...steps)}`);
    // Symmetric: half way through the fade the square is half in.
    const middle = illustrationFrame({
      ...input,
      phase,
      schedule,
      seconds: (schedule.arrive + schedule.arrived) / 2,
    }).squares[1];
    assert.ok(middle !== undefined && Math.abs(middle.opacity - 0.5) < 1e-12);
  }
});

test("the arrival delay moves the fade and never the resize, which stays smooth at 60 Hz", () => {
  const configuration = defaultConfiguration();
  const sides: number[][] = [];
  const arrivals: number[] = [];
  for (const delay of [0, DEFAULT_ARRIVAL_DELAY_FRACTION, 0.6]) {
    configuration.arrivalDelay = delay;
    const schedule = pairSchedule(configuration, 0, "tween");
    const drawn: number[] = [];
    for (let frame = 0; frame / 60 <= schedule.containerEnd; frame++) {
      drawn.push(illustrationFrame({ ...input, schedule, seconds: frame / 60 }).containerSide);
    }
    drawn.push(
      illustrationFrame({ ...input, schedule, seconds: schedule.containerEnd }).containerSide,
    );
    sides.push(drawn);
    const seen = instants(schedule).find(
      (seconds) =>
        (illustrationFrame({ ...input, schedule, seconds }).squares[1]?.opacity ?? 0) > 0,
    );
    // The delay is a share of the moving span, not seconds: the old `delay * 0.9` only matched the
    // delay in seconds while the span was 0.9 s, before the correct beat shrank to 0.2 s.
    const span = configuration.timing.move + configuration.timing.correct;
    assert.ok(Math.abs(schedule.arrive - schedule.containerEnd - delay * span) < 1e-12);
    assert.ok(seen !== undefined && seen > schedule.arrive);
    arrivals.push(seen);
    const steps = drawn.slice(1).map((side, index) => side - (drawn[index] ?? side));
    // The resize takes `CONTAINER_RESIZE_FRACTION` of the moving span, so its per-frame step is
    // inversely proportional to that span: 0.22 held while the span was 0.7 s, and the same
    // motion over the 0.6 s span of the 2026-09-22 beat measures 0.2519. The bound is the
    // arithmetic of the beat, not a tolerance.
    assert.ok(Math.min(...steps) >= 0 && Math.max(...steps) < 0.26, `max ${Math.max(...steps)}`);
    assert.equal(drawn.at(-1), input.toSide);
  }
  assert.deepEqual(sides[1], sides[0]);
  assert.deepEqual(sides[2], sides[0]);
  assert.ok((arrivals[0] ?? 0) < (arrivals[1] ?? 0) && (arrivals[1] ?? 0) < (arrivals[2] ?? 0));
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
  for (const [index, expected] of [-0.09, -2.09, 2.18, 2.18].entries()) {
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

test("captured SVG frames fade the new square in without ever scaling it", async () => {
  const written: string[] = [];
  const arrival = {
    ...timing,
    startSeconds: 3,
    durationSeconds: 1,
    framesPerSecond: 10,
    maxFrames: 11,
  };
  const receipt = await captureIllustration({
    source,
    timing: arrival,
    seek,
    cancelled: () => false,
    writeFrame: async (frame) => {
      written.push(frame.svg);
    },
  });
  assert.equal(receipt.status, "completed");
  const opacities = written.map((svg) => {
    // The only scale in a frame is the stage's own y-flip; no square is ever scaled.
    assert.doesNotMatch(svg, /rotate\([^)]*\) scale\(/);
    const found =
      /data-identity="2" transform="translate\(0\.5 1\.5\) rotate\(0\)" opacity="([^"]+)"/.exec(
        svg,
      );
    assert.ok(found !== null, svg);
    return Number(found[1]);
  });
  assert.deepEqual(opacities.slice(0, 3), [0, 0, 0]);
  assert.ok(
    opacities.every((opacity, index) => index === 0 || opacity >= (opacities[index - 1] ?? 0)),
  );
  assert.equal(opacities.at(-1), 1);
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
