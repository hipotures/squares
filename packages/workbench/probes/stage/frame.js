// The whole drawn frame: every square's transform, and the container it sits in.
() => {
  const container = document.getElementById("container");
  if (container == null) {
    throw new Error("probe requires #container");
  }
  return {
    squares: Array.from(
      /** @type {NodeListOf<SVGGElement>} */ (
        document.querySelectorAll("#squares g[data-identity]")
      ),
    )
      .filter((e) => e.style.display !== "none")
      .map((e) => `${e.dataset.identity}@${e.getAttribute("transform")}`),
    box: container.getAttribute("width"),
  };
};
