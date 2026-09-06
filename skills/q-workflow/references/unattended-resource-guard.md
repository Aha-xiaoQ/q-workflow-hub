# Unattended Resource Guard

Use this reference for recurring heartbeats, autonomous loops, or any run that creates session, log, or subagent state on the system volume.

## Executable Gate

```text
rule_id: unattended-resource-guard
level: executable gate
trigger: before creating, resuming, or retrying an unattended automation, heartbeat, or isolated subagent; on a user stop request; or after a resource/write failure
must: check the system-volume free space and persist the run state before mutating the automation. GREEN (>= 3 GiB): normal bounded work is allowed. YELLOW (>= 1 GiB and < 3 GiB): finish only the current atomic step, write a recovery point, and do not create a new long loop or parallel subagent. RED (>= 512 MiB and < 1 GiB): set PAUSED_RESOURCE and cancel the heartbeat before returning; do not create or retry an automation or subagent. CRITICAL (< 512 MiB or any session/write failure): do not retry business work; persist PAUSED_RESOURCE or STOPPED, then execute the one-time stop path only.
blocks: creating/retrying unattended work, claiming an automation stopped when deletion is unverified, and emitting ordinary progress from a blocked loop
check: record the free-space result and run state; verify the automation id no longer exists after a stop; verify PAUSED_RESOURCE or STOPPED from durable state before honoring an old heartbeat instruction
repair: for a stop request, write STOPPED plus automation id and deletion-pending state to a durable non-system-volume project/state file, then delete the automation. For PAUSED_RESOURCE, write the same cancel-pending state before returning, then delete or disable the heartbeat. If deletion fails, enter one-shot circuit-breaker mode: no training, no repeated notices, and only one retry after the system volume recovers to at least YELLOW. Any residual heartbeat must first read STOPPED/PAUSED_RESOURCE and end silently; it must not execute task work or emit a normal status. For a resource pause, obtain explicit approval before deleting or moving user data; prefer reversible movement of explicitly archived data to a non-system volume.
waiver: Xiao Q may waive a non-destructive local pause only; no waiver permits background retries while CRITICAL, deletion of current sessions, or unverified stop claims
scope: resource governance and automation lifecycle only; it does not approve work artifacts, change normal task quality gates, or encode user paths, project names, automation ids, or cleanup targets
```

## Session archive hygiene (added after a real Codex lag incident)

`archived_sessions` is storage, not a second active queue. When an archived or
completed subagent log is no longer needed on the system volume, move it
reversibly to an explicitly named non-system-volume archive and leave a
manifest/readme. Do not copy it back merely to make a thread visible. A thread
visibility problem must be solved through thread metadata or a compact recovery
note, not by rehydrating multi-gigabyte history.

Before starting or resuming unattended work, sample: system-volume free space,
active thread statuses, and the size/growth of the largest session files. If a
completed child log is larger than 100 MB and its parent is idle/stopped, it is
an archive candidate; never move the current turn's session or an active child.
After a stop, verify both the thread status (`idle`/`stopped`) and that no new
session file is being written for that parent. If an archived log reappears in
the system-volume queue, classify it as archive rehydration and offload it
again only after confirming it is completed.

Anti-patterns: treating an archived file as disposable cache, restoring a full
history to fix a UI listing, starting a new subagent while large completed logs
are accumulating, or claiming a lag fix without a before/after free-space and
process-memory sample.

## Required State Fields

- `run_state`: `ACTIVE`, `PAUSED_RESOURCE`, or `STOPPED`
- `system_volume_band`: `GREEN`, `YELLOW`, `RED`, or `CRITICAL`
- `automation_id`: optional and private
- `stop_requested_at`: optional
- `automation_delete`: `not_requested`, `pending`, `verified`, or `failed`
- `resume_condition`: the exact capacity band and next safe action

## Regression Scenarios

1. At 2 GiB free, a loop records YELLOW, finishes no new fan-out work, and writes a recovery point.
2. At 400 MiB free, a loop records PAUSED_RESOURCE, cancels the heartbeat, and creates no new subagent or heartbeat.
3. At 0 free with a user stop request, STOPPED is persisted off the system volume before deletion; a failed deletion produces no regular loop output, and a residual heartbeat exits silently.
4. After storage recovers, a pending stop retries deletion once and verifies absence; it does not resume the old task.
5. A PAUSED_RESOURCE task resumes only after GREEN and one minimal runtime-write smoke test.

## Anti-Patterns

- Treating free space on a project/data volume as proof that the system volume can write session or automation state.
- Repeating the same retry or blocked notification on every heartbeat.
- Deleting current sessions, unknown user data, or system files to make a loop continue without explicit approval.
- Treating an API error during automation deletion as proof that the automation has stopped.
