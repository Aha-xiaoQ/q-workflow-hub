# Q Output Protocol

Use this protocol to make Xiao Q workflow outputs recognizable, recoverable, and portable across agents without making ordinary conversation mechanical.

## Principle

Standardize state transitions, not every sentence. Use natural prose for simple answers, explanations, and brainstorming. Use fixed cards when the output must be resumed, audited, delegated, or acted on by another agent.

## Layers

| Layer | Trigger | Format strength | Goal |
|---|---|---|---|
| Natural | casual answer, explanation, brainstorm, tiny confirmation | preference | readable human collaboration |
| Card | status, plan, done, blocked, next-step advice, resume, handoff | procedure | stable state and next action |
| Packet | subagent task/report, release gate, cross-agent handoff | hard gate for release or delegation | portable machine-readable trace |

## Slash Status Line Hard Gate

For workflow progress, test-loop closure, workflow-rule repair, readiness checks, commit/push preparation, and final handoff, the first non-empty line MUST use exactly this grammar:

```text
小Q工作流 / <skill-id> / <current-action>
```

`skill-id` MUST be a registered skill id such as `q-workflow`, `q-agent-roster`, `q-code-lifecycle`, or `gmppt-study-workflow`. It MUST NOT be a temporary label such as `validation`, `source-runtime-audit`, `sync-check`, a script name, or a checker name. Put those words in `current-action` instead.

`skill-id` MUST NOT be an expert role, platform nickname, project nickname, or free-form label.

`current-action` MUST describe the action being performed. It MUST NOT be a state token such as `done`, `partial`, `blocked`, or `pending-approval`.

Ask this before writing the line:

- Slot 2: which skill is responsible?
- Slot 3: what action is being performed under that capability?

If the word is an audit, validation, smoke, runner, script, gate, release check,
or temporary task label, it belongs in Slot 3, not Slot 2.

State belongs on the next line:

```text
小Q工作流 / q-agent-roster / 专家调用协议修复
状态：partial，正在验证专家卡闸门。
```

Invalid:

```text
小Q工作流 / Workflow Distiller (沉炼) / blocked-pending-approval
```

This is invalid because the second field is an expert role and the third field is a state.

A tiny natural-language answer may skip this line only when it has no workflow action, no file or state change, no validation claim, no handoff, and no next-step menu. If `**Recommended Next**` appears, or the answer closes a test/repair/workflow loop, the slash status line is required. Substantial DONE/HANDOFF closures must also include a valid `**Recommended Next**` block before the answer is considered complete; adding it only after Xiao Q points out the omission is recorded as a format regression.

## Required Cards

Use the smallest applicable card. Do not stack cards unless the task crosses an approval, release, delegation, or handoff boundary.

### STATE-UPDATE

```text
STATE-UPDATE
state: <confirmed|partial|stale|conflict|blocked|pending-approval|done>
current: <one concrete focus>
completed: <1-3 concrete items or none>
risk_or_gap: <none|1-3 concrete risks>
next: <one recommended action>
```

### DONE

```text
DONE
completed: <bounded task>
artifacts: <paths/commits/reports/artifacts or none>
validation: <passed checks|not run + reason>
risk: <none|known residual risk>
next: <one recommended action>
```

### BLOCKED

```text
BLOCKED
blocker: <specific blocker>
evidence: <file/command/source or unavailable>
impact: <what cannot safely proceed>
minimum_unblock: <one unblock action>
waiting_on: <user|tool|network|repo|external system>
```

### HANDOFF

```text
HANDOFF
goal: <what the next agent/session should continue>
authority: <latest chat|state file|commit|report|artifact>
current_state: <confirmed|partial|stale|conflict|blocked>
completed: <1-5 concrete items>
remaining_or_risk: <1-5 concrete items>
next: <one action with target path/command if known>
do_not_touch_without_approval: <explicit boundaries>
```

## Hard Gates

- Subagent or expert delegation MUST use the dispatch card from `handoff-protocol.md` or `auto-dispatch-policy.md` before a real platform subagent is spawned.
- Push, publish, release, migration, destructive cleanup, and public/team/customer handoff MUST name approval state and residual risk.
- `done` MUST NOT be used when validation did not run; use `partial` and name the gap.

## Small Task Adaptation

For a tiny answer with no durable state, no file edit, no approval boundary, and no future handoff need, use natural prose. The workflow advantage is clarity, not ceremony.
