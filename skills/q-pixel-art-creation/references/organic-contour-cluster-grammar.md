# Organic Contour Cluster Grammar

Use this reference when a generated or translated portrait, creature, cloth,
hair, hood, or other organic pixel-art component has a sound silhouette but
its contour looks noisy, thin, heavy, or rhythmically inconsistent.

## Research Posture

These rules are independently written mechanisms distilled from artist-owned
tutorials and local regression evidence. External artwork is reference-only:
do not copy coordinates, palettes, clusters, or assets.

Primary learning sources:

- Cure, *The Pixel Art Tutorial* (PixelJoint): intentional placement,
  clusters, jaggies, banding, noise, and selective outlining.
- Pedro Medeiros, *Cluster Sketching and Painting* and *Anti-Alias and
  Banding*: cluster-first construction, monotonic stair logic, and bounded AA.
- Raymond Schlitter / SLYNYRD, *Back to Basics*: repetition, order, cluster
  economy, and deliberate cleanup.
- Lospec, *Pixel Art Outlines Tutorial*: regular diagonal steps, progressive
  curve steps, deliberate corners, and selective internal outlines.
- Aseprite official documentation: outline/despeckle features are mechanical
  operators, not aesthetic authorities; their output still requires manual
  semantic review.

## Trigger And Strength

- Trigger: an organic contour is already recognizable but contains mixed
  near-colours, orphan cells, inconsistent apparent weight, random step-length
  changes, or a second fringe line after generation/transcription.
- Strength: procedure plus hard visual gate for user-facing final assets.
- Goal: preserve the approved silhouette and identity while making every
  contour cluster read as deliberate at native 1x.
- Anti-pattern: global smoothing, morphology, automatic outline replacement,
  row-wise width normalization, or scattered one-cell edits that do not change
  the connected arc.

## 1. Calibrate The Visual Pixel Unit

The file pixel is the coordinate unit; it is not always the dominant visual
stroke unit. A translated 512 image may use recurring 2x2, 2x3, or 3-cell
clusters to express one apparent pixel-art stroke.

Before editing a semantic component:

1. Sample at least three stable straight or gently curving segments.
2. Record the recurring core thickness, step lengths, and smallest purposeful
   cluster. Call this the local visual pixel unit (LVU).
3. Measure thickness perpendicular to the path, not by horizontal row width or
   vertical column height alone.
4. Keep file-level coordinates for replay, but judge rhythm in LVU-scale
   clusters.

An isolated one-file-pixel repair can be valid as a gap fix, but it is only a
diagnostic patch when the dominant contour language is built from larger
clusters. It cannot be presented as a perceptually meaningful contour pass.

## 2. Classify Every Boundary Segment

Each connected contour segment must be one of:

- `REGULAR_LINE`: constant slope; repeat equal step lengths.
- `CURVE`: step lengths progress monotonically toward or away from the local
  horizontal/vertical tangent; plateaus are allowed.
- `PURPOSEFUL_CORNER`: a named tip, fold, chin turn, ear point, or hard corner;
  may break the progression once.
- `JUNCTION`: two volumes meet; preserve both silhouettes and the occlusion
  order before optimizing either local line.
- `CONTACT_OR_OCCLUSION`: line weight may increase to separate overlapping
  forms.

Do not repair a junction using a rule learned from a regular line. Do not call
an unexplained bump a purposeful corner.

## 3. Build Curves From Step Sequences

- A straight diagonal repeats one step ratio.
- A curve uses ordered run lengths, for example `1,1,2,2,3` or
  `4,3,3,2,1`; it may accelerate or decelerate, but must not chatter like
  `1,3,1,2,4` without a named corner.
- Avoid abrupt jumps when an intermediate run can preserve the same silhouette
  intent.
- Judge the whole arc between semantic anchors. Crop boundaries are not curve
  endpoints.
- Preserve the source-local visual weight. A three-layer local contour cannot
  be replaced by a one-cell diagonal just because the latter is mathematically
  smoother.

## 4. Use A Three-Band Boundary Model

Review each arc along its local normal:

1. `INNER_PLANE`: the object's quiet base or shadow plane.
2. `CORE_CONTOUR`: the connected dark cluster carrying silhouette or
   occlusion.
3. `OUTER_PLANE`: background or the adjoining object.

Optional transition colour is not a fourth ribbon. It must be a short,
purposeful cluster attached to a named turn, light transition, or long stair.
It must not run parallel to the core for a long distance, duplicate endpoints,
or create banding.

## 5. Anti-Alias Only After Geometry Passes

- First make the hard contour readable at native 1x.
- Consider AA only on steps longer than 1x1 when the native curve still looks
  jagged.
- Keep AA proportional to the step it softens and use the minimum number of
  half-tone clusters.
- Do not AA straight lines or 45-degree 1x1 stairs by default.
- Do not use AA to hide a wrong run sequence, wrong silhouette, or broken
  junction.
- Remove AA that forms hugging, a parallel contour, blur, or an unexplained
  material colour.

## 6. Orphan And Fringe Decision

A one- or two-cell cluster survives only when it has an explicit role:

- specular highlight or essential tiny feature;
- part of a deliberate AA sequence;
- connector between larger same-role clusters;
- material, contact, or occlusion cue visible at native 1x.

Otherwise merge it into the adjacent semantic plane. For contour cleanup,
foreign near-black, near-yellow, wall-blue, or shadow colours inside the core
are defects unless the segment contract names their role.

## 7. Required Editing Order

1. Freeze baseline hash, semantic component, silhouette anchors, junctions,
   identity, and local visual pixel unit.
2. Normalize colour roles without changing occupancy.
3. Write the complete arc's current run-length sequence and mark only proven
   rhythm breaks.
4. Repair occupancy in coherent arc patches with an explicit coordinate
   ledger; do not scatter independent edits around the component.
5. Rebuild the adjacent inner/outer plane where the repair exposed fringe.
6. Add or remove bounded transition clusters only after the hard contour
   passes.
7. Validate native 1x first, then integer zoom and a 1px coordinate grid.

If the local edit improves the grid but is imperceptible at 1x, record it as a
diagnostic cleanup, not an art-direction improvement. If a visible improvement
would require moving protected anchors or changing identity, stop and return
to the parent candidate.

## 8. Evidence Contract

For every contour candidate provide:

- immutable parent and hash;
- complete semantic-component crop, not a tiny disputed fragment;
- `BASELINE / CURRENT / CHANGED` with a visible 1px grid;
- native full image and native semantic crop;
- coordinate ledger grouped by arc and reason;
- run sequences before and after;
- counts for recolour, occupancy add, and occupancy remove;
- explicit verdict for silhouette, junctions, local visual weight, orphan
  pixels, parallel fringe, and native 1x visibility.

## 9. Hard Rejection Conditions

Reject the candidate if any is true:

- a smooth arc still contains an unexplained run-length reversal;
- contour weight changes because horizontal/vertical counts were normalized
  without considering path direction;
- a junction, ear root, tail root, face opening, or contact seam changes form;
- transition colour becomes a second contour or a long hugging band;
- a new orphan cluster or foreign colour appears beside the repaired arc;
- only a few file pixels changed while the claimed improvement concerns the
  whole contour rhythm;
- the grid looks tidier but the native 1x silhouette is unchanged or worse.
