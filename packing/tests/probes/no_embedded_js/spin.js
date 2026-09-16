// A probe whose body never returns, for the contract test that proves the probe inspector
// gives each evaluation a deadline. Evaluating this file yields the function without running
// it, so `devtools.check_probes` reads it as the function it is; the test writes `applied()`
// of it into a temporary tree, where the inspector does run it and has to give up.
//
// The condition is true but not constantly so, and the counter is returned, because Biome
// holds this file to the same floor as every other probe.
() => {
  const started = Date.now();
  let spins = 0;
  while (Date.now() >= started) {
    spins += 1;
  }
  return spins;
};
