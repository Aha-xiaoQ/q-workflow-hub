---
name: q-skill-pattern-learning
description: Study external or internal skills, public agent workflows, prompt packs, or reusable automation examples to extract transferable patterns and validate whether they should enter q-workflow. Use when Xiao Q wants to compare skills, learn from another skill, extract reusable mechanisms, or internalize lessons without copying third-party material.
---

# Q Skill Pattern Learning

Use this skill to turn skill study into measurable workflow improvement. The
goal is not to admire a source skill, but to define a learning framework,
research useful prior art, extract transferable mechanisms, validate them on
real work, and only then promote durable workflow changes.

## Intent Router

| User intent | Read next |
|---|---|
| Define the overall skill-learning framework | `references/design-framework.md` |
| Search for related skills or materials | Use `q-research-discovery`, then record findings against `references/design-framework.md` |
| Study one or more external skills | `workflows/study-and-internalize.md` |
| Deep-study a high-value source or design/workflow system | `workflows/deep-study-mode.md` |
| Check whether prior learning improved our work | `references/learning-rubric.md` |
| Borrow from third-party material | `references/license-boundaries.md` |
| Patch or create a q-workflow skill from lessons | Use `q-skill-creation` after this skill identifies the patch target |
| Validate a learned PPT/design lesson | Use `q-ppt-creation` and `q-ppt-visual-review` after this skill defines scenarios |

## Core Rules

- Do not start by patching q-workflow. Start with the learning question,
  Xiao Q's theme, and the failure mode the learning system should reduce.
- Distinguish source observation, adaptation, testing and stabilization in the
  evidence. A bounded study may complete them in one pass; generalized framework
  improvement needs transfer evidence across tasks.
- Separate surface features from mechanisms. Names, folder shapes, or prompt
  wording are surface; routing logic, validation contracts, artifact strategy,
  and feedback loops are mechanisms.
- Use deep-study mode for unusually valuable or subtle sources. Extract stage
  gates, source-of-truth choices, evidence surfaces, parameter boundaries, and
  review loops before deciding whether any ordinary skill patch is justified.
- Learn ideas and patterns only unless license compatibility and attribution
  explicitly allow copying. Do not copy code, prompts, schemas, text, images,
  or assets from third-party skills by default.
- Map each useful lesson to the right layer: always-on profile rule, skill
  router, workflow reference, script, project state, evaluation scenario, or
  TODO. Do not overload the highest layer with rare cases.
- Require evidence. A learning claim should include source observed, mechanism
  extracted, local adaptation, validation scenario, result, and remaining gap.
- Prefer small candidate patches plus real follow-up tests over a large
  abstract rewrite.
- Record framework assumptions, research findings, candidate mechanisms,
  validation evidence, and promotion decisions in durable files before claiming
  the workflow improved.

## Skill-Creation Preflight Mode

When `q-skill-creation` calls this skill as part of a Discovery And Approval
Gate, use compact mode instead of the full Default Learning Program unless the
lane is `release` or Xiao Q explicitly asks for deep study.

Compact mode output:

- failure mode the new skill should prevent;
- 1-3 internal or external prior-art sources/examples;
- 2-4 transferable mechanisms;
- 1-2 rejected patterns or overreach risks;
- license posture and copy/no-copy boundary;
- recommendation for create, update existing skill, or defer.

Do not call `q-skill-creation`, patch skills, start a second learning loop, or
promote durable rules from inside this preflight pass. Return the brief to the
caller; the caller owns the plan, expert review, and user approval.

## Default Learning Program

1. **Frame**: write the intended learning model, source roles, promotion bar,
   and known risks before searching.
2. **Research**: find related skills, agent workflow docs, and adjacent learning
   frameworks; record source role, license posture, and useful mechanism.
3. **Synthesize**: map findings to the user-requested target or report without
   copying third-party material. Change this learning framework only when that
   change is itself in scope.
4. **Pilot**: for a bounded lesson, exercise one different realistic scenario.
   Use multiple skill types only for generalized framework or stabilization claims.
5. **Validate**: use `references/learning-rubric.md` for comparative or promotion
   claims; a bounded study needs concise behavioral evidence and known gaps.
6. **Stabilize**: only promote rules that survive repeated real use; keep rare
   cases in references or examples.

## Learning Output

Each learning pass should produce a compact record:

- `Framework`: learning question, target failure mode, and promotion bar.
- `Sources`: source names, license posture, and whether material was only
  studied or actually copied.
- `Mechanisms`: 2-5 transferable mechanisms, each tied to a failure mode.
- `Adaptation`: target skill/workflow layer and the smallest proposed change.
- `Validation`: a targeted transfer scenario; broader cases for generalization claims.
- `Evidence`: generated artifact, review report, diff, score, or real-task
  comparison.
- `Decision`: promote, keep experimental, defer, or reject.

## Anti-Patterns

- Treating a skill as improved because its wording sounds better.
- Copying another skill's prompt text, code, or schema without license records.
- Turning every interesting idea into an always-on rule.
- Updating a skill after one successful artifact without a separate validation
  scenario.
- Calling a lesson internalized when it only fixed the current file.

## Handoff

Before closing a learning round:

- update the relevant work item or project state with the learning output;
- validate any changed skill with `quick_validate.py`;
- run at least one realistic usage scenario when the change affects behavior;
- state what is stable for normal use and what still needs more evidence.
