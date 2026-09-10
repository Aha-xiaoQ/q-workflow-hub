# Repository Naming And Rename Governance

Use this reference when creating, renaming, or auditing workflow repositories,
local folders, registry keys, installed skill folders, or starter packages.

## Goals

- Make names predictable across remote repositories, local folders, registry
  project keys, and installed skills.
- Preserve recovery during migrations by recording compatibility aliases and
  old names until they are safe to retire.
- Avoid broad renames that create more recovery risk than clarity.

## Naming Scheme

Prefer lower-kebab-case slugs.

Use these patterns:

- Public workflow starter: `q-workflow-hub`
- Public reusable workflow skill: `q-workflow`
- Private workflow hub: user-owned private state repo, commonly named `workflow-hub` or `q-workflow-state`

Avoid new underscores in repository names. Keep underscores only for legacy
remotes or external systems that already use them.

## Local Folder Policy

For managed Git repositories, the local folder should normally match the remote
slug in lower-kebab-case. Treat workspace parent folders, such as a user's
project root, as user-configurable containers rather than repository names.

The personal control hub should also use the canonical slug for new installs,
for example `workflow-hub`. Existing hub paths may remain temporarily as
compatibility recovery paths when they are already hard-coded in profiles,
installed skills, bootstrap notes, and active work records. Record such paths
as compatibility aliases with a retirement plan; do not use them as examples
for new projects or promotion packages.

## Repository Identity Gate

Before `pull`, `push`, `clone`, `sync`, `install`, or recovery from another
machine, identify the repository by evidence, not by a remembered folder name.
The accepted identity is:

```text
canonical_slug = remote repository slug
primary_path = registry or q-profile path whose .git remote matches the slug
compatibility_aliases = documented old local folders or staging names
```

Pass conditions:

- local folder name equals the remote slug; or
- local folder name differs, but the folder is listed as a compatibility alias
  in the active registry/profile and `.git\config` remote matches the canonical
  repository.

Block conditions:

- two local folders match the same remote and no registry/profile marks one as
  primary;
- local folder name differs from the remote slug and no compatibility alias is
  recorded;
- a registry path exists but points to a Git repo with a different remote;
- a broad or legacy key such as `project`, `skills`, `test`, or `demo` is the
  active lookup name for a current repository.

When a mismatch is intentional, record it as an alias instead of silently
accepting it. This keeps staging folders such as a public checkout or old hub
path recoverable without teaching new users the old name.
## Alignment Rule

When practical, align all of these to the same slug:

- remote repository name;
- local project folder;
- `PROJECT_REGISTRY.md` project key;
- `SKILL_SYNC.md` source entry;
- installed `.codex\skills\<skill-name>` folder for installable skills;
- user-facing prompt examples.

Avoid broad registry keys such as `test`, `demo`, `tmp`, `skills`, or
`project` for current entries. They are hard to search, easy to match
accidentally during recovery, and often produce unsafe rename suggestions. If
one exists historically, replace the active key with the full canonical slug
and record the old name as a compatibility alias or historical note.

If one layer cannot be renamed yet, record it as a compatibility alias with:

- old name;
- new canonical name;
- why it remains;
- retirement condition;
- validation already performed.
## Related File Placement

Keep naming and recovery governance in one management area per repo instead of
spreading it through ad hoc notes:

- project-specific naming decisions, migration maps, and alias retirement notes
  go in `00-project/`;
- reusable workflow rules go in the owning skill's `references/`;
- cross-project routing inventories go in the workflow hub registry
  and `docs/standards/`;
- historical research or long audit evidence goes in dated `reports/<topic>/`
  folders and should link back to the active rule, not duplicate it.

Do not move durable root memory files such as `README.md`, `PROJECT_STATE.md`,
`TASKS.md`, `DECISIONS.md`, `ENVIRONMENT.md`, or
`CONTINUATION_PROMPT.md` into the archive area. They are intentionally visible
at the project root for quick recovery.

## Rename Sequence

1. Capture recoverable scoped state and classify dirty-file ownership in each
   affected repo. Preserve unrelated changes; they do not by themselves block
   a non-overlapping local rename. Apply remote freshness/push prerequisites
   only to an explicitly authorized remote migration, not local-only work.
2. Decide whether the old name is a compatibility alias, pending rename, or
   permanent exception.
3. For an explicitly authorized remote migration, rename the remote first only
   when the hosting service supports it and the blast radius is understood;
   honor a user-owned remote rename. Skip this step for local-only renames.
4. Update local `origin` URLs only when the remote actually changed and verify
   `git remote -v`; preserve the existing remote for local-only renames.
5. Rename local folders only after confirming target paths do not already
   exist and stay inside the expected workspace root.
6. Update registries, skill sync records, scripts, README/state/task files, and
   installed runtime skill copies.
7. Scan active records for old names. Do not rewrite historical work items
   unless the old text is misleading current recovery.
8. If any affected repository is dirty, classify the dirty state before
   continuing. Do not combine a rename with unrelated generated artifacts,
   project outputs, or review notes unless the work item explicitly makes that
   part of the same checkpoint.
9. Validate skills and scripts from the new paths.
10. Checkpoint only the reviewed rename changes in affected source/state repos.
    Push only the explicitly authorized candidate and targets under
    `sync-and-push-policy.md`; record other remote surfaces as pending.

## Validation Checklist

- `git status --short --branch` is clean before and after the migration.
- `git remote -v` shows the intended canonical remote URL.
- Old active names do not appear in current registries, active work, scripts,
  starter docs, or installed canonical skill copies except as documented
  aliases.
- Skill validation passes for changed skills.
- `git diff --check` passes for every changed repo.
- Privacy or public-safe scans pass before pushing public-facing repositories.
