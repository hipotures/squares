import type { Corpus, CorpusFacts } from "../data/corpus.js";
import { createDom, requireHtml } from "./dom.ts";

/** The label under each badge the panel draws, keyed `glyph/style`. */
export const BADGE_LABELS: Readonly<Record<string, string>> = {
  "★/star": "new result",
  "O/solid": "optimal",
  "=/solid": "exact",
  "≈/muted": "numerical",
  "R/solid": "rigid",
  "R/muted": "rigid (catalogue)",
};
/** The badge that says the lower bound on the stage was first proved here. */
export const NEW_RESULT_BADGE = Object.freeze({ glyph: "★", style: "star" });
const OPEN_LABELS: Readonly<Record<string, string>> = {
  optimality: "optimality",
  "exact value": "exact value",
  rigidity: "rigidity",
};

export interface FactsBadge {
  glyph: string;
  style: string;
  label: string;
}
/** What the panel says about one n, before any of it is drawn. */
export interface FactsPlan {
  /** PROVEN's badges, in order: `new result` first when the lower bound was first proved here. */
  badges: FactsBadge[];
  /** OPEN's items, or null when nothing is open and the section is left out, heading and all. */
  open: FactsBadge[] | null;
}

/**
 * The panel's content for one n.
 *
 * A bound first proved here is a badge of its own, `new result` under the red star, in the same
 * row and the same type as every other badge; it used to be a separate serif line under the
 * bound. OPEN is drawn only when something is open: a heading over the word "none" said nothing
 * the absence of the section does not.
 */
export function planFacts(facts: CorpusFacts, n: number): FactsPlan {
  const badges: FactsBadge[] = [];
  if (facts.star) {
    badges.push({ ...NEW_RESULT_BADGE, label: badgeLabel(NEW_RESULT_BADGE, n) });
  }
  for (const badge of facts.badges) {
    badges.push({ glyph: badge.glyph, style: badge.style, label: badgeLabel(badge, n) });
  }
  const open =
    facts.open.length === 0
      ? null
      : facts.open.map((key) => ({ glyph: "?", style: "query", label: OPEN_LABELS[key] ?? key }));
  return { badges, open };
}

/** A badge item's classes: `new result` is set in the star's colour, every other in the label's. */
export function badgeClass(badge: { glyph: string; style: string }): string {
  return badge.glyph === NEW_RESULT_BADGE.glyph && badge.style === NEW_RESULT_BADGE.style
    ? "badge-item is-new-result"
    : "badge-item";
}

function badgeLabel(badge: { glyph: string; style: string }, n: number): string {
  const label = BADGE_LABELS[`${badge.glyph}/${badge.style}`];
  if (label === undefined) {
    throw new Error(`unknown badge ${badge.glyph}/${badge.style} for n = ${n}`);
  }
  return label;
}

/** Catalogue fact panels only render trusted, build-time mathematical markup. */
export function createFactsView(document: Document, DATA: Corpus) {
  const { el, text } = createDom(document);
  const FACTS = DATA.facts;
  const METRICS = DATA.metrics;
  function glyphBaseline(glyph: string) {
    const b = METRICS.badge_baseline;
    return /[A-Za-z]/.test(glyph) ? b.letter : glyph === "?" ? b.query : b.math;
  }
  function approxPath() {
    const a = METRICS.approx;
    const k = a.font_size / 1000;
    const baseline = 9.5 + ((a.y0 + a.y1) / 2) * k;
    const tx = 9.5 - (a.advance * k) / 2;
    return el("path", {
      d: a.d,
      class: "glyph-path",
      "stroke-width": String(a.stroke_units),
      transform:
        "translate(" +
        tx.toFixed(3) +
        " " +
        baseline.toFixed(3) +
        ") scale(" +
        k.toFixed(4) +
        " -" +
        k.toFixed(4) +
        ")",
    });
  }
  function badgeSvg(glyph: string, style: string) {
    const s = el("svg", {
      viewBox: "-1 -1 21 21",
      class: `badge badge-${style}`,
      "aria-hidden": "true",
    });
    if (style === "star") {
      const k = (19 * METRICS.star_span) / (2 * METRICS.star_inset);
      const pts = DATA.star_points
        .map((p) => `${(9.5 + p[0] * k).toFixed(3)},${(9.5 + p[1] * k).toFixed(3)}`)
        .join(" ");
      s.appendChild(el("polygon", { points: pts, class: "star" }));
      return s;
    }
    s.appendChild(
      el("rect", { x: "0", y: "0", width: "19", height: "19", rx: "4.5", class: "box" }),
    );
    if (glyph === "≈") {
      s.appendChild(approxPath());
    } else {
      const t = el("text", {
        x: "9.5",
        y: String(glyphBaseline(glyph)),
        "text-anchor": "middle",
        class: "glyph",
      });
      t.textContent = glyph;
      s.appendChild(t);
    }
    return s;
  }
  function badgeItem(cls: string, glyph: string, style: string, label: string) {
    const item = text("span", cls);
    item.appendChild(badgeSvg(glyph, style));
    item.appendChild(text("span", "label", label));
    return item;
  }

  // **A typeset number is split into one span per character.** KaTeX sets a number as one span
  // (`4.67553`, `17`), and the handover holds a part only where the n and n + 1 layers draw it
  // identically, so a digit the two numbers share -- the `1` of 12 and 13 -- crossfaded with
  // itself and lightened mid-roll, against the owner's request that unchanged text never fade
  // out and back. Split, each character is a part of its own. The spans carry no class and no
  // style, so the line is drawn as before; only KaTeX's visible HTML is split, not its MathML.
  function splitNumerals(root: HTMLElement) {
    for (const leaf of root.querySelectorAll(".katex-html .mord")) {
      const digits = leaf.textContent ?? "";
      if (leaf.children.length > 0 || digits.length < 2 || !/[0-9]/.test(digits)) {
        continue;
      }
      leaf.textContent = "";
      for (const character of digits) {
        const span = document.createElement("span");
        span.textContent = character;
        leaf.appendChild(span);
      }
    }
  }

  function buildFacts(layer: HTMLElement, n: number) {
    const f = FACTS[String(n)];
    if (f === undefined) {
      throw new RangeError(`no catalogue facts for n = ${n}`);
    }
    layer.textContent = "";
    // The headline under the packing: `n = 26` is an equation, so it is set as one, the `=`
    // included. It belongs to the picture rather than to the panel, but it rolls with the layer
    // whose facts it names, so it is built here and placed in that layer's headline slot. Each
    // rolling slot draws only the number; a third, still slot draws `n =` and never fades (see
    // `buildPair` and the stylesheet), because a step changes the number and nothing else. Where it
    // starts is the headline's `--stage-numeral-left`, which the page measures once the faces land.
    const numeral = text("div", "numeral");
    if (f.html_headline) {
      numeral.innerHTML = f.html_headline;
    } else {
      numeral.appendChild(text("span", "n-val", String(n)));
    }
    // An empty inline block on the line stands on its baseline, which is where the stage's
    // attribution is set (`placeAttribution`). It has no width and no text.
    numeral.appendChild(text("span", "baseline"));
    const slot = requireHtml(document, layer.id === "facts-a" ? "numeral-a" : "numeral-b");
    slot.textContent = "";
    slot.appendChild(numeral);
    // **The mathematics is set by KaTeX, at build time.** It used to be assembled here from four
    // spans -- an italic `s`, an upright `(n)`, a relation glyph borrowed from a KaTeX face, and a
    // value in tabular figures -- which is an imitation of typesetting rather than typesetting: no
    // real spacing around the relation, no maths italic, and a closed form's fraction written with
    // a solidus because a vinculum was out of reach. The build now renders each line once through
    // the same KaTeX the explainer sets its paper with, so `s(11) <= 3.877084` is set here the way
    // it is set there. See `katex_html` in build_candidate.py for why that happens at build time.
    function mathLine(cls: string, html: string | null) {
      const line = text("div", cls);
      if (html) {
        line.innerHTML = html;
        splitNumerals(line);
      }
      return line;
    }
    // PROVED, in the order a reader wants it: the chained bound on the side, then the badges, led by
    // `new result` when its lower bound was first proved here. Both bounds are proved facts -- a
    // construction proves its upper bound -- so both belong here, and OPEN below carries the
    // questions.
    const plan = planFacts(f, n);
    layer.appendChild(text("div", "section-head head-proved", "Proven"));
    // The bound is one chained statement now, so it is one row. The star sits to the LEFT of
    // the lower bound it marks, inside a slot that is always the star's width whether or not
    // there is a star in it -- otherwise the whole inequality would step sideways at every n
    // that has one, which during a sweep is a line that jitters rather than rolls.
    const bound = mathLine("side", f.html_side);
    const starSlot = text("span", "bound-star");
    if (f.star) {
      starSlot.appendChild(badgeSvg("", "star"));
    }
    bound.insertBefore(starSlot, bound.firstChild);
    layer.appendChild(bound);
    // No closed-form line. It sat under a chain of two bounds and did not say which bound it was
    // the value of -- 108 of the 110 n that had one show `lower <= s(n) <= upper` -- so the owner
    // asked for it to go. The data keeps `html_exact` and `degree` for a design that attaches a
    // form to the bound it belongs to.
    const badges = text("div", "badges");
    for (const b of plan.badges) {
      badges.appendChild(badgeItem(badgeClass(b), b.glyph, b.style, b.label));
    }
    layer.appendChild(badges);
    // OPEN, only when something is open. The two layers are compared slot by slot, and OPEN's
    // slots come last, so a layer without them lines up with one that has them: those two slots
    // fade in or out whole while every slot before them hands over as before.
    if (plan.open !== null) {
      layer.appendChild(text("div", "section-head head-open", "Open"));
      const items = text("div", "open-items");
      for (const item of plan.open) {
        items.appendChild(badgeItem("open-item", item.glyph, item.style, item.label));
      }
      layer.appendChild(items);
    }
    return numeral;
  }
  return { buildFacts };
}
