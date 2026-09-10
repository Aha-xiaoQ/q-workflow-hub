# Workflow standardization — compatibility checklist

**English** · [Simplified Chinese](workflow-standardization-ledger-20260701.zh-CN.md)

Historical candidate reference, 2026-07-01. Use the
[current release notes](../releases/q-workflow-v1.2.md) for package status.

## Check before adopting a standard

| Surface | Compatibility concern | Required check |
| --- | --- | --- |
| Project structure | Folder naming and migration impact | Review the structure reference before moving existing projects. |
| Structure auditor | Excess warnings and small-task behavior | Review severity and run profile fixtures, including relaxed mode. |
| Expert dispatch | Role-to-run mapping must be visible before delegation. | Standard checks and an actual expert-review scenario. |
| Output status line | Route, action and state must not be mixed. | Standard checks and a transcript scenario. |

## Lessons for maintainers

- Pair prose rules with severity, checks and explicit blockers.
- Keep route identifiers, expert roles and task states separate in examples.
- Establish role-to-run mappings before delegation.
- Define which warnings block delivery.
- Do not treat draft standards as stable before their lifecycle checks pass.

## Adoption checklist

1. Run the standard checker's self-test.
2. Run the checker against the affected q-workflow skill.
3. Run the encoding guard on changed Markdown and Python files.
4. Run `git diff --check` for affected repositories.
5. Obtain independent documentation or workflow review; fix and recheck blockers.
6. State any remaining limits and distinguish validation, synchronization,
   migration and publishing. Each action needs its own scope and authorization.

Review only the intended changes. Do not use a standards update as permission
for unrelated file moves, broad mirror synchronization or public pushes.
