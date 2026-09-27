# Skill Quality Bar

Use this as the q-workflow standard for skill readiness.

## Principles

- Reliable first: a future agent can recover from files and Git.
- Friendly: a non-expert user gets concrete next actions.
- Efficient: no unnecessary ceremony or duplicated context.
- Simple by default: prefer the already validated path before adding new
  branches, abstractions, or process machinery.
- Polished: the default user-facing path feels clean, focused, and
  confidence-building instead of sprawling.
- Validated: at least one realistic path has been tested.
- License-aware: references and copied material are handled explicitly.
- Self-improving: repeated lessons are recorded in the right durable layer.

## Required Before Ready

- Clear user intent and success criteria.
- Clear creation trigger: a new top-level skill is justified only when a smaller durable layer cannot own the behavior.
- Concise trigger description.
- Scoped workflows and references.
- Clear skill boundary: each skill has an owner, trigger family, output
  contract, dependency mode, and merge/split decision when adjacent skills are
  involved.
- Clear default path, with advanced or experimental branches kept out of the
  first-read experience.
- Promote a verified reusable mechanism into its owner only within authorized
  adaptation. Otherwise the findings may remain in the existing report or work
  item; a successful task does not automatically authorize a skill update.
- Important skill changes have a lightweight usability check, such as a small
  scenario run or a bounded read-only sub-agent review, before they are treated
  as generally reliable.
- Option-style decisions for high-impact tradeoffs.
- Public-safe scan when publishing.
- Changelog and work-item updates.
- Clear ownership for new lessons: reusable skill, project state, personal
  profile, or active work item.

- Portfolio-wide warnings are not automatic rewrite commands. Refactor only
  when the warning maps to a real trigger conflict, first-read context cost,
  missing output/validation contract, stale mirror, or user-facing confusion.

## Model-Portable Authoring

Apply when creating reusable behavior, changing it, or auditing its routing.
Editorial fixes retain the update workflow's smaller lane. Use the existing
work item and fixtures; this is not a new form, extra approval or model-call gate.

- **Discovery:** put the concrete task and main trigger first in a short
  description. Move exhaustive aliases and capability lists into the body.
  Add an exclusion only for a plausible adjacent misroute. There is no universal
  character limit or reason to remove a safety boundary to meet a size target.
- **Execution:** state required inputs, the default action and observable done
  condition. Write conditional branches next to their triggers. A smaller model
  should not need to infer exceptions from a distant section or chat history.
  Use a short example or ordered procedure when it prevents a known error;
  keep open-ended choices flexible and rare modes behind explicit pointers.
- **Authority:** distinguish report-only, authorized local work and external
  actions. Existing scope-specific authorization remains valid unless revoked
  or exceeded. Ask only for missing consequential input/authority. An audit is
  not permission to edit; completing local work is not permission to publish.
- **Failure:** name the next action for relevant missing inputs, tools or stale
  authority. Do independent useful work where possible. If the needed record,
  capability or permission cannot be verified, stop that dependent action and
  report the gap; never invent a pass or bypass a protected operation.
- **Preservation:** for changed existing behavior, note keep/change/retire and
  the reason in the current diff or work item. Compare the owning source with
  its applicable mirrors before writing. A shorter prompt, newer model name or
  older template is not evidence that a validated safeguard is obsolete.
- **Consumer consistency:** follow affected entry routes into references,
  templates, scripts and UI default prompts. Give each rule one owner; remove
  conflicting older instructions from active callers or record an unresolved
  gap. Do not make an archive/history example an execution source.

For a new or changed trigger, keep one intended invocation and one adjacent
negative case. For other behavior, use the changed path and a contrasting case.
Add only the risk contrasts affected: existing/missing/revoked authorization,
current/stale authority, or available/missing capability. Check the observable
action and output, not merely whether a phrase occurs in the generated skill.

When claiming compatibility with a smaller model, capture a bounded real run
using an available target model: exact prompt, model/effort, files and tools
actually used, outputs, unexpected writes, result and remaining gaps. Without
that evidence, label compatibility untested. One model/run does not establish
cross-model stability. Do not change global model settings or create a permanent
model-specific fork merely to perform the check. Reuse results until relevant
instructions, model behavior or the execution environment changes.
