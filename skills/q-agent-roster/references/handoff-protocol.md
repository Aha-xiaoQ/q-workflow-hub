# Handoff Protocol

Use this protocol for prompts sent to expert agents and for reports returned to
the main agent. The goal is predictable integration, not verbose narration.

## Relationship To Q-OUTPUT

Use `references/output-protocol.md` for Xiao Q-visible status, completion,
blocker, and handoff cards. Use this file when agents exchange structured task
packets, reports, integration notes, identity updates, or durable parallel
coordination. Do not force `AGENT-TASK` / `AGENT-REPORT` onto ordinary user
conversation.


## Protocol Profiles

Choose the lightest profile that preserves reliability.

| Profile | Use when | Required shape |
|---|---|---|
| `compact` | Tiny local pass, deterministic review, no artifact, no risk escalation | Dispatch card + mission/result + `lesson_class: none` when no durable learning |
| `standard` | Nontrivial review, research, validation, or skill/workflow change | `AGENT-TASK v2` + `AGENT-REPORT v1` with evidence, next owner, and expert delta |
| `durable-parallel` | Real subagent, parallel fan-out, release guardrail, long evidence, or public/team candidate | Standard profile + objective contract + artifact/output namespace + capability check + structured error/cancel fields |

Escalate profile when the task adds write scope, public/team risk, bulky
evidence, multiple agents, unclear capabilities, or user-visible release impact.
Demote profile when the task is tiny and a full packet would add more overhead
than reliability.

## Expert Task Prompt

Use `AGENT-TASK v2` for new work. `AGENT-TASK v1` remains readable for older
notes.

In English-facing packets and reports, write expert names as English alias
first, Chinese codename second, for example `Usability Validator (验用)`.
Chinese codenames remain accepted input shortcuts, but English docs should not
introduce a role with the codename alone.
For Xiao Q and Chinese-user-facing output, the Chinese codename is mandatory,
not optional. Dispatch cards, report headings, review summaries, integration
notes, and final answers must show `English Alias (中文名)`, such as
`Workflow Distiller (沉炼)`. If an internal field only stores the English alias,
add a visible `Chinese name` field or adjacent parenthetical name before
handoff.

Protocol design rules live in `agent-protocol-design.md`. The friendly
handoff forms below carry the minimal `Q-AGENT-PACKET` fields needed for trace,
ownership, lifecycle, and integration; do not expand them into a verbose schema
unless a runner needs machine parsing.

```text
AGENT-TASK v2
protocol: Q-AGENT-PACKET
version: 1
packet_profile: <compact|standard|durable-parallel>
message_id: <unique within this work round>
trace_id: <shared across related agent messages>
parent_id: <previous message_id, or none for root>
kind: task
expert: <Visual Arbiter (版衡)|Source Scout (寻源)|Pagewright (页匠)|Doc Architect (文构)|Code Auditor (码鉴)|Workflow Distiller (沉炼)|Usability Validator (验用)>
platform_agent: <tool/type/nickname/id when known, or filled after spawn>
mode: <local-pass|subagent-as-tool|phase-handoff|parallel-worker>
method: <dispatch|review|validate|research|install-test|sediment|integrate>
lifecycle_state: <planned|dispatched|running>
mission: <one bounded outcome>
scope: <files/artifacts/questions owned by this expert>
context_packet: <source-of-truth paths, relevant excerpts, state, constraints>
allowed_actions: <read/research/edit/run/open/none, with scope>
forbidden_actions: <no-edit zones, no broad search, no destructive operations>
acceptance_criteria: <observable pass/fail checks>
stop_condition: <when to stop, including time/round/blocked thresholds>
constraints: <style, safety, time, output language, budget>
capability_check: <needed tools/data/access; known unavailable items; fallback>
capacity_decision: <none for local-pass, otherwise model-routing score/signals/main boundary/actual model/effort/cost posture/unchanged action authority/evidence/stop condition>
error_policy: <how to report blocked/partial/cancelled states>
improvement_target: <tiny expert capability this task can exercise, or none>
output_cap: <max sources/findings/words or file-output expectation>
output_format: AGENT-REPORT v1
output_target: <chat-only|file-report|artifact-manifest|changed-files>
artifact_output: <none|chat-only|file-path|changed-files|manifest>
next_owner: <main|expert name>
```

## Task Objective Contract

Every nontrivial expert task should define the objective in a way the expert
can execute without hidden chat context:

```text
objective:
  user_outcome: <what Xiao Q should be able to do or decide afterward>
  expert_mission: <one bounded outcome assigned to this expert>
  owned_scope: <files, artifacts, questions, or validation gates owned here>
  out_of_scope: <nearby work explicitly not owned by this expert>
  acceptance_criteria: <observable pass/fail checks>
  stop_condition: <time, round, evidence, blocker, or handoff limit>
  next_owner: <main|expert role>
```

Use `mission` for the one-line dispatch card and `objective` for the complete
task contract. If the objective cannot be written in this shape, do not spawn a
real subagent yet; narrow the task or ask Xiao Q.

## Artifact And File Output Contract

Default to `chat-only` for small reviews. Require a file or manifest when the
expert produces durable evidence, generated artifacts, long notes, screenshots,
logs, exports, or changed files.

```text
artifact_output:
  mode: <none|chat-only|file-path|changed-files|manifest>
  root: <workspace temp dir, report dir, or assigned output dir>
  naming: <descriptive kebab/snake name with date or trace id when useful>
  file_type: <md|json|csv|html|png|pptx|log|mixed>
  required_paths: <expected output paths, or "report exact paths returned">
  summary_required: <yes|no; compact chat summary still required for files>
  evidence_required: <commands, screenshots, citations, logs, or file paths>
```

Default file guidance:

- Research or source scan: compact chat table; use `*.md` only when notes are
  too long for the parent context.
- Review or critic pass: chat findings by severity; use `*.md` if the review is
  long, repeated, or part of promotion/release evidence.
- Validator replay: return command/log evidence in chat and put long logs,
  screenshots, CSVs, or exports under the assigned report directory.
- Install/usability run: use `*.md` report for first-run trace, blockers,
  friction taxonomy, score, and exact paths; put raw logs separately when long.
- Worker/build task: return changed files plus validation; use a manifest when
  more than one artifact type is produced.
- Workflow sedimentation: update only the assigned durable files, or return a
  proposed patch/report path when write ownership was not assigned.

Output target rules:

- Use chat-only for small local passes with no generated artifact and no more
  than five findings.
- Use a file report when findings are long, validation evidence is bulky,
  artifacts are produced, or the parent context should not carry details.
- Prefer project-local `reports/agents/<trace_id>/<expert>-<method>.md` when a
  project has a reports area; otherwise return the explicit path chosen by the
  main agent.
- For public/team/customer-facing artifact reviews, the main agent must ensure
  a durable report exists under that standard path before final handoff. If a
  real subagent returns chat-only, persist the report text and mark it as
  parent-persisted in the integration note.
- Final chat should carry status, top findings, `report_path`,
  `artifact_manifest`, validation summary, and next owner.

## User-Visible Dispatch Card

Use this stable, compact multi-line card in chat whenever a real subagent or
local expert pass is announced. The goal is that Xiao Q can immediately see
role, execution handle, mode, task, permissions, and boundaries. Keep one field
per line.

```text
Subagent start
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: <platform type>/<nickname-or-id>
Mode: <subagent-as-tool|phase-handoff|parallel-worker>
Mission: <one-line mission>
Permissions: <read-only|bounded-run|temp-write|owned-write>
Boundaries: <no push/publish/credentials/...>

Expert pass
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: main-thread/local-pass
Mode: local-pass
Mission: <one-line mission>
Permissions: <read-only|bounded-run>
Boundaries: <no platform subagent/no file edits/...>
Reason: <why no real subagent>

Subagent done
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: <platform type>/<nickname-or-id>
Result: <done|partial|blocked|failed>
Key findings: <short summary>
Next: <integrate|patch|ask|defer>
```

`Expert role` is the stable reusable q-workflow role. `English name` and `Chinese name` make the same role readable for both protocol use and Xiao Q memory; always show both in user-visible dispatch cards. `Run instance` is the platform
execution handle for this run. They must stay separate in both chat and packet
fields. Example: `Expert role=Workflow Distiller (沉炼)` is the reusable workflow role;
`Run instance=explorer/Aquinas/019...` is only this run's trace handle, not another
expert name.
Chinese-name visibility gate: before sending a user-visible dispatch card,
expert report summary, integration note, or final handoff, verify that every
expert role mention includes its Chinese codename. If any expert appears as
English-only, fix the display before handoff and log the omission as a protocol
finding when it affected user understanding.

Identity integrity gate: before the dispatch card is shown, verify that
`Expert role` is one of the stable roster entries or an explicitly documented
candidate. Do not present a newly invented human name as the expert. Put the
platform nickname/id only in `Run instance`, and put task-specific labels only
in `Mission` or `agent_slot`. If this gate fails, correct the mapping in chat
and record it under `protocol_findings` in the integration note.
For real platform subagents, the parent agent must backfill the final mapping. In multi-expert or parallel work this is one dispatch card and one backfill/update per real subagent; batching several experts into one card is invalid. If a spawn attempt fails or is retried after a platform/tool constraint, the retry needs its own fresh card before the next spawn call. The parent must backfill the final
`platform_agent` value after spawn if the initial task used `pending`. Send a
short follow-up message such as:
```text
IDENTITY-UPDATE
trace_id: <trace_id>
expert: <stable role>
platform_agent: <platform type>/<nickname>/<id>
report_requirement: Use this exact platform_agent in AGENT-REPORT v1; do not
report local-pass for this real subagent run.
```

If the returned report omits `platform_agent`, still says `local-pass` or
`pending`, or uses a different run handle for a real subagent, the main agent
must correct the trace in `INTEGRATION v1` and record the mismatch as a
protocol issue when material. When the mismatch is caused by a late or missing
identity update, the main agent should patch the expert handoff habit or
dispatch rule before closing the task.

## Expert Report

Every real platform subagent report must start with `AGENT-REPORT v1`. A useful
free-form review is not a protocol report unless it carries the packet identity,
status, evidence, ownership, and next-owner fields below. If the returned answer
is missing these fields, the main agent must either request a corrected report
or write an `INTEGRATION v1` note that marks `packet_complete: fail` and
normalizes the usable findings without hiding the protocol defect.

`AGENT-REPORT v1` is an internal machine packet, so the raw agent-to-agent
payload keeps that packet header as its first line. It is not itself a
user-visible Phase B update. If the parent exposes or summarizes the packet to
the user, the parent adds the required `小Q工作流 / <skill-id> / <action>` line
in the user-facing wrapper and preserves the raw packet unchanged in its
artifact or integration record.

```text
AGENT-REPORT v1
protocol: Q-AGENT-PACKET
version: 1
message_id: <unique report id>
trace_id: <same trace_id as task>
parent_id: <task message_id>
kind: report
packet_profile: <compact|standard|durable-parallel>
expert: <English Alias (中文名)>
platform_agent: <required; tool/type/nickname/id if a real subagent was used; local-pass only for local-pass>
status: <done|partial|blocked|failed|cancelled>
confidence: <high|medium|low>
lifecycle_state: <reported|blocked|cancelled>
actions: <what was inspected, created, or changed>
findings: <evidence-backed issues or conclusions>
changes: <files changed, if any>
validation: <checks run and result>
capacity_outcome: <not-applicable|sufficient|insufficient|over-provisioned>
report_path: <none|path to detailed report>
artifact_manifest: <none|paths/types/purpose of generated or reviewed artifacts>
evidence: <paths, citations, screenshots, logs, command results, or none>
risks: <remaining uncertainty or missed checks>
error_code: <none|blocked-capability|blocked-permission|invalid-scope|validation-failed|timeout|cancelled|other>
blocked_on: <none|user|permission|tool|source|file|subagent|external-state>
error: <structured blocker when status is blocked/failed/cancelled>
next: <recommended next owner/action>
lessons: <candidate durable lessons, if any>
lesson_class: <none|task-local|expert-profile|workflow-rule|validation-scenario|source-registry>
delta_evidence: <0-3 evidence bullets supporting or rejecting a reusable lesson>
promotion_decision: <promote|experimental|defer|discard|none>
context_used: <which packet/files/sources mattered>
```

For chat readability, use one field per line and keep long findings under
numbered bullets. For durable reports, use this fixed section order:

```text
AGENT-REPORT v1
protocol: Q-AGENT-PACKET
version: 1
message_id: <report id>
trace_id: <trace id>
parent_id: <task id>
kind: report
packet_profile: <compact|standard|durable-parallel>
expert: <stable q-workflow role>
platform_agent: <platform type/nickname/id, or local-pass only for local pass>
status: <done|partial|blocked|failed|cancelled>
confidence: <high|medium|low>
lifecycle_state: reported

## Mission
<one bounded mission and owned scope>

## Actions
<what was inspected, run, created, or changed>

## Findings
1. severity: <P0|P1|P2|P3>
   item: <issue or conclusion>
   evidence: <file/path/command/source>
   recommendation: <fix or next action>

## Changes
<none|changed files owned by this expert>

## Validation
<checks run, result, and evidence path/log, or explicit not-run reason>

capacity_outcome: <not-applicable|sufficient|insufficient|over-provisioned>

## Artifacts
report_path: <none|path>
artifact_manifest: <none|paths/types/purpose>

## Risks
confidence: <high|medium|low>
<remaining uncertainty and missed checks>

## Next
next_owner: <main|expert role>
next_action: <integrate|patch|ask|defer>

## Lessons
<candidate durable rules, or none>

## Expert Delta
practice_target: <capability exercised, or none>
delta_evidence: <0-3 evidence bullets>
lesson_class: <none|task-local|expert-profile|workflow-rule|validation-scenario|source-registry>
promotion_decision: <promote|experimental|defer|discard|none>
validation: <smallest readback/scenario/check, or not-run reason>
next_trigger: <when to revisit, or none>

## Context Used
<paths/sources/packet fields that mattered>
```

For artifact-producing or artifact-reviewing tasks, `validation` should name the
command/check, result, and supporting path/citation/screenshot/log when
available. Do not write `validated` without replayable evidence or a stated
reason why evidence is unavailable.

## Parallel Coordination Contract

When multiple agents run under one `trace_id`, each agent must receive a
disjoint `owned_scope` and an assigned output namespace before it starts.

```text
parallel_contract:
  trace_id: <shared work round id>
  agent_slot: <short unique slot, such as usability-validator-audit or doc-architect-docs>
  owned_scope: <files/questions/artifacts this agent owns>
  no_touch_scope: <files/questions/artifacts owned by others>
  output_namespace: <reports/agents/<trace_id>/<agent_slot>/ or chat-only>
  merge_owner: main
  conflict_rule: <report conflict; do not overwrite; main arbitrates>
```

Rules:

- Read-only reviewers may inspect overlapping artifacts, but their findings
  must be separated by `agent_slot`.
- Write-capable workers must never share the same file or artifact path unless
  the main agent explicitly serializes the handoff.
- File reports, logs, screenshots, and manifests must be written under the
  assigned `output_namespace`.
- If an expert discovers overlap with another agent's scope, it must stop that
  part, report the conflict, and let the main agent arbitrate.
- The main agent is the only merge owner. Experts may recommend integration but
  cannot close the user task or push/publish artifacts.

## Integration Note

Use this shape when the main agent merges multiple expert outputs:

```text
INTEGRATION v1
protocol: Q-AGENT-PACKET
version: 1
message_id: <unique integration id>
trace_id: <same trace_id as task/report group>
parent_id: <latest report or task message_id>
kind: integration
task: <user goal>
experts_used: <English Alias (中文名) entries>
platform_agents: <tool/type/nickname/id mapping, or local-pass only; keep separate from expert role names>
route_decisions: <why each English Alias (中文名) expert/mode was selected or deferred>
accepted: <findings or changes integrated>
rejected_or_deferred: <items and reason>
validation: <final checks>
durable_updates: <skills/state/docs updated>
protocol_findings: <packet/profile/identity/capability issues, or none>
trace: <subagent ids, report paths, commands, or citations when relevant>
user_handoff: <short final summary>
```

For any integration triggered by Xiao Q feedback, include a short
`process_lesson` field or paragraph that names what the expert/process should do
better next time and where that durable rule was updated.

## Distance From Chat

- Keep facts tied to files, citations, screenshots, exports, or command output.
- Do not depend on hidden chat memory for anything the next agent must know.
- Treat a durable `TASK-PACKET v1` from the owning workflow or project as the
  parent-session cache and recovery bridge, not as a replacement for this
  handoff protocol. When a task
  packet exists, copy only the fields needed for the expert into
  `AGENT-TASK v2.context_packet`, then keep `allowed_actions`,
  `forbidden_actions`, `acceptance_criteria`, and `output_cap` at the
  top level.
- If an expert finds a reusable rule, send it to `Workflow Distiller (沉炼)` or record it in the
  appropriate skill/workflow file before closing.
- Pass only the context needed for the expert's scope. Keep noisy exploration,
  logs, long source files, and irrelevant chat out of the parent context unless
  the main agent must inspect them.
- Keep `allowed_actions`, `forbidden_actions`, and `acceptance_criteria` as
  top-level task fields. The context packet can mention related constraints, but
  these three fields should not be buried inside it.
- Use `output_cap` for research, usability, and reviewer passes. This is a
  cache-stability guardrail, not a quality limit: the expert should preserve
  evidence by path/citation and return only the parts needed for arbitration.
- When a real platform subagent is used, record the q-workflow expert role and
  the platform execution handle separately. The expert role is stable workflow
  semantics; the platform nickname/id is trace evidence for this run.
- A real subagent report must not use `local-pass` as its platform handle. If
  the parent only learned the nickname/id after dispatch, it should send the
  identity update before waiting for the report.
- A real subagent report that omits `platform_agent` is still a trace defect.
  The parent should not treat a missing field as equivalent to a valid
  identity update.
