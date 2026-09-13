// The retained record's side at one size, with the open-ended run's state settled first.
// o.n is the size.
/** @param {{n: number}} o */
(o) => {
  window.atlasTransitions.optimizeState();
  const data = document.getElementById("atlas-data")?.textContent;
  if (data == null) {
    throw new Error("probe requires #atlas-data text");
  }
  return Number(JSON.parse(data).facts[String(o.n)].side);
};
