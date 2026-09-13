// An open-ended run from the grid start, read before, during and after two batches of
// steps. o.n is the size, o.steps the size of each batch.
/** @param {{n: number, steps: number}} o */ (o) => {
  const api = window.atlasTransitions;
  api.setStepN(o.n);
  api.setInitial("grid");
  const a = api.optimizeState();
  api.optimizeStep(o.steps);
  const b = api.optimizeState();
  api.optimizeStep(o.steps);
  const c = api.optimizeState();
  return { a, b, c };
};
