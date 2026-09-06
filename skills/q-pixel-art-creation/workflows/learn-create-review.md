# Learn, Create, Review

## 1. Classify the task

- `study`: mechanism learning from tutorials, games, public previews, or asset libraries;
- `reconstruct`: exact recovery of a user-owned drawing or sprite;
- `create`: original character, action sheet, prop, tile, or scene;
- `review`: native-size and perceptual audit of an existing asset.

Record target size, use, shippability, identity anchors, required poses, final
file type, and downstream consumer before drawing.

## 2. Build the source card

For every source, record URL/file, source role, author/site, license evidence,
what may be learned, and what may not be copied. A public preview is observable,
not automatically reusable. A study reconstruction stays `non-shippable`.

## 3. Study before synthesis

Observe and name mechanisms:

- silhouette rhythm and step-length variation;
- feature planes and asymmetric perspective;
- palette families and value grouping;
- hair/fabric/metal/stone/foliage material cues;
- pose skeleton, support foot, contact, gaze, and secondary motion;
- environment depth, scale, focal contrast, and texture density.

Create a small mechanism brief. Do not copy source coordinates, full palettes,
prompts, code, or artwork.

When the study target is a semantic part such as an eye, brow, mouth, hand,
hair lock, or prop contact, route the localization pass through
`semantic-feature-study.md` before generating exercises. Precise coordinates
must come from per-sample native evidence, not from a detector, symmetry, or a
batch contact sheet.

## 4. Use a staged ladder

Default ladder for character-heavy work:

1. single-color contour and negative space;
2. limited-value object with intentional light direction;
3. multi-color material study;
4. native 128 portrait with facial planes, hair volume, clothing, and jewelry;
5. native 256 full-body character with prop contact and three distinct poses;
6. action/interaction sheet whose frames remain readable without labels;
7. fantasy/complex-material character;
8. character-in-environment scene, ending at the actual requested resolution.

Reference reconstruction is evidence of observation and construction only. It
does not prove original creation ability. Before claiming the staged ladder is
mastered, or before integrating a personal avatar or identity asset, require an
unseen no-reference original transfer test with the same native-size and
independent-review gates.

Skip a stage only when existing evidence already passes its gate. A nominally
larger canvas is not evidence of higher skill.

## 5. Reconstruction mode

For a user-owned avatar or sprite:

1. analyze the real pixel coordinates and palette;
2. create a gridded exact reconstruction at the requested native size;
3. obtain expert and user review of the exact reconstruction;
4. duplicate it into a separate refinement candidate;
5. erase/replace jagged or inconsistent pixels while preserving identity;
6. add shading or detail only where it improves form and remains faithful;
7. never paint a second outer contour around the original silhouette.

The exact version and refinement version are separate artifacts.

## 6. Creation mode

Build in this order:

1. silhouette and gesture;
2. skull/torso/pelvis/limb masses or environment perspective blocks;
3. broad light and shadow families;
4. face, hands, attachment points, and material turns;
5. selective 1-2 px transitions and highlights;
6. action secondary effects or environmental texture;
7. palette merge: remove colors that do not clarify form, material, contact,
   hierarchy, or identity.

For full-body/action work, local contour cleanliness does not authorize value or
pixel polish. If the pose remains stiff, return to an unlabeled gesture/support
read and continuous mass relay. Do not enter broad light/shadow or finished
detail until the action family, dominant direction, support side, and functional
contacts survive blind review in both a true silhouette and grayscale masses.

For tools and props, explicitly draw which pixels are in front of the hand,
inside the grip, and behind the palm. For motion, change the skeleton and weight;
do not move only the prop.

When one mechanism uses repeated radial or rotated parts that should share one
topology, approve one mother part before duplication. Transform the complete
part together, including its negative space, thickness, handed opening, pivot,
and attachment point; then inspect the rasterized result at native size and in
a whole-object mirror. Use the design's actual angle rather than a universal
rotation value. For non-right-angle pixel rotation, allow bounded cluster
cleanup after nearest-neighbor rasterization, but do not redraw each copy until
its handedness or topology drifts. Perspective shortening, different lighting,
flexible deformation, or intentional asymmetry may reuse only the structural
mother and should record why rigid duplication is not applicable.

## 7. Review loop

1. inspect native 1x first without titles or explanatory captions;
2. inspect integer nearest-neighbor zoom second;
3. run `scripts/validate_pixel_art.py` for dimensions, palette, alpha, and
   exact integer-scale comparison when a zoom preview is supplied;
4. ask a Visual Arbiter to judge feature naturalness, plane continuity,
   contour rhythm, material, action, color hierarchy, and effective resolution;
5. ask an action/structure reviewer when poses, weapons, tools, or interaction
   are involved;
6. classify findings: P1 blocks; P2 should be fixed in the same round when it
   affects final polish; P3 is optional;
7. rebuild from the failed form layer. When action stops at a joint or body mass,
   return to gesture/support/mass instead of polishing pixels. Do not hide
   structural failures with extra micro-details or noise;
8. rerun the same gate after repair.

For a mature or high-detail original character final, record two independent
decisions from the native artifact:

- a native/structure decision covering anatomy, support, contact, silhouette,
  value continuity, and semantic locks;
- a cold-context first-look art-direction decision covering appeal, proportion,
  visual hierarchy, material language, effective detail, and whether the result
  still reads as assembled icons or beginner shorthand.

The art-direction reviewer must cite native observable evidence and the earliest
failed layer; an unexplained taste vote is not sufficient. Both decisions must
pass. A split verdict remains a rejection even when dimensions, palette, alpha,
integer zoom, or a previous structure board pass.

When visual calibration is genuinely unclear, make a same-native-size maturity
comparison board. Disclose the source, license posture, generation/derivation
method, and label any reference- or image-generation-derived target
`non-deliverable`. Use it to compare silhouette economy, focal hierarchy,
material clusters, and effective resolution only. It cannot be traced into the
final, treated as the answer key, or authorize approval.

For one isolated local defect, allow a bounded native-cluster repair. For the
same evidenced system failure, allow no more than two local repair rounds; do
not spend both when the upstream structural cause is already clear. On repeated
failure, or when either reviewer identifies the current baseline as the cause,
stop patching and restart from the earliest implicated layer or the last clean
baseline before that failure. Preserve failed candidates as evidence.

## 8. Release and handoff

Only approved original or licensed assets may enter games or public pages.
Record native dimensions, palette count, transparent-background behavior,
study/shipping status, reviewer result, generation/edit tools, and source card.
If an asset becomes a game dependency, hand it to `q-game-canvas-iteration`
after this workflow is complete.
