# HTML Diagram Rules

Use this reference before drawing diagrams in HTML, CSS, SVG, Canvas, or
Mermaid.

## Choose The Renderer

| Diagram Need | Prefer |
|---|---|
| Simple process, architecture, data flow | CSS grid boxes plus SVG arrows |
| Precise arrows, lanes, grouping, callouts | Inline SVG |
| Documentation-native flowchart/sequence/class diagrams | Mermaid |
| Dense interactive visualization | Canvas or a proven chart/graph library |

Avoid hand-positioning many independent absolute elements without a layout
model. That is the common path to overlaps and broken mobile views.

## Build From A Diagram Spec

Before rendering, define:

- nodes: id, label, group/lane, type, importance;
- edges: from, to, label, direction, emphasis;
- groups: title, purpose, node ids;
- layout: row/column, lane, timeline, radial, matrix, or swimlane;
- legend: colors, shapes, line meanings.

For reusable diagrams, keep this spec separate from rendering code.

## Layout Rules

- Use rows, columns, lanes, or matrices before custom coordinates.
- For diagram-heavy pages, define the diagram boundary and minimum grid unit
  first. Place nodes into grid cells and route arrows through connector lanes;
  do not center the rendered nodes manually after drawing.
- Align node titles on a shared baseline.
- Reserve fixed label slots inside nodes; do not let text touch borders.
- Route arrows between component centers or edge anchors, not arbitrary points.
- Leave enough gap for arrowheads and edge labels.
- Keep connector lines behind nodes and labels above lines.
- Use `viewBox` for SVG and preserve aspect ratio.
- Provide a legend when color, line style, or shape carries meaning.

## SVG Rules

- Use `<defs><marker>` for arrowheads instead of text arrows.
- Use groups (`<g>`) for each node with a rect and text elements.
- Keep text in HTML overlays if wrapping is important, or use short SVG labels
  plus a supporting table.
- Set `pointer-events` intentionally when overlays or tooltips exist.
- Avoid tiny labels; if a label needs to be small, put the detail below the
  diagram as a table.

## Mermaid Rules

- Use Mermaid when editability and documentation-native source matter more than
  exact pixel control.
- Include an offline fallback note if the page imports Mermaid from a CDN.
- Keep node labels short. Long Chinese/English labels should move to adjacent
  explanatory text.
- Theme Mermaid to match page tokens when possible.

## Validation

Inspect diagrams at desktop and mobile widths:

- no blank canvas or failed Mermaid block;
- no overlapping node labels;
- no arrows crossing important text;
- no cropped legend or labels;
- arrow direction is obvious without reading every label;
- diagram remains useful when printed or exported as a screenshot.

If the diagram fails visual inspection, simplify the diagram before adding more
styling.
