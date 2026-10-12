# Source Runtime Remote Consistency

Read before an in-scope reusable package install, mirror, commit, push, release or readiness claim. Scope evidence to that claim.

## Source Runtime Remote Consistency Gate

When: committing, pushing, publishing, syncing to GitHub/Bitbucket, updating
runtime, refreshing templates/bootstrap copies, mirroring branches, or claiming a
skill/workflow package is installed, released, synced, mirrored, or colleague-ready.
Goal: prevent local runtime skills, canonical source, installer templates, and
remote branches from drifting apart.
Strength: hard gate for skill/workflow pushes and reusable package handoff.

Required lifecycle gate:

Scope the gate to the claim: a local checkpoint needs a reviewed scoped diff;
a local install or mirror refresh needs the affected source/runtime/template
comparison; a remote release or colleague-rebuild claim additionally needs the
approved remote and consumer-path evidence. Steps involving pushed source apply
only to those remote claims. An offline local install may complete with remote
state explicitly unproven. Public eligibility is not permission to push.

1. Identify all in-scope surfaces before staging: canonical source, runtime
   install, bootstrap/template copy, packaged assets, generated user cache, all
   intended remotes, and the exact target branches or tags.
2. Capture `git status --short --branch` and targeted diffs for every source
   repository that will be committed or pushed. Name unrelated dirty files and
   exclude them.
3. Compare key files across source/runtime/template surfaces before commit. Use
   hashes or a freshness script when available; otherwise record exact file
   paths and the comparison result.
4. If runtime is newer than source, backfill source first. Do not push an older
   source just because the repository is clean.
4a. Public scope follows the user's instructions and the maintained publication
   inventory. Absence of sensitive keywords does not make a personal skill
   public. Export only explicitly included packages/files; preserve private,
   withdrawn and unclassified skills locally. Apply generic fixes to an existing
   public counterpart by reviewed hunks, never by copying a private source tree.
   Record intentional variant differences and verify the exact outgoing tree
   and commit range before claiming remote sync or rebuild readiness.
5. After commit and before push, verify the commit contains the intended files
   and no local-only runtime paths, private artifacts, generated scratch output,
   or stale template copies.
6. After push, verify every intended remote/branch tip matches the local pushed
   commit. Check GitHub and Bitbucket separately when both are in scope, and
   confirm the default/release branch is the expected target, not an accidental
   side branch.
7. Verify the installed runtime or colleague-install path can be refreshed from
   the pushed source and that bootstrap/template copies contain the changed rule.
8. In the handoff summary, state the local commit, every remote branch/tip,
   runtime sync state, skipped surfaces, validation commands, and residual drift.

Blocks: saying `pushed`, `published`, `released`, `synced`, `mirrored`,
`installed`, `runtime updated`, `template refreshed`, or `colleague-ready` for a
skill/workflow package when drift on the surfaces required for that specific
claim is unclassified. Say `locally installed; remote not verified` when that
is exactly what was tested; remote publication is not a local-install prerequisite.

Avoid: editing only `%USERPROFILE%\.codex\skills`, pushing only the source repo,
or assuming Git/Bitbucket is correct without proving the runtime install can be
recreated from it.

Regression scenarios: runtime newer than canonical source; source pushed but
runtime not reinstallable; Bitbucket branch pushed while GitHub or source branch
remains stale; bootstrap/template copy missing a changed rule; remote default
branch differs from the intended release branch.
