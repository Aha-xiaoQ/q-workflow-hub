# Context And Guardrails

Use this file before delegating to a real subagent or simulating a specialist
pass on a nontrivial task.

## Mode Boundary

| Mode | Use when | Parent role | Return |
|---|---|---|---|
| Local pass | The main agent can apply the expert lens without context risk | Acts directly | Short note or final answer |
| Subagent-as-tool | A bounded independent result is useful but the main agent keeps control | Defines packet and integrates | Summary, findings, or artifact slice |
| Phase handoff | A specialist owns the next phase before returning control | Schedules and validates | Phase report plus next owner |
| Parallel worker | Scopes are independent and non-overlapping | Assigns ownership and arbitrates | Separate reports merged by main |

## Context Packet

Prefer this shape instead of passing broad chat history:

```text
context_packet:
  goal: <user-visible outcome>
  source_of_truth: <paths, exports, links, citations, or feedback>
  current_state: <what is already done and what is unresolved>
  owned_scope: <files/sections/questions this expert owns>
  no_edit_zones: <paths or behavior not to modify>
  constraints: <style, safety, time, output language, budget>
  output_target: <chat-only|file-report|artifact-manifest|changed-files>
  return_contract: <AGENT-REPORT v1 fields expected>
```

Keep `allowed_actions`, `forbidden_actions`, and `acceptance_criteria` as
top-level `AGENT-TASK v2` fields so the main agent can scan permissions and pass
conditions without opening the context packet. Keep `stop_condition` and
`output_target` visible in the task or context packet so the expert knows when
to stop and whether durable files are expected.

## Cache-Aware Expert Output

When the main session has high context pressure or unstable cache hit rates,
expert prompts should include explicit output caps. Prefer a compact report that
the main agent can integrate without copying long dynamic content forward.

Default caps:

- `Source Scout (寻源)`: 4-6 sources, 5-8 mechanisms or findings, decision implications, and
  next query/action. Avoid long source excerpts.
- `Usability Validator (验用)`: first-run trace, blockers, top friction points, score, and ordered
  fixes. Put exhaustive notes in a file when available.
- `Visual Arbiter (版衡)`: slide/location findings, root cause, patch plan, validation needed.
  Avoid restating the whole deck narrative.
- `Workflow Distiller (沉炼)`: only reusable lessons with target layer and validation case; no broad
  recap unless the user asked for a summary.

If an expert needs more room, ask it to return a file path or artifact path plus
a compact summary. The parent context should carry the path, score, blockers,
and next action, not the whole report.

## Expert Guardrails

- `Visual Arbiter (版衡)`: read-only by default. It may propose generator/component patches, but
  should not edit the artifact unless explicitly assigned repair ownership.
- `Source Scout (寻源)`: research-first. It may browse or cite sources when the task requires
  current or niche information; it should not implement artifacts during the
  same pass.
- `Pagewright (页匠)`: edit-capable only for assigned HTML/UI files or generated assets; it
  should return preview path, viewport checks, and visual risks.
- `Doc Architect (文构)`: edit-capable only for assigned docs/plans/specs; it should preserve a
  fixed reusable structure.
- `Code Auditor (码鉴)`: read-only by default. It may patch code only when explicitly assigned
  a bounded fix and file ownership.
- `Workflow Distiller (沉炼)`: may update skills, workflow notes, or state only when the lesson is
  reusable and the target layer is named.
- `Usability Validator (验用)`: read-only by default. It should run or simulate only the documented
  first-user path, report missing tools/docs/prompts, and avoid using hidden
  maintainer context unless the test explicitly asks for expert recovery.

## Guardrail Questions

Ask these before delegation:

1. What can this expert do that the main agent should not spend context on?
2. What exact context does the expert need, and what should be filtered out?
3. What actions are allowed, and what actions require main-agent approval?
4. What observable result proves the expert succeeded?
5. What evidence should be kept so the route can be replayed later?
6. What output cap prevents this expert from bloating the parent context?

## Failure Signals

- The expert asks for broad missing context that should have been in the packet.
- The report cannot be integrated because output fields are missing.
- The expert returns a long narrative when a source table, findings list, score,
  and next action would have been enough.
- A reviewer edits files without ownership.
- A builder reviews itself on a user-visible artifact without independent pass.
- The main agent cannot explain why a mode or expert was chosen.
