# Grid-First Layout Planning

Use this reference when a diagram, PPT component, HTML page, dashboard, or
report surface has visible alignment/centering risk and should be planned
before rendering.

## Default Standard

For reusable/generated PPT work, grid-first is the default authoring model, not
a cleanup trick. This includes ordinary slide pages, component-library samples,
simple PPT-native block diagrams, flowcharts, state machines, timing diagrams,
and imported-image layouts. A future agent should be able to recover the layout
from a written or encoded contract instead of guessing from final coordinates.

Rule record:

- **When:** generating or repairing a reusable PPT/page/diagram layout, or
  after the user flags alignment, cramped text, connector, or readability misses.
- **Goal:** make placement repeatable, visually stable, and easy to edit.
- **Strength:** should for normal generated layouts; must after two or more
  visual repair rounds, component-library work, or any user-flagged obvious
  layout miss.
- **Layer:** task workflow plus this on-demand reference.
- **Do:** declare the layout boundary, grid/zones, component slots, text slots,
  ports, connector lanes, label-clearance constants, and parent-child
  relationship constraints before rendering.
- **Avoid:** independent per-shape coordinates, copied offsets, and late
  visual nudges that are not tied to a named contract field.
- **Validation:** exported PNG plus source/audit check must show that visible
  alignment follows the declared contract.

## Why This Exists

the user's 2026-06-19 PV application experiment showed that a loose "invisible
grid" is not enough. The successful part was not snapping manually placed boxes
to nearby coordinates; it was treating the whole figure as a planned layout
system:

1. infer the intended outer boundary;
2. choose the smallest useful grid unit;
3. reserve node cells and connector lanes;
4. define side-center ports;
5. render from the grid boundary inward;
6. validate the exported image against the declared grid.

This matches patterns from graph layout engines, diagram editors, and UI grid
systems: layout has a model before it has pixels.

The follow-up 2026-06-20 PPT component-library loop exposed the same issue in
ordinary slide layouts: text rows, framed labels, timing markers, state-machine
labels, and page-level previews failed when their coordinates were chosen by
local feel. The durable fix is one shared layout contract that covers both
diagrams and page composition.

## Source Patterns Learned

Learn patterns only; do not copy third-party code, examples, screenshots,
templates, or proprietary text.

- ELK layered layout exposes layout options for ports, port constraints,
  spacing, edge routing, node sizing, and layered graph structure. The useful
  idea is that port placement and edge routing are layout inputs, not visual
  afterthoughts.
- Graphviz DOT supports directed graph layout, node/edge attributes, rank
  direction, node/edge spacing, and port positions such as compass points. The
  useful idea is to encode attachment intent in the source.
- draw.io / diagrams.net provides snap-to-grid, snap-to-connection-point,
  custom connection points, connectors, and waypoints. The useful idea is that
  manual diagram editing still benefits from explicit anchors and bend points.
- CSS Grid defines a two-dimensional layout model with rows, columns, tracks,
  named regions, and item placement. The useful idea for pages and dashboards
  is to define structure before placing content.
- Figma layout guides / grid systems are used to preserve consistency across
  frames and screen sizes. The useful idea is to separate the frame boundary,
  columns/rows/gutters, and content alignment decisions.
- Existing local component-library notes already promoted semantic diagram
  specs, ports, orthogonal routing, obstacles, route scoring, and fixture-based
  validation. The grid-first rule makes this usable for PPT-native simple block
  helpers and general page layout.

Use these as idea sources only. Do not copy third-party documentation text,
example diagrams, screenshots, templates, source code, or proprietary assets
into q-workflow skills or project outputs.

## Vocabulary

- **Canvas:** the full slide, page, SVG, or HTML viewport.
- **Safe area:** the rectangle where ordinary required content may appear.
- **Layout boundary:** the outer rectangle of the figure, page body, or
  repeated component set. Center this first.
- **Grid:** rows, columns, gutters, and optional named regions inside the
  boundary.
- **Zone:** a named area such as header, body, diagram, table, legend, footer,
  side rail, or bottom callout.
- **Cell:** an addressable grid rectangle.
- **Slot:** a content rectangle derived from a cell or component bounds, for
  example a title slot, body slot, icon slot, image slot, or label slot.
- **Component:** a helper-owned object such as a card, row, node, badge,
  callout, waveform lane, or connector group.
- **Port:** a declared attachment point on a node or component, usually the
  side center.
- **Lane:** a declared path row/column or segment used by connectors, buses,
  feedback lines, timing markers, or whitespace-separated labels.
- **Clearance:** the visual gap between text/labels/connectors/frame edges,
  measured from visible strokes or text-box edges.
- **Relationship constraint:** an explicit check between related objects, such
  as equal internal symbol gutters, one centerline shared by upstream and
  downstream connector segments, or a child bar staying inside its parent
  media/chart slot with declared inset.

If a layout cannot be described with these nouns, it is probably being placed
by feel rather than by a reusable layout model.

## When To Use

Use grid-first planning when any of these are true:

- the user flags centering, spacing, or alignment problems;
- a block diagram needs repeated boxes and straight/orthogonal connectors;
- a page has repeated cards, panels, KPIs, tables, or a diagram canvas;
- a generated layout has already needed two or more visual repair rounds;
- the output should become a reusable component/helper rather than a one-off
  manually nudged slide.
- the slide contains imported diagram/image renders whose labels must be
  readable at slide size;
- connector labels, edge markers, timing markers, or framed text have already
  produced near misses.

Do not force this method onto tiny one-off sketches with two or three objects.
For dense/branchy diagrams, use this method as a planning layer or route to a
layout tool such as draw.io, D2, Graphviz, or ELK-style layout before PPT
restyling.

## Contract Levels

Choose the lightest contract that prevents the known failure mode.

| Level | Use For | Required Contract |
|---|---|---|
| L0 quick sketch | two or three throwaway shapes | safe area and rough flow direction |
| L1 ordinary PPT page | title/body layouts, cards, tables, screenshots, summaries | safe area, zones, columns/rows, component slots, typography sizes, insets |
| L2 simple editable diagram | block, flow, state, timing, control-loop diagrams | all L1 fields plus node cells, ports, connector lanes, label slots, line/label clearance |
| L3 routed or dense diagram | electronics blocks, many branches, feedback loops, wire-heavy figures | semantic graph/source format, obstacles, route scoring or external layout tool, plus import/restyle contract |

Component-library examples and generated decks that the user will reuse should
start at L1 or L2. If the diagram cannot meet L2 without awkward manual bends,
promote it to L3 instead of forcing PPT-native drawing.

## Planning Contract

Before rendering, write down or encode:

```text
canvas:
  width, height
  content_safe_area

grid:
  outer_boundary: x, y, w, h
  rows, columns
  min_unit: cell_w, cell_h
  gutters: optional

zones:
  title/header/footer
  main diagram/page area
  side rail / legend / table / callout

nodes:
  id, label, type
  cell_rect: col, row, col_span, row_span
  allowed_size_class
  text_slot: inset, max_lines, font_size
  ports: left, right, top, bottom side-center by default

groups:
  id, label, cell_rect
  visual_boundary: dashed/solid/background

edges:
  source, source_port
  target, target_port
  route_kind: straight, orthogonal, bus, feedback
  lane: row/column or explicit waypoints
  semantic_kind: power, signal, control, data, fault

validation:
  boundary_centered_in_safe_area
  node_cells_inside_boundary
  ports_on_node_sides
  routes_do_not_cross_node_interiors
  labels_readable_at_export_size
  related_lines_share_centerlines
  internal_symbols_have_symmetric_gutters
```

For ordinary PPT pages, use the same shape with page-oriented fields:

```text
canvas:
  slide_size: 16:9 or template-defined
  safe_area: x, y, w, h

page_grid:
  boundary: x, y, w, h
  columns: 12 or 24
  rows: 6, 8, 12, or task-specific
  gutters: horizontal, vertical

zones:
  header: row range and text baseline
  body: row/column range
  figure_or_table: cell range
  side_note_or_legend: cell range
  bottom_callout: optional cell range

components:
  id, kind, grid_area, size_class
  internal_grid: rows/columns or centerline
  text_slots: inset, max_lines, min_font_pt, anchor
  media_slots: crop_mode, readable_label_requirement

validation:
  required_text_min_font_pt
  no_text_border_contact
  repeated_components_share_helpers
  child_elements_respect_parent_insets
  icon_or_bullet_label_pairs_share_centerline
  exported_png_reviewed
```

For PPT component-library outputs, the contract is part of the source. A final
PPTX without the source/generator fields is not enough evidence that the route
is reusable.

## Numeric Defaults For 16:9 PPT

Use these values as starting points, then adjust by template and slide purpose:

- Slide canvas: `13.333 x 7.5 in` unless the template says otherwise.
- Ordinary content safe margin: `0.35-0.55 in`; use the larger end for dense
  decks, meeting-room readability, or template footer/header art.
- Component-library required text: minimum `9 pt`; if it needs smaller text,
  split the sample across slides or move details to notes/source.
- Body text in normal content: prefer `12-18 pt`; use `9-11 pt` only for
  compact labels, tables, legends, or secondary metadata.
- Framed text inset: small labels `0.08-0.12 in`; diagram nodes
  `0.12-0.18 in`; cards/callouts `0.18-0.28 in`.
- Connector-label clearance from stroke to nearest text-box edge:
  `0.06-0.10 in`, default `0.08 in`, for horizontal, vertical, and diagonal
  labels.
- Connector stroke: keep equivalent semantic lines visually consistent; do not
  mix thin local callout strokes with heavy signal strokes unless the semantics
  require it.
- Corner radius: use one declared size per component family. Do not let
  rounded boxes become cramped pills around long text.

These are visual-contract defaults, not magic constants. If the exported PNG
looks tight, fix the component size, label length, scale, or topology before
loosening the standard one object at a time.

## How To Infer The Grid

From a reference image or target figure:

1. **Find the real figure boundary.** Exclude title/footer chrome, but include
   labels that belong to the figure. If the boundary is unclear, define a
   conservative safe boundary with visible margin.
2. **Identify repeated sizes.** Use repeated module width/height, row
   centerlines, group boundaries, and arrow lanes to estimate the base unit.
3. **Choose a practical unit.** The unit should divide the figure into enough
   cells to express box sizes and connector lanes without micromanaging every
   pixel. For PPT, 24-48 columns and 12-24 rows is often enough for one
   diagram region.
4. **Separate node cells from line lanes.** Boxes own cell rectangles. Lines
   use row/column lanes and may be offset from node rows so arrowheads and
   branch points do not touch boxes.
5. **Place from the boundary inward.** Do not draw several objects and then
   try to center them. Center the grid boundary first, then derive all objects.
6. **Use side-center ports by default.** If a route cannot connect cleanly from
   side-center ports, this is a signal that the grid or diagram family needs
   redesign.
7. **Treat text as part of the grid.** A readable label owns a slot and
   clearance. Do not place text after the shapes as decoration.
8. **Validate local subgrids.** A symbol, icon, chart, table, or note row
   inside a grid cell needs its own internal relationship checks. Do not stop
   at "the child is on a grid"; verify left/right and top/bottom gutters,
   child-to-parent inset, and sibling row centerlines.
9. **Make deltas explicit.** If a reference image has a non-grid feature,
   record it as an intentional exception such as `diagonal_feedback_route` or
   `legend_overhang`, not as a hidden coordinate tweak.

## Page Layout Rules

Use these for ordinary PPT slides, reports, and dashboards:

- Establish header, body, footer, and optional side/bottom zones before adding
  content.
- Choose a simple grid: 12 columns for page composition, 24 columns when
  diagrams or compact cards need more precision. Use 6-12 rows for ordinary
  slide bodies and 12-24 rows inside diagram regions.
- Assign every repeated card, row, figure, table, or callout to a named grid
  area and size class.
- Use local internal grids for components. A card's badge, title, body, icon,
  and accent strip should be positioned by that card helper, not by the slide.
- Treat bars, bullets, icons, badges, labels, and chart rows as child
  components with parent-owned bounds. A bar track is sized from the chart
  slot width and insets; it is not a fixed global width. A bullet/dot and its
  text share one row centerline; they are not separate nearby objects.
- Center the parent boundary or zone. Do not center individual children after
  they have already drifted.
- Reserve image slots by aspect ratio. If embedded labels must be read, the
  slot must be large enough at exported-slide size; otherwise crop, split, or
  redraw as a simpler diagram.
- Put long text into planned multi-line slots with explicit wrapping. A
  hard-gate row, verdict row, or summary sentence must share a row/baseline
  with its label and wrap inside the safe width.

## Diagram Layout Rules

Use these for PPT-native or imported editable diagrams:

- Define node cells first. Node bounds, text slots, and ports derive from the
  cell and size class.
- Use side-center ports by default. Only use custom ports when the source
  explicitly declares why, for example a top timing marker or a bottom feedback
  branch.
- Separate node rows from connector lanes. Branches and buses should use named
  lanes, not arbitrary bend points.
- Prefer straight or single-purpose orthogonal routes. Tiny accidental doglegs
  are source defects.
- Use diagonal transitions when they are the clearest route between two states
  and no obstacle needs an elbow. The diagonal label follows the line angle,
  stays near the midpoint, and is offset by the declared label clearance so the
  text never covers the stroke.
- Flowcharts use standard symbol semantics: terminal, process, decision, and
  directed arrows. Decision branches require labels.
- State machines use initial node when entry matters, named states, directed
  transitions, and transition labels in the form `event [guard] / action` when
  applicable.
- Timing marker vertical lines share the exact x-coordinate of the waveform
  transition edge they annotate.

## Connector And Label Placement

Generate connector labels from the line segment, not from independent x/y
values.

- Horizontal label: center the text box on the segment midpoint, place it just
  above or below the line by the clearance target, and keep the whole text box
  inside the segment's whitespace lane when possible.
- Vertical label: center on the segment midpoint, place it left or right of
  the line by the clearance target, and keep the label close enough that the
  ownership is obvious.
- Diagonal label: compute the segment angle, normalize it for readable text,
  place the box at the segment midpoint, rotate it with the line, then offset
  it along the line normal by the clearance target.
- Multi-segment route label: attach the label to the semantic segment it
  names, usually the longest clean segment or the segment nearest the source
  decision/state.
- If a label touches a line or crosses a node, fix in this order: enlarge the
  layout boundary, shorten the label, increase the node spacing, reroute to a
  cleaner lane, reduce font only down to the minimum readable size, then use a
  callout or split the diagram.

The intended visual gap is measured from the connector stroke to the nearest
text-box edge. Center-to-center distances are not a reliable clearance metric.

## Rendering Rules

- Rendering code should consume the grid spec. It should not contain unrelated
  manual offsets such as `x + 0.17` for one box and `x + 0.23` for a peer box.
- Allowed box sizes should be named, for example `module`, `wide_module`,
  `tall_controller`, `small_output`.
- Text boxes should be derived from the node rectangle and an inset, not from
  independent coordinates.
- Arrows should be drawn from declared ports and lanes. For branch/bus
  connections, define the bus lane once and connect branches to it.
- If a connector segment reads as a continuation of another segment, all
  related source node ports, intermediate bus points, and target row ports must
  share the same centerline. A symmetric branch fan-out can still fail if the
  upstream source-to-hub line is half a row above or below the branch center.
- Labels on groups, axes, or regions should occupy reserved grid rows/columns
  so they do not touch boundary strokes.
- If a symbol or icon does not fit the grid, place it inside a declared symbol
  cell and align its center to that cell. For repeated internal marks, validate
  the internal gutters, for example a PV panel icon with equal left and right
  margins around black cell columns.
- Repeated PPT components should be emitted by one helper and, where practical,
  as actual PowerPoint groups after the helper lays out the internal grid.
- Any residual adjustment must be a named field such as
  `label_clearance_in`, `node_text_inset_in`, `feedback_lane_y`, or
  `reference_legend_offset`, not an unexplained one-off nudge.

## Validation Gates

Reject or mark as targeted fixes when:

- the grid outer boundary is not centered in the content safe area;
- any box or group touches the boundary without being intentionally edge-flush;
- a connector leaves a box from an arbitrary point instead of a declared port;
- a connector lane crosses through a node interior;
- branch connectors use ad hoc bend points instead of a declared bus/lane;
- repeated boxes use different sizes without a named size class;
- text slots are not derived from node rectangles and safe insets;
- the rendered PNG looks less centered than the declared boundary suggests.
- required text is below the minimum readable size or visually too small in the
  exported PNG;
- text inside frames appears tight even if the geometry barely avoids overlap;
- a marker, connector, arrowhead, or label is near the intended anchor but not
  actually generated from the same coordinate;
- a local subgrid symbol is visually off-center because its left/right or
  top/bottom gutters differ without an explicit reason;
- connector segments that read as one route do not share one centerline across
  the upstream node, hub/bus, and downstream target;
- bars, bullets, note dots, chart rows, or other child elements touch or escape
  the parent frame instead of using a declared inset;
- dot/label, badge/text, chart-label/bar, or icon/label pairs are emitted as
  separate objects without a shared row centerline helper;
- the source uses repeated manual offsets for repeated components instead of a
  helper or layout contract;
- the validation report cannot point to the source file, helper, or encoded
  contract that owns the layout.

For PPT-native output, visual review must inspect the exported PNG. Geometry
checks are useful but not sufficient.

## General Page Layout Use

The same idea applies outside diagrams:

- Define the page safe area and content width first.
- Choose rows, columns, gutters, and zones before cards or panels.
- Assign components to grid areas and size classes.
- Let inner components use their own local grids.
- Center the parent grid or content boundary, not individual cards.
- Use CSS Grid / flexbox, PPT helper grids, or HTML layout primitives as the
  renderer. The planning model stays the same.

When the user asks whether a diagram-layout lesson applies to ordinary layout,
answer that question directly with a page/report/dashboard layout contract or
sample. Do not stop at another diagram helper. The validation surface should
show named page zones, component size classes, text/image slots, and responsive
or slide-safe constraints.

## Minimal Experiment Loop

1. Pick one representative sample, not the full deck.
2. Write the grid contract or encode it in a small class/spec.
3. Render the sample.
4. Export PNG.
5. Compare visible result with the declared boundary, node cells, and lanes.
6. Update the contract, not only the final shapes.
7. Record the lesson in this reference or the project quality gate.
