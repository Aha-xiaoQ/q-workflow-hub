---
name: q-workflow
description: Reusable project workflow and executable foundation gate invoked by q-assistant-profile. Use when creating, resuming, organizing, validating, updating, syncing, migrating, or recovering projects, durable state, workflow rules, or foundational command installations.
---

# Q Workflow

Keep work recoverable through the registered project, task record and Git.
Project facts belong in project files; reusable rules in skills; personal
routing in the private hub; installed skills are rebuildable copies.

## Choose The Smallest Applicable Path

- **Answer or tiny edit:** answer/check the actual target. Do not create a
  material task, expert ceremony, broad audit or release drill solely for this
  path. Honor applicable instructions and existing task state.
- **Material work:** validate the matching task/event record, read its work
  item, choose the owning skill, then edit and verify the affected surface.
  Obtain a deterministic role plan from q-agent-roster before active work.
- **Release or recovery risk:** load the named domain/release contract before
  the governed action. Local success cannot prove remote deployment, stable
  promotion or an independent review.

Plan only the next useful segment. A stage in this guide is not a requirement
for a separate tool call, document or agent. Read applicable instructions once
in full and reuse them while unchanged. Expand context only for a named decision,
failed check or unresolved risk.

## First-Read Router

Select the applicable row, not the whole table.

| Intent | Next source |
|---|---|
| Exact TODO/help/TOKEN/bare 小Q | Foundational commands below |
| Resume/status/recover | Managed focus, matching work item, one targeted status check; `references/recovery-routing.md` for ambiguity or a previously used tool |
| Material task registration, transitions or non-focus task | `references/lifecycle-contract.json`; `references/workflow-kernel-architecture.md` for manager transactions |
| New project/folder migration | `references/project-structure.md`; relevant bootstrap section of `references/full-guide.md` |
| Excessive process/context, tool choice or adaptation | `references/adaptive-execution.md` |
| Health check or mirror drift | `references/workflow-kernel-architecture.md`; manager status first, doctor only for requested/deeper diagnosis |
| Workflow cleanup | `references/workflow-hygiene.md` |
| Tests and evidence depth | `references/testing-standard.md` |
| Commit, push or public sync | `references/sync-and-push-policy.md` |
| Unattended/recurring work or resource exhaustion | `references/unattended-resource-guard.md` before creating or retrying work |
| Loop engineering | `references/full-guide.md` Command Alias Layer; permission preflight, bounded stop and progress |
| Competing authorities, quality/format rules, learning/design or reference reproduction | `references/q-standard-contract.md` and owning domain skill |
| Chinese/UTF-8 or display corruption | `references/encoding-safety.md` |
| Workflow architecture/native replacement | `references/workflow-evolution.md` |
| A new capability signal or repeated friction | `references/proactive-evolution.md`; no unchanged inventory or network ritual |
| Repository naming, workflow identity or portfolio | `references/repository-naming.md` or `references/workflow-identity.md`, according to the decision |
| Explicit consolidation/lesson capture or legacy recovery | Relevant section of `references/full-guide.md`; do not load it for ordinary execution |

## Foundational Commands

Exact commands route before semantic interpretation through the installed
`scripts/q_base_command.py` and `references/base-command-contract.json`.

- `TODO`/`todo`: `--input TODO --format json`; `TODO:<text>` appends and a
  plain number selects the current listed item. No incidental repo scan/push.
- `TOKEN`/`token`/`tokens`/`token usage`:
  `--input TOKEN --open-ui --format json`.
- Exact `帮助`: `--input "帮助" --open-ui --format json`.
- Bare `小Q`: `--input "小Q" --format json`.
- For TODO, TOKEN, 帮助 and bare 小Q, display returned `surface.chat_text` verbatim.
  Do not replace its receipt or add a TODO-number menu.

Resolve authority from q-profile. The runtime personal-state mirror is
rebuildable, not editable authority. Missing/malformed authority or an
unregistered exact command blocks that command; do not invent a fallback.
For reported drift, use `q_base_command.py --audit --sync-runtime` and rerun.

## Authority, Recovery And Visibility

Inspect managed focus before claiming status for ongoing material work. Validate
a v2 pointer through the matching task record and bound event; use `--task-id`
or `--trace-id` for non-focus work. Closed/unrelated focus cannot redirect the
current request. Locate unknown work through the registry.

Use the installed manager's plan/apply transaction for task transitions; check
each command's exit status before applying its output. Never replay an older
plan because a new plan failed. Keep one compact work-item checkpoint at a
meaningful handoff: intent/authorization, done/pending, source/runtime paths,
current evidence, pending operation IDs, blockers and next action. Historical
reports and summaries are navigation/evidence, not renewed authorization.
Reconcile the latest user correction before more artifact work.

For `visibility_latch: phase-b-required`, every user-visible message begins
`小Q工作流 / <registered q-skill-id> / <Chinese current action>`.
The latch ends only on explicit close, pause, switch or return to Phase A.
Read `references/phase-b-output.md` before first Phase B output; retain its
handoff validator and required output contract.

## Execution And Checks

- Reuse existing authorization. Make routine reversible choices within scope;
  ask only for a consequential missing decision or newly expanded authority.
  Answer/diagnosis stays read-only. Newer cancellations override old approval.
- Preserve unrelated dirty changes; inspect touched ownership first. Use a
  clean isolated checkout when needed, never stage a whole dirty repository.
- Choose tests by changed surface and intended claim. Reuse passed evidence
  until inputs, environment or a new concern invalidate it. Stop at acceptance.
- Whole-workflow stable/install-ready or foundational repair claims require
  `workflow_stability_suite.py --rounds 2 --check-only --strict --stdout`.
  Touched-file mirror claims use hashes; they do not establish full readiness.
- Keep work progress, integrity and release posture distinct. Verify remote
  state by successful fetch before remote claims; verify running artifacts
  separately from source tests.
- Independent domain/release reviews remain independent. Role plans assign
  responsibility, not minimum headcounts. Follow host delegation restrictions.
- Before external text delivery, check audience relevance, factual support,
  clear instructions, limitations, safety and attribution in final exports.
  Do not expose assistant/client process notes as product content.
- Learn from inspected evidence; distinguish hypotheses from proven methods.
  Do not invent domain facts or copy unclear-license third-party material.
- Preserve privacy, license, credential and destructive-action boundaries.
  Push/publication requires scope-specific authorization, which may already
  be present. Do not change global settings merely to optimize workflow cost.
- Use native context handling. Do not infer model limits or install memory
  hooks. Keep tool results bounded to necessary evidence; store bulky logs in
  the existing workbench.

## Close The Requested Work

Check affected artifacts, relevant diffs and known mirrors. Reconcile the
matching work item, task/event state, matching TODOs and residual risks; do not
audit unrelated hub state. Record review dispositions and evidence once, with
paths to raw receipts. Commit meaningful checkpoints and complete an authorized
push after its checks.

A normal completion does not start another research, expert-learning or
skill-update cycle. Capture a reusable lesson only when evidence warrants it;
park unrelated opportunities. Report edited, tested, installed and published
states separately, including concrete deferred gaps. Do not claim measured
token savings from shorter files or a higher cache ratio alone.
