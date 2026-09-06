# Context Governor

Use this reference when Xiao Q asks for autonomous context-pressure management,
when the chat feels heavy, before another broad work segment, or after repeated
compaction/recovery friction.

## Purpose

The context governor keeps the workflow responsive by deciding when to continue,
when to narrow, and when to checkpoint into durable state. It does not claim to
modify the model's already-loaded context. It makes the next segment smaller and
recoverable through files.

## Preflight Triggers

Run a context preflight before:

- broad repo or personal-hub scans;
- multi-repo closure, commit, or push preparation;
- deep research or web-source aggregation;
- generated decks, reports, screenshots, or visual-review loops;
- skill updates that touch source, runtime mirrors, and adjacent references;
- sub-agent orchestration or long autonomous loops;
- any task after Xiao Q mentions context pressure, token health, compacting,
  `降智`, or lost last-state recovery.

## Live Gate

Preferred command:

```powershell
python <q-workflow>\scripts\context_governor.py --format text --objective "<current objective>"
```

For a durable handoff packet:

```powershell
python <q-workflow>\scripts\context_governor.py --format text --objective "<current objective>" --packet-out <path> --next-action "<next step>" --validation "<validation command>"
```

Use `--strict` in automation when a throttle/critical result should stop the
next broad step with a nonzero exit code.

## Decision Matrix

| Level | Meaning | Required behavior |
|---|---|---|
| `ok` | pressure is low and trend is stable enough | keep reading targeted files only; no special checkpoint required |
| `watch` | pressure or cache instability could make the next broad step costly | write a task packet before broad work; keep dynamic outputs in files |
| `throttle` | another broad step is likely to degrade recovery or UX | finish the current validation or checkpoint, then split the task |
| `critical` | the session is too heavy for new broad work | create a durable packet and continue from saved state in a fresh/compacted segment unless the remaining action is tiny |

## Task Packet Requirements

## Compact Entry Packet

A compression packet is an entry index, not a compressed transcript. Keep it
small enough that reading it does not materially expand a fresh context. It
should preserve the key evidence chain only:

- current objective and exact next action;
- authoritative source-of-truth paths;
- commit ids, report paths, validation commands, or reviewer report anchors;
- unresolved risk or sync gap that changes the next action.

Completed work that already lives in reports, commits, project state, or
validation logs should be referenced by path, not summarized again. Open those
paths only when the entry is ambiguous, state conflicts, validation fails, or
the next action depends on a missing fact.

Size target: keep normal entry packets under about 1-2 KB and avoid exceeding
about 3 KB. If more detail is needed, write a separate evidence report and link
it under `handoff_paths`.

## Automatic Compression Checkpoint

After a recommended checkpoint, major closure point, or user-visible "this round
is closed" moment, do not wait for Xiao Q to ask for compression when the live
gate is `watch`, `throttle`, or `critical`. Automatically write or refresh a
compact entry packet that includes only the key evidence chain:

- the last completed objective;
- authoritative source-of-truth paths;
- changed repositories and local commit ids when available;
- validation already run or report anchors;
- push/sync gaps that affect the next action;
- exact next action for a fresh or compacted continuation.

Use a path under the active personal hub or project report directory, such as
`reports/context_governor_<date>/compression-packet-<topic>.md`. Then keep the
final answer short and recommend continuing from that packet or `ACTIVE_WORK.md`.

This is not platform memory compaction. It is a compact entry index that lets
the next segment avoid carrying the long chat narrative or reopening completed
reports unless the evidence chain breaks.


A useful packet is short enough to paste or load in a fresh segment without
recreating the old context. Include:

```text
TASK-PACKET v1
objective:
source_of_truth:
current_state:
changed_files:
constraints:
no_edit_zones:
next_actions:
validation:
handoff_paths:
residual_risks:
```

Use authoritative file paths instead of long explanations. If validation has
not run, say exactly which command remains.

## Operating Rules

- Prefer one deliverable or one validation loop per segment once pressure is in
  `watch` or higher.
- Use source/runtime mirror paths as handoff anchors instead of reopening full
  chat history.
- Keep research findings, sub-agent output, visual reports, and token JSON in
  reports; pass only short summaries and paths forward.
- When the active pointer is stale or the last assistant recommendation matters,
  use `session_pointer.py` before broad recovery and then write the recovered
  next action into durable state.
- Before final closure of a context-governor improvement, validate with at least
  one scenario: current token JSON, one packet write, and a mirror/source sync
  check.

## Escalation Boundaries

Allowed without extra user approval when filesystem permissions permit:

- read-only token scans;
- local task-packet or work-item checkpoint writes;
- targeted validation commands;
- runtime mirror refresh of already-approved skill surfaces.

Ask before:

- pushing to remotes;
- public/GitHub sync;
- destructive cleanup;
- broad installs or global configuration changes;
- copying private or restricted material into public artifacts.
