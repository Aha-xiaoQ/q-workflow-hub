---
name: q-workflow
description: Reusable project workflow and executable foundation gate invoked by q-assistant-profile. Use when creating, resuming, organizing, validating, updating, syncing, migrating, or recovering projects, durable state, workflow rules, or foundational command installations.
---

# Q Workflow

Use this skill to make a project recoverable across agent sessions, machines,
and interruptions. q-workflow is file- and Git-based: project facts live in
project files and Git; reusable behavior lives in skills; personal routing
lives in the user's private hub.

## First-Read Router

| User intent | Read next |
|---|---|
| Exact `TODO` / `todo`, `TODO:<text>`, or a number after a TODO list | Micro path: `TODO`/`todo` lists routed `personal-state/TODO.md`; `TODO:<text>` appends; a plain number selects the current listed item. Do not scan project repos, validate, commit, or push just because a TODO was listed or added. |
| Exact `TOKEN` / `token` / `tokens` / `token usage` | Micro path: run `scripts/q_base_command.py --input TOKEN --open-ui --format json`; show `surface.chat_text` verbatim so the concise summary and dashboard receipt always appear together. |
| Loop run, loop engineering, bounded autonomous run, or `循环执行` | `references/full-guide.md` `Command Alias Layer`; treat as unattended by default, infer reasonable validation/progress defaults, run permission preflight, and avoid waiting idly on mid-loop approvals. |
| Unattended automation, recurring heartbeat, resource exhaustion, automation stop failure, or repeated blocked wakeups | `references/unattended-resource-guard.md` before creating, resuming, retrying, or stopping the loop |
| Resume, continue, recover, or status | Personal `ACTIVE_WORK.md`, active work item, then one targeted Git status |
| Existing project resume | Project README/state files, project-local workflow instruction, then targeted Git status/log |
| New project bootstrap, project structure, folder standardization, or migration cleanup | `references/project-structure.md`, then `references/full-guide.md` `New Project Bootstrap` section |
| Workflow architecture, evolution, or native capability replacement | `references/workflow-evolution.md` |
| Capability adaptation, excessive clarification/testing, native-tool selection, or model changes | `references/adaptive-execution.md`; optional `scripts/execution_policy.py` for regression or ambiguous planning, never a per-turn gate |
| Workflow health check, manager CLI, task registry, state transaction, or source/bootstrap/runtime surface drift | `references/workflow-kernel-architecture.md`, then `scripts/q_workflow_manager.py status` or `doctor` |
| Long-running work with scattered evidence, competing principles, stale pointers, or repeated micro-tuning | `references/q-standard-contract.md` `Single Active Authority Gate`, then the owning domain skill |
| Learning/training, design, visual creation, translation, tool selection, or quality-improvement work | `references/q-standard-contract.md` `evidence-led-learning-design`, then the owning domain skill; collect/inspect reliable material before promoting a method or candidate |
| Visual imitation, reference reproduction, pixel/grid reconstruction, higher-resolution optimization, candidate activation, or a request to learn a visual reference before creating | `references/q-standard-contract.md` `visual-candidate-review-before-live-activation`, then the mapped domain skill's visual-review reference |
| Material task lifecycle, parallel task lookup, compaction recovery, source/bootstrap/runtime authority, or remote freshness | `references/lifecycle-contract.json`, then `scripts/workflow_lifecycle.py --strict`; use `--task-id` or `--trace-id` for non-focus tasks |
| Workflow bloat, cleanup, hygiene, or identity risk | `references/workflow-hygiene.md` |
| Standards, rule hardness, output grammar, blocker semantics, lifecycle gates, or expert auto gates | `references/q-standard-contract.md` |
| Workflow identity, skill-fit, portfolio, or distinctiveness | `references/workflow-identity.md` |
| Chinese text, UTF-8, mojibake, terminal display corruption, `Get-Content` garbled output, encoding issue, or PowerShell display corruption | `references/encoding-safety.md` |
| Context budget, large files, or excessive process | `references/adaptive-execution.md` `Bounded Context And Work` |
| Recovery after compact/session failure | `references/full-guide.md` `Platform Session Failure Recovery` section |
| A previously used custom workbench/tool is mentioned, forgotten, or needs continuation | `references/recovery-routing.md` `Reusable Tool Continuity Gate`, then the owning domain skill |
| Workflow hub, work items, or lesson capture | `references/full-guide.md` `Personal Cross-Project State` and `Lesson Capture` sections |
| Summary, consolidation, or lessons learned after a work loop | `references/full-guide.md` `Summary And Sedimentation` section |
| Command aliases, help, permissions, or push ambiguity | `references/full-guide.md` `Command Alias Layer`, `Help and Feature Prompts`, and `Permission Posture` sections |
| Commit, push, end-of-round sync, promotion-repo cadence, or GitHub proxy troubleshooting | `references/sync-and-push-policy.md`, then `references/full-guide.md` `GitHub Push Troubleshooting` section only if proxy/debug detail is needed |
| Repository naming or migration | `references/repository-naming.md` |
| Full legacy detail | `references/full-guide.md` |

## Foundational Command Gate

- Exact base commands are registered in
  `references/base-command-contract.json`; route them before free-form semantic
  interpretation.
- For exact `TODO`/`todo`, run
  `scripts/q_base_command.py --input TODO --format json` from the installed
  `q-workflow` tree. Use its q-profile authority and Open items; never search
  for a file by name first or answer from a legacy mirror.
- For exact `帮助`, run
  `scripts/q_base_command.py --input "帮助" --open-ui --format json`. For exact
  `TOKEN`, use the same gate with `--input TOKEN --open-ui`. For bare `小Q`, use
  the gate with `--input "小Q"`. In all four cases, show the returned
  `surface.chat_text` verbatim; do not simplify it, substitute a free-form
  summary, or append a TODO-number continuation menu.
- `%CODEX_HOME%\q-personal-state` is a read-only, rebuildable mirror. If the
  command reports drift, list from the configured hub, repair with
  `q_base_command.py --audit --sync-runtime`, and rerun before claiming sync.
- Missing profile authority, malformed state, an unregistered exact command,
  or a stale foundational runtime is a blocked result. Do not fall back to an
  unrelated path or silently reinterpret the command.
- Whole-workflow stable/install-ready or foundational repair claims require
  `workflow_stability_suite.py --rounds 2 --check-only --strict --stdout`.
  Touched-file mirror equality alone uses targeted hashes; it does not claim
  whole-workflow readiness. Choose other checks via `references/testing-standard.md`.
- Use `scripts/q_workflow_manager.py status` as the quick read-only entry and
  `doctor --full` as the unified deep gate. Task mutation is a separate
  plan/apply transaction and requires explicit `--yes`.

## Core Principles

- Apply skills within the user's intent and current host instructions. Reuse
  existing authorization, infer routine reversible choices, and continue until
  the requested outcome is complete. A checklist is not a reason to ask again.
  When a real missing decision blocks an action, explain the exact boundary and
  continue useful independent work. Domain correctness and privacy still apply.

- Before drafting, exporting, or approving externally delivered text, verify
  its actual audience. Remove assistant or
  commissioner process narration; preserve reader-useful instructions, limits,
  safety and attribution. Check authoritative generators and final exports.
  Apply this check to the final exported content, not only its source;
  do not publish internal review notes as product copy.

- Use the smallest context that makes the next action safe, reversible, and
  recoverable.
- Keep `SKILL.md` as a router and short policy surface. Move detailed
  procedures, examples, rare cases, and historical guidance into references.
- Separate authority layers:
  - project facts and deliverables belong in the project repository;
  - reusable behavior belongs in skills;
  - cross-project routing belongs in the workflow hub;
  - runtime skill folders are loaded copies, not the only source of truth.
- Treat native agent features, scripts, MCP tools, and subagents as capability
  engines behind q-workflow's authority, safety, observability, and recovery
  gates.
- Prefer one primary skill plus one or two sidecar skills for complex work.
  Avoid skill fan-out unless an orchestration note explains why each skill is
  needed.
- Compose only the checks required by changed surfaces and intended claims.
  A task label alone does not activate research, expert fan-out, a full audit,
  or sedimentation. Keep exact commands and tiny edits on the micro path;
  preserve explicit domain, safety and release gates.
- For learning, training, design, visual creation, translation, and tool-path
  selection, do not promote imagined mechanisms into methods. Keep source
  roles, direct material inspection, contextual comparison, and hypotheses
  explicit; unsupported ideas may be explored only as unproved experiments.
- Record assumptions, validation gaps, changed files, sync gaps, and next
  actions in durable files before claiming a work round is complete.
- For long-running research/design work, keep one compact active authority
  pointer separate from the evidence archive. It names the governing
  specification, current stage, latest material user correction, one next
  artifact, and blocked actions. Raw research, historical reports, images, and
  binaries are evidence only; they cannot become executable by being newer or
  more detailed.
- For unattended work, check the system-volume write budget before creating or
  retrying heartbeats or subagents. A resource stop must persist before the
  automation mutation; repeated resource failure is a circuit-breaker state,
  not a reason to keep waking or emitting duplicate progress.
- Treat a real successful path as reusable operational evidence: record its
  selection key, required preconditions, result, and smallest recovery action;
  on recurrence, replay it before exploring alternatives. Do not replace a
  proven path with anonymous probes, generic retries, or a larger fallback tree
  unless its failure is observed and classified.
- For material work, keep the three independent axes explicit: work progress,
  integrity/freshness, and release posture. A local validation or cached Git
  tracking ref never proves remote freshness; use `remote-unproven` language
  until a successful fetch-based gate supplies evidence.
- Before material work becomes active, obtain a deterministic expert role plan
  from q-agent-roster. The primary role participates in the work plan; mapped
  reviewers/validators are gates, not the sole reason experts appear.
- When a request contains several independent items, keep a compact numbered
  action/TODO list and update each item as done, paused, blocked, or deferred.
- Before saying a work round is complete, run the bounded closure-ledger check:
  active focus, work item, matching TODOs, validation evidence, runtime mirrors,
  and residual risk must be reconciled or explicitly deferred.
- Consolidate at a meaningful handoff or after a repeated failure. One compact
  work-item checkpoint can hold decisions, review findings and validation
  receipts. Do not start another skill-update loop merely because a task ended.
- Do not store project-specific facts, customer/private data, credentials, or
  personal active-work details in public reusable skills.

## Lightweight Execution Contract

Use this default flow for normal implementation work:

```text
route -> plan -> edit -> validate -> review -> checkpoint
```

### Phase B Output

For a managed `visibility_latch: phase-b-required`, begin every user-visible
message with `小Q工作流 / <registered q-skill-id> / <Chinese current action>`.
The latch ends only on explicit close, pause, switch, or return to Phase A.
Read [Phase B preflight](references/phase-b-output.md) before first Phase B
output; retain its handoff validation and task/event binding requirements.

Keep each stage proportional:

- `route`: choose project, work item, primary skill, and risk tier.
- `plan`: make only the plan needed for the next safe segment.
- `edit`: keep changes scoped to the active work.
- `validate`: run task-matched checks or state why they are unavailable.
- `review`: inspect diffs, generated artifacts, source/runtime mirrors, or
  evidence probes as appropriate.
- `checkpoint`: update durable memory and commit when the checkpoint is
  meaningful.

The experimental YAML contract in `experiments/` can be validated with:

```powershell
python .\scripts\validate_experiments.py
```

## Context And Escalation

Use progressive context loading:

| Tier | Trigger | Action |
|---|---|---|
| Micro | Fixed command or stable answer | Avoid tool reads when the answer is known |
| Quick | Resume/status with clear target | Read routing state and one targeted status check |
| Project | Normal project work | Read targeted project state and relevant files |
| Deep | Overlapping/unclear dirty ownership, stale authority, contradictory, public, destructive, or cross-profile state | Inspect relevant diffs, decisions, handoff notes, and sources |
| Full | Broad audit or legacy detail | Read `references/full-guide.md` only after a reason is clear |

Load applicable instructions once; reuse them while unchanged. Keep tool output
bounded to findings and necessary evidence. Do not reopen full reports or
transcripts to restate status. See `references/adaptive-execution.md` for details.

Stop reading when the next action is clear and low risk. Inspect dirty changes
in the touched scope first; unrelated dirty files do not require a whole-repo
audit. Escalate when ownership overlaps, authority conflicts, a failure cannot
be localized, or an action adds publication, deletion, or data-exposure risk.
Required AGENTS/skill reads and task/event validation are not optional context.

## Safety And Portability

- Ask before destructive actions, credential handling, global configuration,
  publishing, public/GitHub sync, or unclear blast-radius operations.
- First check the newest user instruction and existing scope-specific approval.
  Do not ask again for the same already-authorized local action. Ask when the
  needed decision, target, candidate, or side-effect boundary is new or unclear.
  An answer or diagnosis request does not authorize implementation. A newer
  no-push/cancel instruction invalidates earlier approval for that action;
  model capability never expands authorization.
- Record local checkpoints when useful. Push/publish/public sync requires
  scope-specific user authorization, which may already be present in the task
  request. Complete authorized actions after review and validation; release need
  or recovery risk alone does not authorize publication.
- Use UTF-8 for Markdown, skill, prompt, and workflow files. Do not copy
  mojibake back into durable files.
- Treat third-party skills and public examples as idea references unless
  license compatibility and attribution are explicit.

## Evolution Guard

At a material task's start, compare already available model/tool evidence and
relevant workflow revisions with the last review, without a routine inventory
or network check. A new signal, repeated friction or a useful milestone lesson
should trigger `references/proactive-evolution.md`. Unchanged evidence and
micro/answer-only tasks stay on the normal path. Review proactively; make only
authorized, validated, recoverable changes. Record material review dispositions
only when record-writing is authorized; unchanged entry checks create no record.

When a platform capability overlaps local workflow behavior, do not delete the
local rule immediately. Use `references/workflow-evolution.md` to decide
whether to `use-native`, `wrap-native`, `keep-local`, `retire-local`, or
`watch`. Retire local behavior only after a realistic scenario proves the old
failure mode is still covered with equal or better authority, safety,
observability, recovery, and cost.

## Handoff

Before ending a substantial round:

- validate generated artifacts or changed skills where practical;
- update the active work item and project state;
- run targeted Git status and review relevant diffs;
- commit meaningful checkpoints locally;
- when reusable skills changed, verify source, runtime, workflow bootstrap, and
  applicable mirrors with file-list and hash checks; remote evidence is required
  for remote sync/rebuild/release claims, not for a clearly local-only change;
- record any deferred push, mirror sync, validation gap, or native-capability
  retirement decision.

The archived pre-router detail lives in `references/full-guide.md`.
