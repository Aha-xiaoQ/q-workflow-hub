# Source Runtime Freshness And Encoding Gate

Use this reference before editing, syncing, or publishing any skill that has more
than one surface, such as source repo, runtime install, hub mirror, public copy,
company copy, or personal bootstrap copy.

## Why This Exists

A surface can be valid but stale. Do not assume the directory named `source` is
newer than runtime or hub. A stale source copied over a newer runtime can remove
recent routing, lifecycle, taxonomy, metadata, or validation rules without any
merge conflict.

Encoding failures have a similar shape: terminal output can look corrupted even
when the file is valid UTF-8, and copying that terminal mojibake back into a
file turns a display problem into durable data loss.

Unclassified source/runtime/public/company drift is a hard gate under
`rule-hardness-ladder.md`; final handoff must classify it as intentional,
stale, blocked, or fixed.

## Freshness Gate Before Editing

Before editing a skill-system rule, lifecycle file, trigger route, public/company
surface, or runtime mirror:

1. List all known surfaces for the target skill.
2. Check Git status for each repository surface and identify unrelated dirty
   files that must not be staged.
3. Compare the target files across surfaces before choosing a baseline.
4. Treat the newest validated surface as the baseline, not necessarily the
   nominal source repository.
5. If two surfaces differ, inspect whether the difference is intentional,
   unpropagated, or stale.
6. Rebase the stale surface onto the chosen baseline before applying the new
   change.
7. After syncing, read back or hash the key files on every updated surface.

Use `scripts/surface_freshness_check.py` when available to compare hashes and
missing files across surfaces. Hash mismatch is not automatically wrong, but it
is a stop sign: choose a baseline before writing.


## Executable Drift Gate Contract

Use this contract whenever skill drift can affect handoff, runtime refresh,
bootstrap reinstall, public/company sync, push, publish, or release readiness.
The goal is not to make every small edit heavy; the goal is to prevent any
propagation claim while source/runtime/remote drift is unclassified.

- Trigger: maintained skill edit, runtime install refresh, bootstrap/template
  update, public/company sync, remote push, or any statement that a
  skill/workflow package is synced, installed, mirrored, or release-ready.
- Must: compare declared surfaces for in-scope files and classify every drift as
  fixed, intentional variant, stale source, stale runtime, stale bootstrap,
  public-blocked/private-only, generated-ignore, or pending with owner/path.
- Blocks: final handoff claiming sync, runtime reinstall from source, affected
  repo push, stable/team/public-ready labels, and colleague-install guidance.
- Check: run `scripts/surface_freshness_check.py` with registry or explicit
  roots, `--fail-on-drift` for pre-close/release, `--check-git` for source
  repositories, and `--fail-on-upstream-drift` before push claims. Store JSON
  evidence with `--json-out` for nontrivial rounds.
- Repair: choose the newest validated baseline, backfill canonical source first
  when runtime is newer, sync mirrors only from the chosen baseline, then rerun
  the gate and record skipped surfaces.
- Waiver: The user may waive only a non-release local emergency runtime recovery;
  the waiver must include an expiry or follow-up source-backfill work item. No
  waiver is allowed for private/public leaks, missing referenced gate files,
  credentials, or unclassified drift before push/release.
- Scope: `SKILL.md`, `agents/`, `workflows/`, `references/`, `scripts/`,
  schemas, manifests, packaged assets, installer/bootstrap copies, and default
  path references. Exclude generated caches only when the manifest or handoff
  records why they are non-authoritative.

### Mode Tiers

- `quick`: targeted readback or hash for the touched file only; no Git/network;
  use for small local edits that do not claim sync.
- `pre-edit`: compare target files across source/runtime/bootstrap surfaces
  before choosing a baseline.
- `pre-close`: run the drift gate for touched maintained skills and record
  classification; blocks `done` if runtime/source drift is unexplained.
- `pre-push`: add dirty-state, upstream ahead/behind, public/private scan when
  applicable, and explicit target repo/branch summary before asking approval.
- `release`: require manifest/registry coverage, full in-scope file comparison,
  variant/public scan, runtime reinstall evidence, and expert review evidence.

A future `skill_drift_gate.py` may orchestrate manifests, public/private scans,
variant parity, and remote checks. Until then, `surface_freshness_check.py` is
the required executable gate for runtime/source parity, and repo-specific push
readiness scripts remain required for remote freshness.

## Surface Authority Model

Every reusable skill must name which surface owns each kind of material before
edits start. Use these layers unless a project has a recorded exception:

- **Canonical source**: the durable repository copy for the skill, including
  `SKILL.md`, `agents/`, `workflows/`, `references/`, `scripts/`, schemas,
  examples, and packaged assets. This is the normal edit target.
- **Runtime install**: the installed copy loaded by Codex, usually
  `%USERPROFILE%\.codex\skills\<skill>`. Treat it as generated from source.
  Direct runtime edits are emergency recovery only and must be backfilled to the
  canonical source before closure.
- **Company/private variant**: a source surface that may carry private rules,
  company assets, internal paths, or restricted templates. It may install to
  runtime, but it must not be copied into public surfaces without a public-safe
  variant audit.
- **Public variant**: a public-safe source surface. It must not include private
  company assets, local user paths as required defaults, credentials, or
  restricted binaries.
- **Packaged assets**: files intentionally shipped with a skill under
  `assets/`, `template_packs/`, `examples/`, `schemas/`, or another documented
  asset directory. They need a manifest or README that records source, license
  or allowed use, and public/private boundary.
- **User cache or selection**: files under user-local locations such as
  `%USERPROFILE%\...`, Downloads, generated reports, previews, chosen template
  pools, or project scratch directories. These are never authoritative skill
  source by default. Promote them only by an explicit review step that copies
  the selected material into the canonical source asset layout and records why.
- **External examples**: third-party repositories, tutorials, screenshots, and
  sample decks. Use them for mechanisms or grammar only until license and
  attribution allow copying concrete assets.

If a runner or HTML intake uses a user cache, the skill must also define the
packaged source seed, the cache update command, and the rule that user deletion
or selection does not silently rewrite the packaged source.


## Canonical Skill Source Placement

When creating or promoting a skill, choose the canonical source by ownership
before creating files:

| Skill type | Canonical source | Runtime mirror |
|---|---|---|
| Public reusable skill | Public workflow hub `skills/<skill-name>/` | `%USERPROFILE%\.codex\skills\<skill-name>/` |
| Private/company reusable skill | Private/company workflow hub `skills/<skill-name>-<variant>/` or recorded standalone source repo | `%USERPROFILE%\.codex\skills\<skill-name>-<variant>/` |
| Personal/profile skill | Personal hub `skills/<skill-name>/` or `generated-skills/<skill-name>/` | `%USERPROFILE%\.codex\skills\<skill-name>/` |
| Project-local skill | `<project-slug>/skills/<project-slug>-workflow/` | Installed only when that project needs runtime loading |
| Third-party skill mirror | Third-party mirror repo until intentionally forked | Installed with original name or documented compatibility alias |

Do not create new skills directly under random user folders, Downloads, or the
runtime `.codex\skills` directory as the only copy. Runtime-only edits are
emergency recovery and must be backfilled to the owning source before closure.
## Standard Sync Path

For all multi-surface skills, use this direction unless the user explicitly
asks for a recovery from runtime:

1. Discover surfaces: canonical source, runtime install, public/company
   counterpart, personal bootstrap, packaged asset roots, generated outputs,
   and user caches.
2. Check dirty state for every repository surface. Do not stage or overwrite
   unrelated dirty files.
3. Compare the files and asset manifests that are in scope. Include scripts,
   HTML intake files, manifests, schemas, generated helper scripts, and default
   path references, not only `SKILL.md`.
4. Choose the baseline. If runtime has the newest valid behavior, freeze it as
   evidence, backfill the canonical source first, then edit source.
5. Edit the canonical source or the explicitly named source variant. Do not
   edit runtime as the normal path.
6. Validate the source copy.
7. Install/sync source to runtime with the documented sync script or command.
   Runtime pruning is allowed only for the named skill and only after the
   source tree is known complete.
8. Validate runtime and compare hashes for the changed files. If runtime differs
   afterward, record whether the difference is intentional, stale, or blocked.
9. Update user caches only through explicit seed/update commands. A user cache
   may be refreshed from packaged assets, but it must not be used as a hidden
   source of truth.
10. Record skipped surfaces and residual drift in the handoff.

## Variant Counterpart Drift Gate

When a skill has a public/company counterpart, treat drift as a release gate,
not a cosmetic diff:

- `counterpart-review` means "queued for file-level decision"; it is not a
  waiver.
- Generic routing, validation, recovery, source/runtime sync, lifecycle,
  testing, encoding, and user-facing output rules must be synchronized or
  explicitly recorded as blocked.
- Brand/template/classification/private-asset wording may remain variant-only
  only with an owner, reason, review date, and next action.
- After any public/company propagation, compare the changed files across source,
  runtime, personal bootstrap, and standalone mirrors with hashes.

Do not close a public/team release while `sync-required` or
`sanitize-to-public` rows remain. `-AllowUnresolvedParity` is for work-in-
progress reports only; it is not release evidence by itself.

## Hard Blockers

Do not close or publish a skill update while any of these are true:

- `SKILL.md`, workflow, or reference links point to missing files.
- A script, HTML page, manifest, or schema has a default path that neither
  exists nor has a documented optional fallback.
- A packaged asset directory is referenced by code but missing from the skill.
- A user cache, generated report directory, or local review folder is the only
  place where a default asset exists.
- A public surface contains private/company assets, local personal paths as
  required defaults, or unclear-license third-party binaries.
- A runtime-only fix has not been backfilled to source or explicitly frozen as
  an emergency exception.
- A source/runtime/public/company drift was detected for in-scope files and the
  final handoff does not classify it as intentional, stale, blocked, or fixed.
- Asset packs lack a manifest or README with source, license/allowed use, and
  public/private boundary.

## Baseline Selection

Choose the edit baseline in this order:

1. The surface explicitly named by the user for the task.
2. The canonical source of truth recorded in inventory, when it is not stale.
3. The newest validated surface that contains the most recent committed route,
   lifecycle, taxonomy, and metadata changes.
4. Runtime only as an emergency recovery source, then immediately backfill the
   source of truth.

Never copy an older source tree over a newer hub/runtime tree. If source is
older, first update source from the newer validated surface, then apply the new
patch.

## Encoding Gate

Before writing files that include localized text, Chinese aliases, expert names,
or user-facing markdown:

- prefer ASCII for generic standards unless localized trigger text is required;
- when Chinese is required, write UTF-8 explicitly and run `encoding_guard.py`;
- do not copy mojibake displayed by PowerShell `Get-Content` into durable files;
- verify suspicious text with a UTF-8 readback, `git diff`, or encoding guard;
- if terminal display is garbled but `encoding_guard.py` and `git diff` are
  clean, treat it as display mojibake, not file corruption.

## Sync Closure Checklist

Before committing or handing off a skill-system change:

- source/runtime/hub surfaces were compared before propagation;
- chosen baseline and any stale surfaces are recorded in the report or handoff;
- unrelated dirty files are named and excluded from staging;
- key changed files were read back or hashed after sync;
- `quick_validate.py` passed on source and runtime/hub copies when applicable;
- `encoding_guard.py` passed when localized or Chinese-bearing files changed;
- `git diff --check` passed for each repository surface;
- skipped surfaces have an explicit reason.

## Anti-Patterns

- Copying from source to runtime/hub without first checking whether source is
  stale.
- Treating a clean Git status as proof that the content is the newest version.
- Letting unrelated dirty files ride along with a mirror sync commit.
- Fixing mojibake by editing what the terminal displays instead of verifying
  the file encoding.
- Recording a sync mistake only in chat instead of adding a durable prevention
  rule or validation script.
