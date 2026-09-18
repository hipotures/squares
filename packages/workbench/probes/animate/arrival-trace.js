// How one step introduces its new square, read off the drawn stage: the step is configured from
// o (its n, style, phase, and whether the continuous beat and the simple-transition speed-up are
// on), then sought to every instant in o.times, given as fractions of the step, and to the
// schedule's own instants. Each sample is [seconds, the new square's opacity, its drawn scale, the
// container's side, the stage's view size, the box's side]. A view that grows is the picture
// shrinking on screen. Seeking is the page's own, so the samples are what a scrub would show.
/** @param {{n: number, style: "tween" | "physics" | "bodies", phase: import("../../src/api/workbench-api.js").AtlasPhase, continuous: boolean, fastSimple: boolean, times: number[]}} o */
(o) => {
  const api = window.atlasTransitions;
  api.setMode("animate");
  api.stopAll();
  api.setStepN(o.n);
  api.setStyle(o.style);
  api.setPhase(o.phase);
  api.setContinuous({ fastSimple: o.fastSimple });
  if (o.continuous) {
    // The continuous beat is the one a run plays, so start the run on this step and hold it.
    api.playAll();
    api.pause();
  }
  const schedule = api.schedule();
  const duration = api.duration();
  const newSquare = api.newSquare();
  const pair = api.pairs().find((candidate) => candidate.n + 1 === o.n);
  /** @param {string} id */
  const element = (id) => {
    const found = document.getElementById(id);
    if (found == null) {
      throw new Error(`probe requires #${id}`);
    }
    return found;
  };
  const stage = element("packing-svg");
  const container = element("container");
  const box = element("bound-box");
  const instants = [
    ...o.times.map((fraction) => fraction * duration),
    ...Object.entries(schedule)
      .filter(([key]) => key !== "roll")
      .map(([, value]) => value),
  ].sort((a, b) => a - b);
  const samples = instants.map((t) => {
    api.seek(t);
    const square = document.querySelector(`#squares g[data-identity="${newSquare.identity}"]`);
    if (square == null) {
      throw new Error(`probe requires the new square, identity ${newSquare.identity}`);
    }
    const scale = /scale\(([^)\s]+)/.exec(square.getAttribute("transform") ?? "");
    const view = (stage.getAttribute("viewBox") ?? "").split(/\s+/).map(Number);
    return [
      t,
      Number(square.getAttribute("opacity") ?? "1"),
      scale === null ? 1 : Number(scale[1]),
      Number(container.getAttribute("width")),
      view[2] ?? Number.NaN,
      Number(box.getAttribute("width")),
    ];
  });
  return {
    kind: pair?.kind ?? null,
    identity: newSquare.identity,
    continuous: api.continuous(),
    schedule,
    duration,
    samples,
  };
};
