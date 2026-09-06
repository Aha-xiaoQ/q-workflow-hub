# Learning Rubric

Use this rubric to judge whether studying another skill produced real workflow
improvement rather than surface imitation.

Score out of 100:

- Source fit, 10: sources address the same kind of work or failure mode.
- License hygiene, 10: source license and copying boundary are recorded.
- Mechanism extraction, 20: the report explains how the source works, not only
  what files or phrases it contains.
- Layer mapping, 15: lessons land in the right q-workflow layer without
  overloading always-on context.
- Adaptation quality, 15: local changes fit existing workflow style and reduce
  a named failure mode.
- Validation evidence, 20: at least one different real or realistic scenario
  shows the lesson generalizes.
- Restraint and maintainability, 10: the patch is compact, understandable, and
  does not create brittle scripts or broad rules.

For multi-source exemplar learning, score the "Mechanism extraction" and
"Validation evidence" categories more strictly:

- The report should compare 2-3 sources with different roles instead of listing
  disconnected observations.
- Promoted mechanisms should be classified as common, source-specific,
  contradictory, or unproven.
- At least one promoted mechanism should be validated outside the original
  source context.
- A source-specific mechanism should not become an always-on rule without a
  local repeated failure mode.

When evaluating deep-study mode, split validation evidence into:

- Artifact validation: the changed files, metadata, mirrors, and syntax checks
  pass. This is necessary but does not prove learning effectiveness.
- Learning validation: the learned mechanism improves behavior on a realistic
  scenario with observable feedback.
- Transfer validation: the mechanism works on a different source or task
  without importing the original source's surface style.

Deep-study rounds should also record whether the lesson is single-loop or
double-loop:

- Single-loop: the workflow does the same kind of work with better tactics.
- Double-loop: the workflow changes an underlying assumption, objective,
  source-of-truth choice, or evaluation model.

A deep-study score above 90 should normally include learning validation. Do not
claim broad stability without transfer validation.

For user-facing or visual outputs, learning validation should include at least
one audience-facing signal: a representative task walkthrough, an explicit
heuristic review, or user/reviewer feedback. Rendered screenshots and contact
sheets are necessary artifact evidence, but they do not by themselves prove the
workflow improved the user's outcome.

For non-visual workflow outputs such as recovery, sync, memory, or runtime
mirrors, learning validation should include observable probes: an authority map,
source/runtime comparison, Git dirty-state check, session or log replay, runtime
readback, stale mirror scan, or command output that proves the route behaves as
claimed. A prose report alone is Level 1 unless at least one probe is captured.

If a deep-study patch changes a high-value workflow, record a pre-mortem before
implementation: likely failure causes, early signals, and which gate or test is
supposed to catch each one.

Score bands:

- 90-100: stable enough to rely on for normal work.
- 80-89: useful but needs more real-task evidence.
- 70-79: promising; keep experimental and patch weak areas before relying on it.
- Below 70: not internalized; redesign the learning target or validation.

## Evidence Levels

- Level 0: opinion only.
- Level 1: source notes and proposed lesson.
- Level 2: skill/workflow patch plus metadata validation.
- Level 3: patch tested on a different realistic scenario.
- Level 4: repeated real-task success with durable reports and user feedback.

Do not call a lesson fully internalized below Level 3.
