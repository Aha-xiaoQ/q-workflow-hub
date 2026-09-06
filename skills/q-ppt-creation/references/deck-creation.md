# Deck Workflow

Use this reference when creating, migrating, or polishing a presentation deck.

## Default Intake Entry

When a user asks to make a PPT and has not already supplied a complete brief,
default to the local HTML intake path:

1. Open `assets/ppt-intake.html` with `scripts/open_ppt_intake.ps1` when GUI
   access is available. If opening is blocked, give the exact HTML path and the
   chat fallback.
2. Explain the two clear user paths:
   - fill the HTML page, copy or download the `q-ppt-intake/v1` JSON, then tell
     the agent `开始制作` or `start making the PPT`;
   - or provide the title, audience, purpose, source material, slide count,
     style preference, and output constraints directly in the current chat.
3. Treat the HTML page as an intake helper only. It does not generate PPTX.
4. If the user already gave enough structured information, skip opening the
   HTML and proceed from the chat brief while naming any remaining gaps.

## New Deck Flow

1. Confirm audience, purpose, delivery format, language, expected length, and
   available source material.
2. If the source includes a story brief, convert it into a slide map and keep
   the brief's audience, promise, claim order, proof points, adoption path, and
   notes intent visible through generation and review.
3. Choose a base: existing template, sample deck, simple PowerPoint theme, or a
   custom visual grammar.
4. Draft the slide map before building: title, problem/context, core message,
   supporting evidence, implications, and next steps.
5. Define a visual grammar: layout rhythm, type scale, accent use, motif,
   density target, chart/table style, and what not to use.
   For unfamiliar styles, first inspect proven templates or high-quality
   open-source presentation examples and extract reusable layout principles
   instead of inventing every card, frame, and type relationship from scratch.
   For custom styles, choose one entry mode before rendering: manually select
   an existing template/style from a library, reuse an approved style id, or
   generate a new style from a brief. Do not blur the fast template-selection
   path with the slower agent-generated-style path.
6. Build one or two representative slides first when the deck has five or more
   slides, the visual direction is uncertain, or the deck is high visibility.
7. Generate the full deck only after the representative slides are readable and
   visually coherent.
8. If a deck has already had two or more visual repair rounds and still has
   placement or harmony problems, do not regenerate the whole deck again.
   Build a sample set first: title/section, dense content/card grid, process or
   connector slide, and summary/bottom-callout slide. Validate the sample with
   exported images and `q-ppt-visual-review`.
9. For generated decks, keep a small authoring contract: slide type, takeaway,
   layout archetype, semantic regions, slot content, density target, focal
   point, helper names, and quality targets. Coordinates should live in
   reusable renderers or template placeholders, not in slide content data.
10. Add speaker notes when they help delivery, discussion, caveats, or next-step
   prompts. Put them in the PowerPoint Notes pane when possible.
11. Run structural readback, story-alignment review, and visual review before
   handoff.

## Intake JSON Flow

Use this flow when the user wants a reusable request file, a local intake page,
or a handoff from one agent/runner to another.

1. Open `assets/ppt-intake.html` locally and collect only the user's deck
   intent, source pointers, style preference, output path, and validation
   choices.
2. Export JSON that follows `schemas/q-ppt-intake.schema.json`; keep the raw
   request beside the generated deck or project handoff notes.
3. Convert the intake JSON into a story brief before rendering slides. Do not
   treat the intake form as the final narrative or slide map.
4. Produce a slide map/source freeze that records the title, audience, purpose,
   density or `targetSlideCount`, section structure, source material list,
   visual grammar, expected notes mode, validation plan, and open gaps.
5. Generate or migrate the PPTX from that slide map, then run structural
   readback, story-alignment review, `q-ppt-visual-review`, and default PPTX
   open unless the user asked for a no-GUI handoff.

Treat requested deck size as a contract. If `targetSlideCount` is present,
match it exactly unless the user explicitly downgrades the request. If it is
blank, map `density` to a target range before slide-map generation: `short` =
6-8 slides, `standard` = 10-14 slides, and `sharing` = 18-22 slides. Record the
chosen range or exact count in the slide map/source freeze and fail or
explicitly downgrade if the final PPTX falls outside the recorded target.

Public intake fields must stay generic. Private or company-specific options,
such as classification labels, official template pack ids, restricted asset
paths, or brand-policy switches, belong in a namespaced `extensions` object or
in a private extension package. The public flow must remain usable without
those extensions.

## Migration Flow

- Keep the original deck untouched unless the user explicitly asks to overwrite
  it.
- Create a fresh output deck and rebuild content into the selected template or
  grammar.
- Avoid carrying old masters, stale placeholders, hidden artifacts, and file
  bloat forward.
- Preserve approved content but let the new template control typography,
  spacing, and layout.
- Search visible text for leftover placeholders, unrelated window text, review
  notes, and draft wording.

## Visual Grammar Gate

Use this gate for long, user-facing, translated, or visually uncertain decks.

- Make a representative title/section slide and one dense content slide.
- For repeated alignment failures, expand the sample to include a process or
  connector slide and a summary/bottom-callout slide.
- Confirm title treatment, type scale, spacing, accent color, chart/table
  treatment, and density.
- Prefer real product screenshots, diagrams, data, or verified images over
  generic decorative placeholders.
- Avoid visual cliches unless the user explicitly asks for them: default
  purple-blue gradients, glowing orbs, robot faces, circuit-board wallpapers,
  and emoji-heavy visuals.
- Record the approved grammar briefly so regeneration and later edits preserve
  the same direction.
- If an agent-generated style is approved, register it as a reusable style
  candidate: save the sample deck, thumbnails/contact sheet, source/license
  note, layout contract, and visual review evidence under a stable style id.
  Later requests should be able to select that style without regenerating it
  from scratch.

## Layout Rules

- Keep text concise and validate that it does not overflow.
- For decks with two or more substantive sections, include an agenda or
  overview page and a divider before the first section, not only before later
  sections.
- Keep agenda and section/transition pages matched. Formal template decks
  should use agenda and divider roles from the same template family; less
  formal custom decks should make transition pages use the same section names,
  order, and visual grammar as the agenda.
- On covers, balance the main title/subtitle group in the visual-safe region
  and keep request-side production hints out of visible metadata.
- For Chinese decks, keep visible English only when it carries recognition
  value: official names, acronyms, command/file identifiers, code symbols, or
  first-use technical terms. Localize ordinary section labels, chart labels,
  workflow words, review terms, and explanatory prose.
- Budget extra width and height for translated or mixed-language labels.
- Build repeated modules as stable components with consistent alignment,
  spacing, line weight, corner radius, and type treatment.
- Repeated modules should be implemented through named helpers or template
  placeholders. If the generator uses slide-by-slide coordinates, any new
  alignment miss should be fixed in the helper or layout IR before full-deck
  regeneration.
- When the final artifact is editable PPTX and the generation library supports
  grouping, emit repeated multi-shape modules as actual PowerPoint groups after
  the helper lays out the internal grid. Use the group as the editable
  component boundary; do not use grouping to hide internal alignment defects.
- Align number badges, labels, and adjacent title/detail rows on the same visual
  center line.
- Put text inside visual frames, cards, badges, and process boxes through
  shape-owned text or an actual grouped component so the frame and text move as
  one unit.
- For every framed text component, reserve a safe internal inset before
  rendering text. The text slot should be calculated from the frame bounds and
  should not touch the border, ride the bottom edge, or extend outside the
  frame. Treat the inset as a visual comfort target as well as a collision
  target: if the rendered PNG still looks tight, enlarge the frame, shorten the
  copy, or increase the inset before handoff.
- For colored accent-rule + label/callout patterns, use one helper that
  computes a shared center line for the rule and the adjacent text. In editable
  PPTX output, group the rule and label/callout text when practical so later
  movement preserves the relationship.
- Do not place tiny number chips in the corner of large cards when the number
  is structural. Enlarge and align the number with the title row, or use a
  deliberate side rail.
- Do not rely on left colored strips as generic decoration. Use strips only when
  they encode a clear category, progress, or hierarchy role.
- Do not repair readability by placing a large unrelated background panel into
  the slide. On a dark style, a white band behind content is a blocker unless
  the chosen reference/template uses that semantic surface. Fix contrast inside
  the visual grammar through palette, typography, spacing, stroke, shadow, or a
  matched component surface.
- Check text/background contrast against the exact local background. Ordinary
  required text should target about 4.5:1 contrast; large/bold display text
  should target about 3:1. Captions over dark image regions or panels are not
  acceptable if they only pass by object bounds.
- Keep list blocks visibly separated from separator lines and nearby shapes.
- For hub-and-spoke diagrams, center the hub among its related nodes and verify
  every intended side is visibly connected.
- For bar/score comparison charts, align labels, bars, and scores on shared row
  centers.
- Force intentional line breaks for long labels or callouts when rendered PNGs
  show pressure against borders or orphan punctuation.
- Reject punctuation-only final lines, single-character CJK final lines, and
  very short wrapped tails in polished decks; fix wording, slot width, or line
  breaks before shrinking type.
- For repeated cards, tiles, process labels, and compact rows, choose one
  punctuation convention for the peer group. Phrase-style items usually omit
  terminal punctuation; sentence-style items should use it consistently.
- Split overloaded slides instead of shrinking text below readable size.

## Validation

Run a readback check after saving:

```python
from pptx import Presentation
prs = Presentation("output.pptx")
print(len(prs.slides))
```

When possible, also inspect slide titles and notes. For high-risk decks, export
slide images and run `q-ppt-visual-review`.

After structural readback and visual review evidence exist, open the final PPTX
for local preview as the default handoff step, unless the user asked for a
headless/no-GUI run. On Windows this is typically `Start-Process -FilePath
<deck.pptx>`. If the platform requires GUI approval, request the narrowest
approval; if PowerPoint or file association is unavailable, report the exact
PPTX path plus the visual review folder and do not imply that preview happened.
