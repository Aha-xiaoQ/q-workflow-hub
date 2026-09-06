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
- A successful path is promoted back into the skill or workflow after it is
  verified; a failed path is recorded only when it prevents repeated mistakes.
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
