# Component Alignment Regressions

Use this reference when a generated deck passed review but a user later finds
obvious alignment or centering problems in repeated components.

## 2026-06-17 Numeric Rows And Circle Badges

Trigger: a sample-first generated PPT had visible agenda-row misalignment and
process-step numbers that were not centered in their circles after a previous
visual gate recorded a pass.

Failure mode:

- The generator placed a row background, number, title, and detail with separate
  y-offsets instead of one row helper with a shared center line.
- The process-step circle and number were separate objects; the number text box
  was nudged inside the circle instead of sharing the circle bounds with a
  middle anchor.
- The automated report had centerline warnings, but manual review treated them
  as low-priority noise because there was no rule that made generated-component
  centerline misses a blocker.

Required future behavior:

- Inspect the authoring source for repeated rows, circle badges, cards,
  callouts, and process steps before approving a generated style sample.
- Treat centerline warnings in repeated components as blockers unless the
  full-size PNG proves the rendered result is intentionally aligned.
- Fix the component helper and regenerate. Do not patch only the final PPTX.
- Record the superseded verdict in the quality gate when a previous pass missed
  the issue.

Validation scenario:

1. Build or locate a generated slide with agenda rows and process-step badges.
2. Run `scripts/ppt_visual_review.py` and export PNGs.
3. Confirm the report flags numeric rows without shared middle anchors and
   numeric circle text boxes that do not share circle bounds.
4. Inspect the affected full-size PNGs before marking the deck shippable.

## 2026-06-17 Contrast Patch On Dark Style

Trigger: after the numeric alignment fix, a representative content slide used a
large white rectangle behind process steps in an otherwise dark style pack. The
text was readable, but the surface looked unrelated to the surrounding visual
grammar.

Failure mode:

- The generator treated readability as a local text/background problem instead
  of a style-system contrast problem.
- A large light panel made the process row legible but broke harmony with the
  dark-tech style.

Required future behavior:

- Do not use a foreign-color panel as the first fix for readability.
- First adjust text color, font weight, component surface, stroke, shadow,
  spacing, or palette contrast inside the selected style grammar.
- If a large light panel is used, the style contract must name its semantic role
  and show that the reference/template uses the same kind of surface.

Validation scenario:

1. Build or locate a dark-style generated slide with a large light rectangle.
2. Run `scripts/ppt_visual_review.py`.
3. Confirm the report flags the panel as a potential style-grammar break.
4. Inspect the PNG and either replace the panel with matched component surfaces
   or document why the selected template intentionally uses it.

## 2026-06-17 Floating Connectors In Shared Process Band

Trigger: after removing a white readability patch, a representative content
slide still used one wide process band with short connector lines between four
step text clusters. The layout was technically aligned, but the connector line
looked suspended inside the band instead of belonging to the step relationship.

Failure mode:

- The generator treated the process row as one container plus independent
  badges, labels, bodies, and connector segments.
- The visual review checked circle centering and panel color, but did not ask
  whether the connectors were attached to actual step components.
- A shared band made the relationship weaker than separate step cards/nodes.

Required future behavior:

- For generated process flows, define a helper-owned step card or node
  component that owns its badge, number, title, body, accent, and surface.
- Draw connectors between adjacent component boundaries or declared center
  lines, not as loose rules floating between text clusters.
- Treat a large shared process band with multiple connector segments as a
  warning or blocker until the full-size PNG proves it is intentional in the
  selected reference grammar.

Validation scenario:

1. Build or locate a generated process slide with multiple steps and connector
   lines.
2. Run `scripts/ppt_visual_review.py`.
3. Confirm the report flags likely shared process bands with floating connector
   segments.
4. Inspect the full-size process slide PNG and verify each connector visually
   connects separate cards or nodes before approving the style sample.

## 2026-06-17 Source Components Need Editable Groups

Trigger: after the visual process-card layout was fixed, Xiao Q confirmed the
slide looked good and pointed out that grouping is useful if it makes the
component easier to operate.

Failure mode:

- A source-level helper can make a repeated component visually correct, but the
  final editable PPTX can still contain loose shapes.
- Loose card surfaces, badges, numbers, and text are easy to separate during
  manual adjustment, recreating the same alignment drift that the helper fixed.
- If review tooling does not recurse into groups, grouping can also hide child
  text, overflow, or badge defects from structural checks.

Required future behavior:

- When the output is editable PPTX and the generation library supports it,
  group repeated multi-shape components after the helper has laid out the
  internal grid.
- Name the group and important child shapes when possible, so readback and
  debugging can confirm the component boundary.
- Keep relationship connectors separate when they represent links between
  components, unless a larger flow-level group is intentionally needed.
- Make review tooling inspect group children. Do not treat grouping as proof of
  alignment by itself.

Validation scenario:

1. Build or locate a generated PPTX with repeated multi-shape cards, badge
   rows, callouts, or process steps.
2. Read back the PPTX and confirm each repeated component is a `GroupShape` or
   an equivalent editable component boundary.
3. Run `scripts/ppt_visual_review.py` and confirm warnings still name child
   shapes inside groups, such as `shape 11.4`.
4. Inspect the rendered PNG to verify the grouping preserved, rather than
   concealed, internal alignment.

## 2026-06-18 Rule Labels, Tight Frames, And Bottom Panels

Trigger: a regenerated dark-style RT-Thread deck fixed border overflow and
contrast issues, but Xiao Q still found tight framed text, accent-rule labels
that were not consistently centered, and a bottom summary panel whose text did
not sit centered in the frame.

Failure mode:

- The generator used a reusable card helper, but the safe inset was only enough
  to avoid structural warnings, not enough to look comfortable in the rendered
  PNG.
- Header, card, command-panel, and bottom-callout accent rules were authored
  with repeated manual y-offsets instead of one rule-label centerline helper.
- One summary panel was handwritten as a box plus independent text boxes, so it
  escaped the bottom-callout component contract.
- The previous review script checked several row centerlines but did not check
  short accent-rule + adjacent label/callout centerlines.

Required future behavior:

- Treat "not touching the border" as a minimum, not a pass. Framed text needs
  visible breathing room; increase component inset, enlarge the frame, or
  shorten the text when the PNG still looks tight.
- Use one helper for colored rule + label/callout patterns. The helper should
  compute a band center, place the rule on that center, create the text with a
  middle anchor, and group the result when the PPTX should remain editable.
- Bottom summary panels should use a grouped frame/label/body component with a
  declared centerline, not hand-authored box and text offsets.
- Add or rerun a script check for short accent-rule + adjacent label/callout
  centerline drift before marking a generated deck visually checked.

Validation scenario:

1. Build or locate a generated slide with card labels, command-panel labels,
   and a bottom callout or summary panel.
2. Run `scripts/ppt_visual_review.py` and export PNGs.
3. Confirm the report warns when a short accent rule and adjacent text do not
   share a centerline or middle anchor.
4. Inspect the full-size PNGs for tight-looking framed text even when the
   geometry report is clean; fix the component helper and regenerate.
