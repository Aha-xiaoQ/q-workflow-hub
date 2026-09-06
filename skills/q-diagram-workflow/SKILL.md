---
name: q-diagram-workflow
description: Use when creating, repairing, or reviewing technical diagrams for q-workflow projects, especially wiring diagrams, block diagrams, training figures, architecture diagrams, and generated SVG/PNG/PPT visuals that must avoid overlaps and remain editable or reproducible.
---

# Q Diagram Workflow

Use this skill when a task needs a technical diagram, wiring figure, generated
visual, or visual repair. Pair it with project-local workflow skills when the
diagram belongs to a project.

Before redrawing a diagram, check available reference diagrams or source files
from the same domain when the user provides them. Reuse their layout logic:
two or three core modules, straight edge-to-edge links, concise labels, and
external devices placed next to the module they connect to.

If the user provides a manually corrected PPTX or annotated figure, treat that
as the target design source. Adopt it as the authoritative editable source,
export the release image from it, compare it with the agent-generated version,
record reusable design deltas, and avoid reimplementing the drawing from
scratch unless asked. If the deltas are reusable, update this skill or its
references before closing the task.

When the task is explicitly a training loop with a 100-point exemplar, also read
`references/exemplar-scoring-loop.md`. Preserve intermediate versions so the
user can calibrate both the artifact quality and the agent's scoring judgment.

## Default Rule

Do not make dense hand-positioned SVGs as the first choice. For training and
engineering docs, the goal is not a vague safe overview; the goal is a clear
teaching figure that a learner can use to understand the hardware situation at
a glance and complete the connection without opening the schematic when the
available information is sufficient.

Prefer:

1. A concrete, readable connection diagram with the main boards visually
   dominant and each relevant interface labeled by function and connector ID.
2. A structured connection table for overflow pins, voltages, directions, and
   safety notes that would make the image crowded.
3. A source artifact that can be edited or regenerated.

Use an abstract overview only after trying to organize the concrete connection
diagram and determining that exact endpoints would make the figure unreadable.
Do not reduce detail merely because the agent is weaker at complex layout; use
user corrections and reviewed examples to improve the layout process.

Manual SVG is acceptable only for simple overview figures with few labels and
clear spacing. If a diagram has many endpoints, wire crossings, labels on
edges, or must be edited by humans, choose a better source format first.

## Visual Grammar Gate

For customer-facing figures, training figures, architecture maps, or any
diagram that may be reused in slides, define the visual grammar before drawing:
audience, target medium, central message, source context, dominant object,
flow direction, label density, color semantics, and what must stay editable.

When the visual direction is uncertain, do not jump straight to one generic
diagram. Create or sketch two to three concrete scene directions, such as
pin-aware connection figure, high-level architecture map, timeline/workflow
story, comparison matrix, or dashboard-style state map. Pick the scene that
best helps the user act, then build that version.

For reusable/generated PPT diagrams or ordinary PPT layouts, use grid-first
layout planning as the default once the surface has alignment risk or reusable
value. Read `references/grid-first-layout-planning.md` and define the safe
area, layout boundary, zones, component slots, ports/lanes, text insets, and
label-clearance constants before rendering. Do not rely on free per-shape
coordinates as the reusable source of truth.

When the diagram contains lines, arrows, buses, branches, transition labels, or
signal direction, also read `references/connector-semantics.md`. Decide the
diagram family's connector contract before drawing: whether endpoints touch or
leave a controlled gap, whether direction must be encoded, whether a link is
one-way or bidirectional, and where labels sit relative to each segment.

For longer training material or high-risk diagrams, make one representative
figure first and validate visual hierarchy, label strategy, line routing, and
editability before producing the rest. Reuse real boards, product screenshots,
connector IDs, known colors, or existing project diagrams when available;
otherwise mark missing assets explicitly instead of hiding the gap with
decorative placeholders.

## Tool Selection

- **Wiring, connectors, harnesses, pinouts:** read
  `references/tool-selection.md`; prefer WireViz when available, or an overview
  diagram plus pin table when WireViz is not installed.
- **Editable training/customer figures:** prefer draw.io/diagrams.net source
  files (`.drawio`) plus exported PNG/SVG/PDF.
- **Training figures that will be placed in Markdown or slides:** prefer a
  PowerPoint or draw.io source plus a reviewed PNG export. Avoid using raw SVG
  as the only source when text layout depends on renderer/font behavior.
- **Controller-to-driver training connection diagrams:** read
  `references/xiaoq-connection-diagram-style.md` before drawing. Prefer a
  pin-aware connection figure when the relevant signals fit cleanly, and move
  excess detail to the connection table.
- **Architecture, flow, dependency, state diagrams:** prefer D2, Graphviz,
  Mermaid, or Kroki-backed text sources.
- **PowerPoint deliverables:** pair with a presentation workflow and visual
  review skill; use PPT shapes or imported reviewed images.

## Workflow

Read `workflows/create-technical-diagram.md` before creating or repairing a
diagram. For visual validation, read `workflows/render-validate.md`.

## Quality Bar

- Labels do not overlap nodes, lines, arrows, legends, or each other.
- Edge labels are used sparingly; long details belong in tables or callouts.
- Direction and ownership are explicit, for example `MCU -> driver`.
- Power sources, voltages, and safety constraints are precise.
- The diagram has a durable source file and, when practical, a rendered image.
- Markdown documents should reference the reviewed PNG/PDF image, while the
  editable source sits beside it.
- Do not put production notes such as "design principle", validation comments,
  or instructions to the agent inside a released training/customer figure.
- Lines must visibly terminate on the object they connect to. Avoid floating
  bus lines, unnecessary bend segments, and arrowheads that sit away from the
  target module.
- Directional diagrams must visibly encode direction. Flowcharts, state
  transitions, data/control chains, and return lanes need arrowheads or another
  explicit direction marker in the final rendered image.
- Do not let relationship lines cross through node/card interiors. Use declared
  ports, reserved lanes, segmented routes, or short gap arrows between stacked
  layers.
- For MCU and electronics block diagrams, encode signal ownership explicitly:
  sensor/ADC feedback points into the controller or MCU, PWM/control outputs
  point outward toward the driver or power stage, and true Tx/Rx links such as
  UART are shown with a double arrow or paired labeled one-way arrows.
- Manual corrections are learning data. When a user edits a diagram, compare
  source and rendered outputs, summarize what changed in abstraction level,
  labels, line routing, color semantics, external devices, and validation
  needs, then store the lesson in the right durable layer.
- If visual rendering could not be verified, say so and do not claim visual QA.
