// The arriving square must stay on trajectory sample zero across the body-motion boundary. Before
// this probe existed, the square was drawn at its target during arrival and jumped back to the
// trajectory's initial pose as soon as body motion began.
() => {
  const api = window.atlasTransitions;
  const before = api.state();
  const beforeDelay = api.containerDelay();
  const moving = api
    .pairs()
    .find((pair) => pair.kind !== "prefix" && pair.kind !== "shared-picture");
  if (moving === undefined) {
    throw new Error("probe requires a moving transition");
  }
  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setPhase("add-then-move");
  api.setContainerDelay(0.2);
  api.setStyle("physics");
  const schedule = api.schedule();
  const index = api.newSquare().index;
  const epsilon = Math.min(0.0001, (schedule.blocksStart - schedule.arrive) / 10);
  api.seek(schedule.blocksStart - epsilon);
  const left = api.poseOf(index);
  api.seek(schedule.blocksStart + epsilon);
  const right = api.poseOf(index);
  if (left === null || right === null) {
    throw new Error("arriving square was not drawn at the motion boundary");
  }
  const jump = Math.hypot(left[0] - right[0], left[1] - right[1]);

  api.setContainerDelay(beforeDelay.fraction);
  api.setPhase(before.phase);
  api.setStepN(before.n + 1);
  api.setStyle(before.style);
  api.setMode(before.aspect);
  return { jump, left, right, schedule };
};
