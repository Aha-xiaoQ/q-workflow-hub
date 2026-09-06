# Study And Internalize Workflow

Use this workflow when studying another skill, agent workflow, prompt pack, or
reusable automation example after the learning framework and source roles are
clear. If the user is still defining how q-workflow should learn from skills,
read `references/design-framework.md` before using this workflow.

## Steps

1. Confirm the framework.
   - Is this an exploratory research pass, a real learning round, or a
     stabilization pass?
   - If Xiao Q asks to "deep-study", "precision learn", or otherwise dig into a
     high-value source beyond a normal learning round, switch to
     `workflows/deep-study-mode.md` before patching skills.
   - Which promotion bar from `references/design-framework.md` applies?
   - If the question is whether `q-skill-pattern-learning` is better than direct
     study, run a paired A/B pass: first create and freeze an unguided direct
     baseline, then run the guided workflow on the same source, and score both
     outputs with the same rubric. Protect the A baseline from contamination:
     use an existing pre-guided historical output when available, or use a
     separate baseline worker when Xiao Q has authorized multi-agent work.
2. Define the learning question.
   - What work should become better?
   - What current failure mode are we trying to reduce?
   - What would count as improvement in a real task?
3. Inventory sources.
   - Record source path or URL, license, and whether the source is public,
     private, company, or personal.
   - If license is unclear, study ideas only and do not copy material.
4. Extract mechanisms.
   - Identify trigger/routing design, workflow phases, validation gates,
     artifact strategy, tool/script boundaries, context-loading strategy, and
     user handoff shape.
   - Ignore branding, wording, decorative structure, and source-specific
     assumptions unless they solve the same failure mode locally.
5. Map to q-workflow layers.
   - Profile: personal collaboration behavior that should always apply.
   - Skill router: trigger and routing rule for a recurring capability.
   - Workflow reference: detailed procedure loaded only when needed.
   - Script: deterministic repeated operation.
   - Project state: current project fact, artifact path, or one-time decision.
   - Evaluation scenario: regression case to prove the lesson later.
6. Patch the smallest target.
   - Prefer one router rule, one workflow reference, or one validation check.
   - Keep copied material out unless license and attribution are explicit.
7. Validate with scenarios.
   - Use at least one scenario different from the artifact that triggered the
     lesson.
   - Score with `references/learning-rubric.md`.
8. Record the decision.
   - Promote if the scenario passes and the behavior is reusable.
   - Keep experimental if the idea is promising but evidence is thin.
   - Defer if the idea needs more sources or tooling.
   - Reject if the source is incompatible, too narrow, or not better than the
     existing workflow.

If the user finds an obvious miss after a positive verdict, score the original
round as unstable. Record the miss, the missed signal, the root cause, and the
smallest reusable rule patch before rerunning the scenario.

## Minimal Report

```text
Learning round:
Question:
Sources and license:
Current failure mode:
Mechanisms extracted:
Local adaptation:
Validation scenarios:
Evidence:
Score:
Decision:
Next patch:
```

## A/B Comparison Add-On

Use this only when the learning question is comparative, such as "is this
skill better than direct study?"

- **A direct baseline**: study the source without this workflow's prompts,
  produce a natural engineer summary, and freeze it before opening this
  checklist again.
- **Independence guard**: prefer a pre-existing historical learning artifact as
  A when one exists. If no historical artifact exists and Xiao Q has authorized
  multi-agent/delegated work, assign A to a separate agent that is explicitly
  told not to use this workflow, the rubric, or B-round conclusions. If neither
  is available, write A to a durable file before starting B and state that the
  control is weaker than an independent baseline.
- **B guided round**: rerun the source through this workflow, explicitly
  recording failure mode, license boundary, mechanisms, layer mapping,
  validation scenario, evidence, and decision.
- **Comparison**: score A and B with the same rubric; record at least one place
  where B caught a miss from A, or state clearly that it did not.
- **Anti-pattern**: do not reconstruct A after seeing B. That makes the control
  round meaningless.
