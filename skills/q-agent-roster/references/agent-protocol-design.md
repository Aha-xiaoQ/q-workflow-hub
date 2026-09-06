# Agent Protocol Design

Use this reference when changing `AGENT-TASK`, `AGENT-REPORT`, or
multi-agent coordination rules. The protocol should stay small enough to type
and scan, but structured enough that the main agent can route, trace, validate,
and integrate several experts without relying on chat memory.

## Research Anchors

Learn mechanisms, not surface syntax:

- JSON-RPC: small envelope, request id, request/response/error separation.
- MCP: base protocol plus lifecycle, capability negotiation, and session
  boundaries.
- CloudEvents: common event envelope with id, source, type, version, time, and
  data content.
- W3C Trace Context and OpenTelemetry: trace id, parent/span relationship, and
  context propagation across components.
- FIPA ACL: communicative act, sender/receiver, content, protocol, and
  conversation control fields.


## Protocol Optimization Rules

These rules keep the expert bus reliable without turning it into a heavy schema.

1. **Envelope stays small.** Keep packet identity, ownership, lifecycle,
   permissions, and output contract at the top level.
2. **Profile before payload.** Use `compact`, `standard`, or `durable-parallel`
   so tiny tasks do not pay the cost of release-grade handoff packets.
3. **Capability check before work.** For real subagents and validators, state
   required tools, data, network, filesystem, and write access before dispatch;
   report unavailable capabilities as structured blockers.
4. **Errors are routable.** Use `error_code` and `blocked_on` so the main agent
   can decide whether to retry, ask Xiao Q, branch around the blocker, or defer.
5. **Trace before prose.** Every material report must be replayable from ids,
   file paths, commands, citations, screenshots, logs, or explicit not-run
   reasons.
6. **Human readability wins unless automation needs more.** Do not move to a
   strict JSON schema until a runner or validator needs machine parsing.

## Q-Agent Packet Principles

1. **One packet, one owner.** Each task packet has exactly one primary expert
   owner and one next owner.
2. **Stable role, variable execution handle.** `expert` is q-workflow semantics;
   `platform_agent` is trace evidence for the current run.
3. **Correlate everything.** Every task, report, and integration note carries
   `message_id` and `trace_id`; replies also carry `parent_id`.
4. **Separate intent from payload.** `method` or `mission` says what kind of
   work this is; `payload` or `context_packet` carries bounded inputs.
5. **Make permissions scannable.** Allowed and forbidden actions are top-level
   fields, never buried inside prose.
6. **Prefer explicit lifecycle.** Use `planned -> dispatched -> running ->
   reported -> integrated -> closed`, with `blocked` and `cancelled` as visible
   exits.
7. **Errors are first-class.** A failed or partial expert pass returns a
   structured blocker, evidence, and next action instead of a narrative apology.
8. **Extensions are optional.** Add specialist fields under `extensions` so the
   base packet remains readable.

## Minimal Packet Fields

For ordinary use, these fields are mandatory:

```text
protocol: Q-AGENT-PACKET
version: 1
message_id: <unique within this work round>
trace_id: <shared across related agent messages>
parent_id: <previous message_id, or none for root>
kind: <task|report|integration|event>
expert: <stable q-workflow role>
platform_agent: <tool/type/nickname/id or local-pass>
method: <dispatch|review|validate|research|install-test|sediment|integrate>
lifecycle_state: <planned|dispatched|running|reported|integrated|closed|blocked|cancelled>
source: <main|expert role>
target: <expert role|main>
mission: <one bounded outcome>
scope: <owned files/artifacts/questions>
context_packet: <bounded source-of-truth and state>
capability_check: <needed tools/data/access and fallback>
allowed_actions: <top-level permissions>
forbidden_actions: <top-level no-go zones>
acceptance_criteria: <observable pass/fail checks>
output_format: <expected return contract>
next_owner: <main|expert role>
```

## Optional Fields

Use only when needed:

```text
packet_profile: <compact|standard|durable-parallel>
priority: <P0|P1|P2|P3>
deadline_or_stop_condition: <time, attempts, or event>
capabilities_required: <tools/network/files/write/test/browser/etc.>
evidence_required: <logs/screenshots/citations/diff/report path>
data_classification: <public|private|company|customer|credential-risk>
dependencies: <message_id or artifact path>
error_code: <none|blocked-capability|blocked-permission|invalid-scope|validation-failed|timeout|cancelled|other>
blocked_on: <none|user|permission|tool|source|file|subagent|external-state>
confidence: <high|medium|low>
improvement_target: <tiny capability this expert run can exercise, or none>
extensions: <specialist-specific structured fields, including expert_delta when useful>
```

## Message Kinds

- `task`: main agent delegates work to one expert.
- `report`: expert returns result, blocker, or partial state.
- `integration`: main agent accepts/rejects/deferred findings and closes the
  loop.
- `event`: lightweight progress, cancellation, user interrupt, or lifecycle
  transition.

## Multi-Agent Coordination Rules

- Use one `trace_id` for a whole user-visible work round.
- Use separate `message_id` values for each expert task and report.
- Parallel experts may share a `trace_id`, but must not share write scope.
- The main agent owns arbitration. Experts can recommend, but cannot close the
  user task.
- If a user interrupts, emit or record a `cancelled` event for any running real
  platform subagent when possible.
- If an expert finds a reusable workflow defect, route the finding to `Workflow Distiller (沉炼)`
  or update the durable skill layer before final handoff.

## Compatibility Rule

`AGENT-TASK v2`, `AGENT-REPORT v1`, and `INTEGRATION v1` remain the user-facing
friendly forms. They should include the minimal packet fields that matter for
the current task, but do not need to become full JSON unless a script or runner
requires machine parsing.
