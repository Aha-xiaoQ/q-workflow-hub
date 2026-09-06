# Semantic Feature Study

Use this workflow when a pixel-art task depends on precisely locating or
learning eyes, brows, noses, mouths, ears, hands, hair locks, accessories, prop
contacts, or another semantic part.

## Evidence order

1. Open the complete source image or complete face/character crop.
2. Count the actually visible instances. Do not assume bilateral symmetry.
3. Establish pose, tilt, perspective, and the neighboring anatomy or attachment
   relationship before drawing a box.
4. Inspect native 1x.
5. Inspect an integer nearest-neighbor enlargement.
6. Inspect a 1px coordinate grid with axes for any precision-critical or
   disputed sample.
7. Frame each visible instance independently in screen-left/screen-right order.
8. Compute a merged box as the exact union of non-null instance boxes.
9. Run structural validation, then independent visual review.

Detector landmarks, segmentation, and similarity retrieval may propose where
to look. They may not write final truth or bypass steps 1-9. A contact sheet may
help compare a collection, but it cannot replace per-sample evidence.

## Annotation decisions

- Include every currently visible semantic pixel and any directly continuous
  structural pixels defined by the task, such as eyelids for an eye study.
- Exclude adjacent brows, hair, background, cosmetics, headphones, clothing,
  and other look-alike parts unless the task explicitly studies their union.
- Record natural occlusion separately from truncation. If a side is naturally
  invisible, store `null` and the reason; do not fabricate it.
- "Complete" means all visible source pixels are enclosed. It does not mean the
  anatomy itself is unoccluded.

## Anti-symmetry hard gate

Each side needs its own evidence. Never mirror, horizontally align, or offset a
known eye, hand, ear, or attachment to invent the other side. Head tilt and
perspective may place paired parts at different heights and sizes. When a dark
line could be a brow, closed eye, wrinkle, hair, or accessory, first establish
the full structural sequence around it, such as `brow -> eye -> nose -> mouth`.
Unresolved ambiguity stays `needs-review` and blocks exercise generation.

## Exercise and review loop

1. Lock an approved, study-only source card and editable private master.
2. Remove one complete semantic unit without leaving answer pixels.
3. Issue one exercise only; do not expose the next answer or the whole batch.
4. Freeze the first attempt before revealing the reference or difference.
5. Score structure, relationship, and native-size readability; pixel equality
   is diagnostic, not the sole authority.
6. Ask an independent visual reviewer to cite the per-sample evidence.
7. Record the reusable rule, failure layer, and next unseen transfer. Do not
   record answer coordinates as a reusable lesson.

## Exit gate

Do not generate downstream exercises while any sample has unresolved semantic
boundaries, missing evidence, a false-symmetry inference, or a visible truncation.
Do not claim mastery until a no-reference original transfer passes the same
native-size and independent-review gates.
