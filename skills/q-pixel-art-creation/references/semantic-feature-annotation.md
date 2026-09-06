# Semantic Feature Annotation Reference

## Coordinate contract

- Coordinate space: native pixels of the complete review crop.
- Side convention: `screen-left` and `screen-right`, never the character's
  anatomical left/right.
- Box format: `[x, y, width, height]` with half-open bounds.
- A naturally invisible side is `null` with an occlusion reason.
- The merged box is the exact minimum union of every non-null side box.

Recommended per-sample fields:

- `id`;
- `screen_left_*_box` and `screen_right_*_box`;
- `merged_*_box`;
- visible-part completeness;
- task-specific boundary completeness, such as upper-lid completeness;
- neighboring-part or attachment relationship;
- natural occlusion by hair, glasses, clothing, prop, or pose;
- confidence, status, notes, and evidence path.

## Observable hard gate

- **Trigger:** a final coordinate, crop, exercise mask, semantic truth, or
  precise approval is requested for a pixel-art part.
- **Must:** count visible instances from the full image; inspect each disputed
  sample at native 1x and on a 1px grid; frame each side independently; record
  null natural occlusion; run structural and independent visual review.
- **Blocks:** exercise generation, mastery claims, avatar/game/site integration,
  and any `precise`, `final`, or `100%` semantic claim.
- **Check:** schema/bounds/union validator plus a Visual Arbiter report that
  cites per-sample native evidence.
- **Repair:** return to the complete crop, discard mirrored or detector-derived
  truth, rebuild the boxes independently, and rerun both checks.
- **Waiver:** none for visible truncation, invented symmetry, or accessory/body
  confusion. A user may accept an explicitly unresolved study sample, but it
  remains excluded from exercise generation.
- **Scope:** pixel-semantic study and precise crop/mask work. It does not force
  this annotation ceremony onto ordinary freehand concept sketches.

## Regression scenarios

1. A side face with one naturally hidden eye must keep the hidden side `null`.
2. Bangs may occlude an eye; visible pixels can still be complete without
   claiming the anatomical eye is fully visible.
3. A headphone, earring, hair clip, or background mark beside an eye must not
   become an eye box.
4. A tilted elderly face may place two closed eyes at different heights; a
   horizontally aligned dark line may be a brow, not an eye.
5. A detector crop that clips an upper lid fails even when its JSON is valid.
6. A contact sheet can flag a sample for inspection but cannot pass its precise
   coordinates without the native sample and grid.
