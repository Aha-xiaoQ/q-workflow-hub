---
name: q-ppt-creation
description: Create, migrate, and polish presentation decks such as PowerPoint files. Use when Codex needs to plan a deck storyline, build or convert slides, define reusable visual grammar, add speaker notes, validate readability/layout, or hand off presentation source files without relying on a company-specific template.
---

# Q PPT Creation

Use this skill for reusable presentation mechanics. Keep project-specific
storyline, domain claims, confidential source material, and final business
decisions in the target project repository.

## Intent Router

| User intent | Read next |
|---|---|
| Bare/new PPT request such as `make/create a PPT` or Chinese `制作PPT` | `references/deck-creation.md` `Default Intake Entry`, then open `assets/ppt-intake.html` with `scripts/open_ppt_intake.ps1` unless the user already provided enough details or asks for chat-only intake. |
| Create a new deck from sufficient details or an approved intake JSON | `references/deck-creation.md` |
| Convert or migrate an existing deck | `references/deck-creation.md` migration section |
| Pick a visual direction | `references/deck-creation.md` visual grammar gate |
| Collect a reusable deck request | `references/intake-schema.md`, then `assets/ppt-intake.html` |
| Validate intake request JSON | `scripts/validate_intake_request.py <request.json>` |
| Validate a generated PPTX visually | `q-ppt-visual-review` |
| Generate slides from an approved story brief | `q-project-storytelling` artifact handoff, then `references/deck-creation.md` |

## Core Rules

- Default PPT request entry: when the user asks to make/create a PPT and has not
  already supplied a sufficiently structured brief, open the packaged local HTML
  intake page by default. Tell the user they can either fill/export the HTML
  request and then say `开始制作` / `start making the PPT`, or provide the same
  details directly in the current chat. Do not block users who already supplied
  title, audience, purpose, source material, style, slide count, and output
  constraints; proceed from chat in that case and record the missing fields.
- Start from audience, purpose, delivery format, and source material.
- When a deck request is captured through intake JSON, treat that JSON as the
  portable input contract. The browser intake page collects user intent only;
  the receiving agent, CLI, or local runner still owns story brief creation,
  slide-map generation, rendering, validation, and repair.
- Keep public intake fields generic. Company, client, or template-specific
  options must live under a namespaced `extensions` object or a separate
  private extension package, not in the public root schema.
- If a story brief exists, treat it as the message contract for the deck:
  preserve the audience, one-line promise, claim order, proof points, adoption
  path, and speaker-notes intent unless the user explicitly changes the story.
- Prefer a verified template, sample deck, or layout grammar over arbitrary
  slide layouts. If none exists, create one or two representative slides first.
- If repeated review rounds still leave placement, alignment, or visual harmony
  problems, stop full-deck regeneration and return to a representative sample
  plus a named layout contract. Continuing to nudge individual slides is a
  workflow failure, not polish.
- For unfamiliar or high-visibility visual styles, study proven templates or
  high-quality open-source presentation examples before inventing a card
  system. Extract layout rhythm, type scale, spacing, and component hierarchy,
  then adapt rather than copying assets or prompts.
- For custom visual directions, separate manual template selection from
  agent-generated style creation. Manual selection is the fast path: preview
  and pick a concrete template/style candidate from a user-provided or packaged
  library. Agent-generated style is the slower path: collect concrete
  requirements, create a representative sample, validate it, and wait for
  approval before full-deck generation. Approved generated styles should be
  saved with previews, source notes, layout contracts, and validation evidence
  so future users can select them manually.
- Keep the deck source editable. Use PowerPoint notes for speaker guidance and
  an external report for validation findings.
- Do not put production notes, draft reminders, source caveats, or review
  comments on visible slides unless the deck is explicitly for internal review.
- Use concise slide titles and one primary idea per slide.
- Prefer diagrams, simplified figures, and short tables over dense paragraphs.
- Avoid default card tricks such as tiny number chips in large frames or left
  color strips used as decoration. If numbers or accent bars carry meaning,
  make their hierarchy and alignment explicit in the visual grammar.
- Do not fix readability by adding a large off-style background patch. Solve
  contrast through the selected palette, typography, component surface, spacing,
  stroke, or shadow unless the chosen template intentionally uses that
  semantic surface.
- Treat text/background contrast as a default gate: required body/caption text
  should be readable against its exact local background, including photos and
  dark panels, and low-contrast captions block handoff.
- For text inside cards, callouts, badges, process boxes, or framed panels,
  define the frame and text as one component with a safe internal inset. Use
  shape-owned text or a grouped helper-owned component; do not rely on
  separately nudged text boxes that can touch or escape the frame. If exported
  PNGs still make the text look tight, enlarge the frame or increase the inset
  instead of accepting a barely passing geometry check.
- For colored accent-rule + label/callout patterns, define one helper-owned
  component with a shared vertical center line and middle-anchored text; group
  it in editable PPTX output when practical.
- If screenshots, paper figures, or charts are unreadable at presentation size,
  enlarge them, simplify them, or move evidence into notes/appendix material.
- When translating or reusing geometry across languages, validate the translated
  deck independently. Expanded labels and line wraps can break layouts that
  worked in the source language.
- After manual PowerPoint edits, inspect the edited PPTX and sync approved
  coordinates, sizing, and wording back into the generator before regenerating.
- Use `q-ppt-visual-review` after generation when the deck is user-facing,
  high-visibility, translated, or visually dense.

## Activation And Risk

| Trigger | Tier | Risk | Reference |
|---|---|---|---|
| New/generated deck | Project | allow local file writes | `references/deck-creation.md` |
| Existing deck migration | Project | preserve source deck | `references/deck-creation.md` |
| Public/client-facing deck | Deep | ask when audience/confidentiality is unclear | `references/deck-creation.md` |
| Private source material or proprietary templates | Deep | do not publish without explicit approval | current project policy |

## Handoff

Before calling the deck ready:

- preserve the intake request JSON path when one exists;
- confirm output PPTX exists and opens or can be parsed;
- run a structural readback check with slide count and titles;
- run visual review or record why it was skipped;
- open the final PPTX for local preview by default after structural readback
  and visual review evidence exist, unless the user asked for a no-GUI handoff
  or the environment cannot open GUI files;
- record source files, generation command, validation report path, and known
  limitations in the project state or handoff notes.
