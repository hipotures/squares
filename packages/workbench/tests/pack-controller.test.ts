import assert from "node:assert/strict";
import { test } from "node:test";
import { parsePackSnapshot } from "../src/api/pack-api.ts";
import { PackController } from "../src/app/pack-controller.ts";
import { createGridPackStart } from "../src/simulation/pack.ts";
import { createColourSystem } from "../src/view/colour.ts";
import { paintPack } from "../src/view/pack-scene.ts";
import { sceneSvg } from "../src/view/stage-renderer.ts";

test("independent Pack supports count 1, off-catalogue 17, and 325", () => {
  for (const n of [1, 17, 325]) {
    const controller = new PackController({ n, seed: 0 });
    const initial = controller.state();
    assert.equal(initial.snapshot.poses.length, n);
    assert.equal(initial.assessment.valid, true);
    const receipt = controller.step(1);
    assert.equal(receipt.configuration.n, n);
    assert.equal(receipt.configuration.reference, null);
    assert.equal(receipt.configuration.guided, false);
    assert.equal(receipt.configuration.effectiveSeed, 0);
  }
});

test("exact seeds and restart reproduce a random run independently of batching", () => {
  const controller = new PackController({ n: 17, seed: 4294967295, startKind: "random" });
  const initial = controller.export();
  const first = controller.step(12);
  controller.restart();
  assert.deepEqual(controller.export(), initial);
  controller.step(3);
  assert.deepEqual(controller.step(9), first);
  const before = controller.state();
  assert.throws(() => controller.configure({ seed: 4294967296 }));
  assert.deepEqual(controller.state(), before);
  assert.throws(() => controller.configure({ n: 0 }));
  assert.deepEqual(controller.state(), before);
});

test("snapshot import/export isolates ownership and invalid input is transactional", () => {
  const controller = new PackController();
  const snapshot = createGridPackStart(5);
  controller.load(parsePackSnapshot(JSON.parse(JSON.stringify(snapshot))));
  snapshot.container.side = 100;
  assert.equal(controller.state().configuration.startKind, "given");
  assert.equal(controller.export().container.side, 3);
  const state = controller.state();
  state.configuration.physics.jiggle = 999;
  state.snapshot.container.side = 200;
  assert.equal(controller.state().configuration.physics.jiggle, 20);
  assert.equal(controller.export().container.side, 3);
  assert.throws(() => controller.load({ ...snapshot, squareSide: Number.NaN }));
  assert.equal(controller.export().container.side, 3);
  assert.throws(() => parsePackSnapshot({ ...snapshot, poses: [{ x: "1", y: 1, angle: 0 }] }));
});

test("successful Resolve retains raw evidence and begins a fresh repaired phase", () => {
  const controller = new PackController({ n: 2, physics: { jiggle: 0, jiggleTorque: 0 } });
  const overlapping = {
    ...createGridPackStart(2),
    poses: [
      { x: 0.5, y: 0.5, angle: 0 },
      { x: 0.5, y: 0.5, angle: 0 },
    ],
  };
  controller.load(overlapping);
  const repair = controller.resolve();
  assert.equal(repair.raw.valid, false);
  assert.equal(repair.termination.resolved, true);
  assert.deepEqual(controller.export(), repair.repaired?.snapshot);
  assert.deepEqual(controller.state().repair, repair);
  assert.equal(controller.state().latest, null);
  assert.equal(controller.state().configuration.startKind, "given");
  assert.equal(controller.step(1).work.baseSteps, 1);
  assert.equal(controller.state().repair, null);
});

test("failed Resolve does not replace raw state", () => {
  const controller = new PackController({ n: 17, startKind: "random", seed: 7 });
  const before = controller.export();
  const repair = controller.resolve(1);
  assert.equal(repair.termination.resolved, false);
  assert.deepEqual(controller.export(), before);
  assert.deepEqual(repair.raw.snapshot, before);
});

test("Pack scene normalizes nonzero origins without altering numerical geometry", () => {
  const colours = createColourSystem({
    palette: ["#123456", "#234567", "#345678"],
    shades: ["#123456", "#234567", "#345678"].map((colour) =>
      Array.from({ length: 5 }, () => colour),
    ),
    angleToleranceDegrees: 0.5,
  });
  const snapshot = {
    squareSide: 0.5,
    container: { originX: 8, originY: -4, side: 2 },
    poses: [{ x: 9, y: -3, angle: Math.PI / 4 }],
  };
  const painted = paintPack(snapshot, colours);
  assert.equal(painted.scene.motion, "packing-snapshot");
  assert.deepEqual(painted.scene.squares[0], {
    index: 0,
    identity: 1,
    x: 1,
    y: 1,
    angleDegrees: 45,
    opacity: 1,
    scale: 0.5,
  });
  assert.equal(snapshot.poses[0]?.x, 9);
  assert.match(sceneSvg(painted), /svg/);
});
