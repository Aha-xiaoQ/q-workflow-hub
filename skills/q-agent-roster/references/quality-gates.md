# Quality Gates

Use this file before calling an expert workflow stable or after a repeated miss.

## Six-Gate Review

```text
Area | Pass? | Evidence | Gap | Patch
Task decomposition |  |  |  |
Fixed output format |  |  |  |
Surface-fix prohibition |  |  |  |
Indexed progressive disclosure |  |  |  |
Stability test |  |  |  |
Failure iteration |  |  |  |
```

## Agent-Specific Stability Checks

- Visual Arbiter (版衡): catches centering, overflow, connector, grid, label, and readability defects before Xiao Q points them out.
- Source Scout (寻源): distinguishes primary sources, freshness, contradictions, source quality, and decision impact.
- Pagewright (页匠): produces the usable experience first and verifies responsive render quality, navigation, connector clearance, and latest-output screenshots.
- Doc Architect (文构): outputs reusable fixed structure rather than polished loose prose.
- Code Auditor (码鉴): leads with file/line findings, behavioral risk, and test evidence.
- Workflow Distiller (沉炼): patches the durable layer instead of only summarizing the mistake.
- Usability Validator (验用): tests whether a new user can find the entry point, supply inputs, run the documented path, recover from errors, and trust the package without chat history.

## Dispatch Stability Checks

- Activation: Did a direct expert/specialist/subagent request trigger q-agent-roster before ordinary execution?
- Auto-dispatch: Did the workflow classify local-pass, real subagent, ask-before-spawn, or deny using `auto-dispatch-policy.md`?
- Protocol profile fit: Did the task use `compact`, `standard`, or `durable-parallel` instead of applying a heavy packet to every small pass?
- Self-review risk: If the main agent created a nontrivial artifact, code/script change, workflow/skill rule, setup path, public/team handoff, or user-visible output, was an independent reviewer/validator scheduled or was a deferral reason recorded?
- Parallel opportunity: Did the workflow check whether independent research, validation, read-only review, install smoke testing, or disjoint file work could run while the main agent continued useful non-overlapping work?
- Mode fit: Did the workflow choose local pass, subagent-as-tool, phase handoff, or parallel worker for an explicit reason?
- Packet identity: Did the handoff include protocol, version, message id, trace id, parent id, kind, stable expert role, and platform execution handle?
- Bilingual role naming: Did every user-visible expert dispatch show both `English name` and `Chinese name` in addition to `Expert role` and `Run instance`?
- Capability check: Did real subagent or validator tasks state required tools, data, access, unavailable capabilities, and fallback before work started?
- Context packet: Did each expert receive only the source-of-truth and state needed for its scope?
- Guardrails: Were allowed and forbidden actions explicit before delegation?
- Acceptance criteria: Could the expert and main agent tell what passing means?
- Task objective: Did the task include user outcome, expert mission, owned scope, out-of-scope, acceptance criteria, stop condition, and next owner?
- Output target: Did the task say chat-only, file report, artifact manifest, or changed files, and did the report include `report_path`, `artifact_manifest`, evidence, validation summary, and next owner when applicable?
- Structured blocker: Did partial/blocked/failed/cancelled reports include `error_code`, `blocked_on`, confidence, and next owner?
- Trace: Are route decisions, reports, validation, and durable updates replayable from files, command output, citations, or subagent ids?
- Identity mapping: If a real platform subagent was used, did Xiao Q see the standardized dispatch card with `Expert role`, `English name`, `Chinese name`, `Run instance`, `Mode`, `Mission`, `Permissions`, and `Boundaries`?
- Identity backfill: If the task was dispatched with `platform_agent=pending`, did the main agent send the actual platform type/nickname/id back to the subagent before accepting `AGENT-REPORT v1`?
- Report identity: Did `AGENT-REPORT v1` include the exact real `platform_agent`, rather than omitting it or falling back to `local-pass`?
- Report shape: Did the result literally use `AGENT-REPORT v1` or an assigned file report with the fixed sections, instead of only a helpful free-form answer?
- Scorecard: Did material expert runs record trigger match, packet completeness, independence value, usefulness, overhead, visible mapping, and next policy patch?
- Scope safety: For real subagents, were review passes read-only by default and write-capable passes limited to disjoint owned scopes?
- Parallel safety: If multiple agents ran under one trace, did each have an `agent_slot`, disjoint write scope, no-touch scope, and separate output namespace?
- Review-before-human-review: Before asking Xiao Q for final subjective review of a nontrivial artifact, skill/workflow rule, setup flow, or release candidate, did the mapped expert/subagent review run and did the main agent integrate or explicitly defer each finding?
- Approval-before-push: Before any `push`, publish, release, external upload, or public package sync, did Xiao Q explicitly approve the exact candidate after local validation and expert review summary were shown?
- Expert self-improvement: Did each material expert run name a practice target, capture only delta evidence, classify the lesson, and either promote it with validation or explicitly record `no durable update`?
- New expert admission: Before adding a new expert, did the workflow prove the gap is recurring or high-value, reject existing-role coverage with reasons, define the role contract, assign maturity, and add a validation scenario?

## Indexed Progressive Disclosure

- Task only needs role choice: read `SKILL.md` and `references/agent-registry.md`.
- Task needs actual delegation: add `workflows/dispatch-agent.md`, `references/context-guardrails.md`, and `references/handoff-protocol.md`.
- Task has repeated quality misses: add `workflows/multi-agent-review-loop.md` and `references/quality-gates.md`.
- Task changes protocol fields or trace semantics: add `references/agent-protocol-design.md`.
- Task is validation or regression: add `references/validation-scenarios.md`.

Do not load learning logs during ordinary dispatch; use them only for audits, summary/sedimentation, or future skill updates.

## Regression Capture

When a defect repeats:

1. Record the symptom and exact artifact.
2. Identify the generator, helper, prompt, missing source, or validation gap.
3. Add a check or workflow field that would have exposed it.
4. Re-run the failed scenario or a smaller representative case.
5. Note residual risk and next trigger.

## Stable Enough

An expert workflow is stable enough for regular use only when:

- A future agent can choose the right expert from `SKILL.md` alone.
- The expert has a fixed input and output shape.
- At least one realistic scenario has been exercised.
- Failures have a defined path back to skill, project state, or profile.
- Mode choice, packet profile, context packet, capability check, allowed actions, acceptance criteria, output target, and trace evidence are present for nontrivial delegation.
- Promotion candidates have at least one Usability Validator (验用) pass or an explicitly recorded reason why first-user testing was deferred.
- Usability Validator (验用) promotion decisions use explicit levels: `not-ready`, `pilot-ready`, `team-ready`, or `public-ready`, with blocking issues overriding numeric score.
