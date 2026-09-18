// The arrival-delay control drives the schedule. The range input is moved the way a viewer moves
// it, by a change event, and the API, the schedule and the readout must all follow; the API then
// clamps an out-of-range value to the bounds and ignores one that is not a number. The page's
// state is put back afterwards.
() => {
  const api = window.atlasTransitions;
  const before = api.state();
  const beforeDelay = api.arrivalDelay();
  const moving = api
    .pairs()
    .find((pair) => pair.kind !== "prefix" && pair.kind !== "shared-picture");
  const input = /** @type {HTMLInputElement | null} */ (
    document.getElementById("motion-arrival-delay")
  );
  const readout = document.getElementById("motion-arrival-delay-val");
  if (moving === undefined || input === null || readout === null) {
    throw new Error("probe requires a moving transition and the arrival-delay control");
  }
  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setStyle("tween");
  api.setPhase("add-then-move");
  api.setArrivalDelay(beforeDelay.dflt);
  const read = () => ({
    delay: api.arrivalDelay(),
    schedule: api.schedule(),
    duration: api.duration(),
    input: { value: input.value, min: input.min, max: input.max, step: input.step },
    readout: readout.textContent,
  });
  const initial = read();
  input.value = "0.4";
  input.dispatchEvent(new Event("change", { bubbles: true }));
  const moved = read();
  const clamped = api.setArrivalDelay(5).fraction;
  // The API takes a fraction, and a value that is not one is ignored.
  const ignored = api.setArrivalDelay(
    /** @type {number} */ (/** @type {unknown} */ ("later")),
  ).fraction;
  const lowest = api.setArrivalDelay(-1).fraction;

  api.setArrivalDelay(beforeDelay.fraction);
  api.setPhase(before.phase);
  api.setStepN(before.n + 1);
  api.setStyle(before.style);
  api.setMode(before.aspect);
  return { initial, moved, clamped, ignored, lowest };
};
