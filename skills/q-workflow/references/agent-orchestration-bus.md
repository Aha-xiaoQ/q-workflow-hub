# Agent Orchestration Bus

Use this reference when a task may benefit from sub-agents, independent
reviewers, parallel validators, or a bounded improvement loop.

## Purpose

Sub-agents are capability engines, not workflow owners. q-workflow should
standardize how agents receive work, report evidence, and hand results back to
the main agent. The goal is an efficient loop:

```text
plan -> dispatch -> execute -> observe -> review -> arbitrate -> integrate -> consolidate
```

Think of the main agent as the scheduler and arbiter. Sub-agents are bounded
workers, validators, or reviewers on a shared bus. The bus is not a chat room;
it is a structured message contract.

## When To Use

Use real sub-agents only when the current environment exposes a native
delegation tool and bounded delegation is authorized by Xiao Q's wording or by
the active `q-agent-roster` auto-dispatch policy for quality-risk review or
parallel independent work. If no native delegation tool is available, do not
simulate sub-agents in narration; use the same contract as an internal
checklist or ask for a narrower validation path.

Use sub-agents when at least one condition is true:

- independent research, source scan, or local file audit can run beside the
  main path;
- several independent questions about the same input can fan out to distinct
  experts and fan back into one integrated decision;
- a generated artifact, code change, report, deck, or workflow rule needs a
  second reviewer;
- validation can run separately from implementation, such as build/test/export
  checks, visual review, log inspection, or regression replay;
- a cold-context new-user, install, onboarding, or promotion-readiness test is
  needed without hidden maintainer context;
- the workflow is stateful or sequential enough to need phase ownership, such
  as research -> build -> review -> release guardrail;
- the task is long, high-risk, subjective, public-facing, customer-facing, or
  has already had a user-found miss;
- two or more candidate approaches should be compared by different lenses;
- a major workflow/skill change needs a replay scenario or transfer check.

Do not use sub-agents for:

- exact micro commands such as `TODO`, `TOKEN`, or quick pointer checks;
- small deterministic edits that the main agent can safely complete faster;
- tasks that require the same file, Git index, generated artifact, or lockfile
  to be edited by multiple agents;
- credentials, destructive cleanup, publishing, pushes, or unclear private data;
- vague "think about this" delegation without an output contract.

## Agent Roles

| Role | Owns | Default permissions | Output |
|---|---|---|---|
| Orchestrator | plan, priority, arbitration, integration, durable memory, final answer | main agent only | final decision and handoff |
| Worker | bounded implementation or artifact production | write only assigned files | changed paths and validation |
| Explorer | independent research or codebase/file audit | read-only | findings, evidence paths, recommendation |
| Validator | tests, exports, screenshots, logs, checks, regression replay | read/run bounded commands | pass/fail evidence |
| Critic / Reviewer | user-risk, quality, gap, contradiction, and rubric review | read-only by default | issues ordered by severity |
| Reflector / Archivist | after-action summary and reusable lesson extraction | read/write durable note only when assigned | lesson, target layer, residual risk |

## Dispatch Brief

Every delegated task should use this full contract for major work:

```text
message_id:
work_item:
role:
priority: P0/P1/P2/P3
objective:
context_minimum:
inputs:
read_scope:
write_scope:
allowed_actions:
forbidden_actions:
expected_output:
evidence_required:
dependencies:
deadline_or_stop_condition:
output_target:
handoff_format:
```

## Cache-Aware Delegation

Use sub-agents to reduce main-context load only when their outputs are bounded.
If a sub-agent returns a long unstructured essay, the cache and context problem
has merely moved back into the parent thread.

Defaults for research/explorer sub-agents:

- Source cap: 4-6 high-value sources unless the brief explicitly asks for a
  broad scan.
- Time cap: 90-120 seconds for scout passes; longer passes need a narrower
  artifact or written stop condition.
- Output cap: source table, 5-8 mechanisms, decision implications, and next
  action; avoid long narrative.
- Evidence: cite or name source paths/URLs, but do not paste long excerpts.
- Return large notes as a file path when the environment supports file output;
  otherwise return a compact summary only.

Defaults for reviewer/validator sub-agents:

- Review only the assigned artifact or exported evidence.
- Lead with blockers and reproduction steps.
- Do not restate all background context already in the brief.
- Return changed files only when the sub-agent had explicit write ownership.

The main agent should pass a compact context packet, not the full conversation.
When context pressure is above about 60% or cache spread is high, use
`context-budget.md`'s `TASK-PACKET v1` before dispatching more agents.
`TASK-PACKET v1` belongs to the parent workflow: it is a cache/recovery bridge.
For a sub-agent, embed only the relevant objective, source-of-truth paths,
current state, constraints, next actions, validation target, and risks into the
delegated `context_packet`. Keep the actual delegation contract as
`AGENT-TASK v2` from `q-agent-roster`; do not create a second return schema in
q-workflow.

`q-agent-roster` owns the concrete agent communication packet. Current
delegations should carry the lightweight `Q-AGENT-PACKET` fields inside
`AGENT-TASK v2`, `AGENT-REPORT v1`, and `INTEGRATION v1`: `protocol`,
`version`, `message_id`, `trace_id`, `parent_id`, `kind`, stable expert role,
platform execution handle, lifecycle state, permissions, acceptance criteria,
and next owner. The stable q-workflow expert role and the platform
nickname/id are different fields; always surface both when a real platform
subagent is used. In user-visible chat, show them as `专家角色` and `运行实例`
inside the standard multi-line dispatch card so the platform nickname does not
look like a second expert name.

If the platform only returns the nickname/id after spawn, the parent agent
should immediately send an identity update to the subagent with the exact
`platform_agent` value expected in `AGENT-REPORT v1`. A real subagent report
must not omit `platform_agent` or use `local-pass` or `pending` as its platform
handle; if it does, the main agent records the corrected trace in
`INTEGRATION v1` before closing the loop.

Before a real platform subagent is spawned, `q-agent-roster`'s
`auto-dispatch-policy.md` should classify the request as local-pass, real
subagent, ask-before-spawn, or deny. This prevents hidden parallelism while
still allowing automatic expert routing for explicit specialist requests,
quality-risk reviews where the main agent would otherwise review its own
nontrivial work, and parallel independent tasks that improve speed or evidence.

Required defaults:

- `no commit, no push`;
- no destructive cleanup;
- no credential or private-data expansion beyond the brief;
- no broad refactor unless the brief owns that scope;
- report uncertainty instead of guessing across missing context.

Daily reviewer/validator minimum:

```text
role:
priority:
objective:
read_scope:
allowed_actions:
forbidden_actions:
expected_output:
evidence_required:
stop_condition:
output_target:
```

Use the minimum form for a single read-only reviewer, validator, or explorer.
Expand to the full contract when there are writes, multiple agents, public
handoff, credentials/privacy risk, or a long-running loop.

## Return Message

Sub-agents should return:

```text
status: completed / blocked / failed / partial
role:
objective:
work_done:
changed_files:
evidence:
report_path:
artifact_manifest:
findings:
risks:
recommended_next_action:
handoff_to:
```

For reviewers, lead with findings and severity. For validators, lead with the
command/report evidence. For workers, list changed paths and tests run. When
evidence is bulky or durable, use a file report or artifact manifest and return
the paths in the chat summary.

## Priority And Arbitration

Priority levels:

- `P0`: safety, privacy, destructive-action prevention, credential/public sync,
  data loss, or user-visible blocker.
- `P1`: correctness, build/test failure, factual error, customer-facing/PPT
  blocker, or published-content issue.
- `P2`: maintainability, workflow durability, repeated friction, or useful
  validation improvement.
- `P3`: polish, optional research, future improvement, or nonblocking style.

Arbitration rules:

- The main agent owns final decisions and conflict resolution.
- Tool/test evidence outranks LLM reviewer judgment.
- Official or primary sources outrank blogs when deciding current tool behavior.
- User feedback outranks agent preference for subjective deliverables.
- If two agents disagree and evidence is weak, run a focused validator or ask
  Xiao Q only when the decision affects scope, safety, privacy, or public
  release.
- If a critic loop repeats the same class of issue twice, stop the loop and
  convert the issue into a rule, test, or user decision.

## Standard Loops

### Reviewer Loop

Use after a nontrivial artifact or user-found miss.

```text
main produces artifact -> critic reviews against rubric -> main fixes or rejects findings -> validator checks -> main records lesson if reusable
```

Default max: two repair rounds before escalation.

### Validator Loop

Use when objective evidence exists.

```text
main edits -> validator runs checks/export/regression -> main fixes failures -> validator reruns only affected checks
```

### Parallel Research Loop

Use for broad or uncertain decisions.

```text
main frames question -> explorer A checks official/primary sources -> explorer B checks local/project evidence -> main synthesizes -> durable report
```

### Skill/Workflow Change Loop

Use before promoting a major lesson.

```text
main patches smallest rule -> validator checks source/runtime readback -> critic checks overreach/context cost -> main updates state and reports residual risk
```


### Permission-Preflight Loop

Use this loop shape when Xiao Q asks for unattended or long-running execution:

```text
loop request -> permission contract -> work segment -> validation -> reviewer -> repair or close
```

The permission contract must name work_roots, write_scope, auto_allowed,
ask_always, branch_around, and stop_condition. The main agent should keep
working inside the contract and should not wait idly on a single denied or
unapproved action while any non-overlapping branch remains useful.
A long loop is eligible for fewer prompts only when it runs inside an approved
workspace or isolated test root, uses stable command shapes, writes checkpoints,
and keeps high-risk actions outside the auto-allowed set.

### Loop Engineering Control Loop

Use this term carefully. Prefer "bounded evaluator-optimizer loop" in durable
rules.

```text
trigger -> goal -> context packet -> action -> observation -> evaluator -> decision -> memory/update -> stop condition
```

The loop is valid only when it has:

- a trigger;
- an explicit goal;
- a bounded context packet;
- an observable check;
- a stop condition;
- a durable memory/update path;
- a human escalation condition.

## MCU Analogy

This is only an engineering analogy, but it is useful:

- **Bus:** message format and evidence artifacts shared by agents.
- **Scheduler:** main agent chooses which task runs now and which can be
  sidecar/background.
- **Arbiter:** main agent resolves write conflicts, priority conflicts, and
  evidence disagreements.
- **Interrupts:** P0/P1 findings can preempt lower-priority polishing.
- **DMA:** long validations/downloads/transcriptions can run while the main
  agent continues non-overlapping work.
- **Peripheral registers:** each agent must report status, changed files,
  evidence, and next action in a stable format.
- **Watchdog:** stop conditions prevent runaway loops and repeated speculative
  review.

## Trigger Matrix

| Task type | Default agent pattern |
|---|---|
| Small file edit | main only |
| Dirty/unclear repo state | explorer for targeted audit if main path is not obvious |
| Code change with tests | worker or main edits, validator runs tests/log review |
| PPT/UI/visual artifact | critic reviews exported evidence, validator checks scripts/reports |
| Broad research | two explorers with different source roles, main synthesizes |
| Skill/workflow update | critic for overreach/context cost, validator for source/runtime readback |
| Public/customer-facing artifact | critic + validator before handoff |
| Repeated user-found miss | reviewer loop plus consolidation |

## Acceptance Criteria

A delegation or loop has succeeded only when:

- the brief followed the full or daily-minimum dispatch contract;
- the return message followed the return contract;
- the main agent integrated the result without duplicating the sub-agent's work;
- evidence is stronger than pure LLM opinion, or the residual uncertainty is
  explicitly reported;
- write scopes did not overlap unless the main agent explicitly arbitrated the
  conflict;
- durable state records reusable lessons, changed rules, skipped surfaces, and
  residual risk when the work changed workflow behavior.

## Promotion To Skills

Create a dedicated skill only after the pattern repeats in real work. Likely
future skills:

- `q-agent-orchestration`: role contracts, bus message format, dispatch and
  arbitration rules.
- `q-critic-review`: reusable reviewer rubrics for PPT, code, research, and
  workflow changes.
- `q-loop-engineering`: bounded control-loop design, stop conditions,
  observability, and memory updates.
- `q-agent-validation-harness`: regression scenarios for agent delegation,
  reviewer loops, and source/runtime synchronization.

Until then, keep the durable rule here and use project reports as validation
evidence.
