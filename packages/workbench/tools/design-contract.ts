/**
 * Static machinery for the workbench's design contract.
 *
 * The page's stylesheet keeps every design value (colour, spacing, type, shape, elevation and
 * motion) in one token block, the first top-level `:root` rule, and everything else refers to those
 * tokens. A value written anywhere else is a second source of truth that drifts from the first, so
 * these functions give a test what it needs to hold the rule: a small CSS reader, the raw-value
 * policy over its declarations, a scan for inline style writes in scripts and markup (which bypass
 * the stylesheet altogether), and the WCAG arithmetic for checking token pairs for contrast.
 *
 * Everything here is pure. Callers read the files and pass the text in; nothing is read from disk.
 */

// ---------------------------------------------------------------------------------------------
// Reading CSS
// ---------------------------------------------------------------------------------------------

export interface Declaration {
  /**
   * The rule's selector list with its whitespace collapsed and its commas written `, `. A nested
   * rule's selector is resolved against its parent. A declaration directly inside an at-rule, such
   * as `@font-face`, takes that at-rule's prelude.
   */
  selector: string;
  /** Lower case, except a custom property, whose name is case-sensitive. */
  property: string;
  /** The value with its whitespace collapsed and without `!important`. */
  value: string;
  important: boolean;
  /** One-based line of the property name. */
  line: number;
  /** The preludes of the enclosing at-rules, outermost first, joined by a space; null outside any. */
  atRule: string | null;
}

export interface TokenBlock {
  /** Custom properties by name; a repeated name keeps its last value, as the cascade would. */
  tokens: Map<string, string>;
  /** First and last line of the rule, one-based and inclusive. */
  startLine: number;
  endLine: number;
}

interface Rule {
  kind: "style" | "at";
  /** The at-rule's name, lower case and without `@`; empty for a style rule. */
  name: string;
  selector: string;
  atRule: string | null;
  topLevel: boolean;
  startLine: number;
  endLine: number;
}

interface ParsedDeclaration {
  declaration: Declaration;
  rule: Rule;
}

interface ParsedStylesheet {
  rules: Rule[];
  declarations: ParsedDeclaration[];
}

const IMPORTANT = /\s*!\s*important$/i;
const PROPERTY_NAME = /^(?:--[^\s:;]*|-?[A-Za-z_][\w-]*)$/;

/** Every declaration in the stylesheet, in source order. */
export function parseStylesheet(css: string): Declaration[] {
  return readStylesheet(css).declarations.map((parsed) => parsed.declaration);
}

/**
 * The custom properties of the first top-level `:root` rule, and where that rule sits, or null when
 * the stylesheet has none. A `:root` inside an at-rule is not the token block: tokens that change
 * with a media query are a second layer, which the raw-value policy reports.
 */
export function tokenBlock(css: string): TokenBlock | null {
  const parsed = readStylesheet(css);
  const rule = tokenRule(parsed);
  if (rule === undefined) {
    return null;
  }
  const tokens = new Map<string, string>();
  for (const { declaration, rule: owner } of parsed.declarations) {
    if (owner === rule && declaration.property.startsWith("--")) {
      tokens.set(declaration.property, declaration.value);
    }
  }
  return { tokens, startLine: rule.startLine, endLine: rule.endLine };
}

function tokenRule(parsed: ParsedStylesheet): Rule | undefined {
  return parsed.rules.find(
    (rule) => rule.kind === "style" && rule.topLevel && rule.selector === ":root",
  );
}

/** Replaces each comment with spaces, keeping its newlines, so every offset keeps its line. */
function blankCssComments(css: string): string {
  const out: string[] = [];
  let index = 0;
  while (index < css.length) {
    const char = css.charAt(index);
    if (char === '"' || char === "'") {
      const end = endOfQuoted(css, index);
      out.push(css.slice(index, end));
      index = end;
    } else if (char === "/" && css.charAt(index + 1) === "*") {
      const close = css.indexOf("*/", index + 2);
      const end = close < 0 ? css.length : close + 2;
      out.push(blankText(css.slice(index, end)));
      index = end;
    } else {
      out.push(char);
      index += 1;
    }
  }
  return out.join("");
}

/** The text with every character but a newline replaced by a space. */
function blankText(text: string): string {
  return text.replace(/[^\n]/g, " ");
}

/**
 * The offset just past the quoted string that starts at `start`. An escape skips the character
 * after it, and an unclosed string ends at its line's end, as it does in both CSS and JavaScript.
 */
function endOfQuoted(text: string, start: number): number {
  const quote = text.charAt(start);
  let index = start + 1;
  while (index < text.length) {
    const char = text.charAt(index);
    if (char === "\\") {
      index += 2;
    } else if (char === quote) {
      return index + 1;
    } else if (char === "\n") {
      return index;
    } else {
      index += 1;
    }
  }
  return text.length;
}

/** A function from an offset in `text` to its one-based line. */
function lineIndex(text: string): (offset: number) => number {
  const starts = [0];
  for (let index = 0; index < text.length; index += 1) {
    if (text.charCodeAt(index) === 10) {
      starts.push(index + 1);
    }
  }
  return (offset) => {
    let low = 0;
    let high = starts.length - 1;
    while (low < high) {
      const middle = (low + high + 1) >> 1;
      if ((starts[middle] ?? 0) <= offset) {
        low = middle;
      } else {
        high = middle - 1;
      }
    }
    return low + 1;
  };
}

function normaliseSpace(text: string): string {
  return text.replace(/\s+/g, " ").trim();
}

/** Splits at each top-level `separator`, outside strings, parentheses and brackets. */
function splitTopLevel(text: string, separator: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  let index = 0;
  while (index < text.length) {
    const char = text.charAt(index);
    if (char === '"' || char === "'") {
      index = endOfQuoted(text, index);
      continue;
    }
    if (char === "\\") {
      index += 2;
      continue;
    }
    if (char === "(" || char === "[") {
      depth += 1;
    } else if ((char === ")" || char === "]") && depth > 0) {
      depth -= 1;
    } else if (depth === 0 && char === separator) {
      parts.push(text.slice(start, index));
      start = index + 1;
    }
    index += 1;
  }
  parts.push(text.slice(start));
  return parts;
}

function normaliseSelector(selector: string): string {
  return splitTopLevel(selector, ",").map(normaliseSpace).join(", ");
}

/** A nested rule's selector: `&` stands for the parent, and a selector without one descends from it. */
function nestSelector(parent: string | null, child: string): string {
  const parts = splitTopLevel(child, ",").map(normaliseSpace);
  if (parent === null) {
    return parts.join(", ");
  }
  const outer = splitTopLevel(parent, ",").length > 1 ? `:is(${parent})` : parent;
  return parts
    .map((part) => (part.includes("&") ? part.replaceAll("&", outer) : `${outer} ${part}`))
    .join(", ");
}

/**
 * A reader for the stylesheets this repository writes: rules, at-rules nested to any depth,
 * declarations, and nesting. It is not a validating parser. Anything it cannot place (a stray `}`,
 * an at-rule statement such as `@import`) is skipped rather than reported.
 */
function readStylesheet(css: string): ParsedStylesheet {
  const text = blankCssComments(css);
  const lineOf = lineIndex(text);
  const rules: Rule[] = [];
  const declarations: ParsedDeclaration[] = [];
  let position = 0;

  function skipSpace(): void {
    while (position < text.length && /\s/.test(text.charAt(position))) {
      position += 1;
    }
  }

  /** The offset of the `;`, `{` or `}` that ends the item at `position`. */
  function itemEnd(): number {
    let depth = 0;
    let index = position;
    while (index < text.length) {
      const char = text.charAt(index);
      if (char === '"' || char === "'") {
        index = endOfQuoted(text, index);
        continue;
      }
      if (char === "\\") {
        index += 2;
        continue;
      }
      if (char === "(" || char === "[") {
        depth += 1;
      } else if ((char === ")" || char === "]") && depth > 0) {
        depth -= 1;
      } else if (depth === 0 && (char === ";" || char === "{" || char === "}")) {
        return index;
      }
      index += 1;
    }
    return text.length;
  }

  function addDeclaration(rule: Rule, item: string, start: number): void {
    const colon = item.indexOf(":");
    if (colon < 0) {
      return;
    }
    const name = item.slice(0, colon).trim();
    if (!PROPERTY_NAME.test(name)) {
      return;
    }
    const leading = item.length - item.trimStart().length;
    const written = normaliseSpace(item.slice(colon + 1));
    const important = IMPORTANT.test(written);
    const declaration: Declaration = {
      selector: rule.selector,
      property: name.startsWith("--") ? name : name.toLowerCase(),
      value: important ? written.replace(IMPORTANT, "") : written,
      important,
      line: lineOf(start + leading),
      atRule: rule.atRule,
    };
    declarations.push({ declaration, rule });
  }

  /** Reads items until the `}` that closes `owner`, or to the end at the top level. */
  function readBlock(
    owner: Rule | null,
    selector: string | null,
    atRules: readonly string[],
  ): void {
    for (;;) {
      skipSpace();
      if (position >= text.length) {
        return;
      }
      const char = text.charAt(position);
      if (char === "}") {
        position += 1;
        if (owner !== null) {
          return;
        }
        continue;
      }
      if (char === ";") {
        position += 1;
        continue;
      }
      const start = position;
      const end = itemEnd();
      const item = text.slice(start, end);
      if (text.charAt(end) !== "{") {
        position = text.charAt(end) === ";" ? end + 1 : end;
        if (owner !== null) {
          addDeclaration(owner, item, start);
        }
        continue;
      }
      position = end + 1;
      const prelude = normaliseSpace(item);
      const isAt = prelude.startsWith("@");
      const chain = isAt ? [...atRules, prelude] : atRules;
      const ruleSelector = isAt ? (selector ?? prelude) : nestSelector(selector, item);
      const line = lineOf(start);
      const rule: Rule = {
        kind: isAt ? "at" : "style",
        name: isAt ? (/^@([\w-]+)/.exec(prelude)?.[1] ?? "").toLowerCase() : "",
        selector: ruleSelector,
        atRule: chain.length > 0 ? chain.join(" ") : null,
        topLevel: owner === null,
        startLine: line,
        endLine: line,
      };
      rules.push(rule);
      readBlock(rule, isAt ? selector : ruleSelector, chain);
      rule.endLine = lineOf(Math.max(start, position - 1));
    }
  }

  readBlock(null, null, []);
  return { rules, declarations };
}

// ---------------------------------------------------------------------------------------------
// The raw-value policy
// ---------------------------------------------------------------------------------------------

export type DesignCategory =
  | "colour"
  | "spacing"
  | "typography"
  | "shape"
  | "elevation"
  | "motion"
  | "custom-property";

const SIDE = "(?:top|right|bottom|left|block|inline|block-start|block-end|inline-start|inline-end)";

/**
 * The properties whose values are design values, by category; the first match names the category.
 * Position offsets (`inset`, `top`), sizes (`width`, `height`) and `opacity` are deliberately
 * absent: they lay out a particular component rather than restate a design value, and control
 * heights are held by tokens and a browser check instead.
 */
export const GOVERNED_PROPERTIES: readonly (readonly [RegExp, DesignCategory])[] = [
  // The side shorthands carry a width as well as a colour; both parts are checked.
  [new RegExp(`^border(?:-${SIDE})?(?:-color)?$`), "colour"],
  [
    /^(?:color|background|background-color|outline|outline-color|fill|stroke|accent-color|caret-color|text-decoration-color)$/,
    "colour",
  ],
  [/^column-rule(?:-[a-z]+)?$/, "colour"],
  [/^(?:margin|padding)(?:-[a-z-]+)?$/, "spacing"],
  [/^(?:gap|row-gap|column-gap)$/, "spacing"],
  [/^(?:font|font-size|font-weight|font-family|line-height|letter-spacing)$/, "typography"],
  [/^border(?:-[a-z]+)*-radius$/, "shape"],
  [new RegExp(`^border(?:-${SIDE})?-width$`), "shape"],
  [/^(?:outline-width|outline-offset)$/, "shape"],
  [/^(?:box-shadow|z-index)$/, "elevation"],
  [/^(?:transition|animation)(?:-[a-z-]+)?$/, "motion"],
];

/** The category of a governed property, or null for a property the policy leaves alone. */
export function governedCategory(property: string): DesignCategory | null {
  if (property.startsWith("--")) {
    return "custom-property";
  }
  return GOVERNED_PROPERTIES.find(([pattern]) => pattern.test(property))?.[1] ?? null;
}

/**
 * What a governed declaration may say without a token. `"0"` stands for every zero, with or
 * without a unit (`0`, `0px`, `-0`, `0%`, `0s`); the rest are keywords, compared case-insensitively.
 *
 * Numbers, hex colours, colour functions and named colours are raw wherever they appear, whatever
 * this list says. Other identifiers (`inset`, `infinite`, a property name inside `transition`)
 * carry no design value and are not raw, with two exceptions where an identifier or string is the
 * value itself: a custom property outside the token block, and `font` and `font-family`. There,
 * anything not listed here is raw.
 */
export const ALLOWED_WITHOUT_TOKENS = [
  "0",
  "none",
  "auto",
  "inherit",
  "initial",
  "unset",
  "revert",
  "revert-layer",
  "transparent",
  "currentcolor",
  "normal",
  "solid",
  "dashed",
  "dotted",
  "italic",
  "uppercase",
  "tabular-nums",
  "ease",
  "ease-in",
  "ease-out",
  "ease-in-out",
  "linear",
  "step-start",
  "step-end",
] as const;

const ALLOWED_KEYWORDS = new Set<string>(ALLOWED_WITHOUT_TOKENS.filter((word) => word !== "0"));

/**
 * Keywords that name a size, a weight or a line width. Each is a design value spelt as a word, so
 * in the properties it sizes it is as raw as the number it stands for.
 */
export const NAMED_DESIGN_VALUES: readonly (readonly [RegExp, readonly string[]])[] = [
  [
    /^(?:font|font-size)$/,
    [
      ...["xx-small", "x-small", "small", "medium", "large", "x-large", "xx-large", "xxx-large"],
      ...["smaller", "larger"],
    ],
  ],
  [/^(?:font|font-weight)$/, ["bold", "bolder", "lighter"]],
  [
    /^(?:border(?:-[a-z-]+)?|outline|outline-width|column-rule|column-rule-width)$/,
    ["thin", "medium", "thick"],
  ],
];

/** Where the identifiers and strings left in a value are themselves the design value. */
const VALUE_IS_A_NAME = /^(?:font|font-family)$/;

const COLOUR_FUNCTIONS = new Set([
  "rgb",
  "rgba",
  "hsl",
  "hsla",
  "hwb",
  "lab",
  "lch",
  "oklab",
  "oklch",
  "color",
  "color-mix",
]);

/** Inside these, a unitless multiplier or divisor applied to a `var()` is arithmetic, not a value. */
const MATH_FUNCTIONS = new Set([
  "calc",
  "min",
  "max",
  "clamp",
  "round",
  "mod",
  "rem",
  "abs",
  "sign",
]);

/**
 * At-rules whose bodies hold descriptors rather than style: `font-weight: 400 700` in `@font-face`
 * says which weights a file covers, not how anything is drawn.
 */
export const DESCRIPTOR_AT_RULES: ReadonlySet<string> = new Set([
  "font-face",
  "property",
  "counter-style",
  "font-feature-values",
  "font-palette-values",
]);

export interface AllowEntry {
  selector: string;
  property: string;
  value: string;
  reason: string;
}

export interface RawValueFinding extends Declaration {
  category: DesignCategory;
  /** The raw pieces, as written: `#fff`, `12px`, `rgb(0 0 0)`, `red`. */
  raw: string[];
}

/**
 * Every governed declaration outside the token block whose value is raw: one that, once every
 * `var()` (fallbacks included) and every allowed keyword and zero is removed, still holds a hex
 * colour, a colour function, a named colour, or a non-zero number or dimension. Inside `calc()` and
 * the other math functions a unitless multiplier or divisor beside a `var()` is allowed; a length
 * or percentage is not. A custom property outside the token block is governed too, since it would
 * be a second token layer, and is clean only when it says nothing a token should.
 *
 * Only custom properties in the token block are exempt. A non-custom declaration inside it is
 * governed like any other, so the block cannot hide a value.
 *
 * `allow` suppresses findings by selector, property and value, each compared after whitespace
 * normalisation (a trailing `!important` on an entry's value is ignored). Each entry must give a
 * reason, and the entries that matched nothing come back in `unusedAllow`, so a test can refuse
 * stale entries and the list can only shrink.
 */
export function rawValueFindings(
  css: string,
  allow: readonly AllowEntry[],
): { findings: RawValueFinding[]; unusedAllow: AllowEntry[] } {
  for (const entry of allow) {
    if (entry.reason.trim() === "") {
      throw new Error(
        `allow entry ${entry.selector} { ${entry.property}: ${entry.value} } must give a reason`,
      );
    }
  }
  const parsed = readStylesheet(css);
  const tokens = tokenRule(parsed);
  const used = new Set<AllowEntry>();
  const findings: RawValueFinding[] = [];
  for (const { declaration, rule } of parsed.declarations) {
    const found = rawValuesOf(declaration, rule, tokens);
    if (found === null) {
      continue;
    }
    const entry = allow.find((candidate) => allowMatches(candidate, declaration));
    if (entry === undefined) {
      findings.push({ ...declaration, ...found });
    } else {
      used.add(entry);
    }
  }
  return { findings, unusedAllow: allow.filter((entry) => !used.has(entry)) };
}

/** The raw pieces of one value, for a property as written in a governed declaration. */
export function rawPieces(property: string, value: string): string[] {
  const raw: string[] = [];
  const custom = property.startsWith("--");
  const named = new Set(
    NAMED_DESIGN_VALUES.filter(([pattern]) => pattern.test(property)).flatMap(([, words]) => words),
  );
  collectRaw(parseValue(value), { names: custom || VALUE_IS_A_NAME.test(property), named }, raw);
  return raw;
}

function rawValuesOf(
  declaration: Declaration,
  rule: Rule,
  tokens: Rule | undefined,
): { category: DesignCategory; raw: string[] } | null {
  if (rule.kind === "at" && DESCRIPTOR_AT_RULES.has(rule.name)) {
    return null;
  }
  if (rule === tokens && declaration.property.startsWith("--")) {
    return null;
  }
  const category = governedCategory(declaration.property);
  if (category === null) {
    return null;
  }
  const raw = rawPieces(declaration.property, declaration.value);
  return raw.length === 0 ? null : { category, raw };
}

function normaliseValue(value: string): string {
  return normaliseSpace(value)
    .replace(IMPORTANT, "")
    .replace(/\s*,\s*/g, ", ")
    .replace(/\(\s+/g, "(")
    .replace(/\s+\)/g, ")");
}

function allowMatches(entry: AllowEntry, declaration: Declaration): boolean {
  const property = entry.property.trim();
  return (
    normaliseSelector(entry.selector) === declaration.selector &&
    (property.startsWith("--") ? property : property.toLowerCase()) === declaration.property &&
    normaliseValue(entry.value) === normaliseValue(declaration.value)
  );
}

type ValueNode =
  | { kind: "function"; name: string; text: string; children: ValueNode[] }
  | { kind: "group"; text: string; children: ValueNode[] }
  | { kind: "number"; text: string; value: number; unit: string }
  | { kind: "hash" | "ident" | "string" | "delim" | "space"; text: string };

const NUMBER = /[+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?/y;
/** Letters, `_` and anything beyond ASCII can start a CSS name. */
const isNameStartChar = (char: string): boolean =>
  /[A-Za-z_]/.test(char) || char.charCodeAt(0) > 127;
const isNameChar = (char: string): boolean => /[\w-]/.test(char) || char.charCodeAt(0) > 127;

/** A CSS value as a tree of the tokens the policy needs, with functions and parentheses nested. */
function parseValue(text: string): ValueNode[] {
  let position = 0;

  function isNameStart(index: number): boolean {
    const char = text.charAt(index);
    if (char === "-") {
      const next = text.charAt(index + 1);
      return next === "-" || isNameStartChar(next);
    }
    return char === "\\" || isNameStartChar(char);
  }

  function readName(): string {
    const start = position;
    while (position < text.length) {
      const char = text.charAt(position);
      if (char === "\\") {
        position += 2;
      } else if (isNameChar(char)) {
        position += 1;
      } else {
        break;
      }
    }
    return text.slice(start, position);
  }

  function startsNumber(index: number): boolean {
    const char = text.charAt(index);
    const next = text.charAt(index + 1);
    const digit = (at: string): boolean => at >= "0" && at <= "9";
    if (digit(char)) {
      return true;
    }
    if (char === ".") {
      return digit(next);
    }
    return (
      (char === "+" || char === "-") &&
      (digit(next) || (next === "." && digit(text.charAt(index + 2))))
    );
  }

  /** The offset just past the `)` closing an unquoted `url(`. */
  function urlEnd(): number {
    let index = position;
    while (index < text.length && text.charAt(index) !== ")") {
      const char = text.charAt(index);
      index = char === '"' || char === "'" ? endOfQuoted(text, index) : index + 1;
    }
    return Math.min(text.length, index + 1);
  }

  function read(closing: boolean): ValueNode[] {
    const nodes: ValueNode[] = [];
    while (position < text.length) {
      const start = position;
      const char = text.charAt(position);
      if (char === ")" && closing) {
        position += 1;
        return nodes;
      }
      if (/\s/.test(char)) {
        while (position < text.length && /\s/.test(text.charAt(position))) {
          position += 1;
        }
        nodes.push({ kind: "space", text: " " });
      } else if (char === '"' || char === "'") {
        position = endOfQuoted(text, position);
        nodes.push({ kind: "string", text: text.slice(start, position) });
      } else if (char === "#") {
        position += 1;
        readName();
        nodes.push({ kind: "hash", text: text.slice(start, position) });
      } else if (char === "(") {
        position += 1;
        const children = read(true);
        nodes.push({ kind: "group", text: text.slice(start, position), children });
      } else if (startsNumber(position)) {
        NUMBER.lastIndex = position;
        const digits = NUMBER.exec(text)?.[0] ?? char;
        position += digits.length;
        let unit = "";
        if (text.charAt(position) === "%") {
          unit = "%";
          position += 1;
        } else if (isNameStart(position)) {
          unit = readName();
        }
        const value = Number.parseFloat(digits);
        nodes.push({ kind: "number", text: text.slice(start, position), value, unit });
      } else if (isNameStart(position)) {
        const name = readName();
        if (text.charAt(position) !== "(") {
          nodes.push({ kind: "ident", text: name });
          continue;
        }
        position += 1;
        const lower = name.toLowerCase();
        if (lower === "url") {
          position = urlEnd();
          nodes.push({
            kind: "function",
            name: lower,
            text: text.slice(start, position),
            children: [],
          });
          continue;
        }
        const children = read(true);
        nodes.push({ kind: "function", name: lower, text: text.slice(start, position), children });
      } else {
        position += 1;
        nodes.push({ kind: "delim", text: char });
      }
    }
    return nodes;
  }

  return read(false);
}

function containsVar(nodes: readonly ValueNode[]): boolean {
  return nodes.some(
    (node) =>
      (node.kind === "function" && (node.name === "var" || containsVar(node.children))) ||
      (node.kind === "group" && containsVar(node.children)),
  );
}

/** The nearest node before (`step` -1) or after (`step` 1) `index` that is not whitespace. */
function neighbour(
  nodes: readonly ValueNode[],
  index: number,
  step: -1 | 1,
): ValueNode | undefined {
  for (let at = index + step; at >= 0 && at < nodes.length; at += step) {
    const node = nodes[at];
    if (node?.kind !== "space") {
      return node;
    }
  }
  return undefined;
}

function isScalingOperator(node: ValueNode | undefined): boolean {
  return node?.kind === "delim" && (node.text === "*" || node.text === "/");
}

interface RawContext {
  /** Whether a leftover identifier or string is itself a value. */
  names: boolean;
  /** Keywords that are raw in this property. */
  named: ReadonlySet<string>;
}

/**
 * Pushes the raw pieces among `nodes`. `math` is set inside a math function or its parentheses,
 * where `scaled` says whether that expression refers to a `var()` a unitless factor could scale.
 */
function collectRaw(
  nodes: readonly ValueNode[],
  context: RawContext,
  raw: string[],
  math = false,
  scaled = false,
): void {
  nodes.forEach((node, index) => {
    switch (node.kind) {
      case "function":
        if (node.name === "var" || node.name === "url") {
          return;
        }
        if (COLOUR_FUNCTIONS.has(node.name)) {
          raw.push(node.text);
        } else if (MATH_FUNCTIONS.has(node.name)) {
          collectRaw(node.children, context, raw, true, containsVar(node.children));
        } else {
          // Inside an ordinary function (a gradient, `cubic-bezier`), words are arguments.
          collectRaw(node.children, { names: false, named: context.named }, raw);
        }
        return;
      case "group":
        collectRaw(node.children, context, raw, math, math && containsVar(node.children));
        return;
      case "number": {
        const factor =
          math &&
          scaled &&
          node.unit === "" &&
          (isScalingOperator(neighbour(nodes, index, -1)) ||
            isScalingOperator(neighbour(nodes, index, 1)));
        if (node.value !== 0 && !factor) {
          raw.push(node.text);
        }
        return;
      }
      case "hash":
        raw.push(node.text);
        return;
      case "ident": {
        const word = node.text.toLowerCase();
        if (
          NAMED_COLOURS.has(word) ||
          context.named.has(word) ||
          (context.names && !ALLOWED_KEYWORDS.has(word))
        ) {
          raw.push(node.text);
        }
        return;
      }
      case "string":
        if (context.names) {
          raw.push(node.text);
        }
        return;
      default:
        return;
    }
  });
}

// ---------------------------------------------------------------------------------------------
// Inline style writes
// ---------------------------------------------------------------------------------------------

export interface InlineStyleFinding {
  path: string;
  line: number;
  /**
   * The CSS property written (`display`, `background-color`, `--stage-scale`), `cssText` or
   * `style` for a bulk write, or `[expression]` when the property is computed.
   */
  property: string;
  /** The source line, trimmed. */
  code: string;
}

export interface InlineAllowEntry {
  path: string;
  property: string;
  count: number;
  reason: string;
}

const ASSIGNS = String.raw`\s*(?:\+=|\?\?=|\|\|=|&&=|=(?![=>]))`;
const STYLE_MEMBER_WRITE = new RegExp(String.raw`\.style\s*\.\s*([A-Za-z_$][\w$]*)${ASSIGNS}`, "g");
const STYLE_INDEX_WRITE = new RegExp(String.raw`\.style\s*\[\s*([^\]]+?)\s*\]${ASSIGNS}`, "g");
const STYLE_METHOD = /\.style\s*\.\s*(?:setProperty|removeProperty)\s*\(\s*([^,)]*)/g;
const STYLE_ATTRIBUTE = /\bsetAttribute(?:NS\s*\(\s*[^,()]*,|\s*\()\s*(["'`])style\1/g;
const STYLE_OBJECT_ASSIGN = /\bObject\s*\.\s*assign\s*\(\s*[^,;]*?\.style\s*[,)]/g;
/**
 * Markup built in a string: `<span style="…">` in a template literal written to `innerHTML`. An
 * attribute selector (`[style="…"]`) reads styles rather than writing them, and is not reported.
 */
const STYLE_MARKUP_IN_STRING = /(?<![\w[-])style\s*=\s*(?:["'`]|\$\{)/g;

/**
 * Every inline style write in the given sources. Scripts (anything not `.html` or `.htm`, with or
 * without a trailing `.txt`) are scanned for `.style.<property> =` and `+=`, `.style["property"] =`,
 * `.style.setProperty(` and `.style.removeProperty(`, `.style.cssText =`, `setAttribute("style"`,
 * `Object.assign(x.style`, and a `style=` attribute inside a string literal. Markup is scanned for
 * `style` attributes, and its `<script>` elements as scripts.
 *
 * Comments are skipped, and so are reads. A `.style` member counts only when a CSS-like name (letters
 * only) follows it and is assigned, so `request.style === "bodies"` and `badge.style` on a data
 * object are not writes. Assigning a string to `.style` itself is not reported, since without types
 * it cannot be told from a data object's field.
 */
export function inlineStyleFindings(
  files: readonly { path: string; text: string }[],
): InlineStyleFinding[] {
  return files
    .flatMap((file) =>
      /\.html?(?:\.txt)?$/i.test(file.path)
        ? markupFindings(file.path, file.text)
        : scriptFindings(file.path, file.text, file.text),
    )
    .sort((left, right) => left.path.localeCompare(right.path) || left.line - right.line);
}

/**
 * Checks findings against counted allowances. An entry allows exactly `count` writes of its
 * property in its file: when there are more, every write of that property in that file is
 * unallowed, so the message shows all the sites to choose among; when there are fewer the entry is
 * stale, so the count has to fall with the code.
 */
export function matchInlineAllow(
  findings: readonly InlineStyleFinding[],
  allow: readonly InlineAllowEntry[],
): { unallowed: InlineStyleFinding[]; stale: string[] } {
  const key = (path: string, property: string): string => JSON.stringify([path, property]);
  const entries = new Map<string, InlineAllowEntry>();
  for (const entry of allow) {
    const name = `${entry.path}: ${entry.property}`;
    if (entry.reason.trim() === "") {
      throw new Error(`inline style allowance ${name} must give a reason`);
    }
    if (!Number.isInteger(entry.count) || entry.count < 1) {
      throw new Error(`inline style allowance ${name} must allow a positive whole count`);
    }
    if (entries.has(key(entry.path, entry.property))) {
      throw new Error(`inline style allowance ${name} is listed twice`);
    }
    entries.set(key(entry.path, entry.property), entry);
  }
  const groups = new Map<string, InlineStyleFinding[]>();
  for (const finding of findings) {
    const group = key(finding.path, finding.property);
    groups.set(group, [...(groups.get(group) ?? []), finding]);
  }
  const unallowed: InlineStyleFinding[] = [];
  for (const [group, sites] of groups) {
    const entry = entries.get(group);
    if (entry === undefined || sites.length > entry.count) {
      unallowed.push(...sites);
    }
  }
  const stale: string[] = [];
  for (const [group, entry] of entries) {
    const found = groups.get(group)?.length ?? 0;
    if (found < entry.count) {
      stale.push(
        `${entry.path}: ${entry.property} allows ${entry.count}, found ${found}; lower the count`,
      );
    }
  }
  return { unallowed, stale };
}

/** Leaves only the given ranges of `text`, blanking the rest but its newlines. */
function keepRanges(text: string, ranges: readonly (readonly [number, number])[]): string {
  const out = blankText(text).split("");
  for (const [start, end] of ranges) {
    for (let index = start; index < end; index += 1) {
      out[index] = text.charAt(index);
    }
  }
  return out.join("");
}

function markupFindings(path: string, source: string): InlineStyleFinding[] {
  const uncommented = source.replace(/<!--[\s\S]*?(?:-->|$)/g, blankText);
  const scripts: (readonly [number, number])[] = [];
  const bodies: (readonly [number, number])[] = [];
  for (const match of uncommented.matchAll(
    /<(script|style)\b(?:[^>"']|"[^"]*"|'[^']*')*>([\s\S]*?)(?:<\/\1\s*>|$)/gi,
  )) {
    const bodyStart = match.index + match[0].indexOf(">") + 1;
    const range = [bodyStart, bodyStart + (match[2] ?? "").length] as const;
    bodies.push(range);
    if ((match[1] ?? "").toLowerCase() === "script") {
      scripts.push(range);
    }
  }
  const findings = scriptFindings(path, source, keepRanges(uncommented, scripts));
  let markup = uncommented;
  for (const [start, end] of bodies) {
    markup = markup.slice(0, start) + blankText(markup.slice(start, end)) + markup.slice(end);
  }
  const lineOf = lineIndex(source);
  const lines = source.split("\n");
  for (const tag of markup.matchAll(/<[A-Za-z][\w:.-]*((?:[^>"']|"[^"]*"|'[^']*')*)>/g)) {
    const attributes = tag[1] ?? "";
    const base = tag.index + tag[0].indexOf(attributes);
    for (const attribute of attributes.matchAll(
      /([^\s"'=<>/`]+)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s"'=<>`]+))?/g,
    )) {
      if ((attribute[1] ?? "").toLowerCase() === "style") {
        const line = lineOf(base + attribute.index);
        findings.push({ path, line, property: "style", code: (lines[line - 1] ?? "").trim() });
      }
    }
  }
  return findings;
}

/**
 * Inline style writes in `script`, a copy of `source` in which anything that is not script has
 * already been blanked. Lines and code come from `source`.
 */
function scriptFindings(path: string, source: string, script: string): InlineStyleFinding[] {
  const { code, strings } = maskScript(script);
  const lineOf = lineIndex(source);
  const lines = source.split("\n");
  const findings: InlineStyleFinding[] = [];
  const report = (offset: number, property: string): void => {
    const line = lineOf(offset);
    findings.push({ path, line, property, code: (lines[line - 1] ?? "").trim() });
  };
  for (const match of code.matchAll(STYLE_MEMBER_WRITE)) {
    const member = match[1] ?? "";
    if (strings[match.index] === 0 && /^[A-Za-z]+$/.test(member)) {
      report(match.index, cssPropertyName(member));
    }
  }
  for (const match of code.matchAll(STYLE_INDEX_WRITE)) {
    if (strings[match.index] === 0) {
      report(match.index, writtenProperty(match[1] ?? ""));
    }
  }
  for (const match of code.matchAll(STYLE_METHOD)) {
    if (strings[match.index] === 0) {
      report(match.index, writtenProperty(match[1] ?? ""));
    }
  }
  for (const pattern of [STYLE_ATTRIBUTE, STYLE_OBJECT_ASSIGN]) {
    for (const match of code.matchAll(pattern)) {
      if (strings[match.index] === 0) {
        report(match.index, "style");
      }
    }
  }
  for (const match of code.matchAll(STYLE_MARKUP_IN_STRING)) {
    if (strings[match.index] === 1) {
      report(match.index, "style");
    }
  }
  return findings;
}

/** The CSS name of a `CSSStyleDeclaration` member: `backgroundColor` is `background-color`. */
function cssPropertyName(member: string): string {
  if (member === "cssText") {
    return member;
  }
  if (member === "cssFloat") {
    return "float";
  }
  const kebab = member.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
  return /^(?:webkit|moz|ms)-/.test(kebab) ? `-${kebab}` : kebab;
}

/** The property named by a string literal argument or index, or the expression in brackets. */
function writtenProperty(expression: string): string {
  const literal = /^(["'`])([^"'`]*)\1$/.exec(expression.trim());
  if (literal === null || (literal[2] ?? "").includes("${")) {
    return `[${expression.trim()}]`;
  }
  const name = literal[2] ?? "";
  return name.includes("-") ? name : cssPropertyName(name);
}

const REGEX_AFTER = new Set("(,=:[!&|?{};+-*%<>~^".split(""));
const REGEX_AFTER_WORD =
  /(?:^|[^\w$])(?:return|typeof|case|do|else|in|of|new|delete|void|throw|yield|await|instanceof)\s*$/;

/**
 * The script with its comments blanked (newlines kept), and a mask of the offsets inside string and
 * template literals. Regular expression literals are recognised, by the character before them, so
 * that a quote or `/*` inside one is not mistaken for the start of a string or a comment.
 */
function maskScript(source: string): { code: string; strings: Uint8Array } {
  const out = source.split("");
  const strings = new Uint8Array(source.length);
  const blank = (start: number, end: number): void => {
    for (let index = start; index < end; index += 1) {
      if (out[index] !== "\n") {
        out[index] = " ";
      }
    }
  };
  // For each open template substitution, the brace depth its closing `}` returns to.
  const substitutions: number[] = [];
  let depth = 0;
  let inTemplate = false;
  let previous = "";
  let index = 0;
  while (index < source.length) {
    const char = source.charAt(index);
    if (inTemplate) {
      if (char === "`") {
        inTemplate = false;
        previous = char;
        index += 1;
      } else if (char === "$" && source.charAt(index + 1) === "{") {
        substitutions.push(depth);
        depth += 1;
        inTemplate = false;
        previous = "{";
        index += 2;
      } else {
        const width = char === "\\" ? 2 : 1;
        strings.fill(1, index, index + width);
        index += width;
      }
      continue;
    }
    const next = source.charAt(index + 1);
    if (char === "/" && next === "/") {
      const newline = source.indexOf("\n", index);
      const end = newline < 0 ? source.length : newline;
      blank(index, end);
      index = end;
    } else if (char === "/" && next === "*") {
      const close = source.indexOf("*/", index + 2);
      const end = close < 0 ? source.length : close + 2;
      blank(index, end);
      index = end;
    } else if (char === '"' || char === "'") {
      const end = endOfQuoted(source, index);
      strings.fill(1, index + 1, Math.max(index + 1, end - 1));
      previous = char;
      index = end;
    } else if (char === "`") {
      inTemplate = true;
      index += 1;
    } else if (char === "/" && startsRegex(source, index, previous)) {
      index = regexEnd(source, index);
      previous = "/";
    } else {
      if (char === "{") {
        depth += 1;
      } else if (char === "}") {
        depth -= 1;
        if (substitutions.length > 0 && substitutions[substitutions.length - 1] === depth) {
          substitutions.pop();
          inTemplate = true;
        }
      }
      if (!/\s/.test(char)) {
        previous = char;
      }
      index += 1;
    }
  }
  return { code: out.join(""), strings };
}

function startsRegex(source: string, index: number, previous: string): boolean {
  if (previous === "" || REGEX_AFTER.has(previous)) {
    return true;
  }
  return (
    /[\w$]/.test(previous) && REGEX_AFTER_WORD.test(source.slice(Math.max(0, index - 16), index))
  );
}

function regexEnd(source: string, start: number): number {
  let inClass = false;
  let index = start + 1;
  while (index < source.length) {
    const char = source.charAt(index);
    if (char === "\\") {
      index += 2;
      continue;
    }
    if (char === "\n") {
      return index;
    }
    if (inClass) {
      inClass = char !== "]";
    } else if (char === "[") {
      inClass = true;
    } else if (char === "/") {
      index += 1;
      while (/[a-z]/i.test(source.charAt(index))) {
        index += 1;
      }
      return index;
    }
    index += 1;
  }
  return index;
}

// ---------------------------------------------------------------------------------------------
// Colour and contrast
// ---------------------------------------------------------------------------------------------

/** A colour in gamma-encoded sRGB, every channel and alpha in 0..1. */
export interface Colour {
  r: number;
  g: number;
  b: number;
  a: number;
}

export interface ContrastPair {
  /** A token name (`--ink`), a value with `var()` references, or a colour. */
  fg: string;
  bg: string;
  min: number;
  role: string;
}

export interface ContrastFailure extends ContrastPair {
  /** The computed ratio rounded down to two decimals, so a failure never prints as its minimum. */
  ratio: number;
}

const clamp = (value: number): number => Math.min(1, Math.max(0, value));

/**
 * Parses `#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, `rgb()` and `rgba()` in comma or space syntax
 * with an optional `/ alpha`, `oklch(L C H)` with an optional `/ alpha`, `transparent`, and the
 * named colours. An `oklch()` outside sRGB is clamped channel by channel. Anything else throws.
 */
export function parseColour(value: string): Colour {
  const text = normaliseSpace(value).toLowerCase();
  if (text === "transparent") {
    return { r: 0, g: 0, b: 0, a: 0 };
  }
  const named = NAMED_COLOURS.get(text);
  if (named !== undefined) {
    return parseColour(named);
  }
  const hex = /^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/.exec(text)?.[1];
  if (hex !== undefined) {
    const pairs =
      hex.length <= 4 ? hex.split("").map((digit) => digit + digit) : (hex.match(/../g) ?? []);
    const [r = 0, g = 0, b = 0, a = 255] = pairs.map((pair) => Number.parseInt(pair, 16) / 255);
    return { r, g, b, a: a === 255 ? 1 : a };
  }
  const call = /^(rgba?|oklch)\((.*)\)$/.exec(text);
  if (call !== null) {
    const [name = "", inner = ""] = call.slice(1);
    const { channels, alpha } = components(inner, value);
    if (name === "oklch") {
      const [lightness = "", chroma = "", hue = ""] = channels;
      return {
        ...oklchToSrgb(amount(lightness, 1, value), amount(chroma, 0.4, value), angle(hue, value)),
        a: alpha,
      };
    }
    const [r = 0, g = 0, b = 0] = channels.map((channel) =>
      channel.endsWith("%") ? amount(channel, 1, value) : amount(channel, 1, value) / 255,
    );
    return { r: clamp(r), g: clamp(g), b: clamp(b), a: alpha };
  }
  throw new Error(`unsupported colour: ${value}`);
}

function components(inner: string, value: string): { channels: string[]; alpha: number } {
  const [main = "", slashed, ...extra] = inner.split("/");
  const channels = main.split(/[\s,]+/).filter((part) => part !== "");
  const written = slashed?.trim() ?? (channels.length === 4 ? channels.pop() : undefined);
  if (extra.length > 0 || channels.length !== 3) {
    throw new Error(`unsupported colour: ${value}`);
  }
  return { channels, alpha: written === undefined ? 1 : clamp(amount(written, 1, value)) };
}

/** A number, or a percentage of `whole`; `none` is zero. */
function amount(text: string, whole: number, value: string): number {
  if (text === "none") {
    return 0;
  }
  const number = Number(text.endsWith("%") ? text.slice(0, -1) : text);
  if (!Number.isFinite(number)) {
    throw new Error(`unsupported colour: ${value}`);
  }
  return text.endsWith("%") ? (number / 100) * whole : number;
}

/** A hue in degrees. */
function angle(text: string, value: string): number {
  const match = /^(.*?)(deg|grad|rad|turn)?$/.exec(text);
  const degrees = amount(match?.[1] ?? "", 1, value);
  switch (match?.[2]) {
    case "grad":
      return degrees * 0.9;
    case "rad":
      return (degrees * 180) / Math.PI;
    case "turn":
      return degrees * 360;
    default:
      return degrees;
  }
}

/** OKLCH through OKLab and linear sRGB (Björn Ottosson's matrices) to clamped, encoded sRGB. */
function oklchToSrgb(lightness: number, chroma: number, hue: number): Omit<Colour, "a"> {
  const radians = (hue * Math.PI) / 180;
  const a = chroma * Math.cos(radians);
  const b = chroma * Math.sin(radians);
  const l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3;
  const encode = (linear: number): number => {
    const magnitude = Math.abs(linear);
    const encoded =
      magnitude <= 0.0031308 ? 12.92 * magnitude : 1.055 * magnitude ** (1 / 2.4) - 0.055;
    return clamp(Math.sign(linear) * encoded);
  };
  return {
    r: encode(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    g: encode(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    b: encode(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  };
}

/**
 * The value of a token with every `var()` in it substituted, following chains and fallbacks. A
 * cycle throws, and so does a name with no token and no fallback.
 */
export function resolveToken(name: string, tokens: ReadonlyMap<string, string>): string {
  return resolveVariable(name, undefined, tokens, []);
}

function resolveVariable(
  name: string,
  fallback: string | undefined,
  tokens: ReadonlyMap<string, string>,
  chain: readonly string[],
): string {
  if (chain.includes(name)) {
    throw new Error(`token cycle: ${[...chain, name].join(" -> ")}`);
  }
  const own = tokens.get(name);
  if (own !== undefined) {
    return resolveValue(own, tokens, [...chain, name]);
  }
  if (fallback !== undefined) {
    return resolveValue(fallback, tokens, chain);
  }
  const via = chain.length > 0 ? ` (via ${chain.join(" -> ")})` : "";
  throw new Error(`unresolved token ${name}${via}`);
}

function resolveValue(
  value: string,
  tokens: ReadonlyMap<string, string>,
  chain: readonly string[],
): string {
  const reference = /(?<![\w-])var\(/gi;
  let resolved = "";
  let copied = 0;
  for (;;) {
    reference.lastIndex = copied;
    const found = reference.exec(value);
    if (found === null) {
      return (resolved + value.slice(copied)).trim();
    }
    const open = found.index + found[0].length - 1;
    const close = closingParenthesis(value, open);
    const [name = "", ...rest] = splitTopLevel(value.slice(open + 1, close), ",");
    const fallback = rest.length > 0 ? rest.join(",").trim() : undefined;
    resolved +=
      value.slice(copied, found.index) + resolveVariable(name.trim(), fallback, tokens, chain);
    copied = close + 1;
  }
}

function closingParenthesis(text: string, open: number): number {
  let depth = 0;
  let index = open;
  while (index < text.length) {
    const char = text.charAt(index);
    if (char === '"' || char === "'") {
      index = endOfQuoted(text, index);
      continue;
    }
    if (char === "(") {
      depth += 1;
    } else if (char === ")") {
      depth -= 1;
      if (depth === 0) {
        return index;
      }
    }
    index += 1;
  }
  throw new Error(`unclosed var() in ${text}`);
}

function luminance(colour: Colour): number {
  const linear = (channel: number): number =>
    channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  return 0.2126 * linear(colour.r) + 0.7152 * linear(colour.g) + 0.0722 * linear(colour.b);
}

/** `top` composited over `bottom` in encoded sRGB, as a browser blends them. */
function over(top: Colour, bottom: Colour): Colour {
  const a = top.a + bottom.a * (1 - top.a);
  if (a === 0) {
    return { r: 0, g: 0, b: 0, a: 0 };
  }
  const mix = (upper: number, lower: number): number =>
    (upper * top.a + lower * bottom.a * (1 - top.a)) / a;
  return { r: mix(top.r, bottom.r), g: mix(top.g, bottom.g), b: mix(top.b, bottom.b), a };
}

const WHITE: Colour = { r: 1, g: 1, b: 1, a: 1 };

/**
 * The WCAG 2.x contrast ratio of a foreground on a background, from 1 to 21. A translucent
 * background is first composited over white, the page's canvas, and a translucent foreground over
 * that background.
 */
export function contrastRatio(foreground: Colour | string, background: Colour | string): number {
  const toColour = (colour: Colour | string): Colour =>
    typeof colour === "string" ? parseColour(colour) : colour;
  const ground = over(toColour(background), WHITE);
  const ink = over(toColour(foreground), ground);
  const [first, second] = [luminance(ink), luminance(ground)];
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

/** The pairs whose contrast falls below their minimum, each with its ratio. */
export function checkContrast(
  tokens: ReadonlyMap<string, string>,
  pairs: readonly ContrastPair[],
): ContrastFailure[] {
  const colourOf = (reference: string): Colour =>
    parseColour(
      reference.startsWith("--")
        ? resolveToken(reference, tokens)
        : resolveValue(reference, tokens, []),
    );
  return pairs.flatMap((pair) => {
    const ratio = contrastRatio(colourOf(pair.fg), colourOf(pair.bg));
    return ratio < pair.min ? [{ ...pair, ratio: Math.floor(ratio * 100) / 100 }] : [];
  });
}

/** The CSS named colours (CSS Color 4), each with its sRGB value. */
export const NAMED_COLOURS: ReadonlyMap<string, string> = new Map(
  Object.entries({
    aliceblue: "#f0f8ff",
    antiquewhite: "#faebd7",
    aqua: "#00ffff",
    aquamarine: "#7fffd4",
    azure: "#f0ffff",
    beige: "#f5f5dc",
    bisque: "#ffe4c4",
    black: "#000000",
    blanchedalmond: "#ffebcd",
    blue: "#0000ff",
    blueviolet: "#8a2be2",
    brown: "#a52a2a",
    burlywood: "#deb887",
    cadetblue: "#5f9ea0",
    chartreuse: "#7fff00",
    chocolate: "#d2691e",
    coral: "#ff7f50",
    cornflowerblue: "#6495ed",
    cornsilk: "#fff8dc",
    crimson: "#dc143c",
    cyan: "#00ffff",
    darkblue: "#00008b",
    darkcyan: "#008b8b",
    darkgoldenrod: "#b8860b",
    darkgray: "#a9a9a9",
    darkgreen: "#006400",
    darkgrey: "#a9a9a9",
    darkkhaki: "#bdb76b",
    darkmagenta: "#8b008b",
    darkolivegreen: "#556b2f",
    darkorange: "#ff8c00",
    darkorchid: "#9932cc",
    darkred: "#8b0000",
    darksalmon: "#e9967a",
    darkseagreen: "#8fbc8f",
    darkslateblue: "#483d8b",
    darkslategray: "#2f4f4f",
    darkslategrey: "#2f4f4f",
    darkturquoise: "#00ced1",
    darkviolet: "#9400d3",
    deeppink: "#ff1493",
    deepskyblue: "#00bfff",
    dimgray: "#696969",
    dimgrey: "#696969",
    dodgerblue: "#1e90ff",
    firebrick: "#b22222",
    floralwhite: "#fffaf0",
    forestgreen: "#228b22",
    fuchsia: "#ff00ff",
    gainsboro: "#dcdcdc",
    ghostwhite: "#f8f8ff",
    gold: "#ffd700",
    goldenrod: "#daa520",
    gray: "#808080",
    green: "#008000",
    greenyellow: "#adff2f",
    grey: "#808080",
    honeydew: "#f0fff0",
    hotpink: "#ff69b4",
    indianred: "#cd5c5c",
    indigo: "#4b0082",
    ivory: "#fffff0",
    khaki: "#f0e68c",
    lavender: "#e6e6fa",
    lavenderblush: "#fff0f5",
    lawngreen: "#7cfc00",
    lemonchiffon: "#fffacd",
    lightblue: "#add8e6",
    lightcoral: "#f08080",
    lightcyan: "#e0ffff",
    lightgoldenrodyellow: "#fafad2",
    lightgray: "#d3d3d3",
    lightgreen: "#90ee90",
    lightgrey: "#d3d3d3",
    lightpink: "#ffb6c1",
    lightsalmon: "#ffa07a",
    lightseagreen: "#20b2aa",
    lightskyblue: "#87cefa",
    lightslategray: "#778899",
    lightslategrey: "#778899",
    lightsteelblue: "#b0c4de",
    lightyellow: "#ffffe0",
    lime: "#00ff00",
    limegreen: "#32cd32",
    linen: "#faf0e6",
    magenta: "#ff00ff",
    maroon: "#800000",
    mediumaquamarine: "#66cdaa",
    mediumblue: "#0000cd",
    mediumorchid: "#ba55d3",
    mediumpurple: "#9370db",
    mediumseagreen: "#3cb371",
    mediumslateblue: "#7b68ee",
    mediumspringgreen: "#00fa9a",
    mediumturquoise: "#48d1cc",
    mediumvioletred: "#c71585",
    midnightblue: "#191970",
    mintcream: "#f5fffa",
    mistyrose: "#ffe4e1",
    moccasin: "#ffe4b5",
    navajowhite: "#ffdead",
    navy: "#000080",
    oldlace: "#fdf5e6",
    olive: "#808000",
    olivedrab: "#6b8e23",
    orange: "#ffa500",
    orangered: "#ff4500",
    orchid: "#da70d6",
    palegoldenrod: "#eee8aa",
    palegreen: "#98fb98",
    paleturquoise: "#afeeee",
    palevioletred: "#db7093",
    papayawhip: "#ffefd5",
    peachpuff: "#ffdab9",
    peru: "#cd853f",
    pink: "#ffc0cb",
    plum: "#dda0dd",
    powderblue: "#b0e0e6",
    purple: "#800080",
    rebeccapurple: "#663399",
    red: "#ff0000",
    rosybrown: "#bc8f8f",
    royalblue: "#4169e1",
    saddlebrown: "#8b4513",
    salmon: "#fa8072",
    sandybrown: "#f4a460",
    seagreen: "#2e8b57",
    seashell: "#fff5ee",
    sienna: "#a0522d",
    silver: "#c0c0c0",
    skyblue: "#87ceeb",
    slateblue: "#6a5acd",
    slategray: "#708090",
    slategrey: "#708090",
    snow: "#fffafa",
    springgreen: "#00ff7f",
    steelblue: "#4682b4",
    tan: "#d2b48c",
    teal: "#008080",
    thistle: "#d8bfd8",
    tomato: "#ff6347",
    turquoise: "#40e0d0",
    violet: "#ee82ee",
    wheat: "#f5deb3",
    white: "#ffffff",
    whitesmoke: "#f5f5f5",
    yellow: "#ffff00",
    yellowgreen: "#9acd32",
  }),
);
