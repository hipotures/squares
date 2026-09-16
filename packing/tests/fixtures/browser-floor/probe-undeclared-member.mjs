import { probe } from "./probe.mjs";

const value = /** @type {() => { declared: number }} */ (
  probe("devtools/probes/math/library.js")
)();
value.undeclared;
