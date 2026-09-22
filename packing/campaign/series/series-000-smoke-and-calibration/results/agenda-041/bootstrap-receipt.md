# Bootstrap Receipt: a Fresh Clone Cannot Run the Research Loop (BC-368)

Status: **five preconditions were missing, none of them written down anywhere, and the
gate could not run until all five were repaired.** After the repair the edit tier passes
at 124.4 s of wall against its 240 s ceiling.
Session-151, efficiency block, 2026-09-22, on a four-cpu remote session cloned fresh at
`97efd26f`.

This is recorded because a review block that cannot run its own instruments is not a
review block, and because the first command of the session was the edit tier and it
failed three steps. `OR-12` opens an efficiency block by measuring, and this is what the
measurement found before any planned item was touched.

## What failed, in the order it was hit

| # | Symptom | Cause | Repair |
| --- | --- | --- | --- |
| 1 | `uv python install 3.14.7` → `No download found for request: cpython-3.14.7-linux-x86_64-gnu`; then `uv sync` → `No interpreter found for Python 3.14.7` | The image ships `uv` 0.8.17, whose compiled-in interpreter index ends at `cpython-3.14.0rc2`. `uv self update` does **not** fix it: it exits on a GitHub API rate limit | Install a current `uv` directly (`curl -LsSf https://astral.sh/uv/install.sh \| UV_INSTALL_DIR=... sh`), which gave 0.12.17 |
| 2 | `.python-version` pins 3.14.7 and no such interpreter is present | Managed interpreters are not part of the image | `uv python install 3.14.7` (2.20 s once `uv` is current) |
| 3 | `uv sync` → `kpress ... does not appear to be a Python project` | The `vendor/kpress` submodule is registered and not populated | `git submodule update --init --recursive` |
| 4 | `provenance: recorded commits are reachable` fails: recorded engine commits are unavailable in local history | The clone is shallow | `git fetch --unshallow` (12 s). The step’s own message already names this remedy |
| 5 | `browser floor (biome, eslint, tsc, node:test)` fails | `npm ci` has not been run | `npm ci` at the repository root, or `make hooks-install`, which also installs the commit hook |

A sixth, found later in the block and not part of the edit tier: the Rust search engine
is not built (`sqsearch/target/release/` absent), so every upper-bound experiment is
blocked until `cargo build --release --manifest-path sqsearch/Cargo.toml` runs.
It cost 19.05 s.

## The measurement that matters

Before the repair: three steps red, and the tier could not reach the other 79.

After the repair, `uv run --frozen --all-extras --group dev packing-validate --edit`:

```
   124.39s  type floor (basedpyright)
    99.64s  browser floor (biome, eslint, tsc, node:test)
    87.20s  exact verification
    15.03s  browser code lives in files
    14.09s  bead tree
    11.45s  soft-schema validation
     9.78s  every session's cost is attributed
     7.13s  provenance: recorded commits are reachable
   124.40s  TOTAL (wall)
50 of 82 STEPS PASSED (a named tier; this is not the full gate)
```

124.40 s of a 240 s ceiling, 52%, exit 0. The run’s shape (4 cpus,
`--jobs 4 --inner-jobs 1`) is not the edit tier’s declared reference (2 cpus,
`--jobs 2 --inner-jobs 1`), so the band was reported and not enforced and **no figure
from this session is the one to write into `gate-budgets.yaml`**. `OR-14`’s target for
the surface is two to two and a half minutes; the tier is inside it on this box.

## Where the answer now lives

`devtools/check_bootstrap.py` reports all five facts with a remedy per failure and
repairs nothing, because installing a toolchain or fetching history behind a check is a
mutation nobody asked for.
It is stdlib-only and imports nothing from `sqpack` or the rest of `devtools`, which is
load-bearing rather than tidy: the failure it diagnoses is the one where the project
interpreter does not exist, so it has to run under whatever `python3` the machine
already has. It was verified clean on CPython 3.10 through 3.14.

It is deliberately **in no tier**. A step inside the gate cannot report the failure it
exists to explain, because when these facts are false `uv run` fails before any step
executes.
In CI the five are true by construction — `fetch-depth: 0`, `submodules: true`,
a pinned `setup-uv`, and `npm ci` — so a step there would be ceremony under `OR-15`, and
inside an edit loop it would re-establish clone-time facts at 0.5 s a cycle against
`OR-14`. The accepted cost is that nothing in CI exercises the module, so it can rot; a
follow-up bead should give it unit tests over its four pure helpers.

`AGENTS.md` gains a `### A fresh clone` subsection under Build & Test with the five
commands and the reason each exists.

## A second finding, repaired in place

While the clone was shallow, `devtools.check_session_gate` reported eleven terminal
sessions as declaring a gate at a commit “which is in this history and is not an
ancestor of HEAD”. That verdict was **wrong, not merely unhelpful**:
`git merge-base --is-ancestor` stops at the graft point in a shallow clone, so a true
ancestor reads as a non-ancestor.
The module already computed `history_state() == "shallow"` and already had it in the
relevant signature, so the fix was to order that branch ahead of the two `orphaned`
branches: in a shallow checkout both readings now go to `unresolved` with a distinct
detail string, and the existing `git fetch --unshallow` remedy line prints.
A complete checkout is unchanged.
Pinned by `test_a_severed_ancestor_in_a_shallow_checkout_is_uncheckable_not_false`,
which builds a merge, clones it `--depth 1`, asserts the false verdict, unshallows, and
asserts the commit reads `reachable`.

## What this receipt does not establish

Nothing about the deep gate, whose 45-minute wall and 1.376x drift are `think-zmos`’s
own measurement and are treated in the CI-wall receipt beside this one.
No figure here is a reference-shape gate cost.
The `check_bootstrap` module has no test of its own.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
