# Expert Self-Improvement Loop

Use this reference when an expert pass, specialist subagent, or multi-agent
review should improve the expert system itself. The goal is professional,
reliable, efficient expertise growth: every material task can exercise an
expert capability, but only evidence-backed lessons become durable rules.

## Core Model

Each material expert run has two outputs:

1. Task output: the review, research, patch, test, or report requested by the
   current task.
2. Expert delta: the smallest reusable lesson that could make the next similar
   expert run more accurate, faster, or more trustworthy.

Do not force a lesson when the task produced no new evidence. A good expert is
allowed to say `no durable update` and close cleanly.

## Mandatory External Calibration

Use Source Scout (寻源) or q-research-discovery before designing or changing
expert-growth, agent-evaluation, release-readiness, research, public-package, or
workflow-standard mechanisms, unless Xiao Q explicitly forbids browsing or the
network is unavailable. External material is calibration, not authority to copy:
extract the mechanism, compare it with local failures, and keep only the part
that improves Xiao Q's workflow with bounded overhead.

Minimum external calibration record:

```text
external_calibration
objective:
sources_checked:
mechanisms_learned:
local_fit:
rejected_or_too_heavy:
rule_or_scenario_delta:
validation:
```

If research is blocked, record `external_calibration: blocked` with the reason
and do not claim the expert-growth rule is fully reviewed.

## Expert Upgrade Gate

A material expert run cannot claim that the expert improved merely because it
was reviewed. Improvement requires at least one closed loop:

- a capability ledger entry with evidence and closure status;
- a role/profile checklist change in `agent-registry.md`;
- a reusable validation scenario or executable gate;
- a workflow/domain skill rule that would catch the miss next time; or
- an explicit `no durable update` reason when the finding is one-off, noisy, or
  below the promotion bar.

Accepted P1/P2 findings, repeated Xiao Q corrections, and parent-agent misses
caught by a real subagent must end as `closed`, `deferred`, or `rejected` before
calling the expert-growth loop complete. Open lessons are work items, not
capability upgrades.

## Lightweight Loop

1. Frame the practice target.
   - Ask: which expert capability is being exercised here?
   - Examples: source triage, alias migration review, first-user friction,
     visual overlap detection, release guardrail, report structure.
2. Execute the expert task against its normal role contract.
3. Capture delta evidence only.
   - Useful source or skill mechanism.
   - Missed check or false alarm.
   - Validation signal that changed confidence.
   - Reusable heuristic that would have prevented a defect.
4. Classify the lesson.
   - `none`: no durable learning; task output is enough.
   - `task-local`: keep in the project report or work item.
   - `expert-profile`: update `references/agent-registry.md` for a role.
   - `workflow-rule`: update a workflow/reference file.
   - `validation-scenario`: add or update a scenario in `references/validation-scenarios.md`.
   - `source-registry`: record a repeated useful or poor source route through
     `q-research-discovery` state.
5. Promote only after evidence.
   - One observation can become a report note or TODO.
   - Repeated misses, high-impact risks, or successful validation can become a
     rule, checklist item, or regression scenario.
6. Validate the promotion.
   - Run the smallest scenario or readback check that proves future routing or
     review behavior changed.
   - If no scenario is practical now, mark the lesson experimental and name the
     next trigger.


## Capability Growth Model

Treat each expert as a role plus a small set of named capabilities. A capability
is something observable, such as `review-class routing`, `PPT overlap
inspection`, `cold-start install friction`, `strict pass detection`, or
`source-quality triage`. Experts improve when a capability gains evidence, not
when a report merely says the expert learned something.

Maturity levels:

| Level | Meaning | Promotion evidence |
|---|---|---|
| `observed` | one task exposed a useful behavior, miss, or heuristic | report note or accepted finding |
| `practiced` | the capability was used deliberately in a later task | expert delta names the practice target |
| `validated` | a reviewer, test, or scenario confirmed it improved behavior | accepted finding, validation command, or subagent review |
| `regression-backed` | future runs have a scenario/check that can catch regression | `validation-scenarios.md`, script, or fixed report gate |
| `deprecated` | a previous heuristic caused noise or false confidence | integration note explains replacement or narrower trigger |

Capability promotion and demotion rules:

- Do not promote a capability from `observed` to `validated` without evidence
  that changed a decision, caught a P1/P2 issue, reduced repeat misses, or
  improved handoff clarity.
- Prefer one narrow capability delta over broad expert praise.
- Record false positives and noisy rules as learning too; a real expert becomes
  sharper by knowing when not to fire.
- Demote or narrow a capability when it produces repeated false positives,
  misses the same issue after a claimed lesson, or its `overhead_fit` is not
  justified by accepted findings or risk reduction.
- Keep the capability ledger task-local or report-local unless the capability
  changes future routing, role contract, validation, or release safety.

## Capability Ledger Record

Use this compact record in durable reports or integration notes when a material
expert run teaches something reusable:

```text
Capability ledger
expert: <English Alias (中文名)>
capability:
trace_id:
message_or_feedback_anchor:
evidence_anchor:
source_calibration:
previous_level: observed | practiced | validated | regression-backed | deprecated | none
new_level: observed | practiced | validated | regression-backed | deprecated | none
evidence:
accepted_findings:
misses_or_false_positives:
rule_or_scenario_changed:
closure_status: accepted | deferred | closed | rejected | open
validation:
next_practice_target:
```

## Growth Metrics

Use metrics lightly. They are signals for expert calibration, not a scoreboard.
Track them when a review is material, repeated, or release-related:

- `accepted_findings`: findings the main agent integrated or explicitly
  deferred with reason;
- `missed_by_parent`: issues a real subagent caught after main-agent review;
- `repeat_miss_count`: same class of issue found again after a claimed lesson;
- `false_positive_count`: findings rejected as unsupported or too noisy;
- `severity_caught`: highest P0/P1/P2/P3 severity caught by this capability;
- `scenario_added_or_reused`: whether a future regression check exists;
- `overhead_fit`: whether the expert pass was worth the time/context cost.

A capability is healthy when it catches more important issues over time, creates
fewer vague findings, and leaves behind smaller, clearer regression checks.

Closure rule: every accepted P1/P2 capability lesson must end as `closed`,
`deferred`, or `rejected` in an integration note. Do not count an expert lesson
as improved when the finding was accepted but no owner, validation, or deferral
reason exists.

## External Calibration

This workflow borrows patterns only as ideas, not copied process text:

- Deliberate practice: expert performance improves through sustained,
  effortful practice with feedback, not through passive experience alone.
- Knowledge engineering V&V: expert knowledge should be verified, validated,
  evaluated, and maintained across the lifecycle.
- Agent evaluation practice: traces, graders, datasets, and repeatable eval runs
  are stronger than one-off self-review when behavior must improve over time.
- Risk governance: continuous `govern`, `map`, `measure`, and `manage` thinking
  keeps expert rules from becoming stale or overconfident.

## Upgrade Triggers

Run a capability growth check when:

- Xiao Q corrects an expert process or identifies a repeated miss;
- a real subagent catches an issue after main-agent self-review;
- a P1/P2 finding is accepted and the same class can recur;
- a rule becomes noisy, too mechanical, or too broad;
- a release/team/public handoff depends on expert reliability.

The smallest acceptable outcome is `no durable update` plus a reason. The best
outcome is a named capability moving one maturity level with a validation
scenario or report gate that can catch regression.

## Research Split Pattern

Use this when a task needs external material, public examples, prior art, or
skill study.

- Main agent owns the framing question, final synthesis, file edits, validation,
  and user handoff.
- Source Scout owns broad source discovery, source roles, freshness, conflicts,
  and decision implications.
- Domain expert owns specialized interpretation: Code Auditor for code risk,
  Pagewright for UI patterns, Visual Arbiter for visual systems, Doc Architect
  for documentation structure, Usability Validator for first-user evidence.
- Workflow Distiller owns the final lesson classification and durable placement.

Parallelize only independent angles. Use sequential handoff when the later phase
needs the earlier phase's decision, source map, artifact, or acceptance criteria.

## Overhead Budget

Use the cheapest record that preserves future value.

- Tiny deterministic pass: one-line `lesson_class: none` is enough.
- Material review with no new reusable evidence: include `no durable update` in
  the report and stop.
- New but weak observation: keep it `task-local` or `defer`; do not patch a
  reusable rule.
- Durable write threshold: the lesson must be evidence-backed, reusable, and
  higher value than the storage and future context cost.

## Storage Router

| Lesson kind | Durable location |
|---|---|
| Expert behavior, role responsibility, or required check | `q-agent-roster/references/agent-registry.md` or this reference |
| Dispatch packet, report field, or handoff trace rule | `q-agent-roster/references/handoff-protocol.md` or `agent-protocol-design.md` |
| Expert validation prompt or regression example | `q-agent-roster/references/validation-scenarios.md` |
| Domain behavior such as PPT, HTML, code, PDF, or skill creation | The relevant domain skill |
| Project-specific fact, decision, or artifact state | Project work item, report, or personal hub state |
| Reusable source route or source quality memory | `q-research-discovery` source registry or research log |
| One-off note with no future trigger | No durable write, or task-local report only |

## Expert Delta Record

Use this compact shape in an expert report, final integration note, or durable
report. Keep it short unless the task is itself a workflow audit.

```text
Expert delta
practice_target:
delta_evidence:
lesson_class: none | task-local | expert-profile | workflow-rule | validation-scenario | source-registry
promotion_decision: promote | experimental | defer | discard | none
validation:
next_trigger:
```

## Promotion Bar

Promote a lesson when at least one is true:

- It would have prevented a P0/P1/P2 finding.
- It fixes a repeated user correction or repeated expert miss.
- It reduces future review cost without hiding important evidence.
- It improves role clarity, handoff quality, validation, or public/release
  safety.
- It is supported by a named source, local scenario, failed validation, or
  successful retest.

Do not promote when the lesson is only a preference, a one-off workaround, a
source copied without license clarity, or a rule that would make every small
expert pass bureaucratic.

## Reliability Checks

A self-improving expert system is healthy when:

- Experts solve the current task first; learning does not distract from delivery.
- Expert reports include enough evidence for the main agent to trust or reject
  the lesson.
- Durable changes land at the smallest useful layer.
- Validation scenarios grow from real misses, not abstract checklists.
- The main agent integrates, arbitrates, and records deferred lessons instead of
  letting subagents silently change standards.
