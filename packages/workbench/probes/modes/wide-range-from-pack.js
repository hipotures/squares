// A range wider than one step, set from Pack, names Animate. o.lo and o.hi are the range.
/** @param {{lo: number, hi: number}} o */ (o) => {
  const api = window.atlasTransitions;
  api.setMode("pack");
  api.setRange(o.lo, o.hi);
  return { mode: api.mode(), range: api.range() };
};
