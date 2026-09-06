# Workflow Identity And Skill Fit

Use this reference when deciding what makes q-workflow distinctive, whether a
new skill belongs in the system, or how to avoid turning the workflow into a
broad integration pack.

Trigger aliases: `workflow-identity`, `skill-fit`, `skill portfolio`,
`workflow distinctiveness`.

## Positioning

q-workflow is not a collection of skills. It is an evidence-first engineering
operating system for terminal-capable agents:

- small entry points;
- durable recovery;
- skill routing by ownership;
- observable validation;
- artifact-backed handoff;
- self-learning and pruning.

Skills provide capability. q-workflow makes those capabilities safer, more
recoverable, easier to combine, and easier to improve after real work.

## How Workflow Makes Skills Better

Every maintained skill should receive at least one concrete workflow amplifier:

| Amplifier | What q-workflow adds | Evidence |
|---|---|---|
| Recovery | The skill can be resumed from state files, project facts, and artifact paths instead of chat memory. | `ACTIVE_WORK.md`, work items, project state |
| Routing | The right skill loads at the right time, with sidecars capped. | `SKILL.md`, command aliases, orchestration notes |
| Authority | The skill knows which file is truth, mirror, evidence, or generated output. | authority maps, source/runtime/bootstrap notes |
| Validation | The skill leaves a check, rendered artifact, diff, trace, or score. | reports, screenshots, validation commands |
| Sedimentation | Real misses become durable rules, regression scenarios, or retirement conditions. | summaries, skill updates, TODOs |

If a skill does not gain one of these amplifiers, it is probably just installed
beside q-workflow rather than integrated into it.

## Skill Portfolio Tiers

Use four tiers:

| Tier | Meaning | Promotion bar |
|---|---|---|
| Core | Required for workflow identity and recovery. | Always useful, low context cost, validated, and maintained. |
| Flagship | Distinctive workflows that demonstrate why q-workflow is special. | Real artifact evidence and memorable user value. |
| Lab | Promising but not yet proven or not yet portable. | Keep bounded; promote only after repeated real use. |
| Archive | Compatibility, legacy, or rarely used material. | Keep discoverable but do not load by default. |

Avoid an unclassified middle state. A skill should be Core, Flagship, Lab,
Archive, or clearly project-local.

## Current Portfolio Pattern

Core:

- `q-assistant-profile`: identity, quick pointer, and resume UX.
- `q-workflow`: route, recovery, authority, context, and handoff control.
- `q-skill-creation`: skill quality gates and update discipline.
- `q-research-discovery`: source strategy and research traceability.

Flagship:

- `q-skill-pattern-learning`: learn mechanisms from skills without copying surfaces.
- `q-ppt-visual-review`: rendered PPT evidence and regression checks.
- `q-pdf-reading`: evidence-first document extraction.
- `q-ppt-creation`: reusable presentation planning and validation.
- `q-project-storytelling`: turns engineering artifacts into reusable
  narratives without losing evidence.

Domain or project-local skills can still be valuable, but they should be
controlled by q-workflow gates rather than treated as core workflow identity.

## Promotion And Pruning

Promote only when a skill has:

1. a named failure mode or artifact-quality target;
2. a workflow amplifier;
3. a tier owner;
4. observable evidence;
5. a demotion, merge, or retirement condition.

If a skill does not meet this bar, keep it Lab, project-local, or archived.
