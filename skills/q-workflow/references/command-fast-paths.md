# Command Fast Paths

Use this reference when editing shortcut behavior, help output, status/resume
routing, checkpoint behavior, or push/publish ambiguity.

## Command Alias Layer

Treat common user shortcuts as intent aliases, not as shell commands. Support
English and Chinese aliases, and treat broad or fuzzy phrases as candidates
that may need one short clarification when multiple intents match.

| Intent | English aliases | Chinese aliases | Fuzzy examples |
|:---|:---|:---|:---|
| Help | `help`, `help detail` | `帮助`, `帮助详细` | `能做什么`, `怎么用` |
| Status | `status` | `状态` | `现在怎样`, `到哪了` |
| Resume and recovery-routing interruption stack | `xiaoQ`, `resume`, `recover`, `continue`, `recovery-routing`, `interruption-stack` | `小Q`, `恢复`, `继续` | `接着做`, `继续做`, `继续小Q` |
| Previous session pointer | `last session`, `previous session`, `session pointer` | `上一次会话`, `上一次session`, `不用截图` | `直接看上一轮`, `别让我再发截图` |
| Checkpoint | `checkpoint`, `save state` | `保存状态`, `打点` | `先记一下`, `留个恢复点` |
| Lightweight TODO | `TODO`, `todo`, `TODO:<text>` | `TODO：<内容>` | `记个小点`, `以后可能要做` |
| Token usage | `TOKEN`, `token`, `tokens`, `token usage` | `token`, `当前token`, `项目token`, `总token` | `看看这轮用了多少`, `查一下token` |
| Loop run | `loop run`, `run loop`, `bounded loop`, `loop engineer` | `循环执行`, `循环`, `循环工程师` | `一直跑到完成或超时`, `给你目标和终止条件自己推进` |
| Fast Execution Mode | `fast mode`, `full speed`, `fast run`, `run fast`, `quick execute` | `全速模式`, `全速`, `快速执行`, `快速运行` | `这次别中途问我`, `能跑就跑到结果`, `少确认直接做` |
| Summary and sedimentation | `consolidate`, `summarize`, `lessons learned` | `总结/沉淀`, `总结`, `沉淀` | `做个大总结`, `把这轮经验沉淀一下`, `复盘并更新skill` |
| Workflow health check | `workflow-health`, `workflow-audit`, `audit workflow` | `体检`, `工作流体检`, `工作流健康检查`, `审查工作流` | `看看工作流重不重`, `顺便优化瘦身`, `完整扫描工作流`, `看看有没有冲突重复` |
| Workflow hygiene | `workflow-hygiene`, `hygiene`, `cleanup workflow` | `清爽性`, `工作流清理`, `自动清理` | `工作流有点臃肿`, `保持小Q特色`, `不要做成整合包` |
| Workflow identity | `workflow-identity`, `skill-fit`, `skill portfolio` | `小Q工作流特色`, `skill匹配`, `技能分层` | `skill如何和工作流匹配`, `工作流如何让skill更好用`, `不要只是整合skill` |
| Text format hygiene | `text-format-hygiene`, `text-format-hygiene`, `format hygiene`, `markdown hygiene` | `文本格式`, `格式问题`, `代码插入格式`, `乱码整合` | `之前乱码和代码插入格式别分散记录`, `格式问题解决过不应复发` |
| Recorded point resume | `quick-resume-recorded-point-lock`, `continue Xiao Q recorded checkpoint` | `继续小Q`, `明天继续`, `记录点恢复` | show the locked checkpoint, previous progress, unvalidated boundary, known pollution, proposed first action, and Resume Briefing before execution; no project execution before authorization |
| Resume briefing status first | `resume-briefing-status-first-fixed-template`, `where were we`, `named artifact resume status` | `继续前状态汇报`, `继续用户手册`, `继续PPT`, `刚才到哪了` | output `RESUME BRIEFING`; lock `已锁定分支`; name `用户手册 polish`, `PPT/deck`, and `目标文件`; report current status, relevant risks and next action; continue authorized unfinished work when requested, while a status-only question remains read-only |
| Task-start pointer promotion | `task-start-pointer-promotion`, `new concrete manual task`, `new concrete PPT task` | `开始用户手册任务`, `开始PPT任务`, `新建长期任务` | promote durable manual/PPT/deck/artifact work at task start when it should become default resume; update RECOVERY_POINTER, Current Focus, RECOVERY_EVENTS.md, and runtime mirror; tiny side quests must do not promote default pointer |
| Post-brief execution approval | `project execution after explicit approval` | `开始编辑`, `开始检查`, `执行你刚才建议的只读检查` | after state validation, continue the identified task under existing current authorization; ask only for ambiguity or scope expansion; preserve named scope and latest restrictions |
| Update rules | `update-rules` | `更新规则` | `优化工作流`, `记住这次教训` |
| Sync rules | `sync-rules` | `同步规则` | `看看有没有漏同步`, `通用skill有没有漏` |
| Targeted push | `push bit`, `push git` | `推送bit`, `推送git` | `提交到bit`, `同步到git` |
| Publish | `publish`, `upload`, `push` | `发布`, `上传`, `推送` | `提交上去`, `同步到远端` |

## Default Behavior

- Exact `help` / `帮助` is always HTML-first. Run the foundational command gate
  with `--input "帮助" --open-ui`, open the current profile hub's
  `FIRST_RUN_GUIDE.zh-CN.html`, and show the returned complete Chinese
  `surface.chat_text`. `ASSISTANT_HELP.md` is only the explicit fallback when
  the HTML artifact is missing. A zero-tool or alias-only answer is forbidden;
  do not append TODO-number selection instructions.
- Exact fixed commands should use the smallest reliable path. Prefer one small
  state file and one targeted repo check over broad skill reads, multi-repo
  scans, validation, commits, or pushes.
- When Xiao Q gives several tasks at once or TODO output grows beyond a few
  items, use a compact numbered list. Keep numbers stable within the current
  round and close, pause, block, or defer each item explicitly.
- When a new user request interrupts active work, write a lightweight interruption node before changing focus. Record the suspended task, current step, changed files or command in flight, next action, validation gap, and return condition. For nested interruptions, use LIFO stack order: finish or defer the newest node, then explicitly return to the previous one. If the same main task is interrupted two or more times, if the inserted branch edits files, discovers pollution, or leaves a validation gap, or if context compaction/session loss is likely, immediately persist a durable interruption stack in `ACTIVE_WORK.md` or `PAUSED_WORK.md`; do not leave it only in the live plan.
- `status` / `状态` should read only routing state, the active work item when
  named, and one relevant `git status` when the target repo is clear.
- `resume` / `xiaoQ` / `小Q` may read routing state and targeted Git status;
  escalate only when state is dirty, stale, contradictory, or missing the next
  safe action.
- Previous-session pointer requests should run `scripts/session_pointer.py` from
  the installed `q-workflow` skill and report the latest local Codex session
  ID, cwd, updated time, and bounded recent messages. Treat this as a
  screenshot replacement and recovery clue, not as an automatic full-context
  import. In a fresh recovery session, use `--offset 1` to skip the just-opened
  current chat and read the previous meaningful session. Do not launch nested
  `codex resume` from inside an active agent unless Xiao Q explicitly asks to
  open a separate Codex TUI.
- Exact `help`, `TODO`, `status`, and `checkpoint` must use
  `小Q工作流 / q-assistant-profile / <command>` as the first line. This
  micro-command marker is mutually exclusive with the Quick Resume card unless
  the command itself is a wake/resume request.
- `checkpoint` should update the active work item or durable state before doing
  more work; do not validate, commit, or push unless asked or recovery risk is
  high. Checkpoint and final handoff must run the bounded relevant closure-ledger check from
  `references/personal-state-routing.md`: completed work must be removed from
  `ACTIVE_WORK.md` `Current Focus`, matched TODOs must be reconciled, and
  runtime mirrors must be refreshed or explicitly deferred.

- Route id: todo-micro-path. `TODO` is a micro personal-inbox path, not a project workflow; exact TODO output is no menu. Exact `TODO` / `todo` lists routed `personal-state\TODO.md`; `TODO:<text>` / `TODO：<text>` appends a new item; a plain number immediately after a TODO list selects that current item. The top-level `SKILL.md` router is sufficient for these paths, using `q-profile.json` only if the hub path is not already known. For company profiles, resolve the personal hub from `%USERPROFILE%\.codex\q-profile.json` (`hub`, `personal_hub`, `company_hub`, or equivalent configured path) and prefer `<hub>\personal-state\TODO.md`; `%USERPROFILE%\.codex\q-personal-state\TODO.md` is only a runtime fallback. If hub and runtime TODO differ, list from the configured hub source and refresh the affected runtime mirror before closing, or explicitly tell Xiao Q why sync was deferred. Do not scan project repos, create work items, validate, commit, or push just because a TODO was listed or added. For zh-CN, list and numeric selection must render only the complete localized `name` / `summary` / `detail` fields; raw source remains internal provenance and must never be pasted into the user surface. IDs, file paths, commands, and project names may remain transparent tokens. Exact `TODO` listing stays a micro path, but completion handoff is not complete until matched Open TODO entries have been reconciled to Done or explicitly left Open with a reason, and the related `ACTIVE_WORK.md` focus entry has been removed or updated to a real next action.
- When listing TODO items, do not collapse them to ids or bare titles. For
  each numbered Open item include at minimum: TODO id, one Chinese actionable
  summary, current or next action, and any evidence, source path, recovery
  entry, or completion gate already present. If the stored entry is too vague,
  mark `缺口: needs expansion` and offer to expand it; do not invent missing
  detail or scan project repos unless Xiao Q selects that item for execution.
- `TOKEN` / `token` is a micro local-usage path. Run
  `scripts/token_usage.py --format html --open` from the installed
  `q-workflow` skill to generate and open
  `%CODEX_HOME%\reports\token_dashboard.html`. If opening fails or the user
  requested a headless run, provide a clickable file link instead. The final reply
  should include the dashboard path plus a brief current/project/total/context
  and cache-health summary, not collapse the command into a pure numeric-only
  answer. Read high `Cached%` as good only when context pressure, uncached
  input, and output cost share are also acceptable. Prefer latest-turn health
  for immediate decisions; use current-session and project cumulative totals to
  find long-term trends. Treat high cache as suspect when recent input growth
  is high, cache ratio spread is large, or estimated cache savings are weak;
  those are signs of context bloat, unstable prefix structure, or output-heavy
  cost. Do not invent latency, TTFT, retry, or cache-route-saturation numbers
  from local Codex logs; add those only when provider/API/proxy traces expose
  reliable timings or request metadata. Keep `--format visual` available as a terminal
  fallback when HTML cannot be shown. Do not install CodexBar, query remote
  services, inspect Git, or read project files for this command. If a project
  path is known from the current working directory or active project, pass it as
  `--project`; otherwise let the script infer the active project from the latest
  session transcript and known project roots instead of treating a broad user
  home cwd as the project. Treat these as local log totals and project
  attribution heuristics, not billing guarantees.
  If the dashboard reports high cache spread, high input growth, false-high-cache
  symptoms, or context pressure above about 60%, use
  `references/context-budget.md`'s Cache Stability Protocol before starting
  another broad research, multi-agent, or skill-update task. For workflow-rule,
  release, colleague-handoff, or customer-facing work, explicitly suggest
  `workflow-health` / `体检` before further expansion.
- `loop run` / `循环执行` is a bounded autonomous loop and assumes unattended
  execution by default unless Xiao Q explicitly asks for stepwise review.
  Confirm or infer a concrete goal, stop conditions, validation cadence, and
  progress boundary; then write a Loop Permission Contract before starting long
  unattended work. Do not make Xiao Q repeat the unattended boilerplate in the
  prompt. In that contract, identify work roots, write scope, low-risk
  local reads/writes, tests, formatters, local commits, or other stable command
  prefixes likely to be needed, and request reusable approval where the platform
  supports it. Do not pre-approve destructive cleanup, credentials, public
  pushes, broad installs, global configuration, or unclear data exposure.
  During the loop, keep implementing, validating, and correcting until the goal
  is reached or a stop condition is hit. If an unapproved action becomes
  necessary while Xiao Q is away, record the blocked action, switch to an
  allowed alternative or another useful branch, and checkpoint before stopping;
  do not wait idly on a single approval unless all meaningful branches are
  blocked. Stop conditions should include completion, an
  explicit time boundary, token/context pressure, a configured no-progress
  threshold, permission boundaries, destructive action, unclear data exposure,
  or a validation blocker that cannot be reduced safely. Use
  `references/agent-orchestration-bus.md` when the loop needs subagents or
  specialist roles.
- `总结/沉淀` / `总结` / `沉淀` is a deep consolidation path. Read
  `references/summary-sedimentation.md`, then summarize the current execution
  and feedback loop, research adjacent evidence or prior art when useful,
  validate which lessons are proven, update the right skill/framework/state
  surfaces, and record remaining risks. Do not use it as a pure chat summary.
- `workflow-health` / `体检` / `工作流体检` / `workflow-audit` is the bounded
  health+slimming command. Read `references/workflow-audit.md`, run audit and
  hygiene summaries first, then inspect routing, state authority, shortcut
  clarity, skill boundaries, sub-agent protocols, cache stability, validation
  loops, and slimming candidates. If the request includes token control,
  release preparation, or colleague/customer handoff, follow the standard
  optimization/slimming path there: benchmark summary, context/cost preflight,
  mechanical gates, archive-backed state slimming, rule slimming, expert pass,
  validation, and report. It must preserve approval gates, release gates,
  recovery authority, and source/runtime ownership. Apply only small
  high-confidence rule patches unless Xiao Q explicitly asks for larger
  migration or public sync.
- `全速模式` / `全速` / `快速执行` / `fast mode` / `full speed`
  activates Fast Execution Mode for the current task. In this mode, do not stop
  for avoidable preference
  questions; make conservative assumptions, batch independent reads/checks, run
  validation, and carry the task through to the final result. This mode cannot
  pre-approve or bypass platform-enforced permission prompts. If a required
  command needs escalation, request approval immediately with the narrowest
  practical reusable `prefix_rule`; do not ask a separate chat question first.
  Still ask or stop for destructive cleanup, broad dependency installation,
  credential handling, public/GitHub sync, remote pushes, unclear data exposure,
  or any approval the tool layer requires.
  Bare `运行` is not a strong shortcut because it often means "run the test" or
  "continue the current command"; treat it as fuzzy execution intent and decide
  from surrounding context.
- Xiao Q's default preference is to use Fast Execution Mode for ordinary
  implementation, validation, recovery, and handoff tasks even when the trigger
  phrase is not repeated. A request to discuss, review, produce only a plan,
  slow down, or wait before editing overrides this default for the current
  task.
- `update-rules` should first report the minimal scope. For small wording,
  alias, help, or formatting fixes, update only the source skill and installed
  runtime copy, then record any starter/public/remote sync as pending.
- `sync-rules` should start with a status/diff summary and a pending-sync list;
  do not push unless Xiao Q explicitly asks.
- `push bit` / `推送bit` means the relevant internal Git remote for the current
  locked repo only; it never overrides company promotion/share repo no-push
  defaults. Promotion/share repos require explicit version update, stable
  release, or major update candidate wording for the named repo/version.
  variant/private repository after normal local status, diff, and validation
  checks.
- `push git` / `推送git` means GitHub/public sync only. Do not create Bitbucket
  or internal Git candidates from this wording. Use the approved staging
  repository, apply only sanitized generic workflow changes, run the
  public-safe scan gates, and ask for final confirmation before pushing.
- `publish`, `upload`, and `push` must run the relevant scan, diff, status,
  and remote checks first. Treat broad `push` as current active repository
  only; ask before multi-repo or public/GitHub pushes.


## Loop Permission Contract

Before starting a bounded loop, write a short execution contract and keep the
rest of the loop inside it. The contract is not a user preference question; it
is the machine-readable boundary that lets the loop run without repeated
mid-loop prompts.

Required fields:

- work_roots: repositories, report directories, and temp roots the loop may
  read or write.
- write_scope: exact files or directories the loop may edit.
- auto_allowed: stable low-risk command families, such as targeted git -C
  status/diff/add/commit, rg, read commands, local validators, formatters,
  encoding checks, and report writes under approved roots.
- ask_always: push, publish, destructive cleanup, credentials, broad installs,
  global configuration, network-heavy actions, and writes outside work_roots.
- branch_around: what to do if an unapproved action appears while the user is
  away. Continue another useful branch, checkpoint the blocker, and stop only
  when all meaningful branches are blocked.
- stop_condition: completion, explicit user stop, unresolved P0/P1/P2 after
  the review budget, permission boundary with no alternative branch, or
  critical context pressure without a compact entry.

For long unattended loops, prefer starting the agent from the target workspace
or a configured workspace root so ordinary file edits are inside the sandbox. If
the platform exposes persistent allowlists or approval presets, ask for the
minimal reusable low-risk set at the start instead of many one-off approvals.
Do not try to make push, publish, destructive cleanup, credential use, or broad
installs part of the auto-allowed set.

## Pointer Authority Fast-Path Boundary

Numeric replies such as `1`, `2`, and `3` bind only to the most recent
still-valid option menu. The binding expires when the topic changes, a new menu
appears, Xiao Q corrects the state, a copied note is introduced as background,
or enough context has passed that the active menu is no longer clear.

For high-impact actions, a numeric reply is valid only when the immediately
preceding option text names the exact action, target object, scope, and likely
impact. This applies to push, publish, release, public sync, external order,
flashing, deleting, credential handling, and global configuration.

If a stale pointer suggests a high-impact action after a revocation or narrower
instruction, state the latest authority and either ask again or run only the
authorized local validation. Do not execute the stale high-impact action.

## Numbered Choice Confirmation

Use compact numbered choices when the next path is clear and the decision is
low-ambiguity. Put the recommended/default action at `1`, keep the list to 2-3
options, and name the practical effect of each option. Immediate replies such
as `1`, `2`, `3`, `OK`, or `嗯嗯` select the matching option only while the
active choice context is still valid.

The active choice context expires when a new question, new user constraint,
option reorder, topic switch, or meaningful time/context gap appears. Bare
`运行` remains fuzzy execution intent unless a recent explicit option context
already names the action.

For flash, motor motion, destructive actions, push/public sync, credentials,
broad installs, or other high-risk effects, the chosen option itself or the
immediately preceding safety line must name the exact action, target object,
scope, and likely impact. A bare `1. 执行（默认）` label is not authorization, and
choice shortcuts must not bypass required safety briefing or approval.

## Ambiguity Handling

- Treat broad words such as `sync`, `同步`, `upload`, and `上传` as ambiguous
  when they could mean rules, runtime mirrors, repository commits, or public
  publishing. Use context if it is clear; otherwise ask one concise question
  with 2-3 concrete options.
- Do not let fuzzy matching trigger destructive actions, credential handling,
  global configuration, or public publishing without the normal safeguards.

## Help And Feature Prompts

When the user asks for help, features, available commands, "what can you do",
or similar:

1. Exact `help` / `帮助` is HTML-first. Route it through
   `q_base_command.py --input "帮助" --open-ui --format json`, open the current
   profile hub's `FIRST_RUN_GUIDE.zh-CN.html`, and show the returned
   `surface.chat_text` in the same reply. Use
   `personal-state\ASSISTANT_HELP.md` only as the explicit fallback when the
   HTML surface is unavailable. Do not replace this with a zero-tool shortcut
   or append TODO-number selection instructions.
2. Start with a concrete default work process. Show the user how a normal task
   moves through recover, choose task, work, verify, record, and handoff. Keep
   it short enough to act on.
3. Prefer standard Markdown tables for compact workflow summaries. Keep cells
   short, include leading and trailing pipes for readability, and do not use
   ASCII box tables, fake bottom borders, or extra separator lines. If CJK,
   mixed-width text, or narrow chat windows make a table unstable, use a
   numbered flow instead.
4. Avoid abstract architecture views for ordinary new-user help unless the user
   asks how the system is designed.
5. Summarize only the currently useful capabilities, with short examples.
6. Mention paused-work recovery options only when already known or requested;
   do not read paused-work files just for fast help.
7. Offer concrete next actions instead of listing every internal rule.

Use proactive hints sparingly. A hint is useful when a task is completed and no
explicit next step exists, paused work remains that the user may have
forgotten, a new workflow feature directly helps the current situation, or the
user appears blocked or asks broad "what next" questions.
