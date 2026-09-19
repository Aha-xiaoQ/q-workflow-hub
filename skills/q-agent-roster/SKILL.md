---
name: q-agent-roster
description: Use when defining, selecting, coordinating, or reviewing Xiao Q expert subagents or specialist passes, including expert self-improvement loops, research delegation, multi-agent review, handoff protocols, validation, and durable workflow sedimentation.
---

# Q Agent Roster

Assign bounded expert work and integrate evidence. The main agent owns the
result. Roles are responsibilities, not a requirement to create many agents.

## Route Before Dispatch

1. For material work run `scripts/task_role_plan.py --task-class <class>`
   before entering active state. Tiny deterministic changes need no formal
   expert pass. A role plan does not override host restrictions on delegation.
2. Use `references/agent-registry.md` to select the stable role below. Direct
   user requests for an expert/specialist route here before execution.
3. Use `references/auto-dispatch-policy.md` to decide local check or real
   independent review. Actual delegation additionally uses
   `workflows/dispatch-agent.md` and `references/handoff-protocol.md`.
   Load each applicable instruction once, not for each follow-up.
4. Inherit model/effort by default. Read `references/model-routing.md` only
   when considering an explicit override. Never spawn just to change models.
5. Announce the stable role, bounded mission and authority before spawning;
   backfill the returned run identity. Continue useful independent main work.
6. Integrate evidence and finding dispositions. Reuse the same reviewer for its
   repairs; add another only for distinct required evidence. Stop when the
   requested result and applicable reviews pass.

## Stable Roles

Identity is checked against `references/expert-registry.json`; human contracts
and invocation aliases are in `references/agent-registry.md`.

| Role | Scope |
|---|---|
| Visual Arbiter (版衡) | Visual layout, diagrams, PPT and component review |
| Source Scout (寻源) | Source discovery, factual research and conflicting evidence |
| Pagewright (页匠) | HTML interfaces, dashboards and interactive previews |
| Doc Architect (文构) | Documents, plans, standards and clear structure |
| Code Auditor (码鉴) | Code, tests, regressions and implementation risk |
| Workflow Distiller (沉炼) | Workflow updates, repeated failures and reusable lessons |
| Usability Validator (验用) | First-user paths, installation and package usability |

Keep the English alias and Chinese codename visible. A platform nickname/id is
a run handle, never a new expert persona. New roles use
`workflows/create-expert.md`; do not invent one during dispatch.

## Review And Authority Boundaries

- Nontrivial public/release candidates and explicitly independent gates require
  real review before human handoff or publication. Main-agent checks are never
  called independent. Preserve domain-specific reviewer requirements.
- For ordinary local work, a disclosed local check may suffice when tiny,
  delegation is unavailable/prohibited, or no useful independent scope exists.
  This exception cannot pass an explicit independent release/domain gate.
- Reviewers are read-only unless assigned bounded write ownership. Parallel
  workers need disjoint owned paths; avoid multiple agents inspecting the same
  question. Respect user no-agent requests and all host delegation restrictions.
- Supply task/trace identity, goal, relevant source paths, allowed/forbidden
  actions, acceptance, evidence, stop condition and next owner. Preserve the
  selected protocol's required fields. Prefer this packet over full history.
- Preserve a material review and integration in the existing work item when
  compact; use separate files for bulky evidence or an explicit domain protocol.
  Keep real run identity, findings, decisions and validation traceable.
- Push/publish requires the user's scope-specific authorization and applicable
  review/freshness/privacy gates. Complete an already authorized delivery;
  do not ask again merely because review has finished.

## Load Specialized Detail Only When Needed

| Decision | Reference |
|---|---|
| Failed/disputed review | `workflows/multi-agent-review-loop.md` |
| Context isolation or action guardrails | `references/context-guardrails.md` |
| Packet/schema semantics | `references/agent-protocol-design.md` |
| User-visible state/cards | `references/output-protocol.md` |
| Scheduling architecture | `references/orchestration-model.md` |
| Stable/promotion claim | `references/quality-gates.md` |
| Roster regression | `references/validation-scenarios.md` |
| Repeated failure or validated new expert method | `references/expert-self-improvement.md` |

Using a subagent alone does not trigger another learning/research cycle.
Record `no durable update` when no reusable lesson emerged. For accepted P1/P2
findings, close with a fix/scenario or an explicit disposition. When the user
specifically challenges expert capability or repeated misses, retain external
calibration through q-research-discovery unless prohibited or unavailable.
