# Skill Composition Boundary Standard

Use this reference when deciding whether two skills should stay separate,
compose in a pipeline, merge into one skill, or split into smaller skills.

## Principle

Prefer high-cohesion skills with clear output contracts and low coupling
between unrelated concerns. A dependency is not a merge signal. Frequent
sequence usually means the skills need a router, quality gate, or handoff
contract, not one larger always-loaded skill.

The default decision is:

1. keep separate when each skill has an independent user intent or output;
2. compose when one skill naturally calls another as a gate or downstream step;
3. merge only when one side has no standalone trigger or contract;
4. split when one skill contains multiple unrelated trigger families, risks, or
   output contracts.

## Keep Separate And Compose

Keep skills separate, then document the dependency, when any of these are true:

- each skill can be invoked directly by a user;
- the downstream skill validates or critiques the upstream output;
- independence improves review quality, safety, or trust;
- the skills have different risk labels, tools, permissions, or evidence;
- one skill is a generic base and the other is a company, public, project, or
  template variant;
- the downstream skill is reusable by several upstream workflows.

Typical dependency modes:

- `pipeline`: upstream creates state, downstream continues work;
- `review_gate`: downstream independently validates quality before handoff;
- `add_on`: variant or style pack layers domain rules on a generic workflow;
- `tool_helper`: skill wraps a specialized tool or script used by others;
- `handoff`: one skill prepares an artifact for a different owner or medium.

Example: PPT generation and PPT visual review should stay separate. Generation
owns story, template, and slide creation. Visual review owns independent layout,
readability, clipping, overlap, and export evidence. A handoff deck should
compose them through a review gate.

## Merge

Merge or absorb a skill into another skill when most of these are true:

- it has no realistic direct user trigger;
- it has no independent output or validation evidence;
- it is only an implementation detail of one parent skill;
- it is always loaded with the parent and mostly duplicates parent context;
- two active skills compete for the same trigger, owner, and output contract;
- keeping it separate causes routing ambiguity without adding review
  independence or reuse.

Prefer turning the smaller item into a `reference/`, `workflow/`, or checklist
inside the owning skill before creating or keeping a top-level skill.

## Split

Split a skill when any of these create real friction:

- unrelated trigger families share one long `SKILL.md`;
- common tasks load rare, heavy, or specialized guidance;
- parts have different risk labels or permission posture;
- parts produce different artifacts and require different validators;
- a review, audit, tool wrapper, or intake path is reusable outside the parent;
- company/private rules are mixed with public-safe generic rules;
- project-local facts are embedded in reusable skill behavior.

Split to the smallest useful unit. If a branch is only a rare checklist,
extract a reference file before creating a new top-level skill.

## Decision Checklist

Before changing skill boundaries, record:

- user intent: what exact prompt should trigger each unit;
- output contract: what artifact, report, or final answer each unit owns;
- standalone value: whether the unit is useful without the other;
- dependency mode: pipeline, review gate, add-on, tool helper, handoff, or none;
- context cost: what the first-read path loads and what stays on demand;
- risk and permissions: whether one branch needs stricter handling;
- source boundary: public, company, project, personal, runtime, or external;
- validation: at least one scenario proving the boundary works.

## Anti-Patterns

- Merging a creator with its reviewer just because they run sequentially.
- Creating a top-level skill for every checklist or edge case.
- Leaving duplicate active skills with the same trigger and output contract.
- Hiding project facts inside reusable public or company skills.
- Moving long reports into `SKILL.md` instead of extracting durable rules.
- Treating a dependency as ownership; the upstream skill may call the
  downstream skill without owning its standards.
