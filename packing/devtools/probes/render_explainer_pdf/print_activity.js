// Watch the document across one `page.pdf()` call, so a draw that could not be reproduced
// can say what was moving under it.
//
// `page.emulate_media(media="print")` does not fire the page's print hooks: `beforeprint`
// and `afterprint` only run when a print actually begins. The certificate figure's script
// answers both by re-running `boot()`, which hands every readout back to
// `squaresMath.render`, and those renders are asynchronous. So math re-renders while
// Chromium lays the printed pages out, on every print and not only the first.
//
// `render_explainer_pdf._PRINT_ACTIVITY` has the measurement and what it costs. Recorded
// rather than prevented: nothing here can stop the page's own handlers, so this is
// diagnosis, and `_draw_reproduced` is what decides whether a draw is kept.
//
// Two blind spots, stated because these records are quoted in a refusal. Style rules changed
// through the CSSOM on an existing sheet are not mutations and are not seen here; and a face
// that began loading before the watch was installed contributes only its `loadingdone`,
// which is why the font status at installation is reported beside the records.
/** @returns {SquaresPrintActivity} */
() => {
  /** @type {SquaresPrintActivityRecord[]} */
  const records = [];
  const start = performance.now();
  const limit = 24;
  const state = {
    records,
    limit,
    truncated: false,
    status: document.fonts.status,
    /** @param {MutationRecord} mutation */
    note: (mutation) => {
      add(mutation.type, describe(mutation.target), mutation.attributeName ?? "");
    },
    stop: () => {
      for (const mutation of observer.takeRecords()) {
        state.note(mutation);
      }
      observer.disconnect();
      document.fonts.removeEventListener("loading", onLoading);
      document.fonts.removeEventListener("loadingdone", onLoadingDone);
      document.fonts.removeEventListener("loadingerror", onLoadingError);
    },
  };

  /**
   * Where a change landed, as a short ancestor path a log can carry.
   * @param {Node} node
   */
  function describe(node) {
    /** @type {string[]} */
    const parts = [];
    let here = node instanceof Element ? node : node.parentElement;
    while (here !== null && parts.length < 3) {
      const classes = (here.getAttribute("class") ?? "").split(/\s+/).filter(Boolean).slice(0, 2);
      parts.unshift(here.tagName.toLowerCase() + classes.map((name) => `.${name}`).join(""));
      here = here.parentElement;
    }
    return parts.join(">");
  }

  /**
   * @param {string} kind
   * @param {string} where
   * @param {string} detail
   */
  function add(kind, where, detail) {
    if (records.length >= limit) {
      state.truncated = true;
      return;
    }
    records.push({ at_ms: performance.now() - start, kind, where, detail });
  }

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      state.note(mutation);
    }
  });
  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    attributes: true,
    characterData: true,
  });

  const onLoading = () => add("fonts", "document.fonts", "a face began loading");
  /** @param {FontFaceSetLoadEvent} event */
  const onLoadingDone = (event) =>
    add("fonts", "document.fonts", `${event.fontfaces.length} faces finished loading`);
  const onLoadingError = () => add("fonts", "document.fonts", "a face failed to load");
  document.fonts.addEventListener("loading", onLoading);
  document.fonts.addEventListener("loadingdone", onLoadingDone);
  document.fonts.addEventListener("loadingerror", onLoadingError);

  return state;
};
