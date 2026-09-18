import assert from "node:assert/strict";
import { test } from "node:test";
import {
  annealSpan,
  baseTiming,
  CONTAINER_RESIZE_FRACTION,
  continuousTiming,
  displayedCount,
  isSpedUpPair,
  type PairSchedule,
  pairDuration,
  pairSchedule,
  pairTiming,
  phaseProgress,
  ramp,
  rangeDuration,
  rangeProgress,
  SIMPLE_TRANSITION_SPEED,
  seekSequence,
  sequenceDuration,
  type TimelineConfiguration,
} from "../src/animation/timeline.ts";
import {
  ARRIVAL_DELAY_BOUNDS,
  DEFAULT_ARRIVAL_DELAY_FRACTION,
  DEFAULT_STEP_TIMING,
  NEW_FRACTION,
  TWEEN_ILLUSTRATION_SETTINGS,
} from "../src/motion-settings.ts";

function configuration(): TimelineConfiguration {
  const timing = { dwell: 0.8, move: 0.55, correct: 0.25, settle: 0.8 };
  return {
    pairs: [
      { n: 1, kind: "prefix" },
      { n: 2, kind: "matched" },
      { n: 16, kind: "shared-picture" },
      { n: 17, kind: "matched" },
    ],
    timing,
    continuous: {
      on: true,
      fullBeat: false,
      beat: timing,
      staticBeat: { dwell: 0.4, move: 0.28, correct: 0.12, settle: 0.35 },
    },
    anneal: 3,
    phase: "add-then-move",
    arrivalFraction: 0.3,
    newFraction: 0.4,
    rollMax: 0.4,
  };
}

function near(actual: number, expected: number): void {
  assert.ok(Math.abs(actual - expected) < 1e-12, `${actual} != ${expected}`);
}

const PHASES = [
  "add-then-move",
  "move-then-add",
  "simultaneous",
  "rotate-first",
  "slide-first",
] as const;
const STYLES = ["tween", "physics", "bodies"] as const;

// With no arrival delay, an add-then-move step's move is the resize (0.3 of the moving span), the
// fade (0.4) and the blocks: 0.7 of the span illustrated, all of it simulated. So a step lasts
// dwell + 1.4 spans + settle under the tween and dwell + 1.7 spans + settle under physics.
test("four-span timing preserves correction in single, continuous and annealed paths", () => {
  const config = configuration();
  near(pairDuration(config, 0, "tween"), 0.4 + 1.4 * 0.4 + 0.35);
  near(pairDuration(config, 1, "physics"), 0.8 + 1.7 * 0.8 + 0.8);
  config.anneal = 8;
  near(pairDuration(config, 1, "physics"), 0.8 + 1.7 * 1.2 + 0.8);
  near(pairDuration(config, 1, "tween"), 0.8 + 1.4 * 0.8 + 0.8);
  near(continuousTiming(config, 0, "bodies").correct, 0.12);
  config.continuous.on = false;
  near(pairTiming(config, 0, "bodies").correct, 0.375);
  config.continuous.on = true;
  config.continuous.fullBeat = true;
  near(pairDuration(config, 0, "physics"), 0.8 + 1.4 * 1.2 + 0.8);
  assert.equal(annealSpan("physics", 0), 1);
  assert.equal(annealSpan("tween", 10), 1);
});

test("simple transitions play every phase at double speed only while the setting is on", () => {
  const config = configuration();
  config.simple = [true, false, true, false];
  const full = [0, 1, 2, 3].map((index) => pairDuration(config, index, "tween"));
  const fullSequence = sequenceDuration(config, "tween");
  const fullRange = rangeDuration(config, { from: 2, to: 18 }, "tween");
  config.fastSimple = true;
  assert.deepEqual(
    [0, 1, 2, 3].map((index) => isSpedUpPair(config, index)),
    [true, false, true, false],
  );
  near(pairDuration(config, 0, "tween"), (full[0] ?? Number.NaN) / 2);
  near(pairDuration(config, 1, "tween"), full[1] ?? Number.NaN);
  near(pairDuration(config, 2, "tween"), (full[2] ?? Number.NaN) / 2);
  near(
    sequenceDuration(config, "tween"),
    fullSequence - ((full[0] ?? Number.NaN) + (full[2] ?? Number.NaN)) / 2,
  );
  near(
    rangeDuration(config, { from: 2, to: 18 }, "tween"),
    fullRange - ((full[0] ?? Number.NaN) + (full[2] ?? Number.NaN)) / 2,
  );
  const beat = pairTiming(config, 2, "tween");
  near(beat.dwell, 0.2);
  near(beat.move, 0.14);
  near(beat.correct, 0.06);
  near(beat.settle, 0.175);
  config.continuous.on = false;
  near(pairTiming(config, 0, "tween").settle, 0.4);
  config.fastSimple = false;
  near(pairTiming(config, 0, "tween").settle, 0.8);
  assert.throws(() => isSpedUpPair(config, 9), /no transition/);
});

test("physics work is priced from the base timing, which the speed-up does not shorten", () => {
  const config = configuration();
  config.simple = [true, false, true, false];
  config.fastSimple = true;
  config.anneal = 8;
  const spans = ["dwell", "move", "correct", "settle"] as const;
  for (const on of [true, false]) {
    config.continuous.on = on;
    for (const index of [0, 1, 2, 3]) {
      const played = pairTiming(config, index, "physics");
      const base = baseTiming(config, index, "physics");
      const speed = isSpedUpPair(config, index) ? SIMPLE_TRANSITION_SPEED : 1;
      for (const span of spans) {
        near(played[span] * speed, base[span]);
      }
    }
  }
  const sped = baseTiming(config, 0, "physics");
  config.fastSimple = false;
  assert.deepEqual(baseTiming(config, 0, "physics"), sped);
  assert.deepEqual(pairTiming(config, 0, "physics"), sped);
  assert.throws(() => baseTiming(config, 9, "physics"), /no transition/);
});

test("staging exposes resize, arrival, free movement, correction and facts-panel count", () => {
  const config = configuration();
  const schedule = pairSchedule(config, 1, "tween");
  near(schedule.moveStart, 0.8);
  near(schedule.containerStart, 0.8);
  near(schedule.containerEnd, 1.04);
  near(schedule.arrive, 1.04);
  near(schedule.arrived, 1.36);
  near(schedule.blocksStart, 1.36);
  near(schedule.blocksEnd, 1.92);
  near(schedule.moveEnd, 1.92);
  near(schedule.end, 2.72);
  // The count changes half way through the roll, which starts when the square starts to fade in.
  assert.equal(displayedCount(2, schedule, 1.23, false), 2);
  assert.equal(displayedCount(2, schedule, 1.25, false), 3);
  assert.equal(displayedCount(2, schedule, 0, true), 3);
  config.phase = "move-then-add";
  const after = pairSchedule(config, 1, "tween");
  near(after.blocksEnd, 1.36);
  near(after.arrive, 1.36);
  near(after.arrived, 1.68);
  near(after.moveEnd, 1.68);
  config.phase = "simultaneous";
  const together = pairSchedule(config, 1, "tween");
  near(together.arrive, 1.6 - 0.4 * 0.8);
  near(together.arrived, together.blocksEnd);
});

test("physical staged phases add arrival time without compressing body motion", () => {
  const config = configuration();
  const addFirst = pairSchedule(config, 1, "physics");
  near(addFirst.moveStart, 0.8);
  near(addFirst.arrive, 1.04);
  near(addFirst.arrived, 1.36);
  near(addFirst.blocksStart, 1.36);
  near(addFirst.blocksEnd - addFirst.blocksStart, 0.8);
  near(addFirst.moveEnd, 2.16);
  near(addFirst.end, 2.96);

  config.phase = "move-then-add";
  const addLast = pairSchedule(config, 1, "bodies");
  near(addLast.blocksStart, 0.8);
  near(addLast.blocksEnd, 1.6);
  near(addLast.arrive, 1.6);
  near(addLast.arrived, 1.92);
  near(addLast.moveEnd, 1.92);
  near(addLast.end, 2.72);

  config.phase = "simultaneous";
  near(pairDuration(config, 1, "physics"), 2.4);
  config.phase = "add-then-move";
  near(pairDuration(config, 0, "physics"), 0.4 + 1.4 * 0.4 + 0.35);
});

/** The owner's order, 2026-09-17: shrink, then the delay, then the fade, never overlapping. */
function assertResizeDelayFade(schedule: PairSchedule, delaySeconds: number, label: string): void {
  const slack = 1e-12;
  const ordered = [
    schedule.moveStart,
    schedule.containerStart,
    schedule.containerEnd,
    schedule.arrive,
    schedule.arrived,
    schedule.moveEnd,
    schedule.end,
  ];
  assert.equal(schedule.containerStart, schedule.moveStart, `${label}: resize opens the move`);
  for (const [index, instant] of ordered.slice(1).entries()) {
    assert.ok(instant >= (ordered[index] ?? Number.NaN) - slack, `${label}: out of order`);
  }
  // The delay starts where the shrink ends and the fade starts no earlier than the delay's end.
  assert.ok(schedule.arrive - schedule.containerEnd >= delaySeconds - slack, `${label}: delay`);
  assert.ok(schedule.blocksStart <= schedule.blocksEnd + slack, `${label}: blocks`);
  assert.ok(schedule.blocksEnd <= schedule.moveEnd + slack, `${label}: blocks end in the move`);
}

test("every phase and style resizes, waits out the arrival delay, then fades the square in", () => {
  for (const delay of [0, DEFAULT_ARRIVAL_DELAY_FRACTION, ARRIVAL_DELAY_BOUNDS[1]]) {
    for (const on of [true, false]) {
      for (const fastSimple of [true, false]) {
        const config = configuration();
        config.arrivalDelay = delay;
        config.continuous.on = on;
        config.simple = [true, false, true, false];
        config.fastSimple = fastSimple;
        for (const phase of PHASES) {
          config.phase = phase;
          for (const style of STYLES) {
            for (const index of [0, 1, 2, 3]) {
              const timing = pairTiming(config, index, style);
              const span = timing.move + timing.correct;
              const label = `${phase} ${style} pair ${index} delay ${delay} beat ${on} fast ${fastSimple}`;
              const schedule = pairSchedule(config, index, style);
              assertResizeDelayFade(schedule, delay * span, label);
              near(
                schedule.containerEnd - schedule.containerStart,
                CONTAINER_RESIZE_FRACTION * span,
              );
              near(schedule.arrived - schedule.arrive, 0.4 * span);
              if (delay > 0 && span > 0) {
                assert.ok(schedule.containerEnd < schedule.arrive, `${label}: no gap`);
              }
              if (phase === "add-then-move") {
                near(schedule.arrive - schedule.containerEnd, delay * span);
              }
            }
          }
        }
      }
    }
  }
});

test("the arrival delay is a share of the moving span that scales with the beat", () => {
  assert.equal(DEFAULT_ARRIVAL_DELAY_FRACTION, 0.2);
  assert.deepEqual(ARRIVAL_DELAY_BOUNDS, [0, 0.6]);
  assert.equal(TWEEN_ILLUSTRATION_SETTINGS.arrivalDelay, DEFAULT_ARRIVAL_DELAY_FRACTION);
  assert.equal(TWEEN_ILLUSTRATION_SETTINGS.newFraction, NEW_FRACTION);
  assert.equal(NEW_FRACTION, 0.4);
  // At the owner's beat (0.5 s move, 0.2 s correct since 2026-09-17; it was 0.4 s) the default is
  // 0.2 of a 0.7 s span, 0.14 s, longer than the 0.084 s box-first staging left between the box
  // growing and the square arriving.
  const beat = DEFAULT_STEP_TIMING;
  near(beat.correct, 0.2);
  near(DEFAULT_ARRIVAL_DELAY_FRACTION * (beat.move + beat.correct), 0.14);

  const config = configuration();
  config.simple = [true, false, true, false];
  config.arrivalDelay = DEFAULT_ARRIVAL_DELAY_FRACTION;
  const gap = (index: number, style: "tween" | "physics") => {
    const schedule = pairSchedule(config, index, style);
    return schedule.arrive - schedule.containerEnd;
  };
  near(gap(1, "tween"), 0.2 * 0.8);
  // The annealing dial lengthens a physical move, and the delay with it.
  config.anneal = 8;
  near(gap(1, "physics"), 0.2 * 1.2);
  near(gap(1, "tween"), 0.2 * 0.8);
  // A static step plays the static beat, and the speed-up halves it with every other phase.
  near(gap(0, "tween"), 0.2 * 0.4);
  config.fastSimple = true;
  near(gap(0, "tween"), 0.2 * 0.2);
  near(gap(1, "tween"), 0.2 * 0.8);
  const sped = pairSchedule(config, 0, "tween");
  config.fastSimple = false;
  const full = pairSchedule(config, 0, "tween");
  for (const key of Object.keys(full) as (keyof PairSchedule)[]) {
    if (key !== "roll") {
      near(sped[key] * SIMPLE_TRANSITION_SPEED, full[key]);
    }
  }
});

test("the delay moves the square and what follows it, never the resize or the dwell", () => {
  const config = configuration();
  for (const style of STYLES) {
    config.phase = "add-then-move";
    config.arrivalDelay = 0;
    const plain = pairSchedule(config, 1, style);
    config.arrivalDelay = 0.25;
    const delayed = pairSchedule(config, 1, style);
    const shift = (0.25 * (plain.containerEnd - plain.containerStart)) / CONTAINER_RESIZE_FRACTION;
    near(delayed.moveStart, plain.moveStart);
    near(delayed.containerStart, plain.containerStart);
    near(delayed.containerEnd, plain.containerEnd);
    for (const key of [
      "arrive",
      "arrived",
      "blocksStart",
      "blocksEnd",
      "moveEnd",
      "end",
    ] as const) {
      near(delayed[key], plain[key] + shift);
    }
    near(delayed.blocksEnd - delayed.blocksStart, plain.blocksEnd - plain.blocksStart);
    // Settle keeps its length: the step grows by exactly the delay.
    near(delayed.end - delayed.moveEnd, plain.end - plain.moveEnd);
    near(pairDuration(config, 1, style) - plain.end, shift);
  }
  // Where block motion already holds the square past the delay, the delay costs nothing.
  config.phase = "move-then-add";
  config.arrivalDelay = 0;
  const waiting = pairSchedule(config, 1, "tween");
  config.arrivalDelay = 0.2;
  assert.deepEqual(pairSchedule(config, 1, "tween"), waiting);
  // A delay that outlasts block motion holds the square, and the unstaged phases' blocks keep
  // their span while the square finishes after them.
  config.arrivalDelay = 0.6;
  const held = pairSchedule(config, 1, "tween");
  near(held.arrive, held.containerEnd + 0.6 * 0.8);
  config.phase = "simultaneous";
  const late = pairSchedule(config, 1, "tween");
  near(late.arrive, late.containerEnd + 0.6 * 0.8);
  near(late.blocksEnd - late.blocksStart, 0.8);
  near(late.moveEnd, late.arrived);
});

test("the arrival delay and fade are validated fractions", () => {
  const config = configuration();
  for (const bad of [1.5, -0.1, Number.NaN, Number.POSITIVE_INFINITY]) {
    config.arrivalDelay = bad;
    assert.throws(() => pairSchedule(config, 1, "tween"), RangeError);
    assert.throws(() => pairSchedule(config, 1, "tween"), /arrival-delay fraction/);
  }
  config.arrivalDelay = 1;
  assert.doesNotThrow(() => pairSchedule(config, 1, "tween"));
  config.newFraction = 1.2;
  assert.throws(() => pairSchedule(config, 1, "tween"), /new fraction/);
});

test("rotation-first and slide-first are distinct pure schedules", () => {
  const rotate = phaseProgress("rotate-first", 0.3);
  const slide = phaseProgress("slide-first", 0.3);
  near(rotate.rot, 0.5);
  assert.equal(rotate.slide, 0);
  near(slide.slide, 0.5);
  assert.equal(slide.rot, 0);
  assert.deepEqual(phaseProgress("simultaneous", 0.5), { rot: 0.5, slide: 0.5, e: 0.5 });
});

test("sequence seeking and sparse ranges share endpoint ownership", () => {
  const config = configuration();
  const still = 0.4 + 1.4 * 0.4 + 0.35;
  const matched = 0.8 + 1.4 * 0.8 + 0.8;
  const physical = 0.8 + 1.7 * 0.8 + 0.8;
  near(sequenceDuration(config, "tween"), 2 * still + 2 * matched);
  near(rangeDuration(config, { from: 2, to: 18 }, "tween"), 2 * still + 2 * matched);
  near(sequenceDuration(config, "physics"), 2 * still + 2 * physical);
  near(rangeDuration(config, { from: 2, to: 18 }, "physics"), 2 * still + 2 * physical);
  assert.deepEqual(seekSequence(config, "tween", still), { index: 1, time: 0 });
  const end = seekSequence(config, "tween", 999);
  assert.equal(end.index, 3);
  near(end.time, matched);
  assert.deepEqual(seekSequence(config, "tween", -10), { index: 0, time: 0 });
  near(rangeProgress(config, { from: 2, to: 18 }, 1, matched / 2, "tween", false), 1.5 / 17);
  near(rangeProgress(config, { from: 2, to: 18 }, 3, 0, "tween", true), 1);
  const samples = [0, 0.7, still, still + matched + 0.3, 2 * still + 2 * matched];
  assert.deepEqual(
    samples.map((time) => seekSequence(config, "tween", time)),
    [...samples]
      .reverse()
      .map((time) => seekSequence(config, "tween", time))
      .reverse(),
  );
});

test("zero-duration phases remain deterministic and malformed durations fail early", () => {
  const config = configuration();
  config.continuous.on = false;
  config.timing = { dwell: 0, move: 0, correct: 0, settle: 0 };
  config.arrivalDelay = DEFAULT_ARRIVAL_DELAY_FRACTION;
  assert.deepEqual(seekSequence(config, "tween", 0), { index: 3, time: 0 });
  assert.equal(pairSchedule(config, 0, "tween").roll, 0);
  assertResizeDelayFade(pairSchedule(config, 1, "physics"), 0, "zero beat");
  assert.equal(ramp(0, 0, 0), 1);
  assert.equal(ramp(-1, 0, 0), 0);
  config.timing.correct = Number.NaN;
  assert.throws(() => pairDuration(config, 0, "tween"), /finite/);
  assert.equal(annealSpan("physics", 20), 2.7);
  assert.throws(() => annealSpan("physics", 21), /zero and twenty/);
  assert.throws(() => seekSequence(configuration(), "tween", Number.NaN), /finite seconds/);
});
