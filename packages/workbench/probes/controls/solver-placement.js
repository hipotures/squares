// Where the solver select sits: which box holds it, whether that is the step-animation
// group, what the box's neighbours are called, and whether the select has a width of its own.
() => {
  const sel = document.getElementById("style-select");
  if (sel == null) {
    throw new Error("probe requires #style-select");
  }
  const box = sel.closest(".subpanel");
  if (box == null) {
    throw new Error("solver select is outside a subpanel");
  }
  const row = box.parentElement;
  if (row == null) {
    throw new Error("solver subpanel has no row");
  }
  /** @param {Element} e */
  const title = (e) => {
    const t = e.querySelector(".box-title");
    return t?.textContent?.trim() ?? null;
  };
  return {
    title: title(box),
    inStepGroup: box.id === "step-anim-box",
    siblings: Array.from(row.children)
      .filter((e) => e.classList.contains("subpanel"))
      .map(title),
    width: getComputedStyle(sel).width,
  };
};
