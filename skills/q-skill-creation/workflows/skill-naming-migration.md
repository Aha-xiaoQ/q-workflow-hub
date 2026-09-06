# Skill Naming Migration

Use when renaming, splitting, or canonicalizing an existing skill while keeping
older prompts, project notes, and runtime recovery paths understandable.

## Trigger

Run this workflow when a skill name changes, a public/private variant receives a
canonical suffix name, a legacy alias is introduced or retired, an audit reports
`naming-migration-needed`, or a name no longer reflects trigger, output, risk,
or ownership.

## Standard Flow

1. Scope the migration.
   - Name the old skill, canonical skill, public counterpart, and any
     private/company/project counterpart.
   - Record whether the old folder becomes a temporary runtime alias, a
     no-alias deletion, or a deferred migration.
   - Classify whether this is `patch`, `minor`, or `major` using
     `references/skill-lifecycle-standard.md`.

2. Confirm the canonical target.
   - Directory name, `SKILL.md name`, `agents/openai.yaml`, installer lists,
     registries, examples, and docs should agree.
   - The canonical name must follow `references/naming-conventions.md` unless a
     documented exception exists.
   - If the migration crosses public/private boundaries, classify what is
     public-safe, private-only, and variant-specific before copying text.

3. Retire or isolate the old skill name.
   - Published source, starter, and marketplace-like skill bundles should show
     only canonical skill folders by default.
   - If a runtime-only compatibility alias is required, record it as an
     exception, keep it out of published starter/source bundles, and schedule a
     concrete retirement scan.
   - Compatibility aliases must not contain active workflows, references,
     scripts, schemas, or assets. Prefer an old -> new mapping note over a
     folder alias when the goal is a clean migration.
   - Alias text must name the exact canonical skill and must not contain
     placeholders such as `$OldName` or `$NewName`.

4. Propagate references.
   - Update source collection, installed runtime, starter/bootstrap, registry,
     project-local skills, generated docs/scripts, and active router text.
   - Preserve historical changelogs, archive notes, and explicit migration
     mapping examples unless they are used as active routing instructions.
   - Scan for old names in commands, docs, templates, install scripts, tests,
     reports, and personal/project state.

5. Run sync and parity audits.
   - Run the available skill-level sync audit for changed source/runtime
     surfaces.
   - Run variant parity audit/classification when public/private starter or
     counterpart packages changed.
   - Treat scan-clean direct-copy candidates as locally copyable only after
     semantic review. Treat `sanitize-required`, `manual-rewrite`,
     `company-only`, `private-only`, and `counterpart-missing` as gated work,
     not automatic sync.

6. Validate every layer touched.
   - Run `quick_validate.py` for canonical skills in every layer touched and for
     any explicitly approved runtime-only alias stubs.
   - Run `python -m py_compile` for changed Python scripts.
   - Scan for broken placeholders, double suffixes, malformed names, empty alias
     prompts, and stale old-name references.
   - Run workflow health or hygiene checks when personal/runtime state,
     workflow rules, or public/team package readiness changed.

7. Review and score.
   - For nontrivial migrations, use Code Auditor and Workflow Distiller review,
     or record why a local pass is enough.
   - Record self-score, reviewer/expert score, accepted findings,
     rejected/deferred findings, validation evidence, and residual risks.

8. Close the loop.
   - Update durable inventory, TODO/next-action notes, active work state, and a
     final report or work-item entry.
   - Do not push, publish, or public-sync without remote freshness, public-safe
     scan, diff review, and explicit user approval.
   - Do not close the migration while published source/starter skill lists still
     expose old folder names, unless the final report names that exception.

## Required Closure Evidence

A migration is closed only when all are true:

- `naming-migration-needed: 0` for the migration scope, or out-of-scope items
  are explicitly listed.
- `counterpart-missing: 0`, or each missing counterpart has a documented
  decision.
- Published source/starter bundles contain no legacy alias folders unless a
  documented exception exists.
- Deferred old names found in the current published skill list are blockers, not
  acceptable closure evidence; either migrate them now or name them as residual
  risk.
- Placeholder and malformed-name scans are clean.
- Workflow or skill audit has no P0/P1 blockers in the migration scope.
- Public/private sync blockers are classified as synchronized, variant-specific,
  sanitize-required, manual-rewrite, private-only, or intentionally deferred.
- Final report names what was migrated, what was not, validation evidence,
  scores, and the next retirement/sync trigger.

## Anti-Patterns

- Renaming because a name feels imperfect, without user-facing misrouting or
  release-readiness evidence.
- Updating only runtime but not durable source, or only source but not runtime.
- Letting old names remain in active route examples without classification.
- Copying public/private files solely because they are scan-clean when their
  semantics differ by variant.
- Treating dirty repos, public sync, commits, and alias retirement as implicitly
  approved by the naming task.
- Leaving two full active skills as competing sources of truth.
