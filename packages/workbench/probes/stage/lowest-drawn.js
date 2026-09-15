// The lowest point the packing drawing reaches through one step, in stage units: every square
// and the container, sampled at evenly spaced instants. o.n is the step's n, o.style the style.
(o) => {
  const api = window.atlasTransitions;
  api.setStyle(o.style);
  api.setStepN(o.n);
  const stage = /** @type {HTMLElement} */ (
    document.getElementById("stage")
  ).getBoundingClientRect();
  const scale = stage.width / 1920;
  const total = api.duration();
  let deepest = -Infinity;
  for (let k = 0; k <= 48; k++) {
    api.seek((total * k) / 48);
    for (const el of document.querySelectorAll("#squares > *, #container")) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 || r.height > 0) {
        deepest = Math.max(deepest, (r.bottom - stage.top) / scale);
      }
    }
  }
  return deepest;
};
