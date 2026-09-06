# Source-Driven Training

Use this on-demand branch when a pixel-character learning project has repeated
unstructured self-practice, user-selected reference material, or a durable
recovery entry. It is additive: ordinary study and creation keep their normal
routes.

## 1. Recover before choosing work

Read, in order: recovery entry, active training packet, source registry/source
cards, last review token, and current artifact. The entry must name active
packet, mode/status, two visual source IDs, tutorial ID, single capability,
observation units, current stage, last decision, next allowed action, blocked
actions, and private/shipping status.

If any field is missing or contradicts another state file, return `RECOVER`:
repair state only. Do not select a topic or draw from chat history, timestamps,
or the latest file.

## 2. Register a source packet

Before drawing, require:

- two distinct visual sources (primary and cross-check);
- one primary tutorial that explains the same single capability; optional
  supplemental tutorials must declare a non-gating cross-check role;
- per-source observable native/display size, provenance/license posture,
  allowed use, forbidden use, and private/shipping status;
- one capability narrow enough to verify without evaluating a whole character.

Record `PASS_SOURCE_PACKET` only when all fields exist. Public previews remain
observable, not reusable.

## 3. Observe, then generalize cautiously

Inspect each source at its own recorded 1× observation unit. Record evidence
for the capability separately. A relation is `general` only if both visual
sources support it and the tutorial explains a compatible mechanism. A
single-source result is `style_exception` or `insufficient_evidence`.

No original drawing, tracing, palette sampling, coordinate list, or full-body
exercise is allowed here. Record `PASS_OBSERVATION` only after independent
review of source binding and evidence.

## 4. One masked unit, not an answer copy

The next exercise must retain the same two visual sources and tutorial, mask
only one named capability, and keep any reference-derived context private and
non-shippable. Do not change references mid-exercise or expand a local feature
exercise into a whole face/character. Use `semantic-feature-study.md` where a
precise feature is involved.

Before `PASS_MASK_UNIT`, re-read the registered tutorial mechanism and record
which visible decision the primary tutorial checks. The review must confirm all of the following:

- the masked region contains only the registered capability;
- both visual sources remain bound and private/non-shippable;
- the restored decision is compatible with the same frozen primary-tutorial
  mechanism;
- no coordinate, palette, trace, or answer-copy evidence entered the unit.

Record `PASS_MASK_UNIT` only after the unit's own native review.

## 5. Same-observation-unit review

Review candidate alone at its native 1× first. Then compare beside sources at
their recorded observation units; do not force unrelated sources into one
canvas or claim a screenshot unit is the author's work grid. Integer
nearest-neighbor zoom comes last and only diagnoses 1× findings.

The review record must also replay the frozen primary-tutorial mechanism: state whether
the candidate supports it, contradicts it, or is a declared style exception.
Record `PASS_SAME_UNIT_REVIEW`, or return through the explicit mapping below.

## 6. Original transfer is separate proof

After the study unit passes, hide references and change applicable identity,
structure/angle, palette, prop, and recognizable contours. Reapply the same
frozen capability and primary-tutorial mechanism without viewing the references. An
independent native review must pass before recording `PASS_ORIGINAL_TRANSFER`.
Study success alone cannot authorize a personal avatar, game/site asset, or
mastery claim.

## Failure semantics

Every rejection records exactly one restart token:
`REBUILD_FROM_STAGE(recover|source_packet|observation|mask_unit|same_unit|original_transfer)`.

| Failure | Required restart token |
|---|---|
| Missing, contradictory, or stale recovery fields | `REBUILD_FROM_STAGE(recover)` |
| Fewer than two visual sources, no compatible tutorial, missing provenance/unit/boundary | `REBUILD_FROM_STAGE(source_packet)` |
| A claimed general relation lacks two-source plus tutorial support | `REBUILD_FROM_STAGE(observation)` |
| The mask leaks an answer, changes capability, loses a source, or lacks tutorial-mechanism review | `REBUILD_FROM_STAGE(mask_unit)` |
| Candidate is reviewed at the wrong observation unit, contradicts the frozen mechanism, or fails native cold read | `REBUILD_FROM_STAGE(same_unit)` |
| Hidden-reference transfer changes the capability incorrectly or fails independent native review | `REBUILD_FROM_STAGE(original_transfer)` |

Changing upstream sources, capability, stage, or result invalidates downstream
tokens. Keep source-specific facts in project-local state; the reusable skill
stores only this generic contract.
