# Workflow Evolution

Use this reference when improving q-workflow itself, reacting to new agent
platform features, or deciding whether a local workflow rule should remain,
move, shrink, or retire.

## Purpose

q-workflow should stay useful as agents gain stronger native capabilities. It
should own the pieces that need to survive across agents and platforms:

- durable source of truth;
- safety and privacy boundaries;
- routing and escalation decisions;
- capability selection and fallback;
- observability probes;
- validation and learning loops;
- cross-session and cross-machine recovery.

Native agent features are engines. q-workflow is the control system that
decides when an engine is trusted, what evidence it must leave, and how the
work remains recoverable if that engine changes.

## External Direction Checked

These sources were used as idea references only; no code, prompts, schemas,
or prose were copied.

| Source family | Mechanism learned | Local adaptation |
|---|---|---|
| OpenAI Codex customization | Project guidance, memories, skills, MCP, and subagents are separate customization layers. | Keep q-workflow layered; do not overload one instruction file. |
| OpenAI AGENTS.md guidance | Project instructions can be layered and discovered before work starts. | Treat project-local instructions as project facts and norms, not generic workflow memory. |
| OpenAI Agents SDK | Grow from one specialist to handoffs, guardrails, human review, state, and observability as complexity rises. | Use capability escalation only when task complexity justifies it. |
| Anthropic effective-agents guidance | Simple, composable patterns beat complex frameworks for many production agent systems. | Keep routers small and make every added stage earn its cost. |
| MCP specification | Tools, resources, and prompts are distinct integration surfaces. | Classify integrations by data/context/tool role before adopting them. |
| A2A protocol | Long tasks need task state, messages, status, and artifacts. | Keep work items, checkpoints, progress notes, and artifact paths explicit. |
| LangGraph persistence | Durable execution separates thread checkpoints from longer-lived stores. | Separate session evidence from durable project truth and personal routing state. |
| Microsoft Agent Framework observability | Workflow execution needs spans, logs, metrics, and error visibility. | Require probes and reports for nontrivial workflow changes, not only final claims. |

## vNext Structure

Think of q-workflow as six planes. Each plane has a different owner and
different retirement rules.

| Plane | Owns | Keep lightweight by |
|---|---|---|
| Intent and policy | User goal, safety gates, privacy, approval boundaries, push/public rules | Store only stable triggers and hard boundaries in routers |
| State and authority | Project truth, personal routing state, source/runtime ownership, Git checkpoints | Use authority maps and avoid treating runtime mirrors or chat as truth |
| Capability | Skills, native agent features, MCP servers, subagents, scripts, external tools | Choose one primary capability and optional sidecars instead of loading everything |
| Execution | Route, plan, edit, validate, review, checkpoint stages | Use reusable stage contracts and stop conditions, not rigid scripts |
| Observability | Diffs, traces, logs, rendered/exported evidence, session pointers, validation output | Require probes matched to the work type |
| Evolution | Research, skill learning, rule-quality review, A/B tests, deprecation decisions | Promote only validated lessons; retire or demote obsolete local rules |

## Lean Core Bar

A new workflow rule, stage, script, skill route, or registry should enter the
core only when it passes all five checks:

1. **Failure-mode check**: it prevents a real repeated or high-impact failure.
2. **Frequency check**: it applies often enough to justify its loading layer, or
   it stays in an on-demand reference.
3. **Evidence check**: it leaves a command, diff, artifact, trace, report, or
   scenario that can prove it worked.
4. **Cost check**: it reduces or justifies added context, tool calls, elapsed
   time, sync work, or maintenance burden.
5. **Retirement check**: it states what native capability, validation result,
   or project maturity would let the rule move down or disappear.

If any check fails, keep the idea as a work-item note, regression scenario,
source-registry entry, or reference detail instead of adding it to `SKILL.md`.

## Capability-Native Rule

When a platform adds a native feature that overlaps with q-workflow, do not
delete the local rule immediately. Reclassify it:

1. **Use native** when the platform feature is more reliable and leaves enough
   evidence.
2. **Wrap native** when q-workflow still needs local authority mapping,
   privacy checks, validation, or handoff notes.
3. **Keep local** when the native feature is unavailable, unobservable,
   platform-specific, unsafe for the current data, or weaker than the local
   workflow.
4. **Retire local** only after a realistic scenario proves the native feature
   covers the old failure mode with equal or better recovery, validation, and
   safety.

The local rule should move down the stack when possible:

- from always-on profile to router;
- from router to on-demand reference;
- from reference to regression scenario;
- from local implementation to validation gate;
- from validation gate to archived lesson.

## Capability Retirement Checklist

Before retiring or shrinking a local workflow feature, check:

- **Failure mode**: which old failure does the feature prevent?
- **Native replacement**: what platform capability now covers it?
- **Authority**: where is the source of truth after replacement?
- **Observability**: what output proves the native feature behaved correctly?
- **Portability**: what happens in another CLI, model, machine, or network
  environment?
- **Safety**: does it preserve approval, credential, private-data, and public
  sync boundaries?
- **Recovery**: can a fresh session resume from durable files without the old
  chat?
- **Cost**: does the replacement reduce context, time, or maintenance load?
- **Regression**: what small scenario would catch a future platform behavior
  change?

If the answer is unclear, keep the local rule as an on-demand reference and
record a future validation scenario instead of deleting it.

## Skill Orchestration Pattern

For complex tasks, use this default shape:

1. **Primary skill**: pick the one skill that owns the task domain.
2. **Sidecar skill**: add at most one or two supporting skills for research,
   visual review, hardware access, or lifecycle work.
3. **Capability gate**: decide whether native platform features, scripts, MCP,
   or subagents are useful for this task.
4. **Authority map**: identify truth, runtime mirrors, evidence, generated
   artifacts, and rebuildable views.
5. **Evidence probe**: choose the smallest command, diff, export, trace, or
   report that proves the route worked.
6. **Durable checkpoint**: update work item, project state, and Git when the
   checkpoint is meaningful.

Avoid skill fan-out. If more than three skills seem needed, write a short
orchestration note first and decide which ones are actually blocking.

## Self-Learning Control Loop

For proactive entry checks, model identity evidence, bounded local maintenance
and review deduplication, use [Proactive evolution](proactive-evolution.md).
This loop refines files and procedures; it does not train or replace a model.

Use learning as a bounded control loop, not an always-expanding memory:

1. Capture a concrete miss, friction point, or new capability.
2. Classify the layer: profile, router, reference, script, project memory,
   validation gate, source registry, or archived lesson.
3. Patch the smallest layer that reduces the failure mode.
4. Validate on at least one realistic scenario before promotion.
5. Revisit the rule after later real use; demote, merge, or retire it when a
   lower-cost native or local mechanism covers the same failure.

Do not let every interesting source become a standing rule. The strongest
learning outcome is often a better validation scenario or retirement condition.

## Periodic Slimness Review

Run a slimness review after major workflow upgrades or when `SKILL.md` grows
noticeably:

- count router lines and identify sections that should be references;
- list duplicated rules across profile, workflow, skill, and project memory;
- find rules with no trigger, no validation cue, or no retirement condition;
- check whether any source/runtime mirror is newer than its durable source;
- confirm that ordinary resume and implementation still use Quick/Project
  paths, not Deep/Full paths by default.


## Evolution Triggers

Run this reference when:

- the user asks to improve workflow structure or prevent obsolescence;
- a platform adds a capability that overlaps with local workflow rules;
- two or more skills start duplicating the same behavior;
- a recovery, sync, validation, or source/runtime mismatch exposes a workflow
  failure;
- context cost grows because rules moved into the wrong layer;
- public standards or official agent docs introduce a better abstraction;
- repeated real work shows a local rule is too rigid, too vague, or too slow.

## Upgrade Procedure

1. Frame the failure mode and the part of the workflow that may be obsolete.
2. Check official and high-signal sources when external/current uncertainty
   affects the decision; use `q-research-discovery` for substantial discovery.
   A demonstrated local contradiction can use local evidence directly.
3. Use `q-skill-pattern-learning` when comparison with other workflows is
   needed for a substantial redesign. Extract mechanisms, not surface wording;
   do not require research fan-out for every narrow, evidenced repair.
4. Use `q-skill-creation` to place the smallest rule at the right layer.
5. Update source, runtime, bootstrap, public, or private variants when
   applicable.
6. Validate with metadata checks and at least one behavior scenario.
7. Record the decision in the active work item, including what was not changed
   and why.

## Anti-Patterns

- Treating every native agent feature as a reason to delete local workflow.
- Treating local workflow as a frozen script that ignores platform progress.
- Loading every relevant skill instead of choosing a primary owner.
- Measuring success only by a clean final answer rather than durable evidence.
- Letting runtime mirrors become the only copy of important workflow behavior.
- Turning a rare failure into an always-on context rule.
