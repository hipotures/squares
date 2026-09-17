/** Shared, headless-safe settings for the catalogue motion strategies. */

export type MotionStyle = "tween" | "physics" | "bodies";

export interface MotionLaw {
  rigidity: number;
  repulsion: number;
  attraction: number;
  range: number;
}

export type MotionLawKey = keyof MotionLaw;

export const DEFAULT_ANIMATE_STYLE: MotionStyle = "tween";
export const DEFAULT_PACK_STYLE: MotionStyle = "physics";

export const LAW_PARAMETER_DEFINITIONS = [
  {
    key: "rigidity",
    label: "contact give",
    step: 0.001,
    decimals: 3,
    says: "penetration tolerated before repulsion steepens; lower is harder",
  },
  {
    key: "repulsion",
    label: "repulsion",
    step: 50,
    decimals: 0,
    says: "the push when penetrating",
  },
  {
    key: "attraction",
    label: "attraction",
    step: 5,
    decimals: 0,
    says: "the pull when separated but close; zero is none",
  },
  {
    key: "range",
    label: "pull range",
    step: 0.005,
    decimals: 3,
    says: "the gap width the attraction acts over; zero is none",
  },
] as const;

export const DEFAULT_PAIR_LAW: MotionLaw = {
  rigidity: 0.35,
  repulsion: 950,
  attraction: 80,
  range: 0.15,
};

export const PAIR_LAW_BOUNDS: Record<MotionLawKey, [number, number]> = {
  rigidity: [0.002, 0.4],
  repulsion: [200, 8000],
  attraction: [0, 400],
  range: [0, 0.5],
};

export interface PairLawPresets {
  balanced: Readonly<MotionLaw>;
  rigid: Readonly<MotionLaw>;
  soft: Readonly<MotionLaw>;
  sticky: Readonly<MotionLaw>;
}

export const PAIR_LAW_PRESETS: PairLawPresets = {
  balanced: DEFAULT_PAIR_LAW,
  rigid: { rigidity: 0.01, repulsion: 4000, attraction: 0, range: 0 },
  soft: { rigidity: 0.35, repulsion: 400, attraction: 0, range: 0 },
  sticky: { rigidity: 0.08, repulsion: 2500, attraction: 120, range: 0.25 },
};

export type PairLawPresetName = keyof PairLawPresets;

export function pairLawPreset(name: unknown): Readonly<MotionLaw> | null {
  switch (name) {
    case "balanced":
      return PAIR_LAW_PRESETS.balanced;
    case "rigid":
      return PAIR_LAW_PRESETS.rigid;
    case "soft":
      return PAIR_LAW_PRESETS.soft;
    case "sticky":
      return PAIR_LAW_PRESETS.sticky;
    default:
      return null;
  }
}

export const DEFAULT_WALL_LAW: MotionLaw = {
  rigidity: 0.25,
  repulsion: 2500,
  attraction: 0,
  range: 0,
};

export const WALL_LAW_BOUNDS: Record<MotionLawKey, [number, number]> = {
  rigidity: [0.002, 0.5],
  repulsion: [0, 8000],
  attraction: [0, 400],
  range: [0, 0.5],
};

export const ANNEAL_SETTINGS = {
  min: 0,
  max: 20,
  defaultLevel: 9,
  amplitude: (level: number): number => (level <= 3 ? level / 3 : 1 + (level - 3) * (2 / 7)),
  decayPower: (level: number): number =>
    level <= 3 ? 1.5 : 1.5 - (Math.min(level, 10) - 3) * (1.15 / 7),
  span: (level: number): number => (level <= 3 ? 1 : 1 + (level - 3) * 0.1),
} as const;

export interface AnnealConfiguration {
  level: number;
  amplitude: number;
  decayPower: number;
  span: number;
}

/** The effective, clamped configuration behind one integer dial level. */
export function annealConfiguration(level: number): AnnealConfiguration {
  const rounded = Math.round(level);
  const effective = Math.max(
    ANNEAL_SETTINGS.min,
    Math.min(
      ANNEAL_SETTINGS.max,
      Number.isFinite(rounded) ? rounded : ANNEAL_SETTINGS.defaultLevel,
    ),
  );
  return {
    level: effective,
    amplitude: ANNEAL_SETTINGS.amplitude(effective),
    decayPower: ANNEAL_SETTINGS.decayPower(effective),
    span: ANNEAL_SETTINGS.span(effective),
  };
}

export const DEFAULT_STEP_TIMING = {
  dwell: 0.6,
  move: 0.5,
  correct: 0.4,
  settle: 0.3,
} as const;

export const DEFAULT_STATIC_STEP_TIMING = {
  dwell: 0.4,
  move: 0.28,
  correct: 0.12,
  settle: 0.35,
} as const;

export const PHYSICS_SETTINGS = {
  stepsPerSecond: 120,
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
  wall: 2500,
  wallCap: 0.25,
  inertia: 1 / 6,
  grow: 0.5,
  jiggle: 20,
  jiggleTorque: 12,
  jiggleHz: [2.5, 4] as const,
  drop: 0,
  appear: 0.15,
  inflateFrom: 0.3,
  blend: 0.12,
  maxSpeed: 10,
  maxSpin: 20,
  cell: 1.5,
} as const;

export const STEPS_PER_SECOND = PHYSICS_SETTINGS.stepsPerSecond;

export const BODY_PHYSICS_SETTINGS = {
  jiggle: PHYSICS_SETTINGS.jiggle,
  jiggleTorque: PHYSICS_SETTINGS.jiggleTorque,
} as const;

/** The exact configuration passed from the browser controller to a trajectory build. */
export const TRAJECTORY_PHYSICS_SETTINGS = {
  ...PHYSICS_SETTINGS,
  bodiesJiggle: BODY_PHYSICS_SETTINGS.jiggle,
  bodiesJiggleTorque: BODY_PHYSICS_SETTINGS.jiggleTorque,
} as const;

export interface MotionResponse {
  /** Maximum centre speed, in square sides per simulated second. */
  speedLimit: number;
  /** Damping applied when overlapping bodies are closing. */
  contactDamping: number;
}

export const DEFAULT_MOTION_RESPONSE: MotionResponse = {
  speedLimit: PHYSICS_SETTINGS.maxSpeed,
  contactDamping: PHYSICS_SETTINGS.contactDamping,
};

export const MOTION_RESPONSE_BOUNDS: Record<keyof MotionResponse, [number, number]> = {
  speedLimit: [1, 80],
  contactDamping: [0, 80],
};

/** Apply the two user-facing response controls to the exact trajectory configuration. */
export function trajectoryPhysicsConfiguration(response: MotionResponse) {
  return {
    ...TRAJECTORY_PHYSICS_SETTINGS,
    maxSpeed: response.speedLimit,
    contactDamping: response.contactDamping,
  };
}

export const BLIND_SETTINGS = {
  inflate: 1.12,
  open: 0.12,
  hold: 0.2,
  close: 0.9,
  overlapTolerance: 0.08,
  gridStep: 0.25,
} as const;

export const BLIND_TRAJECTORY_SETTINGS = BLIND_SETTINGS;

/**
 * Share of the moving span over which the new square fades in, in every phase. It fades at its
 * final size: opacity is the only thing that changes (owner request, 2026-09-17).
 */
export const NEW_FRACTION = 0.4;
export const ROLL_MAX = 0.4;
export const BOUND_CLEAR = 0.3;
export const BOUND_GROW = 0.2;
export const BOUND_FADE = 0.12;
/**
 * Share of the moving span between the container finishing its resize, which is when the picture
 * stops shrinking, and the new square starting to fade in. The direction is resize first, square
 * second. At the default beat 0.2 is 0.18 s, against the 0.108 s gap box-first staging left.
 */
export const DEFAULT_ARRIVAL_DELAY_FRACTION = 0.2;
export const ARRIVAL_DELAY_BOUNDS: readonly [number, number] = [0, 0.6];

/** Constants that define the illustrated tween's staging rather than the physical integrator. */
export const TWEEN_ILLUSTRATION_SETTINGS = {
  newFraction: NEW_FRACTION,
  rollMax: ROLL_MAX,
  boundClear: BOUND_CLEAR,
  boundGrow: BOUND_GROW,
  boundFade: BOUND_FADE,
  arrivalDelay: DEFAULT_ARRIVAL_DELAY_FRACTION,
} as const;

/**
 * How far in the new square is at `progress` through its fade: smoothstep, symmetric, with zero
 * slope at both ends, so the first visible frame is nearly transparent and the square settles
 * into full opacity rather than stopping on it. The square is never scaled.
 */
export function newSquareOpacity(progress: number): number {
  const value = Math.max(0, Math.min(1, progress));
  return value * value * (3 - 2 * value);
}

export interface PhysicalPresentationTiming {
  move: number;
  correct: number;
}

/** Map the part of a presented span assigned to body motion onto stored physical progress. */
export function physicalPresentationProgress(
  elapsedMovingSeconds: number,
  presentedMovingSeconds: number,
  timing: PhysicalPresentationTiming,
  motionStartFraction = 0,
  motionEndFraction = 1,
): number {
  const startFraction = Math.max(0, Math.min(1, motionStartFraction));
  const endFraction = Math.max(startFraction, Math.min(1, motionEndFraction));
  const start = presentedMovingSeconds * startFraction;
  const end = presentedMovingSeconds * endFraction;
  const span = end - start;
  const total = timing.move + timing.correct;
  if (span <= 0 || total <= 0) {
    return elapsedMovingSeconds <= start ? 0 : 1;
  }
  const local = Math.max(0, Math.min(span, elapsedMovingSeconds - start));
  const knee = span * (timing.move / total);
  if (local < knee) {
    return knee <= 0 ? 0 : (local / knee) * PHYSICS_SETTINGS.tightenFrom;
  }
  const correction = span - knee;
  return correction <= 0
    ? 1
    : PHYSICS_SETTINGS.tightenFrom +
        ((local - knee) / correction) * (1 - PHYSICS_SETTINGS.tightenFrom);
}

export interface PhysicalPresentationSchedule {
  /** Fraction of the presented moving span at which stored body motion begins. */
  motionStartFraction: number;
  /** Fraction of the presented moving span at which stored body motion completes. */
  motionEndFraction?: number;
  /** Fraction of the presented moving span at which visible container motion begins. */
  containerStartFraction: number;
  /** Fraction of the presented moving span at which visible container motion completes. */
  containerEndFraction?: number;
  /** Fractions over which the arriving square fades into view at its final size. */
  arrivalStartFraction: number;
  arrivalEndFraction: number;
}

export interface PhysicalPresentationState {
  trajectoryProgress: number;
  containerProgress: number;
  appearanceProgress: number;
}

function unit(value: number): number {
  return Math.max(0, Math.min(1, value));
}

function intervalProgress(
  elapsedMovingSeconds: number,
  presentedMovingSeconds: number,
  startFraction: number,
  endFraction: number,
): number {
  const start = presentedMovingSeconds * unit(startFraction);
  const end = presentedMovingSeconds * unit(endFraction);
  if (end <= start) {
    return elapsedMovingSeconds < start ? 0 : 1;
  }
  return unit((elapsedMovingSeconds - start) / (end - start));
}

/** The three independent clocks a physical frame presents, with no DOM or solver dependency. */
export function physicalPresentationState(
  elapsedMovingSeconds: number,
  presentedMovingSeconds: number,
  timing: PhysicalPresentationTiming,
  schedule: PhysicalPresentationSchedule,
): PhysicalPresentationState {
  const arrival = intervalProgress(
    elapsedMovingSeconds,
    presentedMovingSeconds,
    schedule.arrivalStartFraction,
    schedule.arrivalEndFraction,
  );
  return {
    trajectoryProgress: physicalPresentationProgress(
      elapsedMovingSeconds,
      presentedMovingSeconds,
      timing,
      schedule.motionStartFraction,
      schedule.motionEndFraction ?? 1,
    ),
    containerProgress: physicalPresentationProgress(
      elapsedMovingSeconds,
      presentedMovingSeconds,
      timing,
      schedule.containerStartFraction,
      schedule.containerEndFraction ?? 1,
    ),
    appearanceProgress: newSquareOpacity(arrival),
  };
}

/**
 * Whether a physical frame needs its trajectory. The container resizes first, before any body
 * moves or the new square shows, and a run that does not snap to the record (a blind one) sizes
 * its container from the trajectory, so from the resize on it needs the trajectory too.
 */
export function physicalPresentationNeedsTrajectory(
  state: PhysicalPresentationState,
  snapToRecord: boolean,
): boolean {
  const moving = state.trajectoryProgress > 0 && state.trajectoryProgress < 1;
  return (
    state.appearanceProgress > 0 ||
    moving ||
    (!snapToRecord && (state.trajectoryProgress > 0 || state.containerProgress > 0))
  );
}

export type MotionControlScopeReason = "active" | "pack" | "search" | "tween" | "static";

export interface MotionControlScope {
  active: boolean;
  reason: MotionControlScopeReason;
  note: string;
}

/** Whether controls that change simulated kinetics affect the step currently on stage. */
export function motionControlScope(
  style: MotionStyle,
  staticStep: boolean,
  view: "animate" | "pack" | "search" = "animate",
): MotionControlScope {
  if (view === "pack") {
    return {
      active: false,
      reason: "pack",
      note: "Independent Pack has its own controller; Animate physics controls are off.",
    };
  }
  if (view === "search") {
    return {
      active: false,
      reason: "search",
      note: "Search has its own plan; Animate physics controls are off.",
    };
  }
  if (style === "tween") {
    return {
      active: false,
      reason: "tween",
      note: "A interpolates known poses; physics controls are off.",
    };
  }
  if (staticStep) {
    return {
      active: false,
      reason: "static",
      note: "Static append: no solver runs; physics controls are off.",
    };
  }
  return {
    active: true,
    reason: "active",
    note:
      style === "physics"
        ? "B simulates each square; physics controls apply."
        : "C simulates matched blocks as bodies; physics controls apply.",
  };
}
