import type { GeometrySnapshot } from "../core/geometry.ts";
import type { PackingAssessment } from "../core/runtime-contracts.ts";
import type {
  PackAnnealConfiguration,
  PackConfiguration,
  PackContainerConfiguration,
  PackPhysicsConfiguration,
  PackReceipt,
  PackStationarityConfiguration,
} from "../simulation/pack.ts";
import type { ResolveReceipt } from "../simulation/resolve.ts";
import type { AtlasLaw } from "./workbench-api.ts";

export interface PackControllerOptions {
  n?: number;
  seed?: number;
  startKind?: "grid" | "random" | "given";
  snapshot?: GeometrySnapshot;
  physics?: Partial<PackPhysicsConfiguration>;
  anneal?: Partial<PackAnnealConfiguration>;
  container?: Partial<PackContainerConfiguration>;
  stationarity?: Partial<PackStationarityConfiguration>;
  pairLaw?: AtlasLaw;
  wallLaw?: AtlasLaw;
}

export interface PackControllerState {
  configuration: PackConfiguration;
  snapshot: GeometrySnapshot;
  latest: PackReceipt | null;
  repair: ResolveReceipt | null;
  assessment: PackingAssessment;
}

/** Public handle for the currently displayed Pack session. */
export interface PackWorkbenchApi {
  configure(options: PackControllerOptions): PackControllerState;
  play(): void;
  pause(): void;
  playing(): boolean;
  step(count: number): PackControllerState;
  restart(): PackControllerState;
  resolve(): ResolveReceipt;
  load(text: string): PackControllerState;
  state(): PackControllerState;
  exportSnapshot(): GeometrySnapshot;
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function finite(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new TypeError(`${label} must be a finite number`);
  }
  return value;
}

/** Parse geometry only. A snapshot does not contain velocities or resume a trajectory. */
export function parsePackSnapshot(value: unknown): GeometrySnapshot {
  if (!object(value) || !object(value.container) || !Array.isArray(value.poses)) {
    throw new TypeError("Pack snapshot requires squareSide, container, and poses");
  }
  const squareSide = finite(value.squareSide, "squareSide");
  const side = finite(value.container.side, "container side");
  if (squareSide <= 0 || side <= 0 || value.poses.length === 0) {
    throw new RangeError("Pack snapshot requires positive dimensions and at least one pose");
  }
  return {
    squareSide,
    container: {
      originX: finite(value.container.originX, "container originX"),
      originY: finite(value.container.originY, "container originY"),
      side,
    },
    poses: value.poses.map((pose: unknown, index: number) => {
      if (!object(pose)) {
        throw new TypeError(`pose ${index} must be an object`);
      }
      return {
        x: finite(pose.x, `pose ${index} x`),
        y: finite(pose.y, `pose ${index} y`),
        angle: finite(pose.angle, `pose ${index} angle`),
      };
    }),
  };
}
