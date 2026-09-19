# Sync And Push Policy

Use this reference for commits, pushes, publication, checkpoint cadence,
permissions, end-of-round workflow, and generic-skill synchronization.

## Activation

| Trigger | Tier | Risk | Action |
|---|---|---|---|
| Local status/diff/validation | Quick | allow | Run targeted local commands. |
| Local commit checkpoint | Project | allow when meaningful | Review diff and commit scoped changes. |
| Push/upload/publish | Project/Deep | ask | Fetch first, verify remote freshness, summarize target, branch, commits, reason, then ask or push if explicitly approved. |
| Public/GitHub sync | Deep | authorize + scan | Fetch, verify freshness, scan the exact candidate, then use existing scope-specific authorization or ask if missing. |
| Destructive cleanup or credential changes | Deep | ask/deny | Ask explicitly; never infer from fuzzy commands. |

## Sync And Push Policy

Use minimal push by default. Local commits and remote pushes are separate
decisions: commits can create recoverable checkpoints, but pushes should be
rarer and usually confirmed by Xiao Q first.

Push only after the current candidate and target are explicitly authorized and
the applicable freshness/publication checks pass. Preparing a release, a ready
artifact, elapsed time, and recovery risk are reasons to propose a push, not
authorization to perform one. In particular:

- Xiao Q explicitly asks to push, upload, or publish the current candidate to a
  known target. For ambiguous backup/handoff requests, resolve the destination;
  `prepare a release` authorizes preparation, not publication.
- If a major deliverable or cross-machine handoff is ready, propose the scoped
  push and preserve a local checkpoint while awaiting authorization.
- If a critical recovery rule changed, preserve it locally and explain the
  recovery risk when proposing remote backup; do not silently push.
- Work has accumulated for roughly a day or a long focused session without a
  push; in this case, ask Xiao Q whether to push instead of pushing silently.

Defer and batch later when:

- The change is a non-critical completed-work note.
- Multiple mirrors or infrastructure repos need routine synchronization.
- Installed skill copies were updated only to keep the current machine usable.
- The change is cosmetic documentation or an overview refresh that does not
  affect recovery.
- The change is a small help, alias, wording, formatting, or collaboration
  behavior tweak. Prefer local source/runtime updates and a pending-sync note
  unless Xiao Q explicitly asks to push.

When deferring, leave a concise pending-sync note in the relevant task or final
response. Do not let routine multi-repository sync dominate a normal project
task.

## Push Target Scope Lock

Push requests are platform- and repo-scoped by the user's words.

- A named hosting platform limits the target to the explicitly identified
  repository on that platform. Do not include other repositories, distribution
  mirrors or runtime synchronization unless requested.
- Generic `push`, `upload`, or `sync` applies only to the already locked active
  repo. If more than one repo could qualify, stop and ask for the target.
- Workflow-rule or skill-maintenance opportunities discovered while handling a
  task push are pending notes by default. They are not added to the push scope
  unless Xiao Q separately asks for workflow sync, publication, or a release.

Before any push command is run, show a target preview and wait for confirmation
unless the same current instruction already approved that exact target:

```text
I understand this as <platform>-only.
Excluded: <excluded platforms/repos>.
Target: <repo> -> <remote>/<branch>.
Scope: <commits or files>.
Reason: <why pushing now>.
Confirm push?
```
Before pushing:

- Run a remote freshness gate first: `scripts\validate-push-readiness.ps1` when available, or at minimum `git fetch --prune <remote>` followed by `git status --short --branch` and an ahead/behind check against the upstream branch.
- If the local branch is behind or diverged after fetch, pull/rebase and resolve before pushing. Do not rely on a stale local `origin/main` or on push rejection as the primary check.
- If fetch is blocked by network, credentials, or proxy setup, do not push blindly. Report the remote-freshness gap and ask whether to retry through the approved route.
- Summarize the target repo(s), branch, last relevant commit(s), ahead/behind result, and reason for
  pushing.
- Ask only when scope-specific push authorization for the candidate and target
  is missing or revoked. Authorization persists across turns in the same task;
  elapsed time or a new briefing does not invalidate it.
- Resolve the intended repository and candidate from the current request and registered context. Do not demand a version number or exact command phrase when the user already authorized this scoped update and push. Ask if multiple destinations remain genuinely plausible.
- Do not infer broad multi-repo push from generic words such as `push`, `同步`,
  or `上传`; ask if the target is unclear.
- Never push public/GitHub targets without the public-safe scan and valid
  scope-specific authorization. Existing explicit authorization satisfies the
  permission requirement; a newer cancellation or exclusion still takes precedence.


## Personal Hub Versus Promotion Hub

Use different push cadence for personal recovery state and promotion/share repos:

- `q-personal-hub`: propose backup more readily after meaningful recovery-state changes. This private state-of-truth hub still requires explicit authorization for the current remote push; record local-only state while pending.
- Promotion/share repositories are no-push by default for routine local notes,
  runtime-only fixes and ordinary checkpoints. An explicit instruction to update
  and push the scoped public package authorizes that action after validation;
  it does not authorize private skills, personal state or other repositories.
- Do not push every personal note, experiment, local report, or runtime-only fix into the promotion hub. Record a pending promotion note instead, then promote after sanitization, validation, and a stable feature boundary.

Remote repository renames are user-owned operations. If Xiao Q says he will rename a remote, do not call hosting-service rename APIs or change remote names speculatively. After he confirms the remote rename, update local `origin` URLs, registries, and recovery docs, then run status and validation gates.
## q-workflow Three-Copy Sync

`q-workflow` normally exists in three maintained places:

- standalone maintenance repo: `<standalone-q-workflow>`
- starter bundled copy: `<starter-root>\skills\q-workflow`
- runtime installed copy: `%USERPROFILE%\.codex\skills\q-workflow`

Use this order for workflow-rule changes:

1. Edit the intended source copy first. For system-level workflow rules, prefer the standalone repo, then sync the starter bundled copy. For starter packaging or onboarding-only changes, edit the starter copy and record whether the standalone repo is intentionally unchanged.
2. Compare standalone versus starter for changed files before claiming completion. If they differ, classify each difference as synchronized, starter-only, standalone-only, or pending-sync.
3. Refresh the runtime copy only from the validated source or starter copy.
4. Validate the edited copies with the available skill validation script or targeted script compile/check commands.
5. Record any intentional unsynced state in `SKILL_SYNC.md`, the active work item, or TODO before closing.

A completed workflow-rule round must say which of the three copies was edited, which was refreshed, and what validation passed.

## Permission Posture

Prefer low-friction approvals without reducing safety:

- For routine, low-risk, recoverable operations needed for the current task,
  use tool-level approval requests directly and choose narrowly scoped reusable
  approval rules when available.
- Do not request approvals for work that is not needed to answer the user's
  current prompt. A completed-state resume should not trigger new Git commits
  or pushes just because the repository can be inspected.
- Ask explicitly before destructive actions, credential handling, global
  configuration changes, publishing or releasing, deleting or moving large
  directory trees, changing unrelated user files, or actions with unclear blast
  radius.

## Checkpoint And Push Cadence

Prefer recoverable checkpoints over constant pushing:

- Create or update the personal work item as soon as a task becomes concrete.
- Use local commits for meaningful, recoverable checkpoints, especially before
  switching tasks or ending a long round.
- Propose a push at a key checkpoint or completed work round when useful.
  Neither completion nor recovery risk waives explicit push authorization.
- Do not turn bookkeeping-only corrections into immediate pushes by default. If
  the user points out an incomplete test or wrong completion status, record the
  correction locally, restate the missing validation, and resume the work.
  Batch the proposed push with the next tested checkpoint; a request to sync
  still needs a clear candidate and destination.
- If push is deferred or fails, record the pending sync state in the work item
  and final response.
- If a new task interrupts unfinished work, update `PAUSED_WORK.md` before
  starting the new task so the previous task can be offered later.

## End-Of-Round Workflow

At the end of a completed work round:

1. Verify generated artifacts exist and are readable/openable where practical.
2. Run relevant build/test/validation commands when feasible.
3. Update durable memory files with concise facts, not full chat transcripts.
4. Run a bounded relevant closure-ledger check: compare the current task id or
   objective against `ACTIVE_WORK.md` `Current Focus`, the active work item,
   matching `TODO.md` entries, `PAUSED_WORK.md` only when the task was paused or
   resumed, and affected runtime mirrors. Prefer
   `scripts/closure_ledger_check.py --task-id <id> --expect closed` for the
   mechanical pass. Completed work must not remain as the default resume target
   or an Open TODO. Do not turn this into a full hub audit unless the task is
   workflow-audit or state repair.
5. Run the remote freshness gate for any repo that may be pushed.
6. Run `git status --short --branch` for the active project.
7. Review relevant diffs.
8. Commit the active project when the checkpoint is meaningful.
9. Re-run the remote freshness gate if new commits were created after the first check.
10. Push according to the sync and push policy. Prefer pushing the active
   project and critical recovery state only; batch routine infrastructure sync.
11. If the work touched workflow rules, reusable skills, starter packages, or
   runtime skill copies, run a generic-skill sync audit before claiming
   completion: compare source, bundled, runtime, public, and company copies;
   classify intentional public/company differences; record any pending sync
   instead of relying on the user to notice a missing push or public update.

Closure records should be compact and colocated with the evidence a future
session will inspect: active work item for personal-state work, final report for
workflow/skill work, or project handoff for project deliverables. Use
`assets/templates/CLOSURE_RECORD.md` when the handoff is more than a sentence.
The record must connect the original objective to evidence, validation,
`ACTIVE_WORK`/`TODO`/work-item state transitions, mirror sync state, parked
follow-ups, and residual risk.

If `git push` needs interactive credentials, open or ask the user to use an
interactive terminal. Do not leave background Git processes waiting for
credentials.

## Updating This Skill

When the user discovers a better workflow:

1. Update this skill or its templates.
2. Keep matching copies synchronized:
   - `q-workflow-hub\skills` reusable package sources
   - standalone skill repo, if one exists
   - installed `.codex\skills` copy
3. Validate with the skill validation script if available.
4. For small feedback loops, keep the first fix local: update the source copy
   and installed runtime copy, validate narrowly, and report pending starter,
   mirror, or remote sync. Preserve scoped local checkpoints as appropriate;
   push only with explicit authorization for the candidate and destination.

Keep this skill concise. Put reusable details in `references/` and reusable
project file starters in `assets/templates/`.


## Standard Variant Sync Gate

When a task changes public/company starter parity, use the scripted gate instead
of relying on ad hoc file comparison:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-root> `
  -CompanyRoot <company-root> `
  -OutputDirectory <report-dir>
```

This gate should run scans, `git diff --check`, PowerShell parsing, Python
compile checks, parity audit, and classification. For manual runs, use
`scripts/audit-variant-parity.py` followed by
`scripts/classify-variant-parity.py`.

Nontrivial sync rounds need a local expert pass before push or release:
`Workflow Distiller` checks classification and durable policy, `Code Auditor`
checks script/path/diff safety, and `Usability Validator` checks setup and
package usability. Add `Pagewright` for HTML/setup pages, `Visual Arbiter` for
diagram/PPT surfaces, and `Doc Architect` for shared docs.

Do not auto-copy company/variant-specific assets, internal paths, project state, credentials,
customer material, or active-work data into public. Sanitize or split company
behavior into generic rules first, then scan the public target.

## Public And variant-specific Share Variant Parity

- When a generic, shareable workflow feature, helper page, quick command,
  validation gate, or onboarding document is completed in the public version or
  the variant share version, check the other version before closing the round.
- Public and variant share variants should stay functionally aligned for generic
  behavior. variant-specific may add company-specific naming, data-classification,
  permission, template, path, and internal sharing guidance, but should not miss
  generic onboarding or workflow improvements that public users receive.
- For a broad sync round or whenever Xiao Q asks whether the variants are
  aligned, run the standard variant sync gate when available, or run `scripts/audit-variant-parity.py --public-root <public-root>
  --company-root <variant-root> --output <report.md>` and classify every reported
  difference as synchronized, intentionally variant-specific, public-safe
  pending work, or private/company-only blocked from public sync.
- If the other variant is intentionally not updated in the same round, record a
  concrete pending-sync TODO or work item with the source commit/report path,
  target repo, skipped surfaces, and reason for deferral.
- Before pushing either share variant, state whether the remote freshness gate passed and whether the counterpart parity check passed, was updated, or remains pending.
