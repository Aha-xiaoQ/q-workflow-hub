# Workflow Test Protocol

Status: candidate
Updated: 2026-07-02

Use this protocol when Xiao Q wants a repeatable test after GitHub personal
pull, internal Git remote/promotion install, runtime refresh, or workflow/skill changes.
It combines automatic checks with Xiao Q's endpoint feedback, then turns misses
into workflow or skill improvements.

## Trigger Phrases

Use this path for:

- `workflow-test`
- `工作流测试`
- `核心自测`
- `全量自测`
- `个人端拉取后测试`
- `GitHub个人端恢复测试`
- `internal Git remote推广端装载测试`
- `推广端安装测试`

## Levels

| Level | Use when | Automatic scope |
|---|---|---|
| `smoke` | quick sanity after a small change | format surface audit and skill portfolio blocker scan |
| `core` | after personal pull, runtime refresh, or ordinary workflow change | smoke plus q-standard, strict lifecycle, lifecycle receipt, Phase B preflight, and release observation |
| `full` | before push/release candidate, remote rebuild verification, or user endpoint testing | core plus runtime text/encoding guards, release install/upgrade smoke, and stability suite |
| `release` | colleague/promotion/public readiness | full plus endpoint feedback and explicit signoff gates |

## Standard Command

```powershell
python <q-workflow>\scripts\workflow_test_flow.py --level core --scenario personal-pull
```

Use `--scenario remote-promotion` after a promotion endpoint or internal Git remote
install test. The script writes a Markdown report and a JSON endpoint-receipt
template.

For a concrete team-release replay, pass every trace-bound evidence input
explicitly:

```powershell
python <q-workflow>\scripts\workflow_test_flow.py --level release --scenario remote-promotion `
  --feedback-input <completed-feedback.json> `
  --release-scenario-dir <top-task-scenarios> `
  --usability-report <usability-pass.md> `
  --signoff-file <release-signoff.md> `
  --recovery-regression-report <recovery-regression.json>
```

The score includes 75-point advisory/manual placeholders for compatibility.
Those placeholders are pending state, not partial passes or remote evidence;
the required/status columns and process exit code determine the gate verdict.

Release endpoint feedback is a JSON receipt, not a free-form pass statement. It
binds `format_version`, `trace_id`, `scenario`, `endpoint`, timezone-qualified
`executed_at`, and unique step rows. A passing step requires non-empty evidence
paths/command receipts and a note; duplicate, unknown, wrong-scenario, or
unbound rows fail closed.

## Feedback Loop

1. Run the chosen level.
2. Give Xiao Q the score, report path, and JSON endpoint-receipt template path.
3. Xiao Q tests endpoint-specific manual steps and records pass/partial/fail
   with notes.
4. For a release-level endpoint replay, rerun with
   `--feedback-input <completed-feedback.json>`; missing, partial, failed, or
   untested endpoint evidence remains a blocker. Core/full endpoint feedback is
   advisory and does not create a remote-ready claim.
5. Convert failed manual or automatic steps into a follow-up report:
   failure mode, expected behavior, observed behavior, owner skill, smallest
   patch, validation command, and whether the standard was too loose or too
   strict.
6. Promote only repeated or high-impact fixes into always-on rules; keep rare
   endpoint notes in reports or references.

## Scoring

- Automatic pass: 100.
- Automatic fail or timeout: 0 and blocks pass for that level.
- Manual pending: 75 until Xiao Q supplies endpoint feedback.
- User feedback can override the practical outcome, but not the raw command
  result. Keep both scores in the report.

## Boundaries

- The test flow never pushes, publishes, deletes, changes credentials, flashes
  hardware, or changes release signoff.
- Remote rebuild claims require actual endpoint evidence from GitHub or
  internal Git remote. Local runtime pass alone is not enough.
- The current foundational suite is the release stability owner. The historical
  `workflow_extended_suite.py` may be observed for legacy evidence, but its
  dated standalone/team-packet fixtures do not block the modern release path.
