# Pixel Art Quality Gates

## Semantic localization gate

- Count actually visible parts on the full image before drawing any box.
- Inspect native 1x first, then integer nearest-neighbor zoom and a 1px
  coordinate grid for every disputed or precision-critical sample.
- Frame each visible part independently. Never mirror, translate, or invent a
  second eye, hand, accessory, or other feature because symmetry suggests one.
- Detector output is a proposal only. A contact sheet is a navigation and
  overview artifact only; neither can authorize precise final coordinates.
- Natural occlusion and crop truncation are separate states. A naturally
  invisible side is `null`; a visible part is complete only when all currently
  visible semantic pixels are inside its box.
- Approval requires 100% coverage of visible semantic pixels and zero
  truncation. An expert reviewer must cite native 1x or 1px evidence rather
  than merely agree with the previous annotation.

## Native and effective resolution

- Review 1× before zoom.
- Zoom previews must be exact integer nearest-neighbor copies.
- Major contours must use purposeful varying step lengths, taper, counter-curve,
  and negative space; repeating 3/4 px stairs across every form fail.
- Detail must explain anatomy, form, material, attachment, light, or hierarchy.
  Random noise and countable decorative dashes do not count.
- A large native canvas or high pixel count does not prove high effective
  resolution. A mature/high-detail claim fails when the native first read still
  looks like a smaller sprite enlarged and its middle/small clusters do not
  continue to explain volume, age, material, contact, or focus. Return to the
  earliest implicated shape, mass, or local-cluster layer. Do not fill quiet
  planes with random 1 px noise, extra colors, uniform texture, or patterns.
  Quiet areas are valid when their information density follows focus and
  material hierarchy. A deliberately low-resolution-on-large-canvas direction
  may pass its own recorded goal, but must not be presented as high-detail.
- Curvature refinement must preserve purposeful bone, seam, tool, contact, and
  load-bearing corners. Reducing angularity by making every contour round fails
  when it creates tube limbs, egg torsos, snowman masses, round glove hands, or
  pill shoes.
- At joints, require a readable mass transition, continuous outer arc, short
  inner compression, distal taper, and any necessary short bone/load plane.
  A uniform bent tube does not pass.

## Mature surface and material specimen gate

Apply this conditional gate to a mature/high-detail original character final,
an explicit material-differentiation claim, or a candidate whose cold review
reports hue-only or component-like surfaces. It is normally N/A for exploration,
flat graphic styles, single-material small props, ordinary tiles, and low-risk
studies when the scope reason is recorded.

- Before whole-character integration, study every in-scope material or endpoint
  family that carries maturity, identity, load, or contact at its actual native
  footprint. Pass a monochrome/grayscale/limited-value construction before
  color. The specimen must retain its real task: a hand grips, a boot relays
  ankle-to-sole load, cloth responds to an anchor/force, and a vessel shows rim,
  wall, cavity, and attachment as applicable.
- Distinguish surfaces through form-related edge hardness, fold origin and
  compression, highlight width and value jump, rim/inner-wall thickness,
  contact shadow, and cluster rhythm. Hue alone cannot carry the distinction.
  Do not require a universal feature count or exact material-name guess; after
  desaturation, different surface response, thickness, and contact logic must
  remain perceptible at native size.
- A specimen pass authorizes integration only. Replay native color, grayscale,
  and mirror after integration, then run the existing independent structure and
  cold art-direction final gates. If the whole character returns to assembled
  components or enlarged-small-sprite language, final remains blocked.

## Repeated radial/rotated component gate

For repeated radial/rotated components that should share one topology, the
mother-part procedure in `workflows/learn-create-review.md` is mandatory. Native
and whole-object mirror review must preserve the shared pivot, attachment,
thickness family, negative space, and handed opening. Rotating only the shell,
mirroring one copy independently, or redrawing copies into different topology
fails; perspective, flexible, organic, or deliberately asymmetric cases may be
N/A with a recorded reason.

## Portrait gate

- Near/far eyes respect perspective and contain readable lids/apertures.
- Nose bridge/side/base and mouth/chin are separate turning planes.
- Cheek, jaw, and skull values connect into one volume.
- Hair is organized into overlapping root-to-tip volumes with tapered ends.
- Jewelry shows attachment/occlusion, body, shadow, and highlight.
- Clothing shows thickness, overlap, seam/fold, and neck/shoulder tension.

## Full-body and action gate

- Each pose has its own spine, shoulder line, pelvis, support foot, and silhouette.
- At 50%, poses remain distinguishable without labels.
- For a final action or integration claim, review the image without a title or
  answer key first. An independent reviewer must recover the action family,
  dominant direction, and support side. Preserve the first blind reading; an
  answer label cannot explain away a mismatch. When a specific action is
  inherently prop-defined, retain the minimum functional prop direction/contact
  needed for a fair read.
- Interaction closes `gaze -> contact -> weight -> cloth`:
  - gaze points toward the task or target;
  - hand/foot overlaps establish contact;
  - ground and support area are explicit, and the center-of-mass projection is
    checked: a static pose keeps the projection inside its support area; a
    dynamic pose may let it leave only when visible momentum, reaction force,
    or the next landing/contact explains the imbalance;
  - sleeves, hems, hair, and props respond to the action.
- Before pixel phrasing or finished detail, grayscale masses and a truly merged
  silhouette must preserve the blind action/support read. Ribcage, pelvis,
  limbs, hands/props, and support feet relay through overlap, compression,
  taper, and contact rather than separate closed pieces.
- A major joint needs an entering direction, an exiting direction, and a visible
  overlap/compression result. Circular bearing joints, trapezoid rods, complete
  internal part outlines, false segmented silhouettes, or floating feet fail
  the mass-relay gate even when the gesture skeleton is correct.
- A hand-held prop must pass in front of and behind the palm/fingers.
- A multi-frame sheet fails if only the prop or UI marker changes.

## Environment gate

- Foreground, middle ground, and background are separable at native view.
- Character scale supports the scene and is not an enlarged low-resolution sprite.
- Focal contrast and brightest accents serve the subject/route, not random texture.
- Texture density varies by distance and material.
- The final scene is authored at the actual requested output size; if any layer
  is intentionally scaled, record the source size and why it remains acceptable.

## High-risk flow and semantic replay gate

- Apply this gate when ordinary creation repeatedly fails on stiffness,
  contact, or support; for a high-risk final/mastery/integration full-body
  action; or for an explicit unseen-original-transfer proof. Ordinary
  exploration does not require the full ceremony.
- Before high-risk or unseen-transfer synthesis, pass the applicable design
  evidence: no-prop/minimum-prop action and support silhouette; same-skull face
  variants when age/identity/expression is in scope; broad flat/round value
  planes; and focal light/color budget when focus is in scope.
- Passing a design-evidence board does not approve the synthesized asset.
  After material and color, replay the named semantic locks at the same native
  size, crop, background, and prop condition. Compare color, grayscale,
  silhouette, and no-prop/minimum-prop views as applicable.
- A prop-defined action may retain the minimum functional prop during blind
  action review. Use a no-prop view to expose weight, action family, false
  appendages, shared mannequins, and contacts that existed only through color.
- Reject any final candidate where material/color reinterprets a grounded knee
  as a shoe, cloth as an arm, a hand as a floating fist, or a face as a different
  age/expression, even when alpha, dimensions, or an earlier board still pass.
- Artifact metrics may support a specific replay but never override native
  perception or become universal requirements for color count, singleton
  pixels, silhouette drift, saturation ratio, or curve-run lengths.
- See `workflows/flow-expression-and-unseen-transfer.md` for the two-mode stage
  sequence and controlled-negative rules used only for study/mastery claims.

## Reconstruction and identity gate

- Exact reconstruction and refinement are separate files.
- First review artifact includes an honest pixel grid.
- Identity anchors are named before refinement and rechecked afterward.
- Refinement replaces incorrect pixels; it does not add a fuzzy outer shell.
- User-owned marks, letters, accessories, and costume meanings are preserved.

## Approval gate

Structural checklists cannot override a perceptual failure. Final approval
requires an independent native-size visual decision. Personal avatars and
public/game integration additionally require Xiao Q review.

For mature or high-detail original characters, approval is a dual gate:

- `native/structure`: anatomy, support, contact, silhouette, value continuity,
  and semantic locks pass at native 1x;
- `cold art direction`: first-look appeal, hierarchy, proportion, material
  phrasing, effective detail, and whole-character coherence pass without relying
  on captions or iteration history.

Both must pass independently. A rejection or split verdict blocks `final` even
when executable format validation passes. A same-size maturity benchmark is
calibration evidence only: disclose source/license/derivation, mark external or
generated targets non-deliverable, and never let the board approve, replace, or
serve as a tracing base for the final asset.

Treat repeated failure of one connected system—such as head/gaze, pelvis-leg-
shoe support, hand-prop contact, or cloth-force response—as patch exhaustion.
After at most two bounded local repairs, or immediately when the upstream cause
is clear, stop local edits and reopen the earliest implicated design layer. Do
not mechanically return to the most recent structural PASS when the aesthetic
failure shows that baseline itself was wrong. Isolated local defects do not
trigger this restart rule.

Reference-study scores cannot override original-transfer failure. A reference
reconstruction may pass its own gate while the overall skill remains unproven.
An original character set must also pass label-free silhouette, age/identity,
prop-contact, and material-readability checks before it can support a mastery
or integration claim.

A practice board or positive example that authorizes later migration must pass
the applicable native, grayscale, silhouette, action/contact, and ensemble
checks on sufficiently different targets. Correct wording cannot override a
misleading picture. Keep a failed teaching example as evidence, repair it, and
re-run the same target gates before reuse.

Review an executable teaching board blind-first: show its unlabeled image,
freeze the reviewer reading, then reveal the answer key. If the picture needs
its caption to become correct, it fails as a positive teaching artifact.

When a migration derivative fails structurally, allow at most one explicitly
bounded repair limited to the failed clusters. If the repair retains the failed
silhouette/body template, adds competing limbs/contacts, or spreads beyond the
frozen scope, stop patching. Restart from the target's last approved baseline,
erase/replace only the violating native clusters, render same-condition
before/after boards, and expose a changed-pixel diff before reapplying the gates.

## Character cast / ensemble gate

- All in-scope cast members must be reviewed together at native 1x in color and
  grayscale, plus an integer nearest-neighbor preview. A no-prop silhouette board
  is required for full-body/action casts or a silhouette-differentiation claim.
- Add a face/age strip when age, facial identity, or expression differentiation
  is claimed. Reusing one face with different hair or palette fails.
- Full-body/action casts fail when no-prop silhouettes collapse into one body
  template, even if props and colors differ.
- A held or interactive prop fails when it sits beside a fist instead of passing
  in front of and behind fingers/palm with readable contact negative space.
- Every in-scope detailed/full-body member must pass grayscale structure before
  final color; passing one anchor does not exempt the rest of the cast. A mature
  face pasted onto a shared mannequin or flat paper torso fails.
- An anchor is a decision example, not a reusable silhouette, limb, hand, foot,
  or torso template. Migration starts from each target's own approved anatomy,
  weight, action and contact chain; copying the anchor's visible roundness or
  curve coordinates across the cast fails even when the anchor itself passed.
- Claimed material differences must survive an unlabeled blind-read by edge,
  fold, reflection, and cluster behavior. Recoloring one hard-cloth mechanism
  does not pass.
- Integrated color must survive native grayscale regression: faces remain the
  primary local focus and hands/props remain secondary action focus.
- Conditional gates may be `N/A` only with a recorded scope reason. Missing an
  applicable all-cast board blocks a final ensemble claim, not exploration.
- See `workflows/character-cast-gates.md` for the gate graph and repair loop.
