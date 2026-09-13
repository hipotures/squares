// Set the run going at o.speed and say where it stood as it started.
/** @param {{speed: number}} o */ (o) => {
  const api = window.atlasTransitions;
  api.setSpeed(o.speed);
  api.play();
  return { playing: api.state().playing, steps: api.optimizeState().steps };
};
