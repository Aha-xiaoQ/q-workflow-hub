# Skill Lifecycle Standard

Use this reference before creating, upgrading, stabilizing, publishing, or significantly changing q-workflow skills. It is the lifecycle layer above `create-skill.md`, `update-skill.md`, `review-skill.md`, naming migration, and the skill taxonomy schema.

## Why This Exists

Some useful skills were created before the current q-workflow standards existed. Do not judge those skills as bad only because they lack newer structure. Treat them as legacy-compatible assets that need incremental uplift, evidence, and compatibility notes before a stable team release.

The goal is a stable skill system that remains easy to use:

- old skills stay recoverable;
- new skills start with the right metadata and validation gates;
- lessons are absorbed only after evidence;
- compatibility and breaking changes are explicit;
- release candidates are auditable by another agent or colleague.

## Lifecycle States

Use these states in the portfolio inventory, release notes, or audit reports. Do not put them in platform frontmatter unless the platform supports them.

- `candidate`: useful idea or early skill; not default for colleagues.
- `pilot`: usable in bounded internal work with explicit validation.
- `stable`: default route validated by scenarios, real use, and source/runtime checks.
- `deprecated`: retained for compatibility; avoid new work and name the replacement.
- `archived`: historical evidence only; not an active route.

A skill is not `stable` because it exists or validates syntactically. It needs evidence.

## Stable Release Bar

Before a skill is included in a colleague-facing stable bundle, require:

1. **Trigger clarity**: frontmatter description has concrete `Use when` intent and 3-7 practical aliases in the portfolio record or docs.
2. **Progressive disclosure**: `SKILL.md` routes; long procedures live in `workflows/` or `references/`.
3. **Taxonomy record**: category, variant, publish profile, source of truth, runtime paths, risk label, output contract, and validation gate are recorded in an inventory, audit, or metadata file.
4. **Compatibility note**: old names, aliases, behavior changes, and deprecations are classified.
5. **Validation evidence**: `quick_validate.py` plus at least one realistic usage scenario; add domain checks such as visual review, py_compile, hardware-safe dry run, freshness comparison, encoding guard, or public scan when relevant.
6. **Source/runtime freshness and sync**: source, runtime, public/company counterpart, and `agents/openai.yaml` are compared before writing, the chosen baseline is recorded, sync is checked after propagation, and deferred surfaces have reasons.
7. **Change record**: release notes or changelog state what changed, why, compatibility impact, validation, and residual risk.
8. **User-facing handoff**: a colleague can discover the entry point, know required inputs, and recover from common failure modes without hidden maintainer knowledge.
9. **Expert review evidence**: high-impact lifecycle, taxonomy, routing, compatibility, source/runtime/public sync, or team-release changes have pre-review and post-review evidence. A colleague-facing stable bundle also needs a Usability Validator pass or an explicit deferred reason.
10. **Hard-gate closure**: every applicable hard gate or executable gate from `rule-hardness-ladder.md` is passed, intentionally waived with residual risk, or recorded as a release blocker.

## Public/Company Variant Promotion

For skills that exist in both public and company variants, classify each change
before promotion:

- `generic-rule`: synchronize both variants and runtime mirrors.
- `public-safe-promotion`: rewrite company/private wording into generic
  behavior, then scan public surfaces before release.
- `variant-policy`: keep only brand, template, classification, private asset,
  or audience-specific onboarding differences, with a file-level reason.
- `blocked-drift`: record owner, reason, review date, and next action before
  ending the work round.

Do not promote a broad directory-level `counterpart-review` as a release waiver.
Core workflow, lifecycle, validation, recovery, and test behavior need file-level
evidence that the difference is intentional or synchronized.

## Legacy Skill Uplift

When reviewing a skill created before current standards:

1. Classify it first: active, project-local, external/tool, deprecated, or archive.
2. Preserve working trigger behavior unless evidence shows it is unsafe or confusing.
3. Add the smallest missing structure: usually taxonomy record, validation cue, output contract, composition boundary note, or compatibility note.
4. Avoid rewriting the whole skill just to match newer style.
5. If the skill has no source of truth or unclear runtime origin, record that as a release blocker or residual risk.
6. If the skill is external or hardware/tool-oriented, allow a narrower standard: frontmatter, category, risk label, validation gate, and handoff notes may be enough.

## Incremental Update Classes

Classify each skill change before editing:

- `patch`: wording, trigger alias, validation note, report link, or bug fix that preserves behavior.
- `minor`: new workflow, new validation gate, new supported input, or backward-compatible capability.
- `major`: renamed skill, removed alias, changed default route, changed output contract, changed safety/risk posture, public/company boundary shift, or incompatible behavior.

Use the class to choose validation:

- `patch`: targeted diff/readback, quick_validate, and one route smoke test when behavior changed.
- `minor`: patch checks plus one realistic scenario, pre-edit freshness gate when multiple surfaces exist, and source/runtime mirror check.
- `major`: minor checks plus migration notes, compatibility/deprecation decision, counterpart audit, freshness and encoding evidence, Pre/Post Expert Review Gate when high-impact, and release-readiness review.

## Sedimentation Absorption Gate

A user correction, failed review, or useful lesson should not automatically become a top-level rule. Before absorbing a lesson into a skill:

1. Name the failure mode it prevents.
2. Decide the correct layer: profile, router, workflow, reference, script, validation scenario, project state, TODO, or report only.
3. State the rule shape: trigger, goal, strength, hardness, loading layer, do, avoid, and validation.
4. Check whether the lesson is one-off, project-specific, company-specific, public-safe, or generally reusable.
5. Run at least one different scenario from the original failure when the rule affects routing, default behavior, or a hard gate.
6. Update source and runtime mirrors or record why propagation is deferred.
7. Record the promotion decision: `promote`, `pilot`, `defer`, or `reject`.

Absorption is incomplete if the lesson only appears in chat or a report and future sessions cannot find it through the normal routing path. A hard rule is also incomplete if it lacks a blocked outcome, check method, repair path, waiver rule, and scope.

## Isolated Reproducibility Gate

Use this hard gate only when a skill is claimed to be portable to a fresh
agent or colleague, when a cold-start result supports `pilot` / `stable`
promotion, or when the handoff says the skill alone can reproduce the learned
capability. It does not run for every ordinary task or private draft.

- **Trigger:** a claim of fresh-agent discoverability, skill-only execution,
  portable/team-ready handoff, or lifecycle promotion supported by cold-start
  evidence.
- **Must:** give a new agent a materially different scenario in a fresh
  context; preserve the exact prompt, allowed inputs, actual file/tool access
  trace, artifact/process manifest, and original independent reviewer packet;
  report `artifact`, `process`, and `isolated reproducibility` as separate
  verdicts. The final domain reviewer must not have created the artifact or
  seen the creator's verdict/iteration narrative before its blind decision.
- **Discoverability versus executability:** a prompt that names the skill can
  prove only executability and transfer. A discoverability claim needs a
  natural user-intent prompt that does not name the skill or its internal
  workflow. Record which claim the scenario actually tested.
- **Blocks:** `isolated reproducibility PASS`, portable/team-ready claims, and
  promotion evidence that depends on the cold-start result while any required
  packet is missing or any applicable domain gate rejects the artifact.
  Deterministic regeneration of an existing script proves artifact
  determinism only; it cannot substitute for skill reproducibility.
- **Check:** inspect one compact evidence packet containing environment/agent
  identity, exact prompt, access trace, outputs, process evidence, independent
  raw review, and the three verdicts. For broad or stable claims, repeat with
  different tasks and agents rather than scoring one success as mastery.
- **Repair:** return a rejected artifact to the same isolated creator with the
  independent findings; the parent must not secretly repair it. Patch the
  skill only when evidence shows a rule, route, loading, or fallback gap. If
  the rule was loaded but ignored, repair execution or reviewer independence
  and rerun the failed scenario.
- **Waiver:** the user may waive the cold-start cost for a local experiment,
  but the result remains `unproven candidate` and cannot support portable,
  team-ready, or stable claims.
- **Scope:** validate general mechanisms, decision order, fallback, and gates;
  do not package third-party assets or promote task-specific coordinates,
  contours, palettes, prompts, or recognizable visual answers into the skill.

## Compatibility And Deprecation

For any rename, alias change, output contract change, or default behavior change:

- keep old prompts recoverable through documentation, mapping, or a temporary runtime alias;
- mark whether the old path is `compatible`, `deprecated`, `removed`, or `archive-only`;
- provide a replacement route and migration note;
- keep historical notes, but remove old names from active published skill lists unless a documented compatibility exception exists;
- never leave two full active skills as competing sources of truth.

Deprecation must include a review trigger for removal. If no removal date is known, record the condition that would make retirement safe.

## Documentation Split

Use documentation layers deliberately:

- `SKILL.md`: trigger, first-read router, default behavior, safety pointers.
- `workflows/`: step-by-step procedures for doing work.
- `references/`: standards, schemas, policies, rubrics, compatibility, and background explanation.
- `scripts/`: deterministic checks, generators, audits, and repair tools.
- `reports/`: evidence from a specific run, not reusable instructions.
- `TODO` or work items: future work that is not yet stable behavior.

Do not promote a long report into `SKILL.md`. Extract the mechanism, not the history.

## New Skill Creation Preflight

New top-level skill creation is a lifecycle change, not just a file scaffold. Before creating or scaffolding files for a new top-level skill, follow the `workflows/create-skill.md` Discovery And Approval Gate:

1. justify why a new skill is the correct durable layer;
2. run `q-skill-pattern-learning` to learn mechanisms from internal/external skills or record a narrow waiver;
3. run `q-research-discovery` / Source Scout for official docs, current facts, public examples, tools, APIs, install paths, or uncertain best practices;
4. draft the plan before implementation;
5. run expert pre-review with Workflow Distiller as the default owner and additional experts by domain;
6. present the plan and expert findings to the user;
7. wait for explicit user approval before scaffolding, unless the current thread contains an explicit approval/preflight waiver.

Patch-level typo, link, or deterministic metadata repairs may skip this preflight when behavior and routing are unchanged. Tiny local-only helpers may skip research only when they do not create reusable skill behavior; record the scope and skip reason. Do not use "local-only" or "do it now" as a blanket bypass.

Validation for this gate includes readback/diff check, metadata validation, source/runtime/public/company sync check or deferred reason, public/private scan when variants are touched, encoding guard when localized text is edited, and one realistic `make a skill` scenario proving the gate fires before scaffolding.

### Invocation And Closure Regression Gate

- **Trigger:** a user explicitly asks to create, rename, standardize, audit, or
  sediment a q-workflow skill, or a previous loop missed the applicable skill
  route, review gate, or source/runtime authority check.
- **Must:** load the applicable creation or review workflow before edits; record
  source authority, lifecycle, validation evidence, and required reviewer
  disposition before calling the work closed.
- **Blocks:** a `ready`, `stable`, `migrated`, `installed`, or colleague-ready
  claim while the route, source/runtime classification, required review, or
  validation record is missing.
- **Check:** replay one creation or migration scenario; run the portfolio and
  source/runtime audits; verify an independent review log names accepted,
  deferred, or rejected findings.
- **Repair:** stop the closure claim, run the missing route/review, add the
  smallest durable record, then rerun the evidence checks.
- **Waiver:** only the user may waive a non-safety local check; record the
  waiver, reason, and residual risk. Public/private, license, and authority
  gaps are not waivable.
- **Scope:** q-workflow skill lifecycle work only. Do not apply it to ordinary
  project code edits or small answer-only requests.

### Context Budget And Recursion Stop

Preflight is a gate, not an invitation to load every related skill. Classify the
new-skill request as `quick`, `standard`, or `release` before downstream loading:

- `quick`: behavior and routing are unchanged; skip learning/research/expert
  ceremony and run targeted validation only.
- `standard`: default candidate/pilot path; use compact prior-art and research
  briefs, one bounded Workflow Distiller review, and ask the user before
  scaffolding.
- `release`: stable/public/team/high-risk path; run fuller research, expert
  review, sync, compatibility, and release gates.

No preflight sub-skill may recursively invoke `q-skill-creation` or promote a
new durable rule while evaluating a proposed new skill. If the learning,
research, or expert pass discovers a separate improvement, capture it as a
follow-up TODO/work item unless Xiao Q explicitly approves expanding the current
scope. This preserves progressive disclosure and prevents prompt-chain bloat.

## Pre/Post Expert Review Gate

For high-impact skill-system changes, use expert review both before and after the main edit. This is a supervision mechanism for the main agent and a learning loop for the expert roster.

Pre-review is required before editing when the change affects any of these:

- stable colleague-facing release criteria;
- skill lifecycle, taxonomy, naming, compatibility, or public/company sync policy;
- default routing, trigger semantics, activation/risk posture, or output contract for a core skill;
- broad source/runtime/public propagation;
- retirement or deprecation of active skills or aliases;
- a repeated user-found workflow miss being promoted into durable rules.

Post-review is required before closure for the same high-impact changes, and should check:

- whether the implemented patch matches the pre-review decision;
- formatting, numbering, links, and progressive-disclosure placement;
- compatibility and release-note completeness;
- validation evidence and residual risk;
- whether the expert profile itself gained a reusable lesson.

Required ownership:

- `Workflow Distiller (沉炼)` is the default pre-review and post-review owner for major lifecycle, taxonomy, compatibility, routing, release-foundation, or sedimentation-rule changes. It checks whether to change the skill at all, which layer should own the rule, and the minimum viable patch.
- `Doc Architect (文构)` reviews standard structure, schemas, release reports, and documentation clarity when the artifact is a formal standard or colleague-facing report.
- `Usability Validator (验用)` is required before a colleague-facing stable v1 bundle, public/team package, or install/onboarding path is called ready. It checks whether a new colleague can discover the entry point, understand the workflow, and recover from common misses.
- `Code Auditor (码鉴)` is required when scripts, validation tools, or code paths change.
- Add a domain expert only when the changed skill is visual, HTML, PPT, hardware, research, or another specialized domain.
Lightweight exceptions:

- Patch-level typo fixes, obvious link corrections, and deterministic metadata repairs do not require formal pre/post review. Run targeted validation and record that the change was patch-level.
- If pre-review was skipped on a change that should have had it, do a post-review as soon as the miss is noticed, record the protocol defect, and patch this lifecycle rule or the expert workflow if needed.

Expert experience capture:

- Save expert reports or integration notes for major changes.
- Record which findings were accepted, rejected, or deferred.
- If an expert catches a new class of miss, add a validation scenario or expert-profile lesson instead of leaving it only in chat.

## Release Readiness Checklist

For a stable bundle or colleague handoff, produce a release report with:

- scope and included skill list;
- excluded/deprecated/archive skills and why;
- taxonomy/inventory status;
- compatibility changes and migration notes;
- validation commands and scenario results;
- encoding/public/private scan results;
- known limitations and unsupported workflows;
- quick-start prompts for the top user tasks;
- rollback/recovery plan;
- commit IDs and push status.

## Changelog And Decision Records

Keep release notes human-readable and chronological. For significant design choices, write a short decision record:

- decision;
- context;
- alternatives considered;
- consequences;
- validation evidence;
- revisit trigger.

This keeps standards from becoming unexplained rules.

## Anti-Patterns

- Rewriting old working skills wholesale to satisfy a new schema.
- Declaring a skill stable after only metadata validation.
- Copying an external skill's structure without validating the mechanism locally.
- Adding every lesson to always-loaded `SKILL.md`.
- Treating `status` as a badge instead of evidence-backed maturity.
- Letting source/runtime/public/company variants drift silently.
- Editing or syncing a skill before choosing the freshest valid source/runtime/hub baseline.
- Copying terminal mojibake or suspicious localized text into durable files without UTF-8 readback or encoding guard.
- Treating post-review as a substitute for pre-review without recording the process defect.
- Breaking old prompts without a compatibility path.
- Merging a creator and reviewer because they often run sequentially.
- Splitting a rare checklist into a top-level skill without standalone trigger,
  output contract, or validation value.
