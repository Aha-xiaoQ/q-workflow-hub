# Q PPT Visual Review Rules

Use this checklist when reviewing exported slide images and automated reports.

## Readability

- Title text should be prominent but not crowd the top edge.
- On cover/title slides, check the whole title/subtitle block's visual center,
  not only its top coordinate. A cover can be technically inside bounds and
  still feel too high.
- On cover/title slides, leave visible air between the main title and subtitle.
  If the subtitle reads as attached to the title, lower it, shorten it, or
  split the line before handoff.
- On standard cover and section/transition slides, check that title and
  subtitle text stay inside the intended text-safe panel and do not overlap or
  visually press into template background art. A subtitle crossing into color
  artwork is a blocker even when object bounds do not geometrically overlap.
- Visible cover metadata should be audience-facing. Flag request-side hints
  such as duration prompts, mode labels, review labels, or duplicated
  classification text unless the presenter explicitly wants them visible.
- Body text should remain readable on a meeting-room screen.
- For generated PPT previews, component-library samples, and route-comparison
  decks, required visible text must be at least 9 pt. If the output needs
  smaller labels to fit, split the content across slides or move the detail to
  notes/source files instead of shrinking the type.
- Component-library evidence must be readable at slide scale. Do not count a
  multi-thumbnail gallery, contact-sheet crop, or compressed external-route
  page as validation evidence when the viewer must read labels inside the
  image. Split it into one large evidence image per slide, or mark the gallery
  as index-only and validate on separate pages.
- Small labels are acceptable only when they are secondary and not required for
  understanding.
- Required text must visibly separate from its background in the exported PNG.
  Use WCAG-style thresholds as a practical gate: about 4.5:1 for ordinary text
  and about 3:1 for large/bold display text. Dark captions on dark photos or
  panels are blockers, even when the font size is technically large.
- Avoid negative letter spacing and compressed text boxes.
- Manually inspect long CJK, English, or mixed-language lines in exported PNGs.
  If a line visually presses into a border, template art, or another object,
  add an intentional line break or shorten the wording.
- For translated decks, do not assume the source-language layout still fits.
  Review every title/body stack, colored row, card, source note, and bottom
  callout.
- Flag orphan punctuation, single-character final lines, or punctuation-only
  wrapped lines as warnings; treat them as blockers for polished decks.
- For peer cards, repeated bullets, process labels, compact rows, and tile
  groups, check punctuation as a group. Decide whether the group is
  phrase-style, usually no terminal punctuation, or sentence-style, terminal
  punctuation on comparable items. Flag mixed punctuation within the same
  visual group as a warning; treat obvious mixed style as a blocker for
  polished decks.

## Layout

- Keep key content away from slide edges unless the design intentionally uses
  bleed art.
- For generated or reusable PPT decks, ask whether the slide was built from a
  declared layout contract: safe area, layout boundary, rows/columns/zones,
  component slots, text/image slots, internal component grids, and, for
  diagrams, ports, connector lanes, and label-clearance constants. A slide that
  looks acceptable but is authored from scattered per-shape coordinates is a
  stability warning; after repeated user-found placement defects, it is a
  blocker.
- Grid-first applies to ordinary PPT pages, not only diagrams. Titles, body
  areas, screenshots, cards, tables, bottom callouts, and summary rows should
  be assigned to named zones or component slots before rendering. Do not
  approve a reusable page helper that centers children one by one after free
  placement.
- Page-region pressure is a layout failure even without geometric overlap.
  Recheck the title/subtitle stack, body diagram boundary, side rail, bottom
  callout, and footer as separate zones; if a clear component visually intrudes
  into another zone, move or resize the whole component instead of only moving
  the offending child.
- Align repeated modules, cards, labels, and diagram blocks.
- For any generated deck with repeated visual components, ask where the
  component positions are defined. If badge rows, cards, headers, or callouts
  are placed by slide-by-slide coordinates instead of a helper, treat new
  alignment defects as generator defects, not slide polish.
- For editable PPTX output, prefer actual PowerPoint groups for repeated
  multi-shape components after the helper lays out the internal grid. The group
  should be the editable component boundary for a step card, badge row, compact
  label row, or framed callout. Do not use grouping to excuse bad internal
  alignment, and make sure review tooling can inspect the group children.
- For generated rows, the number, title, and detail should be children of one
  row component. They should share a declared row height, center line, and
  vertical-anchor strategy. Do not accept separate y-offsets such as
  `num_y + 0.15`, `title_y + 0.10`, and `detail_y + 0.14` unless a rendered
  baseline check proves the visual centers still match.
- For note rows, bullet rows, icon-label rows, and right-side explanation
  lists, the marker and text must be one row component with a shared center
  line. A dot or circle that sits slightly above or below adjacent text is the
  same class of component defect as a miscentered number badge.
- For numbered circles, the number must be drawn by the circle-badge component:
  the text frame should share the circle's bounds or be centered by a helper
  against the circle center with a middle anchor. A manually nudged text box
  inside an oval is a blocker on generated decks.
- Compare the rendered PNG with the script's `layout_audit.csv` when available.
  If repeated title/header/rule positions drift numerically and the PNG report
  does not explain why, the review missed an alignment risk.
- For generated decks, check the repeated top header as a component: accent
  rule, section label, main title, subtitle, and page number should follow one
  explicit grid. A short decorative line that floats above every title is a
  blocker until tied to the title grid or removed.
- Main title positions should be stable across ordinary content slides unless
  the generator declares a different slide type. If title x/y positions drift
  without intent, fix the generator header helper rather than moving individual
  titles.
- Check visual centering, not only object bounds.
- For number badge + title/detail rows, verify the badge, title text, and
  paired detail text share one visual center line.
- For text inside cards, badges, or process boxes, verify the frame and text
  behave as one component. If the text appears separately nudged over the
  frame, treat off-centering as a component-authoring defect.
- For framed text, require a declared safe inset between the text box and frame
  edges. Text should not touch the border, ride the bottom edge, or cross
  outside the frame. In generated decks, the helper should calculate the
  content slot from the frame bounds before adding text. Treat "technically not
  touching" as insufficient when the rendered PNG still looks tight; enlarge
  the frame, shorten the text, or increase the inset until the component has
  visible breathing room.
- For short accent-rule + label patterns, verify the colored rule and adjacent
  label/callout text are generated by one helper or actual group and share one
  vertical center line. A text box that is consistently a little high or low
  relative to the rule is a component defect, not a local polish issue.
- For large cards, summary tiles, and three-column layouts, flag tiny corner
  number chips as warnings or blockers when the number is part of the structure.
  The number should scale with the card and align with the title row or an
  intentional side rail; it should not float as a small off-center decoration.
- For compact colored-label rows, verify the colored label and adjacent same-row
  text share one visual center line.
- For card systems with left colored strips or accent bars, verify the strip has
  a clear semantic role and does not substitute for real layout quality. If the
  card depends on a strip while typography, spacing, or alignment remains weak,
  mark it as a design-quality issue.
- Do not repair readability by dropping a large off-style background patch into
  the slide. On a dark style pack, a white rectangle behind content is a
  blocker unless the chosen reference grammar clearly uses that kind of
  semantic surface. Fix contrast through the palette, text color, font weight,
  spacing, stroke, shadow, or a matched dark/light component surface instead.
- For agenda and list pages, leave visible air between separator lines and the
  first list item.
- Agenda and section/transition pages must use the same navigation grammar.
  Flag a custom agenda paired with unrelated official template dividers, or an
  official agenda paired with custom dividers, as a blocker unless the review
  explicitly records that mixed style as intentional.
- For style-pack sample reviews, verify the sample includes enough component
  coverage to approve the pack: cover/title, agenda or navigation, section or
  transition, one representative content slide, and closing/contact. Do not
  approve a full-deck run from a sample that omits the closing/contact grammar.
- For non-company style packs, flag mismatched company logo, footer,
  classification, official dividers, or branded closing pages as blockers
  unless the request explicitly combines the style pack with that brand add-on.
- For stacked text inside a single panel, verify title and detail text have
  separate vertical space in the rendered PNG.
- For bottom callouts, check the sentence is vertically centered in the frame
  and does not touch the border. Summary panels at the bottom of a slide should
  use the same grouped component contract: frame, label, and body text should
  share a declared center line and generous internal padding.
- Shape-owned text is not automatically safe. If a callout, tag, node, or row
  helper moves text into the frame's own text frame, the helper must still set
  explicit left/right/top/bottom margins and a minimum component height. For
  compact PPT rows, use at least about 0.14 in vertical padding and enlarge the
  bar rather than allowing text to visually hug the border.
- For hard-gate, verdict, or rule-summary rows, the label and explanatory text
  must sit on a deliberate shared row/baseline, and the explanatory text must
  have intentional line breaks inside the safe width. A label floating above or
  below an overlong unwrapped sentence is a layout blocker, not a copy issue.
- For process/flow slides, verify connector lines share the visual center of
  the cards or nodes they join; numbers, labels, connectors, and cards should
  be generated from one component contract, not separate offsets.
- Do not put a multi-step process into one large shared band when the steps
  have connector lines. This makes the connectors read as floating lines inside
  a container. Use separate helper-owned step cards or nodes and connect their
  boundaries or center lines.
- For repeated process steps, inspect the authoring source when available. If
  the circle, number, title, body, and connector are individually positioned
  with unrelated offsets, require a helper-level fix before approving the
  sample for full-deck generation.
- For hub-and-spoke or central-control diagrams, confirm the hub is centered
  among its related nodes and visibly connects to every intended side.
- For bar/score comparison charts, check that series labels, bars, and numeric
  scores sit on shared row centers.
- For bar/score comparison charts, also check containment and parent-child
  spacing. The bar track must be sized from the chart/card slot with declared
  left and right insets; it must not extend past the frame or sit flush against
  the frame just because it snapped to a grid.
- For figure/media slots that contain simplified bars, screenshots, or chart
  placeholders, verify that the child content and the inner frame cooperate:
  bars stay inside the inner frame, the inner frame keeps air inside the outer
  card, and the layout contract records both relationships.
- Avoid nested card-on-card layouts unless the selected template requires them.
- Flag visible production notes, draft reminders, or source caveats that do not
  fit the intended audience.
- For complete generated decks, confirm the exported slide set includes the
  intended closing/contact page. A missing closing page is a deck-structure
  blocker even when all content slides render cleanly. A generic slide titled
  `Closing` is also a blocker if it does not visually match the selected
  template/navigation family's branded closing or intentionally authored
  contact page.

## Diagrams

- Arrows should point to the intended target and avoid crossing important text.
- Connector endpoints should sit close to the objects they connect.
- Use consistent line weights and arrowhead styles.
- Prefer a clear left-to-right or top-to-bottom flow.
- For program flowcharts, require standard symbol semantics: terminal
  start/end shapes, process rectangles, decision diamonds, and directed arrows.
  Every decision branch must have a visible `Yes`/`No` label or an equivalent
  short condition. If labels do not fit, split or simplify the flow instead of
  accepting unlabeled branches.
- For state-machine diagrams, require an initial node when entry matters, named
  states, directed transition arrows, and transition labels such as
  `event [guard] / action` in readable whitespace. A state diagram without
  arrowheads or transition conditions is a blocker, even if the boxes align.
- State-machine transition labels should be close to the transition they name,
  usually just above or beside the line, but they must not sit on top of the
  stroke. Prefer a single straight or diagonal transition over a multi-corner
  route when no obstacle requires the extra bends. For diagonal transitions,
  the label should usually rotate with the diagonal and sit near the transition
  midpoint, offset parallel to the line so the text does not cover the stroke,
  while preserving normal reading direction.
- For PPT-native flow/state labels, use a consistent connector-label clearance
  across horizontal, vertical, and diagonal lines. At normal 16:9 slide scale,
  the default visual gap from connector stroke to nearest text-box edge should
  be about 0.06-0.10 in, with 0.08 in as the target. If that gap causes text to
  touch the line, fix the diagram scale, font size, label length, or topology
  before accepting inconsistent spacing.
- Reject tiny connector doglegs when a straight connection is intended. A
  barely visible bend, jog, or waypoint near a node usually means the source
  route/port is wrong; fix the source route or simplify the topology.
- In framed overview cards or component-library cards, reject long prose that
  forces small type or visually overruns the frame. The fix is to shorten,
  split, or resize the component, not to accept a cramped catalog card.
- For component-library and route-comparison decks, verify route editability:
  every promoted route preview must keep readable export scale and a durable
  source. A fuzzy, cropped, half-width, or overly flat render should be
  redrawn as PPT-native/grid-first content or split into a full-size route
  evidence page before promotion.
  slide display PNGs are acceptable, but the package must include a human-
  editable source that can be changed and re-exported. Bitmap-only generations
  are rejected as component-library routes even if their current slide preview
  looks clean.
- For component-library previews, do not place several labeled diagram
  screenshots as small thumbnails on one slide. If labels matter, each route or
  component gets its own slide or a large crop; a contact-sheet view is only an
  index, not validation evidence.
- In dense electronics block diagrams, avoid decorative horizontal rules inside
  every module box; they make the box feel crowded and are not useful
  hierarchy. Prefer typography, spacing, or a small semantic color marker.
- Do not put boxed labels on top of connector lines in dense diagrams. Small
  label boxes can hide wires, arrows, or module borders. Use unboxed short
  labels in whitespace lanes, a legend, or no edge label.
- Route major lines around blocks, often through lower or outer lanes. A line
  that visually presses on a box, crosses the box, or makes the box look
  covered is a diagram-quality issue even if the connector endpoint is valid.
- For directly generated PPT diagrams, check whether the diagram is simple
  enough for PPT-native authoring. Few branches and clear connectors are
  acceptable; dense electronics blocks, many branch paths, feedback loops, or
  nontrivial routing should be marked as needing an external layout/source
  route before PPT restyling.
- For PPT diagrams reproduced from a reference image, check whether the
  reference's grid was preserved: repeated box sizes, row centerlines, column
  positions, dashed group boundaries, and arrow centerlines should visibly
  align. If objects are placed freely and drift from the reference's regular
  alignment, mark it as a layout-quality failure even when there are no
  overlaps.
- For quantized PPT block diagrams, verify that modules snap to an invisible
  grid, use only declared box sizes, connect from side-center ports, and keep
  connectors on shared grid lanes. The review should check the declared grid
  boundary, not only the visible objects: the boundary should be sized from the
  intended figure, centered inside the content safe area, and used as the
  source for every module, region, port, and lane. Node cells and connector
  lanes may be offset from each other, but the relationship should be explicit.
  The final diagram should not touch the slide canvas, outer content frame, or
  section boundary unless the declared grid intentionally uses that edge.
- For quantized PPT block diagrams, verify the relationships between adjacent
  grid systems. A local subgrid symbol such as a PV panel icon must have
  balanced internal gutters when it is meant to read centered. A branch fan-out
  must preserve the whole route centerline: upstream source, hub, straight
  connector, bus, and middle target should align when they visually read as one
  continuous path.
- For timing diagrams, vertical trigger markers must coincide with the actual
  waveform transition edge they describe. If a marker is near but not on the
  rising/falling edge, fix the generator to share the waveform edge coordinate
  instead of nudging the marker by hand.
- Score automatic graph-layout outputs by diagram family. D2-style output may
  be usable for state machines or simple logic diagrams after enlarging text,
  but dense electronics block diagrams usually need PPT-native restyling when
  fonts are small, labels are busy, or curved lines compete with blocks.
- Do not accept tiny unreadable figures or screenshots as visual evidence. If
  key labels cannot be read in the exported PNG, require enlarging/cropping the
  figure, replacing it with a simplified diagram, or moving the original into
  notes/appendix material.

## Tables

- Avoid dense tables when a visual explanation works better.
- Keep table body text large enough to read.
- Use row and column spacing that prevents text from touching borders.
- Check the table header/body transition. A heavy header band attached directly
  to tiny body rows can feel visually harsh even when the grid aligns; add
  breathing room, subtler header fill/rules, or clearer row rhythm.
- Avoid table headers whose border looks darker on three sides than the rest
  of the grid. Use a consistent subtle grid, or a deliberate single bottom
  separator, so the header does not look accidentally framed.

## Design Quality Layer

- Visual hierarchy: the first thing a viewer sees should match the slide's core
  message.
- Craft quality: repeated objects should share alignment, spacing, corner
  radius, line weight, and type treatment.
- Density and function: each slide should have one primary idea and enough
  whitespace for the intended viewing context.
- Brand/template consistency: typography, footer, color use, and light/dark
  intent should support the message rather than look pasted on.
- Audience fit: visible slide text should match the target audience; delivery
  notes and production guidance belong in notes or reports.
- Cliche avoidance: avoid default purple-blue gradients, glowing orbs,
  circuit-board wallpapers, robot faces, and emoji-heavy visuals unless the
  user explicitly asks for that style.
- Representative-slide review: for long generated decks, review one
  title/section slide and one dense content slide before applying the grammar
  across the whole deck.

Each finding should include:

- slide number
- issue type
- object or visual location
- severity: `info`, `warning`, or `blocker`
- suggested fix
