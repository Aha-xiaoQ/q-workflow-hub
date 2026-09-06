# Auto Dispatch Policy

Use this reference when deciding whether a q-workflow expert request should
stay in the main agent as a local specialist pass or spawn a real platform
subagent. The goal is predictable automation, not hidden parallelism.

## Decision Ladder

1. **Route first.** If Xiao Q names a specialist, reviewer, tester, or
   subagent, use `agent-registry.md` before ordinary execution.
2. **Default to local pass only for tiny non-review work.** A local pass is
   enough when the task is deterministic, narrow, low-risk, and does not need
   independent cold context. For a tiny user-specified text correction with an
   obvious target and no structural, visual, behavioral, or release-risk change,
   skip even the formal expert/local-pass step; regenerate affected outputs and
   run the smallest relevant validation instead.
3. **Default review-class work to real subagents.** For audit, review,
   validation, acceptance, release-readiness, expert checking, or any case where
   the main agent would otherwise review its own nontrivial work, use a real
   read-only subagent by default. Use local-pass only when the work is tiny and
   deterministic, the platform delegation tool is unavailable, or the subagent
   would cross a hard boundary that requires asking first; record the exception
   in the dispatch card or integration note.
4. **Use real subagents for explicit delegation or parallel efficiency.** A
   real platform subagent is directly eligible when Xiao Q says `子agent`,
   `并行`, `独立测试`, or frames the task as a real delegation workflow. Phrases
   such as `专家` or `专员` must route to the stable expert first; review-class
   expert requests use a real subagent by default, while creation/research work
   uses a real subagent when independent/cold context, nontrivial review, or
   parallel value justifies the overhead.
5. **Prefer read-only reviewers and disjoint parallel workers.** Automatic
   review subagents are read-only by default. Automatic parallel workers need a
   named owner, non-overlapping scope, acceptance criteria, and a return
   contract before dispatch.
6. **Ask before spawn when risk is high or scope is unclear.** Ask if the
   subagent would touch private data, write outside an assigned temp/workspace
   scope, use credentials, push/publish, run destructive cleanup, or the write
   scope overlaps another owner.
7. **Never spawn silently.** Always announce the dispatch card before spawning a real platform subagent. The card must separate the stable q-workflow expert
   role from the platform run instance so Xiao Q does not see two ambiguous
   names. If no real platform subagent is running, say `local-pass`.
8. **Gate identity before naming.** Choose from the stable expert roster before
   inventing any label. A task-specific label, human-friendly nickname, or
   platform nickname may appear only as `Mission`, `agent_slot`, or
   `Run instance`; it must not become `Expert role` unless it passed New Expert
   Admission. If the main agent already announced an ad hoc expert name, correct
   the mapping immediately and log the protocol defect.
9. **Keep Chinese names visible.** Every user-visible expert card, review
   summary, integration note, and final handoff must show the stable English
   alias plus Chinese codename, such as `Workflow Distiller (沉炼)`. The Chinese
   name is not optional decoration; it is part of the user's recognition and
   memory model.

## Automatic Review Triggers

Treat these as default reviewer/validator opportunities even when Xiao Q did
not explicitly say `subagent`:

- nontrivial code, script, workflow, or skill changes where the main agent would
  otherwise review its own work;
- generated user-visible artifacts: HTML pages, dashboards, PPT/deck outputs,
  diagrams, reports, public docs, setup flows, or onboarding material;
- public, team, customer-facing, or promotion-ready handoffs;
- repeated correction, user-found miss, failed validation, or a rule change
  created from feedback;
- changes that affect install/setup, source/runtime mirrors, GitHub sync,
  package readiness, credentials/privacy boundaries, or release posture.

Default review mode is a real read-only subagent for nontrivial review-class
work. Local-pass is an exception, not the default, and must be justified when
used for audit/review/validation/acceptance work:

- `Code Auditor (码鉴)`: code/script/test/regression review, read-only unless a fix scope is
  explicitly assigned.
- `Pagewright (页匠)`: HTML/UI usability and responsive-render review.
- `Visual Arbiter (版衡)`: PPT, diagram, and exported visual artifact review.
- `Doc Architect (文构)`: document/report/spec clarity and reusable structure review.
- `Usability Validator (验用)`: install, onboarding, package, and first-user readiness review.
- `Workflow Distiller (沉炼)`: workflow-rule overreach, context-cost, and durable lesson review.

For HTML onboarding or setup pages, prefer two disjoint review scopes before
user handoff when the artifact is nontrivial: `Pagewright (页匠)` owns layout/product shell/
responsive/diagram issues, and `Usability Validator (验用)` owns first-user comprehension, success
criteria, failure recovery, and trust/privacy. The main agent integrates both
reports before asking Xiao Q for subjective review.

For any nontrivial user-visible artifact, the expert output must be durable
before handoff. Prefer `reports/agents/<trace_id>/<expert>-<method>.md` in the
active project or report hub. If the subagent can only return chat, the main
agent must persist the usable report there, then cite that path in the
integration note.

If no real platform delegation tool is available, the artifact is tiny and
deterministic, or a hard boundary requires asking first, run the same expert as
`local-pass` only after stating the exception. For tiny deterministic copy-only
fixes requested by Xiao Q, a formal expert pass is not required; record that the
change was copy-only and validate the regenerated output with targeted checks.
Do not close a nontrivial artifact, ask Xiao Q for final human review, push,
publish, release, upload, or sync a public package when the required real
reviewer/validator was skipped. If review is blocked or intentionally deferred,
report the blocker/deferred reason and keep the candidate local/pending.

## Parallel Execution Triggers

Use real subagents for parallel work when all of these are true:

- the work can be split into independent questions, validations, or file scopes;
- the subtask output can be integrated without rereading broad chat history;
- any write scopes are disjoint and explicitly owned;
- the subtask has a stop condition and evidence requirement;
- the main agent has useful non-overlapping work to do while the subagent runs.

Good parallel candidates:

- independent source scan while the main agent inspects local state;
- install smoke test in a temp directory while the main agent prepares docs or
  validates repo status;
- read-only code/doc/HTML/PPT review while the main agent runs formatting,
  scans, or builds;
- validator running tests, export checks, screenshots, or regression replay
  after the main agent has produced the artifact;
- two explorers with different evidence roles, such as official sources versus
  local project evidence.

Concurrency defaults:

- use at most one reviewer and one validator by default;
- use at most two real platform subagents in parallel unless Xiao Q explicitly
  asks for broader parallel work;
- do not spawn another agent for the same unresolved scope until the first
  report is integrated or cancelled.

## Externally Inspired Scenario Classes

These scenario classes are strong candidates for real subagents when the scope
is bounded and the hard boundaries below are respected. They synthesize public
multi-agent patterns such as context isolation, fan-out/fan-in, specialists,
handoffs, guardrails, tracing, stateful flows, and controlled validation.

| Scenario | Trigger wording | Default expert | Default mode | Boundary |
|---|---|---|---|---|
| Independent fan-out over the same input | `several independent questions`, `compare from different angles`, `can parallel`, `fan-out/fan-in` | `Source Scout (寻源)` plus the relevant domain expert | real subagents only for disjoint questions; main integrates | no duplicate broad review; each worker needs evidence and stop condition |
| Cold-context usability, install run, or human pilot | `new user`, `fresh environment`, `without chat history`, `installation specialist`, `promotion readiness`, `I try it as a new user`, `真实流程` | `Usability Validator (验用)` | real read-only or controlled sample subagent for isolated execution; local guided pilot when the user is acting as the test participant | temp workspace only; ask before credentials, profile changes, network-heavy installs, publish, or non-temp writes |
| Self-review risk after generated artifact | generated HTML/PPT/report/code/skill, `handoff`, `public/team/customer-facing`, `close the loop` | artifact owner: `Pagewright (页匠)`, `Visual Arbiter (版衡)`, `Code Auditor (码鉴)`, `Doc Architect (文构)`, or `Workflow Distiller (沉炼)` | real read-only subagent for nontrivial review; local-pass only for tiny deterministic work or unavailable delegation | reviewer is read-only unless explicit repair ownership is assigned |
| Current or niche research sidecar | `latest`, `current tools`, `compare platforms`, `source-backed`, `external examples`, `unknown ecosystem` | `Source Scout (寻源)` | explorer while main inspects local/project state | high-stakes or paid decisions require ask-before-spawn and source-quality constraints |
| Sequential phase handoff | `research then build then review`, `stateful workflow`, `multi-stage`, `conditional branch`, `loop` | `Doc Architect (文构)` or `Workflow Distiller (沉炼)` as coordinator; phase owner by domain | phase handoff, not parallel by default | do not parallelize dependent phases; each phase publishes state, acceptance criteria, and next owner |
| Guardrail or release-readiness review | `before sharing`, `public-ready`, `team-ready`, `customer handoff`, `policy/privacy/safety check` | `Usability Validator (验用)` for package readiness, `Workflow Distiller (沉炼)` for workflow policy, domain expert for artifact quality | read-only validator | no push, publish, upload, credential use, or classification expansion by subagent |
| Validator replay after implementation | `run validation`, `screenshot check`, `regression replay`, `export check`, `test independently` | `Code Auditor (码鉴)`, `Pagewright (页匠)`, `Visual Arbiter (版衡)`, or `Usability Validator (验用)` by artifact type | subagent-as-tool when validation can run independently | commands must be bounded and non-destructive; privileged/network/non-temp writes require approval |

Do not promote `complex task` alone into a real subagent. First identify the
independent scope, phase boundary, reviewer role, or validator evidence that
justifies delegation.

## Hard Boundaries

Do not auto-spawn real subagents for:

- credentials, secrets, private-data expansion, customer/company confidential
  artifacts, or unclear data classification;
- push, publish, release, external upload, or deleting/cleaning files;
- broad filesystem writes, broad refactors, or overlapping write ownership;
- vague strategy work without a bounded output contract;
- tasks where Xiao Q explicitly asked for no agents or a single-threaded path.

Use `ask-before-spawn` when a reviewer or validator would need privileged
commands, network access, non-temp writes, or user profile changes.

## Review Before Human Review And Publish

For any nontrivial artifact or release candidate that Xiao Q is expected to
judge, expert review comes before Xiao Q's human review. The main agent may
write local notes, reports, candidate files, screenshots, and review summaries
freely inside the approved workspace, but must not ask Xiao Q to do final
subjective review until the relevant expert pass or real subagent review has
run and the findings have been integrated or explicitly deferred.

Required order:

1. Create the local candidate.
2. Run the mapped expert review or real subagent review.
3. Persist the expert report under the standard report path.
4. Patch and validate locally.
5. Write an integration note that maps findings to fixes, deferrals, and
   remaining risks.
6. Present a compact review summary, remaining risks, and exact preview path to
   Xiao Q.
7. Wait for Xiao Q's explicit approval before any push, publish, release,
   upload, or public package sync.

If Xiao Q points out that an expert review, report path, or integration step
was skipped, treat it as a workflow defect. Run the missing review, integrate
or defer each finding explicitly, update the relevant expert/process rule, and
record the lesson before closing the task.

`push`, `publish`, `release`, external upload, and GitHub-bound sync are always
approval-gated even when local validation passes. Local durable logging and
local skill/runtime updates are encouraged and do not need separate approval
unless they touch credentials, broad user profile state, or destructive cleanup.

## Dispatch Matrix

| Trigger | Default expert | Default mode | Real subagent threshold | Ask before spawn |
|---|---|---|---|---|
| install/onboarding/package usability | `Usability Validator (验用)` | local pass for checklist or human-in-loop pilot; subagent for cold run | user says `安装专员`, `测试专员`, `子agent`, `新用户环境`, `我作为新用户试用`, or public/team readiness | credentials, real user profile, non-temp writes, publish |
| code review, risky script, test failure | `Code Auditor (码鉴)` | real read-only subagent by default for review; local-pass only for tiny deterministic diffs | user says code expert/reviewer or diff is broad/risky | write fixes, overlapping files, destructive commands |
| HTML/UI/page/dashboard | `Pagewright (页匠)` | local pass for review; worker for assigned HTML build | user asks HTML expert or UI build/review is nontrivial | browser/network install, broad asset writes |
| PPT/diagram/visual artifact | `Visual Arbiter (版衡)` | local visual pass | exported artifact exists and user asks expert review | editing deck/generator, private/customer deck |
| research/current/niche direction | `Source Scout (寻源)` | explorer subagent when source scan can run independently | current info, multiple source roles, or user asks research expert | paid/high-stakes/legal/medical/financial decisions |
| document/standard/report structure review | `Doc Architect (文构)` | real read-only subagent by default for nontrivial review; local-pass for tiny deterministic docs | long reusable doc or independent structure review | publishing, policy-sensitive wording |
| repeated miss/workflow lesson or rule review | `Workflow Distiller (沉炼)` | real read-only subagent for review/critique; local-pass only for tiny deterministic sedimentation | repeated feedback, workflow miss, user asks sedimentation, or workflow-rule review | changing public/company mirrors or retiring skills |

## Spawn Preview

Use one of these visible multi-line cards. Keep one field per line so Xiao Q can
scan role, run instance, mode, task, permissions, and boundaries without
parsing a long sentence.

```text
Subagent start
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: <platform type>/<nickname-or-id>
Domain memory: <legacy domain label if relevant, otherwise none>
Mode: <subagent-as-tool|phase-handoff|parallel-worker>
Mission: <one-line mission>
Permissions: <read-only|bounded-run|temp-write|owned-write>
Boundaries: <no push/publish/credentials/...>

Expert pass
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: main-thread/local-pass
Domain memory: <legacy domain label if relevant, otherwise none>
Mode: local-pass
Mission: <one-line mission>
Permissions: <read-only|bounded-run>
Boundaries: <no platform subagent/no file edits/...>
Reason: <tiny deterministic|no cold context needed|no native delegation>

Subagent done
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: <platform type>/<nickname-or-id>
Domain memory: <legacy domain label if relevant, otherwise none>
Result: <done|partial|blocked|failed>
Key findings: <short summary>
Next: <integrate|patch|ask|defer>
```

If the platform nickname is unknown before spawn, first say:

```text
Subagent plan
Expert role: <stable role, e.g. Workflow Distiller (沉炼)>
English name: <Workflow Distiller>
Chinese name: <沉炼>
Run instance: <platform type>/pending
Domain memory: <legacy domain label if relevant, otherwise none>
Mode: <mode>
Mission: <mission>
Permissions: <permissions>
Boundaries: <boundaries>
```

Then immediately follow with the final mapping.

For parallel or multi-expert work, emit one dispatch card per real subagent. A single combined paragraph or one card naming several experts does not satisfy the gate. If a spawn attempt fails, is rejected by platform constraints, or is retried with different parameters, retry after a failed spawn only after treating the retry as a new actual dispatch and showing a fresh card before the retry. After each successful spawn, backfill the final mapping with the platform type, nickname, and id before waiting on or citing that expert.

Field meaning:

- Readable role names: show both English alias and Chinese codename in every user-visible dispatch card, for example `English name: Code Auditor` and `Chinese name: 码鉴`.

- `Expert role`: stable q-workflow role and skill contract, such as `Usability Validator (验用)` or
  `Code Auditor (码鉴)`. This is the name Xiao Q should use when improving the reusable expert.
- `Domain memory`: optional legacy domain label such as `控审-钱学森` or `注审-沈括`. This helps Xiao Q recognize historical review tracks, but it must never replace the stable `Expert role`.
- `Run instance`: platform execution handle for this run, such as
  `explorer/Darwin/019...` or `worker/Aquinas/019...`. This is trace evidence
  only and may change every run.
- `Mode`: how control is delegated: local pass, subagent-as-tool, phase handoff,
  or parallel worker.
- `Permissions`: what the expert may do.
- `Boundaries`: what the expert must not do without main-agent or user approval.

## Scorecard

After a material expert run, record or report:

```text
expert:
mode:
platform_agent:
trigger_match: pass/fail
packet_complete: pass/fail
independence_value: high/medium/low
findings_useful: high/medium/low
overhead: high/medium/low
user_visible_mapping: pass/fail
self_review_risk: high/medium/low
parallel_value: high/medium/low
write_scope_safe: pass/fail/not-applicable
next_policy_patch:
```

Use the scorecard to decide whether a role should remain experimental, become a
default auto-spawn candidate, or be demoted to local-pass only.

## Anti-Patterns

- Inventing a temporary expert name for one run, such as a structure auditor
  persona, instead of routing to the nearest stable role and recording any new
  role idea through New Expert Admission.
- Doing the work in the main agent and then calling it an expert result.
- Spawning a subagent just to repeat the same read scope.
- Hiding the platform nickname/id from Xiao Q.
- Letting an expert write files without assigned ownership.
- Spawning multiple experts before the primary owner and acceptance criteria
  are clear.
