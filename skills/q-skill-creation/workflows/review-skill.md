# Review Skill

Use for a quality, reliability, lifecycle, or compliance review of a skill.

## Review Areas

- **Triggering:** frontmatter description is specific enough and not too broad.
- **Structure:** `SKILL.md` is concise; workflows and references are discoverable.

- **Portfolio audit:** for broad skill-system reviews, run
  `scripts/skill_portfolio_audit.py` when available before subjective edits.
  Treat reproducible required-path/encoding/contract failures as closure issues.
  Line count, formatting variation, and keyword matches are review heuristics,
  not capability or quality measurements; require behavioral evidence before
  refactoring. Do not claim unvisited roots or untested behavior passed.
- **Reference ownership:** inline paths must be classified as local skill files,
  cross-skill dependencies, hub/repository helpers, packaged assets, or optional
  tools. A missing local required path is a blocker; an optional or cross-skill
  path is acceptable only when its owner is named and the fallback is clear.
- **Taxonomy:** category, variant, status, source of truth, runtime path, risk label, and output contract are recorded in an inventory, report, or supported metadata layer.
- **Lifecycle:** state, compatibility, deprecation, changelog/release notes, and stable-readiness evidence match `references/skill-lifecycle-standard.md`.
- **Incremental change:** patch/minor/major classification matches the actual behavior and compatibility impact.
- **Expert review timing:** high-impact lifecycle, taxonomy, routing, compatibility, release-foundation, or sedimentation-rule changes have pre-review and post-review evidence, or a recorded process defect plus post-review if pre-review was skipped.
- **Sedimentation:** lessons are absorbed only after failure mode, layer, validation, and promotion decision are clear.
- **Reliability:** fragile operations are scripted or have clear guardrails.
- **User experience:** errors and next actions are plain-language and concrete.
- **Validation:** realistic scenario tests exist or are easy to run.
- **Recovery:** decisions and next steps are recorded in project or personal state.
- **License:** third-party material is identified and compatible.

## Output

Lead with findings ordered by severity. If reviewing stable release readiness, state pass/fail for colleague-facing readiness before the summary. If there are no blocking issues, say so and list remaining validation gaps.
