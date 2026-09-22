// Which steps play sped up, observed rather than asked for: every pair's duration with the
// simple-transition speed-up off and then on, and whether it shrinks by the page's own declared
// factor. The factor is read, not assumed: the census once hard-coded "halves", and when the
// speed-up went to 3x it reported no step sped up at all. Puts the setting back.
() => {
  const api = window.atlasTransitions;
  const { fastSimple: found, simpleSpeed } = api.continuous();
  const pairs = api.pairs();
  api.setContinuous({ fastSimple: false });
  const full = pairs.map((_, index) => api.duration(index));
  api.setContinuous({ fastSimple: true });
  const rows = pairs.map((pair, index) => {
    const long = full[index] ?? Number.NaN;
    return {
      n: pair.n,
      kind: pair.kind,
      sped: long > 0 && Math.abs(simpleSpeed * api.duration(index) - long) < 1e-9,
    };
  });
  api.setContinuous({ fastSimple: found });
  return rows;
};
