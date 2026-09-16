export interface MotionPose {
  x: number;
  y: number;
  angleRadians: number;
  /** Physical side in square-side units; defaults to one. */
  size?: number;
  /** False excludes an invisible illustration square from geometry, but not its reported pose. */
  active?: boolean;
}

export interface MotionFrame {
  timeSeconds: number;
  containerSide: number;
  poses: readonly MotionPose[];
  /** Optional shared browser presentation clocks for event localization. */
  trajectoryProgress?: number;
  containerProgress?: number;
  appearanceProgress?: number;
  /** Optional simulator-native diagnostics for the interval ending at this frame. */
  simulatorPairPenetration?: number;
  nearPairs?: number;
}

export interface MotionTrace {
  frames: readonly MotionFrame[];
  target?: readonly MotionPose[];
  squareSide?: number;
  contactTolerance?: number;
  reversalMinimumDisplacement?: number;
  /** Wall-clock boundary at which established bodies first begin their motion. */
  motionStartTimeSeconds?: number;
  /** Wall-clock boundary at which the displayed correction/landing tail begins. */
  landingStartTimeSeconds?: number;
}

export interface Distribution {
  count: number;
  minimum: number;
  maximum: number;
  mean: number;
  rootMeanSquare: number;
  p95: number;
}

export interface MotionSummary {
  samples: {
    frames: number;
    squares: number;
    durationSeconds: number;
    intervals: number;
  };
  translation: {
    displacement: Distribution;
    speed: Distribution;
    acceleration: Distribution;
    jerk: Distribution;
    reversals: {
      count: number;
      opportunities: number;
      ratio: number;
      minimumDisplacementUnits: number;
    };
    localization: {
      largestDisplacement: DisplacementEvent | null;
      strongestReversal: ReversalEvent | null;
      preLanding: MotionSegment | null;
      landing: MotionSegment | null;
      motionStartBoundary: MotionSegment | null;
      finalInterval: MotionSegment;
    };
    appearances: {
      count: number;
      reportedPoseDisplacement: Distribution;
      largestReportedPoseDisplacement: DisplacementEvent | null;
    };
  };
  rotation: {
    displacementRadians: Distribution;
    speedRadiansPerSecond: Distribution;
    accelerationRadiansPerSecondSquared: Distribution;
  };
  presentedGeometry: {
    pairPenetration: Distribution;
    wallPenetration: Distribution;
    contactPairs: { maximum: number; mean: number; final: number };
    nearestNeighborGap: Distribution;
  };
  simulatorNative: {
    pairPenetration: Distribution;
    nearPairs: Distribution;
  } | null;
  endpoint: {
    maximumCenterError: number;
    rootMeanSquareCenterError: number;
    maximumAngleErrorRadians: number;
  } | null;
}

export interface DisplacementEvent {
  squareIndex: number;
  endingFrameIndex: number;
  endingTimeSeconds: number;
  trajectoryProgress?: number;
  displacement: number;
}

export interface ReversalEvent {
  squareIndex: number;
  endingFrameIndex: number;
  endingTimeSeconds: number;
  trajectoryProgress?: number;
  cosine: number;
  previousDisplacement: number;
  displacement: number;
}

export interface MotionSegment {
  startTimeSeconds: number;
  endTimeSeconds: number;
  intervals: number;
  displacement: Distribution;
  reversals: {
    count: number;
    opportunities: number;
    ratio: number;
  };
}

const EMPTY_DISTRIBUTION: Distribution = Object.freeze({
  count: 0,
  minimum: 0,
  maximum: 0,
  mean: 0,
  rootMeanSquare: 0,
  p95: 0,
});

function finite(value: number, label: string): number {
  if (!Number.isFinite(value)) {
    throw new RangeError(`${label} must be finite`);
  }
  return value;
}

function positive(value: number, label: string): number {
  if (finite(value, label) <= 0) {
    throw new RangeError(`${label} must be positive`);
  }
  return value;
}

/** Keep JSON and equality checks stable without throwing away meaningful trajectory precision. */
export function stableNumber(value: number): number {
  finite(value, "metric");
  const rounded = Number(value.toPrecision(13));
  return Object.is(rounded, -0) ? 0 : rounded;
}

export function distribution(values: readonly number[]): Distribution {
  if (values.length === 0) {
    return { ...EMPTY_DISTRIBUTION };
  }
  const checked = values.map((value) => finite(value, "distribution sample"));
  const sorted = checked.slice().sort((left, right) => left - right);
  const total = checked.reduce((sum, value) => sum + value, 0);
  const squares = checked.reduce((sum, value) => sum + value * value, 0);
  const p95Index = Math.min(sorted.length - 1, Math.ceil(sorted.length * 0.95) - 1);
  return {
    count: checked.length,
    minimum: stableNumber(sorted[0] ?? 0),
    maximum: stableNumber(sorted.at(-1) ?? 0),
    mean: stableNumber(total / checked.length),
    rootMeanSquare: stableNumber(Math.sqrt(squares / checked.length)),
    p95: stableNumber(sorted[p95Index] ?? 0),
  };
}

function squareProjectionRadius(
  axisX: number,
  axisY: number,
  pose: MotionPose,
  half: number,
): number {
  const cosine = Math.cos(pose.angleRadians);
  const sine = Math.sin(pose.angleRadians);
  return (
    half * (Math.abs(axisX * cosine + axisY * sine) + Math.abs(-axisX * sine + axisY * cosine))
  );
}

/**
 * Signed separating-axis gap for equal squares. Positive means separated, zero touching, and
 * negative means penetration. For a separated diagonal pair this is the strongest face-normal
 * separation, not Euclidean polygon distance; the unit and definition are declared in the report.
 */
export function pairFaceNormalGap(left: MotionPose, right: MotionPose, squareSide = 1): number {
  positive(squareSide, "square side");
  const leftHalf = positive(left.size ?? squareSide, "left square size") / 2;
  const rightHalf = positive(right.size ?? squareSide, "right square size") / 2;
  const dx = finite(right.x - left.x, "pair x delta");
  const dy = finite(right.y - left.y, "pair y delta");
  const axes: [number, number][] = [];
  for (const angle of [left.angleRadians, right.angleRadians]) {
    finite(angle, "square angle");
    axes.push([Math.cos(angle), Math.sin(angle)], [-Math.sin(angle), Math.cos(angle)]);
  }
  let maximumSeparation = -Infinity;
  for (const [axisX, axisY] of axes) {
    const separation =
      Math.abs(dx * axisX + dy * axisY) -
      squareProjectionRadius(axisX, axisY, left, leftHalf) -
      squareProjectionRadius(axisX, axisY, right, rightHalf);
    maximumSeparation = Math.max(maximumSeparation, separation);
  }
  return stableNumber(maximumSeparation);
}

function checkFrames(frames: readonly MotionFrame[]): number {
  if (frames.length < 2) {
    throw new RangeError("motion trace requires at least two frames");
  }
  const count = frames[0]?.poses.length ?? 0;
  if (count < 1) {
    throw new RangeError("motion trace requires at least one square");
  }
  let previousTime = -Infinity;
  for (const [frameIndex, frame] of frames.entries()) {
    positive(frame.containerSide, `frame ${frameIndex} container side`);
    if (frame.poses.length !== count) {
      throw new RangeError("every motion frame must contain the same squares in the same order");
    }
    const time = finite(frame.timeSeconds, `frame ${frameIndex} time`);
    if (time <= previousTime) {
      throw new RangeError("motion frame times must increase strictly");
    }
    previousTime = time;
    for (const pose of frame.poses) {
      finite(pose.x, "square x");
      finite(pose.y, "square y");
      finite(pose.angleRadians, "square angle");
      positive(pose.size ?? 1, "square size");
    }
  }
  return count;
}

function quarterTurnAngleError(left: number, right: number): number {
  const period = Math.PI / 2;
  const remainder = (((left - right) % period) + period) % period;
  return Math.min(remainder, period - remainder);
}

function endpoint(
  finalPoses: readonly MotionPose[],
  target: readonly MotionPose[] | undefined,
): MotionSummary["endpoint"] {
  if (target === undefined) {
    return null;
  }
  if (target.length !== finalPoses.length) {
    throw new RangeError("motion target must contain every trace square in trace order");
  }
  const centerErrors: number[] = [];
  const angleErrors: number[] = [];
  for (let index = 0; index < target.length; index += 1) {
    const actual = finalPoses[index];
    const expected = target[index];
    if (actual === undefined || expected === undefined) {
      throw new RangeError("motion endpoint is incomplete");
    }
    centerErrors.push(Math.hypot(actual.x - expected.x, actual.y - expected.y));
    angleErrors.push(quarterTurnAngleError(actual.angleRadians, expected.angleRadians));
  }
  return {
    maximumCenterError: stableNumber(Math.max(...centerErrors)),
    rootMeanSquareCenterError: stableNumber(
      Math.sqrt(centerErrors.reduce((sum, value) => sum + value * value, 0) / centerErrors.length),
    ),
    maximumAngleErrorRadians: stableNumber(Math.max(...angleErrors)),
  };
}

/** Analyze a square-motion trace without a DOM, canvas, SVG, or browser. */
export function analyzeMotionTrace(trace: MotionTrace): MotionSummary {
  const squareSide = positive(trace.squareSide ?? 1, "square side");
  const contactTolerance = finite(trace.contactTolerance ?? 0.01, "contact tolerance");
  const reversalMinimum = finite(
    trace.reversalMinimumDisplacement ?? 1e-6,
    "reversal minimum displacement",
  );
  if (contactTolerance < 0 || reversalMinimum < 0) {
    throw new RangeError("motion tolerances cannot be negative");
  }
  const squareCount = checkFrames(trace.frames);
  const displacements: number[] = [];
  const speeds: number[] = [];
  const accelerations: number[] = [];
  const jerks: number[] = [];
  const angularDisplacements: number[] = [];
  const angularSpeeds: number[] = [];
  const angularAccelerations: number[] = [];
  const pairPenetration: number[] = [];
  const wallPenetration: number[] = [];
  const simulatorPairPenetration: number[] = [];
  const nearestGaps: number[] = [];
  const simulatorNearPairs: number[] = [];
  const contactCounts: number[] = [];
  const velocities: { x: number; y: number; dt: number }[][] = [];
  const angularVelocities: { value: number; dt: number }[][] = [];
  const displacementEvents: DisplacementEvent[] = [];
  const appearanceEvents: DisplacementEvent[] = [];
  const reversalEvents: ReversalEvent[] = [];
  const reversalOpportunityEvents: Pick<
    DisplacementEvent,
    "squareIndex" | "endingFrameIndex" | "endingTimeSeconds"
  >[] = [];
  let reversalCount = 0;
  let reversalOpportunities = 0;

  for (let frameIndex = 0; frameIndex < trace.frames.length; frameIndex += 1) {
    const frame = trace.frames[frameIndex];
    if (frame === undefined) {
      throw new RangeError("motion frame is missing");
    }
    let nearestGap = Infinity;
    let contacts = 0;
    let measuredPairPenetration = 0;
    let measuredWallPenetration = 0;
    for (let left = 0; left < squareCount; left += 1) {
      const first = frame.poses[left];
      if (first === undefined) {
        throw new RangeError("motion square is missing");
      }
      if (first.active === false) {
        continue;
      }
      const half = (first.size ?? squareSide) / 2;
      const radius =
        half * (Math.abs(Math.cos(first.angleRadians)) + Math.abs(Math.sin(first.angleRadians)));
      measuredWallPenetration = Math.max(
        measuredWallPenetration,
        radius - first.x,
        first.x + radius - frame.containerSide,
        radius - first.y,
        first.y + radius - frame.containerSide,
      );
      for (let right = left + 1; right < squareCount; right += 1) {
        const second = frame.poses[right];
        if (second === undefined) {
          throw new RangeError("motion square is missing");
        }
        if (second.active === false) {
          continue;
        }
        const gap = pairFaceNormalGap(first, second, squareSide);
        nearestGap = Math.min(nearestGap, gap);
        measuredPairPenetration = Math.max(measuredPairPenetration, -gap);
        if (Math.abs(gap) <= contactTolerance) {
          contacts += 1;
        }
      }
    }
    if (Number.isFinite(nearestGap)) {
      nearestGaps.push(nearestGap);
    }
    contactCounts.push(contacts);
    pairPenetration.push(Math.max(0, measuredPairPenetration));
    wallPenetration.push(Math.max(0, measuredWallPenetration));
    if (frame.simulatorPairPenetration !== undefined) {
      simulatorPairPenetration.push(
        finite(frame.simulatorPairPenetration, "simulator pair penetration"),
      );
    }
    if (frame.nearPairs !== undefined) {
      simulatorNearPairs.push(finite(frame.nearPairs, "simulator near pairs"));
    }
    if (frameIndex === 0) {
      continue;
    }
    const previous = trace.frames[frameIndex - 1];
    if (previous === undefined) {
      throw new RangeError("previous motion frame is missing");
    }
    const dt = frame.timeSeconds - previous.timeSeconds;
    const intervalVelocities: { x: number; y: number; dt: number }[] = [];
    const intervalAngular: { value: number; dt: number }[] = [];
    for (let square = 0; square < squareCount; square += 1) {
      const from = previous.poses[square];
      const to = frame.poses[square];
      if (from === undefined || to === undefined) {
        throw new RangeError("motion square is missing");
      }
      if (from.active === false || to.active === false) {
        if (from.active === false && to.active !== false) {
          appearanceEvents.push({
            squareIndex: square,
            endingFrameIndex: frameIndex,
            endingTimeSeconds: stableNumber(frame.timeSeconds),
            ...(frame.trajectoryProgress === undefined
              ? {}
              : { trajectoryProgress: stableNumber(frame.trajectoryProgress) }),
            displacement: stableNumber(Math.hypot(to.x - from.x, to.y - from.y)),
          });
        }
        intervalVelocities.push({ x: Number.NaN, y: Number.NaN, dt });
        intervalAngular.push({ value: Number.NaN, dt });
        continue;
      }
      const dx = to.x - from.x;
      const dy = to.y - from.y;
      const distance = Math.hypot(dx, dy);
      const da = to.angleRadians - from.angleRadians;
      displacements.push(distance);
      displacementEvents.push({
        squareIndex: square,
        endingFrameIndex: frameIndex,
        endingTimeSeconds: stableNumber(frame.timeSeconds),
        ...(frame.trajectoryProgress === undefined
          ? {}
          : { trajectoryProgress: stableNumber(frame.trajectoryProgress) }),
        displacement: stableNumber(distance),
      });
      speeds.push(distance / dt);
      angularDisplacements.push(Math.abs(da));
      angularSpeeds.push(Math.abs(da) / dt);
      intervalVelocities.push({ x: dx / dt, y: dy / dt, dt });
      intervalAngular.push({ value: da / dt, dt });

      if (frameIndex >= 2) {
        const before = trace.frames[frameIndex - 2]?.poses[square];
        if (before === undefined) {
          throw new RangeError("motion square is missing");
        }
        const previousDx = from.x - before.x;
        const previousDy = from.y - before.y;
        const previousDistance = Math.hypot(previousDx, previousDy);
        if (
          before.active !== false &&
          distance >= reversalMinimum &&
          previousDistance >= reversalMinimum
        ) {
          reversalOpportunities += 1;
          reversalOpportunityEvents.push({
            squareIndex: square,
            endingFrameIndex: frameIndex,
            endingTimeSeconds: stableNumber(frame.timeSeconds),
          });
          const dot = dx * previousDx + dy * previousDy;
          if (dot < 0) {
            reversalCount += 1;
            reversalEvents.push({
              squareIndex: square,
              endingFrameIndex: frameIndex,
              endingTimeSeconds: stableNumber(frame.timeSeconds),
              ...(frame.trajectoryProgress === undefined
                ? {}
                : { trajectoryProgress: stableNumber(frame.trajectoryProgress) }),
              cosine: stableNumber(dot / (distance * previousDistance)),
              previousDisplacement: stableNumber(previousDistance),
              displacement: stableNumber(distance),
            });
          }
        }
      }
    }
    velocities.push(intervalVelocities);
    angularVelocities.push(intervalAngular);
  }

  const accelerationVectors: { x: number; y: number; dt: number }[][] = [];
  for (let interval = 1; interval < velocities.length; interval += 1) {
    const current = velocities[interval];
    const previous = velocities[interval - 1];
    const currentAngular = angularVelocities[interval];
    const previousAngular = angularVelocities[interval - 1];
    if (
      current === undefined ||
      previous === undefined ||
      currentAngular === undefined ||
      previousAngular === undefined
    ) {
      throw new RangeError("motion velocity interval is missing");
    }
    const intervalAcceleration: { x: number; y: number; dt: number }[] = [];
    for (let square = 0; square < squareCount; square += 1) {
      const velocity = current[square];
      const priorVelocity = previous[square];
      const angular = currentAngular[square];
      const priorAngular = previousAngular[square];
      if (
        velocity === undefined ||
        priorVelocity === undefined ||
        angular === undefined ||
        priorAngular === undefined
      ) {
        throw new RangeError("motion velocity is missing");
      }
      if (
        !Number.isFinite(velocity.x) ||
        !Number.isFinite(velocity.y) ||
        !Number.isFinite(priorVelocity.x) ||
        !Number.isFinite(priorVelocity.y) ||
        !Number.isFinite(angular.value) ||
        !Number.isFinite(priorAngular.value)
      ) {
        intervalAcceleration.push({ x: Number.NaN, y: Number.NaN, dt: velocity.dt });
        continue;
      }
      const dt = (velocity.dt + priorVelocity.dt) / 2;
      const ax = (velocity.x - priorVelocity.x) / dt;
      const ay = (velocity.y - priorVelocity.y) / dt;
      accelerations.push(Math.hypot(ax, ay));
      angularAccelerations.push(Math.abs(angular.value - priorAngular.value) / dt);
      intervalAcceleration.push({ x: ax, y: ay, dt });
    }
    accelerationVectors.push(intervalAcceleration);
  }
  for (let interval = 1; interval < accelerationVectors.length; interval += 1) {
    const current = accelerationVectors[interval];
    const previous = accelerationVectors[interval - 1];
    if (current === undefined || previous === undefined) {
      throw new RangeError("motion acceleration interval is missing");
    }
    for (let square = 0; square < squareCount; square += 1) {
      const acceleration = current[square];
      const priorAcceleration = previous[square];
      if (acceleration === undefined || priorAcceleration === undefined) {
        throw new RangeError("motion acceleration is missing");
      }
      if (
        !Number.isFinite(acceleration.x) ||
        !Number.isFinite(acceleration.y) ||
        !Number.isFinite(priorAcceleration.x) ||
        !Number.isFinite(priorAcceleration.y)
      ) {
        continue;
      }
      const dt = (acceleration.dt + priorAcceleration.dt) / 2;
      jerks.push(
        Math.hypot(acceleration.x - priorAcceleration.x, acceleration.y - priorAcceleration.y) / dt,
      );
    }
  }

  const first = trace.frames[0];
  const final = trace.frames.at(-1);
  if (first === undefined || final === undefined) {
    throw new RangeError("motion trace endpoints are missing");
  }
  const segment = (
    events: readonly DisplacementEvent[],
    reversals: readonly ReversalEvent[],
    startTimeSeconds: number,
    endTimeSeconds: number,
    startExclusive = false,
  ): MotionSegment => {
    const opportunities = reversalOpportunityEvents.filter(
      (event) =>
        (startExclusive
          ? event.endingTimeSeconds > startTimeSeconds
          : event.endingTimeSeconds >= startTimeSeconds) &&
        event.endingTimeSeconds <= endTimeSeconds,
    ).length;
    return {
      startTimeSeconds: stableNumber(startTimeSeconds),
      endTimeSeconds: stableNumber(endTimeSeconds),
      intervals: new Set(events.map((event) => event.endingFrameIndex)).size,
      displacement: distribution(events.map((event) => event.displacement)),
      reversals: {
        count: reversals.length,
        opportunities,
        ratio: stableNumber(opportunities === 0 ? 0 : reversals.length / opportunities),
      },
    };
  };
  const eventRange = (start: number, end: number) =>
    displacementEvents.filter(
      (event) => event.endingTimeSeconds >= start && event.endingTimeSeconds <= end,
    );
  const reversalRange = (start: number, end: number) =>
    reversalEvents.filter(
      (event) => event.endingTimeSeconds >= start && event.endingTimeSeconds <= end,
    );
  const finalStart = trace.frames.at(-2)?.timeSeconds ?? final.timeSeconds;
  let preLanding: MotionSegment | null = null;
  let landing: MotionSegment | null = null;
  if (trace.landingStartTimeSeconds !== undefined) {
    const landingStart = finite(trace.landingStartTimeSeconds, "landing start time");
    if (landingStart < first.timeSeconds || landingStart > final.timeSeconds) {
      throw new RangeError("landing start time must lie within the motion trace");
    }
    const before = displacementEvents.filter((event) => event.endingTimeSeconds < landingStart);
    const beforeReversals = reversalEvents.filter(
      (event) => event.endingTimeSeconds < landingStart,
    );
    preLanding = segment(before, beforeReversals, first.timeSeconds, landingStart);
    landing = segment(
      eventRange(landingStart, final.timeSeconds),
      reversalRange(landingStart, final.timeSeconds),
      landingStart,
      final.timeSeconds,
    );
  }
  const largestDisplacement = displacementEvents.reduce<DisplacementEvent | null>(
    (largest, event) =>
      largest === null || event.displacement > largest.displacement ? event : largest,
    null,
  );
  const strongestReversal = reversalEvents.reduce<ReversalEvent | null>(
    (strongest, event) =>
      strongest === null || event.cosine < strongest.cosine ? event : strongest,
    null,
  );
  const largestAppearanceDisplacement = appearanceEvents.reduce<DisplacementEvent | null>(
    (largest, event) =>
      largest === null || event.displacement > largest.displacement ? event : largest,
    null,
  );
  let motionStartBoundary: MotionSegment | null = null;
  if (trace.motionStartTimeSeconds !== undefined) {
    const motionStart = finite(trace.motionStartTimeSeconds, "motion start time");
    if (motionStart < first.timeSeconds || motionStart > final.timeSeconds) {
      throw new RangeError("motion start time must lie within the motion trace");
    }
    const firstMotionFrameTime =
      trace.frames.find((frame) => frame.timeSeconds >= motionStart)?.timeSeconds ??
      final.timeSeconds;
    const priorFrameTime =
      [...trace.frames].reverse().find((frame) => frame.timeSeconds < firstMotionFrameTime)
        ?.timeSeconds ?? first.timeSeconds;
    motionStartBoundary = segment(
      displacementEvents.filter(
        (event) =>
          event.endingTimeSeconds > priorFrameTime &&
          event.endingTimeSeconds <= firstMotionFrameTime,
      ),
      reversalEvents.filter(
        (event) =>
          event.endingTimeSeconds > priorFrameTime &&
          event.endingTimeSeconds <= firstMotionFrameTime,
      ),
      priorFrameTime,
      firstMotionFrameTime,
      true,
    );
  }
  return {
    samples: {
      frames: trace.frames.length,
      squares: squareCount,
      durationSeconds: stableNumber(final.timeSeconds - first.timeSeconds),
      intervals: trace.frames.length - 1,
    },
    translation: {
      displacement: distribution(displacements),
      speed: distribution(speeds),
      acceleration: distribution(accelerations),
      jerk: distribution(jerks),
      reversals: {
        count: reversalCount,
        opportunities: reversalOpportunities,
        ratio: stableNumber(
          reversalOpportunities === 0 ? 0 : reversalCount / reversalOpportunities,
        ),
        minimumDisplacementUnits: reversalMinimum,
      },
      localization: {
        largestDisplacement,
        strongestReversal,
        preLanding,
        landing,
        motionStartBoundary,
        finalInterval: segment(
          displacementEvents.filter(
            (event) =>
              event.endingTimeSeconds > finalStart && event.endingTimeSeconds <= final.timeSeconds,
          ),
          reversalEvents.filter(
            (event) =>
              event.endingTimeSeconds > finalStart && event.endingTimeSeconds <= final.timeSeconds,
          ),
          finalStart,
          final.timeSeconds,
          true,
        ),
      },
      appearances: {
        count: appearanceEvents.length,
        reportedPoseDisplacement: distribution(appearanceEvents.map((event) => event.displacement)),
        largestReportedPoseDisplacement: largestAppearanceDisplacement,
      },
    },
    rotation: {
      displacementRadians: distribution(angularDisplacements),
      speedRadiansPerSecond: distribution(angularSpeeds),
      accelerationRadiansPerSecondSquared: distribution(angularAccelerations),
    },
    presentedGeometry: {
      pairPenetration: distribution(pairPenetration),
      wallPenetration: distribution(wallPenetration),
      contactPairs: {
        maximum: Math.max(...contactCounts),
        mean: stableNumber(
          contactCounts.reduce((sum, value) => sum + value, 0) / contactCounts.length,
        ),
        final: contactCounts.at(-1) ?? 0,
      },
      nearestNeighborGap: distribution(nearestGaps),
    },
    simulatorNative:
      simulatorPairPenetration.length === trace.frames.length &&
      simulatorNearPairs.length === trace.frames.length
        ? {
            pairPenetration: distribution(simulatorPairPenetration),
            nearPairs: distribution(simulatorNearPairs),
          }
        : null,
    endpoint: endpoint(final.poses, trace.target),
  };
}

/** Exact, allocation-free replay comparison for deterministic headless traces. */
export function identicalMotionFrames(
  left: readonly MotionFrame[],
  right: readonly MotionFrame[],
): boolean {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((frame, frameIndex) => {
    const other = right[frameIndex];
    return (
      other !== undefined &&
      frame.timeSeconds === other.timeSeconds &&
      frame.containerSide === other.containerSide &&
      frame.trajectoryProgress === other.trajectoryProgress &&
      frame.containerProgress === other.containerProgress &&
      frame.appearanceProgress === other.appearanceProgress &&
      frame.simulatorPairPenetration === other.simulatorPairPenetration &&
      frame.nearPairs === other.nearPairs &&
      frame.poses.length === other.poses.length &&
      frame.poses.every((pose, poseIndex) => {
        const otherPose = other.poses[poseIndex];
        return (
          otherPose !== undefined &&
          pose.x === otherPose.x &&
          pose.y === otherPose.y &&
          pose.angleRadians === otherPose.angleRadians &&
          pose.size === otherPose.size &&
          pose.active === otherPose.active
        );
      })
    );
  });
}
