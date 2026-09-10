# Changelog

All notable changes to q-workflow-hub will be documented in this file.

This project follows semantic versioning once stable release tags are created.

## Unreleased

### v1.2

- Add a Simplified Chinese README, refresh the English entrypoint and reuse the
  current pixel Q logo. Add an adaptable bilingual README standard and starter
  template to project storytelling; align the after-setup update link with the
  current package. Installation behavior is unchanged.
- Apply proportionate skill routing: focused PDF/transcript work no longer
  requires unrelated extraction packs or provider benchmarks; retain evidence,
  privacy, authorization and independent release-review gates.
- Treat audit length/ordinary mixed-newline findings as advisory, validate
  explicit roots, and require proof that rollback fault injection was reached.
- Preserve important audience-facing limitations and required license notices.
- Add capability-aware core execution and project-specific release binding.
- Isolate explicitly scoped portfolio audits; retain v1.1 safety regressions.
- See [v1.2 release notes](docs/releases/q-workflow-v1.2.md).

### September maintenance
- Preserve Bilibili multipart selection, reuse authorized local subtitle routes,
  and distinguish login failures from absent captions, with offline regressions.
- Add saved-route opt-out and isolate explicit route registries.
- Document default-private asset promotion.

See the [maintenance notes](docs/releases/maintenance-2026-09-06.md).

## 1.1.0-beta - 2026-09-06

Display version: `v1.1-beta`. See the release notes for scope and migration limits.

- Harden recovery-pointer visibility and validation contracts.
- Add bounded pilot state tracking with explicit probe-success checks.
- Correct filtered task-list validation and terminal-state resume guards.
- Extend skill lifecycle/evaluation guidance and regression coverage.
- Remove machine-specific pixel-skill paths and private evidence references.
- Install every registered bundled skill and initialize empty TODO display metadata.
- Support first-task registration from an idle hub and preserve original TODO names.
- Initialize a new runtime mirror using explicit paths, without replacing existing mirrors.
- Add two-round public-install checks, including transactional updater rollback.

Use the quickstart's update procedure to refresh an existing installation.

## 1.0.0-beta - 2026-08-12

This public beta is published under the display tag `v1.0-beta`. It introduces
the recovery-first workflow kernel while preserving the existing starter and
legacy-pointer paths.

### q-workflow kernel

- Added the read-only-by-default `q_workflow_manager.py` entry point for
  status, doctor, surface inspection, registry validation, and transactional
  task-state operations.
- Added versioned task records, an append-only authority event chain,
  compare-and-swap planning, an operating-system lock, atomic replacement,
  readback validation, rollback, and idempotent apply receipts.
- Added a strict surface registry and registry-gated bootstrap/runtime sync.
- Added minimal operational evidence through stable status, `elapsed_ms`, and
  `failure_class` fields without storing prompts or private artifact bodies.
- Hardened recovery authority, runtime manifests, release evidence,
  user-visible output preflight, portfolio-root resolution, and independent
  expert handoff/model-routing checks.

### Compatibility and release posture

- Existing Markdown state and `RECOVERY_POINTER v1` remain readable.
- `ACTIVE_WORK.md` remains the selected focus view; registered task records are
  the material-task authority, and `sync_state` remains a derived compatibility
  alias.
- This is a public beta, not a stable-v1 declaration. The five registered core
  surfaces are release-gated; lab surfaces are outside the beta stability
  guarantee.
- A forced process termination between multi-file switches can still leave a
  partial transaction because a durable write-ahead journal is not yet
  implemented.

- Added `q-game-canvas-iteration` as a pilot generic skill for original local
  Canvas/browser game feedback loops, with source/runtime authority and
  scenarios. Retired the initial `game-canvas-iteration` folder alias after
  confirmation; the old phrase remains a canonical text trigger.

- Tightened promotion-repo push cadence: company-side promotion/share repos are
  no-push by default for routine sync and require an explicit version update,
  stable release, or major update request before pushing.
- Added reusable human-loop TC-15 for permission refusal handling, focused on user-visible safe-continuation output and local alternatives.
- Changed human-loop review cards to lead with the tested prompt and user-visible assistant output, keeping machine evidence in separate result/raw files.
- Added reusable human-loop TC-14 for Chinese project registration write validation, including registry write, resolver, no-copy, and no-push checks.
- Added reusable human-loop TC-12 for Chinese setup and first recovery, plus a Chinese `ASSISTANT_HELP.md` template so Chinese installs no longer receive English or mojibake help surfaces.
- Added a default PPT intake entry so bare PPT-making requests open the
  packaged HTML intake first, while still allowing users to say `开始制作` after
  exporting JSON or provide details directly in chat.
- Renamed q-workflow-family skills to use the `q-<domain>-<job>` pattern,
  including `q-assistant-profile`, `q-skill-creation`,
  `q-skill-pattern-learning`, `q-ppt-creation`, `q-ppt-visual-review`, and
  `q-project-storytelling`; added a skill naming convention reference and
  taught the personal-bootstrap sync scripts to remove obsolete renamed skill
  copies.
- Added an explicit pull/rebase-before-push rule for GitHub handoffs so
  `push GitHub` includes remote freshness checks before publishing.
- Tightened GitHub handoff guidance so known proxy-needed environments use a
  proxy-backed pull/rebase before proxy-backed push instead of trying direct
  HTTPS first.
- Clarified public `q-video-intake` / `q-audio-intake` entry points so users
  can distinguish subtitle/visual video intake from STT provider benchmarking
  and closed-loop transcript scoring.
- Added public `q-workflow` hygiene and identity references so cleanup,
  skill-fit, and workflow distinctiveness checks are part of the starter.
- Expanded `init-user.ps1` to copy the full default skill set into both the
  workflow bootstrap and optional runtime install, instead of installing only a
  small subset.
- Added a quick-recovery invocation rule to the q-assistant-profile template so a
  profile-name prompt can produce a compact workflow recovery panel instead of
  being treated as a bare greeting.
- Fixed `init-user.ps1` to read templates as UTF-8 before expanding them, so
  Chinese prompt examples and recovery headers do not become mojibake.
- Added a workflow bootstrap sync script and hardened generic-skill sync rules
  so source, runtime, bootstrap, private, and GitHub mirrors are checked with
  recursive file-list and hash validation instead of spot checks.
- Fixed the local setup runner so web form submissions pass named
  `init-user.ps1` parameters correctly, expand `%USERPROFILE%` and `~` paths,
  and show install logs without corrupting the Quick Resume marker.
- Added `setup-intake.html` and a configurable `WorkflowLabel` setup parameter
  so new users can collect setup fields locally and get a visible Quick Resume
  marker such as `【q-workflow | Quick Resume】` or `【小Q工作流 | Quick Resume】`.
- Added first-run visual onboarding guides for generated workflow hubs:
  `FIRST_RUN_GUIDE.html` for English setup and `FIRST_RUN_GUIDE.zh-CN.html` for
  Chinese setup.
- Added `q-skill-pattern-learning` for studying external/internal skills, extracting
  transferable workflow mechanisms, validating lessons on separate scenarios,
  and deciding whether to promote them into q-workflow.
- Added generic `q-ppt-creation` and `q-ppt-visual-review` skills for
  presentation creation, migration, visual review, and PowerPoint validation.
- Added q-workflow experiment contracts and a validator for a standard
  `route -> plan -> edit -> validate -> review -> checkpoint` task flow.
- Added `fast mode` / `全速模式` as an explicit execution-speed command with
  preserved safety gates.
- Added a command-alias layer for help/status/resume/checkpoint/rule-sync and
  publish flows, with English/Chinese aliases, narrow fuzzy matching, and a
  generic-skill sync audit before completion.
- Synchronized `q-skill-creation` rule-quality and workflow-evaluation
  references from the company workflow into the public starter.
- Added recovery hardening rules for multi-repository dirty-state
  classification, post-recovery consolidation, narrow runtime mirror sync, and
  repository naming governance.
- Added a public `repository-naming` reference and linked it from `q-workflow`
  for rename and registry-key audits.
- Added Quick Resume recovery rules to `q-workflow` and q-assistant-profile
  templates, including dirty-state inspection before hidden truth and explicit
  first-pass correctness/resource/speed reporting.
- Simplified the quickstarts around installation only, moved daily usage
  guidance into after-setup docs, shortened first prompts, added Git install
  links, documented Chinese resume prompts, and moved setup checks into the
  agent-led flow.
- Added beginner guidance for context/data/memory boundaries, prompt/work-item
  shape, and tool/MCP safety.
- Added a workflow hub work item brief template and made the initializer copy
  it into new workflow hubs.
- Added a first-pass route map to the quickstart and aligned the Chinese guide
  with the first-run validation score.
- Recorded Bilibili beginner tutorials as reference material only, with an
  explicit note that no transcripts, screenshots, assets, or distinctive prose
  were copied.
- Added a concise q-video-intake field guide that summarizes validated paths,
  sample categories, visual sampling choices, and completion rules.
- Added explicit uncertainty-discipline rules: unknown facts must be labeled as
  unknown/unverified/needs retest instead of guessed into durable records.
- Added real-sample evidence registry rules so completed video/audio analyses
  and benchmark samples remain recoverable after chat compaction.
- Added `q-video-intake/workflows/sample-registry.md` and wired it into quick
  summary, deep-dive, and visual reverse-parse workflows.
- Added `templates/SAMPLE_REGISTRY.md` for projects that need a tracked sample
  ledger.
- Clarified that a user-identified missing sample must be matched by exact URL,
  title, creator, or phrase before an inferred local candidate can be treated as
  the target sample.
- Added durable sample-record requirements to `q-audio-intake` benchmark
  guidance so STT provider conclusions do not depend on ignored local outputs.
- Clarified that ignored `local-state` outputs are evidence, not durable
  memory, and that real sample analysis is not complete until conclusions are
  recorded durably.
- Added parallel sub-agent workflow rules so long downloads, benchmarks,
  research, validation, and disjoint patches can run beside main-agent work
  without losing integration control.
- Switched durable emergency checkpoint trigger examples to ASCII aliases to
  avoid encoding drift in reusable workflow files.
- Added hook-assisted lesson capture guidance and explicit routing rules for
  `q-skill-creation` and `q-research-discovery`.
- Added platform compact/session failure recovery rules so a broken chat
  window can be abandoned and a fresh session can recover from durable files,
  screenshots, and the latest visible user request.
- Added emergency checkpoint triggers for compact/session instability,
  including `紧急记录`, `保存现场`, `checkpoint`, and `emergency save`.
- Changed GitHub sync guidance to prefer a temporary local proxy by default
  when direct HTTPS is unreliable, while avoiding global Git proxy changes.
- Added low-friction permission posture and completed-state resume rules so
  agents avoid repeated routine approvals and avoid reopening finished work.
- Added skill portability guidance so local skill experiments can be promoted
  or recorded for cross-machine restore.
- Added `q-research-discovery` v1 for targeted research planning, skill
  discovery, lateral stuck-work exploration, source evaluation, and durable
  search logs.
- Improved `q-research-discovery` after dogfooding with source roles, adoption
  decisions, a source-registry template, and recorded public reference families.
- Added experiment-validation guidance and a scoring rubric for checking
  whether a skill, workflow, or documentation pattern worked in practice.
- Added `q-audio-intake` MVP for audio-first transcription preparation,
  OpenAI/Gemini STT provider entry points, and CER/WER transcript scoring.
- Added `q-audio-intake` `whisper-cpp` provider support so local
  `whisper.cpp` CLI builds, including Windows AMD/Vulkan builds, can be
  benchmarked through the same transcript and scoring workflow.
- Added a reproducible `whisper.cpp` install workflow for `q-audio-intake`,
  covering stable local paths, environment variables, CPU smoke setup,
  AMD/Vulkan validation, and closed-loop benchmark promotion.
- Added closed-loop STT benchmark workflows so audio transcription quality can
  be judged against official/platform subtitle references instead of subjective
  transcript inspection.
- Added a first-run validation score to the quickstart so new users and agents
  can judge setup health with observable checks.
- Improved q-video-intake subtitle robustness by falling back through subtitle
  languages when one platform language fails or is rate-limited.
- Improved q-video-intake and q-audio-intake ffmpeg detection so Windows app
  execution aliases are not mistaken for runnable ffmpeg binaries.
- Documented `yt-dlp` JavaScript runtime and impersonation warnings as
  nonblocking compatibility warnings when subtitle extraction still succeeds.
- Added assistant operating profile and role-mode hooks for stable assistant
  behavior and lightweight task-specific working modes.
- Added proactive help and feature-hint rules so assistants can explain useful
  workflow capabilities and suggest next steps at natural stopping points.
- Added paused-work queue rules so interrupted tasks can be offered as resume
  options after later work finishes.
- Added memory and efficiency rules for automatic lesson capture, progressive
  context reading, recoverable checkpoint cadence, and GitHub proxy fallback.
- Added `PRINCIPLES.md` to document q-workflow's reliability-first, friendly,
  license-aware product principles.
- Added `q-skill-creation` for creating, updating, and reviewing reliable
  q-workflow-compatible skills.
- Updated generated assistant profiles to prefer Chinese discussion with Xiao Q
  and preserve the reliability-first collaboration style.
- Added the first `q-video-intake` reusable skill for subtitle-first
  video/audio intake, optional OpenAI transcription fallback, and
  tutorial-analysis notes.
- Added q-video-intake analysis packs: transcript chunking, reusable analysis
  prompts, and an `analyze` command for existing transcripts.
- Added q-video-intake workflow routing docs inspired by mature video-summary
  skills: transcript extraction, quick summary, and deep-dive analysis.
- Added q-video-intake visual reverse-parse frame packs for sampling local
  video frames and preparing vision/human review prompts before adding a model
  adapter.
- Added q-video-intake visual notes templates so frame packs can move directly
  into structured UI/action/OCR review without a model adapter.
- Added q-video-intake `visual-analyze` for provider-ready visual prompts and
  optional GPT vision calls from sampled frame packs.
- Added q-video-intake `visual-agent-task` so Codex/GPT sessions can produce
  structured visual notes from frame packs when API access is blocked.
- Added q-video-intake `visual-score` for checklist-based regression scoring
  of visual notes against expected labels, facts, and frame observations.
- Added Azure OpenAI support for q-video-intake `visual-analyze` so Azure keys
  use Azure endpoints and deployment names instead of the standard OpenAI API.
- Improved Windows ffmpeg detection so PowerShell-resolved ffmpeg installs work
  for local video and audio fallback.
- Added third-party reference and license-compliance notes for future skill
  integrations.
- Improved q-video-intake next-step guidance when Bilibili subtitles require
  login or browser cookies cannot be copied.
- Added q-video-intake `--cookies-file` support for exported Netscape-format
  cookies when browser cookie copying or DPAPI decryption fails.
- Added Bilibili AI subtitle language defaults and request-order subtitle
  selection so Chinese AI subtitles are preferred over English when available.
- Validated real Bilibili subtitle extraction with exported cookies, Bilibili
  AI subtitle languages, and Chinese transcript selection.
- Added a user-facing quickstart guide with setup prerequisites, first prompts,
  generated files, daily prompts, and troubleshooting.
- Added Chinese quickstart and first-prompt docs for bilingual onboarding.
- Expanded environment preflight checks for Git, PowerShell, network access,
  writable workspace paths, and optional workflow hub remotes.
- Added beginner-oriented setup route guidance for Codex, Claude Code, and
  optional CC Switch usage.
- Reworked quickstart onboarding around a beginner-friendly happy path,
  checkpoints, and success criteria.
- Added a first-run "get it running first" path and a normal agent-dialogue
  sequence so new users know what should happen after pasting the prompt.
- Changed generated template files to UTF-8 without BOM so generated skill
  files load cleanly in frontmatter-based skill loaders.
- Updated first-run guidance so agents explain the workflow after collecting
  setup fields and before changing files.
- Hardened recovery behavior: the initializer now preserves existing personal
  registry and active-work files, and resume instructions require a recovery
  scan before concluding that no active work exists.
- Fixed public-scan false positives for safe API-key variable passing and a
  PowerShell `$Matches` variable collision.

## 0.1.0 - 2026-06-05

- Initial public starter repository.
- Added `q-workflow` skill.
- Added workflow hub and project memory templates.
- Added Windows PowerShell initializer.
- Added first-run agent prompt and machine bootstrap guide.
