// The headline through one step, sampled across its whole duration: the still `n =` slot's
// opacity and transform, how far each rolling slot faded, and which parts of each copy are
// hidden. o.n is the step's n.
(o) => {
  const api = window.atlasTransitions;
  api.setStepN(o.n);
  const total = api.duration();
  const still = /** @type {HTMLElement} */ (document.getElementById("numeral-static"));
  const slotA = /** @type {HTMLElement} */ (document.getElementById("numeral-a"));
  const slotB = /** @type {HTMLElement} */ (document.getElementById("numeral-b"));
  const shown = (/** @type {Element | null} */ e) =>
    e ? getComputedStyle(e).visibility : "absent";
  const samples = [];
  for (let k = 0; k <= 12; k++) {
    api.seek((total * k) / 12);
    const numeral = /** @type {HTMLElement | null} */ (still.querySelector(".numeral"));
    samples.push({
      stillOpacity: Number(getComputedStyle(still).opacity),
      stillTransform: numeral ? numeral.style.transform : "absent",
      fadeA: Number(getComputedStyle(slotA).opacity),
      fadeB: Number(getComputedStyle(slotB).opacity),
    });
  }
  return {
    samples,
    stillEquals: shown(still.querySelector(".katex .mrel")),
    stillDigits: shown(still.querySelector(".katex .mord.mathbf")),
    rollingEquals: shown(slotA.querySelector(".katex .mrel")),
    rollingDigits: shown(slotA.querySelector(".katex .mord.mathbf")),
  };
};
