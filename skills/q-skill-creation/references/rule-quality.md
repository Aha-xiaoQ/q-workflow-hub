# Rule Quality And Loading Tiers

Use this reference when writing or revising workflow, profile, or skill rules.
The goal is stable behavior without turning the assistant into a rigid script
or loading too much context for every task.

## Rule Record Shape

Prefer this shape for nontrivial behavior rules:

- `When`: the concrete trigger or situation.
- `Goal`: the user or workflow outcome the rule protects.
- `Strength`: `must`, `should`, `prefer`, `avoid`, or `must not`.
- `Hardness`: `principle`, `preference`, `strong default`, `procedure`,
  `hard gate`, or `executable gate`; use `rule-hardness-ladder.md` when the
  rule can affect final handoff or repeated failure prevention.
- `Layer`: always-on profile, router, task workflow, on-demand reference, or
  regression example.
- `Tier`: `Micro`, `Quick`, `Project`, `Deep`, or `Full` when the rule affects
  context loading.
- `Risk`: `allow`, `ask`, or `deny` when the rule affects file edits, commits,
  pushes, public sharing, credentials, or destructive actions.
- `Reference`: the on-demand file to read when detailed procedure is needed.
- `Do`: one to three natural actions.
- `Avoid`: the overcorrection or failure mode to prevent.
- `Example`: a short good or bad example when wording matters.
- `Validation`: how to notice whether the rule fired correctly.

Short rules can be prose, but they should still imply the same fields.

## Strength Levels

- `must`: Required for safety, privacy, data integrity, destructive actions,
  commits/pushes when explicitly requested, or recovery correctness. Use
  sparingly.
- `should`: Strong default behavior with room for judgment. Use for stable
  collaboration habits, project hygiene, and normal validation steps.
- `prefer`: Optimization or taste. Missing it should not make the task wrong.
- `avoid`: Known degradation pattern. State the safer substitute when possible.
- `must not`: Hard prohibition for unsafe, destructive, secret-leaking, or
  license-violating behavior.

Do not use `must` to enforce tone, catchphrases, formatting preferences, or
low-risk habits. Those usually belong under `should` or `prefer` with an
anti-pattern.
## Hardness Levels

Strength says how strongly the assistant should obey a rule. Hardness says what
happens when the rule is missed.

- `principle`: background rationale; never blocks handoff by itself.
- `preference`: style or comfort optimization; do not convert it into a hidden
  requirement.
- `strong default`: normal path for reliable work; may be skipped with a short
  reason, risk, and compensating check.
- `procedure`: required sequence for a named workflow; skipped steps need a
  recorded reason.
- `hard gate`: blocks final handoff, release, publication, public/private
  boundary changes, or generated artifact delivery until fixed or waived.
- `executable gate`: a hard gate with a script, build, visual review, scenario
  replay, freshness check, or other observable validator.

Use `references/rule-hardness-ladder.md` for promotion criteria and the hard
rule record shape. A rule is not ready for stable use if it says `must` but does
not explain the blocked outcome, check method, repair path, and scope.

## Loading Layers

- Always-on profile: very small set of identity, collaboration style,
  recovery, privacy, and continuity rules that should influence most sessions.
- Router: intent detection and skill selection. It should decide what to load,
  not contain detailed task procedures.
- Task workflow: concrete steps for a specific domain or project type.
- On-demand reference: detailed checklists, examples, templates, scoring
  rubrics, or rare edge cases loaded only when relevant.
- Regression example: saved before/after cases used to audit or improve rules,
  not loaded during ordinary work.

If a rule grows longer than a few lines, move the detail into a reference file
and keep only the trigger and pointer in `SKILL.md`.

## Context Tiers

- `Micro`: fixed commands or stable answers that should avoid tool reads.
- `Quick`: routing state, one small state file, or one targeted status check.
- `Project`: normal project or skill work with targeted state and source files.
- `Deep`: dirty, stale, contradictory, public, credential, destructive, or
  cross-profile situations.
- `Full`: whole long-file reads, broad audits, or validation that requires full
  context; use only after a reason is clear.

## Risk Labels

- `allow`: local, low-risk, recoverable reads or writes needed for the current
  task.
- `ask`: pushes, publishing, public/GitHub sync, destructive cleanup,
  credential handling, global configuration, or unclear blast-radius actions.
- `deny`: storing secrets, copying unclear-license material, moving private
  company data into public artifacts, or bypassing security controls.

## Writing Guidance

- Write the behavior goal, not just a phrase to repeat.
- Include the anti-pattern so the model does not overfit the rule.
- Prefer scenario triggers over broad always-active instructions.
- Keep `Do` actions concrete enough to execute but flexible enough to sound
  natural.
- Put personal collaboration preferences in the assistant profile, reusable
  workflow behavior in a workflow skill, and project facts in project memory.
- When a native agent capability overlaps a local rule, prefer demoting the
  local rule into an adapter, validation gate, regression scenario, or archived
  lesson before deleting it. Keep the rule only if it still protects a named
  failure mode that the native capability does not cover.
- Promote only stable lessons. One-off corrections can stay in a work item or
  journal until they recur.

## Review Checklist

- Does the rule say when it should fire?
- Is the strength appropriate for the risk?
- Is the loading layer small enough for future scale?
- Does it explain what not to overdo?
- Would a fresh session know how to act without reading chat history?
- Can the result be checked by a short scenario, validation command, or review
  question?
