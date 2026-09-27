# Automatic frontier search-grid refinement

## Incident and scope

The supplied production log reaches VERIFIED 3.964699 after four full-gate
successes at resolution 1/1000000, then idles because every configured strategy
has an observed heuristic ceiling at 3.964700. The gap is one grid step and
there is no admissible interior grid point. Manually changing strategy-width
only postpones the same administrative stop.

This change refines the search grid autonomously. It does not assert that the
method can pass the old heuristic ceiling, certify any untested side, change
numerical proof tolerances, or discard earlier search failures.

## Policy

The existing fixed-grid planner is unchanged except that search_resolution
reads the persisted effective grid. The controller's read-only choose_work
preview first asks for normal generation, same-side rationalisation and repair.
Only an otherwise exhausted plan may return refine-resolution. Before doing so,
an exhausted observed ceiling is eligible for one stronger-seed re-probe.

An eligible observed strategy bracket must be too narrow for two current grid
steps, or have no aligned interior grid point after rounding. An unobserved
horizon, a disabled strategy or a duplicate operational failure alone is not
an excuse to repeat work at a smaller step. Live cycles, a durable generation
wave, active repairs and BLOCKED mode preclude refinement.

Each committed transition uses exact Fraction arithmetic:

    new = max(old / 10, 32 * ulp(float(verified_low)))

The final floor-clamped transition need not be exactly one decade. At the floor
there is no further transition, no reset and no repeated refinement heartbeat.
If the fixed-grid planner still has no work, IDLE remains legitimate and names
the 32-ULP floor. This is not a mathematical impossibility proof.

When a verified bound has approached an observed heuristic ceiling until the
current grid has no interior point, the controller first re-probes that ceiling
with the stronger verified seed. This prevents an asymptotic decimal chase that
can never cross the old heuristic observation. A failed re-probe is not repeated
again until the verified seed advances; only then may the grid refine further.

For the observed 3.964699999999 versus 3.964700000000 state, the next useful
target is therefore 3.964700000000 itself, not another midpoint below it. If the
unchanged full exact gate verifies that target, its old UNRESOLVED/SEARCH_FAILED
records cease to bound the strategy and normal exploration continues above it.

## Persistence, stop and resume

config.strategy_width remains the requested starting grid. adaptive_resolution
stores requested_width and effective_width, and resolution_history stores every
exact transition, timestamp, lower endpoint, search revision and triggering
strategy brackets. Saving precedes admission of generation at the new grid.
The ordinary state backup and resume machinery preserves these fields.

Omitting strategy-width on resume retains the effective value. An explicitly
changed starting width starts from that new setting; an equivalent spelling
of the same rational width does not reset automatic progress. Earlier history
is retained in either case. No schema replacement or experiment deletion is
needed. Status/summary/report previews never commit transitions.

The controller checks operator cycle/time/target limits before adapting.
Ctrl-C before the transition prevents it; a stop after its checkpoint leaves
the smaller grid resumable without launching a new stage. No active wave is
modified and no new CPU executor or native kernel is introduced.

## Validation and operation

The focused tests reproduce both 1e-5 and 1e-6 one-step gaps, multiple decades,
the 32-ULP floor, nonaligned rational endpoints, disabled/error-only instruments,
active work and repairs, corrupted checkpoints, explicit width changes,
read-only status, real state loading, controller continuation and stop ordering.
Fixture VERIFIED/UNRESOLVED records are controller inputs, not proof artifacts.
The tests are included in the existing Frontier autonomy, Native A/B validation
and Frontier utilization workflows.

After stopping a running process and pulling the change, use the ordinary
production campaign command. No smaller strategy-width argument is required:

```bash
cd /home/user/DEV/squares/packing
uv sync --frozen
uv run --frozen python -m devtools.native_ab campaign \
  --root /home/user/DEV/squares/Experiments/n12-frontier-search \
  --resume --workers 16 --generation-trials 3 --minutes 0 --label production
```

The log emits [resolution] with decimal and exact old/new grids. Startup and
summary show the effective grid. Resolution refinement changes target admission,
not the meaning of VERIFIED, search budgets, kernel selection or CPU limits.
