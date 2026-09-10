---
name: q-agent-roster
description: Use when defining, selecting, coordinating, or reviewing Xiao Q expert subagents or specialist passes, including expert self-improvement loops, research delegation, multi-agent review, handoff protocols, validation, and durable workflow sedimentation.
---

# Q Agent Roster

Use this skill to turn Xiao Q's expert-agent idea into a repeatable dispatch
system. The main agent remains accountable for the final answer; expert agents
or local specialist passes provide bounded review, research, creation, or
sedimentation.

Expert identity is machine-checked from `references/expert-registry.json`.
`references/agent-registry.md` owns the human-readable role contracts, but its
English aliases and Chinese codenames must match the JSON registry exactly.

## Default Flow

1. Classify the task and success criteria.
2. For every material task, run `scripts/task_role_plan.py --task-class <class>`
   before work enters `active`. The emitted primary owner is a work role, not
   merely a late reviewer; the main agent remains integration owner. `tiny` is
   the only deterministic exemption.
3. Select one primary expert and optional reviewers from
   `references/agent-registry.md`. If no existing role owns a recurring or
   high-value task class, read `workflows/create-expert.md` before proposing a
   new expert.
4. Use `references/auto-dispatch-policy.md` to choose local pass, real
   platform subagent, ask-before-spawn, or deny.
5. When a real subagent is justified, read `references/model-routing.md` before
   choosing its model and reasoning effort. This adapts child-agent capacity;
   it never claims to switch the already-running main model.
6. Read `workflows/dispatch-agent.md` before actual delegation or parallel
   subagent work.
7. Use `references/output-protocol.md` for Xiao Q-visible state, status, done,
   blocked, and handoff cards; use `references/handoff-protocol.md` for all
   agent prompts, reports, and integration notes.
8. For review, correction, or repeated failure, use
   `workflows/multi-agent-review-loop.md`.
9. For system-level scheduling, priority, or MCU-style bus/arbitration design,
   use `references/orchestration-model.md`.
10. For context isolation, tool/action limits, or guardrails, read
   `references/context-guardrails.md`.
11. Before changing agent packet fields, trace fields, or multi-agent protocol
   semantics, read `references/agent-protocol-design.md`.
12. Before calling a new or changed workflow stable, check
   `references/quality-gates.md`.
13. For forward tests or smoke tests, use `references/validation-scenarios.md`.
14. For new expert admission, use `workflows/create-expert.md` and keep the
   role `candidate` until validation proves it should become `pilot` or `stable`.

## Activation Guard

If Xiao Q names an expert, asks for a specialist, or frames the task as a
subagent/expert workflow, q-agent-roster must fire before ordinary execution.
This includes indirect phrases such as `安装专员`, `测试专员`, `评审专家`,
`代码审查专家`, `HTML 专家`, `文档专家`, `沉淀专家`, `子agent`, or
`让专家来测一下`. Do not start the task as a generic main-agent action and only
add the roster afterward.

Before acting, run this quick self-check:

- Did the user ask for a named expert, specialist, reviewer, tester, or
  subagent?
- Which stable q-workflow expert owns that role?
- Is this a local specialist pass or a real platform subagent?
- If real subagent: has Xiao Q seen the role/type/nickname/id/mission mapping?
- If local pass: has Xiao Q been told no separate platform subagent is running?
- Does the work create self-review risk or a parallel opportunity even if Xiao
  Q did not explicitly name a subagent?

## Expert Roster

- `Visual Arbiter (版衡)`: PPT, diagram, visual alignment, grid, connector, and component-library
  review.
- `Source Scout (寻源)`: research discovery, source strategy, citation evidence, and direction
  planning.
- `Pagewright (页匠)`: HTML interfaces, HTML-native decks, dashboards, visual systems, and
  interactive previews.
- `Doc Architect (文构)`: documents, reports, structured plans, standards, and reusable written
  outputs.
- `Code Auditor (码鉴)`: code review, implementation risk, tests, maintainability, and
  regression detection.
- `Workflow Distiller (沉炼)`: retrospectives, skill updates, workflow learning, loop engineering, and
  durable feedback capture.
- `Usability Validator (验用)`: first-time user testing, skill/package usability, onboarding friction,
  missing tool/description checks, and promotion readiness review.

Read `references/agent-registry.md` for each expert's profile, trigger,
required inputs, fixed output, and anti-patterns.

## Delegation Rules

- Distinguish a preferred independent review for ordinary local work from an
  explicitly required independent domain/release gate. Host restrictions and
  the user's no-agent request always govern dispatch. For ordinary local work,
  if delegation is prohibited, unavailable, or has no bounded independent scope
  alongside useful main-agent work, run and disclose a local check; do not call
  it independent. This exception does not pass an explicit independent quality
  gate or authorize publication; keep that specific claim pending.

- Use actual subagents when Xiao Q explicitly asks for subagents, delegation, or
  parallel agent work, and also for automatic quality-risk review or parallel
  independent work when `auto-dispatch-policy.md` says the scope is bounded and
  safe. Otherwise, run a local specialist pass using the same profile.
- If the work creates or changes a nontrivial user-visible artifact, reusable
  skill/workflow rule, setup/install path, public package, or GitHub-bound
  release candidate, do not ask Xiao Q for final human review until the
  relevant expert reviewer or real subagent has reviewed the candidate and the
  main agent has integrated or explicitly deferred each finding.
- Do not push, publish, release, upload, or claim an explicitly gated independent
  acceptance after only main-agent self-review. Ordinary local completion may
  use the disclosed exception above. For GitHub-bound changes, the required order is:
  produce candidate, run expert/subagent review, patch and validate, present the
  review summary to Xiao Q, wait for Xiao Q's explicit approval, then push.
- Before or immediately after spawning a real platform subagent, tell Xiao Q the
  visible mapping with the standard dispatch card from
  `references/auto-dispatch-policy.md`. Separate `Expert role` from `Run instance`:
  `Expert role` is the stable q-workflow contract, while `Run instance` is only the
  platform type/nickname/id for this run. This keeps the loop auditable and
  prevents the platform nickname from looking like a second expert name. When announcing an expert, show both the English alias and Chinese codename so the role is memorable and still protocol-stable.
- Do not spawn multiple agents to inspect the same unresolved question. Split by
  ownership: research, visual review, code review, documentation, or workflow
  synthesis.
- Give each expert a bounded task, source-of-truth files, context packet,
  allowed actions, acceptance criteria, output format, next-owner expectation,
  and the lightest protocol profile that preserves traceability.
- The main agent arbitrates disagreements, integrates results, validates the
  artifact, and records reusable lessons in the right durable layer.
- Distinguish q-workflow expert roles from platform nicknames. Roles such as
  `Usability Validator (验用)` and `Code Auditor (码鉴)` are the stable skill contract; platform names such as
  `worker`, `explorer`, or an auto nickname are execution handles and may change
  between runs.
- Do not invent a one-off expert persona, Chinese name, or English alias for a
  single dispatch. If the task fits an existing role, use that stable role and
  put task-specific wording in `Mission` or `agent_slot`. If a new memorable
  name seems useful, treat it as a candidate idea under `workflows/create-expert.md`,
  not as the expert for the current run.

## Escalation Map

| Situation | Default expert | Optional reviewer |
|---|---|---|
| PPT or diagram artifact | Visual Arbiter (版衡) | Workflow Distiller (沉炼) |
| Research or direction planning | Source Scout (寻源) | Doc Architect (文构) |
| HTML page, local app, or HTML PPT | Pagewright (页匠) | Visual Arbiter (版衡) |
| Report, plan, TODO, or standard | Doc Architect (文构) | Workflow Distiller (沉炼) |
| Code edit or bug risk | Code Auditor (码鉴) | Workflow Distiller (沉炼) |
| Skill/package before sharing with colleagues | Usability Validator (验用) | Workflow Distiller (沉炼) |
| Repeated feedback loop or skill update | Workflow Distiller (沉炼) | relevant domain expert |

## Durable Learning

After a material expert-agent workflow, write down:

- What was delegated and why.
- Which expert profile worked or failed.
- Which handoff field was missing or noisy.
- What validation caught or missed.
- What should be patched into skills, project state, or personal preferences.

Use `Workflow Distiller (沉炼)` for this step when the task had repeated user feedback, hidden
quality misses, or a new reusable rule.

## Expert Self-Improvement

Every material expert pass should solve the current task and, with low overhead,
check whether the task produced a reusable expert delta. Use
`references/expert-self-improvement.md` when the run involved research,
subagents, repeated feedback, nontrivial skill/workflow changes, or a new review
method. The default answer can be `no durable update`; promote only
validated lessons to expert profiles, workflow rules, validation scenarios, or
source registries.

When Xiao Q challenges whether experts improved, reports repeated misses, or
asks how expert capability should grow, treat external calibration as required
unless networking is blocked or Xiao Q explicitly says not to browse. Use
q-research-discovery / Source Scout first, then decide the smallest durable
expert delta. Accepted P1/P2 expert findings must close with a capability ledger
entry, validation scenario, rule/profile patch, or an explicit no-upgrade reason.
