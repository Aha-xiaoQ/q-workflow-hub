# Shape Narrative Workflow

Use this workflow to turn a project, product, architecture, research result, or
workflow into a clear explanation before writing slides or long-form text.

## Default Path

1. **Audience**
   - Who is listening or reading?
   - What do they already believe?
   - What do they care about?
   - What will make them resist or ignore the message?

2. **Promise**
   - Write one sentence: "After this, the audience should understand or do X
     because Y will improve."
   - If there are multiple promises, choose the one that changes behavior.

3. **Problem**
   - Use 2-4 pains the audience already recognizes.
   - Avoid abstract claims such as "efficiency" unless tied to a concrete
     failure, delay, risk, cost, or missed opportunity.

4. **Mechanism**
   - Explain why the solution works, not only what features it has.
   - Use zoom levels:
     - context: actors, environment, adjacent systems;
     - capability: major modules or workflow stages;
     - component: skills, scripts, files, APIs, or teams;
     - detail: implementation only when needed.

5. **Proof**
   - Attach evidence to each important claim:
     validation result, before/after comparison, score, artifact, screenshot,
     benchmark, user feedback, commit, tag, or operational example.
   - If proof is weak, say "candidate", "pilot", or "needs validation".

6. **Adoption**
   - Give a first action the audience can take in one session.
   - Separate immediate usage, pilot usage, and full standardization.

7. **Speaker Notes**
   - For each major section, write:
     purpose, core message, concrete example, objection/risk, transition.

## Review Path

When auditing an existing deck or document, first check these questions:

- Is the intended audience explicit?
- Is there a clear promise before structure?
- Does the story show a recognizable problem?
- Does it explain the mechanism at the right zoom level?
- Are claims backed by proof?
- Is there a practical adoption path?
- Do speaker notes add explanation rather than repeat slides?
- Are technical terms defined and used consistently?

Then use `references/evaluation-rubric.md` to score the baseline. If there is a
rewritten story brief, score both versions with the same audience assumption and
report the delta, gains, regressions, unsupported claims, and decision.

## Output Shape

Return a compact story brief:

```text
Audience:
Desired action:
One-line promise:
Recognized pains:
Mechanism narrative:
Proof points:
Adoption path:
Recommended artifact:
Speaker-notes pattern:
Open gaps:
```

Use the brief as the source of truth for the next PPT, README, overview,
article, or onboarding artifact.

## Copy Style Polish

After the story brief is accepted, use `workflows/copy-style-polish.md` when
the next task is wording, speaker-note naturalness, style, or human readability.
Do this after structure and proof are stable, not before. A smoother sentence
is a regression if it weakens evidence, caveats, adoption, or terminology.

## Artifact Handoff

When the brief will drive a PPT, README, overview, demo, or onboarding guide,
read `references/artifact-handoff.md` before invoking the target artifact skill.
The next artifact may adapt wording, density, layout, and format, but it should
not silently change the audience, promise, claim order, proof points, adoption
path, or notes intent.

When replacing an existing artifact story, run the A/B comparison in
`references/evaluation-rubric.md` before treating the new brief as the contract
for generation.
