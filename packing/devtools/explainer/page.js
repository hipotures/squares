/* ---------- shared: certificate picker and queued static math ---------- */
(() => {
  /* SVG font sizes use viewBox units. Compensate for the drawing scale so
     labels have the same on-page size as captions, including during print. */
  const diagrams = [...document.querySelectorAll(".line-fig svg, .chart svg")].map(
    (svg) => /** @type {SVGSVGElement} */ (svg),
  );
  function sizeDiagramLabels() {
    for (const svg of diagrams) {
      if (!svg.getBoundingClientRect().width) {
        continue;
      }
      const matrix = svg.getScreenCTM();
      const scale = matrix && Math.hypot(matrix.c, matrix.d);
      if (!scale) {
        continue;
      }
      const size = parseFloat(getComputedStyle(svg.parentElement).fontSize) / scale;
      svg.style.setProperty("--paper-diagram-font-size", `${size}px`);
    }
  }
  const diagramObserver = new ResizeObserver(sizeDiagramLabels);
  diagrams.forEach((svg) => {
    diagramObserver.observe(svg);
  });
  window.addEventListener("beforeprint", sizeDiagramLabels);
  window.addEventListener("afterprint", sizeDiagramLabels);
  window.matchMedia("print").addEventListener("change", sizeDiagramLabels);
  void document.fonts.ready.then(sizeDiagramLabels);
  sizeDiagramLabels();
  const render = squaresMath.render;
  async function typeset() {
    // DOM state chooses the priority without measuring every formula's layout.
    // Keep document order within active panels, the visible paper, and hidden copies.
    const groups = [[], [], []];
    const nodes = [...document.querySelectorAll(".tex, .tex-d, .kpress-math")].map(
      (node) => /** @type {HTMLElement} */ (node),
    );
    for (const el of nodes) {
      el.dataset.squaresMathQueued = "true";
      const priority = el.closest(".cert-figure[hidden]") ? 2 : el.closest(".panel") ? 0 : 1;
      groups[priority].push(async () => {
        try {
          if (!el.classList.contains("kpress-math")) {
            if (el.dataset.done) {
              return;
            }
            const source = el.dataset.kpressMathSource ?? el.textContent;
            await render(el, source, el.classList.contains("tex-d"));
            el.dataset.done = "1";
            return;
          }
          // Native math keeps MathML available if the required font fails.
          const box = /** @type {HTMLElement | null} */ (el.querySelector(".kpress-math-render"));
          if (!box || box.dataset.done) {
            return;
          }
          const src =
            box.dataset.kpressMathSource ??
            box.textContent
              .trim()
              .replace(/^\\[([]/, "")
              .replace(/\\[)\]]$/, "");
          await render(box, src, el.dataset.kpressMath === "display").then((rendered) => {
            box.dataset.done = "1";
            if (rendered) {
              el.dataset.kpressMathRendered = "true";
            } else {
              delete el.dataset.kpressMathRendered;
            }
          });
        } finally {
          delete el.dataset.squaresMathQueued;
        }
      });
    }
    try {
      await squaresMath.batch(groups.flat());
    } finally {
      // A producer failure releases unsubmitted fallbacks too. Issued renders
      // retain KPress's own visibility gate until their required fonts settle.
      for (const el of nodes) {
        delete el.dataset.squaresMathQueued;
      }
    }
    await squaresMath.settled();
    kpressMathText.complete();
    document.documentElement.classList.add("math-ready");

    /* Footnote hover previews, kpress's own, bundled into this page. Booted after
       the static math so the preview clones already carry rendered formulas. */
    if (window.kpressInitTooltips) {
      window.kpressInitTooltips(document, { only: "footnote" });
    }
    if (window.kpressInitCodeCopy) {
      window.kpressInitCodeCopy(document);
    }
  }
  /* One copy of each figure per certificate. The switch beside every figure
     shows one certificate's copies and records it in the hash, so a link can
     open the page on either; the figure the reader switched from stays where
     it was on screen. */
  const switches = [...document.querySelectorAll(".cert-toggle button")].map(
    (button) => /** @type {HTMLButtonElement} */ (button),
  );
  const articles = [...document.querySelectorAll(".cert-figure")].map(
    (article) => /** @type {HTMLElement} */ (article),
  );
  const slugs = [...new Set(articles.map((a) => a.dataset.cert))];
  const scroller = document.querySelector("[data-kpress-viewport]") || document.scrollingElement;
  const figureKey = (el) => {
    const f = /** @type {HTMLElement | null} */ (el.closest("figure"));
    return f ? f.dataset.figure || null : null;
  };
  function show(slug, record, from) {
    if (!slugs.includes(slug)) {
      slug = slugs[0];
    }
    const restoreFocus = from && document.activeElement === from;
    const key = from ? figureKey(from) : null,
      top = from ? from.getBoundingClientRect().top : 0;
    for (const a of articles) {
      const on = a.dataset.cert === slug;
      if (on && a.hidden) {
        a.hidden = false;
        a.classList.remove("swap");
        void a.offsetWidth;
        a.classList.add("swap");
      } else {
        a.hidden = !on;
      }
    }
    for (const b of switches) {
      b.setAttribute("aria-pressed", String(b.dataset.cert === slug));
    }
    document.dispatchEvent(new Event("squares:certificatechange"));
    if (key) {
      const twin = [...document.querySelectorAll(".cert-figure:not([hidden]) figure")].find(
        (f) => figureKey(/** @type {HTMLElement} */ (f)) === key,
      );
      const button = /** @type {HTMLButtonElement | null | undefined} */ (
        twin?.querySelector('.cert-toggle button[aria-pressed="true"]')
      );
      if (button) {
        if (restoreFocus) {
          button.focus({ preventScroll: true });
        }
        scroller.scrollBy(0, button.getBoundingClientRect().top - top);
      }
    }
    if (record && location.hash !== `#${slug}`) {
      history.replaceState(null, "", `#${slug}`);
    }
  }
  switches.forEach((b) => {
    b.addEventListener("click", () => show(b.dataset.cert, true, b));
  });
  /* Only a hash naming a certificate switches the page. A footnote jump sets
     the hash too (#fn-3, #fnref-3), and it leaves the selection alone. */
  window.addEventListener("hashchange", () => {
    const slug = location.hash.slice(1);
    if (slugs.includes(slug)) {
      show(slug, false);
    }
  });
  show(location.hash.slice(1), false);
  /* PDF and layout tools wait for math-ready, which follows the complete queue
     and the initial readouts submitted by the later certificate boot scripts. */
  void typeset();
})();
