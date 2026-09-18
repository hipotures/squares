// Every setting that changes a path must pause and return the current step to t=0, never swap a
// newly built trajectory under the old playhead.
() => {
  const api = window.atlasTransitions;
  const before = api.state();
  const beforeLaw = api.law();
  const beforeResponse = api.motionResponse();
  const beforeDelay = api.arrivalDelay();
  const moving = api
    .pairs()
    .find((pair) => pair.kind !== "prefix" && pair.kind !== "shared-picture");
  if (moving === undefined) {
    throw new Error("probe requires a moving transition");
  }
  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setStyle("physics");

  /** @type {Record<string, {before: {playing: boolean, t: number}, after: {playing: boolean, t: number}}>} */
  const results = {};
  const check = (name, change) => {
    api.pause();
    api.seek(api.duration() * 0.6);
    api.play();
    const started = api.state();
    change();
    const ended = api.state();
    results[name] = {
      before: { playing: started.playing, t: started.t },
      after: { playing: ended.playing, t: ended.t },
    };
  };

  check("solver", () => api.setStyle("bodies"));
  check("law", () => api.setLawPreset("rigid"));
  check("anneal", () => api.setAnneal(api.anneal().level === 0 ? 9 : 0));
  check("response", () => {
    const response = api.motionResponse();
    api.setMotionResponse({ speedLimit: response.speedLimit === 10 ? 11 : 10 });
  });
  check("arrival delay", () => {
    const delay = api.arrivalDelay();
    api.setArrivalDelay(delay.fraction === 0.2 ? 0.25 : 0.2);
  });
  check("phase", () => {
    const next = api.phases().find((phase) => phase !== api.state().phase);
    if (next !== undefined) {
      api.setPhase(next);
    }
  });

  api.pause();
  api.setLaw(beforeLaw);
  api.setAnneal(before.anneal);
  api.setMotionResponse(beforeResponse);
  api.setArrivalDelay(beforeDelay.fraction);
  api.setPhase(before.phase);
  api.setStepN(before.n + 1);
  api.setStyle(before.style);
  api.setMode(before.aspect);
  return results;
};
