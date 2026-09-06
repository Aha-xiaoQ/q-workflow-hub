# Deck Quality Gate

Use this gate when a deck is generated, high-visibility, unfamiliar in style, or
the user questions whether the visual review really happened. This gate catches
slides that are technically valid but still look weak, generic, confusing, or
unfinished.

## Required Review Surfaces

- Contact sheet of all exported slides.
- Full-size PNGs for the title slide, one dense content slide, one diagram
  slide, and every slide flagged by the automated report.
- For style-pack sample-first flows, full-size PNGs for every sample page:
  cover/title, agenda/navigation, section/transition, representative content,
  and closing/contact.
- The automated report, used as leads rather than the final verdict.
- For generated decks with custom visual grammar, the layout stability gate in
  `layout-stability-gate.md`, including header/title/footer and component
  contracts.
- For complete generated decks, a structure check confirming the expected cover,
  section/navigation pages, content pages, and closing/contact page are present.

Do not claim visual review is complete unless at least the contact sheet and
representative full-size PNGs were inspected.

Do not give `Pass` while an automated warning on a cover, title slide, bottom
callout, hero statement, dense table, or long label remains uninspected in the
rendered PNG. Either fix the generator or record a slide-specific justification
that the full-size PNG is visually acceptable. Long-unwrapped-text warnings in
large visible statements are review blockers until checked visually.

Also check visual-region pressure, not only overlap. A cover subtitle, hero
line, or bottom takeaway can fail even when its shape does not geometrically
overlap another object: if the rendered line runs close to the next visual
region, crosses the implied column boundary, or makes the eye read across two
unrelated groups, add an intentional line break or shorten the wording.

Also check peer-item text style, not only individual warnings. Repeated cards,
tiles, process labels, and compact rows should use one punctuation convention:
phrase-style items usually omit terminal punctuation, while sentence-style
items use it consistently. Mixed terminal punctuation inside the same visual
group is a polish blocker unless the report explains why the items are not
comparable.

## Five-Second Test

For each representative slide, answer without reading speaker notes:

- What is the single takeaway?
- Where does the eye land first?
- What should the viewer read second?
- Does any element look decorative rather than useful?
- Would this look acceptable in the intended meeting or handoff context?

If the single takeaway or first focal point is unclear, mark the slide as a
design-quality blocker even when text boxes do not overlap.

If a reviewer says the slide is still "not aligned", "not harmonious",
"awkward", "floating", or otherwise visually wrong after an automated pass,
treat the previous verdict as failed. Do not defend the score by pointing to
shape geometry. Restart from contact-sheet and full-slide screenshots, name the
layout grammar that failed, and decide whether the deck needs a new layout
system rather than local fixes.

If the miss is in a repeated generated component, do not downgrade it to a
small polish issue. Numeric rows, circle badges, process steps, cards, callouts,
and connector groups must be generated from helper-owned centerlines and
anchors. A user-visible offset in one instance means the component contract or
review gate failed; fix the authoring helper, regenerate the deck, rerun the
script, and inspect the affected full-size PNG before restoring `Pass`.
For editable PPTX, prefer making repeated multi-shape components actual
PowerPoint groups after the helper lays out the internal grid, so later manual
movement preserves the component. Grouping is not a substitute for internal
alignment; the review must still inspect group children.

If the miss is a process line that looks like it floats inside a large shared
container, treat it as a process-component grammar failure, not a connector
style preference. Split the flow into individual step cards or nodes, connect
their boundaries or center lines, and record the helper/component contract.

If the miss is readability on a custom/generated style pack, do not accept a
large off-style background patch as the fix. A white panel on a dark deck, or
any similar unrelated surface, can make text readable while breaking the visual
grammar. Treat it as a design-quality blocker unless it is a declared semantic
surface from the selected reference/template. Repair contrast with the style
palette, typography, component surface, spacing, or stroke/shadow treatment.

If the miss is low text/background contrast, treat it as a real readability
failure, not a subjective style preference. Use about 4.5:1 contrast for
ordinary required text and about 3:1 for large/bold display text. Any dark-on-
dark or light-on-light caption that is hard to read in the exported PNG blocks
handoff until the palette, surface, or typography is fixed.

If the miss is text pressing against, or escaping from, a card/callout/frame,
fix the authoring component. The frame must own a safe content slot with
internal padding; the text should be shape-owned or grouped with the frame.
Do not accept a manual nudge that only hides the current instance. If the
rendered PNG still looks tight even after it clears the minimum inset, enlarge
the frame or shorten the copy; a barely passing inset is still a quality
failure in a polished generated deck.

If a generated preview or component-library sample uses text below 9 pt,
multi-thumbnail diagram pages where labels are unreadable, a rule/hard-gate
sentence that runs outside the slide, or framed text that visually hugs the
border, treat the previous review as unstable. The fix must change the layout
contract or helper, not only the current PPTX.

If the miss is a colored rule paired with a label or callout sentence, fix the
rule-label component. The line and text should be generated together, grouped
when editable PPTX is the output, and vertically centered on one declared
center line.

If the miss is an unreadable screenshot, paper figure, UI capture, or dense
chart, treat the picture as too small for the slide. Enlarge and crop the
evidence, rebuild the message as a simplified diagram, or move the original
into notes/appendix material.

If the miss is orphan punctuation, a one-character final line, or a very short
wrapped tail, fix wording or line breaks in the generator. Reducing font size
is secondary and must not create a squeezed-looking card.

If the same failure survives two repair rounds, switch from full-deck repair to
sample-first recovery using `layout-stability-gate.md`. The quality gate cannot
return `Pass` until the representative sample, layout contract, and
`layout_audit.csv` evidence show that the repeated component positions are
stable.

## Scorecard

Score each category from 0 to 2:

- Message clarity: one clear point per slide, title supports that point.
- Visual hierarchy: scale, contrast, position, and grouping guide the eye.
- Composition and whitespace: the slide has stable margins, balance, and air.
- Typography: text is readable, intentional, and not squeezed into UI labels.
- Craft consistency: repeated objects share alignment, spacing, shape, stroke,
  radius, and color treatment.
- Diagram value: diagrams explain relationships instead of decorating the page.
- Audience fit: style, density, and wording fit the deck purpose.
- Polish and originality: the deck looks finished, not like a generic dark UI
  mockup or repeated card grid.

Interpretation:

- 14-16: shippable after normal content fixes.
- 10-13: needs targeted visual repair.
- below 10: needs redesign before handoff.
- Any score of 0 in message clarity, visual hierarchy, typography, or audience
  fit is a blocker regardless of total score.

## Common Failure Patterns

- Decorative grid, neon strokes, or dark background used as a substitute for
  content hierarchy.
- Every slide uses the same card layout, so nothing feels specifically designed
  for the message.
- Many small labels are technically readable up close but not presentation
  readable.
- Diagram nodes are evenly distributed but the relationship or story is weak.
- The slide has no strong focal point, or the focal point is a page number,
  accent bar, connector, or background decoration.
- Contact sheet reveals monotony, weak rhythm, or inconsistent density.
- Automated warnings are numerous and noisy, causing obvious visual weakness to
  be ignored.
- Repeated top headers, accent rules, page numbers, titles, or section labels
  drift or float independently from the slide grid.
- Process steps, command rows, badges, labels, connectors, or bottom callouts
  are built from manual offsets instead of one component center line.
- Repeated multi-shape components remain loose shapes in the final editable
  PPTX even though the library supports grouping, making later adjustment
  likely to break alignment.
- A process slide uses one large shared band with short connector lines floating
  between text clusters instead of separate connected cards or nodes.
- The automated report contains centerline or circle-badge warnings, but the
  manual gate records `Pass` without full-size PNG evidence and a slide-specific
  justification.
- A slide uses a large foreign-color panel to force readability instead of
  solving contrast inside the selected style grammar.
- Required text has low contrast against a photo, dark panel, light panel, or
  gradient, especially captions under images.
- Text inside cards, callouts, process boxes, or framed panels touches the
  frame edge, rides the bottom border, or extends outside the frame.
- Colored accent rules and adjacent labels/callout text are placed with
  separate offsets, causing text to sit high or low relative to the line.
- A screenshot, UI capture, paper figure, or chart is present but its embedded
  labels are unreadable at exported-slide size.
- Wrapped text leaves a punctuation mark, one CJK character, or a two-character
  tail alone on the final line.
- A top accent rule, label, or decorative line is technically aligned by x/y
  but has no clear visual function, so it reads as detached from the title.
- The deck passes object-level checks while the contact sheet still shows weak
  rhythm, unclear focal points, or many slides that feel individually patched.

## Report Requirement

Add a short verdict before detailed findings:

```text
Visual verdict: Pass / Targeted fixes / Redesign required
Reason: <one sentence>
Score: <n>/16
Main blockers: <top 1-3 issues>
```

When the verdict is `Redesign required`, do not spend the main response on small
geometry fixes. State the design direction that should replace the current
layout grammar.

When the user finds an obvious alignment issue after a high score, treat the
previous review as an unstable workflow result. Update the layout stability
gate or script, create a regression note, and rerun the affected scenario before
claiming the deck is visually checked again.

When the user finds a cover title/subtitle spacing issue or a missing closing
page after review, treat it as a failed quality gate even if the automated
geometry report was clean. Add a regression note for title-block spacing or deck
structure and rerun the affected deck before handoff.

When the closing page exists but is only a generic content slide with visible
placeholder text such as `Closing`, treat it the same as a missing closing page.
Verify the final slide visually matches the selected branded closing/contact
page or contains intentionally authored audience-facing contact content.

When a sample-first style pack is under review, the verdict should say whether
the pack is approved for full-deck generation. If the user has not approved the
sample yet, do not report the full deck as complete; report the preview path,
chosen reference, known license status, and what approval is needed next.

When the issue is overall harmony or composition rather than a single measurable
box, the next report must include:

```text
Superseded verdict: <previous score/verdict and why it failed>
Grammar failure: <title block / grid / rhythm / focal point / component system>
Fix strategy: <redesign layout archetype / rebuild preview system / local patch>
Reviewer confidence: <human checked / screenshot judge checked / still uncertain>
```
