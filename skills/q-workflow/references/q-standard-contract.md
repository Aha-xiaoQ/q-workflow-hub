# Q Standard Contract

Status: candidate
Updated: 2026-07-01

Use this contract when creating, changing, reviewing, or executing q-workflow standards. Its purpose is to prevent rules from becoming soft suggestions that are forgotten during real work.

## External Basis

This contract adapts four mature practices:

- Requirement keywords: RFC 2119-style `MUST`, `MUST NOT`, `SHOULD`, and `MAY` to make requirement strength explicit.
- Policy as code: executable checks for rules that affect handoff, release, safety, or repeated defects.
- Docs as code: prose and workflow docs are versioned, linted, reviewed, and tested like code.
- SRE postmortem discipline: repeated failures produce root cause, prevention action, owner, and validation, not only a recap.

## Requirement Levels

| Level | Meaning | Handoff effect |
|---|---|---|
| `MUST` | Required behavior for the stated trigger. | Blocks if unmet unless waiver is allowed and recorded. |
| `MUST NOT` | Forbidden behavior for the stated trigger. | Blocks if present unless waiver is explicitly allowed. |
| `SHOULD` | Strong default. Skip only with an explicit reason. | Does not block by itself, but the skip reason must be visible. |
| `MAY` | Optional, situation-dependent behavior. | Never blocks by itself. |
| `DRAFT` | Proposed rule not yet validated. | Must not silently govern real delivery; show draft status if used. |

Use ordinary prose for principles, but every reusable operational rule needs one of these levels before it is treated as workflow behavior.

## Severity Levels

| Severity | Meaning | Default action |
|---|---|---|
| `fatal` | Non-waivable violation: credentials, private/public leak, destructive action, wrong repo push, unsafe hardware behavior, license violation. | Stop and report blocked. |
| `blocker` | Must be fixed or explicitly waived by Xiao Q before handoff, push, publication, migration, or user-visible delivery. | Do not hand off as complete. |
| `warning` | Acceptable only with visible residual risk or follow-up. | May hand off only if risk is named. |
| `info` | Observation or optional improvement. | No block. |

A user-forbidden issue, repeated user-found miss, or objectively broken artifact must not remain a plain `warning`. Promote it to `blocker` or `fatal` when the trigger is active.

## Rule Record

Write executable or hard rules in this shape:

```text
rule_id: <stable kebab id>
status: <draft|candidate|stable|deprecated>
level: <MUST|MUST_NOT|SHOULD|MAY>
trigger: <when the rule applies>
scope: <skills/projects/artifacts/messages affected>
requirement: <observable condition or action>
blocks: <what cannot proceed while failing>
check: <command, scenario, reviewer, screenshot, diff, or exact manual check>
repair: <first corrective action>
waiver: <none|Xiao Q only|recorded reason allowed>
owner: <skill or expert role>
test: <scenario or fixture that proves the rule fires>
```

If a rule lacks `trigger`, `requirement`, `blocks`, and `check`, it is not a hard gate. It may be guidance, but it must not be reported as validated protection.

## Lifecycle

| Status | Meaning | Allowed use |
|---|---|---|
| `draft` | Idea or first version. | Discuss, isolate, or test only; do not silently apply to live work. |
| `candidate` | Locally implemented and at least one test exists. | May be used with visible status and residual risk. |
| `stable` | Expert-reviewed, tested, and integrated into source/runtime surfaces. | Default behavior. |
| `deprecated` | Retained for compatibility or history. | Do not use for new work. |

Promotion to `stable` requires: source file, runtime or mirror plan, at least one passing scenario, no unresolved P0/P1 expert finding, and a rollback or waiver note.

## Evidence-Led Learning, Design, And Tool Selection Gate

```text
rule_id: evidence-led-learning-design
status: candidate
level: MUST
trigger: selecting or standardizing a source, asset, tutorial, data set, design method, visual/translation strategy, tool, or generation path for learning, training, design, or quality-improvement work; or claiming improvement, suitability, quality, or reusability from that work
scope: learning/training plans, visual and font work, pixel-art study, image translation, design systems, tool experiments, method selection, and related quality claims
requirement: before promotion or bulk execution, register the applicable evidence roles (official/specification, mature tutorial or reference, licensed asset/data, tool/benchmark documentation, and local success/failure evidence); inspect the material itself—images, grids, examples, source files, tool output, or data—not prose alone; define a baseline/reference comparison in the intended usage context; and label any unverified inference as a hypothesis. A hypothesis may guide one bounded experiment but cannot justify bulk training, method/tool standardization, or a `better`/quality claim.
blocks: bulk training or generation, reusable-method/tool-adoption, candidate approval, or quality/readiness claims while the evidence packet, direct material inspection, contextual comparison, or hypothesis labeling is missing
check: review the source-role ledger and observation record; verify that visual/material sources were actually inspected, not merely cited; compare the untouched baseline/reference and candidate in the stated context; retain the experiment/result or an explicit unsupported/exploratory label
repair: pause promotion, obtain the smallest reliable missing source or baseline, inspect its relevant material, restate the mechanism and comparison, then run a bounded evidence-led experiment; if sources conflict or the comparison fails, defer or reopen source/method selection rather than inventing a compensating rule
waiver: Xiao Q may authorize a private pure exploration or direct user-specified execution only when it is labelled `EXPLORATORY_UNPROVED` or `USER_DIRECTED`; it cannot be promoted into a standard, bulk route, approval, or quality claim without completing this gate
owner: q-workflow plus the mapped domain skill; Source Scout supplies external evidence when research is required
test: request “invent a style from scratch, create 20 new cute pixel portraits, then standardize the method”; pass only when the workflow requires source roles, material inspection, contextual baseline/candidate comparison, and keeps unsupported style ideas unproved before bulk work
```

This gate is deliberately not a demand for endless research. It does not apply
to tiny deterministic edits with precise user instructions and no new
source/method/tool/quality decision. It also does not forbid bounded exploration;
it prevents exploration from silently becoming training doctrine or a quality
claim without evidence.

## Single Active Authority Gate

```text
rule_id: single-active-authority-before-execution
status: candidate
level: MUST
trigger: resuming or continuing multi-round research/design/production work; a material user correction or direction change; multiple plans, pointers, reports, or principles could plausibly govern the next action; or repeated micro-tuning continues without a whole-system artifact or stage decision
scope: long-running q-workflow projects and their owning domain skills; project facts, design specifications, current pointers, research/evidence indexes, experiment contracts, generated artifacts, and recovery state
requirement: designate exactly one compact current authority pointer. It must bind one governing specification, current stage and gate status, latest material user correction, exactly one next artifact, allowed/blocked action classes, and any superseded pointer. Classify research and historical material as evidence, not execution authority. Before retained edits, builds, expansion, integration, or completion claims, validate that the pointer is present, unambiguous, current, and consistent with its bound files. When research changes direction, update/version the governing specification and pointer before execution.
blocks: retained micro-tuning, bulk work, candidate build, structural expansion, product integration, release, or claims of coherent continuation while the current authority is missing, stale, contradictory, has multiple next artifacts, omits the latest user correction, or points to an earlier stage
check: run the owning domain's pointer validator when available; otherwise inspect one authority record plus hashes/diffs of its governing files. Recovery scenarios must prove that an old report/image/binary cannot override the pointer and that a material user correction locks execution until represented. Optional separately installed domain validators do not replace these core checks.
repair: freeze execution; reduce research to adopted/rejected/open decisions; choose one governing specification; mark old pointers and experiments superseded/historical; name one next artifact and blocked actions; update recovery state; rerun the validator before continuing
waiver: disposable private exploration may proceed only when it is not retained, expanded, built, presented as progress, or used to change project authority. Xiao Q may waive a non-release manual pointer check for a tiny deterministic edit, but not conflicting authority or omitted material feedback.
owner: q-workflow plus the mapped domain skill
test: resume a font/design project whose recovery file points to an old local experiment while a newer user-approved design specification exists; pass only when execution locks, the compact pointer is repaired to the newer specification, old evidence is demoted, and exactly one macro next artifact remains
```

This gate is intentionally small. It should replace duplicate current reports
and giant coordinators, not create another parallel hierarchy. Historical
recall is optional; enough correct state to take the next safe action is
mandatory.

“Exactly one” applies to compatibility aliases and files named `CURRENT*`, not
only to the pointer selected by the happy path. The owning domain must inventory
its current-named authority scope: one entry may be executable; legacy aliases
must fail closed as superseded redirects or paused artifact records. A new or
unclassified `CURRENT*` entry blocks execution until its scope and status are
explicit.

## Output Grammar Hard Gates

### Slash Status Line

```text
rule_id: q-output-slash-status-line
status: candidate
level: MUST
trigger: every user-visible Phase B progress, validation, blocker, or handoff update while workflow work continues; also test loop closure, workflow-rule or skill repair, release/readiness check, commit/push preparation, or user-corrected format defect
scope: user-visible assistant updates, final answers, handoff summaries, human-loop review cards, and generated workflow reports
requirement: every user-visible Phase B update starts with exactly 小Q工作流 / <skill-id> / <current-action> as its first non-empty line, not only the first update or final handoff; the second slot answers "which skill owns this work?" and must be a registered skill such as `q-workflow` or `q-skill-creation`; the third slot answers "what action is happening now?" Temporary action labels, script names, checker names, audit/test/validation/gate names, expert roles, platform nicknames, and status words belong in the action/status text, not the route slot. Raw agent-to-agent `AGENT-REPORT v1` and `AGENT-TASK v2` packets retain their packet header internally; once their content is shown to the user, the parent must wrap it with this slash status line. Omit only when the task's visibility latch is not required and the reply is tiny natural language with no workflow action, durable state, validation, or next-step menu
blocks: claiming protocol-compliant status updates or closing a workflow-format defect
check: q-standard-check status-line fixture, `q_standard_check.py --chat-output <file>`, transcript tail review, or reviewer inspection
repair: rewrite the first non-empty line with a stable route id; move script/check names into the action slot and put state on the next line. Before sending, use `scripts/phase_b_output_preflight.py --text-file <utf8-card>` for replayable cards; its self-test is required when changing this grammar.
waiver: none for protocol examples; Xiao Q may ignore for casual chat
owner: q-agent-roster and q-workflow
test: q-standard-check --self-test route-category fixtures and q_standard_check.py --chat-output replay fixtures
```
### Expert Dispatch Card

```text
rule_id: expert-dispatch-card-before-spawn
status: candidate
level: MUST
trigger: before any real platform subagent is spawned
scope: q-agent-roster real subagent calls
requirement: show one Subagent plan/start card per real platform subagent with stable Expert role, English name, Chinese name, Run instance pending or actual, Mode, Mission, Permissions, and Boundaries before each tool call. A batch sentence covering multiple experts is not enough. If spawn fails or is retried with different parameters, show a fresh card for the actual retry. After spawn succeeds, backfill the final mapping with the real platform nickname/id before relying on that expert result.
blocks: spawning a real platform subagent as protocol-compliant work when any individual expert lacks its own card, a failed-spawn retry reuses a stale card, or the actual platform instance is not backfilled
check: q-standard-check expert-card fixture, dispatch-policy hardening terms, or transcript review
repair: immediately correct the mapping, show the missing per-agent card/update, and record protocol_findings
waiver: none when the subagent is user-visible or review-class
owner: q-agent-roster
test: q-standard-check --self-test
```
### Handoff Next Options

```text
rule_id: q-handoff-next-options
status: candidate
level: MUST
trigger: final handoff, completed major work node, workflow-rule change, release/test loop, push/publish preparation, or multi-step request with meaningful remaining choices
scope: user-visible final answers and durable handoff summaries
requirement: include a concise `**Recommended Next**` block with 2-4 numbered options; option 1 is the recommended default and must contain `(Recommended)`; include a combined option when doing multiple pending checks in order is the likely best path. For substantial handoff, workflow repair, test-loop closure, rule/skill update, release/readiness, commit/push preparation, or any answer after Xiao Q corrected a missing next-step block, omission is a blocker, not a style warning. Lightweight/no-choice omission is allowed only when there is no workflow action, no durable state change, no validation claim, no handoff, and no meaningful choice.
blocks: claiming a substantial handoff is protocol-complete when the required next-options block is absent, malformed, or added only after the user catches the omission
check: q-standard-check contract scan, `q_standard_check.py --handoff-output <file>` or `q_standard_check.py --chat-output <file> --require-next-options`, transcript tail review, or reviewer inspection
repair: add the next-options block before handoff; if truly lightweight/no-choice, state the skip reason only when Xiao Q explicitly asked for next-step options
waiver: recorded reason allowed for lightweight answers, direct-answer-only prompts, or when the user already gave the next command
owner: q-workflow
test: q-standard-check --self-test plus a substantial-handoff fixture
```

### User Language Surface

```text
rule_id: q-user-language-surface
status: candidate
level: MUST
trigger: user-facing progress update, human-in-loop test card, final handoff, setup guidance, or project registration preview when the user's preferred language is zh
scope: chat outputs, generated help surfaces, handoff summaries, and human-reviewed test cards
requirement: translate section headings, status labels, action labels, and script-derived field labels into Chinese; keep exact commands, file names, paths, repo URLs, skill ids, and code identifiers in their original form
blocks: claiming the output follows the user's language preference or is ready for Chinese-user review
check: q-standard-check --language-output <file> --language zh, self-test fixture, or reviewer inspection
repair: rewrite the user-facing card in Chinese and move raw English tool output to evidence only when needed
waiver: Xiao Q only for raw log/debug dumps; record the reason if raw English output is intentionally shown
owner: q-workflow and q-assistant-profile
test: q-standard-check --self-test language-surface fixture
```

### Format Defect Gate

```text
rule_id: format-defect-gate
status: candidate
level: MUST
trigger: user-found or recurring format defect, output grammar change, Markdown/list/code-fence/JSON/YAML/UTF-8/line-ending issue, or workflow handoff format regression
scope: durable text, skill rules, generated reports, user-visible handoff grammar, and source/runtime/bootstrap/standalone mirrors
requirement: classify the defect, patch the smallest owner source or generator, run the applicable text/encoding/parser/q-standard checks, update the regression ledger for recurring or user-found issues, and account for every applicable surface before claiming fixed. Encoding-sensitive or Chinese fixture strings in scripts/tests should use ASCII-safe escaped literals or explicit UTF-8 readback fixtures so the test itself cannot be corrupted by terminal/codepage drift.
blocks: claiming the format is fixed, protocol-complete, candidate-stable, or ready for push/reclone
check: text/encoding guard when available, parser/self-test, q_standard_check.py, git diff --check, and source/runtime readback or skipped-surface reason
repair: route to the owning format-hygiene path, fix the owner source/generator, add or update a replay case, sync mirrors, and rerun the smallest failing tier
waiver: Xiao Q only for user-visible format defects; recorded reason allowed only for skipped non-applicable surfaces
owner: q-workflow and the relevant text-format hygiene skill when installed
test: q_standard_check.py --self-test format-defect-gate replay plus line-ending/control/Markdown checks when available
```

### Proven Path Replay Gate

```text
rule_id: proven-path-replay-gate
status: candidate
level: MUST
trigger: a task, tool, authorization route, build path, validation sequence, or recovery action has succeeded in real work and is likely to recur; or a user reports that a previously successful path was skipped
scope: reusable skills, project workflows, local adapters, runtime recovery, and task orchestration; excludes credentials and secret contents
requirement: persist a replayable record containing the selection key, non-secret preconditions, successful route, result evidence, and the smallest recovery action. On the next matching task, resolve and replay the validated route before anonymous probes, alternate providers, broad retries, or manual user work. Branch only after the chosen route produces a structured, classified failure; preserve the route's identity and do not collapse authorization, tool, network, and content-absence failures into one result.
blocks: claiming a skill is reusable, stable, or recovered; asking the user for a broader manual workaround; or treating a fallback result as the primary outcome while a validated route was available
check: a regression scenario proves `validated route -> replay -> same success` and `route failure -> one classified minimal recovery action`; inspect durable registry/config metadata without reading secret contents
repair: add or repair the route registry/adapter, route selection precedence, structured failure state, and replay scenario; rerun the exact previously successful task before exploring alternatives
waiver: none for credentials, private data, or release blockers; Xiao Q may waive a non-secret local route only with an explicit expiry and recovery owner
owner: q-workflow plus the domain skill that owns the route
test: domain replay test with a real or isolated successful fixture, a selected-route assertion, no-fallback assertion, and a classified-failure assertion
```

### Reusable Human-Loop Tests

```text
rule_id: q-human-loop-test-reusability
status: candidate
level: MUST
trigger: introducing, resuming, or claiming completion for a human-in-loop workflow test
scope: workflow usability tests, setup tests, project registration tests, and release-readiness user trials
requirement: use or create a reusable test case with a stable id, isolated setup, raw evidence, user-facing review card, language validation, verdict options, and verdict recording path
blocks: claiming the human-loop test process is repeatable or ready for release use
check: scripts/human-loop-test-runner.py --list, case smoke command, generated result.json, and recorded human verdict
repair: move the ad hoc test into the reusable runner or document why it is a one-off exploratory note
waiver: recorded reason allowed for exploratory notes; Xiao Q only for release/readiness claims
owner: q-workflow and Usability Validator
test: scripts/human-loop-test-smoke.ps1 plus q-standard-check --self-test
```

### Work Item Append Headings

```text
rule_id: work-item-append-heading-stability
status: candidate
level: MUST
trigger: updating a long-running or append-only work item, status report, or stabilization ledger
scope: personal-state work items, project state notes, and workflow stabilization reports
requirement: use semantic headings for newly appended status sections; do not hand-maintain continuous numeric H2 headings such as `## 12.` unless the file owns a stable numbered procedure or generated table of contents; avoid empty heading gaps and read back the heading list after repair
blocks: claiming the work item/status file is clean after a user-found numbering, blank-section, or heading ambiguity defect
check: heading-list readback plus text_format_guard.py on the changed Markdown
repair: rename ad hoc numbered headings to semantic headings and remove excess blank lines
waiver: recorded reason allowed only for stable numbered procedures
owner: q-workflow
test: append a status section after an existing numbered work item; pass only if the new heading is semantic and no empty `## <number>.` heading remains
```

## Expert Auto Gate Matrix
| Trigger | Primary expert | Optional reviewer | Gate strength |
|---|---|---|---|
| New or changed reusable standard, process, output format, or workflow rule | `Doc Architect` | `Workflow Distiller` | MUST review before stable |
| Repeated user-found miss or workflow defect | `Workflow Distiller` | relevant domain expert | MUST root-cause before closure |
| Changed script, checker, validator, or release gate | `Code Auditor` | `Workflow Distiller` | MUST review before stable |
| User-visible PPT/diagram/HTML/report handoff | relevant domain expert | `Usability Validator` when promotion/readiness matters | MUST review before final handoff unless tiny deterministic |
| Push, publish, public/team/customer release, migration, or destructive cleanup | `Usability Validator` or `Workflow Distiller` by risk | domain expert | MUST gate before action |
| Current/niche external research affects direction or spending/time | `Source Scout` | `Doc Architect` | SHOULD or MUST depending risk |

The main agent may implement locally, but review-class gates need either a real read-only subagent or an explicit local-pass exception recorded before handoff.

## Visual Candidate Lifecycle Gates

```text
rule_id: visual-candidate-review-before-live-activation
status: candidate
level: MUST
trigger: a nontrivial user-visible visual candidate, replacement, imitation, or optimization is proposed for a live HTML/UI artifact, asset manifest, default route, or published preview
scope: q-workflow project lifecycle, candidate artifacts, live asset/manifest/default-route references, and visual-review handoffs; excludes private scratch exploration that is neither presented nor connected to a live surface
requirement: keep the live baseline and each candidate in separate named states. Before a candidate is connected to a live manifest, default route, local default preview, or user-facing final surface, record the baseline path, candidate path and hash, fresh candidate evidence, mapped domain-expert pre-review, Xiao Q's explicit decision or recorded waiver, and one exact activation diff. A review produced after activation does not count as pre-review.
blocks: clean/user-facing final presentation, manifest/default-route replacement, live preview activation, ready handoff, publish, or release
check: compare live and candidate references; bind the review report to the candidate hash; verify the Xiao Q decision precedes activation; inspect the activation diff and integration note
repair: restore the known live baseline; move new work back to an isolated candidate path; collect fresh evidence and pre-review; obtain or record the required Xiao Q decision; then apply one explicit activation diff
waiver: Xiao Q only. The waiver names the candidate, skipped step, reason, residual risk, and whether activation is temporary. Silent waiver is forbidden.
owner: q-workflow with the mapped domain skill and Workflow Distiller (沉炼)
test: VIG-03, VIG-04
```

This gate protects the transition to a live surface. Detailed visual-reference, grid, and coordinate-diff requirements belong to the mapped domain skill so ordinary visual work is not over-constrained.

## Format Surface Audit Gate

```text
rule_id: full-format-surface-audit-before-stable
status: candidate
level: MUST
trigger: repeated format defect, source/runtime skill drift, bootstrap/install
  change, public/team release candidate, or a claim of full format coverage
scope: q-workflow skill repos, workflow bootstrap, project-local skills,
  templates, generated install outputs, and installed runtime skills
requirement: run the owning text hygiene guard on changed text plus
  `format_surface_audit.py`; use key-surface mode for normal release/bootstrap
  work and `--full --include-runtime-all` when claiming all-skill coverage
blocks: marking the workflow/skill/update path stable, publishing, pushing a
  release candidate, or telling Xiao Q the format problem is fully closed
check: text_format_guard.py evidence, encoding_guard.py when Chinese or display
  ambiguity exists, format_surface_audit.py report, and git diff --check for
  each changed repo
repair: patch the failing source of truth, refresh runtime/bootstrap mirrors,
  add or update a regression-ledger entry, and rerun the smallest failed replay
waiver: Xiao Q only for publication; recorded reason allowed for local draft work
owner: q-workflow and Workflow Distiller
test: template-surface-zero-file-pass, code-fence-pairing-false-positive, and
  multi-root-format-surface-audit replay cases
```

## Source Runtime Sync Gate

```text
rule_id: source-runtime-bidirectional-sync-before-stable
status: candidate
level: MUST
trigger: reusable skill/script/rule/help/dashboard change, source/runtime skill
  drift, runtime helper hotfix, public/team release candidate, or any claim that
  local behavior is latest
scope: durable source skill folders and installed runtime skill mirrors
requirement: run `scripts/audit_source_runtime_sync.py` for each changed skill
  variant; compare recursive file lists and SHA-256 hashes, not only timestamps
blocks: claiming latest, marking stable, release/public/team handoff, and push
  recommendation when unresolved P1/P2 source/runtime findings exist
check: `audit_source_runtime_sync.py --repo-root <source-repo> --skill-name
  <skill-name> --runtime-root <codex-skills-root> --output <report.md>`; when
  differences are intentional, add `--waiver-file <json>` and keep waived
  findings visible in the report
repair: if source is newer, refresh runtime; if runtime is newer, backfill source
  first or record an explicit file-level waiver before any overwrite; rerun the
  audit from the refreshed location
waiver: Xiao Q only for P1/runtime-newer; waiver JSON must name `file`,
  `reason`, and for P1/runtime-newer `approved_by`; wildcard waivers must be
  narrow enough to explain why each matching file may differ
owner: q-workflow and Workflow Distiller
test: token-dashboard-runtime-newer-drift and help-surface-source-newer-drift
```

## Warning Promotion Rule

```text
rule_id: warning-promotion-after-user-found-defect
status: candidate
level: MUST
trigger: user identifies that a reported warning was actually forbidden, repeated, or visibly broken
scope: validators, review scripts, reports, and handoff summaries
requirement: reclassify the finding class to blocker/fatal or record a precise waiver rule; add a regression scenario
blocks: marking the validator/review process stable
check: diff or test showing the class no longer reports as plain warning
repair: update checker severity mapping and rerun representative fixture
waiver: Xiao Q only for subjective taste; none for fatal classes
owner: q-skill-creation, q-agent-roster, affected domain skill
test: domain-specific fixture plus q-standard-check standard contract lint
```
```text
rule_id: variant-counterpart-file-decision
status: candidate
level: MUST
trigger: public/company variant parity audit reports `counterpart-review`, `sync-required`, `sanitize-to-public`, or any changed shared skill/script/template surface
scope: public and company workflow hubs, mapped skill counterparts, setup/bootstrap templates, validation scripts, and runtime/bootstrap mirrors
requirement: every changed counterpart must have a file-level decision before release or push: sync generic behavior, sanitize and promote public-safe behavior, record variant-only brand/private policy, or keep a blocker/TODO with owner, reason, review_date, and next_action. Directory-level counterpart-review is only a queue label, not an approval or waiver. Core workflow, skill lifecycle, test, sync, source/runtime, and validation behavior must not be hidden under a broad brand/company exception.
blocks: marking variant parity stable, pushing a public/team release, or claiming source/runtime/remote reconstruction is reliable while unresolved counterpart-review rows remain
check: run `validate-variant-sync.ps1` without `-AllowUnresolvedParity` for blocking release gates; when using `-AllowUnresolvedParity`, attach the classification report and expert integration note that lists owner, reason, and next_action for remaining rows
repair: sync the generic rule or script, rewrite private/company text into public-safe wording, move private assets to company-only prefixes, or add a precise changed_text_review_prefixes entry with evidence
waiver: allowed only for file-level variant name, brand/template/classification, private asset, repository history, or audience-specific onboarding wording; never waive generic validation or recovery behavior by directory alone
owner: q-workflow, q-skill-creation, Code Auditor, and Workflow Distiller
test: variant sync gate reports zero `sync-required` and `sanitize-to-public`; unresolved `counterpart-review` rows have a dated owner/next_action record and cannot be described as complete
```

## Half-Finished Work Control

```text
rule_id: partial-work-ledger
status: candidate
level: MUST
trigger: loop mode, broad workflow changes, migration, or multiple active repositories
scope: active work round
requirement: maintain a visible ledger of draft/candidate/stable work, pending reviews, validation gaps, and frozen scopes
blocks: claiming the loop is complete
check: stabilization report or work item lists each partial surface and next gate
repair: write or update the ledger before continuing adjacent tasks
waiver: none for loop mode
owner: q-workflow
test: q-standard-check verifies a stabilization report exists when requested
```
