# Workflow Kernel Architecture

Use this reference for workflow-wide health checks, task-state management, and
source/bootstrap/runtime reconciliation. It defines the small stable kernel;
domain skills keep their own procedures and evidence.

## Ownership Model

```text
registered source -> content manifest -> personal bootstrap -> runtime copy
                                  |
task record + JSONL authority event -> ACTIVE_WORK focus view + runtime mirror
```

- A repository registered in `q-profile.json` is the normal source authority.
- `references/surface-registry.json` declares which skill surfaces are expected
  at each layer and their stability tier. It is inventory, not a copy engine.
- `personal-state/tasks/<task_id>.json` is the canonical record for one material
  task. `personal-state/TASK_EVENTS.jsonl` binds its current revision to one
  append-only authority event.
- `ACTIVE_WORK.md` is only the selected focus view. It may point to one task,
  while other registered tasks remain independently inspectable.
- A managed `q-workflow-focus-v2` pointer is valid only when its `task_id`
  resolves to one canonical task JSON and its `authority_event` resolves to the
  bound latest JSONL event. A Markdown pointer without that entity/event chain
  is a dangling pointer, not recoverable state.
- Managed focus pointers also carry a derived visibility lease. Work states
  `active`, `validating`, and `blocked` require
  `visibility_latch: phase-b-required`; all other states require
  `visibility_latch: not-required`. Task transactions derive this field;
  status, task listing, and base audit reject a missing or contradictory value.
- Domain-specific stages and verdicts live in the task record's `detail`
  object. They never replace the generic work, integrity, or release axes.

## Unified Manager

The manager is local-first and read-only by default:

```powershell
python scripts/q_workflow_manager.py status
python scripts/q_workflow_manager.py doctor
python scripts/q_workflow_manager.py doctor --full --rounds 2
python scripts/q_workflow_manager.py surfaces --tier all --strict
python scripts/q_workflow_manager.py task list
python scripts/q_workflow_manager.py task validate --task-id <task-id>
```

Task changes use a two-step transaction:

```powershell
python scripts/q_workflow_manager.py task plan --record <candidate.json> --focus-file <focus.md> --output <plan.json>
python scripts/q_workflow_manager.py task apply --plan <plan.json> --yes
```

Use `--focus-current` only when the candidate task already owns the managed
focus and its existing human `Current Focus` prose should remain byte-for-byte
equivalent after normalized rendering. It is an executable error to use
`--focus-current` for a different `task_id`: use `--focus-file` to replace the
complete focus prose during an explicit cross-task switch, or omit both focus
options to update a non-focus task without changing `ACTIVE_WORK`.

An explicit cross-task switch must also carry non-empty
`detail.recovery_rules` and `detail.non_executable_index` arrays in the
candidate task record. The manager replaces those task-scoped sections in the
same CAS transaction as `Current Focus` and `RECOVERY_POINTER`; it blocks if
the candidate omits them. This prevents a valid pointer for task B from being
paired with recovery guidance left behind by task A.

This semantic identity gate complements the existing hash/CAS gate. Hashes can
prove that a transaction is intact, but they cannot make prose about task A
valid for a pointer to task B.

Planning writes no authoritative state. Apply verifies the profile and runtime
identity, compares every expected SHA-256, takes an exclusive lock, writes by
same-directory atomic replacement, appends the bound event, regenerates the
focus view and runtime mirror, validates readback, and writes a receipt. A
hash mismatch blocks instead of merging concurrent edits. Replaying an already
applied plan is idempotent.

`task list` is the discovery entry for non-focus tasks. `surfaces` is advisory
unless `--strict` is present; release and automated gates must use `--strict`.
`status`, `task list`, `doctor`, and the foundational base-command audit must
fail closed when a managed focus pointer is dangling, even if source/runtime
Markdown mirrors are byte-identical. Mirror equality proves replication only;
it does not prove task authority or recoverability.
TODO commits, the base-command runtime mirror, and the task manager share the
same non-blocking OS state-writer lock. The operating system releases ownership
when a process exits, so a persistent lock file is not a stale-lock condition.
Each writer rolls back every switched file after an in-process failure.
Unexpected process termination between file switches can still leave a partial
multi-file transaction; that remains a local-only residual risk until a durable
write-ahead recovery journal is implemented.

## Compatibility And Migration

- Existing `RECOVERY_POINTER v1` readers remain supported. A migrated focus
  pointer carries `schema: q-workflow-focus-v2`, task-record/event paths, and
  hashes while retaining flattened compatibility fields.
- `sync_state` is a derived compatibility alias. New validation is governed by
  `integrity_state`; absence of `sync_state` is not itself a defect.
- Legacy Markdown recovery events remain readable for unmigrated tasks. New
  task transactions use JSONL so event identity and revision hashes are
  machine-checkable without parsing prose.
- `workflow_lifecycle.py --task-id` and `--trace-id` inspect parallel tasks;
  calling it without a selector inspects the active focus and falls back to the
  legacy envelope when no registered record is attached.
- New task records start at `briefing/local-validated/local-only`. The only
  non-briefing registration exception is the named legacy-pointer migration;
  its record and authority event must both carry the migration marker.
- The legacy pointer branch may retire only after all active material tasks
  have task records, a golden-equivalence replay covers one full lifecycle,
  and a release note names the compatibility window.

## Design Boundary

The kernel borrows proven mechanisms without importing an orchestration
framework: progressive disclosure, versioned checkpoints, explicit task and
artifact lifecycles, capability-aware surfaces, trace evaluation, minimal
telemetry, and content-addressed descriptors. q-workflow does not require
LangGraph, MCP, A2A, OpenTelemetry, or a hosted service to resume local work.
Those systems can be adapters later; they do not become local state authority.

Do not record prompts, tool arguments, credentials, or private artifact bodies
in default telemetry. Health evidence is limited to statuses, hashes,
`elapsed_ms`, stable failure classes, and explicit artifact paths.

## Change Gate

Before promoting a kernel change:

1. Run the manager self-test.
2. Run lifecycle and portfolio checks from the profile-resolved authority.
3. Reconcile every registered surface manifest; do not overwrite a newer or
   divergent runtime silently.
4. Run the two-round strict stability suite.
5. Complete independent code review and cold-start usability validation for a
   major candidate.
6. Keep release local-only until remote freshness and user signoff are proven.
