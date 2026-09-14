// The facts panel through one step, sampled at evenly spaced instants. For each slot: whether the
// n and n + 1 layers draw it identically, and, at every instant, the opacity each drawn part is
// seen at (the product of its own and every ancestor's up to the panel). A part is an SVG, or an
// element with no element children; its key is its markup and its box, so a key found in both
// layers is the same glyph in the same place. o.n is the step's n.
(o) => {
  const api = window.atlasTransitions;
  api.setStepN(o.n);
  const total = api.duration();
  const facts = /** @type {HTMLElement} */ (document.getElementById("facts"));
  const layers = ["facts-a", "facts-b"].map(
    (id) => /** @type {HTMLElement} */ (document.getElementById(id)),
  );
  const partsOf = (/** @type {Element | undefined} */ root) => {
    /** @type {Element[]} */
    const out = [];
    const walk = (/** @type {Element} */ el) => {
      for (const child of el.children) {
        if (child instanceof SVGElement || child.children.length === 0) {
          // A part with no box draws nothing (KaTeX's spacing spans), so it has no opacity to see.
          const r = child.getBoundingClientRect();
          if (r.width > 0 || r.height > 0) {
            out.push(child);
          }
        } else {
          walk(child);
        }
      }
    };
    if (root) {
      walk(root);
    }
    return out;
  };
  // The markup without the opacity the page itself writes on each part, which differs between the
  // layers by design and is not what makes two glyphs the same.
  const keyOf = (/** @type {Element} */ el) => {
    const bare = /** @type {Element} */ (el.cloneNode(true));
    bare.removeAttribute("style");
    const r = el.getBoundingClientRect();
    const h = (/** @type {number} */ v) => Math.round(v * 2);
    return `${bare.outerHTML}@${h(r.left)},${h(r.top)},${h(r.width)},${h(r.height)}`;
  };
  const seen = (/** @type {Element} */ el) => {
    let value = 1;
    for (let e = /** @type {Element | null} */ (el); e && e !== facts; e = e.parentElement) {
      value *= Number(getComputedStyle(e).opacity);
    }
    return value;
  };
  const count = Math.max(layers[0].children.length, layers[1].children.length);
  const slots = [];
  for (let i = 0; i < count; i++) {
    const a = layers[0].children[i];
    const b = layers[1].children[i];
    const parts = [partsOf(a), partsOf(b)];
    slots.push({
      name: (a || b).className,
      same: a !== undefined && b !== undefined && a.innerHTML === b.innerHTML,
      keys: parts.map((side) => side.map(keyOf)),
      samples: /** @type {number[][][]} */ ([]),
      parts,
    });
  }
  for (let k = 0; k <= 40; k++) {
    api.seek((total * k) / 40);
    for (const slot of slots) {
      slot.samples.push(slot.parts.map((side) => side.map(seen)));
    }
  }
  return slots.map(({ name, same, keys, samples }) => ({ name, same, keys, samples }));
};
