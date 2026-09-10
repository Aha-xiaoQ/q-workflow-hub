# Public Sync

**English** · [Simplified Chinese](PUBLIC_SYNC.zh-CN.md)

This repository should stay structurally similar to private or company variants
so generic q-workflow improvements can move between them with a clear review
path.

## Shared Structure

Keep these areas aligned unless a documented variant reason exists:

- `README.md`
- `QUICKSTART.md`
- `FIRST_PROMPT.md`
- `AFTER_SETUP.md`
- `MACHINE_BOOTSTRAP.md`
- `scripts\init-user.ps1`
- `templates\workflow-hub\`
- `templates\project\`
- `templates\skills\q-assistant-profile\`
- generic skills such as q-workflow, research discovery, audio/video intake,
  diagram workflow, code lifecycle, project overview, PPT creation/review, and
  other explicitly included companion skills

## Naming Map

| Public | Private or company variant |
|:---|:---|
| `q-workflow-hub` | variant-specific hub repository |
| `q-workflow` | variant-specific q-workflow package name when needed |
| private workflow hub | user-owned private state repository; not part of the public starter release |
| generic skills | generic skills plus private/company-only skills |

## Sync Direction

Public to private/company variants:

- starter structure
- Quick Resume and recovery evaluation rules
- skill creation and validation patterns
- generic templates and onboarding improvements

Private/company variants to public:

- only sanitized generic workflow lessons
- no private paths, internal hosts, project names, customer material, active
  work, project registries, project state, screenshots, credentials, or private
  artifacts

## Review Rule

Before moving a private/company lesson to the public repo, rewrite it as
generic behavior and scan the target repository for private markers.

## Push Readiness Gate

Before pushing any synced public/private candidate, refresh the remote state
first. Run `scripts\validate-push-readiness.ps1 -RepoRoot <repo>` when available.
The gate fetches with prune, checks the upstream ahead/behind state, refuses
dirty worktrees by default, and fails when the local branch is behind or
diverged. If fetch is blocked, record the validation gap and do not push
blindly.

## Standard Variant Sync Gate

Before closing a public/private sync round, run the standard validation gate
from either starter:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-q-workflow-hub-root> `
  -CompanyRoot <private-or-company-q-workflow-hub-root> `
  -OutputDirectory <review-report-directory>
```

The gate runs public/private scans, `git diff --check`, PowerShell parsing,
Python compile checks, the parity audit, and a classification draft. The parity audit reads `docs/governance/VARIANT_MAP.json` as the machine-readable source for allowed variant differences, sync-required prefixes, and counterpart-review rules.

For each reported difference that is not resolved by `VARIANT_MAP.json`, classify it as:

- synchronized now;
- intentionally variant-specific and recorded in the variant delta;
- public-safe generic work that needs a pending TODO/work item;
- private content that must never be copied to public.

For nontrivial sync rounds, run expert review before push or shared release:
`Workflow Distiller` owns policy/classification and durable notes, `Code
Auditor` owns script/path/diff safety, and `Usability Validator` owns setup and
package usability. Add `Pagewright` for HTML/setup pages, `Visual Arbiter` for
diagram/PPT surfaces, and `Doc Architect` for shared docs.

Do not call a shared release ready while a generic onboarding page, quick
command, validation gate, setup helper, or reusable skill exists on only one
side without either syncing it or recording the concrete pending parity item.
