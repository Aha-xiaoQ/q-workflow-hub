---
name: q-research-discovery
description: Use when planning or running targeted research discovery for current or niche information, public examples, useful skills, source strategies, stuck-work directions, or durable research lessons.
metadata:
  short-description: Research planning and source discovery
---

# Q Research Discovery

Use this skill when research is part of the work, not a side chat. It helps the
agent choose source roles, search deliberately, evaluate fit, and record lessons
that should make the next research round faster.

## Core Workflow

Route by intent:

| User or task needs | Use |
|:---|:---|
| Focused answer, source, or example | `workflows/quick-find.md` |
| Public skills, workflows, or prior art | `workflows/skill-discovery.md` |
| Broad or ambiguous research topic | `workflows/deep-research-plan.md` |
| Validate whether a skill or workflow works | `workflows/experiment-validation.md` |
| Work is stuck and needs new directions | `workflows/stuck-lateral.md` |
| Choose starting sites or maintain a reusable research source library | `references/recommended-source-library.md` |
| Durable source or query lesson | `references/search-log-template.md` |
| Reusable source registry entry | `references/source-registry-template.md` |

## Operating Rules

1. Define the research objective before searching.
2. Start with the strongest relevant primary source. Add source roles only
   for unresolved, conflicting or consequential claims; counts are not quotas.
3. Keep source use license-aware. Learn from ideas and patterns; do not copy
   code, prompts, schemas, text, or assets without explicit compatible license
   and attribution.
4. Label warnings by severity: blocking, degraded, informational, or future
   risk. Do not treat a nonblocking warning as a failed validation.
5. For an authorized change, test a realistic scenario and its relevant
   contrast. Use numeric scoring only for an actual comparative evaluation.
6. Record reusable source, query, and validation lessons in the user's durable
   state or the project handoff file.
7. Use the recommended source library as a starting map, not a closed world.
   Search beyond it for current, niche, or task-specific sources, then update
   the source registry when a source repeatedly helps or disappoints.

## Skill-Creation Preflight Mode

When `q-skill-creation` calls this skill for a Discovery And Approval Gate,
choose `quick-find.md` or `skill-discovery.md` unless the lane is `release` or
Xiao Q explicitly asks for deep research.

Compact mode output:

- research objective and freshness need;
- the sources needed to resolve the question, prioritizing official evidence;
- key findings that affect the skill design;
- warnings by severity;
- what was intentionally not searched and why;
- next action for the skill plan.

Do not start source-registry maintenance, deep research, another skill-learning
loop, or a `q-skill-creation` update from inside this preflight pass. Record
separate reusable research lessons as a follow-up unless Xiao Q approves scope
expansion.

## Outputs

For small tasks, a concise answer with cited or named sources is enough.

Persist a compact decision/source note only when needed for task recovery or
reusable learning. Use the existing work item; project membership alone does
not require a separate research log, score or source-registry update.

## References

- `references/search-log-template.md`: reusable research log format.
- `references/recommended-source-library.md`: starter source families,
  star/deprioritize rules, and embedded-engineering research anchors.
- `references/source-evaluation.md`: source, skill, and license fit checklist.
- `references/source-registry-template.md`: durable source memory format.
- `references/validation-rubric.md`: experiment scoring for skill and workflow
  validation.
