# Rule Hardness Ladder

Use this reference when a skill rule needs to become more precise without making
the assistant mechanical. The goal is to separate non-negotiable gates from
strong defaults and preferences.

## Ladder

1. `principle`: Explains why a behavior matters. It does not block handoff.
2. `preference`: Improves style or comfort. Missing it is not a defect.
3. `strong default`: Should run in normal cases, but may be skipped with an
   explicit reason.
4. `procedure`: A required sequence for a specific workflow. Skipping a step
   needs a recorded reason.
5. `hard gate`: Blocks final handoff, release, publication, or user-visible
   delivery until fixed or explicitly waived by the user.
6. `executable gate`: A hard gate backed by a script, visual check, scenario
   replay, build, diff, freshness check, or another observable validator.

Prefer the lowest layer that reliably prevents the failure. Promote a rule only
when the miss is repeated, high-impact, or objectively checkable.

## When To Use A Hard Gate

Use `hard gate` or `executable gate` when the rule protects:

- data loss, destructive actions, credentials, private/public boundary, license
  compliance, or unsafe hardware behavior;
- source/runtime/public/company mirror consistency for active skills;
- build/test pass requirements before code handoff;
- user-visible artifact quality that has already failed in real work, such as
  PPT overlap, clipped text, unreadable font size, wrong template, or stale
  generated output;
- repeated user corrections that expose a stable process gap;
- process, format, or recovery rules that have failed in real work and can be
  checked through a transcript tail, scenario replay, reviewer packet, visual
  review, diff, or other concrete evidence;
- release, colleague handoff, customer-facing, or public publishing readiness.

Do not use hard gates for tone, one-off wording preferences, exploratory
brainstorming, or subjective design taste unless the user explicitly makes that
criterion a release requirement.

## Hard Rule Record

Write hard rules as an observable contract:

- `Trigger`: when the rule fires.
- `Must`: the action or condition that is mandatory.
- `Blocks`: what cannot be handed off while the rule fails.
- `Check`: how to verify it, preferably by command, screenshot, diff, scenario,
  or named reviewer.
- `Repair`: the first recovery action.
- `Waiver`: who can waive it and what must be recorded.
- `Scope`: where it applies and where it must not over-apply.

## Precision Without Rigidity

- Gate handoff quality, not early exploration. Drafting can be flexible; final
  delivery must satisfy the contract.
- Bind hard rules to observable artifacts, not vague intent.
- Keep exceptions explicit. A waived hard gate must name the reason and residual
  risk. Some gates are non-waivable: credential exposure, license violations,
  private/public boundary leaks, unsafe hardware behavior, and other `deny`
  risks must be fixed or recorded as blocked instead of waived.
- When a validator exists, prefer running it over restating the rule in prose.
- If a rule cannot be checked, keep it as a strong default until a scenario,
  review question, or script makes it observable.

## Feedback Absorption

When user feedback exposes a failure:

1. Name the failure mode.
2. Decide whether it is one-off, project-local, personal, or reusable.
3. Choose the ladder level.
4. Add a positive action and an anti-pattern.
5. Add a validation cue or regression scenario.
6. Propagate to source/runtime/public/company surfaces when applicable.

Absorption is incomplete if the lesson stays only in chat, a report, or a
single generated artifact.
