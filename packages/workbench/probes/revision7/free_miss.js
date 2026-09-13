// What a free run of one pair under one style misses the record by. Takes {index, style}.
/** @param {{index: number, style: Parameters<import("../../src/api/workbench-api.js").AtlasTransitions["physics"]>[1]}} o */ (
  o,
) => window.atlasTransitions.physics(o.index, o.style, "free").miss;
