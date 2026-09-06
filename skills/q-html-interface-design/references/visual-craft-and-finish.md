# Visual Craft And Finish Gate

Use this reference when Xiao Q says a page is ugly, amateur, entry-level,
visually crude, unfinished, or when the requested artifact must look genuinely
high-fidelity. This gate evaluates execution quality. It is separate from
anti-template identity, usability, accessibility, and functional correctness.

## Why This Gate Exists

A page can have a unique topology and still look like an enlarged wireframe.
Passing swap, squint, remove-name, or signature tests does not prove that the
type, spacing, color, edges, and controls were designed with precision.

When user feedback exposes this miss, freeze the rejected render and score it
again under this gate. A previous positive verdict becomes unstable evidence;
do not defend it with the old rubric.

## Candidate Maturity

Declare exactly one state before review:

- `low-fi`: structure and task order only; visual finish is intentionally not
  evaluated and the artifact cannot be presented as the aesthetic answer.
- `visual study`: type, color, proportion, and composition are being compared;
  interactions may be partial but the render must be visually intentional.
- `high-fi`: representative content and states, responsive behavior, and craft
  details are ready for visual approval.
- `production`: high-fi plus complete interaction, accessibility, performance,
  error/empty/dense states, and implementation verification.

## Reference Calibration

For `visual study` and above, select 2-3 references with different roles:

1. domain/product exemplar for density, hierarchy, and work rhythm;
2. typography/composition exemplar for scale, measure, alignment, and visual
   tension;
3. interaction/craft standard when controls, motion, or responsive behavior are
   important.

For each source, record `mechanism`, `local adaptation`, and `do-not-copy`
boundary. References calibrate quality; they do not authorize cloning layout,
tokens, code, copy, screenshots, or brand assets.

## Six Craft Axes

Score each axis `0–3` with screenshot evidence.

### 1. Typography

- `0`: generic/default type with accidental hierarchy, awkward Chinese/Latin
  mix, widows/orphans, or oversized heavy headings.
- `1`: legible but neutral and under-tuned; too many weights/sizes or weak
  measure/leading.
- `2`: deliberate roles, stable hierarchy, clean wrapping, aligned numbers,
  and credible Chinese/Latin fallback.
- `3`: typography carries product character while remaining precise and calm.

### 2. Proportion and composition

- `0`: enlarged wireframe, accidental balance, excessive empty or occupied
  mass, or a signature that consumes space without earning it.
- `1`: structurally clear but visually inert, crowded, or mechanically even.
- `2`: focal mass, supporting regions, and negative space form a deliberate
  composition at desktop and mobile.
- `3`: the composition has controlled tension and remains recognizable without
  labels or accent color.

### 3. Spatial rhythm

- `0`: arbitrary gaps, repeated dividers, stacked bars, or inconsistent
  vertical cadence.
- `1`: uses a spacing scale but lacks optical correction or grouping nuance.
- `2`: adjacency, grouping, and breathing room match content relationships.
- `3`: rhythm guides scanning almost invisibly across dense and sparse states.

### 4. Color and material

- `0`: generic palette, timid equal distribution, muddy contrast, or color used
  mainly to make an unfinished layout feel designed.
- `1`: coherent and accessible but flat or weakly tied to the subject.
- `2`: dominant/supporting/semantic roles are clear; surfaces and depth form a
  credible material world.
- `3`: color and material create a specific atmosphere without reducing data
  legibility or trust.

### 5. Edge and component precision

- `0`: every region outlined, arbitrary rules/radii/shadows, debug-like focus,
  misaligned icons/text, or controls that look like browser defaults.
- `1`: consistent tokens but insufficient optical tuning and state finish.
- `2`: borders, radii, shadows, icons, controls, and states share coherent
  geometry and visual weight.
- `3`: detail crops remain convincing; components feel authored rather than
  assembled.

### 6. Responsive art direction

- `0`: desktop merely stacks; fixed bars collide; mobile loses composition or
  becomes generic app chrome.
- `1`: usable at mobile width but the visual idea weakens substantially.
- `2`: hierarchy is deliberately re-sequenced, compressed, or made persistent.
- `3`: mobile feels like the same art direction expressed through a different
  composition, not a reduced desktop.

## Evidence Scales

Review all three:

1. `thumbnail`: whole page at reduced size; judge mass, focal relationship,
   rhythm, and color balance.
2. `normal`: actual viewport; judge hierarchy, reading measure, density, and
   state clarity.
3. `detail`: crop representative heading/body/data, one control group, and one
   material boundary at 100–200%; judge type rendering, spacing, alignment,
   border/shadow/radius, and icon balance.

Source inspection alone cannot pass this gate.

## Pass And Block Rules

- `visual study`: no axis may be `0`; at least four axes must reach `2`.
- `high-fi`: every axis must reach `2`; at least two axes should reach `3`.
- `production`: every axis must reach `2`, with complete state and
  implementation validation from the normal HTML gate.
- Any `0` blocks polished/high-fi/excellent/exemplar claims. Do not average it
  away.
- If typography, proportion/composition, or edge/component precision scores
  below `2`, the page cannot be called visually ready even when the total looks
  high.

## Repair Routing

- Typography failure: return to type roles and real content; do not tune cards.
- Proportion failure: return to composition and visual mass; do not add detail.
- Rhythm failure: remove redundant separators/bars, regroup content, then tune
  optical spacing.
- Color/material failure: reduce to neutral structure, then rebuild functional
  roles from the subject world.
- Component precision failure: create detail crops and tune one component
  family before propagating. When selection is central to the user's reading
  task, return to the state grammar: selected/current must change a meaningful
  relationship or consequence, not merely receive an isolated library-style
  marker.
- Responsive failure: redesign the narrow composition; do not append more fixed
  bars.

## Anti-Patterns

- Treating a high anti-template score as proof of good taste.
- Giving a low-fi prototype a high visual score because its idea is novel.
- Adding gradients, textures, shadows, or motion before type and proportion are
  credible.
- Using an average score to hide one visibly amateur axis.
- Reviewing only a full-page screenshot where weak typography and component
  edges are too small to judge.
