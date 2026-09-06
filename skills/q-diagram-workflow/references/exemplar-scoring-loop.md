# Exemplar Scoring Loop

Use this reference when the user provides a corrected artifact, a high-score
example, or a 100-point exemplar. The exemplar may not be mathematically
perfect, but it is the current anchor for learning what the user considers good.

## Purpose

The goal is to improve both output quality and judgment quality:

- output quality: generate a better artifact;
- judgment quality: learn to score the artifact more like the user would;
- workflow quality: preserve enough intermediate evidence for the user to correct
  both the work and the scoring.

## Versioned Training Samples

For early training rounds, keep each iteration:

- source or generator script;
- rendered artifact;
- self-score by category;
- comparison against the exemplar;
- notes about what changed in the next version.

Do not collapse the process to only the final file. Intermediate versions are
useful because the user can point to exactly where the agent's visual judgment or
scoring judgment was wrong.

## Scoring Method

Use a 100-point anchor, but split the score into task-specific categories.
For technical training diagrams, useful categories are:

- operational clarity;
- visual hierarchy;
- mapping to real hardware;
- signal readability;
- layout discipline;
- style consistency.

Scores below 90 should trigger another revision when the task is a training
exercise. A score above 90 is not automatically complete: compare the remaining
gap to the exemplar and do one refinement pass if the gap is concrete.

The exemplar is a quality and judgment anchor, not a command to copy every
detail. If exemplar content conflicts with authoritative source data, preserve
source correctness, record the difference, and score the artifact on whether it
meets the task's human-facing quality goals.

## Calibration

When the user says the score is too high, too low, or based on the wrong reason:

1. Record the user's scoring correction.
2. Update the rubric or category weights.
3. Re-score the previous version if useful.
4. Apply the revised judgment to the next version.

Do not assume a later iteration is better because it fixed a visible symptom.
Check whether the fix damaged a higher-level quality such as overall balance,
main-object hierarchy, or composition symmetry. Record reverse optimizations as
negative training examples.

This is how visual judgment improves over time. The agent should not treat
subjective-looking feedback as vague; it should translate the feedback into
observable checks such as focus, spacing, alignment, font consistency, arrow
proportion, color semantics, and whether the user can act from the artifact.

For visual artifacts, scoring itself is part of the deliverable during training
rounds. the user may correct both the artifact and the score; both corrections
should feed the next skill update.

## Consolidation Pass

After a major quality jump or after the user says a version is satisfactory, do a
final consolidation pass before closing the loop:

1. Summarize the version history and identify which changes were local fixes,
   which were scoring corrections, and which became reusable methods.
2. Check that each reusable lesson landed in the correct durable layer:
   diagram skill, generic skill workflow, assistant profile, or project state.
3. Check that the scoring method itself improved, not only the artifact.
4. Look for transferable methods that solve more than one issue, such as layer
   toggling as both diagnosis and repair, or whole-family style checks after a
   single shape was corrected.
5. Record remaining uncertainty and what needs the user calibration.

The consolidation pass is part of the training deliverable. It prevents useful
feedback from staying only in chat or in a single project artifact.
