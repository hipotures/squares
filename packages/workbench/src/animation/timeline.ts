import type { AtlasPhase, AtlasStyle, AtlasTiming } from "../api/workbench-api.js";
import { rangeIndexBounds, type StepRange } from "../core/navigation.ts";
import type { CorpusPair } from "../data/corpus.js";

export interface ContinuousTiming {
  on: boolean;
  fullBeat: boolean;
  beat: AtlasTiming;
  staticBeat: AtlasTiming;
}

/** How many times faster a simple transition plays while `fastSimple` is on. */
export const SIMPLE_TRANSITION_SPEED = 2;

export interface TimelineConfiguration {
  pairs: readonly Pick<CorpusPair, "n" | "kind">[];
  /** Per pair, whether the step only fills an axis-aligned grid; see `isSimpleTransition`. */
  simple?: readonly boolean[];
  /** Play simple transitions, every phase, at `SIMPLE_TRANSITION_SPEED`. */
  fastSimple?: boolean;
  /**
   * Fraction of the moving span between the container finishing its resize and the new square
   * starting to fade in. The resize is always first; the default zero fades the square in as soon
   * as the resize completes.
   */
  arrivalDelay?: number;
  timing: AtlasTiming;
  continuous: ContinuousTiming;
  anneal: number;
  phase: AtlasPhase;
  /** In the illustrated staged phases, the share of the moving span block motion gives up. */
  arrivalFraction: number;
  /** The share of the moving span the new square takes to fade in, in every phase. */
  newFraction: number;
  rollMax: number;
}

/** The share of the moving span the container takes to resize, whatever the delay or phase. */
export const CONTAINER_RESIZE_FRACTION = 0.3;

/**
 * Every instant is in seconds from the pair's start, and they are ordered
 * `moveStart = containerStart <= containerEnd <= arrive <= arrived <= moveEnd <= end`, with
 * `blocksStart <= blocksEnd <= moveEnd`. The new square starts to fade in at least the arrival
 * delay after the resize completes, and exactly then unless a phase holds it for block motion.
 */
export interface PairSchedule {
  moveStart: number;
  moveEnd: number;
  end: number;
  /** When the new square starts to fade in, and when it is fully in. */
  arrive: number;
  arrived: number;
  /** When the container starts to resize: the start of the move, before the new square shows. */
  containerStart: number;
  /** When the container resize completes, which is the arrival delay before `arrive` or earlier. */
  containerEnd: number;
  blocksStart: number;
  blocksEnd: number;
  roll: number;
}

function finiteNonnegative(value: number, name: string): number {
  if (!Number.isFinite(value) || value < 0) {
    throw new RangeError(`${name} must be finite and nonnegative`);
  }
  return value;
}

function fraction(value: number, name: string): number {
  if (finiteNonnegative(value, name) > 1) {
    throw new RangeError(`${name} must be between zero and one`);
  }
  return value;
}

function checkedTiming(timing: AtlasTiming): AtlasTiming {
  return {
    dwell: finiteNonnegative(timing.dwell, "dwell"),
    move: finiteNonnegative(timing.move, "move"),
    correct: finiteNonnegative(timing.correct, "correct"),
    settle: finiteNonnegative(timing.settle, "settle"),
  };
}

function pairAt(
  configuration: TimelineConfiguration,
  index: number,
): Pick<CorpusPair, "n" | "kind"> {
  const pair = configuration.pairs[index];
  if (pair === undefined) {
    throw new RangeError(`no transition at index ${index}`);
  }
  return pair;
}

export function isStillPair(configuration: TimelineConfiguration, index: number): boolean {
  const kind = pairAt(configuration, index).kind;
  return kind === "prefix" || kind === "shared-picture";
}

/** The simulation has more work above level three; an illustration has no annealing. */
export function annealSpan(style: AtlasStyle, level: number): number {
  if (finiteNonnegative(level, "anneal") > 20) {
    throw new RangeError("anneal must be between zero and twenty");
  }
  return style !== "tween" && level > 3 ? 1 + (level - 3) * 0.1 : 1;
}

export function continuousTiming(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): AtlasTiming {
  const { continuous } = configuration;
  if (isStillPair(configuration, index) && !continuous.fullBeat) {
    return checkedTiming(continuous.staticBeat);
  }
  return scaledTiming(continuous.beat, annealSpan(style, configuration.anneal));
}

/** Whether this pair is a simple transition that currently plays sped up. */
export function isSpedUpPair(configuration: TimelineConfiguration, index: number): boolean {
  pairAt(configuration, index);
  return configuration.fastSimple === true && configuration.simple?.[index] === true;
}

function spedTiming(timing: AtlasTiming, speed: number): AtlasTiming {
  const valid = checkedTiming(timing);
  return {
    dwell: valid.dwell / speed,
    move: valid.move / speed,
    correct: valid.correct / speed,
    settle: valid.settle / speed,
  };
}

function scaledTiming(timing: AtlasTiming, scale: number): AtlasTiming {
  const valid = checkedTiming(timing);
  return { ...valid, move: valid.move * scale, correct: valid.correct * scale };
}

/**
 * The timing a pair's work is priced from: the beat, and the annealed span of the move, with no
 * presentation speed-up. Physics steps are counted from this, so a simple transition played at
 * double speed simulates what it simulates at full length, and `physics()` and the benchmark do
 * the same work whatever the clock plays. A trajectory is sampled by move fraction, so a faster
 * clock still plays all of it.
 */
export function baseTiming(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): AtlasTiming {
  pairAt(configuration, index);
  return configuration.continuous.on
    ? continuousTiming(configuration, index, style)
    : scaledTiming(configuration.timing, annealSpan(style, configuration.anneal));
}

/** The timing a pair plays on the clock: its base timing, sped up while it plays sped up. */
export function pairTiming(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): AtlasTiming {
  const timing = baseTiming(configuration, index, style);
  return isSpedUpPair(configuration, index) ? spedTiming(timing, SIMPLE_TRANSITION_SPEED) : timing;
}

export function timingDuration(timing: AtlasTiming): number {
  const checked = checkedTiming(timing);
  const duration = checked.dwell + checked.move + checked.correct + checked.settle;
  return finiteNonnegative(duration, "total duration");
}

/** A physical style simulates a staged step's bodies over the whole moving span. */
function isStagedPhysicalPair(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): boolean {
  return (
    style !== "tween" &&
    !isStillPair(configuration, index) &&
    (configuration.phase === "add-then-move" || configuration.phase === "move-then-add")
  );
}

/**
 * The owner's order of 2026-09-17: the container resizes, which shrinks the picture; the arrival
 * delay passes; then the new square fades in at its final size. Every duration is a share of the
 * moving span, so the speed-up and the beat scale all of them together. Block motion keeps its
 * phase: before the square in `move-then-add`, after it in `add-then-move`, and across the whole
 * span in the unstaged phases, whose square finishes with the blocks unless the delay holds it.
 * The step grows by whatever the resize and the delay add in front of the square.
 */
function scheduleForTiming(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
  timing: AtlasTiming,
): PairSchedule {
  const span = timing.move + timing.correct;
  const moveStart = timing.dwell;
  const arrivalFraction = fraction(configuration.arrivalFraction, "arrival fraction");
  const fade = span * fraction(configuration.newFraction, "new fraction");
  const delay = span * fraction(configuration.arrivalDelay ?? 0, "arrival-delay fraction");
  const containerStart = moveStart;
  const containerEnd = containerStart + span * CONTAINER_RESIZE_FRACTION;
  const earliestArrival = containerEnd + delay;
  // The illustrated staged phases have always given the arrival a share of the span; a physical
  // style simulates its bodies over all of it.
  const stagedBlocks = isStagedPhysicalPair(configuration, index, style)
    ? span
    : span * (1 - arrivalFraction);
  let arrive: number;
  let blocksStart: number;
  let blocksEnd: number;
  if (configuration.phase === "add-then-move") {
    arrive = earliestArrival;
    blocksStart = arrive + fade;
    blocksEnd = blocksStart + stagedBlocks;
  } else if (configuration.phase === "move-then-add") {
    blocksStart = moveStart;
    blocksEnd = moveStart + stagedBlocks;
    arrive = Math.max(blocksEnd, earliestArrival);
  } else {
    blocksStart = moveStart;
    blocksEnd = moveStart + span;
    arrive = Math.max(blocksEnd - fade, earliestArrival);
  }
  const arrived = arrive + fade;
  const moveEnd = Math.max(blocksEnd, arrived);
  const end = moveEnd + timing.settle;
  return {
    moveStart,
    moveEnd,
    end,
    arrive,
    arrived,
    containerStart,
    containerEnd,
    blocksStart,
    blocksEnd,
    roll: Math.min(finiteNonnegative(configuration.rollMax, "roll maximum"), end - arrive),
  };
}

export function pairDuration(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): number {
  return pairSchedule(configuration, index, style).end;
}

/** Arrival, movement, and correction are explicit intervals, including zero-duration beats. */
export function pairSchedule(
  configuration: TimelineConfiguration,
  index: number,
  style: AtlasStyle,
): PairSchedule {
  return scheduleForTiming(configuration, index, style, pairTiming(configuration, index, style));
}

export function clampUnit(value: number): number {
  if (!Number.isFinite(value)) {
    throw new RangeError("progress must be finite");
  }
  return Math.max(0, Math.min(1, value));
}

function easeInOut(value: number): number {
  return value < 0.5 ? 4 * value * value * value : 1 - (-2 * value + 2) ** 3 / 2;
}

export function phaseProgress(
  phase: AtlasPhase,
  progress: number,
): { rot: number; slide: number; e: number } {
  const unit = clampUnit(progress);
  const e = easeInOut(unit);
  if (phase === "rotate-first") {
    return {
      rot: easeInOut(clampUnit(unit / 0.6)),
      slide: easeInOut(clampUnit((unit - 0.4) / 0.6)),
      e,
    };
  }
  if (phase === "slide-first") {
    return {
      rot: easeInOut(clampUnit((unit - 0.4) / 0.6)),
      slide: easeInOut(clampUnit(unit / 0.6)),
      e,
    };
  }
  return { rot: e, slide: e, e };
}

/** A zero-length interval is a deterministic step, never division by zero. */
export function ramp(time: number, from: number, to: number): number {
  if (![time, from, to].every(Number.isFinite)) {
    throw new RangeError("ramp inputs must be finite");
  }
  return to > from ? clampUnit((time - from) / (to - from)) : time >= from ? 1 : 0;
}

export function rangeDuration(
  configuration: TimelineConfiguration,
  range: StepRange,
  style: AtlasStyle,
): number {
  const bounds = rangeIndexBounds(
    configuration.pairs.map((pair) => pair.n + 1),
    range,
  );
  let duration = 0;
  for (let index = bounds.first; index <= bounds.last; index += 1) {
    const continuous = continuousTiming(configuration, index, style);
    const timing = isSpedUpPair(configuration, index)
      ? spedTiming(continuous, SIMPLE_TRANSITION_SPEED)
      : continuous;
    duration += scheduleForTiming(configuration, index, style, timing).end;
  }
  return finiteNonnegative(duration, "range duration");
}

export function sequenceDuration(configuration: TimelineConfiguration, style: AtlasStyle): number {
  return configuration.pairs.reduce(
    (total, _pair, index) => total + pairDuration(configuration, index, style),
    0,
  );
}

/** Seeking and capture share boundary ownership: an exact interior endpoint starts the next pair. */
export function seekSequence(
  configuration: TimelineConfiguration,
  style: AtlasStyle,
  seconds: number,
): { index: number; time: number } {
  if (configuration.pairs.length === 0 || !Number.isFinite(seconds)) {
    throw new RangeError("sequence seek requires pairs and finite seconds");
  }
  let time = Math.max(0, Math.min(sequenceDuration(configuration, style), seconds));
  let index = 0;
  while (
    index < configuration.pairs.length - 1 &&
    time >= pairDuration(configuration, index, style)
  ) {
    time -= pairDuration(configuration, index, style);
    index += 1;
  }
  return { index, time };
}

export function rangeProgress(
  configuration: TimelineConfiguration,
  range: StepRange,
  index: number,
  time: number,
  style: AtlasStyle,
  optimizing: boolean,
): number {
  const pair = pairAt(configuration, index);
  const duration = pairDuration(configuration, index, style);
  const within = optimizing ? 1 : duration > 0 ? clampUnit(time / duration) : 0;
  return clampUnit((pair.n + within - (range.from - 1)) / Math.max(1, range.to - range.from + 1));
}

/** The facts panel changes count at the midpoint of the arrival roll, independent of paint. */
export function displayedCount(
  n: number,
  schedule: PairSchedule,
  time: number,
  optimizing: boolean,
): number {
  if (optimizing) {
    return n + 1;
  }
  const progress = ramp(time, schedule.arrive, schedule.arrive + schedule.roll);
  return progress >= 0.5 ? n + 1 : n;
}

export const timeline = Object.freeze({
  isStillPair,
  isSpedUpPair,
  annealSpan,
  continuousTiming,
  baseTiming,
  pairTiming,
  timingDuration,
  pairDuration,
  pairSchedule,
  phaseProgress,
  ramp,
  rangeDuration,
  sequenceDuration,
  seekSequence,
  rangeProgress,
  displayedCount,
});
