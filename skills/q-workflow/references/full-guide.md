---
name: q-workflow
description: Reusable project workflow for Codex and other terminal-capable coding agents. Use when a user wants to create, clone, resume, organize, document, update, commit, push, migrate, or recover a project with durable memory files, project-local skills, environment setup notes, Git handoffs, and automatic use of relevant generic skills.
---

# Q Workflow

Use this skill to make a project recoverable across agent sessions, machines,
and interruptions. It is packaged as a Codex skill, but the underlying workflow
is file- and Git-based. Any terminal-capable coding agent can follow it by
reading this file, the workflow hub, and the project's durable memory files.
The user should be able to say a short prompt such as
`Continue my project. Use q-workflow.` and the agent should recover the working
state from files and Git.

## Core Principle

Separate four things:

- Workflow memory lives in this generic skill.
- Reusable capabilities live in generic skills.
- Project-specific rules live in the target project repository.
- Project facts and current state live in durable project files and Git.
- Personal cross-project activity state lives outside project repositories.

Do not store project-specific facts in generic skills. Do not store personal
active-work details in public or reusable skill repositories.

When the user asks to update a workflow rule, reusable lesson, or skill
behavior, treat it as a propagation task, not a single-file edit. Identify the
related source, runtime, workflow bootstrap, company variant, adjacent skill,
validation gate, and durable memory surfaces. Update all applicable surfaces or
record why a surface was intentionally skipped.

## Product Goals

The workflow should stay efficient, easy to use, and extensible for other users:

- Efficient: keep ordinary task completion focused on the active project. Avoid
  multi-repository synchronization unless it is needed for recovery,
  handoff, or a reusable workflow change.
- Easy to use: the user should be able to resume work with short prompts and
  should not need to manage Git housekeeping after every small task.
- Extensible: new domains should add project-local skills, templates, or
  optional helper scripts before changing the generic workflow core. Promote
  only patterns that are reusable across projects or users.

## Capability-Native Evolution

Treat native agent features, scripts, MCP tools, and sub-agents as capability
engines behind q-workflow's authority, safety, observability, and recovery
gates. Do not keep local workflow rules just because they were historically
useful, but do not delete them just because a platform feature now overlaps
them.

When the user asks to improve workflow structure, prevent workflow
obsolescence, adopt an agent-native capability, or retire a local rule, read
`references/workflow-evolution.md`. The default decision is one of: use native,
wrap native with q-workflow gates, keep local, or retire local after a realistic
validation scenario.

## Context Efficiency

Use progressive reading by default:

1. Read routing state first: personal `ACTIVE_WORK.md`, the active work item,
   registry entries, project README, and durable state files.
2. Use `rg`, file listings, Git status, and recent logs to locate the relevant
   surface before opening long files.
3. Read targeted sections first. Expand to full files only when the change is
   high-risk, cross-cutting, or the local context proves insufficient.
4. Short-circuit completed work. If durable state clearly says the previous
   round is complete, do not run repository checks, validation, commits, or
   pushes just to re-confirm it.
5. Record assumptions when working from partial context.

Use Quick Resume for general continuation prompts and recovery evaluations:

- When the user asks to continue, resume, recover, or evaluate recovery without
  naming a specific project, prefer this first-pass order: workflow hub
  `ACTIVE_WORK.md`, active work item, Git dirty/untracked status for the
  workflow hub or named project, then dirty evidence such as drafts or new work
  items.
- Delay opening skill files, project histories, validation logs, and unrelated
  repositories until routing state is unclear, stale, contradictory, dirty, or
  missing a decision-critical fact.
- Before reading hidden truth, scoring files, or answer keys in a recovery
  evaluation, inspect dirty and untracked files surfaced by Git status. A
  recovery evaluation that skips this step should not receive a high score.
- A first-pass recovery report should include the recovered objective, next
  safe action, confirmed facts, skipped or unrecovered low-impact detail,
  files opened, commands run, repos touched, elapsed-time estimate, turn count,
  and separate scores for correctness, resource economy, and speed or
  momentum.
- When a recovery sees multiple dirty repositories, classify them before
  acting: workflow hub metadata, target project work, unrelated project work,
  generated artifacts, and unknown ownership. Do not treat a dirty repo as a
  clean rename, migration, validation, or sync target until its dirty state is
  either part of the current objective or explicitly checkpointed.

Use the shortest reliable recovery path, not the most exhaustive path:

- Recover the critical state first: current objective, active or paused status,
  next safe action, changed files or artifacts, validation and sync gaps, and
  any user-visible correction or decision that could change the work.
- Treat missing low-impact detail as acceptable when it does not change the
  next action. Say what was not recovered instead of expanding into broad
  scans for perfect recall.
- Prefer bounded evidence over completeness: a clean route plus known gaps is
  better than spending large context on unrelated history.

## Workflow Experiments

Use `experiments/` for draft workflow contracts that standardize repeatable
agent task flow before adding a runtime runner. The current version-0 contract
uses this fixed stage order:

```text
route -> plan -> edit -> validate -> review -> checkpoint
```

Validate experiment drafts with:

```powershell
python .\scripts\validate_experiments.py
```

Treat these YAML files as manual/agent execution contracts. They are not
external runner inputs, and they should not bypass the normal safety gates for
destructive changes, credentials, public sync, remote pushes, or broad
dependency installation.

## Uncertainty Discipline

Do not fill gaps by guessing. If a title, source, owner, result, date,
conclusion, command, or file path is not known from durable state or observed
evidence, say it is unknown, unverified, or needs retest.

When recovering state or recording results:

- distinguish confirmed facts from inferred candidates;
- label partial evidence as `unknown`, `unverified`, `likely`, or `needs retest`
  instead of presenting it as fact;
- do not promote a similar local artifact to the target unless it matches the
  user's URL, title, source id, file name, or other identifying clue;
- prefer an honest gap over a clean-looking but invented record;
- if a guess was recorded, correct the durable record and explicitly downgrade
  the old entry to mistaken or unverified evidence.

## Real Sample Evidence

When a task uses real-world samples as evidence, such as videos, audio files,
benchmarks, public examples, user-provided documents, screenshots, or provider
test cases, keep a durable sample registry or equivalent work-item section.

Record enough for recovery before treating the work as complete:

- stable source id, URL, or file hash, with private tracking parameters removed;
- title/topic and creator/source when known;
- why the sample was used and what user question it answered;
- commands, providers, models, presets, or review methods used;
- output paths for metadata, transcripts, notes, scores, screenshots, or logs;
- result state: completed, partial, failed, or inconclusive;
- key conclusions and workflow/product lessons that survive local cleanup;
- gaps and follow-up checks.

Ignored `local-state/` files are evidence, not durable memory. A completed
analysis is not recoverable if only chat text or ignored artifacts contain the
conclusion. If the user later names a sample that cannot be recovered from
durable state, treat it as a workflow defect and add the missing registry rule
or entry immediately.

## Encoding Safety

Use UTF-8 for Markdown, skill, state, prompt, and workflow files. On Windows,
PowerShell output can display UTF-8 Chinese text as mojibake if the encoding is
not explicit; do not copy mojibake back into durable files.

Rules:

- Prefer ASCII trigger aliases in reusable workflow rules when a phrase must be
  typed exactly, for example `checkpoint`, `emergency save`, `save state`, and
  `pause note`.
- Chinese discussion text is fine, but durable command triggers should not rely
  on Chinese as the only spelling.
- When reading or writing Chinese-bearing files with Windows PowerShell, use
  explicit UTF-8 handling where practical, such as `Get-Content -Encoding UTF8`
  and UTF-8 writes.
- Before committing workflow/state changes that touched Chinese text, search
  for replacement characters or common mojibake fragments such as `U+FFFD`, `绱`,
  `淇`, `鐜`, `瓨`, and `褰`. If a hit is intentional because the file documents
  a past mojibake incident, leave a clear note.

## Parallel Agent Workflow

Use sub-agents to reduce idle time only when their task is concrete, bounded,
and safe to run beside the main work. The main agent remains responsible for
the plan, integration, durable memory, commits, pushes, and final user-facing
answer.

First split the work:

- Critical path: the next blocking task the main agent should do locally.
- Sidecar tasks: independent research, log analysis, download monitoring,
  validation, or bounded patches that can run in parallel.
- Background tasks: long downloads, model setup, video/audio processing,
  benchmarks, or other commands that can continue while planning or docs move
  forward.

Delegate when:

- a large download, benchmark, transcription, conversion, or test run would
  otherwise leave the main agent idle;
- research can be answered independently while the main agent prepares code,
  tests, or docs;
- implementation can be split into disjoint files or modules with clear write
  ownership;
- a second reviewer can inspect logs, diffs, docs, or validation output without
  blocking the next local step.

Do not delegate when:

- the result blocks the immediate next action and can be handled faster by the
  main agent;
- the task requires broad judgment, vague exploration, or tight integration;
- multiple agents would edit the same file, work item, lockfile, generated
  artifact, or Git index;
- the task would require credentials, destructive cleanup, publishing, global
  configuration, or unclear network/data access.

Sub-agent task briefs must state:

- objective and expected output;
- read scope and write scope;
- whether file edits are allowed;
- output directory for downloads or experiments, preferably under
  `local-state/<task>/<run-id>/`;
- commands that are allowed or forbidden;
- independent report or work item path when durable notes are needed;
- explicit `no commit, no push` unless the user and main agent deliberately
  chose otherwise.

While sub-agents run, the main agent should continue non-overlapping work
instead of waiting by reflex. Wait only when the next critical-path action
needs the result. When a sub-agent returns, review its changes or findings
before integrating them, then record important outputs, gaps, and decisions in
the relevant work item.

## Platform Session Failure Recovery

If the agent platform repeatedly reports a remote compaction, summarization, or
session-continuation failure, treat the current chat window as unreliable
platform state instead of asking the user to keep retrying in that window.

Rules:

1. If the current session can still write files before switching away, update
   the active work item with a short `Session Recovery Note`:
   - the latest user-visible request;
   - the latest completed step;
   - the next intended action;
   - relevant uncommitted, unpushed, or unvalidated state;
   - the visible platform error text when useful.
2. If the current session cannot write files, ask the user to open a new
   session and paste a short recovery prompt plus any screenshot of the last
   visible state.
3. In the new session, recover from durable state first: assistant profile,
   `ACTIVE_WORK.md`, the active work item, `PROJECT_REGISTRY.md`, and only then
   recent Git status/logs or screenshots.
4. Do not commit, push, run validation, or resume expensive commands until the
   recovered durable state has been compared with the user's latest prompt or
   screenshot.
5. For long, remote, model-heavy, or interruption-prone work, keep a rolling
   checkpoint in the work item after meaningful plan changes, user corrections,
   or completed substeps. Interruption recovery should not depend on an
   end-of-round summary.
6. If the user says the old chat window keeps triggering the same failure,
   continue in the new session from files and screenshots rather than trying to
   rely on the broken window.
7. After a real recovery round, run a short consolidation pass before closing:
   identify one reusable failure mode, patch the smallest correct workflow or
   reference layer, sync only the needed runtime mirrors, and record the
   validation result. Avoid turning every recovery into broad multi-repository
   cleanup.
8. If the workflow hub was updated during recovery, refresh only the affected
   runtime mirror files needed for future routing, such as `PAUSED_WORK.md` or
   the active work item. Do not bulk-copy the workflow hub unless the user is
   doing machine bootstrap or mirror repair.

Automatic detection is limited to visible signals. The agent usually cannot
see an internal platform compaction failure before it happens, but it should
treat these as checkpoint triggers when it can still act:

- the user says the old window is stuck, repeating an error, or asks to test
  recovery;
- the conversation shows a platform/session/compact error;
- the work is about to start a long, expensive, remote, or model-heavy step;
- the task just finished a meaningful substep, accepted a user correction, or
  changed direction;
- the user says `checkpoint`, `emergency save`, `save state`, or `pause note`.

Emergency save behavior:

1. Stop nonessential work immediately.
2. Update the active work item with `Session Recovery Note` or `Emergency
   Checkpoint`.
3. Record the latest user request, current plan status, files changed, commands
   currently relevant, validation/sync gaps, and the next 1-3 actions.
4. Do not commit or push unless the user explicitly asks, or unless the work
   item says a local commit is the required recovery checkpoint.
5. Reply with the new-session recovery prompt and the work item path.

Useful new-session prompt:

`Recover from a platform compact/session failure. Use q-assistant-profile and q-workflow. First read ACTIVE_WORK.md and the active work item. Do not commit, push, or run validation until you reconstruct the current state. Last visible request was: <paste last request>.`

## Personal Cross-Project State

When a private workflow hub exists, use it as the first routing layer for
interruption recovery, project switching, and parallel work.

Expected structure:

- `PROJECT_REGISTRY.md`: project names, local paths, remotes, resume skills,
  and status.
- `personal-state/ACTIVE_WORK.md`: small index of current focus and active or
  recent work items.
- `personal-state/ASSISTANT_HELP.md`: short capability guide to answer user
  prompts such as "help", "features", or "what can you do".
- `personal-state/SKILL_SYNC.md`: optional inventory of local skills, durable
  sources, install methods, and cross-machine migration notes.
- `personal-state/PAUSED_WORK.md`: short queue of interrupted tasks to present
  when the user asks to continue previous work.
- `personal-state/work-items/<id>.md`: one file per active or paused work item.
- `personal-state/journal/<date>/<entry>.md`: notes for important recovery
  findings.

Rules:

- The workflow hub stores routing data, active task intent, repository paths,
  owner/session notes, and next actions.
- Project repositories remain authoritative for project facts, outputs,
  decisions, and validation status.
- Skills remain authoritative for reusable behavior.
- Prefer one work-item file per task so multiple agents do not repeatedly edit
  the same file.
- When switching away from unfinished work, mark the work item as paused and add
  it to `PAUSED_WORK.md` with the reason and next concrete action.
- Keep `ASSISTANT_HELP.md` current when user-facing workflow capabilities are
  added, changed, or retired.
- Store only minimal routing data in the workflow hub; do not store
  credentials, private secrets, generated deliverables, or private data dumps.
- Create or update the personal work item as soon as a task becomes concrete,
  even before code, docs, or tests are complete. Interruption recovery must not
  depend on an end-of-round checkpoint.
- Distinguish reference material from owned work. Imported third-party skills,
  cloned examples, downloaded tutorials, and web pages are evidence, not the
  active project, unless the work item says they are the deliverable.
- Treat agent-local skill install folders as runtime copies. If a local skill
  becomes part of normal work, promote it into an owned Git-tracked source or
  record its source, install method, version, license posture, and migration
  notes in `SKILL_SYNC.md`.

## Lesson Capture

Capture reusable lessons without waiting for the user to remind you. Record a
lesson when a work round reveals:

- a repeated environment issue or workaround;
- a recovery gap, sync failure, or Git/network failure mode;
- a validation lesson that should change future checks;
- a user preference that should change collaboration behavior;
- a workflow friction point that caused wasted time or context.
- a scope or completion mistake where adjacent validation was treated as the
  original target being complete.
- a completed real-sample analysis was not recorded durably enough to recover
  source, result, and conclusions after compaction.

Use the right layer:

- Generic reusable behavior belongs in `q-workflow` or another reusable skill.
- Skill-making rules belong in `q-skill-creation`.
- User collaboration preferences belong in the personal `q-assistant-profile`.
- Project facts, outputs, and decisions belong in the project repository.
- Active routing and incomplete work belong in personal work items.

If hook-assisted lesson capture is configured, treat hook output as an inbox of
candidates, not as authoritative memory. Review hook candidates during resume
or end-of-round cleanup, then decide whether to discard them or promote them to
the correct durable layer.

Hooks may remind the assistant to record lessons after `Stop`, `PreCompact`,
`SubagentStop`, or prompt-trigger events, but hooks should not directly edit
core shared state, commit, push, or make product decisions.

## Summary And Sedimentation

Use this path when the user asks for `总结/沉淀`, `总结`, `沉淀`,
`consolidate`, `summarize`, or `lessons learned`, or when a major work node
has closed and the agent should consolidate proactively.

The pass should:

1. summarize the execution and feedback loop;
2. identify root causes, not only symptoms;
3. research adjacent evidence, prior art, local skills, or counterexamples when
   the lesson is nontrivial;
4. validate the lesson with realistic evidence from the current work when
   possible;
5. update the right durable layer: project state, reusable skill, assistant
   profile, public-safe generic mirror, validation script, or handoff note;
6. record residual risks and the next trigger.

Do not treat this as a pure chat recap. It is complete only when useful lessons
are either durably captured or explicitly rejected/deferred with a reason.

## Skill And Research Routing

Use the relevant q-workflow skill when the user's task matches one:

- Creating, updating, or reviewing a reusable skill must use
  `q-skill-creation`.
- Research-heavy work, public examples, provider/tool selection, license
  checks, current-info uncertainty, source strategy, or stuck-work exploration
  should use `q-research-discovery`.
- Tiny source checks can stay in the main agent when they are narrow and do not
  need durable source lessons.
- If the relevant skill is unavailable or cannot be applied, say so briefly,
  use the best fallback, and record the gap when it affects recovery or
  repeatability.

This routing keeps successful lessons reusable without turning every task into
a large process.

## Command Alias Layer

Treat common user shortcuts as intent aliases, not as shell commands. Support
English and Chinese aliases, and treat broad or fuzzy phrases as candidates
that may need one short clarification when multiple intents match.

Recommended first-pass aliases:

| Intent | English aliases | Chinese aliases | Fuzzy examples |
|:---|:---|:---|:---|
| Help | `help` | `帮助` | `能做什么`, `怎么用` |
| Status | `status` | `状态` | `现在怎样`, `到哪了` |
| Resume | `resume`, `recover`, `continue` | `恢复`, `继续` | `接着做` |
| Checkpoint | `checkpoint`, `save state` | `保存状态`, `打点` | `先记一下`, `留个恢复点` |
| Lightweight TODO | `TODO`, `todo`, `TODO:<text>` | `TODO：<内容>` | `记个小点`, `以后可能要做` |
| Token usage | `TOKEN`, `token`, `tokens`, `token usage` | `token`, `当前token`, `项目token`, `总token` | `看看这轮用了多少`, `查一下token` |
| Summary and sedimentation | `consolidate`, `summarize`, `lessons learned` | `总结/沉淀`, `总结`, `沉淀` | `做个大总结`, `把这轮经验沉淀一下`, `复盘并更新skill` |
| Loop run | `loop run`, `run loop`, `bounded loop`, `loop engineer` | `循环执行`, `循环`, `循环工程师` | `一直跑到完成或超时`, `给你目标和终止条件自己推进` |
| Update rules | `update-rules` | `更新规则` | `优化工作流`, `记住这次教训` |
| Sync rules | `sync-rules` | `同步规则` | `看看有没有漏同步`, `通用skill有没有漏` |
| Workflow hygiene | `workflow-hygiene`, `hygiene` | `工作流清理`, `清爽性` | `工作流有点臃肿`, `帮我清理一下` |
| Workflow identity | `workflow-identity`, `skill-fit`, `skill portfolio` | `工作流特色`, `skill匹配`, `技能分层` | `这个skill该不该进工作流`, `工作流有什么特别` |
| Targeted push | `push bit`, `push git` | `推送bit`, `推送git` | `提交到bit`, `同步到git` |
| Publish | `publish`, `upload`, `push` | `发布`, `上传`, `推送` | `提交上去`, `同步到远端` |

Default behavior:

- When the user gives several tasks at once or the TODO output grows beyond a
  few items, use a compact numbered list. Keep numbers stable within the
  current round and close, pause, block, or defer each item explicitly.
- `help`, `status`, and `resume` may read routing state and Git status directly.
- `checkpoint` should update the active work item or durable state before doing
  more work; commit only when the current workflow policy calls for it.
- `TODO` is a micro personal-inbox path. List or append
  `personal-state/TODO.md` in the private local hub; create the file from the
  standard template if it is missing. Do not scan project repos, create a work
  item, validate, commit, or push merely because a TODO was listed or added.
- `TOKEN` / `token` is a micro local-usage path. Run
  `scripts/token_usage.py --format html --open` from this skill when the helper
  is installed, then report the dashboard path and a brief current/session
  health summary. If local Codex session logs or the helper are unavailable,
  say that directly instead of inventing usage numbers. Treat these as local
  log totals and project attribution heuristics, not billing guarantees.
- `总结/沉淀` / `总结` / `沉淀` should run the Summary And Sedimentation path:
  summarize, research when useful, validate lessons, update durable layers, and
  record residual risks.
- `loop run` / `循环执行` should run a bounded autonomous loop and should assume
  unattended execution by default unless the user explicitly asks for stepwise
  review. Confirm or infer a concrete goal, stop conditions, validation
  cadence, and progress boundary; then run a permission preflight before
  starting long unattended work. Do not make the user repeat the unattended
  boilerplate in the prompt. In that preflight, identify low-risk local
  reads/writes, tests, formatters, local commits, or other command prefixes
  likely to be needed, and request reusable approval where the platform
  supports it. Do not pre-approve destructive
  cleanup, credentials, public pushes, broad installs, or unclear data exposure.
  During the loop, keep implementing, validating, and correcting until the goal
  is reached or a stop condition is hit. If an unapproved action becomes
  necessary while the user is away, record the blocked action, switch to an
  allowed alternative or another useful branch, and checkpoint before stopping;
  do not wait idly on a single approval unless all meaningful branches are
  blocked. Stop conditions should include completion, an
  explicit time boundary, token/context pressure, a configured no-progress
  threshold, permission boundaries, destructive action, unclear data exposure,
  or a validation blocker that cannot be reduced safely.
- `update-rules` should use `q-skill-creation`, place lessons at the right
  layer, and validate changed skills.
- `sync-rules` should audit generic skill/rule changes across source, starter,
  runtime, public, private, workflow bootstrap, and GitHub remote copies before
  claiming completion.
- `workflow-hygiene` should read `references/workflow-hygiene.md`, score
  bloat/drift/identity risk, and separate automatic cleanup from ask-before
  cleanup.
- `workflow-identity` and `skill-fit` should read
  `references/workflow-identity.md` and explain how q-workflow improves skills
  through recovery, routing, authority, validation, and sedimentation.
- User-defined remote shortcuts such as `push bit` / `推送bit` and `push git` /
  `推送git` may be treated as explicit target aliases once confirmed. If the
  target remains unclear, ask one concise clarification before pushing. Public
  or cross-profile targets still require the normal scan gates and final
  confirmation.
- `publish`, `upload`, and `push` must run the relevant scan, diff, status,
  remote freshness gate, and remote checks first. Public-facing pushes require public-safe scans and
  any required final confirmation.

Ambiguity handling:

- Treat broad words such as `sync`, `同步`, `upload`, and `上传` as ambiguous
  when they could mean rules, runtime mirrors, repository commits, or public
  publishing. Use context if it is clear; otherwise ask one concise question
  with 2-3 concrete options.
- Do not let fuzzy matching trigger destructive actions, credential handling,
  global configuration, or public publishing without the normal safeguards.

## Short Resume Prompts

When the user says a general resume phrase, including English prompts such as
`Continue my project. Use q-workflow.` and Chinese prompts such as
`继续我的项目，使用 q-workflow。`:

1. Find the user's workflow hub from the assistant profile or project registry.
2. Read `personal-state/ACTIVE_WORK.md`.
3. If it says there is no active focus and the user did not ask to continue
   paused work, give a compact status handoff and offer paused or new-work
   options. Do not scan Git history or validate repositories by default.
4. If it names an active work item, open that file and check the status first.
   If the item is already `Completed`, report the completed state and next
   options without reopening the round.
5. If no active work item exists and the user asks to continue previous,
   earlier, unfinished, or paused work, read `personal-state/PAUSED_WORK.md`
   and present 2-5 candidates with short descriptions.
6. If no active or paused work item is named, do a recovery scan before asking:
   - list recent files under `personal-state/work-items/`;
   - inspect `PROJECT_REGISTRY.md` for non-placeholder projects;
   - check recent Git status/logs for the workflow hub and registered projects;
   - inspect recently modified local skills under the agent's skills directory;
   - use repo names, local paths, URLs, user names, or project names in the
     user's prompt as routing evidence.
7. Choose a target only when the evidence is specific. Otherwise present 2-4
   concrete recovery candidates and ask which one to resume.
8. Once the target is clear, immediately create or update the matching work item
   and `ACTIVE_WORK.md`.

If the prompt names a specific project, the named project overrides the latest
active work item. If the prompt names the user rather than a project, use the
assistant profile and workflow hub first, then choose from the active or
registered projects.

## Permission Posture

Prefer low-friction approvals without reducing safety:

- For a new user, ask once during setup whether they prefer an efficient
  low-friction approval posture or a conservative approval posture, then record
  the answer in their assistant profile or personal state.
- For routine, low-risk, recoverable operations needed for the current task,
  use tool-level approval requests directly and choose narrowly scoped reusable
  approval rules when available. Examples include local Git index writes,
  local commits, normal test commands, dependency installs, skill installs, and
  temporary proxy retries.
- Do not request approvals for work that is not needed to answer the user's
  current prompt. A completed-state resume should not trigger new Git commits
  or pushes just because the repository can be inspected.
- Ask explicitly before destructive actions, credential handling, global
  configuration changes, publishing or releasing, deleting or moving large
  directory trees, changing unrelated user files, or actions with unclear blast
  radius.

## Skill Portability

Local installed skills are useful for testing, but they should not become the
only copy of an important workflow:

- Experimental skills may stay local while being evaluated.
- Common skills should live in a Git-tracked source repository, or be recorded
  in the workflow hub's `SKILL_SYNC.md` with source URL/path, install method,
  current status, license/attribution notes, and restore instructions.
- Third-party skills should be referenced, not copied, unless the license
  permits reuse and attribution is recorded.
- During machine migration, restore durable repositories first, then regenerate
  or reinstall local skill copies from their recorded sources.

## Help and Feature Prompts

When the user asks for help, features, available commands, "what can you do",
or similar:

1. Read `personal-state/ASSISTANT_HELP.md` if it exists.
2. Summarize only the currently useful capabilities, with short examples.
3. Mention paused-work recovery options when paused work exists.
4. Offer concrete next actions instead of listing every internal rule.

Use proactive hints sparingly. A hint is useful when:

- a task is completed and there is no explicit next step;
- paused work remains that the user may reasonably have forgotten;
- a newly added workflow feature directly helps the user's current situation;
- the user appears blocked, uncertain, or asks broad "what next" questions.

Avoid repeating the same hint in every response. Keep hints brief and actionable.

## Handoff Next Options

For substantial final handoffs, `Recommended Next` is a hard gate from `q-standard-contract.md`; use a short `Recommended Next` block after the
status summary and validation notes. This is required for major task nodes,
workflow-rule changes, release/test loops, push/publish preparation, project
migration, and multi-step requests with meaningful remaining choices. If Xiao Q
explicitly points out a missing next-step block, repair the current reply and
record the correction instead of treating it as optional polish.

Use this shape:

```text
**Recommended Next**
1. Continue the most likely next validation or repair path. (Recommended)
2. Continue the remaining independent test items.
3. Run 1 then 2 in order.
4. Give a different direction.
```

Keep it concrete to the current work. Use 2-4 options, not a long menu. The
first option should be the recommended default, and one option may combine the
obvious sequence when that saves Xiao Q from typing a long prompt. For a tiny
one-step answer, direct command result, exact TODO path, or a prompt that asks
for no extra guidance, omit the block and answer normally.

## Work Item Contents

Each active work item should be concise but sufficient for a fresh session:

- Objective and current status.
- Status values should distinguish `Active`, `Paused`, `Completed`, and
  `Blocked` rather than leaving stale handoff wording.
- Local paths and remotes involved.
- Reference URLs, imported example skills, or tutorials being used.
- Decisions made, open questions, and the next 1-3 actions.
- Validation and sync gaps, including network failures and uncommitted work.
- For append-only work items, prefer semantic headings over hand-maintained
  continuous numeric `## 12.` sections; reserve numbered headings for stable
  procedures or generated TOCs.
- A `Session Recovery Note` when platform/session failures, compaction
  failures, or broken chat windows could hide the latest user intent.

Use this brief shape for new work items and substantial first prompts:

- Role or working mode: the kind of help needed.
- Current state: what exists, what is active, and what has already been tried.
- Task: the concrete next outcome.
- Constraints: paths, permissions, time, privacy, tools, style, and validation
  requirements.
- Output: the expected artifact, report, patch, decision, or checkpoint.
- References: exact files, URLs, screenshots, source ids, or examples.

For project facts, prefer durable files and Git over chat memory, searchable
notes, RAG, or fine-tuned style. Search and RAG can help find background
material; they should not be treated as the authoritative current project
state unless the project explicitly defines them that way.

Update the work item after planning discussions that change direction, not only
after file edits.

## Checkpoint and Push Cadence

Prefer recoverable checkpoints over constant pushing:

- Create or update the personal work item as soon as a task becomes concrete.
- Use local commits for meaningful, recoverable checkpoints, especially before
  switching tasks or ending a long round.
- Record local notes and commits after key checkpoints, user-facing
  deliverables, or completed work rounds when useful. Push only after Xiao Q
  explicitly approves the current candidate; recovery risk is a reason to ask
  for sync, not to push silently.
- Before pushing to GitHub, run `scripts\validate-push-readiness.ps1` when available, or fetch/pull/rebase the relevant remote branch first unless that repo was already fetched or pulled in the same work segment. If the
  user says only `push GitHub` / `推 GitHub`, treat that as: check status, pull
  or rebase remote updates, resolve or report conflicts, then push.
- If the user's profile or previous session notes say GitHub direct HTTPS is
  unreliable, the pull/rebase-before-push step must use the known temporary
  proxy path first. Do not split the rules into "pull first" and "maybe proxy
  later"; the proven path is proxy-backed pull/rebase, then proxy-backed push.
- Do not turn bookkeeping-only corrections into immediate pushes by default.
  If the user points out an incomplete test or wrong completion status, record
  the correction locally, restate the missing validation, and resume the work.
  Batch the push with the next real tested checkpoint unless recovery risk is
  high or the user explicitly asks for sync.
- If push is deferred or fails, record the pending sync state in the work item
  and final response.
- If a new task interrupts unfinished work, update `PAUSED_WORK.md` before
  starting the new task so the previous task can be offered later.

## Existing Project Resume

When the user provides an existing project path or repo:

1. Locate or clone the project.
2. Read `README.md` first if it exists.
3. Read project-local workflow instructions if present:
   - `skills/<project>-workflow/SKILL.md`
   - `.project/PROJECT_SKILL.md`
   - `PROJECT_SKILL.md`
4. Check Git state:
   - `git status --short --branch`
   - `git log --oneline --decorate -5`
   - `git remote -v`
5. Read durable memory files when present:
   - `PROJECT_STATE.md`
   - `TASKS.md`
   - `DECISIONS.md`
   - `CONTINUATION_PROMPT.md`
   - `ENVIRONMENT.md`
   - `PROJECT_OVERVIEW.md`
6. Identify the active task domain and use relevant generic skills.
7. Load only task-relevant project files next.
8. Continue the task, then update durable memory files and the personal work
   item if project direction, outputs, decisions, environment, or next steps
   changed.

## New Project Bootstrap

When the user starts a new project:

1. Infer or ask for:
   - local project path
   - remote Git URL, if available
   - project name and one-line objective
2. Create or clone the repo.
3. Add baseline folders when appropriate:
   - `docs/`
   - `scripts/`
   - `assets/`
   - `archive/`
   - `skills/<project>-workflow/`
4. Add durable memory files:
   - `README.md`
   - `PROJECT_STATE.md`
   - `DECISIONS.md`
   - `TASKS.md`
   - `CONTINUATION_PROMPT.md`
   - `ENVIRONMENT.md`
   - `PROJECT_OVERVIEW.md`
6. Run `scripts/audit_project_structure.py --root <path> --profile <profile>` when available, then initialize Git if needed, add remote if provided, commit, and push one
   default branch only. Prefer the hosting service's configured default branch
   when it is discoverable with `git ls-remote --symref origin HEAD`. After the
   first push, verify that the remote `HEAD` target exists in the remote branch
   list. If the web UI reports a missing default branch, align the pushed branch
   with the repository default or change the repository default branch. Avoid
   leaving duplicate `main` and `master` branches long term.

Before creating, organizing, migrating, renaming, or registering workflow repositories, read `references/project-structure.md` and
`references/repository-naming.md`. Use consistent slugs across remote
repository names, local folders, registry project keys, and installed skill
folders unless a deliberate compatibility alias is recorded.

During rename recovery, audit registry keys for accidental broad names such as
`test`, `tmp`, `demo`, or `skills`. If a key is too broad to search or discuss
safely, prefer the full canonical slug in current registries and keep the broad
name only as a historical alias in the work item or rename queue.

## Durable Memory Files

Use these files consistently:

- `README.md`: project purpose, structure, key files, and resume prompt.
- `PROJECT_OVERVIEW.md`: human-readable project overview and project map.
- `PROJECT_STATE.md`: current objective, latest outputs, assumptions,
  validation status, and next steps.
- `DECISIONS.md`: dated decisions, rationale, and alternatives rejected.
- `TASKS.md`: active work, backlog, completed work, and paused checkpoints.
- `CONTINUATION_PROMPT.md`: short prompt that lets a fresh session resume.
- `ENVIRONMENT.md`: tools, dependencies, commands, and reproduction notes.

Do not create separate temporary handoff files unless the user explicitly asks.
Prefer updating durable files.

## End-of-Round Workflow

At the end of a completed work round:

1. Verify generated artifacts exist and are readable where practical.
2. Run relevant build, test, or validation commands when feasible.
3. Update durable memory files with concise facts.
4. Run `git status --short --branch` for the active project.
5. Review relevant diffs.
6. Commit the active project when the checkpoint is meaningful.
7. Use minimal push by default: push the active project and critical recovery
   state immediately, and batch routine infrastructure or mirror sync later.
8. Run a bounded relevant closure-ledger check: compare the current task id
   or objective against `ACTIVE_WORK.md`, the active work item, matching TODO
   entries, paused-work state only when the task was paused or resumed, and
   affected runtime mirrors. Completed work must not remain the default resume
   target or an open TODO.
9. Update `ACTIVE_WORK.md` before ending the turn. If work is still active,
   leave an explicit work-item link and next action; if complete, move it to
   recently completed.
10. If other paused tasks remain, keep `PAUSED_WORK.md` current so a later
    "continue previous work" prompt can show choices.
11. If the work touched workflow rules, reusable skills, starter packages, or
    runtime skill copies, run a generic-skill sync audit before claiming
    completion: compare source, starter, runtime, public, and private copies;
    classify intentional differences; record any pending sync instead of
    relying on the user to notice a missing push or public update.

When deferring sync, leave a concise pending-sync note in the relevant task or
final response. Do not let routine multi-repository sync dominate a normal
project task.

If the next session starts after the user already ended a completed work round,
do not repeat this end-of-round workflow by default. Read the routing state,
confirm that the last work is complete, and wait for the next concrete request
or offer paused candidates.

## Generic Skill Sync Audit

Run this when a task changes reusable skills, workflow rules, public starter
content, workflow bootstrap content, or installed runtime skill copies.

When comparing independently configured variants, use the read-only parity audit:

```powershell
python .\scripts\audit-variant-parity.py `
    --public-root "<public repo>" `
    --company-root "<private counterpart repo>" `
    --variant-map "<private policy file>" `
    --output "<private report path>"
```

The default public policy makes no organization-specific mapping or waiver.
Classify every difference before copying. Keep private mappings, scanner terms,
and audit reports outside public source. A matching name or hash does not grant
permission to publish; inspect the content and its rights separately.

The audit must check the full tree, not only `SKILL.md` or recent filenames:

1. Fetch the relevant GitHub remotes before comparing when network access is
   available. Prefer `scripts\validate-push-readiness.ps1` so ahead/behind state is explicit. If fetch is blocked, record the remote check as a validation gap and do not push blindly.
2. Compare recursive file lists between the durable source skill and each
   expected mirror: installed runtime skill, workflow bootstrap skill, public
   starter copy, private workflow copy, or company variant.
3. Compare file hashes for matching relative paths. A file-list match is not
   enough when content can diverge.
4. Check both directions: a runtime mirror may contain the newest behavior.
   When runtime content is newer than the durable source, either backfill the
   source first or record an explicit waiver; do not overwrite it silently or
   claim the dashboard/helper/help surface is latest.
5. Refresh mirrors with a fresh directory copy that removes the old destination
   first. Plain recursive copy can leave deleted or renamed files behind, and
   can create nested stale skill folders.
6. Read back at least one changed key file from every refreshed mirror and
   check that no nested stale skill directory was created.
7. Re-run skill/script validation from the refreshed location, not only from
   the source repository.
8. Record intentional differences, skipped mirrors, pending pushes, and remote
   fetch/push gaps in the work item before claiming the update is complete.

For a workflow bootstrap that is generated from `q-workflow-hub`, prefer the
repository script when available:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\sync-workflow-bootstrap.ps1 `
    -WorkflowHubPath "<workflow hub path>" `
    -InstallRuntime
```

The script should be treated as the validation gate for this path: it copies
selected common skills into the workflow bootstrap, optionally refreshes the
runtime install, and fails on missing, extra, or hash-mismatched files.

## Useful References

- Read `references/repository-naming.md` before naming, renaming, or auditing
  workflow repositories, local folders, registry keys, or runtime skill names.
- Read `references/workflow-evolution.md` before making structural workflow
  changes or replacing local workflow behavior with native agent/platform
  capabilities.

## GitHub Push Troubleshooting

If HTTPS GitHub operations are known to fail directly in the user's environment,
prefer a temporary local proxy by default instead of wasting a direct fetch,
pull, or push attempt. Do not ask in chat before trying a routine temporary
proxy; use the tool approval path if the execution environment requires it.

Rules:

1. Prefer per-command proxy configuration such as `-c http.proxy=...`. Do not
   change global Git proxy settings unless the user explicitly asks.
2. Reuse a recently proven local proxy first, such as `127.0.0.1:7897`.
3. If the known proxy fails, check Git proxy config, proxy environment
   variables, WinHTTP proxy, and local proxy listeners. Common local proxy
   ports include `7897`, `7890`, `7891`, `1080`, and `10808`.
4. Test with a temporary proxy command, for example:
   `git -c http.proxy=http://127.0.0.1:7897 ls-remote origin`.
5. If it works, use the same temporary `-c http.proxy=...` for fetch/pull/push.
6. Proxy app screenshots can be used as evidence that a local proxy exists, but
   never store or repeat subscription URLs, tokens, or provider credentials
   from those screenshots.
7. Record the successful proxy endpoint and any direct-connect failure in the
   work item if it was needed to complete the round.

Before a GitHub push, always try to incorporate remote updates first with
`git pull --rebase` or an equivalent fetch/rebase flow. In a known proxy-needed
environment, that command should be proxy-backed from the first attempt. If a
direct attempt fails because this rule was missed, immediately retry the same
remote-freshness check through the known proxy before treating the pull as
blocked. If the proxy-backed pull is blocked by network failure, do not push
blindly; report that remote freshness could not be verified.


## Standard Variant Sync Gate

When a task changes public/company starter parity, use the scripted gate instead
of relying on ad hoc file comparison:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-root> `
  -CompanyRoot <company-root> `
  -OutputDirectory <report-dir>
```

This gate should run scans, `git diff --check`, PowerShell parsing, Python
compile checks, parity audit, and classification. For manual runs, use
`scripts/audit-variant-parity.py` followed by
`scripts/classify-variant-parity.py`.

Nontrivial sync rounds need a local expert pass before push or release:
`Workflow Distiller` checks classification and durable policy, `Code Auditor`
checks script/path/diff safety, and `Usability Validator` checks setup and
package usability. Add `Pagewright` for HTML/setup pages, `Visual Arbiter` for
diagram/PPT surfaces, and `Doc Architect` for shared docs.

Do not auto-copy company assets, internal paths, project state, credentials,
customer material, or active-work data into public. Sanitize or split company
behavior into generic rules first, then scan the public target.
