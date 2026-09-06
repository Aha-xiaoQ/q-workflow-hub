# Learning Log 2026-06-20

Objective: improve `q-agent-roster` after the first runtime seed by studying
strong adjacent agent-orchestration sources and validating whether the skill
now produces better delegation behavior.

## Sources

| Source | Role | License posture | Material used |
|---|---|---|---|
| OpenAI Agents SDK docs: agents, handoffs, guardrails, orchestration | Primary agent-orchestration docs | Docs studied only | Ideas/patterns only |
| Claude Code docs: custom subagents and SDK subagents | Primary subagent behavior docs | Docs studied only | Ideas/patterns only |
| LangChain/LangGraph multi-agent docs and supervisor reference | Primary/implementation reference | Docs studied only; related repos are MIT but no code copied | Ideas/patterns only |

No code, prompt text, schemas, screenshots, or assets were copied from external
sources. Local wording and protocol fields were independently adapted to Xiao Q
workflow needs.

## Mechanism Matrix

| Mechanism | Source signal | Local adaptation | Status |
|---|---|---|---|
| Specialist agents need clear descriptions and bounded tools/actions | Common across sources | Added allowed/forbidden actions and expert guardrails | Promoted |
| Context isolation prevents parent-context pollution | Claude Code and LangChain context engineering | Added context packet and filtering rules | Promoted |
| Handoff and subagent-as-tool are different modes | OpenAI and LangChain | Added local-pass, subagent-as-tool, phase-handoff, parallel-worker taxonomy | Promoted |
| Guardrails must run at the right layer | OpenAI guardrails | Added pre-delegation guardrail questions and acceptance criteria | Promoted |
| Route decisions need replayable traces | OpenAI tracing concept and q-workflow durability | Added route_decisions and trace fields | Promoted |
| Swarm-style dynamic handoff memory | LangGraph swarm | Deferred until we have real repeated phase-handoff sessions | Deferred |

## Pre-Mortem

- The next run may overuse subagents for small tasks. Gate: mode boundary table.
- The next run may pass too much context. Gate: context packet requirement.
- A reviewer may edit without ownership. Gate: expert guardrails.
- Reports may still be hard to integrate. Gate: `AGENT-TASK v2` and
  `AGENT-REPORT v1` required fields.
- The loop may claim improvement without evidence. Gate: validation scenarios,
  trace field, and subagent forward test.

## Patch Summary

- Updated `SKILL.md` and `dispatch-agent.md` to require context packet,
  allowed actions, acceptance criteria, and mode choice.
- Upgraded task prompt to `AGENT-TASK v2`.
- Added `context-guardrails.md`.
- Expanded orchestration, quality gates, and validation scenarios around mode
  choice, context isolation, guardrails, and traceability.

## Learning Score

Initial score estimate after artifact validation and one forward test:

- Source fit: 10/10
- License hygiene: 10/10
- Mechanism extraction: 18/20
- Layer mapping: 14/15
- Adaptation quality: 14/15
- Validation evidence: 15/20
- Restraint and maintainability: 9/10

Initial total: 90/100 before independent structure review.

Independent structure review after the patch scored 84/100. Findings were
actionable: indexed disclosure needed definition, context/guardrail field
placement needed alignment, the root-cause gate label was ambiguous, and the UI
metadata did not mention `AGENT-TASK v2`. Follow-up patch aligned those points.
The skill remains stable enough for normal experimental use, but not yet Level
4; it still needs repeated real-task evidence after the next HTML PPT or
PPT-component run.

2026-06-21 follow-up: added `Usability Validator (验用)` as the first-time user testing expert after
Xiao Q identified colleague promotion of the PPT skill as a real upcoming
scenario. Forward test selected `Usability Validator (验用)` correctly, deferred `Workflow Distiller (沉炼)`, and produced a
read-only first-run usability task with a 0-10 rubric. This improves promotion
readiness coverage but still needs a real PPT skill package path before it can
count as Level 4 evidence.

2026-06-21 deepening pass for `Usability Validator (验用)`: main thread and a subagent researched
first-time user testing, cognitive walkthroughs, documentation structure,
developer onboarding, scorecards, package health, and maturity levels. Promoted
only mechanisms: cold-start top tasks, four test modes, friction taxonomy, docs
gap matrix, readiness gates, 100-point rubric, and `not-ready`/`pilot-ready`/
`team-ready`/`public-ready` decisions. The next real validation should run
against the actual packaged PPT skill and record a first-run trace.

2026-06-21 report-shape correction: during the q-workflow public starter
English-parity audit, the `Usability Validator (验用)` real subagent returned useful findings but did
not use `AGENT-REPORT v1`. The main agent normalized the findings into a
durable report and patched `handoff-protocol.md`, `dispatch-agent.md`,
`quality-gates.md`, and `validation-scenarios.md` so future real subagents must
start with `AGENT-REPORT v1`, include packet identity and `platform_agent`, and
use separate `agent_slot`/output namespaces for parallel work. Lesson: useful
prose is not a standard report; it can be integrated only after correction or
after logging `packet_complete: fail`.

2026-06-21 HTML review-gate correction: Xiao Q pointed out that the first-run
HTML was sent for human review before independent layout/content review. A
parallel `Pagewright (页匠)` and `Usability Validator (验用)` pass caught obvious issues: weak first action, mobile
layout problems, card-heavy hierarchy, missing success criteria, weak privacy
trust boundary, and missing failure prompts. The workflow now requires
nontrivial user-visible HTML, especially onboarding/setup pages, to pass
`Pagewright (页匠)` layout/product-shell review and `Usability Validator (验用)` first-user review before Xiao Q is
asked for subjective review. Lesson: static HTML checks are necessary but not
sufficient; the first human review should evaluate product judgment, not catch
basic layout and onboarding defects.

2026-06-22 design-language correction: Xiao Q found the revised first-run guide
still had product-design issues after the previous review pass: a numbered
side rail read as a broken directory, active state could mislead users, and
the content frame over-weighted session recovery instead of explaining the
whole q-workflow system. A parallel `Source Scout (寻源)` and `Doc Architect (文构)` pass was useful: `Source Scout (寻源)`
extracted progress/task-list/onboarding mechanisms from external design
systems, while `Doc Architect (文构)` grounded the content in local q-workflow PPT/report
material. Lesson: for visually important onboarding artifacts, the subagent
set may need both design-language research and narrative/content framing, not
only layout and usability review. The main agent remains responsible for
integrating those findings into one coherent local design and for checking that
state behavior matches screenshots and interaction expectations.

2026-06-22 publish-gate correction: Xiao Q caught a serious process defect when
the main agent pushed a first-run HTML change before the final expert review
and before Xiao Q human approval. Xiao Q clarified the operating policy:
record local notes, reports, candidates, screenshots, and local checkpoints
frequently, but require explicit Xiao Q approval before push, publish, release,
upload, or GitHub-bound sync. A `Workflow Distiller (沉炼)` pass found two contradictions: an old
fallback still allowed closing a nontrivial artifact when review was deferred,
and an old validation note described push/publish as main-agent approval. A
`Usability Validator (验用)` pass found that public install scripts had been fixed to include
`q-agent-roster`, but the new skill directory was still untracked and
quickstart success checks did not verify it. Patches promoted three durable
rules: expert/subagent review before Xiao Q final human review; Xiao Q explicit
approval before any remote/public action; and `git status --short
--untracked-files=all` as a release-candidate gate so new skill directories are
not missed. This round also exposed a protocol issue: the parent did not
backfill `platform_agent` before reports returned, so corrected identity
addenda were requested and integrated.
2026-06-24 expert self-improvement loop: Xiao Q clarified that every expert
run should be both task execution and efficient deliberate practice. The main
thread framed a candidate loop, checked local `q-research-discovery`,
`q-skill-learning`, and q-agent-roster protocol files, researched outside
learning mechanisms, then used an independent `Workflow Distiller` explorer
(`Chandrasekhar`, id `019ef57e-7386-7520-8de3-6b5f33fb3fd7`) to audit the
framework. Adopted mechanisms: tiny `improvement_target`, delta-only evidence,
`lesson_class`, promotion decision, storage router, overhead budget, and an
explicit `no durable update` escape hatch. External mechanisms were adapted as
ideas only: deliberate practice, after-action review, double-loop learning,
blameless postmortem culture, lessons-learned repositories, and eval-style
repeatable validation. Patches landed in `expert-self-improvement.md`,
`handoff-protocol.md`, `agent-protocol-design.md`, `quality-gates.md`,
`validation-scenarios.md`, and `agents/openai.yaml`. Validation: runtime and
starter copies of `q-agent-roster` both passed `quick_validate.py` with UTF-8 mode.
Residual risk: next real multi-expert task should verify that the new fields
stay lightweight and do not force durable writes for tiny local passes.


2026-06-24 protocol communication optimization: Xiao Q asked whether the expert
interface protocol is now standardized enough to become a reliable and efficient
communication system. Recent task evidence showed strong packet identity and
handoff rules, but also remaining friction: mojibake in expert names, heavy
packet risk for tiny passes, and insufficiently structured capability/blocker
fields. External mechanisms checked: JSON-RPC-style small envelope and error
separation, MCP-style lifecycle/capability negotiation, CloudEvents-style common
event metadata, W3C Trace Context-style trace/parent propagation, and OpenAI
Agents/evals patterns for handoffs, guardrails, and repeatable regression tests.
Adopted local mechanisms: `packet_profile` (`compact`, `standard`,
`durable-parallel`), `capability_check`, `error_policy`, `error_code`,
`blocked_on`, `confidence`, protocol findings in integration notes, bilingual
expert names, and Scenario 15 protocol regression. Rejected: strict JSON-only
schema for now, because human-readable packets remain faster and sufficient
until a runner requires machine parsing.


2026-06-24 new expert admission: Xiao Q clarified that new experts should have
explicit creation rules so recurring or high-value task classes can gain real
specialist coverage without bloating the roster. Adopted mechanism: new roles go
through `workflows/create-expert.md`, must prove a gap beyond existing experts,
define English alias and Chinese codename, specify role contract and dispatch
thresholds, add quality and validation surfaces, and start as `candidate` until
real evidence promotes them to `pilot` or `stable`. Rejected: creating a new
expert for one-off tasks or for work that an existing expert plus a checklist can
cover.
