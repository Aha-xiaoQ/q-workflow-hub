# Create Skill

Create under the user's existing request; proposal-only work stops at a proposal.
Prefer extending the owning skill or a smaller durable layer when it already
covers the task. Use `../references/skill-creation-trigger.md` only when that
ownership decision is unclear.

## Default candidate path

1. Identify concrete trigger, inputs, expected result, owner/source and one
   adjacent request it must not capture. Infer routine reversible choices.
2. Reuse a relevant local example when useful. Invoke q-skill-pattern-learning
   only for requested comparative study or an unfamiliar mechanism; no mandatory
   prior-art round or skip waiver. Research current/niche/uncertain facts when
   they affect implementation. Read the license reference before copying external
   text/code/assets; learning a mechanism is distinct from copying it.
3. Sketch the smallest structure and validation in the existing work item.
   A q-owned reusable name passes `scripts/skill_naming_audit.py --candidate-name
   <name> --candidate-kind q-owned` before scaffolding; external/project-local
   names use their real ownership class. Avoid duplicate active aliases.
4. Write a concise entry: task/trigger, default action, inputs, success and
   failure behavior. Add a workflow/reference only for genuinely conditional
   detail. Add scripts only for a repeated deterministic operation. Record
   source, expected mirrors and lifecycle as candidate or pilot.
5. Keep `agents/openai.yaml` consistent with routing. Validate metadata,
   referenced resources and affected encoding, then exercise the intended
   invocation and adjacent negative case. Verify touched mirrors after install.
6. Record outcome, compatibility and remaining limits once. A new candidate is
   not stable merely because metadata passes.

## Escalation

Core routing/authority, new hard gates, lifecycle/compatibility changes, broad
propagation and retirement require independent pre/post review. Use
`../references/skill-lifecycle-standard.md` for those decisions or a
stable/public/team/portable claim; keep actual domain and cold-start evidence.
Code/validator changes need relevant tests and Code Auditor (码鉴) review.

No external research, expert ceremony or second approval is required solely
because a simple authorized instruction-only candidate is being created.
Missing consequential choices/authority still need clarification. Publication
requires its own scope-specific authority; a completed local skill is not that
authority. Do not let preflight spawn another skill-creation loop.
