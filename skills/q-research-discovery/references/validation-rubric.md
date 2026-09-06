# Validation Rubric

Use this rubric to judge whether a skill, workflow, prompt, or documentation
pattern has been validated well enough to keep.

Score each category from 0 to 2.

| Category | 0 | 1 | 2 |
|:---|:---|:---|:---|
| Scenario realism | Toy or unclear task | Plausible task | Real task from current work |
| Success criteria | Not defined | Partly observable | Defined before test and observable |
| Evidence quality | Anecdotal impression | Some files/commands/sources checked | Reproducible outputs, diffs, logs, or citations |
| Improvement loop | No change made | Change made but not rechecked | Change made and relevant checks rerun |
| Durability | Only in chat | Local note or uncommitted state | Work item, project docs, or commit updated |

## Interpretation

- 0-3: weak signal. Do not generalize yet.
- 4-6: useful trial. Keep as a local lesson or run another scenario.
- 7-8: strong enough to improve a workflow or template.
- 9-10: strong validation. Mark the pattern ready unless risk remains.

Also record blockers and warnings separately:

- Blocking: prevents the workflow from working.
- Degraded: works, but with meaningful friction or missing coverage.
- Informational: worth knowing, not a failure.
- Future risk: not a problem now, but likely to matter later.
