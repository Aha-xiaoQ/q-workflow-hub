# Workflow Standardization Stabilization Ledger

Date: 2026-07-01
Status: candidate, local gates and expert review passed

## Current Freeze

Allowed:

- define and test q-standard-contract;
- fix output grammar and expert dispatch gates;
- produce read-only expert review and integrate findings;
- commit local checkpoints after validation.

Frozen until this loop passes:

- GMPPT file moves;
- PPT-specific checker severity refactor;
- public/GitHub push;
- broad mirror synchronization beyond changed skill/runtime surfaces;
- declaring project-structure standard stable.

## Partial Work Inventory

| Surface | State | Risk | Gate before use |
|---|---|---|---|
| `skills/q-workflow/references/project-structure.md` | draft/candidate | naming conflict found by expert review; not stable | revise after q-standard-contract is stable |
| `skills/q-workflow/scripts/audit_project_structure.py` | draft/candidate | warning noise and small-task semantics need fixes | Code Auditor review + fixture tests |
| `gmppt-study/docs/PROJECT_STRUCTURE.md` | draft | project overlay created before global standard stabilized | hold; revise after global standard |
| `gmppt-study/scripts/audit_gmppt_structure.py` | draft | overreports ignored PNG exports | hold; revise after global standard |
| q-agent expert dispatch protocol | candidate | previously failed to show stable role/card before spawn | q-standard-check + real expert review |
| output status line | candidate | route/action/status fields were mixed | q-standard-check + transcript scenario |

## Root Cause Summary

- Rules existed as prose but not all had hardness levels, checks, or blockers.
- Some examples mixed route ids, expert roles, and state fields.
- Expert dispatch rules allowed or tolerated late mapping, causing platform nickname leakage.
- Warning semantics were not reliably tied to handoff blocking.
- Draft standards entered real task flow before lifecycle gates were complete.

## Stabilization Exit Gate

This loop can exit only when:

1. `q-standard-check --self-test` passes.
2. `q-standard-check --root <q-workflow skill>` passes.
3. Encoding guard passes on changed Markdown/Python files.
4. `git diff --check` passes for changed repositories.
5. `Doc Architect (文构)` or `Workflow Distiller (沉炼)` review reports no blocking issue, or each blocking issue is fixed and rechecked. Completed: Doc Architect (文构) reported no blocker; Code Auditor (码鉴) reported blocker, fix applied, rereview passed.
6. The final handoff names remaining frozen scopes and states that no push/migration happened.
