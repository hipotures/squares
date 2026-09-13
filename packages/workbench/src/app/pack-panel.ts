import { type PackWorkbenchApi, parsePackSnapshot } from "../api/pack-api.ts";
import type { GeometrySnapshot } from "../core/geometry.ts";
import { assessPackingSnapshot, parseUint32Seed } from "../core/runtime-contracts.ts";
import type { ColourSystem } from "../view/colour.ts";
import { paintPack } from "../view/pack-scene.ts";
import { renderStage, type StageTargets } from "../view/stage-renderer.ts";
import { PackController } from "./pack-controller.ts";

const SVG_NS = "http://www.w3.org/2000/svg";
const MIN_COUNT = 1;
const MAX_COUNT = 400;
const MAX_STEPS_PER_FRAME = 8;
const RESOLVE_ITERATIONS = 100;

export interface PackPanel extends PackWorkbenchApi {
  setVisible(visible: boolean): void;
  visible(): boolean;
  redraw(): void;
}

export interface PackPanelOptions {
  document: Document;
  colours: ColourSystem;
  reducedMotion(): boolean;
  onChange(): void;
}

function element<T extends Element>(
  document: Document,
  id: string,
  type: new (...args: never[]) => T,
): T {
  const found = document.getElementById(id);
  if (!(found instanceof type)) {
    throw new Error(`Pack panel needs #${id}`);
  }
  return found;
}

function cloneSnapshot(snapshot: GeometrySnapshot): GeometrySnapshot {
  return {
    squareSide: snapshot.squareSide,
    container: { ...snapshot.container },
    poses: snapshot.poses.map((pose) => ({ ...pose })),
  };
}

function download(document: Document, name: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** One DOM owner for Pack; the numerical controller and painter remain browser-free. */
export function mountPackPanel(options: PackPanelOptions): PackPanel {
  const { document, colours } = options;
  const root = element(document, "pack-workspace", HTMLElement);
  const status = element(document, "pack-status", HTMLOutputElement);
  const repairStatus = element(document, "pack-repair-status", HTMLOutputElement);
  const stageFacts = element(document, "pack-stage-facts", HTMLElement);
  const count = element(document, "pack-count", HTMLInputElement);
  const seed = element(document, "pack-seed", HTMLInputElement);
  const start = element(document, "pack-start", HTMLSelectElement);
  const shake = element(document, "pack-shake", HTMLInputElement);
  const shakeValue = element(document, "pack-shake-value", HTMLOutputElement);
  const json = element(document, "pack-json", HTMLTextAreaElement);
  const stage = element(document, "stage", HTMLElement);
  const svg = element(document, "packing-svg", SVGSVGElement);
  const world = element(document, "world", SVGGElement);
  const catalogueSquares = element(document, "squares", SVGGElement);
  const packSquares = document.createElementNS(SVG_NS, "g");
  packSquares.id = "pack-squares";
  packSquares.style.display = "none";
  world.append(packSquares);
  const squareNodes = new Map<number, { node: SVGGElement; shape: SVGRectElement }>();
  const targets: StageTargets = {
    svg,
    containerRect: element(document, "container", SVGRectElement),
    squares: squareNodes,
    mark: element(document, "mark", SVGGElement),
    markShape:
      element(document, "mark", SVGGElement).querySelector("rect") ??
      document.createElementNS(SVG_NS, "rect"),
    links: element(document, "links", SVGGElement),
    ghost: element(document, "ghost", SVGGElement),
  };
  const controller = new PackController();
  let active = false;
  let playing = false;
  let frameHandle: number | null = null;
  let generation = 0;
  let lastFrame: number | null = null;
  let focusedIndex = 0;
  let preview: GeometrySnapshot | null = null;
  let drag: {
    index: number;
    x: number;
    y: number;
    pose: GeometrySnapshot["poses"][number];
  } | null = null;

  function nodeFor(index: number): void {
    const identity = index + 1;
    if (squareNodes.has(identity)) {
      return;
    }
    const node = document.createElementNS(SVG_NS, "g");
    node.classList.add("pack-sq");
    node.dataset.packIndex = String(index);
    node.dataset.identity = String(identity);
    node.setAttribute("role", "button");
    const shape = document.createElementNS(SVG_NS, "rect");
    for (const [key, value] of Object.entries({
      x: "-0.5",
      y: "-0.5",
      width: "1",
      height: "1",
      stroke: "#000000",
      "stroke-width": "1.5",
      "stroke-linejoin": "round",
      "vector-effect": "non-scaling-stroke",
    })) {
      shape.setAttribute(key, value);
    }
    node.append(shape);
    packSquares.append(node);
    squareNodes.set(identity, { node, shape });
  }

  function redraw(): void {
    if (!active) {
      return;
    }
    const current = controller.state();
    const snapshot = preview ?? current.snapshot;
    for (const [identity, { node }] of squareNodes) {
      if (identity > snapshot.poses.length) {
        node.remove();
        squareNodes.delete(identity);
      }
    }
    for (let index = 0; index < snapshot.poses.length; index += 1) {
      nodeFor(index);
    }
    renderStage(targets, paintPack(snapshot, colours));
    focusedIndex = Math.min(focusedIndex, snapshot.poses.length - 1);
    for (const [identity, { node }] of squareNodes) {
      const index = identity - 1;
      node.setAttribute("tabindex", index === focusedIndex ? "0" : "-1");
      node.setAttribute(
        "aria-label",
        `Square ${identity} of ${snapshot.poses.length}; Page Up and Page Down select squares, arrow keys move, Q and E rotate`,
      );
    }
    const assessment =
      preview === null ? current.assessment : assessPackingSnapshot(preview, preview.poses.length);
    const valid = assessment.valid && snapshot.squareSide === 1;
    const steps = current.latest?.work.baseSteps ?? 0;
    const score = Number.isFinite(assessment.requiredSide)
      ? assessment.requiredSide.toFixed(6)
      : "unavailable";
    const overlap = Math.max(assessment.maxPairOverlap, assessment.maxWallOverlap);
    const validity = valid
      ? "valid unit packing"
      : snapshot.squareSide !== 1
        ? `not unit squares (side ${snapshot.squareSide.toFixed(4)})`
        : `not a valid packing (overlap ${overlap.toExponential(2)})`;
    status.value = `n = ${current.configuration.n} · seed ${current.configuration.seed} · ${steps} steps · required side ${score} · ${validity} · ${preview === null ? (playing ? "running" : "paused") : "drag preview"}`;
    const repair = current.repair;
    repairStatus.value =
      repair === null
        ? ""
        : `Resolve ${repair.termination.reason}: raw side ${repair.raw.requiredSide.toFixed(6)}, repaired side ${repair.repaired?.requiredSide.toFixed(6) ?? "unavailable"}; ${repair.termination.resolved ? "checked repair shown" : "raw arrangement retained"}`;
    stageFacts.textContent = `n = ${current.configuration.n}\nRequired side ${score}\n${valid ? "Valid unit packing" : `Overlap ${overlap.toExponential(2)}`}\n${steps} steps · ${preview === null ? (playing ? "running" : "paused") : "drag preview"}`;
    element(document, "stage-accessible-description", HTMLElement).textContent = status.value;
    svg.setAttribute("aria-label", `${current.configuration.n} packing squares`);
  }

  function pause(): void {
    playing = false;
    generation += 1;
    lastFrame = null;
    if (frameHandle !== null) {
      cancelAnimationFrame(frameHandle);
      frameHandle = null;
    }
    redraw();
  }

  function tick(timestamp: number, expectedGeneration: number): void {
    if (!active || !playing || expectedGeneration !== generation) {
      return;
    }
    const elapsed =
      lastFrame === null ? 1 / 60 : Math.max(0, Math.min(0.1, (timestamp - lastFrame) / 1000));
    lastFrame = timestamp;
    const wanted = Math.max(
      1,
      Math.round(elapsed * controller.state().configuration.physics.stepsPerSecond),
    );
    try {
      controller.step(Math.min(MAX_STEPS_PER_FRAME, wanted));
      redraw();
    } catch (error) {
      pause();
      status.value = error instanceof Error ? error.message : String(error);
      return;
    }
    frameHandle = requestAnimationFrame((next) => tick(next, expectedGeneration));
  }

  function play(): void {
    if (!active || playing) {
      return;
    }
    if (options.reducedMotion()) {
      controller.step(1);
      redraw();
      return;
    }
    playing = true;
    generation += 1;
    frameHandle = requestAnimationFrame((timestamp) => tick(timestamp, generation));
    redraw();
  }

  function point(event: PointerEvent): { x: number; y: number } | null {
    const matrix = world.getScreenCTM();
    if (matrix === null) {
      return null;
    }
    const transformed = new DOMPoint(event.clientX, event.clientY).matrixTransform(
      matrix.inverse(),
    );
    return { x: transformed.x, y: transformed.y };
  }

  function commitPreview(): void {
    if (preview === null) {
      return;
    }
    controller.load(preview);
    start.value = "given";
    preview = null;
    redraw();
  }

  const panel: PackPanel = {
    setVisible(visible) {
      if (active === visible) {
        return;
      }
      if (!visible) {
        pause();
        preview = null;
        drag = null;
      }
      active = visible;
      root.hidden = !visible;
      stageFacts.hidden = !visible;
      catalogueSquares.style.display = visible ? "none" : "";
      packSquares.style.display = visible ? "" : "none";
      document.body.classList.toggle("pack-independent", visible);
      if (visible) {
        redraw();
      }
      options.onChange();
    },
    visible: () => active,
    playing: () => playing,
    play,
    pause,
    configure(settings) {
      if (settings.n !== undefined && (settings.n < MIN_COUNT || settings.n > MAX_COUNT)) {
        throw new RangeError(`Pack count must be ${MIN_COUNT}–${MAX_COUNT}`);
      }
      pause();
      const next = controller.configure(settings);
      count.value = String(next.configuration.n);
      seed.value = String(next.configuration.seed);
      start.value = next.configuration.startKind;
      shake.value = String(
        Math.max(0, Math.min(10, Math.round(next.configuration.anneal.amplitude * 3))),
      );
      shakeValue.value = shake.value;
      redraw();
      return next;
    },
    step(count) {
      pause();
      controller.step(count);
      redraw();
      return controller.state();
    },
    restart() {
      pause();
      controller.restart();
      redraw();
      return controller.state();
    },
    resolve() {
      pause();
      const receipt = controller.resolve(RESOLVE_ITERATIONS);
      if (receipt.termination.resolved) {
        start.value = "given";
      }
      redraw();
      return receipt;
    },
    load(text) {
      const value: unknown = JSON.parse(text);
      const snapshot = parsePackSnapshot(value);
      if (snapshot.poses.length > MAX_COUNT) {
        throw new RangeError(`Pack supports at most ${MAX_COUNT} squares in this browser`);
      }
      pause();
      controller.load(snapshot);
      start.value = "given";
      count.value = String(snapshot.poses.length);
      redraw();
      return controller.state();
    },
    state: () => controller.state(),
    exportSnapshot: () => controller.export(),
    redraw,
  };

  function guarded(action: () => void): void {
    try {
      action();
    } catch (error) {
      status.value = error instanceof Error ? error.message : String(error);
    }
  }

  element(document, "pack-run", HTMLButtonElement).addEventListener("click", () => panel.play());
  element(document, "pack-pause", HTMLButtonElement).addEventListener("click", () => panel.pause());
  element(document, "pack-restart", HTMLButtonElement).addEventListener("click", () =>
    panel.restart(),
  );
  element(document, "pack-resolve", HTMLButtonElement).addEventListener("click", () =>
    guarded(() => {
      panel.resolve();
    }),
  );
  element(document, "pack-apply", HTMLButtonElement).addEventListener("click", () =>
    guarded(() => {
      const n = Number(count.value);
      const requestedSeed = seed.value.trim() === "" ? null : parseUint32Seed(Number(seed.value));
      if (!Number.isSafeInteger(n) || n < MIN_COUNT || n > MAX_COUNT) {
        throw new RangeError(`Pack count must be ${MIN_COUNT}–${MAX_COUNT}`);
      }
      if (requestedSeed === null) {
        throw new RangeError("Pack seed must be an unsigned 32-bit integer");
      }
      if (start.value !== "grid" && start.value !== "random") {
        throw new RangeError("select a supported Pack start");
      }
      pause();
      controller.configure({
        n,
        seed: requestedSeed,
        startKind: start.value,
        anneal: { amplitude: Number(shake.value) / 3 },
      });
      redraw();
    }),
  );
  element(document, "pack-reset", HTMLButtonElement).addEventListener("click", () => {
    pause();
    count.value = "17";
    seed.value = "1";
    start.value = "grid";
    shake.value = "3";
    shakeValue.value = "3";
    controller.configure({ n: 17, seed: 1, startKind: "grid", anneal: { amplitude: 1 } });
    redraw();
  });
  shake.addEventListener("input", () => {
    shakeValue.value = shake.value;
  });
  element(document, "pack-load", HTMLButtonElement).addEventListener("click", () =>
    guarded(() => {
      panel.load(json.value);
    }),
  );
  element(document, "pack-export", HTMLButtonElement).addEventListener("click", () =>
    guarded(() => {
      download(
        document,
        `packing-n${controller.state().configuration.n}.json`,
        JSON.stringify(controller.export(), null, 2),
      );
    }),
  );

  packSquares.addEventListener("pointerdown", (event) => {
    if (!active || !(event.target instanceof Element)) {
      return;
    }
    const square = event.target.closest("g[data-pack-index]");
    const index = Number(square?.getAttribute("data-pack-index"));
    const at = point(event);
    const pose = controller.state().snapshot.poses[index];
    if (square === null || at === null || pose === undefined) {
      return;
    }
    event.preventDefault();
    pause();
    focusedIndex = index;
    drag = { index, x: at.x, y: at.y, pose: { ...pose } };
    preview = cloneSnapshot(controller.export());
    packSquares.setPointerCapture(event.pointerId);
    event.stopPropagation();
    redraw();
  });
  packSquares.addEventListener("pointermove", (event) => {
    if (drag === null || preview === null) {
      return;
    }
    const at = point(event);
    const pose = preview.poses[drag.index];
    if (at === null || pose === undefined) {
      return;
    }
    if (event.shiftKey) {
      pose.angle = drag.pose.angle + (at.x - drag.x) * 0.03;
    } else {
      pose.x = drag.pose.x + at.x - drag.x;
      pose.y = drag.pose.y + at.y - drag.y;
    }
    redraw();
  });
  packSquares.addEventListener("pointerup", (event) => {
    if (drag === null) {
      return;
    }
    if (packSquares.hasPointerCapture(event.pointerId)) {
      packSquares.releasePointerCapture(event.pointerId);
    }
    drag = null;
    guarded(commitPreview);
  });
  packSquares.addEventListener("pointercancel", () => {
    preview = null;
    drag = null;
    redraw();
  });
  packSquares.addEventListener("keydown", (event) => {
    if (!(event.target instanceof Element)) {
      return;
    }
    const square = event.target.closest("g[data-pack-index]");
    const index = Number(square?.getAttribute("data-pack-index"));
    if (square === null || !Number.isSafeInteger(index)) {
      return;
    }
    const stride = event.shiftKey ? 0.25 : 0.05;
    const snapshot = cloneSnapshot(controller.export());
    const pose = snapshot.poses[index];
    if (pose === undefined) {
      return;
    }
    switch (event.key) {
      case "ArrowLeft":
        pose.x -= stride;
        break;
      case "ArrowRight":
        pose.x += stride;
        break;
      case "ArrowUp":
        pose.y += stride;
        break;
      case "ArrowDown":
        pose.y -= stride;
        break;
      case "q":
        pose.angle -= Math.PI / 36;
        break;
      case "e":
        pose.angle += Math.PI / 36;
        break;
      case "PageDown":
      case "]":
        event.preventDefault();
        event.stopPropagation();
        focusedIndex = (index + 1) % snapshot.poses.length;
        redraw();
        squareNodes.get(focusedIndex + 1)?.node.focus();
        return;
      case "PageUp":
      case "[":
        event.preventDefault();
        event.stopPropagation();
        focusedIndex = (index + snapshot.poses.length - 1) % snapshot.poses.length;
        redraw();
        squareNodes.get(focusedIndex + 1)?.node.focus();
        return;
      case "Escape":
        stage.focus();
        event.stopPropagation();
        return;
      default:
        return;
    }
    event.preventDefault();
    event.stopPropagation();
    pause();
    focusedIndex = index;
    controller.load(snapshot);
    start.value = "given";
    redraw();
  });
  stage.addEventListener(
    "keydown",
    (event) => {
      if (!active || event.target !== stage) {
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        event.stopPropagation();
        squareNodes.get(focusedIndex + 1)?.node.focus();
      } else if (event.key === " ") {
        event.preventDefault();
        event.stopPropagation();
        if (playing) {
          pause();
        } else {
          play();
        }
      }
    },
    { capture: true },
  );
  return panel;
}
