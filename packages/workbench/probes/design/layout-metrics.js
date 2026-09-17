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
  };
};
