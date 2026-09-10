# q-workflow v1.1-beta

A Windows-first public starter for file-backed project recovery, explicit task
state, reusable skills and review gates. It remains beta software.

## Changes

- Hardened task-pointer validation and pilot state transitions.
- Registry-driven installation of all 17 bundled source skills, plus the
  generated assistant profile.
- Working empty-hub setup, first-task registration and TODO display metadata.
- TODO names preserve the user's original text; explanatory fields currently
  use a Chinese framework. This is not automatic translation.
- Public-install tests exercise actual installed commands, mirror rebuilding,
  package parity, update preservation and fault-injected rollback.

## Installation and migration

Use the [English](../../QUICKSTART.md) or [Chinese](../../QUICKSTART.zh-CN.md)
quickstart. Git, Python 3.10+ and Windows PowerShell are required.

This distribution starts a new public Git history. Existing starter clones
must not merge the old history into this release. Keep any local modifications
privately, clone `v1.1-beta` into a separate directory, then use the documented
updater against your existing private hub and runtime. Do not rerun the
initializer as an upgrade: it writes setup configuration.

The initializer creates a runtime state mirror only when its directory does
not already exist. Existing or partially initialized mirrors require explicit
validation and repair; they are never silently overwritten. A TODO commit
updates authoritative files; use `q_base_command.py --preflight-sync`, then
`--sync-runtime --audit` when rebuilding the read-only mirror is intended.
Run these from the installed skill with your own configured profile.

## Verification and limitations

Installation checks cover fresh setup, state recovery, update preservation and
rollback on Windows.

Existing users should review their configured paths, permissions and integrations
before updating, then verify the normal resume flow with their coding agent.

## Recovery

Back up your private hub and runtime before updating. A failed package switch
is rolled back by the updater; do not discard your private backup after a
successful install until your normal resume flow has been verified. This
release supports updates through the quickstart's documented migration path.
