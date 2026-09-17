import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { test } from "node:test";
import {
  ALLOWED_WITHOUT_TOKENS,
  checkContrast,
  contrastRatio,
  type InlineStyleFinding,
  inlineStyleFindings,
  matchInlineAllow,
  NAMED_COLOURS,
  parseColour,
  parseStylesheet,
  rawPieces,
  rawValueFindings,
  resolveToken,
  tokenBlock,
} from "../tools/design-contract.ts";

/**
 * Unit tests of the design contract's machinery, not of the page: the test that applies it to
 * `assets/workbench.css` and the sources lives beside the stylesheet's owner. A contract check that
 * finds nothing proves nothing on its own, so every rule here has a negative control (a fixture that
 * smuggles the thing past it) as well as a positive one.
 *
 * The positive control `clean.css` is a real `.css` file under Biome. Every fixture that breaks the
 * floor on purpose ends in `.txt` so that neither Biome nor `tsc` compiles it, and is only ever read
 * as text: the raw-value stylesheet carries an `!important` that Biome's `noImportantStyles` refuses,
 * and the repository admits no suppression outside its declared accessibility exceptions; the script
 * and markup fixtures hold deliberate inline style writes.
 */
const FIXTURES = join(import.meta.dirname, "fixtures", "design");

function fixture(name: string): string {
  return readFileSync(join(FIXTURES, name), "utf8");
}

/**
 * The one-based line of `needle`, searched for after `after` when given. This is found by plain
 * string search, independently of the reader under test, so it checks the reader's line numbers.
 */
function lineOf(text: string, needle: string, after = ""): number {
  const from = text.indexOf(after);
  const index = text.indexOf(needle, Math.max(0, from));
  assert(from >= 0 && index >= 0, `fixture lacks ${after} ... ${needle}`);
  return text.slice(0, index).split("\n").length;
}

test("the reader keeps selectors, at-rules, lines and !important through comments and strings", () => {
  const css = [
    "/* a comment with ; and } in it,",
    "   over two lines */",
    '@import url("x;y.css");',
    "html,",
    "body { margin: 0; }",
    "@font-face {",
    '  font-family: "Odd; Name}";',
    "  src: url(data:font/woff2;base64,AAAA);",
    "}",
    "@media (min-width: 1px) {",
    "  @supports (display: grid) {",
    "    .a > .b { color: red !important }",
    "  }",
    "}",
    ".card {",
    "  &:hover { padding: 1px; }",
    "  .x, .y { gap: 2px; }",
    "}",
  ].join("\n");
  assert.deepEqual(parseStylesheet(css), [
    {
      selector: "html, body",
      property: "margin",
      value: "0",
      important: false,
      line: 5,
      atRule: null,
    },
    {
      selector: "@font-face",
      property: "font-family",
      value: '"Odd; Name}"',
      important: false,
      line: 7,
      atRule: "@font-face",
    },
    {
      selector: "@font-face",
      property: "src",
      value: "url(data:font/woff2;base64,AAAA)",
      important: false,
      line: 8,
      atRule: "@font-face",
    },
    {
      selector: ".a > .b",
      property: "color",
      value: "red",
      important: true,
      line: 12,
      atRule: "@media (min-width: 1px) @supports (display: grid)",
    },
    {
      selector: ".card:hover",
      property: "padding",
      value: "1px",
      important: false,
      line: 16,
      atRule: null,
    },
    {
      selector: ".card .x, .card .y",
      property: "gap",
      value: "2px",
      important: false,
      line: 17,
      atRule: null,
    },
  ]);
});

test("the token block is the first top-level :root rule, and only its custom properties", () => {
  const css = fixture("raw-values.css.txt");
  const block = tokenBlock(css);
  assert(block !== null);
  assert.equal(block.startLine, lineOf(css, ":root {"));
  assert.equal(block.endLine, lineOf(css, "}", ":root {"));
  assert.equal(block.tokens.size, 9);
  assert.equal(block.tokens.get("--accent"), "oklch(54.14% 0.1337 246.71)");
  assert.equal(
    tokenBlock(fixture("clean.css"))?.tokens.get("--serif"),
    '"Semi; Colon {Serif}", "PT Serif", serif',
  );

  const nested = "@media print { :root { --a: 1px; } }\n:root { --b: 2px; color: var(--b); }";
  assert.deepEqual([...(tokenBlock(nested)?.tokens ?? [])], [["--b", "2px"]]);
  assert.equal(tokenBlock(".a { --b: 2px; }"), null);
});

test("each kind of smuggled raw value is found where it is, and nothing in the token block", () => {
  const css = fixture("raw-values.css.txt");
  const expected: [string, string, string, string[], string | null][] = [
    [".hex", "color", "colour", ["#fff"], null],
    [".rgb", "background-color", "colour", ["rgb(0 0 0 / 50%)"], null],
    [".oklch", "border-color", "colour", ["oklch(70% 0.1 200)"], null],
    [".named", "outline-color", "colour", ["red"], null],
    [".padding", "padding", "spacing", ["12px"], null],
    [".margin", "margin", "spacing", ["0.5em"], null],
    [".leading", "line-height", "typography", ["1.2"], null],
    [".weight", "font-weight", "typography", ["600"], null],
    [".layer", "z-index", "elevation", ["3"], null],
    [".shadow", "box-shadow", "elevation", ["2px", "4px"], null],
    [".motion", "transition", "motion", ["150ms"], null],
    [".calc", "margin-inline", "spacing", ["4px"], null],
    [".scoped", "--gutter", "custom-property", ["4px"], null],
    [".narrow", "gap", "spacing", ["6px"], "@media (max-width: 600px)"],
    [".important", "letter-spacing", "typography", ["0.02em"], null],
  ];
  const { findings, unusedAllow } = rawValueFindings(css, []);
  assert.deepEqual(
    findings.map((finding) => [
      finding.selector,
      finding.property,
      finding.category,
      finding.raw,
      finding.atRule,
      finding.line,
    ]),
    expected.map((row) => [...row, lineOf(css, `${row[1]}:`, `${row[0]} {`)]),
  );
  assert.deepEqual(unusedAllow, []);
  assert.equal(findings.find((finding) => finding.selector === ".important")?.important, true);

  const block = tokenBlock(css);
  assert(block !== null);
  const inBlock = findings.filter(
    (finding) => finding.line >= block.startLine && finding.line <= block.endLine,
  );
  assert.deepEqual(inBlock, []);
});

test("a stylesheet of tokens, var(), zero and keywords has no raw value", () => {
  assert.deepEqual(rawValueFindings(fixture("clean.css"), []).findings, []);
});

test("calc, custom properties, font families and descriptors follow the policy's edges", () => {
  const cases: [string, string, string[]][] = [
    ["margin", "calc(var(--a) * -1)", []],
    ["margin", "calc(2 * var(--a))", []],
    ["margin", "calc((var(--a) + var(--b)) / 2)", []],
    ["margin", "calc(var(--a, 4px) * 2)", []],
    ["line-height", "calc(1.5 * 2)", ["1.5", "2"]],
    ["margin", "calc(var(--a) * 2px)", ["2px"]],
    ["margin", "calc(100% - var(--a))", ["100%"]],
    ["gap", "min(var(--a), 10vw)", ["10vw"]],
    ["padding", "0px -0 0%", []],
    ["transition", "transform var(--t) cubic-bezier(0.2, 0, 0, 1)", ["0.2", "1"]],
    [
      "color",
      "color-mix(in oklch, var(--a), var(--b))",
      ["color-mix(in oklch, var(--a), var(--b))"],
    ],
    ["color", "CurrentColor", []],
    ["border", "var(--w) solid Tomato", ["Tomato"]],
    ["border-width", "thin", ["thin"]],
    ["font-weight", "bold", ["bold"]],
    ["font-family", "Georgia, serif", ["Georgia", "serif"]],
    ["font-family", "inherit", []],
    ["font", "italic var(--size) var(--sans)", []],
    ["--x", "var(--a)", []],
    ["--x", "none", []],
    ["--x", "calc(var(--a) * 2)", []],
    ["--x", '"PT Serif"', ['"PT Serif"']],
    ["--x", "linear-gradient(to right, var(--a), var(--b))", []],
  ];
  for (const [property, value, raw] of cases) {
    assert.deepEqual(rawPieces(property, value), raw, `${property}: ${value}`);
  }
  assert.ok(ALLOWED_WITHOUT_TOKENS.includes("0"));

  const css = [
    ".a { width: 12px; top: 3px; height: 1em; opacity: 0.5; }",
    '@font-face { font-family: "PT Serif"; font-weight: 400 700; }',
    "@property --x { syntax: '<length>'; inherits: false; initial-value: 4px; }",
    ":root { --a: 1px; color: #000; }",
  ].join("\n");
  assert.deepEqual(
    rawValueFindings(css, []).findings.map((finding) => [finding.selector, finding.property]),
    [[":root", "color"]],
    "only a non-custom declaration in the token block is governed there",
  );
});

test("an allow entry suppresses exactly its finding, needs a reason, and is reported unused", () => {
  const css = fixture("raw-values.css.txt");
  const all = rawValueFindings(css, []).findings;
  const hex = { selector: ".hex", property: "color", value: "#fff", reason: "the print sheet" };
  const spaced = {
    selector: "  .margin ",
    property: "MARGIN",
    value: " 0.5em    0 ",
    reason: "whitespace and case do not matter",
  };
  const important = {
    selector: ".important",
    property: "letter-spacing",
    value: "0.02em !important",
    reason: "!important on the entry is ignored",
  };
  const allowed = rawValueFindings(css, [hex, spaced, important]);
  assert.deepEqual(
    allowed.findings,
    all.filter((finding) => ![".hex", ".margin", ".important"].includes(finding.selector)),
  );
  assert.deepEqual(allowed.unusedAllow, []);

  assert.throws(
    () => rawValueFindings(css, [{ ...hex, reason: "  " }]),
    /\.hex \{ color: #fff \} must give a reason/,
  );

  const stale = { selector: ".hex", property: "color", value: "#000", reason: "no longer written" };
  const result = rawValueFindings(css, [hex, stale]);
  assert.deepEqual(result.unusedAllow, [stale]);
  assert.equal(result.findings.length, all.length - 1);
});

test("inline style writes are found in every form, and reads, data and comments are not", () => {
  const script = fixture("inline-styles.ts.txt");
  const markup = fixture("inline-styles.html.txt");
  const findings = inlineStyleFindings([
    { path: "inline-styles.ts.txt", text: script },
    { path: "inline-styles.html.txt", text: markup },
  ]);
  const site = (path: string, text: string, needle: string, property: string) => ({
    path,
    line: lineOf(text, needle),
    property,
  });
  const html = (needle: string, property: string) =>
    site("inline-styles.html.txt", markup, needle, property);
  const ts = (needle: string, property: string) =>
    site("inline-styles.ts.txt", script, needle, property);
  assert.deepEqual(
    findings.map(({ path, line, property }) => ({ path, line, property })),
    [
      html('<div id="a" style=', "style"),
      html("STYLE='stroke: red'", "style"),
      html('body.style.opacity = "0"', "opacity"),
      ts('stage.style.display = "none"', "display"),
      ts("stage.style.left +=", "left"),
      ts("stage.style.backgroundColor", "background-color"),
      ts('stage.style["opacity"]', "opacity"),
      ts("stage.style['z-index']", "z-index"),
      ts("stage.style.setProperty(", "--stage-scale"),
      ts("stage.style.removeProperty(", "transform"),
      ts("stage.style.cssText", "cssText"),
      ts('stage.setAttribute("style"', "style"),
      ts("stage.setAttribute('style'", "style"),
      ts("Object.assign(stage.style", "style"),
      ts("stage.innerHTML =", "style"),
      ts("stage.style.width", "width"),
      ts("stage.style.height", "height"),
      ts('stage.style.display = "";', "display"),
    ],
  );
  const first = findings.find((finding) => finding.property === "cssText");
  assert.equal(first?.code, 'stage.style.cssText = "top: 0";');
});

test("an inline allowance allows exactly its count, and a lower count makes it stale", () => {
  const finding = (path: string, line: number, property: string): InlineStyleFinding => ({
    path,
    line,
    property,
    code: `${property} ${line}`,
  });
  const findings = [
    finding("a.ts", 1, "display"),
    finding("a.ts", 2, "display"),
    finding("a.ts", 3, "left"),
    finding("b.ts", 4, "display"),
  ];
  const entry = (path: string, property: string, count: number) => ({
    path,
    property,
    count,
    reason: "shown and hidden by the panel",
  });

  assert.deepEqual(
    matchInlineAllow(findings, [
      entry("a.ts", "display", 2),
      entry("a.ts", "left", 1),
      entry("b.ts", "display", 1),
    ]),
    { unallowed: [], stale: [] },
  );
  assert.deepEqual(
    matchInlineAllow(findings, [entry("a.ts", "display", 1), entry("b.ts", "display", 1)]),
    { unallowed: [findings[0], findings[1], findings[2]], stale: [] },
    "one write over the count reports every site of that property, and an unlisted one is unallowed",
  );
  assert.deepEqual(
    matchInlineAllow(findings, [
      entry("a.ts", "display", 3),
      entry("a.ts", "left", 1),
      entry("b.ts", "display", 1),
      entry("c.ts", "opacity", 1),
    ]),
    {
      unallowed: [],
      stale: [
        "a.ts: display allows 3, found 2; lower the count",
        "c.ts: opacity allows 1, found 0; lower the count",
      ],
    },
  );
  assert.throws(
    () => matchInlineAllow(findings, [{ ...entry("a.ts", "left", 1), reason: "" }]),
    /must give a reason/,
  );
  assert.throws(() => matchInlineAllow(findings, [entry("a.ts", "left", 0)]), /positive whole/);
  assert.throws(
    () => matchInlineAllow(findings, [entry("a.ts", "left", 1), entry("a.ts", "left", 1)]),
    /listed twice/,
  );
});

test("colours parse from hex, rgb(), oklch() and names", () => {
  assert.deepEqual(parseColour("#fff"), { r: 1, g: 1, b: 1, a: 1 });
  assert.deepEqual(parseColour("#00000080"), { r: 0, g: 0, b: 0, a: 128 / 255 });
  assert.deepEqual(parseColour("rgba(255, 0, 0, 0.5)"), { r: 1, g: 0, b: 0, a: 0.5 });
  assert.deepEqual(parseColour("rgb(0 100% 0 / 25%)"), { r: 0, g: 1, b: 0, a: 0.25 });
  assert.deepEqual(parseColour("transparent"), { r: 0, g: 0, b: 0, a: 0 });
  assert.deepEqual(parseColour("White"), { r: 1, g: 1, b: 1, a: 1 });
  assert.equal(NAMED_COLOURS.size, 148);
  // CSS Color 4 gives sRGB red as oklch(62.796% 0.25768 29.2339) and blue as
  // oklch(45.201% 0.31321 264.05).
  for (const [oklch, srgb] of [
    ["oklch(62.796% 0.25768 29.2339)", "#ff0000"],
    ["oklch(0.45201 0.31321 264.05deg / 1)", "#0000ff"],
  ] as const) {
    const converted = parseColour(oklch);
    const expected = parseColour(srgb);
    for (const channel of ["r", "g", "b", "a"] as const) {
      assert(Math.abs(converted[channel] - expected[channel]) < 0.01, `${oklch} ${channel}`);
    }
    assert(Math.abs(contrastRatio(oklch, "#fff") - contrastRatio(srgb, "#fff")) < 0.01);
  }
  assert.throws(() => parseColour("hsl(0 100% 50%)"), /unsupported colour/);
});

test("contrast ratios match WCAG, composite translucency, and resolve token chains", () => {
  assert.equal(contrastRatio("#000", "#fff"), 21);
  assert.equal(Math.round(contrastRatio("#767676", "#fff") * 100) / 100, 4.54);
  assert(
    Math.abs(
      contrastRatio("rgb(0 0 0 / 50%)", "#fff") - contrastRatio("rgb(127.5 127.5 127.5)", "#fff"),
    ) < 1e-9,
    "a translucent foreground is composited over its background",
  );
  assert(
    Math.abs(
      contrastRatio("#000", "rgb(0 0 0 / 50%)") - contrastRatio("#000", "rgb(127.5 127.5 127.5)"),
    ) < 1e-9,
    "a translucent background is composited over white",
  );

  const tokens = new Map([
    ["--ink", "var(--text)"],
    ["--text", "var(--missing, var(--grey))"],
    ["--grey", "#767676"],
    ["--paper", "#fff"],
    ["--quiet", "#999"],
    ["--loop-a", "var(--loop-b)"],
    ["--loop-b", "var(--loop-a)"],
  ]);
  assert.equal(resolveToken("--ink", tokens), "#767676");
  assert.throws(
    () => resolveToken("--loop-a", tokens),
    /token cycle: --loop-a -> --loop-b -> --loop-a/,
  );
  assert.throws(() => resolveToken("--absent", tokens), /unresolved token --absent/);

  assert.deepEqual(
    checkContrast(tokens, [
      { fg: "--ink", bg: "--paper", min: 4.5, role: "body text" },
      { fg: "--quiet", bg: "var(--paper)", min: 4.5, role: "quiet label" },
      { fg: "#000", bg: "--paper", min: 21, role: "black on white" },
    ]),
    [{ fg: "--quiet", bg: "var(--paper)", min: 4.5, role: "quiet label", ratio: 2.84 }],
  );
});
