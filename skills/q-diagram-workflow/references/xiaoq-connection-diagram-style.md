# Connection Diagram Style

Use this reference for training or handson figures that show how an MCU,
controller board, driver board, power input, debug interface, and actuator are
connected. It captures reusable preferences learned from the user's manual
correction of a controller-to-driver PowerPoint figure.

## Training Figure Goal

For hands-on training, the diagram must be immediately operational. A learner
should be able to look at the figure once and understand:

- which two or three boards are central to the task;
- which physical connector or pin to use on each board;
- what each signal does;
- which direction the signal or power path goes;
- how the drawing maps back to the real hardware.

Do not hide exact connections in a table just because the layout is difficult.
Use the corrected high-score example as evidence that a clear pin-aware layout
is achievable for moderately complex board-to-board figures.

## Intent

Choose the figure type deliberately:

- Use `connection diagram` when the image shows exact signal names, connector
  IDs, and endpoint names.
- Use `connection overview` only when the image intentionally abstracts pin
  details into groups and the exact mapping lives in a table.
- Do not mix the two: if exact pins are visible, make the title and layout
  behave like a connection diagram.

## Layout

- Keep the two core boards large, symmetric, and horizontally aligned:
  controller on the left, driver or power stage on the right.
- When two boards are both core modules, keep their visual weight balanced.
  Equal or near-equal board widths often read better than narrowing one side to
  solve a local spacing issue.
- Make the main boards the strongest visual objects. In an MCU-to-driver lab,
  the controller board and driver board are the visual focus because almost all
  important connections happen between them.
- Put board titles and short role labels at the top of each board.
- Put matching endpoint labels near the board edge they belong to. The reader
  should be able to trace one signal from left pin, through one line, to right
  endpoint without reading surrounding prose.
- Place external connectors inside or attached to the lower edge of the board
  they belong to, then put the external device directly below that connector.
- For connector blocks that overlap a main board edge, align the shared edge
  precisely. A small connector block should feel fused with the main board, not
  visually separated by a double or offset border.
- Treat shared-edge alignment as a rendered-border problem, not only an
  `x/y/w/h` problem. PowerPoint strokes are drawn around the path, so attached
  connector line weight should match the main board line weight unless there is
  a deliberate reason not to.
- When changing connector stroke weight, check the whole related small-shape
  family. Attached connectors and bottom external device boxes should usually
  share stroke weight unless the diagram deliberately uses line weight to show
  hierarchy.
- Use vertical arrows for USB/debug, power input, and motor output. Use
  horizontal arrows for board-to-board control and sensing signals.
- Avoid explanatory subtitles in the figure when the diagram is already
  self-contained. Put instructions, checks, and long notes in the Markdown
  text or connection table.
- Preserve a clear focal structure: title first, main boards second, signal
  bundle third, external devices fourth. Avoid scattered labels, uneven object
  distribution, or decorative elements that compete with the main boards.
- Do not fix arrow or spacing issues by distorting the main-board composition.
  First try endpoint alignment, connector placement, label position, and shared
  edge alignment.
- For repeated board-to-board signal rows, define the full row grid before
  drawing individual objects. The repeated left endpoints, right endpoints,
  connector centerlines, and signal labels must be generated from the same row
  list rather than hand-nudged one at a time.
- Repeated signal rows should be vertically even: equal row center spacing,
  equal endpoint heights, and enough visible air between adjacent boxes. If one
  row is moved, recompute the whole stack instead of only moving that row.
- Left and right endpoint boxes should use symmetric board-edge gutters unless
  a hardware shape clearly requires an exception. A visibly wider gutter on one
  side reads as accidental, even when the line endpoints still connect.
- Put horizontal signal labels consistently above their connector lines with a
  stable visual gap. Do not alternate label positions unless the drawing has a
  deliberate lane system that explains the change.
- For PPT-native connection diagrams, verify arrowheads in the PPTX XML or
  shape model after saving. A rendered PNG can look acceptable while the
  editable source contains plain lines without `headEnd` or `tailEnd` arrow
  definitions.
- Arrow direction must be checked by signal ownership, not by visual habit or
  by arrowhead existence alone. For MCU-to-driver figures, command/PWM/enable
  normally point from MCU to driver, sensing/status returns from driver to MCU,
  external supply/debug points into the board, and motor output points from the
  driver to the motor.
- Debug/control links such as a host monitoring tool over UART are bidirectional. Draw them
  with visible double arrowheads, give the shaft enough length for both
  arrowheads to be readable, and place the `UART` label beside the line instead
  of between crowded arrowheads.

## Detail Level

- Show exact pin names and connector IDs when the diagram has about six to
  eight board-to-board signals and the labels can remain readable.
- Group details into a table when exact endpoints would require dense labels,
  crossed lines, diagonal routing, or small fonts.
- Use concise functional labels on signal lines, such as phase, enable, ADC
  channel, UART, power, or motor output.
- Prefer explicit endpoint names over aggregated labels. For example, a set of
  PWM signals should be drawn as separate parallel lines if space allows,
  rather than one combined bus label.
- Label every physical interface with both role and connector ID where known,
  for example `USB Type-C / J15`, `DC IN / P3`, or `BLDC OUT / P2`.
- The figure should let users connect hardware even without the schematic, but
  should still align with board silkscreen, connector naming, and signal
  function.

## Visual Semantics

- Color by signal family and keep the mapping consistent within the figure:
  PWM or digital control in blue, ADC/current feedback in yellow or orange,
  power input in red, motor output in neutral gray or a distinct non-control
  color, and USB/debug in cyan or blue.
- Keep lines straight and parallel. Avoid bends unless they remove an overlap.
- Arrowheads must touch the target object or endpoint line; no floating line
  ends.
- For PowerPoint board-edge arrows, if stroke-width overlap remains visible
  after coordinate alignment, add a final no-fill board-outline overlay above
  the wires. Keep text visually on top or use no-fill overlays so labels are
  not covered.
- Treat layer changes as both diagnostics and repairs. Toggle which shape is on
  top to reveal hidden radius, stroke, and edge mismatches, but do a full-figure
  review before accepting that layer order as final.
- Prefer the smallest overlay that fixes the actual defect. If only signal
  endpoints need masking, use short local edge masks instead of a full board
  outline that can disturb connector corners elsewhere.
- Text inside compact connector blocks must fit comfortably; use short labels
  plus connector IDs instead of long sentences.
- Match corner radius to the role and overlap behavior. Large main-board
  corners can be acceptable, but when connector blocks overlap the board edge,
  the radii should be compatible so the shapes merge cleanly.
- For PowerPoint rounded rectangles of different sizes, the same adjustment
  value does not mean the same visible corner radius. When a small connector is
  attached to a larger board, often reduce the large-board radius and increase
  the connector radius until the visible outlines meet cleanly.
- Validate attached connectors by the visible outside edge after rendering,
  especially right edges and bottom edges. A connector can have matching
  coordinates but still look slightly inset or protruding because of stroke
  width and corner curvature.
- Leave generous white space between the title, boards, signal bundle, and
  bottom external devices.
- Use consistent font family, weight, and size hierarchy. Board titles,
  connector labels, pin labels, and signal labels should each have a stable
  style; none should look accidentally too large or too small.
- For PPT-native connection diagrams, keep a role-based font contract:
  audit labels by visible role/content and peer family, not only by shape ID;
  main title uses the chosen CJK-capable title font; English-only board titles
  and pin/connector IDs use the agreed Latin technical font; Chinese role
  subtitles, legends, and Chinese/mixed device labels use the agreed CJK font.
  Once set, do not switch fonts per edit. A label with `font.name=None`, theme
  fallback, unexpected bold, or unexpected color fails review even when the
  text content and geometry are correct.
- Keep arrow stroke width and arrowhead size consistent and proportional to the
  diagram. Oversized arrows distract from the endpoints; undersized arrows make
  direction ambiguous.
- Use alignment and spacing as quality signals: related labels should sit on
  shared baselines, parallel wires should have equal spacing, and external
  device blocks should line up with the connector they attach to.

## Scoring Rubric

Before accepting a training connection diagram, score it against these criteria:

- `operational clarity`: can a learner complete the hardware connection from
  the figure without reading the schematic?
- `visual hierarchy`: are the main boards obviously the focus, with secondary
  devices visually subordinate?
- `mapping to hardware`: are connector IDs, pin names, and functional labels
  present and close to the relevant physical side of the board?
- `signal readability`: are color, direction, and grouping clear at first
  glance?
- `layout discipline`: are objects evenly distributed without crowding,
  overlap, random placement, or inconsistent arrow/font sizes?

A low score means revise the source, not remove useful detail. A high-score
human correction is a template to learn from and reuse.

## Correction Learning Loop

When the user provides a corrected version:

1. Preserve the corrected editable source as authoritative.
2. Export or inspect both the agent version and corrected version.
3. Compare visual structure and source metadata when possible: title wording,
   object count, connector count, shape positions, label granularity, colors,
   and external device treatment.
4. Treat the agent version as the low-score sample and the user's correction as
   the high-score exemplar. Identify why the high-score version is easier for a
   human to use.
5. Summarize reusable deltas in the project state and update this reference or
   the relevant workflow before closing the task.
