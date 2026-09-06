# Connector Semantics

Use this reference when a generated or reviewed diagram contains lines, arrows,
edge labels, buses, branches, transitions, signal links, or layer dependencies.

## Required Sequence

1. Identify the diagram family before drawing: flowchart, decision tree,
   state machine, signal/control chain, MCU block diagram, architecture layer
   map, timing diagram, or generic relationship map.
2. Declare the connector contract: line or arrow, single or bidirectional,
   touch boundary or controlled gap, straight or orthogonal, label side, and
   clearance.
3. Draw from declared ports and lanes, not from nearby visual coordinates.
4. Export and inspect the rendered image. Check semantics first, then geometry.
5. If the user flags a connector issue, update the helper or contract and add a
   regression note. Do not only move the final object.

## Diagram Family Rules

| Family | Connector default | Direction rule | Endpoint rule | Label rule |
|---|---|---|---|---|
| Flowchart / process | Arrow | Required; shows execution or workflow direction | Touch node boundary or visually terminate on boundary; no mixed gaps | Decision exits need `Yes`/`No` or short condition |
| State machine | Arrow | Required for every state-changing transition | Port-to-port; avoid crossing state boxes | Event/guard/action label near transition, never on stroke |
| Decision tree / classification tree | Plain branch line by default | Arrowheads optional only when process direction is the message | Branches connect node boundary to child boundary or a clean branch point | Branch meaning can be in node text or edge labels; keep symmetrical |
| Signal/control chain | Arrow | Required along sample/control/power ownership | Side-center ports; consistent touch or consistent small gap | Units, rate, latency, or threshold labels use whitespace lanes |
| MCU/electronics block | Arrow or paired arrows | ADC/sensor feedback points into MCU/controller; PWM/control output points outward; UART/Tx-Rx uses double arrow or two labeled opposite arrows | Use named side ports; avoid lines through modules | Signal name, voltage, rate, or direction label if ambiguity exists |
| Architecture layer map | Arrow only if dependency or call direction matters | If arrows encode dependency instead of signal direction, state that in the slide or legend | Gap arrows between layers are acceptable if all rows use the same convention | Keep labels out of layer boxes unless they are node-owned |
| Timing diagram | Marker lines/rules | Direction is usually time axis, not arrowheads | Marker x must reuse waveform edge x | Labels align to marker or lane with fixed clearance |

## Endpoint Contract

- A connector either touches the target boundary or uses a declared visual gap.
  Mixing one attached end and one floating end in the same diagram family is a
  defect unless the difference is semantic and documented.
- Flowcharts, state machines, and signal chains should normally terminate on
  the node boundary.
- Gap arrows are acceptable for layer maps and some compact card workflows, but
  every equivalent gap in the family should be the same visual size.
- Arrowheads must not press into text, sit inside a node interior, or stop just
  short of a target unless a gap is declared.
- For attached-endpoint diagram families, any visible connector endpoint gap
  above about 0.04 in should be treated as a review issue unless the component
  contract explicitly declares an intentional gap style.
- Use side-center ports by default. Custom ports need a reason such as a timing
  marker, feedback branch, bus tap, or physical connector position.

## Arrowhead Choice

- Use a straight line when the relationship is classification, grouping,
  containment, or undirected association.
- Use a single arrow when the relationship has one owner direction: execution
  flow, state transition, data flow, control output, sample input, or power
  delivery.
- Use a double arrow when the link is truly bidirectional at the abstraction
  level shown, such as UART Tx/Rx, command/response links, negotiation, or a
  two-way debug/control channel.
- Use two labeled one-way arrows instead of one double arrow when the two
  directions carry different names, rates, voltages, or safety meaning.
- Avoid decorative arrows. If the arrowhead does not change the reader's
  interpretation, use a line or remove the connector.

## Label Placement Contract

- Generate labels from the connector segment, not independent x/y guesses.
- Horizontal segment: center the label on the segment midpoint and offset above
  or below by the label clearance.
- Vertical segment: center the label on the segment midpoint and offset left or
  right by the same perpendicular clearance. Keep the side choice consistent
  for equivalent transitions.
- Diagonal segment: rotate the label with the segment when that improves
  ownership, then offset along the normal so the nearest text edge clears the
  stroke.
- For vertical writing, keep the read direction consistent; bottom-to-top is
  usually preferred for rotated side labels in compact engineering diagrams.
- Default PPT clearance at 16:9 slide scale: 0.06-0.10 in, with 0.08 in as the
  normal target. Measure from connector stroke to nearest text-box edge.
- Label clearance outside roughly 0.035-0.18 in should be checked visually:
  smaller gaps usually read as touching the connector, while larger gaps can
  break ownership unless the label is intentionally placed in a separate lane.

## Review Output

When connector semantics matter, include these fields in the review or handoff:

```text
Connector family:
Direction contract:
Endpoint contract:
Label clearance:
Bidirectional links:
Exceptions:
Visual evidence:
Residual risk:
```

## Regression Checks

Use these as small stability tests after skill or generator changes:

- Flowchart: at least one decision with two labeled branches; every branch has
  an arrowhead and touches the node boundary.
- Decision tree: branch lines do not use arrowheads unless the slide explicitly
  explains process direction.
- MCU I/O: ADC/sensor arrow points into MCU, PWM arrow points out, UART shows
  double arrow or paired Tx/Rx arrows.
- State machine: every transition has a visible arrowhead and a label placed
  with consistent clearance; diagonal labels follow the diagonal when used.
- Layer map: if gap arrows are used, each row uses the same gap convention and
  no arrowhead presses a frame.
