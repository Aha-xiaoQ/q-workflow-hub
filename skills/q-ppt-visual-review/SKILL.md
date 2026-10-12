---
name: q-ppt-visual-review
description: Review PowerPoint decks visually and structurally. Use when Codex generates, edits, validates, or reviews PPTX files and needs to catch unreadable fonts, crowded layouts, margin violations, overlapping text or shapes, clipped content, poor alignment, arrow/connector problems, text overflow, or slide image export issues before handoff.
---
# Q PPT Visual Review

Use this skill after any meaningful PPT generation or visual edit. The first
pass should produce a visual issue report, not silently rewrite the deck.

## Review Path

1. Inspect the actual PPTX structure with `python-pptx` or the bundled script:
   `python <skill-dir>\scripts\ppt_visual_review.py <deck.pptx> --out <report-dir>`.
   The script scans geometry/text including group children and attempts Windows
   PowerPoint PNG export. Its findings are heuristics, not visual acceptance.
2. Inspect exported slide images at intended viewing size. Use
   `references/visual-rules.md` for applicable text, component, diagram, table
   and visual-language checks. Clipping, unreadable required text/figure labels,
   unintended overlaps, bad connections and off-center repeated components
   block acceptance. Fix the source/helper and render again.
3. Select additional evidence only when triggered:
   - Generated, high-visibility, unfamiliar-style or user-questioned deck:
     `references/deck-quality-gate.md`; verdict is shippable, targeted fixes or
     redesign. Geometry success cannot approve weak design.
   - Repeated alignment/centering misses:
     `references/layout-stability-gate.md`; inspect helper/component ownership,
     grid, safe insets and group children. After two unsuccessful repair rounds,
     mark the prior review unstable and prove a representative sample before
     further full-deck generation.
   - Windows PNG export failure: `references/png-export.md`; try its supported
     recovery paths and verify PNG count before declaring review unavailable.
4. For high-visibility, translated or dense decks inspect every exported slide.
   For a bounded edit inspect changed slides and affected shared families;
   preserve known-regression coverage. Report actual coverage and remaining gaps.
5. Report slide number, issue, object/location, severity and concrete fix.
   Review-only requests produce findings; authorized repairs proceed directly,
   then render and review the affected output without redundant approval.

## Text And Language Changes

After any PPT text edit, run a same-family text style diff before accepting
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

For translated decks, include language-specific review before any Pass verdict: visible slide text, PowerPoint Notes, generated diagrams, screenshots, and bitmap figures must match the target language or have slide-specific accepted exceptions. An English deck with Chinese Notes or meaningful Chinese text baked into images is blocked even if exported PNG geometry passes.
For English decks, also review title wrapping visually: large titles, section titles, agenda labels, and short headings must not inherit source-language line breaks or wrap when they can reasonably fit on one line. Treat avoidable English title wrapping as a blocker, not a cosmetic preference.


## Common Visual Floor

Keep one layout contract for repeated components: helper-owned frame/text with
safe insets, shared centerlines and groups where useful for editable output.
Inspect source and rendered result; grouping cannot hide arbitrary offsets.
Required body/caption text should reach about 4.5:1 contrast, large/bold display
text about 3:1, against its actual local background. Use the chosen visual
grammar rather than an off-style patch. Reject unreadable embedded labels,
unintended CJK tails, source-language wrapping, orphan punctuation and floating
connectors. Detailed component cases have one owner in `visual-rules.md`.

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
