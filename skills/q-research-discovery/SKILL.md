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
2. Pick source roles intentionally: stable source, boundary source, primary
   documentation, public example, counterexample, or adjacent-domain source.
3. Keep source use license-aware. Learn from ideas and patterns; do not copy
   code, prompts, schemas, text, or assets without explicit compatible license
   and attribution.
4. Label warnings by severity: blocking, degraded, informational, or future
   risk. Do not treat a nonblocking warning as a failed validation.
5. Prefer experiment loops for skill and workflow changes: choose a realistic
   scenario, define observable success criteria, run it, score the evidence,
   improve the artifact, and rerun the relevant checks.
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
- 2-4 source roles or concrete sources, prioritizing official docs and strong
  public examples;
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

For project work, also write a short research log that captures:

- objective;
- source roles;
- queries or discovery path;
- findings;
- warnings and severity;
- validation score when the work tested a workflow or skill;
- validation result;
- next action.

## References

- `references/search-log-template.md`: reusable research log format.
- `references/recommended-source-library.md`: starter source families,
  star/deprioritize rules, and embedded-engineering research anchors.
- `references/source-evaluation.md`: source, skill, and license fit checklist.
- `references/source-registry-template.md`: durable source memory format.
- `references/validation-rubric.md`: experiment scoring for skill and workflow
  validation.
