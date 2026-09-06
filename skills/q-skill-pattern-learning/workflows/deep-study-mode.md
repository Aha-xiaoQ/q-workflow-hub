# Deep Study Mode

Use this workflow when a source is unusually valuable, subtle, or likely to
improve a major q-workflow capability. It is a deeper pass than a normal
learning round. The goal is to learn the source's operating system, not its
surface style, file names, prompts, or demo assets.

## Trigger

Use this mode when:

- Xiao Q asks for precision learning, deep study, or a careful framework before
  patching.
- A source has already passed a normal learning round but still seems to hide a
  deeper mechanism.
- The source affects high-value outputs such as decks, visual systems, project
  memory, sync, recovery, agent orchestration, or validation.
- A previous learning round produced a useful patch but did not explain why the
  source is reliable.

## Rules

- Start with a written frame: target failure mode, source role, depth question,
  and promotion bar.
- Learn ideas and independently reimplement mechanisms. Do not copy code,
  prompts, schemas, text, screenshots, HTML demos, images, audio, or other
  assets unless license compatibility and attribution are explicit.
- Treat "inspired by another product or circulated prompt" as a boundary flag.
  Learn the mechanism, but do not ingest or repeat the upstream prompt text.
- Prefer source evidence paths and short paraphrased observations over pasted
  source excerpts.
- Keep the patch small. Deep study should improve precision, not turn a router
  into a monolith.

## Deep Questions

Answer these before changing a skill:

1. **Stage gates**: what phases must happen in order, and where does the source
   stop instead of guessing?
2. **Source-material completeness**: what real inputs are required, what is
   optional, and what degradation path is honest when inputs are missing?
3. **Source of truth**: what upstream artifact drives downstream work: facts,
   brand spec, transcript, timeline, rubric, test fixture, or another file?
4. **Observability**: how can the artifact be inspected, replayed, compared,
   rendered, exported, or debugged without relying on confidence alone?
5. **Parameter surface**: which decisions are fixed by the workflow, which are
   exposed as variants or controls, and which should not become options?
6. **Alternative generation**: when does the source create multiple independent
   candidates, and what criteria choose among them?
7. **Review loop**: what rubric, expert lens, platform fit, or user checkpoint
   catches failures before handoff?
8. **Layer mapping**: should the lesson land in a profile rule, skill router,
   workflow reference, script, quality gate, scenario, or project state?
9. **Learning effectiveness**: what would prove the learned mechanism transfers
   to a different task, and what would show that only the current artifact was
   improved?
10. **Assumption change**: did the source merely improve an action, or did it
    change a governing assumption about how the work should be done?
11. **Pre-mortem**: if this learned mechanism fails in the next real task, what
    are the most likely causes and what evidence would reveal the failure early?

## Procedure

1. **Frame the pass**
   - Name the current failure mode.
   - State why normal study is insufficient.
   - Define the promotion bar and at least one different validation scenario.
2. **Inventory sources**
   - Record repo/path/URL, license, commit or access date when practical, and
     source role.
   - Identify origin and boundary risks, especially derivative sources,
     unclear prompts, private material, brand assets, or generated media.
   - For a multi-source exemplar pass, pick only 2-3 sources with different
     roles. Prefer one design reference, one implementation example, and one
     boundary/evaluator example. More sources are allowed only when they answer
     a specific contradiction.
3. **Mechanism extraction**
   - Extract 5-8 mechanisms using the deep questions above.
   - For each mechanism, record evidence path, local adaptation, and risk.
   - Mark whether the mechanism is mature enough to promote, experimental, or
     only useful as a future scenario.
   - For multiple sources, build a mechanism matrix and classify each mechanism
     as common, source-specific, contradictory, or unproven before patching.
4. **Synthesis**
   - Cluster mechanisms into a compact local framework.
   - Decide the smallest target layer to patch.
   - Keep rare or high-cost behavior in this workflow or a reference file, not
     in `SKILL.md`.
   - Promote only mechanisms that can be expressed as trigger, minimal default
     path, explicit fallback condition, validation evidence, and durable-state
     target.
   - Run a short pre-mortem before implementation: imagine the next user-facing
     run failed, name 3-5 likely causes, and convert them into gates or
     validation checks.
5. **Validation design**
   - Define 2-4 scenarios that would prove the lesson transfers.
   - At least one scenario should be different from the source artifact.
   - For visual/design learning, require rendered artifact evidence such as PNG
     exports, contact sheets, review reports, or user-visible feedback.
   - For memory, workflow, sync, recovery, or runtime learning, write an
     authority map and observability probe list before promotion. Name the
     authoritative source, runtime mirror, generated artifact, session log,
     Git state, and validation command separately; mark which items are truth
     and which are only evidence or rebuildable views.
   - Separate three validation levels:
     - artifact validation: the changed skill/file is syntactically valid and
       loaded in runtime;
     - learning validation: the mechanism produces better behavior on a
       realistic scenario;
     - transfer validation: the mechanism helps on a different source or task
       without reusing the original source's surface style.
   - Use an after-action review shape for real trials: intended result, actual
     result, difference, cause, and next rule or scenario.
   - Use a double-loop check for high-impact lessons: identify whether the
     lesson changes only execution tactics or also changes the assumptions,
     objectives, or source-of-truth model behind the workflow.
   - Use a deliberate-practice check before claiming improvement: the scenario
     should have a specific target, observable feedback, repeated attempt or
     comparison, and a narrower next drill.
   - For design, deck, UI, or user-facing workflow lessons, include either a
     representative task walkthrough, a heuristic review against explicit
     criteria, or user/reviewer feedback. Screenshots alone are useful
     artifact evidence, but they are not by themselves proof that the learned
     workflow helps the intended audience.
6. **Promotion decision**
   - Promote only mechanisms that reduce a named failure mode and map cleanly to
     the right layer.
   - Keep speculative mechanisms as TODOs or future scenarios.
   - Update third-party notices when public workflow changes were shaped by a
     studied public source.

## Minimal Deep Study Report

```text
Deep study:
Depth question:
Sources and license:
Boundary flags:
Current failure mode:
Mechanism matrix:
Stage gates:
Source materials and degradation:
Source of truth:
Authority map:
Observability hooks:
Observability probes:
Parameter surface:
Alternative generation:
Review loop:
Learning effectiveness test:
Assumption change:
Pre-mortem risks:
Mechanisms promoted:
Mechanisms deferred:
Validation scenarios:
Evidence:
Decision:
Next patch:
```

## Exemplar Skill Lens

When studying 2-3 excellent skills, avoid ranking them by polish alone. Look
for mechanisms that reduce local failure modes:

- **Trigger precision:** the description and router make the skill load for the
  right tasks without broad always-on context.
- **Default path and fallback boundary:** the skill names the normal path,
  fallback path, and the condition for switching.
- **Deterministic helper boundary:** fragile repeated work moves to scripts or
  validators instead of being hand-rewritten each run.
- **Artifact policy:** generated outputs, temporary files, and final project
  assets have a clear location and handoff rule.
- **Forward-testing:** the skill is tested on realistic tasks with minimal
  leaked context, and promotion depends on observable behavior.
- **License and exposure boundary:** the learning round records whether it used
  ideas only or copied compatible material.

## Huashu-Style Design Source Lens

Huashu Design is a useful example of why deep study exists. A normal learning
round can identify its visual anti-drift protocol. A deep pass should go
further and ask how the source turns design quality into a system:

- fact verification before design assumptions;
- design context and required asset inventory before styling;
- honest placeholders and early user checkpoints before full execution;
- multiple visible directions for vague briefs instead of one generic answer;
- parameterized variations only where they test meaningful decisions;
- rendered or exported artifacts as evidence;
- expert review dimensions and platform/use-case fit before handoff.

For this type of source, copy none of the prompt text, style library prose,
demo HTML, screenshots, audio, or assets. Learn only the protocol structure and
reimplement local checks in q-workflow language.
