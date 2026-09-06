---
name: q-pixel-art-creation
description: Create, study, reconstruct, refine, or review pixel-art characters, portraits, action sheets, props, tiles, and scenes. Use when Xiao Q asks for pixel characters, 128/256 avatars, sprite studies, pixel animation poses, pixel-game art, grid reconstruction, native-size review, or a staged learn-copy-internalize-create workflow.
---

# Q Pixel Art Creation

Use this skill for pixel-art asset creation and the learning loop that precedes
high-stakes avatar or game-asset work.

## Route

| Intent | Route |
|---|---|
| Learn from tutorials, games, or asset sites | Run `workflows/learn-create-review.md` in study mode; read `references/license-and-sources.md` |
| Resume a registered source-driven training project, or replace repeated unstructured self-practice | Read the project recovery entry and source registry first; then run `workflows/source-driven-training.md` and read `references/license-and-sources.md` |
| Study or localize eyes, brows, facial features, or other pixel-semantic parts | Run `workflows/semantic-feature-study.md`; read `references/semantic-feature-annotation.md` |
| Reconstruct an existing personal drawing | Run reconstruction mode; preserve a gridded exact version before any refinement |
| Create an original character, pose sheet, prop, tileset, or scene | Run creation mode and the applicable gates in `references/quality-gates.md` |
| Rescue repeated stiffness/contact/weight failures, or prove a high-risk final/mastery/integration full-body action or unseen original transfer | Run `workflows/flow-expression-and-unseen-transfer.md` in the matching mode; for a cast, then run `workflows/character-cast-gates.md` |
| Build or validate a multi-character cast with age, identity, action, prop, or material differences | Run `workflows/character-cast-gates.md`; then apply the ensemble gate in `references/quality-gates.md` |
| Review a pixel-art candidate | Run review mode at native 1× first, then integer nearest-neighbor zoom |
| Clean noisy organic outlines while preserving an approved silhouette | Read `references/organic-contour-cluster-grammar.md`; normalize colour roles before changing occupancy |
| Package an accepted avatar for profile, website, and detailed review | Read `references/avatar-delivery-and-archive.md`; retain one native authority and named derivatives |
| Integrate approved art into a game | Finish this skill first, then hand the approved asset to `q-game-canvas-iteration` |

## Default Behavior

1. Lock the target size, use, identity anchors, palette intent, and whether the
   output is study-only or shippable.
2. When learning from references, extract mechanisms rather than copying
   coordinates, artwork, text, or palettes. Mark reconstruction studies
   `non-shippable` until license and originality gates pass.
3. Work from structure to feature planes, material, action, and environment.
   Do not jump from small icons directly to a high-stakes 256 avatar.
4. Inspect the native image at 1× before zooming. Use only integer
   nearest-neighbor zoom for pixel-construction review.
5. Prefer perceptual evidence over checklist counts. A nominal 128/256 file
   fails if it looks like enlarged 32/64 art.
6. For movement and tool use, close the `gaze -> contact -> weight -> cloth`
   loop. Moving a prop beside a static body is not a new action.
7. Require independent visual review before the asset is called final or is
   integrated into a personal avatar, game, or public-facing page.
8. For pixel-level semantic approval, review one sample at a time from the full
   image through native 1x and a 1px coordinate grid. Treat detector output and
   contact sheets as proposals, not truth.
9. Treat any practice board, positive/negative diagram, or anchor that will
   drive later migration as an executable teaching artifact. Its pictured
   mechanism must pass on sufficiently different targets before its caption can
   be treated as a reusable rule.
10. Refine curvature through **structure before roundness**: freeze age,
    proportion, action, weight, contact, and purposeful corners first; then
    erase/replace only the contour or value clusters that violate the intended
    curve rhythm. Do not turn limbs into tubes or torsos into eggs to reduce
    angularity.
11. For a mature or high-detail original character final, require both an
    independent native/structure decision and a cold-context first-look art
    direction decision. Either rejection, including a split verdict, blocks
    `final`; format validation or an earlier structure pass cannot overrule it.

## Composition Boundaries

- `q-pixel-art-creation` owns pixel-art learning, construction, native-size
  validation, action readability, asset provenance, and visual approval.
- `q-game-canvas-iteration` consumes approved assets and owns game behavior,
  controls, collisions, feedback, level flow, packaging, and runnable QA.
- `imagegen` may assist with original concept exploration or bitmap ideation;
  it does not waive provenance, grid, native-size, effective-resolution, or
  independent-review gates. Generated studies must be disclosed in the work
  record.
- Do not use this skill for general photo pixelization, an editable SVG/logo
  system, ordinary UI icons, or simple image-format conversion. Route general
  bitmap generation/editing to `imagegen`; route vector-native work to its
  owning design/code workflow.

## Hard Stops

- Do not ship or integrate a reference reconstruction.
- When a project declares a recovery entry, do not recover its active source, exercise, stage, or next action from chat history, modification time, or the newest artifact. Missing or inconsistent recovery state blocks drawing until it is repaired.
- Do not call a 128/256 asset high-detail because of canvas dimensions,
  color count, or part count alone.
- Do not smooth a personal pixel drawing by painting outside its old contour.
  Erase/replace incorrect pixels, preserve an exact version, and refine in a
  separate candidate.
- Do not hide a failed native 1× read behind a large preview.
- Do not continue to a personal 256 avatar until the staged practice and
  independent review have passed and Xiao Q has seen the gridded first version.
- Do not infer a hidden or tilted feature by mirroring another feature. Each
  visible eye, brow, hand, accessory, or contact point needs independent pixel
  evidence; naturally invisible parts stay `null` or unresolved.
- Do not approve precise pixel semantics from a contact sheet alone. The final
  reviewer, including an expert reviewer, must inspect native 1x and 1px
  evidence for every disputed sample.
- Do not treat a passed anchor as a shape library. It demonstrates a decision
  process; each target must derive its own contours from its approved structure,
  action, weight, and contact evidence.
- Do not promote a technically valid mature-character sprite while its cold
  first-look art-direction review still reads icon assembly, weak appeal, or
  immature material/anatomy. Record it as a candidate and return to the earliest
  implicated design layer.

## Outputs

- reference/source card with license posture;
- structure/grid draft when reconstruction or identity work is involved;
- native-resolution PNG and integer-zoom review preview;
- action sheet or environment scene when in scope;
- validation output from `scripts/validate_pixel_art.py`;
- expert review report with pass/fail and repair loop.

## Handoff

Record which artifacts are study-only, which are approved, the native sizes,
palette and identity anchors, review result, source/runtime tool path, and any
remaining limitations. Keep failed candidates as private evidence, not final
deliverables.
