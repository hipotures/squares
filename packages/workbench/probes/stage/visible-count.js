// How many squares are actually drawn: on the stage, not transparent, and with a width.
() =>
  Array.from(
    /** @type {NodeListOf<SVGGElement>} */ (document.querySelectorAll("#squares g[data-identity]")),
  ).filter((e) => {
    if (
      e.style.display === "none" ||
      Number(e.getAttribute("opacity") === null ? 1 : e.getAttribute("opacity")) <= 0.01
    ) {
      return false;
    }
    const rect = e.firstElementChild;
    if (rect == null) {
      throw new Error(`square identity ${e.dataset.identity} has no drawn rect`);
    }
    return rect.getBoundingClientRect().width > 0;
  }).length;
