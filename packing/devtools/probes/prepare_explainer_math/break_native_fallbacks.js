// Negative control for required-font failure: falsely retain the rendered marker so the
// semantic-MathML fallback stays hidden and the host oracle must reject the page.
() => {
  for (const node of [...document.querySelectorAll(".kpress-math")].slice(0, 3)) {
    /** @type {HTMLElement} */ (node).dataset.kpressMathRendered = "true";
  }
};
