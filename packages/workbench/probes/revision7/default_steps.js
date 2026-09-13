// How many steps the same run takes at the default level. Takes {index, mode}.
/** @param {{index: number, mode: import("../../src/api/workbench-api.js").AtlasSimMode}} o */ (
  o,
) => {
  const A = window.atlasTransitions;
  A.setAnneal(3);
  return A.physics(o.index, "physics", o.mode).steps;
};
