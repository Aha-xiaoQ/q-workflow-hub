# Adaptive Child-Agent Model Routing

Use this reference only after `q-agent-roster` has already established that a
real child agent is justified. It selects capability for that bounded child
task; it is not a reason to create an agent for ordinary work.

## Authority Boundary

- A skill cannot replace the model already serving the main conversation,
  change the user's account allocation, install a provider, or override product
  policy.
- The main agent remains the default owner. It should use the current main
  model for routine work and create no child merely because a task is long.
- This procedure applies only when the platform exposes explicit child-agent
  `model` and `reasoning_effort` controls. If either is unavailable, record the
  capability constraint and keep the task on the main path or use the platform
  default; do not pretend an escalation occurred.
- Side-effect authority does not increase with model capability. A stronger
  child still needs the same approval, privacy, push/publish, credential, and
  destructive-action gates.

## Routing Contract

- **When:** A bounded child-agent task has a plausible capability gap relative
  to the current main model.
- **Goal:** Spend additional capability only where it materially improves the
  chance of a correct, well-evidenced result.
- **Strength:** should.
- **Hardness:** procedure.
- **Layer:** q-agent-roster dispatch reference.
- **Tier:** Project; Deep only when source, risk, or platform availability is
  uncertain.
- **Risk:** allow for model selection; existing action-risk rules still apply.
- **Avoid:** escalating because of input length, urgency, or a vague wish for a
  "smarter" agent; silently downgrading a requested high-capability task; using
  several expensive agents before one bounded pass produces evidence.

## Intensity Assessment

Score one point for each signal that is present after the task is decomposed:

1. The result requires resolving materially conflicting evidence or making a
   non-obvious tradeoff, not applying a known checklist.
2. Three or more tightly coupled technical, visual, or workflow constraints
   must remain coherent in one output.
3. A mistake is costly to recover from even after normal validation, such as a
   broad architectural choice, difficult code diagnosis, or a high-quality
   review gate.
4. The task needs independent adversarial review, specialist synthesis, or
   perceptual judgment beyond a deterministic test.
5. The same class has already failed on the current path, or a bounded previous
   pass explicitly returned `insufficient` evidence/capability.
6. The task must reconcile current external evidence with local project facts
   and the answer will steer a consequential next step.

Subtract one point for a fully deterministic single-file/task operation with a
known validator. Do not count file size, token count, or a long chat history as
intensity by themselves.

| Net score | Default decision |
|:---|:---|
| 0–1 | Keep the work on the main path. Do not spawn for capacity. |
| 2–3 | Delegate only when isolation, a role contract, or parallelism already justifies it; choose default/current capability and normally `medium` reasoning. |
| 4–5 | If the main path is not confidently sufficient, select a higher approved child model for one bounded task. Choose reasoning independently under the four-axis rule below. |
| 6+ or a failed high pass | If a documented capability gap remains after decomposition, select the highest approved child model for one owner first, with explicit evidence and stop conditions. Otherwise keep the main path and use its reliable validator. `xhigh` reasoning needs its own justification; it is not an automatic consequence of the score. |

The score is an escalation signal, not a bundled model/effort/cost/permission
setting.

The effort examples in this table and the four-axis assessment apply only
after an explicit override is justified, supported and allowed. Otherwise
inherit model and effort without sending override parameters, including for
full-history forks. A suggested `medium` or `high` here is not a mandatory value.

## Four Independent Decision Axes

1. **Model class — capability gap.** Use a higher child model only when the
   main path is not credibly sufficient for the task's synthesis, diagnosis,
   review, or perceptual judgment. A 4+ score is a prompt to check this gap, not
   proof by itself.
2. **Reasoning effort — inference depth.** Use `medium` for bounded known
   procedures, `high` for several interdependent constraints or conflicting
   evidence, and `xhigh` only when the child must maintain a long dependency
   chain *and* the result is bounded by a concrete evidence/stop condition.
   A stronger model does not automatically require higher effort.
3. **Cost posture — bounded spend.** Preserve the platform/user budget. Mark
   the pass `normal` or `elevated`; an elevated pass has one owner first, an
   output cap, and no speculative fan-out. Do not convert remaining budget into
   extra agents or deeper effort without a new need.
4. **Action authority — unchanged.** Model class and reasoning never grant
   write, install, deletion, credentials, push/publish, privacy, or approval
   authority. Those decisions stay under their existing risk gates.

## Observed Host Binding

Default to inheriting the current main model and effort when a child is useful.
Do not choose a historical model name from this reference as an automatic
escalation. Read the current tool's exposed choices separately from the main
model identity; if identity is not observable, record `unknown`.

For example, an Astra main agent must not route a difficult pass to Sol merely
because older guidance called Sol the highest tier. Conversely, a host exposing
only older models still uses its actual supported choices. Model capability,
reasoning depth, cost posture and action authority remain four separate axes.

Overrides require a concrete capability/efficiency reason, an exposed choice,
and permission under the host's actual tool contract. Some hosts disallow
overrides with full-history forks; use the supported inheritance mode or an
explicit minimal packet, never invent a configuration. Capability descriptions
are not measured quality or cost evidence for this user's tasks.

## Task-Shaped Default Posture

- Keep the current main model as integration owner. Do not spawn merely to move
  routine work to a cheaper model; coordination can cost more tokens than the
  delegated work saves.
- Delegate only when a bounded independent question, review or parallel task
  earns the coordination cost. Stronger models do not remove self-review risk.
- A different child model is an explicit experiment, not an automatic response
  to task length or intensity score. Prefer inheritance until evidence supports
  an override. No routing rule overrides a user or platform no-delegation rule.
- Promote cross-task defaults only after representative matched runs compare
  accepted quality, total tokens, elapsed time, retries, rework and missed
  escalation. Keep untested alternatives experimental, including Astra routes.

## Dispatch Record And Feedback

Before spawning, add these fields to the task packet or integration note:

```text
capacity_decision:
  main_model_switchable: no
  observed_main_model: <actual current model when observable, otherwise unknown>
  exposed_child_models: <actual selectable child values>
  intensity_score: <0-6>
  signals: <short list>
  why_main_is_not_enough: <or not-applicable>
  selected_child_model: <actual platform value>
  selected_reasoning_effort: <actual value>
  cost_posture: <normal|elevated, with output cap if elevated>
  action_authority: unchanged
  expected_evidence: <report/test/review artifact>
  stop_condition: <bounded completion condition>
```

After the report, record one outcome: `sufficient`, `insufficient`, or
`over-provisioned`. Use it to calibrate future thresholds, but never turn one
success into a permanent default escalation.

For model-routing experiments, compare against a no-child baseline. Lower
child-model price, fewer main-thread tokens, or faster wall-clock time is not an
efficiency win when total tokens, retries, coordination, or accepted-result
quality is worse.

## Promotion And Evaluation Gate

Evaluate routing candidates in three ordered layers. A later layer cannot
compensate for an earlier failure:

1. **Safety and authority hard gate.** Any unauthorized proceed, destructive
   action, credential expansion, privacy breach, or invented capability makes
   the run ineligible regardless of aggregate score.
2. **Schema and protocol conformance.** Reject missing/duplicate/unknown cases,
   invalid enums or evidence types, incomplete required fields, and forbidden
   behavior. Label the resulting number `protocol_conformance`; do not present
   it as answer quality or model intelligence.
3. **Semantic quality and utility.** Use masked independent review for
   correctness, rationale, evidence relevance, over-blocking, rework, and user
   usefulness. Record disagreements and adjudication instead of forcing every
   defensible route into one exact gold label.

A durable promotion comparison also requires matched model/effort/context/tool
conditions, fresh per-invocation workers unless persistence is the treatment
being tested, a pre-registered stop/pass rule, and separate token, latency,
retry, rework, recall, precision, and disagreement measures. If these conditions
are absent, report the run as a scorer or protocol calibration only and set
`promotion_eligible: false`. A small calibration slice may improve the harness;
it cannot establish a global default.

## Smoke Scenarios

1. **Tiny deterministic fix:** a one-line label repair with a snapshot check
   scores 0. Keep it on the main path; a higher child is over-provisioned.
2. **Bounded research synthesis:** conflicting current sources justify one
   independent child while the main agent inspects local constraints. Inherit
   the current model/effort unless a supported override has a documented reason;
   require a source table, not a higher-model claim.
3. **Unavailable escalation:** a score-6 code diagnosis has no higher child
   model exposed. State `main_model_switchable: no`, select the strongest
   available permitted path, add an independent regression check, and do not
   claim that the model changed.
4. **High score without a gap:** a score-6 release checklist has an existing,
   reliable main-path validator that covers the coupled requirements. Record
   `why_main_is_not_enough: not-applicable`, keep the work on the main path,
   and do not escalate merely because the score is high.
5. **Astra main with independent review:** keep Astra as integration owner and
   inherit for one disjoint review. Do not silently downgrade to an old named
   default. Required review still runs; compare utility against a no-child
   baseline before claiming a permanent efficiency improvement.
6. **Luna main but Luna child unavailable:** runtime evidence shows Luna is the
   active main model while the spawn surface exposes only Sol and Terra. Record
   both facts separately; do not claim a Luna worker was dispatched and do not
   infer child availability from the main session log.
