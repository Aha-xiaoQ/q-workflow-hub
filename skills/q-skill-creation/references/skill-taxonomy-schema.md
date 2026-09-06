# Skill Taxonomy Schema

Use this reference when auditing, creating, reviewing, or migrating a skill portfolio. It standardizes the vocabulary for skill type, status, risk, output, trigger, and source authority without forcing every small skill to carry a large header.

## Design Rule

Keep platform-facing `SKILL.md` frontmatter minimal unless the platform officially supports extra fields. Store portfolio metadata in a catalog, audit report, or optional metadata file first. Promote fields into individual skill files only when they are stable, useful during routing, and validated by tooling.

Lifecycle state and stable release gates are defined in `skill-lifecycle-standard.md`; this file defines the portfolio fields used by that lifecycle.

## Minimal Portfolio Record

```yaml
skill_id: canonical-skill-name
display_name: Human readable name
variant: generic | company | project | runtime | external
category: router | workflow | domain | tool | intake | review | profile | project | orchestration
status: candidate | pilot | stable | deprecated | archived
publish_profile: private | company | public
source_of_truth: path-or-repo
runtime_paths:
  - installed/path
activation_contract:
  - trigger: one concrete user intent
    aliases: [3-7 stable aliases]
    negative_triggers: [phrases that should not trigger this skill]
    tier: Micro | Quick | Project | Deep | Full
    risk_label: allow | ask | deny
    risk_notes: why the risk label applies
    reference: SKILL.md or on-demand reference path
    validation_prompt: one replayable scenario
output_contract:
  chat_summary: what the final answer must include
  file_outputs: expected files or none
  report_path: required | optional | none
  validation_evidence: command, screenshot, report, citation, or explicit not-run reason
dependencies: tools, runtimes, templates, hardware, skills, or none
composition_boundary:
  mode: standalone | pipeline | review_gate | add_on | tool_helper | handoff | internal_reference | none
  upstream: [skill ids, or none]
  downstream: [skill ids, or none]
  merge_split_status: keep_separate | merge_candidate | split_candidate | deprecated_overlap | not_reviewed
  notes: why this boundary is intentional
encoding_guard: required | optional | not-applicable
validation: quick_validate, smoke test, scenario replay, visual review, or other gate
review_ownership:
  pre_review_required: always | conditional | no
  post_review_required: always | conditional | no
  primary_reviewer: expert role or human reviewer
  review_evidence: report path, packet id, PR review, or deferred reason
sync_notes: source/runtime/public/private mirror obligations, freshness baseline, skipped surfaces, and last sync evidence
```


## Reference Ownership

When auditing or writing skill instructions, classify every inline path or tool
reference by owner:

- `local`: file must exist inside the current skill directory.
- `cross-skill`: another named skill owns the file or script.
- `hub`: the repository or personal hub owns the helper outside the skill.
- `asset`: packaged material owned by an asset manifest or README.
- `optional`: allowed only when the phrase states `when available` or a clear
  fallback path.

Do not make every missing-looking `scripts/...` string a blocker. Block only
when a required local path is missing, the owner is unnamed, or the missing file
would break the default workflow. This keeps audits strict on real defects and
light enough for small tasks.

## Field Semantics

- `category` describes the skill's job in the portfolio. It is not a quality score.
- `status` describes maturity and must be backed by validation evidence. Do not use `stable` as a promise without a replayed scenario, real use, or review gate.
- `publish_profile` describes where the skill can safely live. It must not imply that private/company content is public-safe.
- `risk_label` is only `allow`, `ask`, or `deny`. Put detail in `risk_notes` so audits can parse the label.
- `activation_contract` is required for core routers, shortcuts, permission-changing skills, hardware/tool skills, and public/team handoff skills. Lightweight domain skills may keep a shorter Trigger Router if their frontmatter and default flow are clear.
- `output_contract` should normalize headings such as `Output`, `Outputs`, `Output Files`, `Default Deliverables`, and `Handoff` into the same review vocabulary.
- `review_ownership` records whether pre-review/post-review is required and where the evidence lives. Use `conditional` for ordinary skills whose review requirement depends on change class, and `always` for stable-bundle, release-foundation, policy, validation-tool, or high-risk routing surfaces.
- `composition_boundary` records how a skill relates to adjacent skills. A dependency does not automatically mean merge; use `skill-composition-boundary.md` to justify keep, merge, split, or deprecate decisions.

## Standard Vocabularies

`variant`:
- `generic`: public-safe, non-company behavior.
- `company`: privately configured organization-specific variant.
- `project`: project-local skill.
- `runtime`: installed copy whose source may be elsewhere.
- `external`: third-party or hardware/tool skill kept mostly as-is.

`category`:
- `router`: routes broad workflow intents.
- `workflow`: owns a reusable multi-step process.
- `domain`: owns a technical/content domain.
- `tool`: controls or wraps a tool, device, runtime, or script family.
- `intake`: converts user input or source materials into structured state.
- `review`: validates or critiques an artifact.
- `profile`: personal or organizational collaboration context.
- `project`: project-local recovery or domain memory.
- `orchestration`: coordinates agents, roles, or task packets.

`status`:
- `candidate`: useful idea or new skill, not validated enough for default use.
- `pilot`: usable in bounded tasks with explicit validation.
- `stable`: default route is validated and maintained.
- `deprecated`: retained for compatibility; avoid new work.
- `archived`: historical only.

`tier`:
- `Micro`: exact shortcut or fixed small path.
- `Quick`: bounded routing or one state slice.
- `Project`: normal project/skill work.
- `Deep`: dirty, stale, public, risky, contradictory, or cross-surface work.
- `Full`: broad audit or migration with explicit reason.

## Encoding And Trigger Quality

Any skill that carries Chinese aliases, expert names, localized prompts, or user-facing markdown should mark `encoding_guard: required` when it changes. Trigger lexicons must include symptoms users actually report, not only technical terms.

For mojibake/encoding routing, include aliases such as:

- terminal output looks garbled
- PowerShell `Get-Content` shows `æ` / `ç` fragments
- file looks broken but `git diff` or `encoding_guard.py` is clean
- is this file corrupted?
- `乱码`, `终端乱码`, `显示乱码`, `编码触发`

Expected behavior: load the encoding safety reference, verify with explicit UTF-8 readback or `encoding_guard.py`, and do not copy terminal mojibake into durable files.

## What Not To Standardize

- Do not require every small or external skill to adopt a full activation table.
- Do not turn aliases into brittle keyword-only matching; keep natural-language routing.
- Do not mix `skill status`, `expert maturity`, `package readiness`, and `source quality` labels.
- Do not store private/company facts in public skill metadata.
- Do not mark a skill `stable` without evidence.

## Audit Checklist

- Does the skill have a canonical source and runtime copy recorded somewhere?
- Is the category clear enough to decide which expert/reviewer owns it?
- Are trigger aliases and negative triggers explicit for shortcuts and risky routes?
- Is `risk_label` parseable as allow/ask/deny?
- Is the output contract clear enough for another agent to complete the task without chat history?
- Does the record say who owns required pre-review/post-review and where the evidence is stored or why it was deferred?
- Is encoding validation required for Chinese-bearing or localized files?
- Are public/company/project variants intentionally different, or just stale?
- Was the freshest valid baseline chosen before editing or syncing?
- Are adjacent skills composed, merged, split, or deprecated for explicit reasons instead of habit?
