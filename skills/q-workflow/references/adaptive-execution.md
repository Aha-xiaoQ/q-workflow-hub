# Adaptive Execution — v1.2 Local Candidate

Trigger: model/tool changes, excessive clarification, overtesting, or ambiguous
execution planning. Layer: on-demand procedure, not a new authority or mandatory
per-turn runner. Existing platform instructions and safety gates take precedence.

## Capability Is Evidence, Not a Model Name

Read the current host's tool descriptions and exposed model/effort choices.
Use the current model by default. An API feature described in documentation
does not imply the desktop host exposes it. Unknown capabilities stay unknown;
do not synthesize unavailable tools, switch the main model, or downgrade a
strong main model through a historical child-model default.

Prefer an available purpose-built connector or supported CLI for the operation;
use UI control only when appropriate and allowed. Check tool-specific policies,
especially browser access, credentials and side effects. Available is not the
same as authorized. Discover narrowly, inspect returned schemas, then invoke.

## Autonomy Within Intent

Model or tool changes can trigger a bounded workflow review through
`proactive-evolution.md`; they do not prove that a rewrite is needed. Keep the
cheap signal check separate from the review and from permission to activate it.

For an explicit change request, fill routine reversible gaps and implement
within its scope. Ask a focused question only if a missing choice materially
changes the result or authorization is absent. Answer/diagnose stays read-only.
When a new user message arrives, classify it as addition, replacement, question,
or cancellation. Record material scope changes before further mutations; do
not restart completed work or continue an explicitly revoked action.

## Native Execution, Local Authority

- Batch independent reads or tool calls when the host supports it; await their
  results before dependent actions. Do not serialize independent work merely
  because an older workflow was written as a numbered list.
- Use async execution and mid-turn steering only through capabilities actually
  exposed by the host. Preserve operation IDs and completed work when a user
  correction arrives. An API feature is not a desktop configuration instruction.
- Keep native compaction and session recovery; do not invent context limits,
  reasoning ceilings or configuration flags from a model name. Task-shaped
  context loading is an efficiency choice, not a limit on model reasoning.

- Use native child agents only for an independently useful scope while the
  main agent has useful work, and only where platform/skill policy allows it.
  Keep ownership disjoint; required independent review must not become self-review.
- Track pending operations by the IDs actually returned by the host. Consume
  results before dependent actions. After cancellation, reconcile outstanding
  writes rather than treating interruption as rollback.
- Use native scheduled-task mechanisms for monitoring. Do not replace a
  scheduler with a blocking polling loop or promise future execution without it.
- Keep task/event state authoritative. Global focus is a view, not an exclusive
  task lock: validate a known task by ID before acting; do not overwrite another
  task's focus or infer ownership from a stale chat summary.
- Resume from the authoritative task, latest correction, next artifact and
  validation gap. Load historical evidence only to answer a specific question;
  mandatory instruction reads still apply in full.

## Verification and Stopping

Choose checks from `testing-standard.md` by changed surface and intended claim.
Passing tests support only what they exercised. Stop when required current
checks and reviews pass and pending actions are reconciled. Broaden testing for
a concrete new risk, not merely because a stronger model can do more tests.

Keep three verdicts separate: deterministic contract tests, real host behavior,
and cross-task quality/cost improvement. Only matched representative runs can
establish the last; this candidate does not claim a measured Astra speedup.

## Bounded Context And Work

Use these strong defaults for normal execution; explicit user, host, safety,
domain and release requirements still govern. They are not additional runners.

- **Load once, then by decision.** Read applicable instructions completely and
  retain them while unchanged. Load an additional reference only for a named
  decision or risk. A cross-reference is not an instruction to read an entire
  skill portfolio. Do not reload a completed task's history for a new question.
- **Bound output before running.** Query the relevant paths/fields first;
  return summaries, counts, failures and evidence paths. Keep verbose test logs
  in the existing workbench. If output truncates, narrow the query rather than
  increasing the cap blindly. Inspect complete selected instructions/diffs.
- **Check the changed surface.** Editorial changes get readback, links/encoding
  and diff checks as applicable. Tools and behavior changes get the relevant
  tests; hardware parameters and release artifacts retain their domain gates.
  A Git push alone does not assert a new installation or stable release.
- **Reuse valid evidence.** Bind checks to input revision and environment.
  Rerun affected checks after changes or failure; do not repeat passed suites
  because a new progress message or local commit was produced. Fetch again when
  remote evidence may have changed before a push.
- **Bound delegation.** A role plan assigns responsibility, not a minimum agent
  count. Use a minimal source packet instead of full-history forks when it
  suffices. Reuse a reviewer for fixes to its concern; add reviewers only for
  distinct evidence needs. Preserve explicitly independent reviews and host
  delegation restrictions.
- **Checkpoint once per useful boundary.** Update the existing work item with
  scope, decisions, current evidence, pending operations and next action. Review
  and integration sections may share that record; retain required trace and
  finding dispositions. Do not create parallel diaries or per-turn reports.
  Required task/event state transitions still use the installed manager.
- **Stop at acceptance.** After requested work, applicable checks and authorized
  delivery are complete, hand off using the required output contract. Do not
  add optional improvement loops or extra menus without a useful decision.
  Never silently change models,
  account settings, hooks or context limits to reduce consumption.

These changes reduce avoidable work; byte/line reductions and scenario checks
are not proof of a measured token or quota saving. Measure that separately on
comparable completed tasks, including cached input and child-agent overhead.

## Optional Policy Probe

Run the commands below from the `q-workflow` skill directory (the directory
containing `SKILL.md`), not from an arbitrary project directory.

`python scripts/execution_policy.py --input facts.json` returns advice without
writing state, running tools, granting authority, or certifying completion.
It consumes explicit fields already used in task/agent packets; it does not
create a second registry. Missing/invalid fields return `needs-context`.

Example for a small authorized local fix:

```json
{
  "intent": "change", "risk": "low", "claim": "local",
  "authority": "in-scope", "evidence": "not-run",
  "decision_missing": false, "pending_tools": false,
  "unresolved_concerns": false, "independent_work": false,
  "useful_main_work": false, "delegation_permitted": false,
  "delegation_available": false, "review_required": false,
  "monitor_available": false
}
```

Enums: intent `answer|diagnose|change|monitor`; risk `low|material|high`;
claim `local|mirror|remote-rebuild|release`; authority `in-scope|missing|denied`;
evidence `not-run|pass|fail|stale`. Remaining fields are strict booleans.
`review_required` means an outstanding required review, not one already passed.
The caller must establish evidence/authority from real artifacts; inputting
`pass` is not proof. Tier suggestions are a floor; domain gates may require more.
`authority` describes one proposed action, not the whole conversation. For
example, "continue locally, do not push" means local edits can be `in-scope`
while a proposed push is `denied`. Evaluate these actions separately; the probe
does not read conversation history or infer authorization.

Regression commands:

```text
python -m unittest discover -s scripts -p test_execution_policy.py -v
python -m unittest discover -s scripts -p test_release_repository.py -v
python scripts/q_workflow_manager.py --self-test
```

Retirement: remove the optional probe if it adds overhead without catching
different decision failures. Retain its regression cases. Durable authority,
privacy and rollback guarantees do not retire based on model marketing claims.
