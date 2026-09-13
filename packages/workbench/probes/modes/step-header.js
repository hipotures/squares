// The step header in each mode, with the stage's own box beside it: the tag is absolutely
// positioned, so hiding it must move nothing. o.n is the size Pack is put on.
/** @param {{n: number}} o */
(o) => {
  const api = window.atlasTransitions;
  const e = document.getElementById("kind-tag");
  const stage = document.getElementById("stage");
  if (e == null || stage == null) {
    throw new Error("probe requires #kind-tag and #stage");
  }
  const box = () => stage.getBoundingClientRect().toJSON();
  api.setMode("pack");
  api.setStepN(o.n);
  const packed = { hidden: e.getClientRects().length === 0, stage: box() };
  api.setMode("animate");
  const swept = { hidden: e.getClientRects().length === 0, stage: box(), text: e.textContent };
  api.setMode("pack");
  api.setStepN(o.n);
  return { packed, swept };
};
