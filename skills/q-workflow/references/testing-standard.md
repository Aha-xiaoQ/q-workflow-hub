# Testing Standard

Status: candidate
Updated: 2026-07-01

Use this reference from the `workflow-health` / `workflow-audit` / `体检` path
and from release or source/runtime sync work. The goal is to choose the smallest
sufficient test tier without turning tiny tasks into release drills.

## Tier Ladder

| Tier | Trigger | Required evidence | Blocks claiming |
|---|---|---|---|
| T0 micro | exact TODO/status/help, direct command output, tiny wording answer | no broad scan; state any skipped validation only when useful | protocol-heavy completion |
| T1 local change | one repo, scoped file/script/doc edit | targeted readback, parser/compile/checker when applicable, `git diff --check`, encoding guard for localized text | local handoff for the changed artifact |
| T2 skill or workflow rule | reusable skill, output grammar, validator, source/runtime mirror, bootstrap copy | source/runtime/bootstrap or source/runtime/standalone checks, `q_standard_check.py --self-test`, task-specific script validation, hash/readback evidence | claiming mirrors are synced or rule is candidate |
| T3 rebuild and clone | GitHub/internal Git remote update, new machine, no-personal-hub, resolver/path ambiguity | fresh clone or isolated temp install, remote/HEAD evidence, resolver identity check, dependency/toolchain check, public/private scan when applicable | saying the remote can rebuild current behavior |
| T4 promotion or release | team/public/customer/promotion-ready, colleague handoff | release_readiness, stability suite, variant/public scan, expert review, explicit signoff, push/reclone evidence | team-ready/public-ready/stable-release labels |


## Workflow Test Flow

Use `scripts/workflow_test_flow.py` for repeatable post-change and endpoint
tests. It is the standard path for `workflow-test`, `工作流测试`, `核心自测`,
`全量自测`, `个人端拉取后测试`, `GitHub个人端恢复测试`,
`internal Git remote推广端装载测试`, and `推广端安装测试`.

Level mapping:

- `smoke`: T2 quick sanity for small workflow/skill changes.
- `core`: T2/T3 default after personal pull, runtime refresh, or ordinary
  workflow rule updates.
- `full`: T3 before push/reclone claims, remote rebuild verification, or Xiao Q
  endpoint testing.
- `release`: T4 for colleague, promotion, public, or stable-release readiness.

`workflow_test_flow.py` deduplicates identical current/public roots, runs strict
lifecycle and Phase B preflight in `core`, and requires completed endpoint
feedback in release scenarios. The legacy extended suite is diagnostic only;
current release authority remains `release_readiness.py` plus the foundational
suite, explicit endpoint evidence, expert review, signoff, and push/reclone
proof.

Every run must produce a score, Markdown report path, JSON/report evidence when
requested, and a JSON endpoint-receipt template for Xiao Q's endpoint result. Endpoint
feedback closes the loop: classify failures into expected behavior, observed
behavior, owner skill, smallest patch, validation command, and whether the
standard was too loose or too strict.


## Selection Rules

### Evidence-Bounded Stop

Bind evidence to the changed files/revision, acceptance criteria, environment
and the claim being made. Once required checks pass, stop testing unless new
changes, failures, or unresolved concerns invalidate that evidence. Do not
repeat a broad suite merely to feel more certain. A mandated two-round suite
still runs twice; this rule does not waive required checks.

Local drift requires affected-surface repair and retest, not automatically a
remote clone. T3 remains necessary for remote rebuild claims; T4 remains
necessary for stable/public/team release claims. Separate known baseline
failures from regressions without relabeling a failing suite as passed.

Changing user requirements or artifacts makes affected evidence stale. A
successful old result, a pending tool, or a review not yet returned cannot
justify a completion claim. The optional `execution_policy.py` scenarios test
these decision boundaries, not model intelligence or actual task completion.

- Start at the tier matching the risk surface; do not run a higher tier for a
  tiny task unless the user asks or the result will be published, pushed, or
  reused as a workflow rule.
- Reassess the affected tier when a test finds remote freshness, source/runtime
  drift, missing dependency, path ambiguity, public/private risk, or a repeated
  defect. Repair and rerun that scope first; escalate only if the intended claim
  or newly demonstrated risk requires broader evidence.
- A local runtime pass is not remote rebuild evidence. Push/reclone or clone from
  the target remote before saying GitHub or internal Git remote can reconstruct behavior.
- If a command times out, leaves only `.git`, or depends on a missing package,
  record `partial` or `blocked`; do not report pass from adjacent checks.
- For substantial final handoffs, use the `Recommended Next` block. T0 micro
  answers stay natural and must not get a menu unless it actually helps.

## Format Defect Gate

Use `text-format-hygiene` whenever a defect affects output shape,
Markdown/list boundaries, code fences, JSON/YAML structure, Chinese/UTF-8,
PowerShell display ambiguity, user-facing handoff grammar, or repeated format
feedback.

Required flow:

1. Classify the defect before editing: repair, review, or sediment.
2. Patch the smallest affected source or generator range; avoid broad reformat
   churn unless the file is generated by that owner.
3. Run `text_format_guard.py` when available, `encoding_guard.py` for localized
   or mojibake-risk files, parsers for JSON/YAML, `q_standard_check.py` for
   output grammar or workflow protocol rules, and `git diff --check` for
   whitespace or line-ending drift.
4. Add or update `text-format-hygiene/references/regression-ledger.md`
   when the issue is repeated, user-found, or could recur across agents.
5. Sync source/runtime/bootstrap/standalone surfaces as applicable and compare
   hashes or read back the changed key files before claiming the format is
   fixed.

Format defects must not close as chat-only lessons. A pass needs a command,
readback, fixture, or ledger entry that a fresh session can replay. Substantial
format-fix handoffs may be checked with `q_standard_check.py --format-replay <file>` and must state `defect_class`, `fix`, `evidence`, `ledger`,
`surfaces_checked`, and `skipped_surfaces` so another agent can replay the gate.

## Regression Lessons From 2026-07-01

- Fresh GitHub clone passed clone/encoding/resolver but failed behavior until
  local `validate_experiments.py` and `scan-public.ps1` fixes are pushed and
  recloned.
- Fresh internal Git remote workflow clone proved access but exposed remote-stale
  validators; company personal hub clone timed out and left only `.git`, so it
  is not a pass.
- `quick_validate.py` may fail under the default Python when PyYAML is missing;
  use the known local Python or add a fallback before treating the skill as bad.
- Public scanners must not self-report denylist terms inside scanner definitions.
- Standalone q-workflow currently supports `q_standard_check.py --self-test`;
  `--root` requires a hub layout with sibling `q-agent-roster` unless a
  standalone mode is added.
- Recommended Next must have positive and lightweight-negative fixtures, not
  only prose in a guide.

## Health Micro-Path Output

A `workflow-health` / `体检` handoff should include:

1. current status: `pass`, `partial`, `blocked`, or `needs-push-reclone`;
2. highest tier actually proven;
3. highest tier required for the user's current goal;
4. failed or skipped test surfaces with exact reason;
5. next recommended test command or approval boundary.

Keep the output short. Put raw logs and long reports in files and cite paths.
