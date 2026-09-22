// One step, sampled at every frame of a declared rate: what the stage draws for each visible
// square (identity, fill, opacity), the view's size, and the bound box's side. Everything the
// transition contract checks is read here in one page turn, so a step costs one evaluate
// rather than one per frame.
//
// Squares are read the way `stage/drawn` reads them -- `#squares g[data-identity]`, skipping
// the hidden -- because the square pool keeps squares from earlier steps in the DOM, and a read
// of every `rect` counts squares that are not on the stage.
//
// o.n is the n the step goes INTO, o.fps the sampling rate, o.style and o.anneal the solver,
// and o.hold whether axis-aligned squares hold their colors.
/**
 * @param {{
 *   n: number,
 *   fps: number,
 *   style: import("../../src/api/workbench-api.js").AtlasStyle,
 *   anneal: number,
 *   hold: boolean,
 * }} o
 */
(o) => {
  const api = window.atlasTransitions;
  api.setMode("animate");
  api.pause();
  api.setStyle(o.style);
  api.setAnneal(o.anneal);
  api.setHoldSquareColors(o.hold);
  api.setStepN(o.n);
  api.pause();
  const svg = /** @type {Element} */ (document.getElementById("packing-svg"));
  const box = /** @type {Element} */ (document.getElementById("bound-box"));
  const duration = api.duration();
  const count = Math.max(1, Math.round(duration * o.fps));
  const frames = [];
  for (let k = 0; k <= count; k += 1) {
    const t = Math.min(duration, k / o.fps);
    api.seek(t);
    const view = Number((svg.getAttribute("viewBox") ?? "0 0 0 0").split(/\s+/)[2]);
    const squares = Array.from(
      /** @type {NodeListOf<SVGGElement>} */ (
        document.querySelectorAll("#squares g[data-identity]")
      ),
    )
      .filter((g) => g.style.display !== "none")
      .map((g) => {
        const rect = g.firstElementChild;
        // An unset inline style reads as "", not null, and Number("") is 0: chained with `??`
        // it reported every square transparent, and the hue rules, which skip anything not
        // fully opaque, checked nothing. An absent opacity is 1.
        const written = g.getAttribute("opacity") || g.style.opacity || "1";
        const opacity = Number(written);
        return [
          Number(g.dataset.identity),
          rect == null ? "" : (rect.getAttribute("fill") ?? ""),
          Number.isFinite(opacity) ? opacity : 1,
        ];
      });
    frames.push({
      t,
      view,
      box: Number(box.getAttribute("width")),
      boxInk: Number(box.getAttribute("stroke-opacity") ?? "1"),
      squares,
    });
  }
  const schedule = api.schedule();
  return {
    n: o.n,
    duration,
    moveStart: schedule.moveStart,
    schedule,
    fade: api.colorFade(),
    frames,
  };
};
