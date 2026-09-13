// One combination of pair, style, run mode, annealing level and instant.
// Takes {index, style, mode, level, at}; mode is 'snap', 'free' or 'blind'.
/** @param {{index: number, style: Parameters<import("../../src/api/workbench-api.js").AtlasTransitions["physics"]>[1], mode: string, level: number, at: number}} o */ (
  o,
) => {
  const A = window.atlasTransitions;
  A.select(o.index);
  A.setStyle(o.style);
  A.setSnap(o.mode !== "free");
  A.setBlind(o.mode === "blind");
  A.setAnneal(o.level);
  A.seek(o.at);
};
