---
name: q-agent-roster
description: Use when defining, selecting, coordinating, or reviewing Xiao Q expert subagents or specialist passes, including expert self-improvement loops, research delegation, multi-agent review, handoff protocols, validation, and durable workflow sedimentation.
---

# Q Agent Roster

Delegate a bounded question or disjoint task when it adds useful independent
evidence or parallel progress. Roles assign responsibility, not headcount.

## Default path

1. For material managed work, retain `scripts/task_role_plan.py --task-class <class>`
   and the task's primary/review/validation fields. A mapped gate may be resolved
   as deferred with its reason for a local claim; it cannot waive an explicitly
   independent domain/release gate. Tiny work needs no formal role ceremony.
2. Select the role below; read `references/agent-registry.md` only for ambiguous
   aliases or the role's specialist contract. Inherit model/effort unless the
   user or a relevant contract requires otherwise.
3. For actual delegation use `workflows/dispatch-agent.md`. It contains the
   ordinary handoff contract; do not load every protocol reference first.
4. Integrate findings and stop at acceptance. Reuse the reviewer for its fixes.

| Role | Independent scope |
|---|---|
| Visual Arbiter (版衡) | Rendered layout, diagrams, PPT and component quality |
| Source Scout (寻源) | Current facts, source discovery, contradictory evidence |
| Pagewright (页匠) | HTML interaction, responsive layout, usable interfaces |
| Doc Architect (文构) | Document structure, clarity, reusable instructions |
| Code Auditor (码鉴) | Correctness, tests, regressions, implementation risk |
| Workflow Distiller (沉炼) | Rule scope, repeated failures, reusable mechanisms |
| Usability Validator (验用) | Cold start, installation, first-user success |

## Boundaries

- Follow user/host delegation rules. A direct independent-review request and
  applicable independent domain/release gates require real separate evidence;
  main-agent checks cannot be called independent. For ordinary local work,
  delegate only when the bounded benefit exceeds its overhead.
- Reviewers are read-only by default. Assign each writer disjoint paths and an
  output location; main integrates. No implicit publication or credential scope.
- One stable English/Chinese role label and the returned run handle establish
  identity. Do not invent personas, duplicate names in several fields, or spawn
  another agent solely to satisfy a form.
- Preserve scope-specific authorization; ask only when missing, revoked or
  exceeded. Record material review evidence once in the existing work item.

## Conditional detail

| Need | Read |
|---|---|
| Ambiguous local/independent/release decision | `references/auto-dispatch-policy.md` |
| Machine consumer, durable multi-stage handoff | `references/handoff-protocol.md` |
| Context/access ambiguity | `references/context-guardrails.md` |
| Model override | `references/model-routing.md` |
| Failed/disputed review | `workflows/multi-agent-review-loop.md` |
| New role | `workflows/create-expert.md` |
| Stable/promotion claim | `references/quality-gates.md` |
| Protocol regression | `references/validation-scenarios.md` |
| Reusable expert-method improvement actually requested | `references/expert-self-improvement.md` |

Using a subagent does not trigger a learning cycle, scorecard or skill update.
Close substantive findings with a fix, evidence or explicit disposition.
