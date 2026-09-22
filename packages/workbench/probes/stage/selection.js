// The page's text selection as a string, and, with o.clear, the selection removed afterwards so
// a failed check leaves nothing selected for the sections after it.
/** @param {{clear?: boolean} | null} o */
(o) => {
  const selection = window.getSelection();
  const text = selection === null ? "" : selection.toString();
  if (o?.clear === true) {
    selection?.removeAllRanges();
  }
  return text;
};
