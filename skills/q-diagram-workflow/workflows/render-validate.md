# Render And Validate

## Structural Checks

- Run source parser or syntax check when available.
- Search for stale text, wrong voltages, old board names, and placeholder labels.
- For PPT connection-diagram text, define a role-based font contract before
  editing and validate against that contract afterward. The contract must map
  component roles to fonts and identify shapes by role/content rather than
  stale shape IDs, for example main title, board titles, board subtitles,
  legend labels, pin boxes, signal labels, connector labels, and bottom device
  labels. Do not choose a font from the text language alone or from the latest
  edited shape. Mixed Chinese/English labels must use the family assigned to
  their component role; if a peer component uses explicit styling, a `None`,
  theme/default, or ad-hoc fallback font is a validation failure.
- For PPT text edits, preserve or explicitly reapply the original style before
  saving. Do not use a bare `shape.text = ...` replacement as a final edit
  unless a style readback confirms the expected font family, size, bold state,
  color, vertical anchor, alignment, and margins. When changing a label inside a
  component family, compare it against a peer shape from the same family, such
  as left/right board titles or bottom device labels.
- Keep labels inside boxes short; put long explanations in surrounding text.
- Avoid edge labels when the line crosses a dense area.
- For generated or reusable PPT outputs, verify that the source contains a
  layout contract or helper-owned grid before visual approval: slide safe area,
  layout boundary, rows/columns/zones, component slots, text insets, ports,
  connector lanes, and label-clearance constants as applicable. If the source
  only contains free per-shape coordinates, mark the layout as unstable even if
  the current PNG looks acceptable.
- For ordinary PPT pages, check that titles, body zones, cards, tables,
  screenshots, bottom callouts, and repeated rows derive from named page zones
  or components rather than copied manual offsets.
- For generated diagrams and pages, verify relationship constraints in
  addition to grid snapping: local symbol gutters are symmetric when intended,
  related connector segments share one centerline, child bars/figures stay
  inside parent slots with declared inset, and dot/label or badge/text pairs
  are emitted by one centerline-owned component.
- For repeated connection-diagram rows, verify the layout contract numerically:
  equal row-center spacing, matching left/right endpoint centerlines, symmetric
  board-edge gutters, stable label clearance above the line, and no endpoint or
  label overlap. Do this after any local correction, because a single moved row
  can break the whole stack.
- For PPT-native connector diagrams, inspect the saved PPTX after every save to
  confirm arrowheads are structural, not only visual. Count or query connector
  `headEnd` / `tailEnd` definitions and verify expected direction counts before
  accepting the diagram.
- Do not treat arrowhead counts as an arrow-direction pass. Build an explicit
  route-to-direction table such as `PWM -> driver`, `current sense -> MCU`,
  `external power -> board`, and `driver -> motor`, then compare that semantic
  table against the rendered PNG or a known PowerPoint head/tail mapping. If a
  user reports reversed arrows, swap the structural mapping and re-export; do
  not change spacing or labels during that fix.
- For bidirectional connectors, verify both structure and readability: the
  saved source must contain arrowheads at both ends, the rendered shaft must be
  long enough that the double arrow is visually obvious, and nearby protocol
  labels such as `UART` should sit to the side of the connector instead of
  reducing arrowhead clearance.
- After editing an editable figure source, re-export the rendered artifact and
  verify the PNG/PDF timestamp is newer than or equal to the source timestamp.
  A stale export is a failed handoff even when the source file is correct.
- For PPT component-library previews, verify editability at the route level:
  the displayed slide may contain PNGs, but each route must keep a human-
  editable source such as PPT shapes, `.drawio`, `.svg`, `.d2`, `.dot`,
  Mermaid, PlantUML, WaveDrom, WireViz, or another durable source. Reject
  bitmap-only routes.
- For program flowcharts, use a standard subset deliberately: terminal for
  start/end, rectangle for process/action, diamond for decision, and arrows for
  control flow. Decision exits must be labeled with `Yes`/`No` or a short
  condition; an unlabeled branch is a failed flowchart, not a styling choice.
- For state machines, include an initial node when the entry condition matters,
  named states, directed transition arrows, and short transition labels in the
  `event [guard] / action` style when applicable. Removing labels or arrowheads
  to reduce clutter makes the diagram no longer usable as a state-machine
  example.

## Visual Checks

Inspect the rendered image or slide export:

- the central task is clear at first glance;
- after any local fix, the whole figure is reviewed again for side effects
  introduced by changed layer order, stroke weight, radius, or masking;
- the main boards or modules are visually dominant when they carry most of the
  connections;
- no text overlaps;
- no labels sit on top of wires or arrows;
- framed text is short enough and large enough to read at the target slide
  size; long prose that spills past a card or looks cramped fails even when a
  geometry check misses it;
- arrow direction matches signal ownership;
- font size is readable at the target page or slide size;
- required visible text in generated PPT previews and component-library samples
  is at least 9 pt; if not, split the content, crop/enlarge the figure, or move
  detail to notes/source rather than shrinking the text;
- font sizes and weights are consistent for equivalent label types;
- equivalent label types also keep the same intended font family and color; structural review must flag any label whose `font.name`, `font.bold`, or text color falls back to theme/default while its peers use explicit styling;
- arrow stroke widths and arrowhead sizes are consistent and proportional;
- connector labels are unboxed or placed in a clear whitespace lane; small
  boxed labels on top of lines are rejected when they hide other wires, arrows,
  or blocks;
- connector routes do not contain tiny accidental doglegs. If a connection
  should be straight, fix the source ports/waypoints or simplify the topology
  until the rendered route is visibly straight;
- state-machine transition labels sit close to their transition line, usually
  just above or beside it, but never on top of the stroke. If a transition
  between two distant states can be read as one straight diagonal line, prefer
  that over a multi-corner elbow route. For diagonal state transitions, rotate
  the label to follow the diagonal and center it along the transition span, but
  offset it slightly parallel to the line so the text never covers the stroke.
- For PPT-native state-machine and flow labels, use a consistent visual label
  clearance from connector strokes: start with about 0.06-0.10 in, with
  0.08 in as the normal target for horizontal, vertical, and diagonal
  transitions at 16:9 slide scale. Treat this as a visual gap between the line
  stroke and the nearest text-box edge, not as a center-to-center distance. If
  the label would touch the line, first scale the diagram, shorten the label,
  or adjust font/box proportion before accepting a larger gap or rerouting.
- For generated connector labels, confirm the label position is derived from
  the connector segment: horizontal labels use the segment midpoint plus a
  vertical clearance, vertical labels use the segment midpoint plus a
  horizontal clearance, and diagonal labels use the segment midpoint, segment
  angle, and normal offset. A label that is merely close to a line after manual
  nudging is not stable enough for reuse.
- dense block diagrams do not use decorative horizontal rules inside every
  module box; if rules make the box feel crowded, use cleaner typography or a
  small semantic color mark instead;
- major connector lines use clear lanes around modules, often lower or outer
  lanes, and do not visually press on or cover the boxes they connect;
- power, ground, USB, and motor wires are visually distinct;
- every visible physical connector has both its function and connector ID when
  that information is available;
- legends do not collide with content;
- image background is intentional, usually white for training docs.
- automatic graph layouts such as D2 are scored by diagram family. They may be
  acceptable for state machines or simple logic diagrams, but dense electronics
  block diagrams should be restyled or rejected when font size, curves, or line
  routing compete with the blocks.
- component-library previews that contain labeled diagram renders should not
  validate multiple small thumbnails on one slide. Put each labeled diagram on
  its own slide or crop/enlarge the render so labels are readable at slide
  size.
- tables use readable type and a smooth header/body transition; a harsh header
  band attached to tiny body text is a design-quality failure.
- for grid-first diagrams, the declared grid boundary is centered in the
  content safe area, node cells and connector lanes are visible in the final
  alignment, side-center ports are respected, and branch/bus lines do not rely
  on ad hoc bend points.
- for grid-first diagrams, branch symmetry must include the whole route, not
  only the final fan-out. If downstream branches are centered on one target
  row, the upstream source node, hub node, and source-to-hub connector must
  share that centerline unless a deliberate offset is documented.
- for internal diagram symbols such as PV panels, IC icons, connector headers,
  or small charts, validate the local subgrid's visual gutters. A symbol can
  be grid-snapped and still look wrong if one side has an extra cell of air.
- for grid-first ordinary pages, the declared page boundary is centered in the
  content safe area, header/body/footer zones remain stable, repeated
  components use one helper or group, text/image slots reserve readable space,
  and no card/callout/table text visually presses against borders.
- for grid-first ordinary pages, inspect parent-child relationships: bars stay
  inside chart/media frames with safe left/right/top/bottom inset, long tracks
  are sized from the parent slot instead of fixed widths, and bullet/dot rows
  align marker and text on one centerline.
- for timing diagrams, trigger/marker vertical lines are generated from the
  exact same x-coordinate values as the waveform rising/falling edges they
  annotate. Do not hand-place a nearby marker; even a tiny visible gap between
  marker and edge is a timing-diagram defect.
- for flowcharts, every branch from a decision is visibly connected to the
  decision boundary and has a branch condition. Use a simpler one-page flow
  rather than shrinking text or hiding branch semantics.
- for state-machine diagrams, every transition that changes state has a visible
  arrowhead and an event, guard, or action label placed in whitespace near the
  connector. A collection of rounded rectangles connected by unlabeled lines is
  rejected even when it has no overlaps.

## Tool Failure Policy

If a renderer or screenshot tool is missing or fails:

- do not claim final visual validation;
- simplify the source rather than adding more manual positioning;
- keep an editable or text source for later rendering;
- tell the user exactly what was and was not verified;
- give the user the official install/download entry for the missing tool, plus a
  local fallback route when possible, instead of stopping at "not installed."

Common official install/download entries to provide when relevant:

| Tool | Official entry | Typical local command or note |
|---|---|---|
| D2 | `https://d2lang.com/tour/install/` | Prefer an OS package manager or approved local installer; verify with `d2 --version`. |
| Graphviz | `https://graphviz.org/download/` | Windows package ID: `Graphviz.Graphviz`; verify with `dot -V`. |
| Mermaid CLI | `https://www.npmjs.com/package/@mermaid-js/mermaid-cli` and `https://github.com/mermaid-js/mermaid-cli` | Requires Node/npm; verify with `mmdc --version` or a bounded `npx` smoke test. |
| draw.io Desktop | `https://github.com/jgraph/drawio-desktop/releases` | Windows package ID: `JGraph.Draw`; use manual editor/export if CLI export is blocked. |

If company policy, permissions, or network access blocks installation, record
the exact missing command, the official entry, and which source files were kept
for later validation.

## Commit Gate

Before committing diagram changes:

- run `git diff --check`;
- run encoding/mojibake scan when Chinese text changed;
- verify the documentation references the correct output path;
- commit the source and rendered artifact together when both are generated.

## Manual Correction Gate

When a human-corrected artifact replaces an agent-generated diagram, do not only
swap the file. Compare the old and corrected render/source, identify reusable
style or workflow lessons, and update the relevant skill, reference, or project
state before treating the round as complete.

Use the user's feedback as a scoring loop. If the user says the corrected version is
clearer or gives a higher score, extract the concrete reasons: visual focus,
layout balance, endpoint labeling, font consistency, arrow proportion, color
semantics, and whether the user can act without reading the schematic.
