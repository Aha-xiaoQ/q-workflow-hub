# Layout Stability Gate

Use this gate when generated slides have already missed obvious alignment,
centering, or template-consistency issues, or when the deck uses a custom
generated visual system rather than a proven template.

## Purpose

The normal visual review asks whether the exported deck looks acceptable. This
gate asks a stricter question: will the next generated deck keep the same
layout quality without the user pointing out each misalignment?

Borrow the mechanism from high-quality slide skills and UI/design-system visual
testing: stable authoring source, reusable layout helpers, preflight/dry-run
checks, rendered evidence, region-level comparison, and explicit review before
updating baselines. Learn the pattern only; do not copy third-party code,
prompts, schemas, text, or assets.

## Escalation Trigger

Use this gate as a hard escalation, not an optional checklist, when:

- the user finds obvious placement, alignment, or harmony issues after a
  previous `Pass` or high visual score;
- the same deck has gone through two or more visual repair rounds;
- the generator uses copied coordinates rather than named layout helpers;
- PNGs show the deck is individually patched instead of governed by one grid.
- the user flags a defect class that the latest visual report already warned
  about, such as overlap, text overflow, tiny evidence images, or label
  mis-centering. In that case the report was evidence but the verdict failed;
  rerun the review with those warning classes treated as blockers until each
  item is triaged.

When this trigger fires, the old verdict is superseded. The next report must
say what failed in the review workflow and cannot return `Pass` until the
layout contract, rendered sample, and audit evidence are all present.

## Required Contract

Before marking a generated deck visually checked, record the layout contract in
the report or project validation notes:

- Header contract: top accent rule, section label, title, subtitle, footer/page
  number positions, and whether they intentionally differ by slide type.
- Component contract: fixed helpers for repeated rows, badges, cards, callouts,
  process steps, and connector groups; avoid repeated manual y-offsets.
  Repeated components must declare their own internal grid: row height,
  centerline, badge diameter, text-frame bounds, title/detail slots, and anchor
  strategy. The generator should pass those values into one helper instead of
  assigning independent coordinates to the badge, number, title, and body.
  Patterns like manually nudging text inside a circle or using separate
  `y + 0.10`, `y + 0.14`, `y + 0.28` offsets for one row are instability
  signals, even when the first rendered deck looks close.
  When the final artifact is editable PPTX and the library supports grouping,
  repeated multi-shape components should be emitted as actual PowerPoint
  groups after their helper-owned internal grid is laid out. The group is the
  editable boundary; the helper remains the source of alignment truth. Review
  tooling must recurse into group children so grouping cannot hide text,
  badge, or overflow defects.
  Framed text components must declare a safe inset from every frame edge before
  text is rendered. The helper should calculate the content rectangle from the
  frame bounds, then place or shape-own the text inside that rectangle; it
  should not place a separate text box by manual offsets that can touch or
  escape the frame. The inset is a visual contract, not only a numeric
  collision threshold: if text still appears close to the frame in the PNG,
  enlarge the frame, shorten the copy, or increase the component inset before
  handoff.
  Short accent-rule + label patterns must be a helper-owned component or actual
  group. The rule and adjacent label/callout text should share one vertical
  center line and middle-anchor strategy; copied offsets that make labels sit
  slightly high or low are instability signals.
  Note rows, bullet rows, icon-label rows, and side-panel explanation lists
  follow the same rule: marker, label, and optional detail text are one
  row-center component, not separate nearby objects.
  For large cards and summary tiles, the contract must state whether numbers
  are primary structure or secondary metadata. Primary numbers must not be tiny
  off-center chips inside large frames.
  For colored strips or accent bars, the contract must state their semantic
  role; decorative strips are not enough to pass a layout-quality gate.
  For contrast surfaces, the contract must state whether a light or dark panel
  belongs to the selected style grammar. A large foreign-color panel used only
  to rescue readability is not a stable component. Required text should meet
  about 4.5:1 contrast against its containing surface, or about 3:1 for
  large/bold display text.
  For process flows, the contract must state the node/card bounds and connector
  endpoints. A single large process band with short connector lines floating
  between text clusters is not a stable connector group; each step should be a
  helper-owned card or node, with connectors attached to adjacent component
  boundaries or declared center lines.
- Grid contract: left/right content margins, column centers, row centers, and
  vertical zones for title, body, and bottom callout.
  Title/subtitle zones and body diagram zones must be separated explicitly.
  A diagram or side panel that is clear by itself still fails if it visually
  presses into the title stack, footer, or another page region.
  For diagram or page-layout components, also require a grid-first planning
  contract: whole-layout boundary, minimum grid unit, row/column count, node or
  panel cells, connector or spacing lanes, and the rule for centering the grid
  boundary inside the safe area. A layout that only snaps individual objects
  after free placement is not stable enough for component promotion.
  The same contract applies to ordinary PPT pages, not only diagrams: title
  stacks, body regions, card grids, screenshot/table slots, bottom callouts,
  summary rows, and route-comparison pages should be assigned to named zones
  and component slots before rendering. Reusable generated pages should center
  the parent boundary or zone, then derive children from it.
  For connector-heavy diagrams, the contract must also declare side-center or
  custom ports, connector lanes, timing marker coordinates, and connector-label
  clearance. Horizontal, vertical, and diagonal transition labels should be
  generated from their segment midpoint plus a clearance offset, not by
  independent text-box coordinates.
  For grid-first diagrams, the contract must also include relationship checks
  between related grids and components: local symbol gutters, parent/child
  insets, sibling symmetry, and route centerline continuity. A diagram can
  snap every object to cells and still fail if an internal PV icon has one
  extra cell of air on the right, or if the upstream source-to-hub line is half
  a row above the branch fan-out it visually feeds.
- Baseline contract: which exported PNGs are the current approved references,
  and which regions must be reviewed if the deck changes.
- Authoring contract: the durable source that rebuilds the deck or sample
  (`.py`, `.js`, `.json`, `.md`, template clone, or layout IR), and where helper
  functions own component positions. If the only source of truth is a final
  `.pptx`, the layout is not stable enough for generated-deck reuse.
  For component-library route previews, authoring source must include a
  human-editable diagram/page source when the displayed slide contains a PNG.
  Bitmap-only routes are not stable reusable components.

If no contract exists, the verdict cannot be `Pass`; at best it is `Targeted
fixes`.

## Sample-First Recovery

After repeated alignment misses, do not keep regenerating the full deck. First
build or repair a small representative sample:

- one title or section slide;
- one dense content/card grid slide;
- one process, flow, or connector slide;
- one summary, command, or bottom-callout slide.

The sample should be rendered to PNG and reviewed before the full deck is
regenerated. An HTML/CSS or other preview renderer is acceptable as an
intermediate visual sandbox when it makes grid/flex alignment easier to debug,
but the final handoff can still be an editable PPTX. Record which sample slides
represent which full-deck component risks.

## Automated Checks

The reviewer script should be run after generation. Treat these findings as
release blockers for generated decks unless the report explains why they are
intentional:

- deck-level title position drift across ordinary content slides;
- top accent rule or section label detached from the main title grid;
- repeated header/footer elements shifting across slides;
- badges, labels, or command rows not sharing a center line with adjacent text;
- numeric text not centered in its circle badge, or circle-badge text drawn as
  a separate nudged textbox instead of a helper-owned text frame;
- generated rows whose title/detail slots lack middle anchors or shared row
  height, even if geometric centers are only slightly off;
- large light/dark panels that break the selected style grammar while trying to
  improve readability;
- required text with low contrast against its containing surface, photo, or
  panel;
- text boxes inside a frame closer than the declared safe inset, or extending
  outside the frame;
- short accent-rule + label/callout pairs that do not share a center line or
  are not middle anchored;
- screenshots, UI captures, charts, or paper figures that are too small for
  their embedded labels to be read in the exported PNG;
- generated preview text below 9 pt, especially in component libraries,
  source notes, badges, route cards, and rule summaries;
- local subgrid symbols whose intended symmetric gutters differ left/right or
  top/bottom without an explicit exception;
- connector routes whose visually continuous upstream, hub, bus, and target
  segments do not share one declared centerline;
- chart bars, media-slot bars, screenshots, or figure placeholders that touch
  or escape their parent frame instead of using parent-owned insets;
- dot/label, badge/text, and icon/text pairs that do not share one row-center
  helper or actual grouped component;
- reusable pages or diagrams whose source lacks the declared layout contract
  needed to rebuild the same alignment;
- hard-gate, verdict, or rule-summary rows where the label and explanatory
  sentence do not share a deliberate row alignment or the sentence lacks
  intentional line breaks inside the slide safe area;
- multi-thumbnail pages used as validation evidence for labeled diagrams; use
  one component per slide or a large crop instead;
  An overview/index slide may show multiple thumbnails only when no internal
  label needs to be read and the slide is explicitly not counted as validation
  evidence.
- route, flow, timing, and state-machine pages where a local fix to one
  connector or label was not followed by whole-diagram review. Moving a label,
  rerouting a line, or changing a node can introduce new title-zone pressure,
  line/label clearance issues, or false grouping.
- punctuation-only final lines, one-character CJK final lines, or very short
  wrapped tails in visible text;
- connector lines not sharing the same center as the cards or nodes they join;
- shared process bands where connectors float between text clusters instead of
  connecting separate cards or nodes;
- bottom callout text not centered in its frame;
- bottom summary panels whose label/body text are not vertically centered in
  the frame;
- text riding a separator line even when shape bounds do not overlap.

The script-generated `layout_audit.csv` is evidence, not the verdict. Use it
to compare repeated title/header/rule positions across slides and across runs.
If the CSV shows drift that the PNG review did not discuss, the review is
incomplete.

## Manual PNG Checks

After script checks pass, inspect:

- contact sheet of all slides;
- every slide with a repeated header or footer component;
- every process/flow slide with connectors;
- every slide whose content was built from repeated generated components;
- any slide the user previously flagged, even if the script no longer warns.

For each repeated component, answer:

- Does it share one obvious baseline or center line?
- Is it authored as one component with a declared center line, or as several
  unrelated coordinates that happen to be near each other?
- If it is a repeated multi-shape PPT component, is it an actual group in the
  PPTX or only a loose set of shapes placed near each other?
- If it has a number, does the number scale with the component and align with
  the intended title row, instead of floating as a tiny corner chip?
- If it uses a left color strip or accent bar, does the strip encode a real
  category/progress/hierarchy role, or is it decorative patching?
- Would a user draw the same alignment guide through the intended elements?
- Is any rule, label, or connector visually floating?
- Does any text inside a frame touch the border or escape the frame?
- Do bars, figure placeholders, screenshots, and chart tracks stay inside the
  parent component with visible air on both sides?
- Are local symbols visually centered inside their own subgrid, with balanced
  gutters where the design expects symmetry?
- For branch diagrams, does the upstream connector line share the same
  centerline as the downstream middle branch when the route reads as one path?
- Is required text readable against its exact local background, including photo
  regions and dark panels?
- Are embedded figure or screenshot labels readable without zooming?
- If this component appears on multiple slides, does it land in the same place?
- Is the component generated by one helper or by copied manual coordinates?

## Baseline Workflow

1. Export PNGs from PowerPoint in a stable environment.
2. Save a contact sheet and representative full-size PNGs in the project review
   folder.
3. Compare the new PNGs with the last approved baseline when one exists.
4. If the change is intentional, update the baseline and record why.
5. If the change is accidental, fix the generator component, not only the final
   PPTX.
6. Add one regression note or test case for any user-found obvious miss.

## Report Requirement

Add a short section to the visual report:

```text
Layout stability verdict: Pass / Targeted fixes / Unstable
Superseded verdict: <previous score/verdict and why it failed, or none>
Contract checked: <header/components/grid/baseline>
Authoring source checked: <file/helper/layout IR/template clone>
Representative sample checked: <slides or missing>
Script blockers: <none or list>
Manual PNG blockers: <none or list>
Baseline action: <kept / updated / missing and must be created>
Generator action: <component fixed / manual coordinates remain>
Audit evidence: <layout_audit.csv/contact sheet/full-size PNGs>
```

If the user finds an obvious alignment issue after a `Pass` or high score, the
next round must score the previous workflow as failed, update this gate or the
script, and rerun the regression case before claiming stability.
