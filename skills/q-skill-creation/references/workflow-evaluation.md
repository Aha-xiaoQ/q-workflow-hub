# Workflow Evaluation Loop

Use this reference to test whether a workflow, profile, or skill change is
stable enough for repeated use. The loop should start with small smoke tests
and then improve from real work feedback.

## Evaluation Loop

1. Define the changed behavior and the failure mode it should prevent.
2. Pick one compact scenario for a small change. Use 3-7 scenarios only when
   the behavior is broad or high risk.
3. Score each scenario with the rubric below.
4. Record misses as concrete lessons: trigger gap, strength gap, layer gap,
   context overload, validation gap, or tone/continuity gap.
5. Patch the smallest correct rule or reference.
6. Re-run the affected scenarios before treating the change as stable.
7. Promote only repeated, stable lessons into always-on profile or router
   layers. Keep rare cases as on-demand references or regression examples.

## Scoring Rubric

Use 100 points:

- Routing accuracy, 15: chose the right profile, project, skill, and local
  state without broad unnecessary scans.
- Rule calibration, 15: applied the rule at the right strength without being
  too weak, too rigid, or overcorrecting.
- Critical-state correctness, 20: recovered or produced the decision-critical
  objective, next action, decisions, changed files, validation and sync gaps,
  user corrections, and risks needed to continue safely.
- Resource economy, 15: used bounded tokens, file reads, scans, commands, repo
  checks, and tool calls for the risk level instead of chasing low-impact
  history.
- Speed and momentum, 10: reached the next safe action quickly in elapsed time
  and turn count without waiting on unnecessary validation or synchronization.
- Durable memory, 10: recorded outcomes, assumptions, validation gaps, and
  useful lessons in the right durable layer.
- Validation discipline, 10: ran appropriate checks or clearly stated why a
  check was unavailable.
- Collaboration continuity, 5: felt stable, personal, and direct without
  mechanical phrasing or distraction from the task.

Optional assistant style self-check, 0-5: use this as a side score when a user
is evaluating collaboration quality rather than task correctness. It should not
inflate the 100-point workflow score. Check whether the assistant sounded like
the same pragmatic partner across turns, kept enough continuity, avoided
robotic repetition, and still stayed focused on the work.

Score bands:

- 90-100: stable enough for normal use.
- 80-89: usable, but keep watching known weak spots.
- 70-79: works only with supervision; patch before relying on it.
- Below 70: unstable; redesign the rule or loading layer.

## Scenario Types

- Smoke: tiny prompts that check routing, continuity, or one rule.
- Recovery: resume after completed, paused, dirty, or interrupted work.
- Blind recovery: intentionally start a new session from ordinary recovery
  files while holding back a fuller ground-truth note, then compare the
  recovered state with the ground truth after the session has done its normal
  recovery.
- Sudden interruption recovery: resume from an incomplete or dirty state where
  the previous session may not have written a final checkpoint, then verify the
  latest visible user request, dirty Git state, generated artifacts, and mirror
  freshness before continuing work.
- Correction: user says the assistant overdid or underdid a behavior.
- Real task: actual project work with commit, push, validation, or artifact
  generation.
- Regression: saved cases where a previous workflow failed.
- Isolated reproducibility: a fresh agent receives a materially different task
  and ordinary allowed inputs, then proves whether the skill is discoverable,
  executable, transferable, and independently reviewable without chat or old
  project state.

## Isolated Reproducibility Test

Use this test when a result will support a portable, colleague-ready,
`pilot`, or `stable` claim. Keep it separate from ordinary smoke tests.

1. Freeze the exact prompt and allowed inputs before the run. Use a natural
   user-intent prompt without the skill name for discoverability; use a second
   named-skill prompt only when executability needs separate testing.
2. Start a genuinely fresh agent/context and a new output namespace. Exclude
   prior artifacts, generators, reports, coordinates, and hidden maintainer
   instructions.
3. Preserve the actual file/tool access trace, output manifest, process
   evidence, and any fallback used. A creator's isolation declaration is useful
   but not sufficient evidence by itself.
4. Ask an independent domain reviewer, uninvolved in creation and blind to the
   creator's verdict, to issue the original final-gate packet.
5. Score three results separately: `artifact`, `process`, and `isolated
   reproducibility`. A format PASS, script hash replay, or creator-arranged
   review cannot override an independent domain rejection.
6. Send failures back to the same isolated creator. Do not let the parent fix
   the artifact and then count that as skill reproduction.
7. Treat one pass as one evidence point. Broad/stable claims need different
   tasks and agents plus the remaining lifecycle gates.

## Blind Recovery Test

Use this when the user wants a realistic recovery-quality test without loading
a large truth record into the fresh session first.

1. Before starting the test, create a ground-truth note outside the normal
   recovery path, or mark it clearly as hidden evaluation evidence.
2. Put only the ordinary recovery files in front of the new session: profile,
   active work, project registry, project state, continuation prompt, and Git
   state.
3. Ask the new session to recover normally and write down what it believes the
   current objective, completed work, missing validation, and next actions are.
4. Reveal the ground-truth note and compare differences by category:
   objective, artifacts, validation, decisions, risks, next actions, and user
   intent.
5. Patch the smallest recovery layer that would have reduced the gap without
   forcing every future session to load the whole truth record.
6. Score recovery accuracy, resource cost, and speed together. A good result is
   not perfect recall; it is enough correct state with bounded loading cost and
   acceptable time to the next safe action.

## Recovery Tradeoff Principle

Score recovery by whether it found the state needed to continue safely, not by
whether it reconstructed every detail. Important information must survive:
objective, next action, decisions, changed files, validation and sync gaps,
user corrections, and risks that could cause wrong work. Low-impact history
may be marked as unrecovered when it does not change the next safe action.

Balance correctness against resource use and speed. Record token/context
budget, files or repositories inspected, broad searches, tool calls, elapsed
time, and turn count when they materially affect the evaluation. A slow or
expensive recovery should be penalized unless the risk justified the extra
work; a fast recovery should not be rewarded if it skips information needed to
continue safely.

Use harder recovery scenarios after clean-state tests pass:

1. sudden interruption before a report or commit is written;
2. dirty worktree with generated artifacts and partial notes;
3. stale runtime mirror versus fresher source hub;
4. another agent touched the repo without a clear handoff;
5. user asks to continue from a short prompt while the previous visible chat
   contained the latest decision.

## Report Shape

Use this compact report shape:

```text
Round:
Scope:
Evaluator:
Evidence:
Exact prompt / claim tested:
Agent and environment:
Allowed inputs and access trace:

Scenario | Expected behavior | Observed behavior | Score | Misses | Next patch

Average score:
Artifact verdict:
Process verdict:
Isolated reproducibility verdict:
Independent reviewer packet:
Style self-score, if used:
Resource/speed notes:
Stable enough for:
Not yet stable for:
Next scenarios:
```

## Interpretation Rules

- Treat self-scores as provisional until the user confirms them or real work
  produces more evidence.
- Do not chase a perfect score by making rules rigid. Prefer higher robustness
  with natural judgment.
- Prefer the path that has already worked in real use. Evaluation should prove
  that the simple path still works before adding alternate flows.
- Do not hide speed or resource cost inside a high correctness score. Report
  the tradeoff explicitly when a recovery is accurate but expensive, or fast
  but incomplete.
- Use style self-scores as calibration, not performance theater. A good score
  means the interaction felt steady and useful; it does not require extra
  friendly wording when the task is simple.
- When a scenario fails because the rule was not loaded, fix the loading layer
  or router pointer before adding more content to the task skill.
- When a scenario fails because the rule was remembered but misapplied, fix the
  rule shape: trigger, strength, anti-pattern, or validation cue.
