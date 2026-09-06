# Experiment Validation

Use when testing whether a skill, workflow, prompt, source strategy, or
documentation change actually works.

## Steps

1. State the hypothesis:
   - "If we use <workflow/change>, then <task/user> should be able to <observable result>."
2. Pick a realistic scenario. Prefer a real project task over a synthetic toy
   example unless the change is dangerous or expensive.
3. Define success criteria before running the test:
   - output produced;
   - time or friction reduced;
   - errors handled;
   - durable state updated;
   - next action clearer than before.
4. Run the scenario and collect evidence:
   - commands, files changed, sources used, warnings, and validation results.
5. Score the result using `references/validation-rubric.md`.
6. Convert findings into one of:
   - keep as is;
   - improve the skill/workflow;
   - add a template/checklist/example;
   - reject or defer the idea.
7. Rerun the relevant checks after changes and record the final result in the
   work item or project handoff.

## Output

- Hypothesis.
- Scenario.
- Success criteria.
- Evidence.
- Score.
- Decision.
- Follow-up change and validation.
