# Project Bootstrap And Memory

Use this reference for creating new managed projects, blank-machine recovery,
project-local skills, durable memory files, and human-readable overviews.

## Activation

| Trigger | Tier | Risk | Action |
|---|---|---|---|
| New project | Project | ask for remote/push | Bootstrap repo, memory files, and optional project skill. |
| Blank machine recovery | Deep | ask before clone/push | Restore hub, skills, and only required projects. |
| Project overview request | Project | allow local write | Use `q-project-overview` and link to durable state. |
| Repository naming or migration | Deep | ask before rename/delete | Read repository naming and migration references first. |

## New Project Bootstrap

When the user starts a new project:

1. Ask for or infer:
   - local project path
   - remote Git URL, if available
   - project name and one-line objective
2. Create or clone the repo.
3. Add baseline folders when appropriate:
   - `docs/`
   - `scripts/`
   - `assets/`
   - `archive/`
   - `skills/<project>-workflow/` when project-specific recovery rules are
     needed
4. Add durable memory files from `assets/templates/`:
   - `README.md`
   - `PROJECT_STATE.md`
   - `DECISIONS.md`
   - `TASKS.md`
   - `CONTINUATION_PROMPT.md`
   - `ENVIRONMENT.md`
   - `PROJECT_OVERVIEW.md`
5. Initialize Git if needed, add remote if provided, commit, and push one
   default branch only. Before the first push, run
   `git ls-remote --symref origin HEAD` and `git ls-remote --heads origin` when
   a remote exists. Prefer the hosting service's configured default branch when
   `HEAD` is discoverable. If an variant-specific internal Git remote Server repo is empty and `HEAD`
   is not discoverable, prefer `master` for the first push unless the user has
   explicitly configured the repository default to `main`; do not push `main`
   into a repo whose default branch is still `refs/heads/master`.
6. After the first push, verify with `git ls-remote --symref origin HEAD` and
   `git ls-remote --heads origin`. The remote `HEAD` target must exist in the
   remote heads list before the push/bootstrap task is considered complete. If
   `HEAD` is missing or points to a nonexistent branch, fix it immediately by
   aligning the pushed branch with the repository default or changing the
   repository default branch. Avoid leaving duplicate `main` and `master`
   branches long term; delete the non-default duplicate after confirmation.

Before creating, renaming, or registering workflow infrastructure repositories,
read `references/repository-naming.md`. Use consistent slugs across remote
repository names, local folders, registry project keys, and installed skill
folders unless a deliberate compatibility alias is recorded.

During rename recovery, audit registry keys for accidental broad names such as
`test`, `tmp`, `demo`, or `skills`. If a key is too broad to search or discuss
safely, prefer the full canonical slug in current registries and keep the broad
name only as a historical alias in the work item or rename queue.

## Project-Local Skills

Use a project-local workflow skill when a project has recurring domain context,
special file conventions, customer/material rules, hardware setup, or
validation steps that are not reusable across unrelated projects.

Recommended source location:

`<project>/skills/<project-slug>-workflow/SKILL.md`

Installed discovery copy:

`%USERPROFILE%\.codex\skills\<project-slug>-workflow\SKILL.md`

Rules:

- Treat the project copy as the source of truth.
- Install or synchronize a copy into `.codex\skills` only for auto-discovery.
- Keep project-local skills concise; put detailed state in durable project
  files.
- Do not add project-local skills to the reusable `skills` collection unless
  they become generic.

## Durable Memory Files

Use these files consistently:

- `README.md`: project purpose, structure, key files, and standard resume
  prompt.
- `PROJECT_OVERVIEW.md` / `PROJECT_OVERVIEW.html`: human-readable project
  overview and project map for Xiao Q.
- `PROJECT_STATE.md`: current objective, latest outputs, active assumptions,
  validation status, and next steps.
- `DECISIONS.md`: dated decisions, rationale, and alternatives rejected.
- `TASKS.md`: active work, backlog, completed work, and paused/debug
  checkpoints worth preserving.
- `CONTINUATION_PROMPT.md`: short prompt that lets a fresh Codex session resume
  the project with minimal context.
- `ENVIRONMENT.md`: machine setup, tools, dependencies, template paths,
  hardware connections, build/run commands, and reproduction notes.

Do not create a separate temporary handoff file unless the user explicitly
asks. Prefer updating these durable files.

Keep durable memory concise enough for token-aware recovery:

- `ACTIVE_WORK.md`: index only; avoid project detail.
- `work-items/*.md`: objective, outputs, validation, and next action; avoid
  transcripts.
- `PROJECT_STATE.md`: current facts and direction; archive old narrative.
- `CONTINUATION_PROMPT.md`: short recovery prompt, not a full project summary.
- Large logs, PPT text exports, papers, and generated artifacts should be
  stored as files with concise summaries and paths.

## Human-Readable Overview

Use `q-project-overview` when the user asks for a project summary, project map,
mind map, or a cleaner human-facing overview. Keep overview files concise and
link to authoritative memory files instead of duplicating all state.

Recommended files:

- `PROJECT_OVERVIEW.md`: editable source.
- `PROJECT_OVERVIEW.html`: generated reading page.

For research projects, emphasize project purpose, research direction, key
reports, slides, simulations, evidence limits, and next customer or PoC
actions. For demo or firmware projects, include hardware, software, connection,
build, flash, run, validation, and handoff information.

## Blank-Machine Bootstrap

When the user provides only the personal internal Git remote URL or asks to recover on a
blank computer:

1. Clone or create the user's private personal hub from
   `<private-personal-hub-remote>` or the company starter.
2. Read `MACHINE_BOOTSTRAP.md`, `PROJECT_REGISTRY.md`, optional
   `SKILL_REGISTRY.md`, and `personal-state/ACTIVE_WORK.md`.
3. Recreate `%USERPROFILE%\.codex\q-personal-state` from
   `<personal-hub>\personal-state`.
4. Clone or restore the skills collection and install required skills.
5. Clone only the project repositories needed for the active work item.
6. Resume the project through its local workflow skill and durable memory
   files.

## Minimal Resume Target

Keep every managed project recoverable from a prompt like:

```text
Continue <project>. Use q-workflow.
```

To make that work, keep `CONTINUATION_PROMPT.md` short and current, keep
`PROJECT_STATE.md` honest about the next action, and commit meaningful
checkpoints before switching tasks.
