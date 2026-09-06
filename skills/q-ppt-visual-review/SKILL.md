---
name: q-ppt-visual-review
description: Review PowerPoint decks visually and structurally. Use when Codex generates, edits, validates, or reviews PPTX files and needs to catch unreadable fonts, crowded layouts, margin violations, overlapping text or shapes, clipped content, poor alignment, arrow/connector problems, text overflow, or slide image export issues before handoff.
---
# Q PPT Visual Review

Use this skill after any meaningful PPT generation or visual edit. The first
pass should produce a visual issue report, not silently rewrite the deck.

## Review Process

1. Inspect the PPTX structure with `python-pptx` or a project validation script.
2. Export slide images when PowerPoint is available.
3. Review exported images or screenshots, not only shape coordinates.
4. After any PPT text edit, run a same-family text style diff before accepting
   the deck. Compare edited labels against peer labels for `font.name`, size,
   bold, color, alignment, vertical anchor, margins, and text order. A text-only
   change that resets fonts, bold, or color is a visual regression even when the
   geometry report has no blocker.
   For diagram slides, also require a role-based font contract before editing:
   identify edited labels by role/content and peer family, not only by shape ID.
   Do not choose fonts ad hoc by the latest text content. Audit all edited
   component families and flag `font.name=None`, theme/default fallback,
   unintended bold/regular changes, or peer labels using different font
   families without a recorded exception.
5. Run the deck quality gate in `references/deck-quality-gate.md` for generated,
   high-visibility, unfamiliar-style, or user-questioned decks. A review is not
   complete until it states whether the deck is shippable, needs targeted fixes,
   or needs redesign.
6. If a generated deck has missed obvious alignment or centering issues, run
   `references/layout-stability-gate.md`. The review must check the repeated
   header/title/footer contract, component center lines, and whether the
   generator uses reusable layout helpers instead of copied manual offsets.
7. If a generated deck uses repeated rows, badges, process steps, cards, or
   callouts, inspect the authoring source for component ownership before giving
   `Pass`: number/text/circle/card parts should be placed by one helper or
   layout contract, not by separate per-element coordinates. Any visible
   centering miss in a repeated component is a generator defect and a blocker
   until the helper is fixed and regenerated.
8. For editable PPTX output, prefer actual PowerPoint groups for repeated
   multi-shape components after the helper lays out the internal grid. A step
   card, badge row, compact label row, or framed callout should move as one
   component when selected. Do not use grouping to hide manual-offset defects;
   the review script and report must still inspect group children.
9. For custom/generated style packs, check readability and visual grammar
   together. Do not accept a large foreign-color panel, such as a white
   rectangle on an otherwise dark style, as a readability fix unless it is an
   intentional semantic surface in the chosen reference grammar. Prefer
   palette contrast, typography weight, spacing, and matched component
   surfaces.
10. Treat text/background contrast as a release gate. Ordinary required text
   should use about 4.5:1 contrast or better; large/bold display text should
   use about 3:1 or better. Dark text on a dark photo/panel, pale text on a
   pale panel, or any caption that cannot be read in the exported PNG is a
   blocker.
11. For framed text, cards, badges, callouts, and process boxes, verify the
    frame and its text are authored as one component: shape-owned text or a
    helper-owned grouped component. Text must reserve a safe inset from every
    frame edge and must never touch or cross the border.
12. For short accent-rule + label patterns, verify the rule and label are a
    helper-owned component or group with one declared vertical center line.
    Do not accept copied offsets where the text sits slightly above or below
    the colored rule.
13. For bottom callouts and summary panels, require a grouped component with
    generous internal padding and vertically centered text. A text box that is
    merely inside the frame is not enough if it visually rides the top or
    bottom edge.
14. For chart bars, figure placeholders, media slots, note rows, and
    icon-label rows, review the parent-child relationship, not only the child
    coordinate. Bars and tracks must be sized from their parent slot with
    visible inset; dots/circles/icons and adjacent text must share one
    helper-owned center line.
15. For screenshots, paper figures, UI captures, and charts, inspect embedded
    labels at exported-slide size. If the labels are required and unreadable,
    enlarge/crop the figure, rebuild it as a simplified diagram, or move it to
    notes/appendix material.
16. For wrapped CJK or mixed-language text, reject punctuation-only final
    lines, one-character final lines, and visually squeezed short tails in
    polished decks. Fix by rephrasing, widening the slot, or adding an
    intentional line break.
17. For process/flow slides, check whether connector lines attach to separate
    step cards or nodes. Do not accept a single large process band with short
    connector rules floating between text clusters unless the chosen reference
    grammar intentionally uses that pattern.
18. For grid-first diagrams, review relationship continuity between related
    subgrids and lanes. A local icon can be grid-snapped but still off-center
    if its internal gutters are uneven; a branch fan-out can be symmetric but
    still wrong if the upstream source-to-hub line is half a row off the middle
    branch centerline.
19. If the same deck or generator has already gone through two or more visual
    repair rounds and the user still finds placement or harmony problems, stop
    treating it as local polish. Mark the previous review result unstable,
    reduce the next pass to a representative sample or layout preview, and do
    not give `Pass` until the sample proves the component/grid contract.
20. Report issues by slide number, issue type, object/location clue, severity,
    and recommended fix.
21. Edit the deck only after the issue report is understood.

For translated decks, include language-specific review before any Pass verdict: visible slide text, PowerPoint Notes, generated diagrams, screenshots, and bitmap figures must match the target language or have slide-specific accepted exceptions. An English deck with Chinese Notes or meaningful Chinese text baked into images is blocked even if exported PNG geometry passes.
For English decks, also review title wrapping visually: large titles, section titles, agenda labels, and short headings must not inherit source-language line breaks or wrap when they can reasonably fit on one line. Treat avoidable English title wrapping as a blocker, not a cosmetic preference.

For high-visibility, translated, or dense decks, review every exported PNG for
known visual regressions: number badge/title/detail row centering, compact
colored-label row centering, agenda/list spacing near separator lines, long
section subtitles, missing intentional line breaks, bottom callout centering,
source-note cleanup, orphan punctuation, peer-card punctuation consistency,
numeric text not centered inside circles, tiny off-center number chips inside
large cards, decorative left color strips that do not serve a clear hierarchy
role, large off-style background patches used only to force contrast, and
translated text overflow inside reused layouts.

## Script

Use the bundled script for a deterministic first pass:

```powershell
python <skill-dir>\scripts\ppt_visual_review.py <deck.pptx> --out <report-dir>
```

The script:

- reads slide geometry and text shapes, including children inside grouped
  shapes;
- flags likely small fonts, edge-margin violations, off-slide objects, and
  text-shape overlaps;
- flags low text/background contrast against containing frames or panels;
- flags text boxes that are too close to, or extend beyond, their containing
  frame;
- flags short accent-rule + adjacent label/callout text pairs that do not share
  one center line or middle-anchor strategy;
- flags likely text overflow or clipped descenders from text length, font size,
  and box height;
- flags likely orphan punctuation, single-character CJK tails, and very short
  wrapped final lines;
- flags screenshots or figures that are likely too small for embedded labels
  to be readable;
- flags repeated title/header drift and top accent rules or section labels that
  are visually detached from the main title grid;
- flags repeated generated-row contract issues where number badges, titles, and
  detail text do not share one center line or middle-anchor strategy;
- flags numeric circle text that is manually nudged inside an oval instead of
  using one circle-badge component;
- flags large light panels on dark visual systems that look like readability
  patches rather than intentional style-pack surfaces;
- flags likely shared process bands where connector rules float inside one
  wide container instead of joining separate step cards or nodes;
- writes a `layout_audit.csv` evidence table for repeated title/header/rule
  positions so alignment drift can be compared across runs;
- attempts PowerPoint COM export to PNG on Windows when available;
- writes a Markdown report with findings.

Automated findings are heuristics. Treat exported images and the report
together as the review surface.

If a deck looks weak, generic, amateur, or visually inconsistent in the exported
PNGs, mark it as a design-quality failure even when the geometry report has no
blockers. Use `references/deck-quality-gate.md` for the required scorecard and
anti-patterns.

If Windows PNG export fails or appears unavailable, read
`references/png-export.md` before declaring the deck unreviewable. The recovery
path covers the native Python command, the built-in PowerShell COM fallback,
PowerPoint open checks, generated-deck repair/bisect, and PNG count
verification.

## Visual Rules

Use `references/visual-rules.md` for the checklist. At minimum verify:

- no content is clipped or outside the slide;
- body text is readable for the intended display context;
- main content keeps comfortable margins;
- text boxes and diagrams do not overlap unintentionally;
- top header elements, section labels, title baselines, and accent rules follow
  one explicit grid across the deck;
- generated/reusable slides have a declared layout contract rather than
  scattered per-shape coordinates;
- repeated labels, badges, rows, and cards are visually centered and aligned;
- translated content has enough room after line wrapping;
- translated decks have target-language speaker notes, and target-language screenshots/figures when those images contain meaningful labels or UI text;
- default bilingual decks have CN/EN variants for text-bearing diagrams and images, or documented shared text-free assets/exceptions;
- English title, section, agenda, and short heading text does not wrap unnecessarily or carry source-language line breaks;
- lines and arrows connect to intended objects and avoid key text;
- slide density is balanced;
- placeholders, production notes, and external window artifacts are absent.

## Output

Save reports under a project-local validation or reports folder unless the user
specifies another path. Do not commit exported slide images unless they are
intentional deliverables or useful review artifacts.

After structural readback and visual review evidence exist, open the final PPTX
for local preview by default when the environment allows and the user has not
asked for a no-GUI handoff. On Windows this is typically
`Start-Process -FilePath <deck.pptx>`. If opening requires platform approval,
request the narrowest approval; if PowerPoint or file association is
unavailable, report the exact PPTX path plus the visual review folder and do
not imply that preview happened.
