---
name: q-skill-creation
description: Create, update, review, stabilize, release, or rename q-workflow-compatible skills with clear names, reliable requirements gathering, option-style decisions, lifecycle gates, compatibility notes, validation, and durable handoff notes. Use when the user wants to make a new skill, improve an existing skill, define skill standards, review a skill, prepare a stable colleague-facing release, rename unclear skills, or turn repeated work into a reusable skill.
metadata:
  short-description: Create and maintain q-workflow skills
---

# Q Skill Creation

Use this skill to make skills that fit q-workflow: reliable, friendly,
recoverable, validated, and license-aware.

## Intent Routing

| User intent | Workflow |
|:---|:---|
| Create a new skill | `workflows/create-skill.md` |
| Update an existing skill | `workflows/update-skill.md` |
| Proactive maintenance after model/tool changes, repeated friction or a reusable milestone lesson | q-workflow `references/proactive-evolution.md`, then `workflows/update-skill.md` for an authorized candidate; no model-name-based rewrite |
| Rename or migrate a skill | `workflows/skill-naming-migration.md`; then update `references/naming-conventions.md` when the naming rule changed |
| Audit naming drift, rename candidates, or split/merge signals across existing skills | Run `scripts/skill_naming_audit.py`; then classify with `references/naming-conventions.md` and `references/skill-composition-boundary.md`. Rename only when the migration gate is met. |
| Review a skill for quality, reliability, or compliance | `workflows/review-skill.md` |
| Audit model constraints, plugin conflicts, or capability adaptation | `references/capability-review.md` and targeted owner files |
| Define or repair a behavioral rule / its hardness | `references/rule-quality.md` and `references/rule-hardness-ladder.md` |
| Lifecycle, compatibility, stable release, or major uplift | `references/skill-lifecycle-standard.md` |
| Source/runtime freshness or installation drift | `references/source-runtime-freshness.md` |
| New skill justification or merge/split | `references/skill-creation-trigger.md` or `references/skill-composition-boundary.md`, according to the decision |
| Portfolio type/status/category fields | `references/skill-taxonomy-schema.md` |
| General quality or naming principles | `references/quality-bar.md` or `references/naming-conventions.md`, according to the question |
| Evaluate workflow or skill stability | Read `references/workflow-evaluation.md` first |
| Audit the full skill portfolio for structure, standards, modularity, runtime/source consistency, or colleague readiness | Run `scripts/skill_portfolio_audit.py`; then use `workflows/review-skill.md`, `references/skill-taxonomy-schema.md`, and `references/skill-lifecycle-standard.md` to classify findings |
| Borrow ideas from another skill/project | Read `references/license-check.md` first |

If the user only says "make a skill", start with `workflows/create-skill.md`.

Select only applicable references, then read each selected instruction in full.
Use the current task, available capabilities, and observed failure modes to set
effort; do not impose historical model limits or a fixed workflow on every task.
Simplify a procedure only when its safety and quality outcomes remain covered.

## Non-Negotiables

- Reliability comes first: record assumptions, outputs, validation, and handoff
  state in files.
- Ask about unresolved high-impact choices only when the answer materially
  changes scope, risk, or output. Reuse explicit user decisions and sufficient
  context; do not ask again merely because a checklist contains a question.
  Follow the host's supported question format and permission rules.
- Keep `SKILL.md` concise. Put mode-specific procedures in `workflows/` and
  reusable standards in `references/`.
- Design skills as routers plus on-demand details: keep trigger/default/safety
  pointers in `SKILL.md`; move long procedures, examples, edge cases, and
  scoring rubrics to `workflows/` or `references/`.
- New top-level skill creation must follow the `workflows/create-skill.md`
  Discovery And Approval Gate before scaffolding files: prior-art learning,
  targeted research when needed, a compact plan and proportional pre-review.
  Reuse the user's creation authorization; ask only for consequential missing
  decisions or additional scope. Proposal-only requests remain proposals.
- Before proactively creating a new top-level skill, use
  `references/skill-creation-trigger.md`: prefer the smallest durable layer
  that will reliably fire, and update existing skills before adding a new one.
- Before editing or syncing multi-surface skills, use
  `references/source-runtime-freshness.md` to choose the correct baseline,
  classify canonical source/runtime/public/company/user-cache surfaces, and
  prevent stale source/runtime/hub copies or mojibake from propagating.
- Before merging or splitting skills, use
  `references/skill-composition-boundary.md`: prefer composition for pipeline
  and review-gate relationships, merge only duplicate ownership, and split when
  triggers, risks, outputs, or context cost diverge.
- For nontrivial or mature rules, record activation/risk fields (`Trigger`,
  `Tier`, `Risk`, `Reference`) and measure context cost after major splits.
- For skill portfolio standardization, use `references/skill-taxonomy-schema.md` before adding new type/category/status fields. Prefer catalog or inventory metadata over unsupported frontmatter until tooling validates the schema.
- For stable releases or legacy-skill uplift, use `references/skill-lifecycle-standard.md` before editing. Classify the change as patch/minor/major, preserve compatibility, and require evidence before marking a skill stable.
- Write behavioral rules with explicit trigger, goal, strength, loading layer,
  expected action, and anti-pattern. Avoid vague preferences that do not fire
  and rigid scripts that make the assistant mechanical.
- For rules that affect handoff, release, public/private boundary, source/runtime
  sync, generated artifact quality, or repeated user-found misses, use
  `references/rule-hardness-ladder.md` to classify the rule as a principle,
  preference, strong default, procedure, hard gate, or executable gate before
  promoting it.
- Test workflow changes with small scenarios and score them before relying on
  them for real work. Use real task feedback as later evaluation rounds.
- Capture lessons at the correct layer: reusable skill behavior in public
  skills, project facts in project state, and personal collaboration preferences
  in the user's assistant profile or personal hub.
- When a user asks to update a rule, lesson, workflow, or skill behavior, audit
  all related surfaces before closing: source skill, runtime skill, personal
  bootstrap copy, company variant, adjacent skills that share the behavior, and
  durable handoff notes. Update every applicable surface or record why a
  surface was intentionally skipped.
- Do not copy third-party code, prompts, schemas, text, or assets unless license
  compatibility and attribution are explicit.
- Treat locally installed skills as test/runtime copies. If a skill becomes
  commonly used, give it a durable source repository or record source,
  installation, license, and migration details in the user's skill inventory.
- Validate the skill before marking it ready.

## Default Deliverables

- `SKILL.md` with clear trigger description and concise routing.
- `agents/openai.yaml` with user-facing display metadata.
- `workflows/` files for multi-step procedures.
- `references/` files for policy, license, schemas, or longer guidance.
- Context-cost note when the skill is large or refactored: line count,
  estimated tokens, and which scenarios should load each reference.
- Personal work-item and project changelog updates when the skill changes.
