# Naming Conventions

Use this reference when naming a new skill, reviewing whether a skill name still
matches its function, or migrating public/private skill variants.

Good names make the skill list predictable. They should tell a user the stable
object/domain and the job, while leaving detailed trigger nuance to the
frontmatter description and workflow references.

## Q Skill Name Pattern

Use this pattern for q-workflow-family skills:

```text
q-<domain-or-object>-<job>
q-<domain-or-object>-<job>-<variant>
```

Rules:

- Keep the `q-` prefix for q-workflow-family skills. It marks that the skill
  belongs to this workflow system.
- Keep `q-workflow` as the short root workflow exception.
- Put the stable domain, object, file type, or medium before the job. Examples:
  `q-pdf-reading`, `q-ppt-creation`, `q-ppt-visual-review`,
  `q-video-intake`, `q-audio-intake`.
- Prefer concrete user jobs over abstract containers. Use `q-skill-creation`,
  not a generic skill manager name; use `q-video-intake`, not
  `q-video-workflow`.
- Use 2-4 lowercase hyphenated words before any variant suffix.
- Avoid overloaded words such as `workflow`, `system`, `manager`, `helper`, or
  `tool` unless that is the thing the user directly asks for.
- Do not use `workflow` in child skill names. Reserve `q-workflow` for the root
  workflow skill; child skills should name the concrete domain and job.
- If a skill mostly studies examples and extracts reusable mechanisms, include
  the mechanism in the name, such as `q-skill-pattern-learning`.
- The `description` must still carry trigger words, scope, and boundaries; do
  not force every nuance into the name.

## Variant Naming

Use suffix variants for company/private/project variants that share a public
counterpart but carry different policy, assets, templates, data boundary, or
install behavior:

```text
q-<domain-or-object>-<job>-<variant>
```

Rules:

- Keep the public/shared skill name unsuffixed when it is public-safe and
  generic.
- Add a suffix such as `-<company>`, `-private`, `-project`, or another recorded
  variant label when the skill cannot be treated as a byte-for-byte public
  mirror.
- Keep the suffix at the end. Avoid leading company/product prefixes for
  q-workflow-family skills because they hide the public counterpart and make
  bidirectional sync depend on hand-made mappings.
- Avoid unsuffixed private variants when behavior differs from public. If a
  private repo contains a byte-for-byte public mirror, document that it is a
  mirror; otherwise use a suffix.
- Truly private-only q-workflow-family skills are allowed, but their missing
  public counterpart must be explicit in the sync audit.

## Naming Drift Review

Run `scripts/skill_naming_audit.py` when a skill name may no longer match its
actual function, after a portfolio-wide standards pass, or before a
colleague-facing release.

Classify findings before renaming:

- `P1/P2`: active route ambiguity, folder/frontmatter mismatch, public install
  mismatch, or a name that causes repeated user/agent misrouting. Fix in the
  same round or record a blocking residual risk.
- `P3/watch`: name feels narrow or generic but routing still works. Prefer a
  clearer description, trigger text, documented aliases, or a future migration
  note over an immediate rename.
- `info/keep`: external package suffix, historical note, intentional variant
  suffix, or intentional composition boundary.

Do not rename on discomfort alone. A rename needs evidence of user-facing
confusion, trigger ambiguity, output-contract drift, public/team readiness
risk, or a required folder/frontmatter/registry alignment.

Allowed resolutions:

- keep current name and strengthen description/routing;
- add a documented compatibility alias or trigger phrase;
- migrate to a canonical name through the migration gate;
- split when triggers, risks, outputs, or context cost diverge;
- merge only when two skills own the same trigger, artifact, and validation
  contract.

## Migration Gate

A skill naming migration is not complete until it has:

1. A canonical directory with matching `SKILL.md name` and `agents/openai.yaml`.
2. Published source/starter bundles expose only canonical folder names, or a
   recorded exception explains any runtime-only alias.
3. Source, runtime, starter/bootstrap, registry, router text, and generated docs
   updated.
4. Old-name reference scan classified into active blockers, historical notes,
   audit mappings, or explicitly deferred migration items.
5. Source/runtime validation and counterpart/variant audits rerun.

Runtime aliases are exceptional and temporary. They must be explicitly
recorded, excluded from published source/starter bundles by default, and retired
by a dated old-name scan.

## Legacy Examples

Use examples as patterns, not as hard-coded current tasks:

- A leading company/product prefix should usually become
  `q-<domain>-<job>-<variant>`.
- A child skill ending in `-workflow` should usually become
  `q-<domain>-<job>` unless it is the root `q-workflow` skill.
- A broad name whose function expanded should first get stronger description,
  routing, and compatibility notes; rename only if users misroute it.
- A creator skill and a reviewer skill should remain separate when their
  triggers, outputs, or validation gates differ, even if they run sequentially.

## Current Generic Decisions

- `q-workflow`: keep. It is the root workflow skill.
- `q-assistant-profile`: keep for generated personal profile and quick-recovery
  context.
- `q-skill-creation`: keep for skill creation, update, review, release, and
  rename lifecycle work. Consider a lifecycle rename only if real users misroute
  this scope.
- `q-skill-pattern-learning`: keep. It names the mechanism of studying skills
  and extracting transferable patterns.
- `q-research-discovery`: keep. It names research/source discovery clearly.
- `q-ppt-creation` and `q-ppt-visual-review`: keep separate. PPT creation and
  visual review share a domain but have different outputs and validation gates.
- `q-project-storytelling`: keep. It names project communication/story shaping
  without using a child-skill `workflow` suffix.
- Private/company variants of public skills should use the same base name plus
  a recorded suffix when their behavior, assets, or policy differs.
