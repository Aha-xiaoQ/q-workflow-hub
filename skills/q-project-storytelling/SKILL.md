---
name: q-project-storytelling
description: Structure project, product, architecture, research, onboarding, and science-popularization narratives before writing slides, README content, speaker notes, project overviews, demos, or internal promotion material. Use when Codex needs to make a technical project understandable, persuasive, audience-aware, modular, and reusable; when a deck or document feels like a feature list; or when Xiao Q asks to improve how a project is explained, promoted, taught, or standardized.
---

# Q Project Storytelling

Use this skill before creating or rewriting communication artifacts. It shapes
the narrative, proof, and speaker guidance; then another skill can generate the
PPT, README, project overview, diagram, or onboarding asset.

## Intent Router

| User intent | Read next |
|---|---|
| Improve a project/product/architecture explanation | `workflows/shape-narrative.md` |
| Prepare a PPT or speaker notes story before slide generation | `workflows/shape-narrative.md`, then `references/artifact-handoff.md` |
| Convert an approved story brief into deck, README, overview, demo, or onboarding instructions | `references/artifact-handoff.md`, then the target artifact skill |
| Turn technical details into a popular-science or onboarding explanation | `references/pattern-library.md` |
| Improve only Notes pane / talk track | `references/speaker-notes.md` |
| Polish wording, copy style, naturalness, or human readability after story structure is set | `workflows/copy-style-polish.md` |
| Audit whether an existing deck/document tells a clear story | `workflows/shape-narrative.md` review path, then `references/evaluation-rubric.md` |
| Compare baseline copy against a rewritten story brief | `references/evaluation-rubric.md` |

## Core Rules

- Start with audience, desired action, prior belief, and likely objection.
- Write the promise before the outline: what will be better if the audience
  understands or adopts the project?
- Prefer a narrative spine over a feature list:
  `audience -> promise -> problem -> mechanism -> proof -> adoption -> notes`.
- Separate story layers:
  - positioning: why this matters and for whom;
  - mechanism: how it works at the right zoom level;
  - proof: evidence that makes claims credible;
  - adoption: what the audience should do first;
  - notes: how the presenter explains and transitions.
- Use architecture zoom levels. Do not start with implementation details when
  the audience first needs context, users, major capabilities, and value flow.
- Keep technical terms when they are real interface or workflow terms, but
  define them once and avoid unnecessary English mixing.
- Do not copy third-party messaging frameworks, slide text, diagrams, prompts,
  or assets. Learn ideas and mechanisms only, with attribution recorded in the
  project state when sources materially shaped the work.
- Before handing off to a PPT or document skill, produce a compact story brief:
  audience, one-line promise, outline, proof points, adoption path, and notes
  pattern.
- Treat the story brief as a contract, not decorative prewriting. A generated
  PPT, README, overview, demo, or onboarding artifact should preserve the
  selected audience, promise, claim order, proof points, adoption path, and
  speaker-notes intent unless the user explicitly changes the story.
- When using this skill to improve existing copy, compare the baseline and
  candidate with `references/evaluation-rubric.md`; do not claim the rewrite is
  better only because it sounds smoother.
- Separate structure from style. First make the story true and useful; then use
  `workflows/copy-style-polish.md` to remove generic AI-sounding phrasing
  without changing proof, caveats, or approved terminology.

## Handoff

Before closing a storytelling round:

- record the chosen story spine and rejected alternatives in the project state
  or work item;
- state whether the next artifact should be a deck, README, overview, demo
  script, or onboarding guide;
- if a deck will be generated, include the `references/artifact-handoff.md`
  contract before handing the story brief to `q-ppt-creation`, the
  relevant template-specific presentation skill, and `q-ppt-visual-review` as
  appropriate;
- if this skill changed a reusable rule, validate and sync source/runtime
  copies before claiming it is ready.
