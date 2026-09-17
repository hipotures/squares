// Scroll the controls to their top or their end, and say whether they scroll at all.
/** @param {{to: "top" | "end"}} o */
(o) => {
  const controls = document.getElementById("controls");
  if (controls == null) {
    throw new Error("scroll-controls requires #controls");
  }
  controls.scrollTop = o.to === "end" ? controls.scrollHeight : 0;
  return {
    scrolls: controls.scrollHeight > controls.clientHeight + 1,
    scrollTop: controls.scrollTop,
  };
};
