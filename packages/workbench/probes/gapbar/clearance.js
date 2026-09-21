// The room the gap bar and the headline have on the stage, in the stage's own units.
// The headline heads the facts column now (the owner, 2026-09-21), so what has to hold is that
// it sits above the bar, inside the column, and clear of the picture beside it -- not that it
// hangs below the packing, which is where it used to be.
() => {
  /** @param {string} id */
  const element = (id) => {
    const found = document.getElementById(id);
    if (found == null) {
      throw new Error(`probe requires #${id}`);
    }
    return found;
  };
  const s = element("stage").getBoundingClientRect();
  const k = s.width / 1920;
  const gapbar = element("gapbar");
  const b = gapbar.getBoundingClientRect();
  const e = element("headline").getBoundingClientRect();
  // The DRAWN container, not the svg element: the element's box carries the view's own
  // padding, so the picture ends well above it and a clearance measured to the element
  // would refuse a headline that is nowhere near the packing.
  const pk = element("container").getBoundingClientRect();
  const f = element("facts").getBoundingClientRect();
  return {
    bottom: (b.bottom - s.top) / k,
    top: (b.top - s.top) / k,
    headTop: (e.top - s.top) / k,
    headBottom: (e.bottom - s.top) / k,
    headLeft: (e.left - s.left) / k,
    headRight: (e.right - s.left) / k,
    packRight: (pk.right - s.left) / k,
    packBottom: (pk.bottom - s.top) / k,
    panelLeft: (f.left - s.left) / k,
    stageBottom: s.height / k,
    right: (b.right - s.left) / k,
    panelRight: (f.right - s.left) / k,
    shown: getComputedStyle(gapbar).display !== "none",
  };
};
