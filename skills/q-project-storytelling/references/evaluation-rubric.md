# Evaluation Rubric

Use this rubric to score an existing story, compare a rewritten story brief
against a baseline, or decide whether a storytelling rewrite is strong enough
to drive a PPT, README, overview, demo script, onboarding guide, or speaker
notes.

The score is not a substitute for judgment. It makes the judgment inspectable:
what improved, what regressed, and what still needs human review.

## 100-Point Rubric

Score each category against the target audience and artifact goal.

| Category | Points | What Good Looks Like |
|---|---:|---|
| Audience fit | 15 | Audience, prior belief, concern, decision role, and likely objection are clear. |
| Promise clarity | 15 | One-line promise is concrete, behavior-changing, and easy to repeat. |
| Recognized problem | 10 | Pains are specific, credible, and tied to risk, delay, cost, friction, or missed opportunity. |
| Mechanism narrative | 15 | Explanation moves at the right zoom level from context to capability to flow or component detail. |
| Proof strength | 15 | Important claims are supported by validation, before/after evidence, examples, artifacts, scores, commits, screenshots, or clear caveats. |
| Adoption path | 10 | The audience has a realistic first action, pilot path, or standardization path. |
| Speaker-notes intent | 10 | Notes explain purpose, message, example, objection or risk, and transition instead of repeating slide text. |
| Terminology and density | 10 | Terms are consistent, defined once, appropriately technical, and free of empty claims or overloaded wording. |

## Naturalness Without Meaning Drift

After structure, proof, and adoption are acceptable, run a copy naturalness
pass. The goal is not to make technical writing casual; it is to remove
formulaic AI-sounding patterns while preserving engineering meaning.

Use `workflows/copy-style-polish.md` for detailed voice calibration, pattern
audit, draft rewrite, still-AI audit, and meaning-drift review.

Check for:

- inflated generic claims where concrete actor/action/result wording would be
  clearer;
- repetitive cadence across bullets, slide titles, or speaker notes;
- empty transitions that do not explain why the next idea follows;
- unnecessary English mixing when the term is not an interface name;
- softened or removed evidence after rewriting;
- changed terminology that conflicts with the source project.

Any naturalness rewrite must preserve the audience, promise, proof, adoption
path, caveats, and approved terminology. If a smoother sentence weakens a
claim or hides a limitation, keep the precise version and improve only the
surrounding phrasing.

Optional style add-on: after the 100-point story score passes, use the
20-point style score in `workflows/copy-style-polish.md` to compare baseline and
rewritten copy.

## Scoring Guide

- `0-49`: weak story; likely a feature list, unclear audience, or unsupported
  claims.
- `50-69`: usable draft; the core material exists but structure, proof, or
  adoption is not yet reliable.
- `70-84`: good working story; ready for artifact generation if no key
  regression exists.
- `85-100`: strong story; clear enough for high-visibility artifacts after
  normal artifact-specific review.

For each category:

- Full credit: clear, audience-specific, and artifact-ready.
- Half credit: present but generic, incomplete, or uneven.
- Low credit: missing, misleading, unsupported, or too vague to guide the next
  artifact.

## A/B Comparison

When a new story brief rewrites an existing deck or document, score both
versions using the same source material and audience assumption.

Report:

```text
Baseline score:
Candidate score:
Delta:
Main gains:
Regressions:
Unsupported claims:
Decision:
```

Decision thresholds:

- `+10` points or more and no key regression: accept the candidate as the new
  story contract.
- `+5` to `+9` points: accept only after fixing the weakest categories or
  getting human review.
- Less than `+5` points: do not replace the baseline without a clear reason.
- Any key regression: revise before artifact generation, even if total score
  improved.

Key regressions include:

- a changed or vaguer target audience;
- a weaker or inflated promise;
- loss of important proof, limitation, or caveat;
- worse adoption path;
- unsupported new claims;
- terminology that conflicts with the source project or target artifact.

## Deck Story Alignment

For PPT output, run a story-alignment review after slide-map creation and again
after generation.

Each substantive slide should serve at least one role:

- audience/context;
- promise;
- recognized problem;
- mechanism;
- proof;
- adoption or next action;
- speaker transition or objection handling.

Flag slides that are only decorative, repeat previous claims without adding
evidence, or introduce claims not present in the story brief. Map every major
claim to visible slide content, speaker notes, appendix material, or a
validation report path.

## Output Format

Use this compact report shape:

```text
Evaluation target:
Audience assumption:
Baseline score:
Candidate score:
Delta:

Category table:
- Audience fit: baseline X / candidate Y / note
- Promise clarity: baseline X / candidate Y / note
- Recognized problem: baseline X / candidate Y / note
- Mechanism narrative: baseline X / candidate Y / note
- Proof strength: baseline X / candidate Y / note
- Adoption path: baseline X / candidate Y / note
- Speaker-notes intent: baseline X / candidate Y / note
- Terminology and density: baseline X / candidate Y / note

Main gains:
Regressions:
Unsupported claims:
Decision:
Required fixes before artifact generation:
```
