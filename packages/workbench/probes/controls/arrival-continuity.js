// The arriving square must stay on trajectory sample zero across the body-motion boundary. Before
// this probe existed, the square was drawn at its target during arrival and jumped back to the
// trajectory's initial pose as soon as body motion began. It also reads the drawn square from the
// start of the move to the end of its fade, at 60 Hz: the container resizes first, the delay
// passes, and the square fades in at full size, so every sample is [seconds, opacity, whether the
// transform scales it].
() => {
  const api = window.atlasTransitions;
  const before = api.state();
  const beforeDelay = api.arrivalDelay();
  const moving = api
    .pairs()
    .find((pair) => pair.kind !== "prefix" && pair.kind !== "shared-picture");
  if (moving === undefined) {
    throw new Error("probe requires a moving transition");
  }
  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setPhase("add-then-move");
  api.setArrivalDelay(0.2);
  api.setStyle("physics");
  const schedule = api.schedule();
  const delay = api.arrivalDelay();
  const { index, identity } = api.newSquare();
  const epsilon = Math.min(0.0001, (schedule.blocksStart - schedule.arrive) / 10);
  api.seek(schedule.blocksStart - epsilon);
  const left = api.poseOf(index);
  api.seek(schedule.blocksStart + epsilon);
  const right = api.poseOf(index);
  if (left === null || right === null) {
    throw new Error("arriving square was not drawn at the motion boundary");
  }
  const jump = Math.hypot(left[0] - right[0], left[1] - right[1]);

  /** @type {[number, number, boolean][]} */
  const samples = [];
  const count = Math.floor((schedule.arrived - schedule.moveStart) * 60);
  const instants = Array.from({ length: count + 1 }, (_, k) => schedule.moveStart + k / 60);
  for (const t of [...instants, schedule.arrived]) {
    api.seek(t);
    const square = document.querySelector(`#squares g[data-identity="${identity}"]`);
    if (square === null) {
      throw new Error(`probe requires the new square, identity ${identity}`);
    }
    samples.push([
      t,
      Number(square.getAttribute("opacity")),
      /scale\(/.test(square.getAttribute("transform") ?? ""),
    ]);
  }

  api.setArrivalDelay(beforeDelay.fraction);
  api.setPhase(before.phase);
  api.setStepN(before.n + 1);
  api.setStyle(before.style);
  api.setMode(before.aspect);
  return { jump, left, right, schedule, delay, samples };
};
