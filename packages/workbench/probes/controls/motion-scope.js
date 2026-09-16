// The UI must never offer an enabled kinetics control when the current strategy does not run it.
() => {
  const api = window.atlasTransitions;
  const before = api.state();
  const pairs = api.pairs();
  const moving = pairs.find((pair) => pair.kind !== "prefix" && pair.kind !== "shared-picture");
  const still = pairs.find((pair) => pair.kind === "prefix" || pair.kind === "shared-picture");
  if (moving === undefined || still === undefined) {
    throw new Error("probe requires one moving and one static transition");
  }
  const read = () => ({
    note: document.getElementById("motion-scope-note")?.textContent ?? "",
    advancedHidden:
      window.getComputedStyle(document.getElementById("motion-advanced-box")).display === "none",
    containerDelayDisabled: /** @type {HTMLInputElement | null} */ (
      document.getElementById("motion-container-delay")
    )?.disabled,
    groups: Array.from(document.querySelectorAll('[data-motion-control="physics"]')).map(
      (host) => ({
        id: host.id,
        inert: host.classList.contains("is-inert"),
        aria: host.getAttribute("aria-disabled"),
        disabled: Array.from(host.querySelectorAll("button, input, select")).every(
          (control) =>
            /** @type {HTMLButtonElement | HTMLInputElement | HTMLSelectElement} */ (control)
              .disabled,
        ),
      }),
    ),
  });

  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setStyle("tween");
  const tween = read();
  api.setStyle("physics");
  const physics = read();
  api.setStepN(still.n + 1);
  const staticStep = read();
  api.setMode("pack");
  const pack = read();
  api.setMode("animate");
  api.setStepN(moving.n + 1);
  api.setStyle("physics");
  api.setMode("search");
  const search = read();

  api.setMode("animate");
  api.setStepN(before.n + 1);
  api.setStyle(before.style);
  api.setMode(before.aspect);
  return { tween, physics, staticStep, pack, search };
};
