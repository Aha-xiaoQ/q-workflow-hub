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

For an explicit change request, fill routine reversible gaps and implement
within its scope. Ask a focused question only if a missing choice materially
changes the result or authorization is absent. Answer/diagnose stays read-only.
When a new user message arrives, classify it as addition, replacement, question,
or cancellation. Record material scope changes before further mutations; do
not restart completed work or continue an explicitly revoked action.

## Native Execution, Local Authority

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
