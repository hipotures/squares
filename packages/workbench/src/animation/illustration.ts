import type { AtlasPhase } from "../api/workbench-api.js";
import type { CorpusBlock } from "../data/corpus.js";
import { newSquareOpacity } from "../motion-settings.ts";
import type { SceneFrame, SceneMark, SceneSquare } from "../view/scene-types.js";
import { type PairSchedule, phaseProgress, ramp } from "./timeline.ts";

export type DegreePose = readonly [number, number, number, ...unknown[]];

/** A prepared correspondence keeps block construction outside the per-frame path. */
export interface MotionTrack {
  ident: number;
  a: DegreePose;
  b: DegreePose;
  turn: number;
  block: Pick<CorpusBlock, "turn" | "from" | "to"> | null;
  dx: number;
  dy: number;
  rx: number;
  ry: number;
}

/**
 * How much of the room after the square has arrived the cross-over may take.
 *
 * The rest is the hold, where the square sits opaque and fully scarlet. Half: a step has to
 * show the square arriving AND show it taking its place, and on the shortest steps -- a grid
 * fill at the page's simple-transition speed-up -- there are only a few frames for each.
 */
const TINT_CROSS_SHARE = 0.5;

export interface IllustrationInput {
  pairIndex: number;
  n: number;
  fromSide: number;
  toSide: number;
  tracks: readonly MotionTrack[];
  arriving: { identity: number; pose: DegreePose };
  previousIndex: number | null;
  phase: AtlasPhase;
  schedule: PairSchedule;
  seconds: number;
  moveSeconds: number;
  padding: number;
  drain: number;
  resting: number;
  /**
   * How far the rest colour has turned from n's packing to n + 1's. The page's one schedule
   * for it, shared with the physical path, so the two cannot turn it at different moments.
   */
  homeward: number;
  links: boolean;
  tint: number;
  /** Seconds the arriving square's tint takes to reach its own fill. */
  tintSeconds?: number;
  /** When the crossing must be done by; see `tintProgress`. */
  tintUntil?: number;
  mark: { wide: number; thin: number; fade: number };
}

function lerp(from: number, to: number, progress: number): number {
  return from + (to - from) * progress;
}

function easeOut(progress: number): number {
  return 1 - (1 - progress) ** 3;
}

/** Block rotation and residual translation are independent of drawing and simulation. */
export function interpolateBlockPose(
  track: MotionTrack,
  progress: { rot: number; slide: number },
): [number, number, number] {
  if (track.block === null) {
    return [
      lerp(track.a[0], track.b[0], progress.slide),
      lerp(track.a[1], track.b[1], progress.slide),
      track.a[2] + track.turn * progress.rot,
    ];
  }
  const angle = (track.block.turn * progress.rot * Math.PI) / 180;
  const cosine = Math.cos(angle);
  const sine = Math.sin(angle);
  return [
    lerp(track.block.from[0], track.block.to[0], progress.slide) +
      cosine * track.dx -
      sine * track.dy +
      track.rx * progress.slide,
    lerp(track.block.from[1], track.block.to[1], progress.slide) +
      sine * track.dx +
      cosine * track.dy +
      track.ry * progress.slide,
    track.a[2] + track.turn * progress.rot,
  ];
}

function previousMark(input: IllustrationInput, squares: readonly SceneSquare[]): SceneMark | null {
  if (input.previousIndex === null) {
    return null;
  }
  const previous = squares[input.previousIndex];
  if (previous === undefined) {
    throw new RangeError("previous square is absent from the illustration");
  }
  const fade = input.moveSeconds * input.mark.fade;
  const gone = ramp(input.seconds, input.schedule.moveStart, input.schedule.moveStart + fade);
  return gone >= 1 ? null : { ...previous, opacity: 1 - gone, strokeWidth: input.mark.thin };
}

/** Sampling a direct illustration never calls a solver and never grants evidence. */
/**
 * How far the arriving square's scarlet has crossed to its own color, 0 to 1, at `seconds`.
 *
 * **One schedule for both renderers.** The tween path and the physics path each used to compute
 * this, and every fix to it landed in one and not the other: the hold before the crossing and
 * the rule that the crossing finishes inside the grey both reached grid fills and never reached a
 * matched step, where the physics path kept crossing during the return. Measured with
 * `check_transitions --trace 11`, the arriving square held red until 2.733 s and crossed in the
 * last 0.3 s, which is exactly the schedule this replaced.
 *
 * The crossing finishes before the packing's color comes back, which it does over the last
 * `tintSeconds` of the step, so red to the square's own color happens among grey squares. A
 * step that never drains keeps the tail of the step instead, which is what `until` says: where
 * the color starts back, `end - tintSeconds` by default, or the step's end. Either way the
 * crossing takes at most half the room after arrival, and what is in front of it is the hold.
 *
 * `until` was once always the default, so a still pair -- which never drains -- finished its
 * crossing 0.3 s before a return that never came: into 8, the arriving square held scarlet for
 * 0.03 s and crossed to green in the next 0.03 s, two frames at 60 fps.
 */
export function tintProgress(
  schedule: PairSchedule,
  seconds: number,
  tintSeconds: number | undefined,
  until: number = schedule.end - (tintSeconds ?? 0),
): number {
  const crossEnd =
    tintSeconds === undefined ? schedule.end : until > schedule.arrived ? until : schedule.end;
  const room = Math.max(0, crossEnd - schedule.arrived);
  const cross =
    tintSeconds === undefined
      ? Math.max(0, schedule.end - schedule.moveEnd)
      : Math.min(tintSeconds, room * TINT_CROSS_SHARE);
  return easeOut(ramp(seconds, crossEnd - cross, crossEnd));
}

export function illustrationFrame(input: IllustrationInput): SceneFrame {
  const { schedule, seconds } = input;
  const progress = ramp(seconds, schedule.blocksStart, schedule.blocksEnd);
  const phased = phaseProgress(input.phase, progress);
  // The new square fades in where it ends up and at its own size: opacity is all that changes.
  const arrival = newSquareOpacity(ramp(seconds, schedule.arrive, schedule.arrived));
  const containerGrowth = phaseProgress(
    "simultaneous",
    ramp(seconds, schedule.containerStart, schedule.containerEnd),
  ).e;
  const side = lerp(input.fromSide, input.toSide, containerGrowth);
  const view = side * (1 + 2 * input.padding);
  const squares: SceneSquare[] = input.tracks.map((track, index) => {
    const [x, y, angleDegrees] = interpolateBlockPose(track, phased);
    return { index, identity: track.ident, x, y, angleDegrees, opacity: 1, scale: 1 };
  });
  const arriving: SceneSquare = {
    index: squares.length,
    identity: input.arriving.identity,
    x: input.arriving.pose[0],
    y: input.arriving.pose[1],
    angleDegrees: input.arriving.pose[2],
    opacity: arrival,
    scale: 1,
  };
  // **The arriving square is saturated scarlet for a beat before it changes** (the owner,
  // 2026-09-21). It fades in over `arrive` to `arrived`, so while it is arriving it is
  // translucent over the paper and reads as a pale mauve whatever its fill says; and the
  // cross-over used to begin the instant the fade finished, which left exactly one frame where
  // the square was both opaque and fully scarlet. On the step into 9 -- fourteen frames end to
  // end -- it was measurably red for two, and both of those were part-transparent.
  //
  // So the cross-over takes a share of the room after arrival rather than all of it, capped at
  // `tintSeconds`. What is left in front of it is the hold: the square sits opaque and scarlet,
  // then crosses to the colour it will keep.
  //
  // **The crossing finishes before the packing comes back** (the owner, 2026-09-21). Red to the
  // square's own colour passes through neutral like every other far blend, and on its own that
  // is a grey square where a red one was. Run while the rest of the packing is still drained, it
  // is a grey square among grey squares and nothing about it reads as an event; by the time the
  // colour returns, the square already wears the colour it will keep. The drain lifts over the
  // last `tintSeconds` of the step, so that is where the crossing has to end.
  //
  // A still pair never drains, so there is nothing to hide the crossing behind and nothing to
  // hide it from: it keeps the tail of the step, which on a grid fill is a few frames.
  const settled = tintProgress(schedule, seconds, input.tintSeconds, input.tintUntil);
  const mark: SceneMark | null =
    arrival > 0
      ? {
          ...arriving,
          strokeWidth: lerp(input.mark.wide, input.mark.thin, settled),
        }
      : previousMark(input, squares);
  squares.push(arriving);
  return {
    pairIndex: input.pairIndex,
    n: input.n,
    containerSide: side,
    viewBox: { x: side / 2 - view / 2, y: -side / 2 - view / 2, size: view },
    squares,
    presentation: {
      drain: input.drain,
      newTint: arrival > 0 ? input.tint * (1 - settled) : 0,
      resting: input.resting,
      homeward: input.homeward,
      mark,
      linksOpacity: input.links ? (progress <= 0 ? 0.35 : 1 - phased.e) : 0,
      ghostOpacity: input.links ? (seconds > schedule.moveStart ? 1 - arrival : 0) : 0,
    },
    motion: "direct-illustration",
  };
}
