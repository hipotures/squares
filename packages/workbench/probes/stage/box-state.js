// The stage's box and trace and the gap bar's pointer as drawn now: the trace's and the box's
// sides, the trace's opacity, the box's stroke and whether it is the page's green or the frames'
// grey, whether the pointer is locked, the pointer's and the record rule's x on the bar, and
// whether the box is drawn over its trace.
//
// The box's colour is the stylesheet's, switched by `is-locked` (`--scene-frame-*`), so the
// stroke is read off the computed style rather than an attribute, and the tokens it is compared
// with are converted to the `rgb(...)` a computed stroke is reported in.
() => {
  /** @param {string} id */
  const element = (id) => {
    const found = document.querySelector(`#${id}`);
    if (found == null) {
      throw new Error(`probe requires #${id}`);
    }
    return found;
  };
  /** @param {string} value a `#rrggbb` token */
  const rgb = (value) => {
    const packed = Number.parseInt(value.slice(1), 16);
    return `rgb(${(packed >> 16) & 255}, ${(packed >> 8) & 255}, ${packed & 255})`;
  };
  const trace = element("bound-trace");
  const box = element("bound-box");
  const pointer = /** @type {SVGGraphicsElement} */ (element("gapbar-box"));
  const root = getComputedStyle(document.documentElement);
  const met = root.getPropertyValue("--scene-best").trim();
  const grey = root.getPropertyValue("--scene-frame").trim();
  const stroke = getComputedStyle(box).stroke;
  const matrix = pointer.transform.baseVal.consolidate()?.matrix ?? null;
  return {
    trace: Number(trace.getAttribute("width")),
    box: Number(box.getAttribute("width")),
    traceOpacity: Number(trace.getAttribute("opacity")),
    boxStroke: stroke,
    green: stroke === rgb(met),
    grey: stroke === rgb(grey),
    pointerLocked: pointer.classList.contains("is-locked"),
    pointerX: matrix === null ? null : matrix.e,
    recordX: Number(element("gapbar-record-rule").getAttribute("x1")),
    boxOverTrace: trace.nextElementSibling === box,
  };
};
