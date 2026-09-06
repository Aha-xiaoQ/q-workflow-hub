# Create Expert Workflow

Use this workflow when an existing expert role cannot reliably cover a recurring
or high-value task class. Creating a new expert should improve professional
coverage, not just add a memorable nickname.

## Admission Trigger

Consider a new expert only when at least one condition is true:

- A task class recurs and repeatedly falls between existing expert boundaries.
- Existing experts miss a distinct risk because their required checks do not
  include that domain.
- The work needs a stable specialist interface for parallel delegation,
  first-user testing, release guardrails, or domain review.
- Xiao Q explicitly asks for a new expert or specialist identity.

Do not create a new expert for one-off tasks, style preferences, temporary
project facts, or a scope that is only a narrower instance of an existing role.
Use a local specialist pass or project-local checklist instead.

## Standard Flow

1. Define the gap.
   - Current task class.
   - Existing experts considered.
   - Why each existing role is insufficient.
   - Evidence: repeated miss, high-risk gap, recurring task, or user request.
2. Propose the expert identity.
   - English alias: stable protocol name.
   - Chinese codename: memorable Xiao Q shorthand.
   - Short role: one sentence.
   - Anti-overlap: which existing roles it must not replace.
3. Define the role contract.
   - Use when.
   - Stable style.
   - Required inputs.
   - Output fields.
   - Must-check items.
   - Anti-pattern.
4. Define dispatch behavior.
   - Default mode: local-pass, subagent-as-tool, phase-handoff, or parallel-worker.
   - Real subagent threshold.
   - Ask-before-spawn boundaries.
   - Preferred reviewers or paired experts.
5. Add protocol and quality surfaces.
   - `references/agent-registry.md`: profile and invocation map.
   - `SKILL.md`: roster summary only if the role is stable enough for first-read routing.
   - `references/quality-gates.md`: one role-specific stability check.
   - `references/validation-scenarios.md`: at least one prompt-level scenario.
   - `agents/openai.yaml`: only when user-facing trigger scope changes.
6. Validate before promotion.
   - Run `quick_validate.py` for each changed skill copy.
   - Run or reason through at least one realistic scenario.
   - Use `packet_profile: compact` for tiny dry runs and `standard` for real admission review.
7. Set maturity.
   - `candidate`: documented but not default; use only when explicitly requested.
   - `pilot`: usable for bounded tasks with review.
   - `stable`: appears in first-read roster and auto-dispatch maps.
   - `retired`: replaced by another expert or merged back into a broader role.

## Admission Bar

A new expert can become `stable` only when:

- It has a unique recurring responsibility.
- Its output cannot be produced as reliably by an existing expert plus a small
  checklist.
- It has clear input/output fields and anti-patterns.
- It has a validation scenario that a future agent can run.
- It improves quality, speed, or trust more than the extra routing overhead.

## Expert Profile Template

```text
## <English Alias> (<Chinese Codename>)

- Maturity: candidate | pilot | stable | retired
- Role: <one sentence>
- Use when: <trigger and task class>
- Do not use when: <overlap and anti-scope>
- Stable style: <review/build/research style>
- Required inputs: <minimum context packet>
- Output: <fixed fields>
- Must check: <domain-specific checks>
- Default mode: <local-pass|subagent-as-tool|phase-handoff|parallel-worker>
- Real subagent threshold: <when independence or parallelism is worth it>
- Pair with: <optional reviewer or downstream expert>
- Anti-pattern: <failure mode>
- Validation scenario: <scenario id or prompt>
```

## Promotion Decision

Use this compact decision record in the integration note or learning log:

```text
new_expert_decision:
  proposed_role:
  gap_evidence:
  existing_roles_considered:
  maturity:
  surfaces_updated:
  validation:
  rollback_or_merge_condition:
```
