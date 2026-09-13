// The law's force at each penetration, which is the gap read the other way round.
// o.penetrations is the list of depths.
/** @param {{penetrations: number[]}} o */ (o) =>
  o.penetrations.map(/** @param {number} p */ (p) => window.atlasTransitions.lawForce(-p));
