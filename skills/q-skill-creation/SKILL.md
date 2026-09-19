---
name: q-skill-creation
description: Create, update, review, stabilize, release, or rename q-workflow-compatible skills with clear names, reliable requirements gathering, option-style decisions, lifecycle gates, compatibility notes, validation, and durable handoff notes. Use when the user wants to make a new skill, improve an existing skill, define skill standards, review a skill, prepare a stable colleague-facing release, rename unclear skills, or turn repeated work into a reusable skill.
metadata:
  short-description: Create and maintain q-workflow skills
---

# Q Skill Creation

Create and maintain reusable skills with clear routing, validated behavior and
recoverable source. Prefer updating the owning skill over adding another.

## Route By Intent

| Intent | Read next |
|---|---|
| Update an existing skill | `workflows/update-skill.md`; choose editorial, behavior or release lane first |
| Create a skill | `workflows/create-skill.md` before scaffolding; follow its discovery/approval gate |
| Rename/migrate | `workflows/skill-naming-migration.md` |
| Review | `workflows/review-skill.md` |
| Source/runtime drift | `references/source-runtime-freshness.md` |
| Stable release, lifecycle/compatibility or legacy uplift | `references/skill-lifecycle-standard.md` |
| Define/change a behavioral gate | `references/rule-quality.md` and `references/rule-hardness-ladder.md` |
| Merge/split or justify a new skill | `references/skill-composition-boundary.md` or `references/skill-creation-trigger.md` |
| Portfolio metadata | `references/skill-taxonomy-schema.md` |
| Full portfolio/naming audit | `scripts/skill_portfolio_audit.py` or `scripts/skill_naming_audit.py`, then applicable review/naming reference |
| Workflow stability evaluation | `references/workflow-evaluation.md` |
| Capability/plugin conflicts | `references/capability-review.md` |
| Borrow external material | `references/license-check.md` before reuse |
| General quality/naming | `references/quality-bar.md` or `references/naming-conventions.md` |

Select only the row required by the decision; do not traverse all linked
references. Read selected instructions fully and reuse them while unchanged.
An editorial patch does not activate every lifecycle or portfolio procedure.

## Common Boundaries

- Preserve user intent and existing authorization. A checklist is not a reason
  to ask again; clarify only consequential missing choices or expanded scope.
  Proposal-only requests do not authorize implementation.
- Keep entry files as concise routers. Put detailed procedures in workflows
  and specialist standards in references. Do not solve instruction bloat by
  moving it to a reference that every task must still read.
- Before editing/syncing multi-surface skills, compare touched files and known
  mirrors, classify drift and choose a validated baseline. Preserve unrelated
  work and intentional variants. Runtime is an installed copy, not sole source.
- Behavior rules need a trigger, owner, expected action, strength and validation
  scenario. High-impact routing, lifecycle, permission or gate changes retain
  the lifecycle standard's pre/post independent review. Editorial relocation
  is behavioral when it changes activation or required evidence.
- Source/runtime/public/company checks cover affected owners and consumers.
  Update applicable surfaces or record the reason for exclusion. Do not run a
  whole-hub inventory to correct a link.
- Keep reusable mechanisms public-safe; project facts stay in project state,
  personal preferences in personal state. Third-party text/code/assets require
  compatible licensing and attribution.
- Validate the actual change before readiness claims. Do not promote to stable
  from metadata checks alone. Model names do not justify automatic rewrites.

## Deliver Only What Changed

Preserve existing layout; add workflows/references/assets only when the task
needs them. Update `agents/openai.yaml` when triggers/default prompts change.
Record compatibility, review dispositions, validation and mirror status once
in the existing work item or changelog, linking raw evidence.

For a context refactor, compare entry size and actual route loading; label
bytes/lines as size measurements, not measured token savings. Check a routine
scenario and a higher-risk scenario so the lighter path cannot bypass a gate.
