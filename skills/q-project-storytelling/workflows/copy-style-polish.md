# Copy Style Polish Workflow

Use this workflow after the story structure is acceptable. It improves wording,
rhythm, and speaker-note naturalness without changing the approved audience,
promise, evidence, caveats, or terminology.

This workflow is inspired by public AI-writing pattern audit skills such as
`blader/humanizer`, but it is independently written for q-workflow project,
PPT, README, onboarding, and speaker-note artifacts. Do not copy third-party
prompt text, examples, pattern prose, or assets into project outputs.

## When To Use

Use this workflow when:

- the story brief already has audience, promise, mechanism, proof, and adoption
  path;
- slide text or speaker notes feel generic, formulaic, overly promotional, or
  too evenly paced;
- Xiao Q asks for more human, natural, senior, concise, or presenter-friendly
  wording;
- an A/B story evaluation shows the structure improved but terminology,
  density, or notes still feel weak.

Do not use it to hide missing evidence, soften technical limitations, or make
an engineering document sound casual when neutral precision is the right voice.

## Inputs

Required:

- artifact type: PPT visible text, speaker notes, README, overview, demo script,
  onboarding guide, or article;
- target audience and desired action;
- approved story brief or source outline;
- source terminology that must not drift;
- evidence and caveats that must remain visible or traceable.

Optional:

- a short sample of Xiao Q's or the target team's preferred writing style;
- target language and formality level;
- slide or section constraints.

If no voice sample exists, use a plain engineering voice: specific, calm,
direct, evidence-aware, and not over-polished.

## Stage Gates

1. **Voice calibration**
   - Identify the intended voice: internal engineering, customer-facing,
     onboarding, executive summary, science-popularization, or speaker notes.
   - If a writing sample exists, observe sentence length, paragraph starts,
     transition style, technical term usage, and punctuation habits.
   - If no sample exists, choose plain engineering voice and record that choice.

2. **Meaning lock**
   - List the facts, evidence, caveats, product names, project terms, and claims
     that must survive the rewrite.
   - Mark which terms are interface names or workflow terms and should not be
     translated or casually varied.

3. **Pattern audit**
   Look for clusters, not isolated words. A single formal phrase is not a
   problem by itself.

   - significance inflation: generic claims that something is pivotal, crucial,
     transformative, or a testament without proof;
   - promotional tone: vibrant, powerful, seamless, must-have, world-class, or
     similar sales wording not supported by evidence;
   - fake depth: trailing `-ing` clauses or abstract summaries that do not add
     facts;
   - vague authority: experts say, industry reports, observers note, or similar
     unsourced claims;
   - copula avoidance: using elaborate verbs where `is`, `has`, or `uses` is
     clearer;
   - forced symmetry: rule-of-three, false ranges, repeated title plus one-line
     warm-up, or every bullet using the same grammar;
   - chatbot residue: of course, great question, I hope this helps, let me know,
     or production comments in final artifact text;
   - empty closers: generic positive endings that do not say what happens next;
   - terminology drift: synonym cycling for the same project term;
   - unsupported naturalness: wording that sounds smoother but weakens proof,
     caveats, or accountability.

4. **Draft rewrite**
   - Rewrite affected passages, not the whole artifact by default.
   - Prefer concrete actor/action/result language.
   - Vary sentence length where the artifact allows it.
   - Use short sentences for important presenter moments, but avoid stacked
     drama or manufactured punchlines.
   - Keep visible slide text compact; put nuance, objections, and caveats in
     speaker notes or appendix material when appropriate.

5. **Still-AI audit**
   - Ask: "What still makes this sound generated, generic, or performative?"
   - Check for remaining pattern clusters and for overcorrection into casual,
     opinionated, or vague wording.

6. **Meaning-drift check**
   Before accepting the rewrite, verify:

   - audience and desired action are unchanged;
   - one-line promise is not inflated;
   - proof and caveats are still present or traceable;
   - technical terms are stable;
   - no unsupported claim was introduced;
   - the output still fits the artifact constraints.

7. **Final polish output**
   Return:

   ```text
   Voice target:
   Meaning lock:
   Pattern audit:
   Draft rewrite:
   Still-AI audit:
   Final rewrite:
   Meaning-drift result:
   Remaining risks:
   ```

## Artifact-Specific Rules

### PPT visible text

- Do not turn slides into prose paragraphs.
- Replace generic labels with concrete claims where space allows.
- Keep terms consistent across slides.
- Avoid slide titles that announce structure but say nothing.

### Speaker notes

- Notes may be more conversational than visible slides.
- Add one concrete example or objection every few slides.
- Remove notes that only repeat visible bullets.
- Preserve the presenter's transition logic.

### README or overview

- Start with the practical promise, proof, and first action.
- Avoid launch-style claims unless there is release or usage evidence.
- Prefer current-state description over diff-anchored wording unless the page
  is a changelog or migration guide.

### Customer or public-facing copy

- Be stricter about unsupported claims.
- Keep limitations visible.
- Do not borrow internal shorthand unless it is defined.

## Scoring Add-On

If comparing before and after style, score only after story structure passes.

Use a 20-point style score:

- specificity and concreteness: 5;
- rhythm and readability: 4;
- voice fit: 4;
- terminology stability: 3;
- evidence and caveat preservation: 4.

Reject a style rewrite if it scores higher on readability but fails evidence,
caveat, or terminology preservation.
