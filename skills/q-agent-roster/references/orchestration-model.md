# Orchestration Model

Use this file when designing or revising the overall multi-agent workflow.

## MCU-Inspired Mapping

| MCU concept | Agent workflow equivalent |
|---|---|
| Main controller | Main agent that owns user intent and final integration |
| Peripheral module | Expert agent with bounded capability and fixed interface |
| Bus | Handoff protocol shared across agents |
| Addressing | Expert name plus owned scope |
| Arbitration | Main agent decides priority, conflicts, and final acceptance |
| Interrupt | User correction, failed validation, or high-risk finding |
| DMA-like worker | Bounded subagent doing an isolated artifact task |
| Status register | Agent report status, risks, validation, and next owner |
| Memory protection unit | Context packet and tool/action restrictions |
| Trace buffer | Route decisions, report evidence, command output, and citations |

The concrete packet rules are in `agent-protocol-design.md`. Treat this file as
the scheduling/arbitration model and `handoff-protocol.md` as the user-facing
packet form.

## Scheduling Rules

- Single-owner task: use one expert; do not create coordination overhead.
- Subagent-as-tool: use when the main agent should keep control and only needs a
  bounded result, such as research notes, review findings, or a test summary.
- Phase handoff: use when a specialist should own the next phase and then
  return control, such as `Pagewright (页匠) -> Visual Arbiter (版衡) -> Workflow Distiller (沉炼)`.
- Independent slices: run multiple experts in parallel only when their scopes do
  not overlap.
- Quality-risk review: after nontrivial code/script, workflow/skill, setup,
  user-visible artifact, public/team handoff, or repeated user-found miss,
  schedule a read-only reviewer/validator or record why the review was
  deferred.
- Parallel efficiency: when research, install smoke testing, validation,
  read-only review, or disjoint file work can proceed independently, dispatch a
  bounded subagent while the main agent continues non-overlapping work.
- Review-after-build: builder finishes first, reviewer checks artifact second.
- Research-before-build: Source Scout (寻源) runs before implementation when direction, facts,
  tools, or platform choices are uncertain.
- Sedimentation-after-loop: Workflow Distiller (沉炼) runs after repeated corrections, missed quality
  gates, or a new reusable workflow pattern.

## Priority

1. Safety, privacy, credentials, destructive actions.
2. Correctness and user-visible artifact quality.
3. Source-of-truth recovery and validation.
4. Reusability and durable learning.
5. Polish and convenience.

## Arbitration

When experts disagree:

- Prefer source-of-truth evidence over preference.
- Prefer validation output over visual impression when the tool measures the
  same property accurately.
- Prefer the user's repeated feedback over default style rules.
- If both options are valid, choose the simpler one that fits the existing
  component/workflow system.

## Observability

- Record why an expert was selected, why other experts were deferred, and what
  context packet was passed.
- Record `trace_id`, `message_id`, `parent_id`, stable expert role, and
  platform execution handle when a real subagent is used.
- Preserve reproducible evidence: report text, changed paths, validation
  commands, screenshots, citations, or subagent ids.
- Treat missing trace evidence as a degraded validation result for nontrivial
  workflows.
