import assert from "node:assert/strict";
import { test } from "node:test";
import { createBrowserSearchPlan, parseBrowserSearchSeeds } from "../src/api/search-api.ts";
import { decodeSearchOutcomes, encodeSearchOutcomes } from "../src/search/outcomes.ts";
import { createPackSearchRunner } from "../src/search/pack-runner.ts";
import { runSearchPlan } from "../src/search/scheduler.ts";

test("browser search plans are deterministic and runnable without corpus", async () => {
  const inputs = { n: 2, seeds: [3, 4], physicsSteps: 2, proposal: "grid", repair: false } as const;
  const plan = createBrowserSearchPlan(inputs);
  assert.deepEqual(plan, createBrowserSearchPlan(inputs));
  assert.equal(plan.cohorts[0]?.partition, "exploratory");
  const ledger = await runSearchPlan(plan, createPackSearchRunner({ batchSteps: 1 }));
  assert.deepEqual(
    ledger.outcomes.map((outcome) => outcome.status),
    ["completed", "completed"],
  );
  assert.deepEqual(decodeSearchOutcomes(JSON.parse(encodeSearchOutcomes(ledger)), plan), ledger);
  assert.throws(
    () =>
      decodeSearchOutcomes(
        JSON.parse(encodeSearchOutcomes(ledger)),
        createBrowserSearchPlan({ ...inputs, physicsSteps: 3 }),
      ),
    /plan/i,
  );
});

test("browser search rejects excessive work and ambiguous seed lists", () => {
  assert.deepEqual(parseBrowserSearchSeeds("0, 17,4294967295"), [0, 17, 4294967295]);
  assert.throws(() => parseBrowserSearchSeeds("1,,2"), /empty/);
  assert.throws(() => parseBrowserSearchSeeds("1,1.5"), /unsigned integer/);
  const baseline = { n: 2, seeds: [1], physicsSteps: 2, proposal: "grid", repair: false } as const;
  assert.throws(() => createBrowserSearchPlan({ ...baseline, n: 33 }), /1 to 32/);
  assert.throws(() => createBrowserSearchPlan({ ...baseline, physicsSteps: 5001 }), /5000/);
  assert.throws(() => createBrowserSearchPlan({ ...baseline, seeds: [1, 1] }), /unique/);
});
