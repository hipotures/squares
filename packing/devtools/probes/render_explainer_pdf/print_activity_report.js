// Close the watch `render_explainer_pdf/print_activity` installed and say what changed while
// the print it spanned was in flight. `quiet` is a description, not a verdict: this page's
// print handlers mutate it on every print, so a draw is judged by whether it can be drawn
// again, not by this. Records are capped by the watch, and `truncated` says whether a short
// list is a complete one.
/** @param {{ watch: SquaresPrintActivity }} o */
({ watch }) => {
  watch.stop();
  return {
    quiet: watch.records.length === 0 && watch.status === "loaded",
    font_status_when_installed: watch.status,
    changes: watch.records.length,
    truncated: watch.truncated,
    records: watch.records,
  };
};
