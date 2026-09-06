# Workflow Audit

Use this reference when Xiao Q asks for `体检`, `工作流体检`,
`workflow-audit`, or a full review of q-workflow architecture, shortcuts,
state routing, skill boundaries, sub-agent usage, cache stability, or rule
slimness.

## Purpose

Workflow audit is a structured architecture review, not a normal resume path.
It should find conflicts, duplication, unclear ownership, stale mirrors,
overloaded shortcuts, overgrown state files, and missing validation loops. The
output should be a durable report plus the smallest useful rule patches.

## Fast Path

Trigger aliases:

- `体检`
- `工作流体检`
- `workflow-audit`
- `审查工作流`

Default behavior:

1. Build a short `TASK-PACKET v1` when context pressure is high.
2. Read `references/testing-standard.md` when the audit involves validation, push/reclone, release, or repeated test misses. Run `scripts/workflow_audit.py` when local files are available. Treat it as
   the mechanical first pass for line counts, hashes, required routes,
   shortcut ambiguity, state bloat, TODO drift, protocol layering, and known
   source-copy drift.
3. Read only the routers and indexes needed for the audit first.
4. Use `rg`, file listings, hashes, and targeted headings before opening long
   logs or full state files.
5. Use one read-only sub-agent or local `沉炼/验用` pass when the task is broad
   enough to benefit from a second lens. When Xiao Q explicitly asks for
   experts, route through `q-agent-roster`, announce the dispatch card, and
   persist or integrate the expert reports before final handoff.
6. Write a dated report under the personal hub or local Codex reports folder.
7. Patch only high-confidence router/reference/help issues immediately; leave
   large migrations as explicit follow-up work.
8. Validate changed skills and record source/runtime/starter sync gaps.

Do not use workflow audit for micro commands such as `TODO`, `TOKEN`, exact
help, or a small deterministic edit.

## Authority Map

| Layer | Owns | Audit check |
|---|---|---|
| `q-workflow` | Entry routing, recovery, shortcut behavior, source/runtime authority, cache budget, workflow evolution | Router is concise; shortcuts are unambiguous; state source and mirrors are clear |
| `q-agent-roster` | Expert names, AGENT-TASK/REPORT contracts, role selection, delegation gates, usability expert | No duplicate dispatch schema; actual sub-agent use is bounded and evidenced |
| `q-skill-creation` | Skill quality standards, six hard parts, creation/update/review procedures | Stable output formats, tests, and failure iteration are present |
| Personal hub | Active work, TODO, paused work, skill sync inventory, cross-project routing | Hub is authoritative; runtime mirror is either fresh or marked stale |
| Project repos | Project facts, generated artifacts, validation reports, source scripts | Personal hub stores pointers, not project contents |
| Runtime mirrors | Installed copies for agent discovery | Mirrors do not become the only copy of durable behavior |

## Research-Derived Review Heuristics

External sources checked on 2026-06-20 point to six mechanisms that should
shape this audit:

1. **Prefer simple composable workflows before broader agent autonomy.**
   Workflow rules should stay predictable for well-defined tasks; use agentic
   flexibility only when the task needs open-ended decision making.
2. **Keep one orchestrator accountable.** Specialists can own bounded work, but
   the main agent owns routing, arbitration, validation, durable memory, and
   final user handoff.
3. **Separate short-term checkpoints from long-term stores.** Session recovery,
   work-item state, reusable skills, and project facts must not collapse into
   one large file.
4. **Treat prompts and skills like code.** Review changes, version them, test
   representative scenarios, and keep rollback paths visible.
5. **Make behavior observable.** Important workflow actions need traces,
   commands, reports, changed paths, screenshots, or validation outputs, not
   only an assistant claim.
6. **Keep cache prefixes stable.** Static routers and shared rules belong
   early; dynamic research, reports, logs, and sub-agent output should be late
   and file-backed.

## Standard Full Audit Flow

Use this fixed flow for `全面体检`, repeated workflow misses, or any audit where
Xiao Q asks for expert assistance:

1. Define scope: quick, full, promotion-readiness, or state-repair audit.
2. Announce and dispatch bounded experts through `q-agent-roster` before
   self-review when requested or when the audit covers nontrivial workflow
   changes. Default pair: `Workflow Distiller (沉炼)` for rule/ownership
   structure, and `Usability Validator (验用)` for real resume/TODO/user-path
   replay.
3. Read routers and authority maps first; avoid loading long state files until
   a finding needs them.
4. Run the mechanical audit script when available and store the report path.
5. Replay at least one historical defect and one current normal path. For
   `recorded-point-lock-resume`, replay: previous user checkpoint request ->
   previous assistant final checkpoint/tag/next action -> `ACTIVE_WORK.md` ->
   runtime mirror -> first resume response. Pass means the first response locks
   the recorded point and does not inspect repos, edit files, build, flash, or
   run hardware before explicit execution authorization. For
   closure defects, replay: original objective/id -> evidence -> TODO ->
   `ACTIVE_WORK.md` -> work item -> runtime mirror.
6. Classify findings as P0/P1/P2/P3, each with owner layer, evidence, impact,
   and recommendation.
7. Apply only high-confidence small patches. Defer large migrations, public
   sync, checker scripts, and schema changes unless Xiao Q explicitly asks.
8. Validate changed files with `diff --check`, targeted readback, and one
   realistic routing replay.
9. Run a bounded relevant closure-ledger check for the audit itself before
   handoff: the audit must not leave a completed TODO, stale `Current Focus`,
   or unsynchronized affected runtime mirror unless explicitly deferred.
10. Write the integration report with expert findings, accepted/rejected items,
    patches, validation, skipped surfaces, and next trigger.
## Audit Procedure

## Optimization And Slimming Standard Path

Use this path when `体检` also asks for workflow optimization, slimming, token
control, release preparation, or colleague/customer handoff readiness.

1. **Benchmark first.** Inspect benchmark summaries before full result rows. Use
   `workflow-benchmark` summary deltas when present, compare quality and
   stability before token cost, and mark token/cost as `not_measured` when
   telemetry is missing.
2. **Context and cost preflight.** Run `context_governor.py` or `TOKEN` when
   local telemetry is available. Treat high cache as healthy only when context
   pressure, uncached input, input growth, and output share are also controlled.
3. **Mechanical gates.** Run `workflow_audit.py --mode audit` and
   `workflow_audit.py --mode hygiene`; for promotion work also run
   `release_readiness.py --target team --stdout`.
4. **State slimming.** If `ACTIVE_WORK.md`, `TODO.md`, or `SKILL_SYNC.md` is
   bloated or stale, archive before editing, preserve recovery pointer/current
   focus/validation gaps/blockers, refresh the runtime mirror, and mark the hub
   copy as authoritative.
5. **Rule slimming.** Keep `SKILL.md` as a concise router. Move detailed,
   rare, dynamic, or task-specific guidance into references; merge duplicate
   ownership into the owning skill; do not remove safety, approval, recovery,
   encoding, or release gates to save tokens.
6. **Expert pass.** For broad optimization or release readiness, dispatch or
   locally replay `Workflow Distiller (沉炼)` and `Usability Validator (验用)`;
   record accepted, rejected, and deferred recommendations.
7. **Patch ladder.** Apply small high-confidence P0/P1/P2 routing, authority,
   mirror, and help fixes. Record P3 drift or larger migrations as follow-up;
   ask before wholesale sync, skill retirement, public sync, or pushes.
8. **Validation and report.** Run targeted readback, `diff --check`, encoding
   guard for Chinese-bearing files, relevant skill validation, and one realistic
   routing replay. The report should state quality delta, measured token delta,
   patches applied, skipped surfaces, remaining blockers, and the next trigger.

1. **Frame scope.** State whether this is a quick audit, full architecture
   audit, or promotion-readiness audit.
2. **Scan entry points.** Check `SKILL.md`, `agents/openai.yaml`, help text,
   shortcut aliases, and activation/risk tables.
   Start with `scripts/workflow_audit.py --output <report-path>` when available,
   then manually inspect only the findings and any user-specific scope.
3. **Scan authority and drift.** Compare source, runtime, starter/public copies
   by paths, hashes, and known sync notes. Do not assume runtime is truth.
4. **Scan responsibility boundaries.** Identify which skill owns each behavior:
   route/state/cache, agent dispatch, skill quality, project facts, visual
   review, research, code, or document generation.
5. **Scan rule quality.** Apply the six hard parts: decomposition, fixed
   output, root-cause prohibition, indexed disclosure, stability tests, and
   failure iteration.
6. **Scan cost and cache.** Find always-loaded rules that should move to
   references, broad reads, long state files, dynamic content in chat, and
   overloaded routers.
7. **Scan merge/extension points.** Classify each repeated rule as:
   - merge into an existing owner skill;
   - move from router to reference;
   - extract into a new skill only after repeated real use;
   - archive as a lesson or regression scenario;
   - leave as project-specific state.
8. **Scan validation.** Check whether real failures have a replay scenario,
   validation command, report, or durable lesson.
9. **Patch or defer.** Patch small high-confidence routing/help/protocol fixes.
   Defer large migrations, public sync, history pruning, and pushes unless Xiao
   Q explicitly asks.
10. **Report and checkpoint.** Write findings, patches, validation, skipped
   surfaces, and next actions.

## Fixed Report Shape

```text
Workflow Audit:
Date:
Scope:
Evidence:

Architecture map:

Findings:
P0/P1/P2/P3 | Area | Evidence | Impact | Recommendation

Conflicts and duplication:

Shortcut and routing review:

State and mirror review:

Sub-agent and loop review:

Skill quality review:

Merge and extension review:

Slimming candidates:

Patches applied:

Validation:
Test tier required/proven:

Deferred work:

Quick path:
```

## Boundaries

- `TASK-PACKET v1` is the parent-session cache bridge. It summarizes objective,
  truth paths, state, next actions, validation, and risks.
- `AGENT-TASK v2` is the sub-agent work contract. When both are used, embed
  only the relevant parts of the task packet into `AGENT-TASK v2.context_packet`.
- Do not create a second sub-agent protocol in q-workflow. Detailed expert
  names, report fields, and role selection belong in `q-agent-roster`.
- Do not let broad terms such as `运行` trigger workflow audit or fast mode by
  themselves. Treat them as fuzzy execution intent and use the surrounding task
  to decide.

## Pass Criteria

Workflow audit is successful when:

- the report identifies the authoritative files and mirrors checked;
- each major issue has an owner layer and recommendation;
- any immediate patches are validated;
- skipped surfaces are listed with a reason;
- the final answer gives the quick trigger to use next time.
