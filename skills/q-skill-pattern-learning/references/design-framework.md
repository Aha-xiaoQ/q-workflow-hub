# Q Skill Pattern Learning Design Framework

Use this reference before changing workflow skills based on another skill or
public example. It captures Xiao Q's intended direction for skill learning.

## Design Intent

The skill should help q-workflow learn from other skills without surface
imitation. A learning round should answer:

- What work should improve?
- Which failure mode are we reducing?
- What mechanism did the source use?
- Where should that mechanism live in q-workflow?
- What different scenario proves the mechanism generalizes?
- What evidence justifies promotion into a durable skill?

## Program Shape

1. **Framework first**: define the learning model and promotion criteria.
2. **Research second**: search related skills, official docs, public examples,
   and adjacent workflow-learning frameworks.
3. **Synthesis third**: convert source observations into candidate mechanisms.
4. **Pilot rounds fourth**: run real learning rounds on different skills.
5. **Stabilization last**: promote only repeated, validated mechanisms.

## Source Roles

- Primary skill docs: define packaging and loading mechanics.
- Public skill examples: show how real skills organize workflows, scripts, and
  references.
- Evaluation references: define scenario-based validation and scoring.
- Documentation frameworks: help separate tutorial, how-to, reference, and
  explanation layers.
- Learning-loop references: keep after-action lessons tied to expected versus
  actual outcomes and next improvements.
- Deep source references: high-value sources that reveal phase gates,
  source-of-truth choices, observability hooks, or review systems rather than
  only a reusable checklist.
- Platform capability references: official docs for native agent features,
  customization layers, tool protocols, handoffs, guardrails, tracing,
  persistence, or interoperability that may replace or shrink a local workflow
  rule.
- Exemplar skill references: 2-3 high-quality skills or official skill
  systems selected for different source roles, such as one design reference,
  one implementation example, and one boundary or evaluator example.

## Candidate Mechanism Types

- Trigger and routing patterns.
- Progressive context-loading strategy.
- Workflow phase design.
- Script versus reference boundary.
- Validation and quality gates.
- Stage gates, stop conditions, and continue conditions.
- Source-material completeness and degradation protocols.
- Source-of-truth inversion: which upstream artifact drives the final output.
- Artifact observability: debug hooks, screenshots, seek points, exports, and
  reproducible validation entry points.
- Authority maps for non-visual workflows: source files, runtime mirrors,
  generated artifacts, session logs, Git state, and validation commands must be
  classified as truth, evidence, derived state, or rebuildable views.
- Capability-native adaptation: decide whether a native platform feature should
  be used directly, wrapped with q-workflow gates, kept separate from local
  rules, or treated as a reason to retire a local rule after validation.
- Parameter exposure: which decisions become user-visible controls or
  alternative candidates.
- Parallel alternatives and explicit selection criteria.
- High-stakes review specs such as director notes, rubric dimensions, and
  platform/use-case fit.
- Durable evidence and handoff records.
- Regression scenarios from real misses.
- License and public-safety boundaries.

## Multi-Source Exemplar Learning

Use this mode when Xiao Q asks to learn from several excellent skills or when
one source is too narrow to justify a durable rule.

Select 2-3 sources with different roles:

- **Design reference:** official docs or a creator skill that explains the
  skill model, trigger surface, resource layout, and validation philosophy.
- **Implementation example:** a mature skill with real decision trees,
  fallback paths, deterministic helpers, artifact policy, and error handling.
- **Boundary/evaluator example:** a source that shows testing, forward-testing,
  review, license boundaries, or governance.

Build a mechanism matrix before patching:

| Source | Role | Mechanism | Failure mode reduced | Local layer | Evidence | Boundary |
|---|---|---|---|---|---|---|

Classify each candidate mechanism:

- **Common:** appears across at least two strong sources or aligns with an
  official platform model; safe to consider for a durable rule after local
  validation.
- **Source-specific:** useful only for a narrow provider, file type, or tool
  mode; keep as a reference or future scenario.
- **Contradictory:** sources disagree; keep both conditions visible and choose
  based on q-workflow authority, safety, observability, and context cost.
- **Unproven:** interesting but not validated locally; record as a TODO or
  experiment, not a workflow rule.

For every promoted mechanism, state:

- trigger condition;
- minimal default path;
- explicit fallback conditions;
- validation evidence;
- durable-state target;
- license/copying boundary.

## Promotion Bar

Do not promote a lesson into an always-on or high-level rule unless:

- it reduces a named failure mode;
- it maps to the correct layer;
- it passes at least one different realistic scenario;
- it has a durable evidence record;
- it does not materially increase context cost for unrelated tasks.

## Current Design Hypotheses

- The first stable version should be a router plus references, not a large
  monolithic procedure.
- The skill should call `q-research-discovery` for source search and
  `q-skill-creation` for final skill patches.
- The skill should require at least 2-3 real learning rounds before being
  treated as stable.
- Visual/design lessons need artifact-level evidence such as exported PNGs,
  contact sheets, before/after reports, or user review notes.
- A user-found visible miss is part of the learning evidence. Record the
  original validation failure, root cause, repair, and rule patch instead of
  only recording the fixed artifact.
- For visual skills, distinguish geometry correctness from visual-region
  pressure. Text that does not overlap can still fail if it crosses an implied
  layout boundary or reads as one long line against nearby components.
- When learning from visual/design skills, separate visual style from
  quality-stabilizing protocols. A useful lesson is rarely "use this look";
  it is usually a protocol that prevents drift: fact verification, asset
  completeness, design-context capture, early assumption/showcase review,
  visible alternatives instead of abstract style choice, rendered-output
  verification, and expert critique loops.
- For high-value visual/design sources, run a deep-study pass before promotion.
  A normal round may identify the anti-drift protocol; the deep pass should
  also identify stage gates, required source materials, honest degradation
  paths, observability hooks, parameter surfaces, and review dimensions.
- When a learned mechanism changes a skill, runtime synchronization is part of
  the evidence. Read back at least one changed runtime file and check for stale
  nested directories; do not rely on metadata validation alone.
- When learning from memory, workflow, sync, or runtime systems, classify
  durable truth separately from derived or rebuildable state before promoting a
  lesson. A validation report, runtime mirror, generated index, or cache can be
  useful evidence, but it should not be treated as authoritative unless the
  source-of-truth layer has also been checked.
- For non-visual workflow transfer validation, require observable probes, not
  only a written conclusion. A useful probe can be a source/runtime diff, Git
  dirty-state check, session-pointer JSON, readback of a changed runtime file,
  stale mirror scan, or validation command that exercises the route.
- When judging whether deep-study mode itself worked, separate artifact
  validation from learning validation and transfer validation. A valid skill
  patch proves only that the instructions load; a different realistic scenario
  must show whether the learned mechanism improves behavior.
- For high-impact lessons, include a double-loop check: state whether the
  lesson only changes tactics, or whether it changes an underlying assumption,
  objective, source-of-truth choice, or evaluation model.
- Before turning deep-study findings into a user-facing artifact, run a compact
  pre-mortem and convert likely failures into validation gates. For visual or
  workflow artifacts, pair rendered evidence with a representative task,
  heuristic review, or user/reviewer feedback signal.
- When learning from current agent-platform materials, separate capability
  adoption from workflow ownership. q-workflow should not duplicate native
  features that are reliable and observable, but it should preserve durable
  state, safety, authority mapping, evidence probes, and regression scenarios
  around those features.
- When learning from 2-3 excellent skills, prefer mechanisms that appear across
  sources or solve a repeated local failure mode. The expected reusable pattern
  is: clear trigger, minimal default path, explicit fallback boundary,
  validation evidence, and durable-state target.
