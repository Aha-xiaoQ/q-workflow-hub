# Contributing

Before adding or updating bundled skills, follow
[Public asset promotion](docs/PUBLIC_ASSET_POLICY.md). New and changed assets
are review-required; installed locally does not mean approved for publication.

Thanks for helping improve q-workflow-hub.

## Contribution Scope

Good contributions improve the generic workflow, not a specific user's private
state. Useful areas include:

- Clearer onboarding and bootstrap instructions
- Safer initialization or update scripts
- Better project memory templates
- More reliable resume and handoff patterns
- Generic validation and scan helpers

Do not submit:

- Personal active work state
- Private project registries
- Private project files or generated artifacts
- Credentials, tokens, keys, or secrets
- Organization-specific paths, hosts, or project names

## Before Opening A Pull Request

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\scan-public.ps1
```

If you need to check extra private terms before publishing, pass them as
arguments:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\scan-public.ps1 -ForbiddenTerms "term1","term2"
```

Also verify any changed setup scripts with a clean dry run in a temporary
folder. The generated private workflow hub should not be committed to this repository.

When a change is shared with an organization/company variant, run the variant
parity audit before calling the sync complete:

```powershell
python .\scripts\audit-variant-parity.py `
  --public-root <public-starter-root> `
  --company-root <company-starter-root> `
  --output <review-report.md>
```

Classify every reported difference as synchronized, intentionally
variant-specific, public-safe pending work, or company-only/private and blocked
from public sync.


## Push Readiness Gate

Before pushing any synced public/company candidate, refresh the remote state first. Run `scripts\validate-push-readiness.ps1 -RepoRoot <repo>` when available. The gate fetches with prune, checks the upstream ahead/behind state, refuses dirty worktrees by default, and fails when the local branch is behind or diverged. If fetch is blocked, record the validation gap and do not push blindly.

## Standard Variant Sync Gate

When a change is shared with an organization/company variant, use the standard
variant-sync gate before calling the sync complete:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate-variant-sync.ps1 `
  -PublicRoot <public-starter-root> `
  -CompanyRoot <company-starter-root> `
  -OutputDirectory <review-report-directory>
```

The gate runs public/company scans, `git diff --check`, PowerShell parsing,
Python compile checks, the parity audit, and a classification draft. To run the
audit and classifier manually:

```powershell
python .\scripts\audit-variant-parity.py `
  --public-root <public-starter-root> `
  --company-root <company-starter-root> `
  --output <audit-report.md>

python .\scripts\classify-variant-parity.py <audit-report.md> `
  --output <classification-report.md>
```

Classify every reported difference as synchronized, intentionally
variant-specific, public-safe pending work, or company-only/private and blocked
from public sync.

For nontrivial sync rounds, use the expert review sequence before pushing:
`Workflow Distiller` for the classification and durable policy, `Code Auditor`
for script/path/diff safety, and `Usability Validator` when setup, onboarding,
or bundled skills changed. Add `Pagewright` for HTML/setup pages,
`Visual Arbiter` for diagram/PPT surfaces, and `Doc Architect` for shared docs.

## Third-Party Material

Before integrating ideas from another project:

- Check its license and whether it is compatible with Apache-2.0.
- Prefer reimplementing ideas and workflow patterns in our own words and code.
- If copying code, prompts, schemas, text, or assets, preserve the upstream
  copyright and license notice.
- Update `THIRD_PARTY_NOTICES.md` when a reference materially informs a feature
  or when any third-party material is included.

## Design Rules

- Keep this starter generic and public-safe.
- Keep user state in the user's private workflow hub.
- Keep project facts in project repositories.
- Prefer small, reviewable changes.
- Update `CHANGELOG.md` for user-visible behavior changes.
