// The n the last pair steps from.
() => {
  const last = window.atlasTransitions.pairs().at(-1);
  if (last === undefined) {
    throw new Error("probe requires at least one pair");
  }
  return last.n;
};
