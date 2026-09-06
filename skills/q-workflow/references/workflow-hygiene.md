# Workflow Hygiene

Use this reference when q-workflow feels bloated, slow to resume, scattered
across too many files, or at risk of losing its identity after many incremental
rules.

Trigger aliases: `workflow-hygiene`, `hygiene`, `cleanup workflow`,
`workflow cleanup`, `workflow bloat`.

## Purpose

Workflow hygiene keeps q-workflow simple, recognizable, and recoverable. It is
not a destructive cleanup mode. It detects bloat, classifies risk, applies only
low-risk mechanical fixes, and leaves larger pruning decisions visible.

## Health Signals

Run a hygiene check when any signal appears:

- a maintained workflow router or starter template was edited;
- `ACTIVE_WORK.md`, a `SKILL.md`, or a bootstrap guide grows enough that quick
  recovery no longer feels cheap;
- source, runtime, bootstrap, private, or GitHub copies drift unexpectedly;
- TODO, active-work, or skill-sync inventories disagree;
- the user says the workflow feels heavy, scattered, slow, or less distinctive.

## Health Score

Use these levels:

| Score | Meaning | Default action |
|---|---|---|
| `Clean` | No material hygiene issue. | Keep working. |
| `Watch` | Small drift, low-priority notes, or rising size signals. | Record and re-check later. |
| `Cleanup Needed` | Debt affects maintainability, recovery, or identity. | Create a focused cleanup task or patch small safe issues. |
| `Blocked` | A routing, authority, safety, or recovery issue affects current work. | Fix before relying on workflow recovery or promotion. |

## Action Ladder

Allowed automatically:

- generate a hygiene report or checklist;
- count lines and compare file hashes;
- classify findings and identity risk;
- add a TODO or handoff note for nonurgent cleanup;
- suggest moving long router content into references.

Allowed with normal local-task judgment:

- slim `ACTIVE_WORK.md` while preserving an archive;
- refresh one runtime or bootstrap mirror from an authoritative source;
- patch obvious router/help wording and validate it;
- update a report path in durable state.

Ask first:

- delete, retire, or wholesale merge skills;
- wholesale source/runtime/bootstrap synchronization;
- push, publish, or change public repository content;
- move private material into a public repo;
- change default execution mode;
- enable scheduled or background cleanup.

## Identity Guard

Before adding or promoting a workflow feature, check:

1. Does it strengthen recovery, evidence, clean routing, self-learning, or
   engineering-artifact feedback?
2. Does it belong in the core, a flagship path, a lab/experimental path, or an
   archive?
3. Can a future agent validate it with an observable probe?
4. Is there a demotion or retirement condition?

If the answer is unclear, keep the idea in a report, TODO, or lab reference
instead of adding it to `SKILL.md`.

## Session and archive hygiene

`ACTIVE_WORK.md` has one executable recovery slot. When `Current Focus` is
active, exactly one level-two heading may begin with `RECOVERY_POINTER`.
Historical envelopes must use a non-matching heading such as
`Historical Recovery Snapshot`. The only zero-pointer exception is the exact
fresh-install idle focus `- No active blocking focus.`. Multiple pointers are a
P1 recovery defect: parsers and audits must fail closed instead of choosing the
first or newest-looking entry.
The explicit idle focus must contain zero executable recovery pointers; an idle
focus plus a pointer is invalid because it creates two authorities.

When Codex feels slow, inspect its own session store before blaming project
software. Keep the current conversation intact, but classify the store into
current sessions, active child sessions, completed child logs, and archived
history. Completed/archived logs belong on the data volume with a manifest;
they should not be duplicated under both the system-volume archive and the
project archive. Recheck the largest files after cleanup because a stopped
thread can still leave one completed child log behind or rehydrate it when its
metadata changes. A compact recovery note is preferable to reloading a large
history just to keep a thread visible.

For skill portfolio and "how q-workflow makes skills better" decisions, read
`workflow-identity.md`.
