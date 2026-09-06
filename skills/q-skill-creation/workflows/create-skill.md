# Create Skill

Use when creating a new skill from an idea, repeated task, project workflow, or external reference. Before creating a new top-level skill proactively, read `references/skill-creation-trigger.md` and confirm that updating an existing skill, reference, workflow, project memory, profile, script, report, or TODO is not the better durable layer.

## Discovery And Approval Gate

Before creating or scaffolding files for a new top-level skill, complete this gate unless an explicit waiver below applies.

### Prompt Chain Budget

Choose the lightest lane before loading downstream skills or experts:

- `quick`: patch-level typo, link, deterministic metadata repair, or explicitly
  local throwaway helper. Do targeted readback and validation; skip prior-art
  learning, external research, and formal expert review unless the user asks or
  risk appears.
- `standard`: default for a new reusable candidate/pilot skill. Run compact
  prior-art learning, targeted research only when the trigger requires current
  or external evidence, one bounded expert pre-review, then stop and ask for
  user approval.
- `release`: public/team/stable/high-risk skill work. Use fuller learning,
  research, real expert/subagent review, compatibility checks, and release
  readiness evidence.

Chain stop rules:

- A preflight call to `q-skill-pattern-learning` must return a compact
  prior-art brief, not start its full learning program unless the lane is
  `release` or the user explicitly asks for deep study.
- A preflight call to `q-research-discovery` must return a compact research
  brief, not start deep research or source-registry maintenance unless the lane
  is `release` or the evidence gap requires it.
- Downstream skills used during this gate must not call `q-skill-creation` to
  create or update another skill in the same chain. Record a follow-up instead,
  unless the user explicitly approves a new work item.
- Stop after the plan plus expert findings are ready. Do not scaffold files,
  expand the research chain, or spawn additional experts before user approval.

1. **Confirm creation trigger.** Use `references/skill-creation-trigger.md` to decide whether to create a new skill, update an existing skill, or use a smaller durable layer. Default to proposing/evaluating rather than silently creating unless the user already authorized skill creation or sedimentation. Record why a new top-level skill is justified.
2. **Understand usage.** Collect 2-3 concrete example prompts, target users, success criteria, and what is out of scope.
3. **Learn from prior art.** Use `q-skill-pattern-learning` for internal/external skill and workflow pattern learning before designing the new skill. Extract mechanisms, rejected patterns, and license posture; do not copy third-party text, prompts, code, schemas, or assets without explicit compatibility and attribution.
4. **Research source roles.** Use `q-research-discovery` / Source Scout when the skill touches official platform behavior, current or niche ecosystems, public examples, external tools, APIs, install paths, or uncertain best practices. Record source roles, key findings, and whether research was skipped because the user declined, networking was unavailable, or the task was explicitly offline.
5. **Draft the plan.** Before file creation, write a compact plan covering goal, trigger, scope, candidate name, ownership class, structure, validation, source/runtime/bootstrap sync, public/company boundary if relevant, compatibility, and residual risks. A Xiao Q/q-workflow-owned reusable skill must use the `q-<domain>-<job>` family; external mirrors and project-local skills require an explicit ownership exception instead of silently dropping the prefix.
6. **Run expert pre-review.** Use Workflow Distiller by default for lifecycle, routing, taxonomy, compatibility, or durable-rule changes. Add Source Scout for research-heavy skills, Code Auditor for scripts or validation tools, and the relevant domain expert for PPT, HTML, diagram, hardware, PDF, audio/video, or other specialized skills.
7. **Ask for user approval.** Present the plan plus accepted/deferred expert findings to the user and wait for explicit approval before creating or scaffolding files.
8. **Proceed only after approval.** After approval, implement the smallest viable skill structure, validate, run post-review when high-impact, and record handoff evidence.

Waivers are narrow:

- Patch-level typo, obvious link, or deterministic metadata repairs may skip this gate only when skill behavior and routing are unchanged.
- Tiny local-only helpers may skip research only when no new reusable skill behavior is created; record scope and skip reason.
- Immediate implementation may skip the approval wait only when the user explicitly says to skip preflight/approval, or when the user has already approved a concrete plan in the current thread.

## Implementation Steps

1. **Choose the shape and pass the name gate.** Decide the skill name, trigger description, workflows, references, scripts, assets, and whether the skill is q-owned, external, or project-local. Before scaffolding a q-owned skill, run `python scripts/skill_naming_audit.py --candidate-name <name> --candidate-kind q-owned`; a missing `q-` prefix blocks creation. External mirrors and project-local skills must use their matching candidate kind and record why the q-owned rule does not apply.
2. **Choose initial lifecycle state.** Read `references/skill-lifecycle-standard.md` and record whether the skill starts as `candidate`, `pilot`, or `stable`. New skills default to `candidate` or `pilot`. Do not mark a new skill `stable` unless the full Stable Release Bar is satisfied with evidence, including source/runtime sync, compatibility notes, realistic scenarios, and required expert review.
3. **Frame option-style choices.** When the skill could reasonably go in multiple directions, turn requirements into 2-3 explicit options before implementing. Each option should state the use case, tradeoff, likely files, validation path, and recommended default. Do not ask questions discoverable from files.
4. **Check third-party material.** If references are involved, use `references/license-check.md` before copying or adapting material. Prefer learning mechanisms over copying text, prompts, code, schemas, or assets.
5. **Implement the skill structure.** Keep `SKILL.md` short and route detailed procedures into `workflows/` or `references/`. Use `references/skill-taxonomy-schema.md` for portfolio metadata rather than adding unsupported frontmatter fields.
6. **Add UI metadata.** Create `agents/openai.yaml` with display name, short description, and default prompt using the current interface metadata convention.
7. **Define compatibility.** Record source of truth, runtime path, public/company counterpart if any, expected old aliases, and whether future renames need a migration note.
8. **Validate.** Re-run the candidate-name gate, then run metadata validation, encoding guard when Chinese or localized text is touched, public/private scan where relevant, source/runtime/public/company sync check or explicit deferred reason, and at least one realistic usage scenario proving the Discovery And Approval Gate fires before scaffolding. Audit the target published skill root and block any non-`q-` compatibility folder when the canonical `q-` counterpart exists. If the new skill is intended for a colleague-facing stable bundle, run the Pre/Post Expert Review Gate and Usability Validator pass before calling it ready.
9. **Record handoff.** Update changelog, work item, portfolio inventory or audit report with lifecycle state, decisions, validation, residual risks, and next actions.

## Ready Checklist

- Skill name is lowercase hyphen-case and under 64 characters.
- A q-owned reusable skill passed the executable `q-` prefix gate; any external
  or project-local exception records its ownership class and reason.
- Published skill roots do not contain both `<name>` and `q-<name>` folders;
  keep old phrases as canonical text aliases or migration notes instead.
- Frontmatter has `name` and `description`.
- Creation trigger is justified using `references/skill-creation-trigger.md`.
- Prior-art learning was run with `q-skill-pattern-learning`, or an explicit waiver/skip reason is recorded.
- Research was run with `q-research-discovery` / Source Scout when official docs, current facts, public examples, tools, APIs, install paths, or uncertain best practices are involved.
- Plan, expert pre-review, and user approval happened before scaffolding, or the current-thread waiver is explicit.
- Description includes clear trigger language.
- `SKILL.md` is concise and does not duplicate long reference content.
- Lifecycle state and compatibility posture are recorded using `references/skill-lifecycle-standard.md`.
- Taxonomy/category/status/risk/output metadata is recorded in an inventory, report, or supported metadata layer.
- Third-party references and license posture are recorded.
- Validation results are written to durable state.
- The first stable release path satisfies the full Stable Release Bar, has pre-review/post-review evidence for high-impact decisions, includes at least one realistic scenario, and records rollback, deprecation, or compatibility notes when applicable.

## Option Pattern

Use this pattern when discussing skill direction with the user:

```text
Option A - <recommended direction>
Best for: <primary user/task>
Includes: <SKILL.md/workflows/references/scripts/assets>
Tradeoff: <what it will not optimize for>
Validation: <how we will know it works>

Option B - <alternative>
...
```

Prefer options that change real behavior, not cosmetic naming choices.
