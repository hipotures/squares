// Whether play carries on from one step into the next, in real time: the range o.from..o.to is
// played from its start for o.seconds of frames, and the probe reports every n the stage showed,
// whether it is still playing, and any error a frame threw. A seek draws one instant and cannot
// see play stop between steps, which is how a regression that halted playback after the first
// step (the owner, 2026-09-21) passed every check. Pauses and puts the range back.
/** @param {{from: number, to: number, seconds: number}} o */
async (o) => {
  const api = window.atlasTransitions;
  const chosen = api.range();
  /** @type {Set<number>} */
  const seen = new Set();
  /** @type {string[]} */
  const errors = [];
  /** @param {ErrorEvent} event */
  const record = (event) => {
    errors.push(String(event.message));
  };
  window.addEventListener("error", record);
  try {
    api.pause();
    api.setRange(o.from, o.to);
    api.playRange();
    const started = performance.now();
    while (performance.now() - started < o.seconds * 1000) {
      await new Promise((resolve) => window.requestAnimationFrame(resolve));
      const n = api.state().n;
      if (n !== null) {
        seen.add(n);
      }
    }
    return {
      playing: api.state().playing,
      seen: [...seen].sort((a, b) => a - b),
      errors,
    };
  } finally {
    window.removeEventListener("error", record);
    api.pause();
    api.setRange(chosen.from, chosen.to);
  }
};
