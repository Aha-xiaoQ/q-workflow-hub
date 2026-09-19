# Personal State Routing

Use this reference for the private personal control hub, runtime mirrors, work
item shape, lesson capture, and skill/source inventory rules.

## Activation

| Trigger | Tier | Risk | Action |
|---|---|---|---|
| General resume or interruption recovery | Quick | allow | Read `ACTIVE_WORK.md`, then the active work item. |
| Dirty or stale mirror | Deep | allow local sync | Prefer source hub; refresh only affected mirror files. |
| New concrete task | Project | allow local write | Create or update one work item early; if it is the default resume target, promote `RECOVERY_POINTER`/`Current Focus` in the same initial task-start turn. |
| Switching away from unfinished work | Project | allow local write | Mark paused and update `PAUSED_WORK.md`. |
| Credential or secret handling | Any | deny/ask | Do not store secrets in hub or skills. |

## Personal Cross-Project State

When a private personal state hub exists, use it as the first routing layer for
interruption recovery, project switching, and parallel work.

Preferred source of truth for a company user:

`<personal-hub>\personal-state`

Runtime mirror for Codex discovery:

`%USERPROFILE%\.codex\q-personal-state`

Personal control hub repository:

`<personal-hub>`

Blank-machine recovery remote:

`<private-personal-hub-remote>`

Expected structure:

- `PROJECT_REGISTRY.md`: project names, local paths, remotes, resume skills,
  and status.
- `ACTIVE_WORK.md`: small index of current focus and active/recent work items.
- `ASSISTANT_HELP.md`: short capability guide to answer prompts such as
  "help", "features", or "what can you do".
- `SKILL_SYNC.md`: optional inventory of local skills, durable sources,
  install methods, and cross-machine migration notes.
- `PAUSED_WORK.md`: short queue of interrupted tasks to present when the user
  asks to continue previous work.
- `SOURCE_REGISTRY.md`: reusable public sources, source role, license posture,
  and safe-use notes.
- `TODO.md`: lightweight personal inbox for small future ideas, reminders, and
  planning fragments that are not yet projects or work items.
- `work-items/<id>.md`: one file per active or paused work item.
- `journal/<date>/<entry>.md`: append-style notes for important cross-project
  recovery findings.

Rules:

- The personal hub stores cross-project pointers, active task intent,
  repository paths, owner/session notes, and next actions.
- Project repositories remain authoritative for project facts, outputs,
  decisions, and validation status.
- When `PROJECT_STATE.md`, `TASKS.md`, a project handoff, or a user-approved
  project state note becomes the new default resume target, update the personal
  hub `ACTIVE_WORK.md` `RECOVERY_POINTER` and `Current Focus` in the initial task-start turn,
  append the corresponding `RECOVERY_EVENTS.md` event, and refresh the runtime
  mirror. If this cannot be completed, set or report a non-synced pointer state
  so the next Quick Resume must run a bounded stale-pointer audit.
- An artifact pointer identifies state; it does not grant permission. Validate
  the matching task and latest user intent. A request to continue identified
  unfinished work resumes its existing authorized scope; a status-only question
  remains read-only. Ask only for an ambiguous target or missing authority,
  preserving all current no-push, hardware and private-data boundaries.
- Skills remain authoritative for reusable behavior.
- Prefer one work-item file per task so multiple AI agents do not repeatedly
  edit the same file.
- Store only minimal routing data in the personal hub; do not store project
  contents, credentials, customer secrets, generated decks, paper PDFs, or
  private data dumps.
- When both `<personal-hub>\personal-state` and
  `%USERPROFILE%\.codex\q-personal-state` exist, treat the personal hub copy as
  authoritative and the `.codex` copy as a runtime mirror unless a
  project-specific instruction says otherwise.
- For exact `TODO` / `todo` / `TODO:<text>`, this authority rule still applies
  even though the command is a micro path. Read or append the hub
  `personal-state\TODO.md` first when available; use the `.codex` TODO only as
  a fallback or mirror. If a TODO appears in the hub but not the runtime mirror,
  refresh the affected mirror before closing or report the drift explicitly.
- If a prompt names project A but the personal hub shows the latest active work
  item is in project B, call out the mismatch before proceeding.
- When switching away from unfinished work, mark the work item as paused and
  add it to `PAUSED_WORK.md` with the reason and next concrete action.
- Keep `ASSISTANT_HELP.md` current when user-facing workflow capabilities are
  added, changed, or retired.
- Keep `TODO.md` lightweight. Use it for small ideas and reminders. Promote a
  TODO into a work item only when it becomes concrete work with files,
  validation, or handoff requirements.
- When completing, handing off, checkpointing, or closing a work round, run a
  bounded relevant closure-ledger check across the current task id/objective,
  `ACTIVE_WORK.md` `Current Focus`, the active work item, matching `TODO.md`
  entries, `PAUSED_WORK.md` only when the task was paused or resumed, and
  affected runtime mirrors. Use `scripts/closure_ledger_check.py --task-id <id>
  --expect closed` for the mechanical pass when a stable id exists; use
  `--objective <text>` only for a narrow phrase, not broad words. A completed
  task is not closed until it is removed from `Current Focus`, its work item is
  marked `Completed` or archived, matching Open TODO entries are moved to Done
  or left Open with a reason, and affected runtime mirrors are refreshed or
  explicitly deferred.
- `ACTIVE_WORK.md` `Current Focus` must contain only work that should resume by
  default. Completed or closed entries belong in `Recently Completed`, `Done`,
  an archive, or a report path. Do not leave text such as `Closed`, `Completed`,
  `done`, `no blocker`, or `no action needed` inside `Current Focus` unless the
  entry still has a concrete next action.
- If a matching Open TODO is only partially complete, keep it Open and append a
  short remaining-action note instead of silently treating adjacent validation
  as closure. Closure must match the original objective or TODO/work-item id
  first; evidence proves closure only after that objective match. If the match
  is ambiguous, say so in the handoff.
- Create or update the personal work item as soon as a task becomes concrete,
  even before code, docs, or tests are complete. The active work item alone is
  not enough for a new default resume target: also promote `ACTIVE_WORK.md`
  `RECOVERY_POINTER`/`Current Focus`, append `RECOVERY_EVENTS.md`, and sync or
  mark the runtime mirror before substantive work continues. Interruption
  recovery must not depend on an end-of-round checkpoint.
- Distinguish reference material from owned work. Imported third-party skills,
  cloned examples, downloaded tutorials, and web pages are evidence, not the
  active project, unless the work item says they are the deliverable.
- Treat agent-local skill install folders as runtime copies. If a local skill
  becomes part of normal work, promote it into an owned Git-tracked source or
  record its source, install method, version, license posture, and migration
  notes in `SKILL_SYNC.md`.
## Closure Record Schema

Use a closure record when a work round changes durable state, reusable workflow
rules, TODO/work-item status, source/runtime mirrors, release posture, or a
handoff artifact. The record may live in the active work item, final report,
project handoff, or another durable file that the next session will read. Use
`assets/templates/CLOSURE_RECORD.md` for longer handoffs; keep tiny bookkeeping
closures inline in the work item or report.

Minimum fields:

- `task_id`: stable TODO id, work-item id, issue id, or short objective slug.
- `objective`: original user objective or explicitly promoted task statement.
- `status`: `closed`, `partial`, `deferred`, or `blocked`.
- `evidence`: output paths, validation commands/results, reviewed diffs,
  commits, tags, checkpoints, or handoff packets.
- `ledger_reconciliation`: what changed in `ACTIVE_WORK.md`, `TODO.md`, the
  active work item, `PAUSED_WORK.md` when relevant, and affected runtime
  mirrors.
- `follow_ups`: parked work with remaining action, reason deferred,
  owner/surface, and reopen trigger.
- `residual_risk`: unvalidated assumptions, skipped surfaces, unrelated dirty
  files, blocked approvals, or known gaps.

A validation log or generated report is evidence, not a closure record, unless
it explicitly connects the original objective to the ledger reconciliation and
remaining follow-ups.
## Lesson Capture

Capture reusable lessons without waiting for the user to remind you. Record a
lesson when a work round reveals:

- a repeated environment issue or workaround;
- a recovery gap, sync failure, or Git/network failure mode;
- a validation lesson that should change future checks;
- a user preference that should change collaboration behavior;
- a workflow friction point that caused wasted time or context;
- a completed task, report, or validation loop was left as an Open TODO because
  closure evidence was not reconciled back into the lightweight task ledger;
- a completed task stayed in `ACTIVE_WORK.md` `Current Focus`, causing resume to
  re-enter a finished round;
- a new concrete default task began but `ACTIVE_WORK.md` was not promoted at
  task start, causing resume to re-enter the previous project;
- a scope or completion mistake where adjacent validation was treated as the
  original target being complete;
- a completed real-sample analysis was not recorded durably enough to recover
  source, result, and conclusions after compaction.

Use the right layer:

- Generic reusable behavior belongs in `q-workflow` or another reusable
  skill.
- Skill-making rules belong in `q-skill-creation`.
- User collaboration preferences belong in `q-assistant-profile`.
- Project facts, outputs, and decisions belong in the project repository.
- Active routing and incomplete work belong in personal work items.

If hook-assisted lesson capture is configured, treat hook output as an inbox of
candidates, not as authoritative memory. Review hook candidates during resume
or end-of-round cleanup, then decide whether to discard them or promote them to
the correct durable layer.

## Work Item Contents

Each active work item should be concise but sufficient for a fresh session:

- Objective and current status.
- Status values should distinguish `Active`, `Paused`, `Completed`, and
  `Blocked` rather than leaving stale handoff wording.
- Local paths and remotes involved.
- Reference URLs, imported example skills, or tutorials being used.
- Decisions made, open questions, and the next 1-3 actions.
- Validation and sync gaps, including network failures and uncommitted work.
- A `Session Recovery Note` when platform/session failures, compaction
  failures, or broken chat windows could hide the latest user intent.

Use this brief shape for new work items and substantial first prompts:

- Role or working mode.
- Current state.
- Task.
- Constraints.
- Output.
- References.

For project facts, prefer durable files and Git over chat memory, searchable
notes, RAG, or fine-tuned style. Search and RAG can help find background
material; they should not be treated as the authoritative current project state
unless the project explicitly defines them that way.

Update the work item after planning discussions that change direction, not only
after file edits.
