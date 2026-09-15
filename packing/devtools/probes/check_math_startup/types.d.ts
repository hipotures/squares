// The instrumentation `check_math_startup`'s init script installs as `__mathStartup`. Only
// the members a probe outside the init script touches are declared here; extend the
// interface by merging as more probes read it.
interface SquaresMathStartupState {
  settlement_state?: "pending" | "resolved" | "rejected";
  errors: string[];
}

declare var __mathStartup: SquaresMathStartupState | undefined;
