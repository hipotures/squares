import assert from "node:assert/strict";
import { test } from "node:test";
import type {
  JsonObject,
  SearchPlan,
  SearchSlot,
  SearchTrialControl,
  SearchTrialValue,
} from "../src/search/contracts.ts";
import {
  decodeSearchOutcomes,
  encodeSearchOutcomes,
  statusCounts,
} from "../src/search/outcomes.ts";
import { decodeSearchPlan } from "../src/search/registry.ts";
import { runSearchPlan } from "../src/search/scheduler.ts";
import { summarizeSearch } from "../src/search/summary.ts";

function required<T>(value: T | undefined): T {
  assert.notEqual(value, undefined);
  if (value === undefined) {
    throw new Error("missing test fixture");
  }
  return value;
}

function plan(seeds: number[] = [0, 1, 2, 3, 4]): SearchPlan {
  return decodeSearchPlan({
    contract: "packing.squares:SearchPlan/v1",
    id: "scheduler-control",
    source: { commit: "abc123", dirty: false, runtime: "node-test", engine: "pack/v1" },
    configurations: [
      {
        id: "control",
        configuration: {
          mode: "blind",
          objective: { kind: "absolute-side", state: "best-observed", require_stationary: false },
        },
      },
    ],
    cohorts: [
      {
        id: "tuning-control",
        configuration_id: "control",
        partition: "tuning",
        n: 1,
        seeds,
        block_size: 2,
        work_budget: {
          proposal_attempts: 1,
          physics_steps: 4,
          repair_iterations: 0,
        },
        timeout_ms: 5,
      },
      {
        id: "held-out-control",
        configuration_id: "control",
        partition: "held-out",
        n: 1,
        seeds: [100],
        block_size: 1,
        work_budget: {
          proposal_attempts: 1,
          physics_steps: 4,
          repair_iterations: 0,
        },
      },
    ],
  });
}

function completed(configuration: JsonObject): SearchTrialValue {
  const state = {
    snapshot: {
      squareSide: 1,
      container: { originX: 0, originY: 0, side: 1 },
      poses: [{ x: 0.5, y: 0.5, angle: 0 }],
    },
    valid: true,
    validityReason: null,
    absoluteSide: 1,
  } as const;
  return {
    raw: state,
    repaired: null,
    bestObserved: state,
    selectedState: "best-observed",
    stationarity: {
      stationary: true,
      stationarySteps: 1,
      window: 1,
      residual: { maxLinearSpeed: 0, maxAngularSpeed: 0 },
      forcingScale: 0,
      thresholds: { linearSpeed: 0, angularSpeed: 0, forcingScale: 0 },
    },
    repair: {
      termination: "not-requested",
      resolved: false,
      exhausted: false,
      tolerance: null,
      iterationLimit: 0,
    },
    objective: 1,
    work: {
      proposalAttempts: 1,
      physicsSteps: 4,
      repairIterations: 0,
      pairCandidates: 0,
      pairForces: 0,
      wallForces: 0,
      repairPairTests: 0,
      repairPairTranslations: 0,
      repairFitTranslations: 0,
    },
    configuration,
  };
}

test("the registry derives ordered disjoint blocks without pooling held-out slots", () => {
  const decoded = plan();
  assert.deepEqual(
    decoded.slots.map(({ partition, seed, block, positionInBlock }) => ({
      partition,
      seed,
      block,
      positionInBlock,
    })),
    [
      { partition: "tuning", seed: 0, block: 0, positionInBlock: 0 },
      { partition: "tuning", seed: 1, block: 0, positionInBlock: 1 },
      { partition: "tuning", seed: 2, block: 1, positionInBlock: 0 },
      { partition: "tuning", seed: 3, block: 1, positionInBlock: 1 },
      { partition: "tuning", seed: 4, block: 2, positionInBlock: 0 },
      { partition: "held-out", seed: 100, block: 0, positionInBlock: 0 },
    ],
  );
});

test("the scheduler retains completed, failed, timeout, cancellation and pending slots", async () => {
  let clock = 0;
  const controller = new AbortController();
  const seen: string[] = [];
  const outcomes = await runSearchPlan(
    plan(),
    (
      slot: SearchSlot,
      configuration: JsonObject,
      control: SearchTrialControl,
    ): SearchTrialValue => {
      if (slot.seed === 1) {
        throw new Error("deliberate failure");
      }
      if (slot.seed === 2) {
        clock = 10;
        assert.equal(control.cancellationReason(), "timed-out");
      }
      if (slot.seed === 3) {
        controller.abort();
        assert.equal(control.cancellationReason(), "cancelled");
      }
      return completed(configuration);
    },
    {
      concurrency: 1,
      signal: controller.signal,
      now: () => clock,
      yieldControl: () => Promise.resolve(),
      onOutcome: (outcome) => {
        seen.push(outcome.status);
      },
    },
  );
  assert.deepEqual(
    outcomes.outcomes.map(({ status }) => status),
    ["completed", "failed", "timed-out", "cancelled", "not-started", "not-started"],
  );
  assert.deepEqual(statusCounts(outcomes.outcomes), {
    completed: 1,
    failed: 1,
    timedOut: 1,
    cancelled: 1,
    notStarted: 2,
  });
  assert.deepEqual(seen, [
    "completed",
    "failed",
    "timed-out",
    "cancelled",
    "not-started",
    "not-started",
  ]);
  assert.match(encodeSearchOutcomes(outcomes), /"planId": "scheduler-control"/);
  const summaries = summarizeSearch(plan(), outcomes);
  assert.equal(summaries[0]?.partition, "tuning");
  assert.deepEqual(summaries[0]?.completionRate, {
    numerator: 1,
    denominator: 5,
    denominatorKind: "planned",
  });
  assert.equal(summaries[0]?.blocks[0]?.bestObjective, 1);
  assert.equal(summaries[0]?.blocks[1]?.bestObjective, null);
  assert.equal(summaries[1]?.partition, "held-out");
  assert.equal(summaries[1]?.status.notStarted, 1);
});

test("fixed physics work and validity are admission conditions", async () => {
  // A frozen clock, as in every other test here that is not about the deadline: the plan's
  // tuning slots allow 5 ms, and decoding a rejected trial on a loaded machine can take longer,
  // which reported the slot as timed out rather than failed.
  const frozen = { now: () => 0 };
  const short = await runSearchPlan(
    plan([0]),
    (_slot, configuration) => {
      const result = completed(configuration);
      return { ...result, work: { ...result.work, physicsSteps: 3 } };
    },
    frozen,
  );
  assert.equal(short.outcomes[0]?.status, "failed");

  const invalidRank = await runSearchPlan(
    plan([0]),
    (_slot, configuration) => ({
      ...completed(configuration),
      raw: {
        ...completed(configuration).raw,
        valid: false,
        validityReason: "pair-overlap",
      },
      selectedState: "raw",
    }),
    frozen,
  );
  assert.equal(invalidRank.outcomes[0]?.status, "failed");
});

test("the registry rejects ambiguous or non-replayable plans", () => {
  const raw = {
    contract: "packing.squares:SearchPlan/v1",
    id: "bad",
    source: { commit: "abc123", dirty: false, runtime: "node-test", engine: "pack/v1" },
    configurations: [{ id: "control", configuration: { value: Number.NaN } }],
    cohorts: [],
  };
  assert.throws(() => decodeSearchPlan(raw), /finite/);
  assert.throws(
    () =>
      decodeSearchPlan({
        ...raw,
        configurations: [{ id: "control", configuration: {} }],
        cohorts: [
          {
            id: "bad-reference",
            configuration_id: "missing",
            partition: "tuning",
            n: 1,
            seeds: [0],
            block_size: 1,
            work_budget: {
              proposal_attempts: 0,
              physics_steps: 1,
              repair_iterations: 0,
            },
          },
        ],
      }),
    /unknown configuration/,
  );
});

test("persisted ledgers resume only not-started slots and reject changed plans", async () => {
  const declared = plan([0, 1]);
  const controller = new AbortController();
  const first = await runSearchPlan(declared, (_slot, configuration) => completed(configuration), {
    now: () => 0,
    signal: controller.signal,
    onOutcome: (outcome) => {
      if (outcome.status === "completed") {
        controller.abort();
      }
    },
  });
  const decoded = decodeSearchOutcomes(JSON.parse(encodeSearchOutcomes(first)), declared);
  const visited: number[] = [];
  const resumed = await runSearchPlan(
    declared,
    (slot, configuration) => {
      visited.push(slot.seed);
      return completed(configuration);
    },
    { resume: decoded, now: () => 0 },
  );
  assert.deepEqual(visited, [1, 100]);
  assert.deepEqual(resumed.outcomes[0], first.outcomes[0]);
  assert.equal(statusCounts(resumed.outcomes).completed, 3);
  const changed = structuredClone(declared);
  required(changed.configurations[0]).configuration.mode = "changed";
  assert.throws(() => decodeSearchOutcomes(first, changed), /exact plan/);
  const forged = structuredClone(resumed);
  required(forged.outcomes[0]).slot.block = 99;
  assert.throws(() => summarizeSearch(declared, forged), /mismatched slot/);
});

test("ledger admission recomputes geometry and refuses missing work and unknown status", async () => {
  const declared = plan([0]);
  const ledger = await runSearchPlan(declared, (_slot, configuration) => completed(configuration), {
    now: () => 0,
  });
  const mutate = (change: (value: Record<string, unknown>) => void) => {
    const value: Record<string, unknown> = JSON.parse(encodeSearchOutcomes(ledger));
    change(value);
    return value;
  };
  assert.throws(
    () =>
      decodeSearchOutcomes(
        mutate((value) => {
          const entries = value.outcomes as Array<{ status: string }>;
          required(entries[0]).status = "success";
        }),
        declared,
      ),
    /unsupported.*status/,
  );
  const forged = structuredClone(ledger);
  const first = forged.outcomes[0];
  assert.equal(first?.status, "completed");
  if (first?.status !== "completed") {
    throw new Error("missing trial");
  }
  required(first.result.raw.snapshot.poses[0]).x = 100;
  assert.throws(() => decodeSearchOutcomes(forged, declared), /validity disagrees/);
  assert.throws(
    () =>
      decodeSearchOutcomes(
        mutate((value) => {
          const entries = value.outcomes as Array<{ result: { work: Record<string, unknown> } }>;
          delete entries[0]?.result.work.physicsSteps;
        }),
        declared,
      ),
    /physicsSteps/,
  );
});

test("no observed valid packing completes with a null objective rather than failing", async () => {
  const ledger = await runSearchPlan(
    plan([0]),
    (_slot, configuration) => ({
      ...completed(configuration),
      bestObserved: null,
      objective: null,
    }),
    { now: () => 0 },
  );
  assert.equal(ledger.outcomes[0]?.status, "completed");
  const summary = summarizeSearch(plan([0]), ledger);
  assert.equal(summary[0]?.rankable, 0);
  assert.equal(summary[0]?.valid, 0);
});

test("observer failure waits for active runners to stop before rejecting", async () => {
  let active = 0;
  let sawCancellation = false;
  await assert.rejects(
    runSearchPlan(
      plan([0, 1, 2]),
      async (slot, configuration, control) => {
        active += 1;
        if (slot.seed === 1) {
          await new Promise<void>((resolve) => globalThis.setTimeout(resolve, 0));
          sawCancellation = control.cancellationReason() === "cancelled";
        }
        active -= 1;
        return completed(configuration);
      },
      {
        concurrency: 2,
        now: () => 0,
        onOutcome: () => {
          throw new Error("ledger write failed");
        },
      },
    ),
    /ledger write failed/,
  );
  assert.equal(active, 0);
  assert.equal(sawCancellation, true);
});
