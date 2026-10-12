# Handoff Protocol

Use this for machine-consumed packets or durable multi-stage/release handoffs.
For ordinary local/read-only agents, the compact contract in
`../workflows/dispatch-agent.md` is sufficient, including real subagents.

## Profiles

- **Compact (default):** goal, source/context, scope/actions, acceptance/stop,
  result/evidence, real run identity and next owner. Prose or bullets are valid.
- **Structured:** add fields required by an actual runner, long-running workflow
  or explicit release protocol. Do not add empty fields merely to complete a
  template. Parallel writers always need disjoint scope and output paths.

Keep stable role names and platform handles distinct. A single
`Workflow Distiller (沉炼)` label carries both language names. The parent can
attach the tool-returned handle; a separate identity-only turn is unnecessary.

## Structured compatibility

Existing `AGENT-TASK v2`, `AGENT-REPORT v1`, `INTEGRATION v1` and Q-AGENT-PACKET
remain supported. When a consumer requires them, retain its protocol/version,
message/trace/parent identity, kind, expert, platform_agent and lifecycle fields.
Use `agent-protocol-design.md` for that consumer's schema. Do not treat historical
packet examples as mandatory for ordinary native-agent calls.

Example of a compact structured handoff:

```text
AGENT-TASK v2
trace_id: <task/trace>
expert: <stable role>
mission: <bounded outcome>
context: <relevant paths and current state>
allowed_actions: <read/run/owned-write scope>
forbidden_actions: <protected paths and external actions>
acceptance_and_stop: <observable result and stop condition>
output: <findings/evidence or assigned report path>
```

Result: checked/changed paths, findings, checks/evidence, unresolved gaps and next
owner. Main preserves actual run identity and dispositions once. Authority,
scope or evidence gaps need repair; a missing decorative header does not merit
another model call. Never call a parent's self-check independent review.

## Parallel and interrupted work

Assign each writer non-overlapping owned paths and output namespace. Read-only
reviewers may inspect common inputs for distinct questions. Stop overlapping
writes and let main arbitrate. Record pending operation IDs and consume outcomes
before retries; interruption is not rollback. Use error/cancel fields when a
machine consumer needs them, otherwise report the blocker and dependent action.

## Integration

Record accepted/rejected/deferred substantive findings, evidence, residual risk
and next action in the existing work item. Reports may be parent-persisted.
Do not duplicate chat, file report, integration report and scorecard for the same
evidence. A reusable lesson is optional and needs authorization and validation;
successful delegation alone does not trigger skill maintenance.
