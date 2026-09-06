# Migration And Closure Record

## Scope

- Old name: `game-canvas-iteration`.
- Canonical name: `q-game-canvas-iteration`.
- Change class: major lifecycle and naming repair.
- Non-goals: no push, public release, company variant, bootstrap update, or
  stable promotion in this work round.

## Baseline

The first candidate existed only in the runtime skill directory. The canonical
baseline is now this public-safe source tree in `q-workflow-hub`; runtime is an
installation target. The previous runtime-only source claim is classified as a
fixed process defect.

## Alias Classification

| Hit | Classification | Decision |
| --- | --- | --- |
| `game-canvas-iteration` runtime directory | retired | Do not create or reinstall it. |
| Source alias directory | retired | Delete it from the published skill bundle. |
| This migration/release history | historical mapping | Keep for recovery. |
| Legacy text trigger | compatibility mapping | Route through canonical description/metadata, without a second skill folder. |

## Closure Gates

Before local migration closure:

1. Validate source files, metadata, UTF-8, naming, and source/runtime parity.
2. Install the source tree to runtime and confirm hashes/readback.
3. Confirm source and runtime contain no old alias directory, while the
   canonical description/metadata still recognize the legacy text trigger.
4. Replay `SCENARIOS.md` and record outcomes.
5. Obtain an independent Workflow Distiller (沉炼) post-review and record every
   finding as accepted, deferred, or rejected.

Until these gates pass, the skill remains pilot and this migration remains
pending local closure.

## Local Closure: 2026-07-12

All local migration gates passed after source-to-runtime installation:

- canonical and runtime trees have identical hashes;
- source and runtime aliases contain only the approved two files;
- naming, UTF-8, public-safe, scenario, and diff-hygiene checks passed;
- Workflow Distiller (沉炼) completed independent pre- and post-review.

Prior B1 is resolved. Prior B2 is resolved for local pilot closure; the initial
skipped preflight remains documented as a process defect. The lifecycle status
stays `pilot`, and no push, public release, team-ready, or stable claim is made.

## Alias Retirement: 2026-07-22

Xiao Q confirmed that the published non-`q-` folder is redundant. The source
alias was removed, and the current runtime had no old alias to delete. Old text
requests remain recoverable through the canonical skill description and
metadata. This is a major compatibility cleanup at the folder level, but it
does not change the canonical workflow, output contract, or pilot status.
