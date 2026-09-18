import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  ANNEAL_SETTINGS,
  annealConfiguration,
  DEFAULT_ANIMATE_STYLE,
  DEFAULT_ARRIVAL_DELAY_FRACTION,
  DEFAULT_MOTION_RESPONSE,
  DEFAULT_PAIR_LAW,
  motionControlScope,
  newSquareOpacity,
  PAIR_LAW_PRESETS,
  physicalPresentationNeedsTrajectory,
  physicalPresentationProgress,
  physicalPresentationState,
  TRAJECTORY_PHYSICS_SETTINGS,
  trajectoryPhysicsConfiguration,
} from "../src/motion-settings.ts";

const application = readFileSync(new URL("../src/application.js", import.meta.url), "utf8");
const template = readFileSync(new URL("../assets/template.html", import.meta.url), "utf8");

test("motion settings have one named, balanced default and distinct experimental presets", () => {
  assert.equal(DEFAULT_ANIMATE_STYLE, "tween");
  assert.deepEqual(PAIR_LAW_PRESETS.balanced, DEFAULT_PAIR_LAW);
  assert.ok(PAIR_LAW_PRESETS.rigid.rigidity < DEFAULT_PAIR_LAW.rigidity);
  assert.ok(PAIR_LAW_PRESETS.soft.repulsion < DEFAULT_PAIR_LAW.repulsion);
  assert.ok(PAIR_LAW_PRESETS.sticky.attraction > 0);
  assert.ok(ANNEAL_SETTINGS.defaultLevel >= ANNEAL_SETTINGS.min);
  assert.ok(ANNEAL_SETTINGS.defaultLevel <= ANNEAL_SETTINGS.max);
  assert.deepEqual(annealConfiguration(ANNEAL_SETTINGS.defaultLevel), {
    level: 9,
    amplitude: ANNEAL_SETTINGS.amplitude(9),
    decayPower: ANNEAL_SETTINGS.decayPower(9),
    span: ANNEAL_SETTINGS.span(9),
  });
  assert.equal(TRAJECTORY_PHYSICS_SETTINGS.bodiesJiggle, TRAJECTORY_PHYSICS_SETTINGS.jiggle);
  assert.equal(
    TRAJECTORY_PHYSICS_SETTINGS.bodiesJiggleTorque,
    TRAJECTORY_PHYSICS_SETTINGS.jiggleTorque,
  );
  const controlled = trajectoryPhysicsConfiguration(DEFAULT_MOTION_RESPONSE);
  assert.equal(controlled.maxSpeed, 10);
  assert.equal(controlled.contactDamping, 20);
  assert.equal(DEFAULT_ARRIVAL_DELAY_FRACTION, 0.2);
  assert.equal(physicalPresentationProgress(0, 1, { move: 0.5, correct: 0.4 }), 0);
  assert.equal(physicalPresentationProgress(1, 1, { move: 0.5, correct: 0.4 }), 1);
  assert.equal(
    physicalPresentationProgress(0.8, 1.04, { move: 0.5, correct: 0.3 }, 0, 0.8 / 1.04),
    1,
  );
  const resizeFirst = {
    containerStartFraction: 0,
    containerEndFraction: 0.2,
    arrivalStartFraction: 0.35,
    arrivalEndFraction: 0.65,
    motionStartFraction: 0.65,
  };
  const timing = { move: 0.5, correct: 0.5 };
  // Resizing: nothing has arrived and nothing moves; a blind run needs its trajectory's sides.
  const resizing = physicalPresentationState(0.1, 1, timing, resizeFirst);
  assert.ok(resizing.containerProgress > 0 && resizing.containerProgress < 1);
  assert.equal(resizing.appearanceProgress, 0);
  assert.equal(resizing.trajectoryProgress, 0);
  assert.equal(physicalPresentationNeedsTrajectory(resizing, true), false);
  assert.equal(physicalPresentationNeedsTrajectory(resizing, false), true);
  // The delay: the resize is over and the square has not started.
  const waiting = physicalPresentationState(0.3, 1, timing, resizeFirst);
  assert.equal(waiting.containerProgress, 1);
  assert.equal(waiting.appearanceProgress, 0);
  assert.equal(physicalPresentationNeedsTrajectory(waiting, true), false);
  // Half way through the fade the square is half in, on the trajectory, before bodies move.
  const fading = physicalPresentationState(0.5, 1, timing, resizeFirst);
  assert.ok(Math.abs(fading.appearanceProgress - 0.5) < 1e-12);
  assert.equal(fading.trajectoryProgress, 0);
  assert.equal(physicalPresentationNeedsTrajectory(fading, true), true);

  const moveFirst = physicalPresentationState(
    0.8,
    1.04,
    { move: 0.5, correct: 0.3 },
    {
      arrivalStartFraction: 0.8 / 1.04,
      arrivalEndFraction: 1,
      containerStartFraction: 0.96 / 1.04,
      containerEndFraction: 1,
      motionStartFraction: 0,
      motionEndFraction: 0.8 / 1.04,
    },
  );
  assert.equal(moveFirst.trajectoryProgress, 1);
  assert.equal(moveFirst.appearanceProgress, 0);
});

test("the control scope names when physics controls do and do not affect motion", () => {
  assert.deepEqual(motionControlScope("tween", false), {
    active: false,
    reason: "tween",
    note: "A interpolates known poses; physics controls are off.",
  });
  assert.equal(motionControlScope("physics", false).active, true);
  assert.equal(motionControlScope("bodies", false).active, true);
  assert.deepEqual(motionControlScope("physics", false, "pack"), {
    active: false,
    reason: "pack",
    note: "Independent Pack has its own controller; Animate physics controls are off.",
  });
  assert.deepEqual(motionControlScope("physics", false, "search"), {
    active: false,
    reason: "search",
    note: "Search has its own plan; Animate physics controls are off.",
  });
  assert.deepEqual(motionControlScope("physics", true), {
    active: false,
    reason: "static",
    note: "Static append: no solver runs; physics controls are off.",
  });
});

test("the page makes physics scope enforceable and calls the bounded restart policy", () => {
  assert.match(template, /data-law="balanced"/);
  assert.match(template, /data-law="rigid"[^>]*>low give</);
  assert.match(template, /data-law="soft"[^>]*>gentle push</);
  assert.match(template, /data-law="sticky"[^>]*>attractive</);
  assert.match(template, /id="motion-scope-note"/);
  assert.match(template, /id="motion-speed-limit"/);
  assert.match(template, /id="motion-contact-damping"/);
  assert.match(template, /id="motion-arrival-delay"/);
  assert.ok((template.match(/data-motion-control="physics"/g) ?? []).length >= 5);
  assert.match(application, /syncMotionControlScope\(\)/);
  assert.match(application, /physics: trajectoryPhysicsConfiguration\(MOTION_RESPONSE\)/);

  for (const setting of [
    "setLawOf",
    "resetPhysics",
    "graphChanged",
    "setPhase",
    "setStyle",
    "setTiming",
    "setSnap",
    "setBlind",
    "setAnneal",
    "setSeed",
    "setBlindInflate",
    "setMotionResponse",
    "setArrivalDelay",
    "setRelationship",
  ]) {
    const start = application.indexOf(`function ${setting}(`);
    assert.notEqual(start, -1, `${setting} is missing`);
    const next = application.indexOf("\n  function ", start + 1);
    const body = application.slice(start, next === -1 ? application.length : next);
    assert.match(body, /restartForTrajectoryChange\(\)/, `${setting} can swap motion mid-play`);
  }

  const keyStart = application.indexOf("function trajectoryKey(");
  const keyEnd = application.indexOf("\n  function ", keyStart + 1);
  const keyBody = application.slice(keyStart, keyEnd);
  assert.doesNotMatch(
    keyBody,
    /arrivalDelay/,
    "presentation timing must not fork or rebuild an equivalent physical trajectory",
  );
});

test("the new square's fade is a smooth, symmetric, clamped ease with no size in it", () => {
  assert.equal(newSquareOpacity(0), 0);
  assert.equal(newSquareOpacity(1), 1);
  assert.equal(newSquareOpacity(-1), 0);
  assert.equal(newSquareOpacity(2), 1);
  assert.equal(newSquareOpacity(0.5), 0.5);
  let previous = 0;
  for (let step = 1; step <= 1000; step++) {
    const progress = step / 1000;
    const opacity = newSquareOpacity(progress);
    assert.ok(opacity >= previous);
    assert.ok(Math.abs(opacity + newSquareOpacity(1 - progress) - 1) < 1e-12);
    // Its slope never exceeds 1.5, so no frame of a fade jumps further than 1.5 frames' share.
    assert.ok(opacity - previous <= 1.5 / 1000 + 1e-12);
    previous = opacity;
  }
  // It starts and ends flat: the first and last hundredth of the fade change it by 0.0003.
  assert.ok(newSquareOpacity(0.01) < 3e-4);
  assert.ok(1 - newSquareOpacity(0.99) < 3e-4);
  assert.match(
    template,
    /<label title="Delay after the container finishes resizing before the new square starts to fade in[^"]*">arrival delay\s*<input type="range" id="motion-arrival-delay">\s*<span class="law-val" id="motion-arrival-delay-val"><\/span>/,
  );
  assert.doesNotMatch(application, /inflateFrom, 1, appear/);
  const reset = application.slice(
    application.indexOf("function resetPhysics("),
    application.indexOf("\n  function ", application.indexOf("function resetPhysics(") + 1),
  );
  assert.match(reset, /arrivalDelayFraction = DEFAULT_ARRIVAL_DELAY_FRACTION;/);
  assert.match(reset, /arrivalDelay: arrivalDelayState\(\)/);
});
