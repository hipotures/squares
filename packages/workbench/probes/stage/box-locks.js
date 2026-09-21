// Whether the stage's box and its gap-bar pointer read "locked" through whole steps, beside
// what the stage shows there. Each pair is sampled half way through its dwell, at fractions of
// its move, and at its end. A sample reports the box's side, whether the box is stroked in the
// page's green, whether the pointer is locked, the n the gap bar describes and its best known
// side. Takes {indices, style, fractions}: indices null for every pair, fractions of the move.
/** @param {{indices: number[] | null, style: import("../../src/api/workbench-api.js").AtlasStyle, fractions: number[]}} o */
(o) => {
  const api = window.atlasTransitions;
  const box = /** @type {Element} */ (document.getElementById("bound-box"));
  const pointer = /** @type {Element} */ (document.getElementById("gapbar-box"));
  const met = getComputedStyle(document.documentElement).getPropertyValue("--scene-best").trim();
  // The box's colour is the stylesheet's, switched by `is-locked`, so it is read off the
  // computed style and the token is converted to the `rgb(...)` that is reported in.
  /** @param {string} value a `#rrggbb` token */
  const rgb = (value) => {
    const packed = Number.parseInt(value.slice(1), 16);
    return `rgb(${(packed >> 16) & 255}, ${(packed >> 8) & 255}, ${packed & 255})`;
  };
  const green = rgb(met);
  api.pause();
  api.setStyle(o.style);
  const pairs = api.pairs();
  const indices = o.indices ?? pairs.map((_, index) => index);
  const rows = [];
  for (const index of indices) {
    api.select(index);
    const sc = api.schedule();
    /** @type {[string, number][]} */
    const instants = [
      ["dwell", sc.moveStart / 2],
      ...o.fractions.map(
        (f) =>
          /** @type {[string, number]} */ ([
            "move",
            sc.moveStart + f * (sc.moveEnd - sc.moveStart),
          ]),
      ),
      ["end", sc.end],
    ];
    for (const [phase, t] of instants) {
      api.seek(t);
      const bar = api.gapBar();
      rows.push({
        index,
        n: pairs[index]?.n,
        phase,
        t,
        side: Number(box.getAttribute("width")),
        green: getComputedStyle(box).stroke === green,
        pointer: pointer.classList.contains("is-locked"),
        shownN: bar.n,
        record: bar.record,
      });
    }
  }
  return rows;
};
