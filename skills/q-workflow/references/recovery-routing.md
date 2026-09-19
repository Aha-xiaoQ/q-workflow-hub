# Recovery Routing

Use this reference for resume, interruption recovery, emergency save, and
existing-project recovery details. `SKILL.md` keeps only the safe routing
summary; this file carries the full procedure.

## Activation

| Trigger | Tier | Risk | Action |
|---|---|---|---|
| `xiaoQ`, `小Q`, `resume`, `continue` | Quick | allow | Read routing state and one targeted Git status. |
| Named project or named artifact resume | Project | within current authorization | Validate bounded task state, lock the target and continue authorized unfinished work. Status-only or ambiguous requests stop at a concise briefing. |
| Dirty, stale, contradictory, or agent-touched state | Deep | ask before risky actions | Inspect diffs and handoff notes before editing. |
| Platform compact/session failure | Deep | ask before commit/push | Reconstruct state before validation or expensive work. |
| High context pressure, token-heavy session, or before broad recovery after compaction | Project | allow read-only token scan and local checkpoint write | Run `scripts/context_governor.py --format text`; if `throttle` or `critical`, write a task packet before continuing. |
| `checkpoint`, `save state`, `pause note` | Quick | allow local write | Write a recovery point before further work. |

## Platform Session Failure Recovery

If the agent platform repeatedly reports a remote compaction, summarization, or
session-continuation failure, treat the current chat window as unreliable
platform state instead of asking the user to keep retrying in that window.

Codex CLI has a real resume path (`codex resume --last`, `codex resume --all`,
or `codex resume <SESSION_ID>`), but that reopens the old full session. If the
old session was already triggering compact or continuation errors, direct resume
may reproduce the same failure. In that case, prefer a new session plus a
bounded local session pointer from `scripts/session_pointer.py`, then recover
from durable state.

Before a broad recovery scan, run `scripts/context_governor.py --format text` when token pressure, compaction friction, or lost-state ambiguity is part of the problem. If the result is `throttle` or `critical`, write or read a compact entry packet first, then recover from source-of-truth files only as needed instead of expanding the chat narrative.

Proactive mitigation for known high-risk work:

1. At the start of a long or interruption-prone task, create or refresh the
   active work item with a compact plan, target files, next command, and
   validation gate.
1a. For user-manual, PPT/deck, handoff, project artifact, or long
   interruption-prone tasks, the active work item alone is insufficient. If the
   task should become the default resume target, promote `ACTIVE_WORK.md`
   `RECOVERY_POINTER`/`Current Focus`, append `RECOVERY_EVENTS.md`, and sync or
   mark the runtime mirror at task start, before substantive artifact work. Skip
   default-pointer promotion only for an explicitly short inserted branch or
   non-default side quest.
2. Break the task into resumable chunks that can be validated independently.
   Prefer one artifact, one script, one deck, one source/runtime sync, or one
   decision per chunk.
3. After each meaningful chunk, update durable state before starting the next
   expensive operation. A good checkpoint includes latest completed step,
   changed files, validation result or gap, and the next command.
4. If a compact/high-demand/continuation error already occurred once, shrink the
   next chunk before retrying and start from durable state, not from chat memory.
5. If the error repeats, stop adding context and produce a short recovery prompt
   for a new session. Do not keep asking the user to retry the same overloaded
   continuation path.
6. When Xiao Q wants to avoid screenshots, run `scripts/session_pointer.py` to
   extract the latest local session ID, cwd, updated time, and bounded recent
   user/assistant messages. Compare that pointer with `ACTIVE_WORK.md` and the
   active work item before resuming work.
7. Bare `小Q` and explicit `继续小Q` / `continue Xiao Q` share a structural
   read-first recovery gate: read `q-profile.json`, the routed `ACTIVE_WORK.md`,
   and a bounded recent chat/session tail before presenting a confident target.
   Run the same gate after context compaction; do not answer from a compacted
   summary or active context alone. For a fresh new session, run the pointer
   helper with `--offset 1 --messages 6 --max-chars 320` to skip the just-created
   session and read the previous meaningful one. Use `--users-only` only when
   the explicit recovery question is limited to Xiao Q's last visible request.

Not every interruption happens after a clean checkpoint. If a session may have
ended suddenly, assume the recovery quality test is harder than ordinary
resume: check for dirty Git state, uncommitted generated artifacts, stale
runtime mirrors, recently changed work items, and the latest user-visible
request before running validation or continuing expensive work.

When using choice questions to test whether Xiao Q and the assistant understand
recovery priorities the same way, collect Xiao Q's answers before revealing the
assistant's expected answers. Record the comparison afterward to avoid
anchoring the user's response.

Rules:

1. If the current session can still write files before switching away, update
   the active work item with a short `Session Recovery Note`.
2. Record the latest user-visible request, latest completed step, next intended
   action, uncommitted or unvalidated state, and visible platform error text
   when useful.
3. If the current session cannot write files, ask the user to open a new
   session and paste a short recovery prompt plus any screenshot of the last
   visible state.
4. In the new session, recover from durable state first: assistant profile,
   `ACTIVE_WORK.md`, active work item, `PROJECT_REGISTRY.md`, and only then
   recent Git status/logs or screenshots.
5. Do not commit, push, run validation, or resume expensive commands until the
   recovered durable state has been compared with the user's latest prompt or
   screenshot.
6. For long, remote, model-heavy, or interruption-prone work, keep a rolling
   checkpoint in the work item after meaningful plan changes, user corrections,
   or completed substeps.
7. After a real recovery round, run a short consolidation pass before closing:
   identify one reusable failure mode, patch the smallest correct workflow or
   reference layer, sync only the needed runtime mirrors, and record the
   validation result. Avoid turning every recovery into broad multi-repository
   cleanup.
8. If the source hub was updated during recovery, refresh only the affected
   runtime mirror files needed for future routing, such as `PAUSED_WORK.md` or
   the active work item. Do not bulk-copy the personal hub unless the user is
   doing machine bootstrap or mirror repair.

Emergency save behavior:

1. Stop nonessential work immediately.
2. Update the active work item with `Session Recovery Note` or `Emergency
   Checkpoint`.
3. Record the latest user request, plan status, files changed, relevant
   commands, validation/sync gaps, and next 1-3 actions.
4. Do not commit or push unless the user explicitly asks, or unless the work
   item says a local commit is the required recovery checkpoint.

Useful new-session prompt:

`Recover from a platform compact/session failure. Use q-assistant-profile and q-workflow. First read ACTIVE_WORK.md and the active work item. Do not commit, push, or run validation until you reconstruct the current state. Last visible request was: <paste last request>.`

If screenshots are unavailable, replace `<paste last request>` by asking the
assistant to run `q-workflow\scripts\session_pointer.py --offset 1
--messages 6 --max-chars 320` and use the previous local Codex session pointer.

## Pointer Authority Recovery

Use this recovery subgate when resume state, copied notes, delayed tool output,
or completed-state corrections disagree about the next action.

Authority order:

1. Latest direct user message or correction.
2. Copied content only when the user explicitly promotes it as authoritative.
3. Project files, durable handoff notes, and current tool output.
4. Old summaries, copied notes, historical plans, delayed tool output, and stale
   pointers.

Rules:

- If the latest direct user event revokes, narrows, or corrects a previous plan,
  record that event before any action selection.
- If copied content contains an option, command, or next action, treat it as
  background unless the user explicitly says to use that copied content as the
  current authority.
- If a tool result arrives after a user revocation or narrower command, do not
  let the delayed result re-authorize push, publish, order, delete, flash, or
  broad sync.
- If durable state says work is pending but the latest user correction says it
  is already done, first repair or verify the state pointer; do not recreate the
  completed external action.
- If the latest user correction says the pointer is wrong/stale or names a
  concrete project path, run a bounded stale-pointer audit before locking the
  resume target: compare `ACTIVE_WORK.md`, `RECOVERY_EVENTS.md`, and that
  project's `PROJECT_STATE.md`/`TASKS.md`. Promote the newer concrete
  project-local objective when it conflicts with an older global pointer, then
  repair the pointer and runtime mirror before continuing.
- For high-impact actions, stop at local validation or ask again when authority
  is stale, ambiguous, or contradicted.

Anti-pattern: treating an old handoff, copied note, previous menu, or delayed
success message as stronger than the latest direct user correction.

## Managed Pointer Entity Gate

Apply this executable gate whenever `RECOVERY_POINTER` declares
`schema: q-workflow-focus-v2` or a `task_record_path`.

- `Trigger`: status, resume, checkpoint, state audit, doctor, task listing, or
  any claim that the managed focus is recoverable.
- `Must`: resolve `task_id` to exactly one JSON under `personal-state/tasks`,
  validate the record hash and pointer fields, and resolve `authority_event` to
  exactly one latest event in `TASK_EVENTS.jsonl`.
- `Blocks`: confident resume, `status: pass`, `record_state: confirmed`, and
  further Phase B execution when the record or event is missing, stale, or
  contradictory. Byte-identical `ACTIVE_WORK.md` mirrors cannot waive this.
- `Check`: run `q_workflow_manager.py status`, `task validate --task-id <id>`,
  and `q_base_command.py --audit`; all must expose the same binding result.
- `Repair`: reconstruct the candidate record from project authority plus the
  latest direct correction, then use manager `task plan` and `task apply --yes`
  so the task JSON, event, focus view, runtime mirror, and manifest switch as one
  checked transaction.
- `Waiver`: legacy v1 pointers may remain explicitly unmanaged during their
  compatibility window, but must not be labelled v2 or reported as a managed
  confirmed task.
- `Scope`: this gate validates task identity and authority. It does not grant
  permission to inspect or mutate the project artifact itself.

Anti-pattern: manually writing a v2 Markdown pointer and treating mirror hash
equality as proof that the canonical task entity exists.

## Interruption Stack And Lightweight Node Records

A mid-task user interruption is not a reason to forget the previous branch. Before switching to the new request, create a lightweight interruption node in the current plan or active work item.

A node should include:

- suspended task or branch;
- last completed step;
- current file, command, or validation in flight;
- next intended action;
- known validation gap or dirty state;
- return condition, such as "after this inserted request is validated" or "after user confirms cleanup".

Use LIFO stack order for repeated interruptions: push the new node before switching, close or defer the newest node first, then pop back to the previous node and state the return point. If the interruption is tiny and a durable file write would create noise, keep the node visible in the live plan and write a durable checkpoint at the next meaningful boundary. If the interruption changes project state, edits files, or exposes pollution, update the active work item before leaving the branch. If the same main task is interrupted two or more times, if the inserted branch edits files, discovers pollution, or leaves a validation gap, or if context compaction/session loss is likely, immediately persist a durable interruption stack in `ACTIVE_WORK.md` or `PAUSED_WORK.md`; do not leave it only in the live plan.

Anti-pattern: treating every new user message as replacing the old task without recording the paused branch, then relying on chat memory to rediscover what was unfinished.

## Resume Briefing Before Execution

After a recorded point or session recovery, briefly state the validated target,
unfinished step and current boundaries. Continue when the user requests execution
of an identified authorized task. A status question or unresolved target needs
only the briefing; a hardware pause retains its bench-readiness requirements.

The following fields are a reference for substantial or ambiguous recovery, not
a mandatory questionnaire for every continuation. Mark unknown evidence honestly.

```text
RESUME BRIEFING / 继续前状态汇报
Route: <quick/project/deep + reason>
Target: <project/artifact/task; lock named manual/PPT/deck branch when present>
Last user intent: <known/unknown>
Authoritative anchor: <ACTIVE_WORK/work item/PROJECT_STATE/TASKS/handoff + sync_state>
Current status: <last completed step + current unfinished point>
Dirty/risk state: <clean/dirty/unknown + known pollution/unvalidated boundary>
Allowed Phase-A reads used: <files/commands>
Recommended first action: <read-only/edit/build/validate + exact scope>
Execution boundary: <current authorized scope and persistent restrictions>
Approval prompt: <only if a consequential decision or additional authorization is missing>
```

For Chinese output, use readable Chinese labels. Explain a real stop in plain
language; do not add a mandatory approval phrase to an already authorized task.

The briefing should be compact but not cryptic. A user returning after hours or
days should not need to open old chat to understand why the proposed next step
is safe.

Anti-patterns: resuming from an unvalidated pointer, ignoring a user restriction,
or stopping authorized work solely to obtain a second approval after briefing.

## Checkpoint Pollution Ledger

A recorded point is only useful if the next session can recover without hidden
pollution. When Xiao Q asks to record, checkpoint, pause, stop for the day, or
make next recovery clean, run a pollution ledger before final handoff.

Classify each dirty or generated surface:

- intentional checkpoint content: belongs to the recorded state and should be
  committed, tagged, or explicitly referenced;
- temporary experiment: should be reverted or isolated before claiming a clean
  checkpoint;
- build/tool side effect: should be reverted when not part of the checkpoint,
  or listed as generated local state if it must remain;
- stale pointer or runtime mirror: should be repaired or marked as stale with a
  next repair action;
- unrelated user work: must be preserved and excluded from cleanup;
- unknown: stop and report the uncertainty instead of hiding it.

Closure requirements:

1. Run or report targeted dirty-state evidence for the active repo and affected
   state hub.
2. Clean assistant-created temporary pollution when the intended clean state is
   unambiguous.
3. If pollution cannot be safely cleaned, write the exact paths, owner,
   suspected source, and next cleanup decision into the handoff packet or
   `ACTIVE_WORK.md`.
4. If a project-local handoff, report, fabrication package, checkpoint note, or
   final artifact becomes the recovery authority during task start, promote it
   immediately using the task-start gate. During closure, verify that
   `ACTIVE_WORK.md`, the matching TODO/work item, and the runtime mirror still
   agree. When `RECOVERY_EVENTS.md` records a `sync_result`,
   mirror the event `sync_result` into `RECOVERY_POINTER.sync_state`; a mismatch
   invalidates Quick Pointer confidence and requires a bounded stale-pointer
   audit using `RECOVERY_EVENTS.md` as the first comparison surface, then the
   matching TODO/work item and named handoff. If the audit cannot resolve the
   current authority, ask Xiao Q instead of continuing from the stale pointer. If
   any surface is skipped, record the reason in the handoff or integration note.
5. The final answer must say whether the recorded point is `clean`,
   `recoverable-with-known-pollution`, or `blocked-by-unknown-pollution`, and
   whether the global recovery pointer was synchronized or intentionally
   deferred.

Anti-pattern: writing a checkpoint/tag/handoff while leaving generated files,
failed build side effects, stale mirrors, or temporary test macros unstated.

## Recorded Point Lock And Two-Phase Resume

When the previous session, active work item, or handoff packet contains a user-approved durable anchor plus next action, that tuple is the authoritative resume anchor. A durable anchor may be a checkpoint, commit, tag, handoff or report path, explicit recorded point, or user-approved state note. Stale or less specific
`ACTIVE_WORK.md` wording may trigger pointer repair, but it must not trigger
project reinterpretation or execution.

Use two phases for `continue Xiao Q` / `继续小Q` recovery after a recorded point:

1. Phase A - recover and lock state. Read only routing state, bounded active
   work, the previous-session pointer, and required handoff packet headers.
   Repair source/runtime active pointers when needed, then present the locked
   checkpoint, evidence consistency, next action, and protected boundaries.
2. Phase B - execute authorized project work. A request to continue an identified
   unfinished task normally resumes its authorized scope after state validation.
   Do not require approval again merely because a briefing was produced. A bare
   wake word, status question, ambiguous target or explicitly paused boundary
   stays in Phase A until intent is clear.
For named artifacts, preserve the selected branch and latest user correction.
Read the body and continue edits/validation when continuation is requested and
the work is already authorized. Existing no-push, hardware, privacy or other
scope limits persist; a summary of old permission is not renewed authorization.

Validated hardware checkpoints add a stricter gate: default to preserving the
last user-validated configuration. Changing a control mode, power-stage route,
PWM/ADC/pin mux, build image, flash state, or motor-moving script requires an
explicit transition plan and bench-readiness confirmation.

Anti-pattern: using stale pointer repair as a bridge into code edits, builds,
or hardware actions in the same resume turn.

## Dual-Pointer Recovery Model

Use this model when `ACTIVE_WORK.md` has a long-lived default project focus but
the previous session was interrupted inside a different loop, review, benchmark,
or skill update.

State roles:

- `RECOVERY_POINTER`: the default project or durable work focus. It is not always
  the most recent interrupted execution thread.
- `Active Execution Thread`: the most recent `active` or `paused` execution
  branch, plus `latest_closed_thread` metadata for context. Closed or
  recommendation-only branches are not live execution authority.
- Previous-session pointer: evidence from `session_pointer.py`; use it to detect
  a mismatch, not as an automatic override of durable state or a way to reopen a
  closed/recommended branch by itself.

Rules:

1. On short resume, read `RECOVERY_POINTER` and `Active Execution Thread` before
   presenting the next action.
2. If the execution thread is `active` or `paused` and differs from the default
   project pointer, present both as numbered choices and do not execute either
   branch until Xiao Q selects one.
3. If the execution thread is `closed`, `completed`, `idle`, or recommendation-
   only, it must not create a numbered choice on a generic resume. Continue from
   the default project pointer; do not turn it into an equal option against an
   active RECOVERY_POINTER unless Xiao Q explicitly reopens or promotes it.
   Mention the closed branch only as context when Xiao Q asks for status or
   explicitly names it.
4. When a loop, benchmark, review, or skill-update branch becomes the live work
   for more than one turn, update `Active Execution Thread` with status,
   evidence path, next action, and return target before running more expensive
   work.
5. When that branch closes, mark it `closed` with the closing report and restore
   or confirm the default project pointer.

User experience requirement: when an `active` or `paused` thread conflicts with
`RECOVERY_POINTER`, the first resume answer should explain why there are two
possible continuations. A bare default-project jump after a live interrupted
thread is a recovery defect. A closed/recommendation-only branch presented as an
equal option is also a recovery defect, because it makes the workflow feel
unstable.

## Short Resume Prompts

When the user says a general resume phrase meaning "continue Xiao Q's
project/task", "continue my project", or "restore Xiao Q's task":

1. Read `%USERPROFILE%\.codex\q-profile.json` when present.
2. If it exists and `profile` is `company`, route through the company hub.
3. In company profile, read `<personal-hub>\personal-state\ACTIVE_WORK.md` if
   present. If `RECOVERY_POINTER v0.1` exists near the top, treat that compact
   block as the first quick-resume authority; otherwise use `Current Focus` and
   at most the first recent item.
4. Fall back to `%USERPROFILE%\.codex\q-personal-state\ACTIVE_WORK.md` with
   the same `RECOVERY_POINTER v0.1` first-read rule.
5. If an `Active Execution Thread` block exists, compare it with the default
   `RECOVERY_POINTER` and the bounded previous-session pointer. If an `active`
   or `paused` thread differs from the default project, present both choices
   before execution. If the thread is closed, completed, idle, or only a next
   recommendation, continue from the default project unless Xiao Q explicitly
   reopens or promotes that branch.
6. If Xiao Q says the pointer is wrong, stale, or contradicts remembered work,
   run a stale-pointer audit before answering: compare `ACTIVE_WORK.md`,
   `RECOVERY_EVENTS.md` when present, the matching TODO/work item, the bounded
   previous-session pointer, and any project-local handoff path named by the
   current focus, recovery pointer, or recent session. If the project handoff or
   event authority is newer or more specific, repair source/runtime state before
   presenting the resume point.
7. If there is no active focus and the prompt does not ask for paused or
   previous work, give a compact status handoff and offer concrete project or
   paused-work options. Do not scan Git history or validate repositories by
   default.
8. If `Current Focus` contains completion language such as `closed`,
   `completed`, `done`, `no blocker`, or only points to reports with no
   concrete next action, and no valid `RECOVERY_POINTER` supersedes it, treat it
   as a stale focus pointer. Do not resume into that round by default; move or
   recommend moving it to `Recently Completed` / `Done`, refresh affected
   mirrors, then present the next real focus or paused-work options.
9. If an active work item is named, open it and check status first. If it is
   already completed, report completion and next options without reopening the
   round.
10. Check the target repository `git status --short --branch`; use
   `git diff --stat` only if dirty.
11. If no active work item exists and the user asks to continue previous,
   earlier, unfinished, or paused work, read `PAUSED_WORK.md` and present 2-5
   candidates with short descriptions.
12. Use the selected hub's `PROJECT_REGISTRY.md` only when the project path is
    unclear.
13. If no active or paused work item is named, do a bounded recovery scan:
    recent work items, non-placeholder registry entries, recent Git status/logs
    for registered projects, recently modified local skills, and repo names or
    URLs mentioned by the user.
14. Choose a target only when the evidence is specific. Otherwise present 2-4
    concrete recovery candidates and ask which one to resume.
15. Once the target is clear, immediately create or update the matching work
    item and `ACTIVE_WORK.md`.

If the prompt names a specific project, the named project overrides the latest
active personal work item.

For stale, conflicting, dirty, or non-primary-agent-touched states, escalate
from Quick Resume to Project Resume or Deep Recovery using
`<personal-hub>\docs\TOKEN_BUDGET.md` when present.

## Reusable Tool Continuity Gate

Apply this gate whenever the user refers to a custom workbench, editor, helper,
or other tool that was used successfully before an interruption or context
compaction.

Before declaring the tool missing, choosing a substitute, creating a new tool,
or restarting its training path:

1. Read the active and paused work items plus the current project authority.
2. Follow exact registered paths to the tool entry, variant registry, launcher,
   protocol, and validators.
3. Confirm the registered variant and run at least one existing read-only or
   smoke validator.
4. Restore a missing project bridge or pointer when the tool exists but is not
   discoverable from the current task.

Do not treat a bounded filename-search miss or compacted chat summary as proof
that the tool never existed. Prefer the registered exact path over rediscovery.
If a required operation is absent, extend the established tool minimally and
validate both the old behavior and the new scenario. A replacement is allowed
only when the user asks for it or the registered tool is verified incompatible
or unusable.

Persist the repaired recovery route so the next session can identify the tool,
launch it, validate it, and resume the exact task without repeating discovery.

## Existing Project Resume

When the user provides an existing project path or repo:

1. Check the private personal state hub if present, especially after
   interruption, crash, "continue", or ambiguous resume prompts.
2. Locate or clone the project.
3. Use Project Resume by default: read `README.md`, `PROJECT_STATE.md`,
   `TASKS.md`, `CONTINUATION_PROMPT.md`, and
   `git log --oneline --decorate -5` when present.
4. Read project-local workflow instructions if the state files or task domain
   indicate they are needed:
   - `skills/<project>-workflow/SKILL.md`
   - `.project/PROJECT_SKILL.md`
   - `PROJECT_SKILL.md`
5. Check Git state:
   - `git status --short --branch`
   - `git remote -v`
6. Escalate to Deep Recovery only when state is stale, contradictory, dirty,
   touched by another agent, or missing the next action. Then read only
   relevant `DECISIONS.md`, `ENVIRONMENT.md`, `PROJECT_OVERVIEW.md`, reports,
   scripts, and diffs.
7. Identify the active task domain and use relevant generic skills. Examples:
   - PPT/deck work -> `q-ppt-creation` when variant-specific style is involved.
   - Code/debug/release work -> `q-code-lifecycle`.
   - MCU build verification -> `MCU build verification skill`.
   - Serial, Saleae, debug probe work -> the matching hardware tool skill.
   - Research/source discovery -> `q-research-discovery`.
   - Skill creation/update/review -> `q-skill-creation`.
   - Video/audio/transcript intake -> `q-video-intake` or `q-audio-intake`.
8. Load only task-relevant project files next. Prefer indexes, state files,
   reports, scripts, and recent diffs over broad file loading.
9. After validating the resume point and current scope authorization, continue the task, then update durable memory files and the personal work
   item if project direction, outputs, decisions, environment, or next steps
   changed.

For rough context estimates, use
`<personal-hub>\scripts\estimate_context.ps1` when present.
