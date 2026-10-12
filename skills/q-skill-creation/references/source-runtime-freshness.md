# Source, Runtime And Mirror Freshness

Use when ownership/drift is unclear, synchronizing skills, or claiming installed,
portable or released state. Compare affected paths, not every repository.

## Authority and baseline

Canonical source is the registered repository; runtime and bootstrap are
rebuildable copies, not automatic merge authority. Personal skills/preferences
belong in the private hub; generic public skills in the public source. Preserve
intentional company/private variants and unrelated dirty work. Caches/reports
are not canonical assets. External code/assets need compatible rights.

Before writing, compare the touched source and declared mirrors. If they differ,
inspect content and validation evidence rather than trusting timestamps or the
directory name. Backfill a newer validated runtime to canonical source before
normal edits. Never copy an older source over unclassified newer work.

## Checks by claim

| Claim/action | Evidence |
|---|---|
| Small local edit | Target readback/diff; no network |
| Multi-surface edit | Pre-edit baseline comparison for touched files |
| Installed/synced | Post-sync hash/readback of all touched declared surfaces |
| Push | Above, exact diff/scope, successful fetch, reviewed destination and authorization; public scan if applicable |
| Stable/team/rebuild | Applicable install/release contract and complete in-scope manifest |

Use `scripts/surface_freshness_check.py --skill <id> --roots <source> <runtime>
--files <affected-paths> --fail-on-drift --json-out <report>` for maintained
mirror claims. Add bootstrap or explicit counterparts where declared; use
`--all-files` for whole-skill claims. `--check-git` reports repository state;
`--fail-on-upstream-drift` is for a release candidate intended to be clean and
aligned. Unrelated dirty files in a maintenance checkout do not become ours.

Classify differences once: fixed, intentional variant, stale source/runtime/
bootstrap, private-only, generated-ignore, or pending with exact owner/path.
Unclassified touched drift blocks sync/install/release claims. Pending public
promotion can remain local with exact changed paths and reason; never imply
GitHub is updated. Generic counterpart rules require a file-level decision.

## Apply and finish

1. Preserve the chosen baseline and check dirty ownership.
2. Edit and validate canonical source.
3. Sync only affected files through the documented installer or a bounded copy
   with pre-write comparison; prune only a named skill whose source is complete.
4. Recheck hashes, referenced inputs and affected encoding. Record excluded
   surfaces and residual drift in the existing work item.

Referenced scripts/assets must exist or have an explicit optional fallback.
A default asset cannot live solely in a disposable cache. Packaged assets keep
source/license/use information. Private paths/assets and credentials do not
enter public variants. Verify suspicious text as UTF-8; never copy terminal
mojibake into source. Run encoding_guard when localized text changes.

A local emergency runtime recovery exception needs user scope and a source
backfill follow-up; it cannot support release or bypass privacy/license checks.
