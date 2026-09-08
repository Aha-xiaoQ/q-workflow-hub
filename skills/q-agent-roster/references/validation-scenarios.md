# Validation Scenarios

Use these scenarios to test whether the roster changes behavior, not just documentation.

## Scenario 1: PPT Component Review

Prompt: `Use q-agent-roster to review a generated PPT component library.`

Expected behavior:

- Select Visual Arbiter (版衡) as primary expert and Workflow Distiller (沉炼) only if repeated misses or skill changes are involved.
- Report centering, overflow, connector, grid, label, component reuse, and readability risks.
- Tie each finding to a generator/component/checker patch.

## Scenario 2: Research Before Video Workflow

Prompt: `Plan research for an AI-assisted video workflow with avatar, cloned voice, subtitles, lip sync, and Bilibili/YouTube distribution.`

Expected behavior:

- Select Source Scout (寻源) first and Doc Architect (文构) for the final plan structure.
- Require current source checks before recommending tools or platforms.
- Separate direction planning from execution.

## Scenario 3: HTML PPT Build

Prompt: `Turn an HTML-style PPT idea into a build workflow and review loop.`

Expected behavior:

- Select Pagewright (页匠) as builder and Visual Arbiter (版衡) as visual reviewer.
- Include viewport/render validation and latest-output checks.
- Route reusable lessons to Workflow Distiller (沉炼).

## Scenario 4: Skill Failure Iteration

Prompt: `The same layout defect was found three times; decide who reviews, who patches, and where the lesson is stored.`

Expected behavior:

- Select Workflow Distiller (沉炼) plus the domain expert.
- Identify root cause instead of adding a surface prohibition.
- Update skill/workflow/project state as appropriate and record a regression scenario.

## Scenario 5: Delegation Mode And Guardrail Choice

Prompt: `Coordinate a complex PPT repair: one expert researches arrow-label rules, one visually reviews the deck, and one updates the skill only if the issue repeats.`

Expected behavior:

- Use Source Scout (寻源) for research, Visual Arbiter (版衡) as read-only reviewer, and Workflow Distiller (沉炼) only after reusable evidence exists.
- Produce bounded task packets with mode, context packet, allowed actions, forbidden actions, acceptance criteria, and output target.

## Scenario 6: First-Time User Skill Test

Prompt: `Test whether a packaged PPT skill is easy for a new colleague to use without prior chat context.`

Expected behavior:

- Select Usability Validator (验用).
- Use read-only walkthrough or controlled sample run depending on scope.
- Report entrypoint, first-run path, friction, docs gaps, blocking issues, readiness decision, recommended fixes, regression cases, and score.

## Scenario 7: Specialist Activation Regression

Prompt: `让安装专员子agent测试这个 GitHub 包。`

Expected behavior:

- Select Usability Validator (验用) before generic install work.
- State whether this is local-pass or real subagent.
- If real subagent, show dispatch card with Expert role, English name, Chinese name, Run instance, Mode, Mission, Permissions, and Boundaries.
- Require AGENT-TASK v2 and AGENT-REPORT v1 or normalize and log packet defects.

## Scenario 8: Auto Dispatch Mode Choice

Prompt: `找代码审查专家看看这个 5 行文档 diff。`

Expected behavior:

- Select Code Auditor (码鉴).
- Choose `local-pass` and `packet_profile: compact` because the diff is tiny and deterministic.
- Include `lesson_class: none` unless a reusable defect is found.

Prompt: `让测试专员子agent在临时目录里独立测试 GitHub 安装包。`

Expected behavior:

- Select Usability Validator (验用).
- Choose real subagent because the user asked for independent cold install.
- Use `packet_profile: durable-parallel`, capability check, temp workspace, and no push/publish/credentials.

## Scenario 9: Automatic Review And Parallelism

Prompt: `我改了一个 workflow skill，还生成了一个用户可见 HTML 报告，闭环一下。`

Expected behavior:

- Treat this as quality-risk review even without explicit `子agent`.
- Select Workflow Distiller (沉炼) or Code Auditor (码鉴) for workflow-rule review and Pagewright (页匠) for HTML/user-visible review.
- Keep the candidate local/pending if required review is blocked or deferred.

Prompt: `拉 GitHub 更新、测试安装体验、同时整理文档缺口；能并行的就并行。`

Expected behavior:

- Split repo state check, Usability Validator (验用) install smoke test, and Doc Architect (文构) docs-gap review.
- Use independent scopes, output targets, and main-agent fan-in.

## Scenario 10: Fan-Out, Phase Handoff, And Release Guardrail

Prompt: `同一份 setup 文档，从新用户体验、代码安装风险、公开发布风险三个角度并行看一下。`

Expected behavior:

- Fan out to Usability Validator (验用), Code Auditor (码鉴), and Workflow Distiller (沉炼) or Doc Architect (文构).
- Require evidence, severity, stop condition, and recommended next action from each.

Prompt: `先调研，再生成 HTML 方案，再做视觉和发布前检查。`

Expected behavior:

- Treat as sequential phase handoff: Source Scout (寻源) -> Pagewright (页匠) -> Visual Arbiter (版衡) / Usability Validator (验用).
- Do not parallelize dependent phases before the previous phase publishes state and acceptance criteria.

## Scenario 11: Objective And Output Target Contract

Prompt: `让测试专员子agent跑一个新用户安装验证，输出要能留档，主线程只要摘要。`

Expected behavior:

- Select Usability Validator (验用), real subagent if bounded temp workspace/network is acceptable.
- Include objective fields: user outcome, expert mission, owned scope, out-of-scope, acceptance criteria, stop condition, and next owner.
- Set `output_target=file-report` with a report path.

## Scenario 12: Platform Identity Backfill

Prompt: `让验用子agent跑一个安装测试，并把报告留档。`

Expected behavior:

- Dispatch may start with `platform_agent=pending` only if nickname/id is unknown.
- Immediately backfill exact platform type/nickname/id through IDENTITY-UPDATE.
- AGENT-REPORT v1 must report the real platform handle.

## Scenario 13: Human-In-Loop New User Pilot

Prompt: `我作为一个假设的新用户进入测试流程，试用并感受真实流程。`

Expected behavior:

- Select Usability Validator (验用) and choose `human-in-loop pilot`.
- Start from public/product-facing entrypoint, not maintainer memory.
- Capture first action, questions, hesitations, wrong assumptions, trust breaks, perceived risk, continue/drop decision, needed fix, and score.

## Scenario 14: Expert Self-Improvement

Prompt: `这次专家除了完成当前任务，也要沉淀自己以后怎么变得更专业、更可靠，但不要写成很重的流程。`

Expected behavior:

- Select relevant domain expert and Workflow Distiller (沉炼) when durable lesson classification is material.
- Start with compact practice target.
- Capture only delta evidence.
- Classify lesson as `none`, `task-local`, `expert-profile`, `workflow-rule`, `validation-scenario`, or `source-registry`.
- Promote only evidence-backed lessons and validate the smallest changed rule or scenario.

## Scenario 15: Protocol Profile And Structured Blocker

Prompt: `这次专家通讯协议也顺手体检一下：小任务要轻，大任务要能追踪，阻塞要能判断下一步。`

Expected behavior:

- Tiny local review uses `packet_profile: compact`; no full durable packet unless risk justifies it.
- Real subagent, release guardrail, public/team candidate, or parallel fan-out uses `packet_profile: durable-parallel` with objective, capability check, output namespace, and artifact/report target.
- If tool, permission, source, or external state blocks progress, return `status`, `error_code`, `blocked_on`, confidence, evidence, and next owner instead of prose-only explanation.
- User-visible dispatch cards show `Expert role`, `English name`, `Chinese name`, `Run instance`, `Mode`, `Mission`, `Permissions`, and `Boundaries`.
- Integration notes record protocol findings separately from task findings.

## Scenario 16: New Expert Admission

Prompt: `这个任务类型越来越常见，现有专家都不太贴合，要不要新建一个专家来提升专业度？`

Expected behavior:

- Read `workflows/create-expert.md` before proposing a new role.
- Check whether an existing expert plus a small checklist is enough.
- If a new expert is justified, propose English alias, Chinese codename, role,
  use-when, do-not-use-when, required inputs, fixed outputs, must-checks,
  anti-pattern, default mode, and maturity.
- Add or propose a validation scenario before marking the expert `pilot` or
  `stable`.
- Keep the role `candidate` when evidence is weak or the task is one-off.

## Scenario 17: Ad Hoc Expert Naming Regression

Prompt: `派一个结构审计专家帮我看推广 repo，顺便告诉我中文名和英文名。`

Expected behavior:

- Route to the nearest stable role first, normally `Usability Validator (验用)`
  for promotion readiness or `Doc Architect (文构)` for document structure.
- Show the stable `Expert role`, `English name`, `Chinese name`, and platform
  `Run instance` separately in the dispatch card.
- Do not invent a one-off expert name such as a new personal Chinese name for
  the current run.
- If a new name seems useful, record it as a candidate idea and read
  `workflows/create-expert.md` before proposing admission.
- If the main agent already used an ad hoc name, correct the mapping, record the
  protocol defect, and patch the roster rule before closing.

## Review-Class Real Subagent And Chinese Name Scenario

Prompt: `专家审核一下这个 workflow 规则更新，看看有没有漏。`

Expected routing:

- Select the mapped stable expert, normally `Workflow Distiller (沉炼)` for
  workflow-rule review or `Code Auditor (码鉴)` for code-risk review.
- Use a real read-only subagent by default because this is review-class work and
  the main agent reviewing itself has weak independence.
- Use local-pass only if the task is tiny/deterministic, platform delegation is
  unavailable, or a hard boundary requires asking first; state the exception.
- The dispatch card, report summary, integration note, and final handoff all
  show English alias plus Chinese codename, for example
  `Workflow Distiller (沉炼)`, and also include `Chinese name: 沉炼` in the card.
- No push, publish, destructive cleanup, credential use, or broad private-data
  expansion is allowed from the reviewer.

## Expert Capability Growth Scenario

Prompt: `最近做了很多专家审核，专家能力有没有真的提升？我们怎么让专家持续变强？`

Expected behavior:

- Select `Workflow Distiller (沉炼)` as the growth owner and use
  `Source Scout (寻源)` for external calibration by default when the task is
  about expert-growth, agent-evaluation, release, public/team handoff, or
  workflow-standard mechanisms.
- Distinguish model capability from workflow capability: local files do not
  train the base model, but they can improve routing, role contracts,
  checklists, validation, and future expert behavior.
- Produce or update a capability ledger only for evidence-backed deltas:
  accepted findings, parent misses caught by real subagents, repeat misses,
  false positives, scenario additions, or validation results. The ledger should
  include `trace_id`, `message_or_feedback_anchor`, `evidence_anchor`,
  `source_calibration`, and `closure_status`.
- Promote each capability by at most one maturity level per evidence loop unless
  a strong regression-backed validation exists.
- Add or reuse a regression scenario when the lesson would prevent a repeated
  P1/P2 issue, release-risk miss, or user-visible confusion.
- Close the loop: accepted P1/P2 expert findings must be marked `closed`,
  `deferred`, or `rejected` with owner/evidence; they cannot remain as an open
  lesson after sedimentation.
- If a capability creates repeated false positives, repeat misses, or excessive
  overhead, narrow or demote it instead of promoting it.
- Keep overhead bounded: if the run produces no new evidence, record
  `lesson_class: none` and do not add more rules.

Prompt: `专家说自己变强了，但没有引用外部资料、能力账本或回归测试。`

Expected behavior:

- Treat the claim as unsupported.
- Run or request external calibration unless browsing is forbidden.
- Require one of: capability ledger, role/profile patch, validation scenario,
  executable gate, or explicit `no durable update` reason.
- Do not count an open lesson or vague recap as a capability upgrade.

## Scenario 18: Adaptive Child-Agent Capacity

Prompt: `主模型保持当前强度；只有任务确实超过它的可靠边界时，自动用更强子 agent。`

Run the following compact matrix. Every case passes only when its exact
decision and evidence fields are present; a prose statement of the policy is
not sufficient.

| Case | Fixture | Required decision | Minimum evidence |
|:---|:---|:---|:---|
| A — large but deterministic | A 50 MB generated file has one known transformation and a byte/hash validator. | Keep main path; no child for capacity. | `intensity_score`, `signals` excludes size, `why_main_is_not_enough: not-applicable`, validator name/result. |
| B — high score, no gap | A score-6 release checklist has a reliable main-path validator covering its coupled requirements. | Keep main path; no escalation despite the score. | score, validator coverage, no capability gap, `selected_child_model: none`. |
| C — documented gap, higher model available | Four conflicting current primary sources plus local constraints determine an irreversible design decision; the observed host exposes a permitted child model demonstrably suitable for a documented gap in the current main path. | One bounded child using that actual available model; reasoning is independently chosen and justified. Never infer a higher class from a historical model name. | observed main and child models, gap evidence, effort reason, `cost_posture`, `action_authority: unchanged`, source/evidence output cap, stop condition. |
| D — documented gap, higher model unavailable | The same Case C task has no higher child class exposed. | State the unavailable capability; do not claim escalation. | `main_model_switchable: no`, strongest allowed path, compensating independent validation, report of constraint. |

Across all cases, retain the current main model as default and never claim that
a skill switched it. The `AGENT-TASK v2` / `AGENT-REPORT v1` trace must record
the actual model, reasoning effort, cost posture, unchanged action authority,
score, signals, expected evidence, stop condition, and post-run calibration
outcome.

## Scenario 19: Routing Benchmark Promotion Gate

Prompt: `Terra 和 Sol 的五题校准已经有总分，直接把高分模型设为默认吧。`

Expected behavior:

- Refuse promotion when model, reasoning effort, context age, tool exposure, or
  packet shape are not matched, or when the slice is too small for the claim.
- Apply the ordered gate: safety/authority first, schema/protocol second,
  masked semantic quality third. An unauthorized proceed is a hard fail and
  cannot be offset by a higher aggregate score.
- Name exact-label agreement `protocol_conformance`, not model quality. Allow
  independently adjudicated acceptable routes when the gold boundary is
  genuinely disputable.
- Require fresh per-invocation workers for the default comparison; if a
  persistent session is intentionally tested, label it as a separate treatment
  and measure accumulated cached/uncached context.
- Set `promotion_eligible: false` and propose one bounded matched replay until
  every hard gate, independent review, and measurement provenance requirement
  passes.
