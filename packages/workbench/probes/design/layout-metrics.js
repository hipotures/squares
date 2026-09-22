// The page's layout as measured boxes, for the layout-consistency check and the design gallery.
// Synchronous: a caller waits for the layout it changed to apply (`design/frames`) first.
//
// - `blocks`: the visible top-level blocks of the controls, in document order. `#panel` is a
//   wrapper, so its visible children stand in for it.
// - `panels`: every visible panel (a `.subpanel`), for overlap.
// - `rows`: every visible row of panels, with the boxes of the panels in it.
// - `controlsFound`: every visible button, select and text or number field, by kind, with its
//   height; a segmented group is measured whole as `segmented`, and its buttons as `segment`.
// - `controls` and `tokens`: the column's box and inline padding, and the layout tokens it is
//   held to, resolved to pixels.
// - `facts`: each stage facts layer's section heads, OPEN items and badges, with each badge
//   label's computed type, while the catalogue owns the stage.
// - `frames`: the three outer container borders the stage draws -- the catalogue's box and the
//   trace under it, and the container Pack and the animation studio draw -- as drawn, beside the
//   tokens they are held to. Null where no stage is shown.
// - `attribution`: the repository's address under the stage's legend, where its first character
//   starts and its baseline beside the legend's left edge and foot it is set from, its type, and
//   the boxes it must not be drawn over. Null where no stage is shown.
//
// The stage is a 1920 x 1080 poster drawn at `--stage-scale`, so `frames` and `attribution` are
// measured in stage pixels: a rule in them holds at every window size rather than at one.
() => {
  /** @param {Element} e */
  const shown = (e) => {
    if (e.getClientRects().length === 0) {
      return false;
    }
    const style = getComputedStyle(e);
    return style.visibility !== "hidden" && Number(style.opacity) > 0;
  };
  /** @param {Element} e */
  const box = (e) => {
    const r = e.getBoundingClientRect();
    return {
      left: Math.round(r.left * 100) / 100,
      top: Math.round(r.top * 100) / 100,
      right: Math.round(r.right * 100) / 100,
      bottom: Math.round(r.bottom * 100) / 100,
    };
  };
  /** @param {Element} e */
  const name = (e) =>
    e.id ? `#${e.id}` : `${e.tagName.toLowerCase()}.${[...e.classList].join(".")}`;
  const controls = document.getElementById("controls");
  /** @param {Element} e */
  const stageOf = (e) => e.closest("#stage-wrap") ?? e;
  const root = getComputedStyle(document.documentElement);
  /** @param {string} token */
  const token = (token) => root.getPropertyValue(token).trim() || null;
  /** A `#rrggbb` token as the `rgb(...)` a computed colour is reported in. @param {string} v */
  const rgb = (v) => {
    const packed = Number.parseInt(v.slice(1), 16);
    return `rgb(${(packed >> 16) & 255}, ${(packed >> 8) & 255}, ${packed & 255})`;
  };
  // The two colours a badge label is set in: the star's scarlet for `new result`, the label grey
  // for every other (the owner, 2026-09-17). Carried with each layer's labels so that the rule
  // over them is a rule over one layer.
  const badgeColours = {
    starred: rgb(root.getPropertyValue("--scene-proved").trim()),
    label: rgb(root.getPropertyValue("--scene-label").trim()),
  };
  if (controls == null) {
    throw new Error("layout-metrics requires #controls");
  }
  const style = getComputedStyle(controls);
  /** @type {Element[]} */
  const top = [];
  for (const child of controls.children) {
    if (child.id === "panel") {
      top.push(...child.children);
    } else {
      top.push(child);
    }
  }
  const blocks = top.filter(shown).map((e) => ({ name: name(e), ...box(e) }));
  const panels = [...controls.querySelectorAll(".subpanel")]
    .filter(shown)
    .map((e) => ({ name: name(e), ...box(e) }));
  const rows = [...controls.querySelectorAll(".panel-row")].filter(shown).map((row) => ({
    name: name(row),
    ...box(row),
    panels: [...row.children]
      .filter((e) => e.classList.contains("subpanel") && shown(e))
      .map((e) => ({ name: name(e), ...box(e) })),
  }));
  /** @param {Element} e */
  const kind = (e) => {
    if (e instanceof HTMLSelectElement) {
      return "select";
    }
    if (e instanceof HTMLInputElement) {
      return ["number", "text"].includes(e.type) ? `input-${e.type}` : null;
    }
    if (e.closest(".mode-tabs")) {
      return "tab";
    }
    if (e.closest(".seg")) {
      return "segment";
    }
    if (e.closest(".chips")) {
      return "chip";
    }
    return "button";
  };
  /** @param {Element} e */
  const height = (e) => Math.round(e.getBoundingClientRect().height * 100) / 100;
  const found = [
    ...[...controls.querySelectorAll("button, select, input")]
      .filter(shown)
      .map((e) => ({ kind: kind(e), name: name(e), height: height(e) }))
      .filter((c) => c.kind !== null),
    ...[...controls.querySelectorAll(".seg")]
      .filter(shown)
      .map((e) => ({ kind: "segmented", name: name(e), height: height(e) })),
  ];
  const facts = document.getElementById("facts");
  /** @param {string} id */
  const layer = (id) => {
    const root = document.getElementById(id);
    if (root == null) {
      throw new Error(`layout-metrics requires #${id}`);
    }
    return {
      heads: [...root.querySelectorAll(".section-head")].map((e) => e.textContent),
      openItems: root.querySelectorAll(".open-items .open-item").length,
      colours: badgeColours,
      badges: [...root.querySelectorAll(".badges .badge-item")].map((e) => {
        const label = e.querySelector(".label");
        const type = label == null ? null : getComputedStyle(label);
        return {
          icon: e.querySelector("svg")?.getAttribute("class") ?? null,
          text: label?.textContent ?? null,
          family: type?.fontFamily ?? null,
          size: type?.fontSize ?? null,
          weight: type?.fontWeight ?? null,
          color: type?.color ?? null,
        };
      }),
    };
  };
  // The stage, in its own 1920 x 1080 pixels. `--stage-scale` is on the wrapper as a transform,
  // so a client rect divided by it is where the thing is on the poster, whatever the window.
  const stage = document.getElementById("stage");
  const poster = stage === null || !shown(stage) ? null : stage.getBoundingClientRect();
  const scale = stage === null || poster === null ? 1 : poster.width / stage.offsetWidth;
  /** @param {DOMRect} r */
  const staged = (r) => ({
    left: Math.round(((r.left - (poster?.left ?? 0)) / scale) * 100) / 100,
    top: Math.round(((r.top - (poster?.top ?? 0)) / scale) * 100) / 100,
    right: Math.round(((r.right - (poster?.left ?? 0)) / scale) * 100) / 100,
    bottom: Math.round(((r.bottom - (poster?.top ?? 0)) / scale) * 100) / 100,
  });
  /** @param {string} id */
  const frame = (id) => {
    const e = document.getElementById(id);
    if (e == null) {
      throw new Error(`layout-metrics requires #${id}`);
    }
    const style = getComputedStyle(e);
    return {
      shown: shown(e) && style.display !== "none" && style.stroke !== "none",
      stroke: style.stroke,
      strokeWidth: style.strokeWidth,
      locked: e.classList.contains("is-locked"),
    };
  };
  const frames = () => ({
    container: frame("container"),
    box: frame("bound-box"),
    trace: frame("bound-trace"),
    tokens: {
      width: token("--scene-frame-width"),
      frame: rgb(root.getPropertyValue("--scene-frame").trim()),
      locked: rgb(root.getPropertyValue("--scene-frame-locked").trim()),
      trace: rgb(root.getPropertyValue("--scene-trace").trim()),
    },
  });
  // Where the attribution's first character starts and its baseline lands, taken from the laid-out
  // text rather than from the `x` and `y` written into it, beside the legend's left edge and foot
  // they are set from. The legend is null where it is not shown, as in Pack and the studio.
  //
  // The start of the first character is read in the text's own user units, which are stage pixels:
  // the overlay is a 1920 x 1080 box over a 1920 x 1080 viewBox, and `frame` reports that box in
  // stage pixels so a caller can hold the mapping to 1:1 rather than assume it. Not through
  // `getScreenCTM`, which Chromium leaves stale for a frame after the stage's scale changes
  // (measured 2026-09-17: read right after a narrowing it reported the scale before it).
  //
  // The obstacles are what it must not be drawn over -- the numeral, the packing, everything the
  // facts panels actually draw, and the page's own fixed note, which is outside the stage and so
  // maps to stage pixels outside it.
  const attribution = () => {
    const holder = document.getElementById("stage-attribution");
    const text = /** @type {SVGTextElement | null} */ (
      document.querySelector("#stage-attribution-text")
    );
    if (holder == null || text == null) {
      throw new Error("layout-metrics requires #stage-attribution and its text");
    }
    const characters = text.getNumberOfChars();
    let start = null;
    if (characters > 0) {
      const p = text.getStartPositionOfChar(0);
      start = { left: Math.round(p.x * 100) / 100, baseline: Math.round(p.y * 100) / 100 };
    }
    const legend = document.getElementById("stage-note");
    const numeral = document.querySelector("#numeral-static .numeral");
    const type = getComputedStyle(text);
    /** @type {Element[]} */
    const near = [];
    for (const id of ["packing-svg", "facts-a", "facts-b", "stage-note", "pack-stage-facts"]) {
      const held = document.getElementById(id);
      if (held === null || !shown(held)) {
        continue;
      }
      // A facts layer is an empty full-stage box, and the legend a wide one; what each draws is
      // its leaves.
      const leaves = [...held.querySelectorAll("*")].filter((e) => e.children.length === 0);
      near.push(...(id === "packing-svg" ? [held] : leaves));
    }
    if (numeral !== null) {
      near.push(numeral);
    }
    const note = document.getElementById("site-note");
    if (note !== null && shown(note)) {
      near.push(note);
    }
    return {
      placed: holder.classList.contains("is-placed"),
      shown: shown(holder),
      ...(start ?? { left: null, baseline: null }),
      legend: legend === null || !shown(legend) ? null : staged(legend.getBoundingClientRect()),
      ink: staged(text.getBoundingClientRect()),
      frame: staged(holder.getBoundingClientRect()),
      // The same ink box in the page's own pixels, which is what a screenshot is clipped to.
      screen: (() => {
        const r = text.getBoundingClientRect();
        return {
          x: r.left + window.scrollX,
          y: r.top + window.scrollY,
          width: r.width,
          height: r.height,
        };
      })(),
      family: type.fontFamily,
      size: type.fontSize,
      weight: type.fontWeight,
      fill: type.fill,
      obstacles: near
        .filter((e) => shown(e))
        .map((e) => ({ name: name(e), ...staged(e.getBoundingClientRect()) }))
        .filter((b) => b.right - b.left > 0 && b.bottom - b.top > 0),
    };
  };
  return {
    viewport: { width: window.innerWidth, height: window.innerHeight },
    documentWidth: document.documentElement.scrollWidth,
    controls: {
      ...box(controls),
      clientWidth: controls.clientWidth,
      scrollWidth: controls.scrollWidth,
      scrollHeight: controls.scrollHeight,
      clientHeight: controls.clientHeight,
      paddingLeft: parseFloat(style.paddingLeft),
      paddingRight: parseFloat(style.paddingRight),
      borderLeft: parseFloat(style.borderLeftWidth),
    },
    tokens: {
      gutter: token("--layout-gutter"),
      stack: token("--layout-stack-gap"),
      control: token("--control-height"),
      tab: token("--tab-height"),
    },
    blocks,
    panels,
    rows,
    controlsFound: found,
    facts:
      facts == null || getComputedStyle(facts).display === "none" || !shown(stageOf(facts))
        ? null
        : { "facts-a": layer("facts-a"), "facts-b": layer("facts-b") },
    frames: poster === null ? null : frames(),
    attribution: poster === null ? null : attribution(),
  };
};
