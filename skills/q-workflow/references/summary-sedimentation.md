# Summary And Sedimentation

Use when Xiao Q says `总结/沉淀`, `总结`, `沉淀`, or when a major work node has
closed and the agent should consolidate without waiting for another reminder.

## Purpose

Turn an execution loop into reusable learning. The output should not be only a
chat recap; it should help the next agent avoid the same misses, validate the
current thinking, and improve the workflow where evidence supports it.

## Trigger

- Exact shortcut: `总结/沉淀`, `总结`, `沉淀`, `consolidate`, or `lessons learned`.
- Major node: a user-confirmed result, repeated execute/feedback/repair rounds,
  a new validation method, a workflow miss, or a reusable skill/framework change.
- Agent self-check: before closing a large node, ask whether the work produced
  a reusable lesson, an untested assumption, a recurring failure mode, or a
  better validation gate.
- Context-governor node: when the loop is closing under `watch`, `throttle`, or `critical` pressure, write a compact task packet before the next broad segment so the lesson is recoverable without reloading the chat.

## Workflow

1. **Scope the loop.** Identify the current task, artifacts, user feedback,
   fixes, validations, and remaining risks.
2. **Extract lessons.** Separate project facts, reusable workflow behavior,
   personal collaboration preferences, and public-safe generic patterns.
3. **Research deliberately.** When the lesson is nontrivial, use
   `q-research-discovery` to check primary docs, adjacent-domain practice,
   public examples, counterexamples, and local skills. Learn patterns only;
   do not copy third-party text, code, prompts, or assets without license
   clearance.
4. **Validate the idea.** Prefer a realistic regression or replay from the
   current work. Define observable evidence: generated artifact, script output,
   diff, exported PNG, audit JSON, citation, or scenario score.
5. **Improve the right layer.** Put project facts in project state, reusable
   behavior in skills/references/scripts, personal preference in
   `q-assistant-profile` or personal hub state, and public-safe generic rules
   in the public mirror only after sanitization.
6. **Run a related-surface audit.** Check source skill, installed runtime skill,
   company starter, public mirror, adjacent skills, validation scripts, project
   handoff notes, and active-state files. Update every applicable surface or
   record why it was skipped.
7. **Write the summary.** Include what changed, what was learned, which claims
   were validated, what remains uncertain, and what the next agent should do
   differently.

## Output Shape

For a normal consolidation pass, write or update a durable note with:

```text
Objective:
Execution loop:
User feedback:
Root causes:
Fixes:
Research evidence:
Validation evidence:
Workflow/skill changes:
Residual risks:
Next trigger:
```

For a lightweight node, a short final-answer summary is enough if no reusable
lesson or workflow change exists. For a major node, durable file updates are
required before the final answer.

## Quality Gate

The consolidation is incomplete if:

- it only describes what happened and does not identify root causes;
- it repeats the user's feedback without turning it into a checkable rule;
- it cites research but does not connect it to local validation;
- it updates a runtime skill but not its source, or vice versa;
- it changes a skill without replaying at least one realistic scenario;
- it records project-specific facts in a reusable public skill;
- it claims the lesson is absorbed but leaves no durable state, script, or
  reference update for future sessions.
