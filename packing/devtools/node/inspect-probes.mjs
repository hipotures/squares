// What each probe file evaluates to, for `devtools.check_probes`.
//
//   node inspect-probes.mjs <probe.js>...
//
// Prints one JSON object mapping each path to `{ "type": <typeof value> }`, or to
// `{ "error": <message> }` when the file does not evaluate. A probe is one expression, so it
// is wrapped in parentheses first: `(o) => o` alone on a line is a syntax error as a
// statement. The trailing semicolon the formatter writes is trimmed, because a statement
// terminator inside the parentheses is a syntax error too, and the closing parenthesis goes
// on its own line so a trailing line comment cannot swallow it.
//
// Each file is evaluated in a fresh, empty context. Evaluating an arrow function does not
// run its body, so nothing a probe does to a page happens here; a probe that is really an
// immediately-invoked function runs, fails on the missing page, and is reported as an error.
// Such a probe can also loop: the evaluation is given a deadline, because a probe whose top
// level is `(() => { while (true) {} })()` otherwise hangs this process, and the CI step
// running it, with no diagnostic at all. The realm is empty, so the blast radius is CPU.
//
// `class` is reported as its own type rather than as a function. `typeof` calls a class a
// function, and a class handed to `page.evaluate` fails in the page with "Class constructor
// cannot be invoked without 'new'": a type tag is not callability. A class is the callable
// whose `prototype` is not writable; an arrow has no `prototype` at all.
import { readFileSync } from "node:fs";
import { createContext, Script } from "node:vm";

/** How long one probe may take to evaluate. Overridable so the contract test that proves
 * the deadline fires does not have to pay the default to do it. */
const TIMEOUT_MS = Number(process.env.PROBE_TIMEOUT_MS ?? 5000);

/**
 * @param {unknown} value
 * @returns {string} `typeof value`, except that a class constructor is `"class"`.
 */
function describe(value) {
  const type = typeof value;
  if (type !== "function") {
    return type;
  }
  const prototype = Object.getOwnPropertyDescriptor(value, "prototype");
  return prototype !== undefined && prototype.writable === false ? "class" : "function";
}

/** @type {Record<string, { type: string } | { error: string }>} */
const verdicts = {};
for (const path of process.argv.slice(2)) {
  const source = readFileSync(path, "utf8").trimEnd().replace(/;$/, "");
  try {
    const value = new Script(`(${source}\n)`, { filename: path }).runInContext(createContext({}), {
      timeout: TIMEOUT_MS,
    });
    verdicts[path] = { type: describe(value) };
  } catch (error) {
    verdicts[path] = { error: error instanceof Error ? error.message : String(error) };
  }
}
process.stdout.write(JSON.stringify(verdicts));
