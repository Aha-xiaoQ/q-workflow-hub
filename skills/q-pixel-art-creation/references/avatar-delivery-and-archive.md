# Pixel Avatar Delivery And Archive

Use this reference after a pixel avatar has passed visual, structural, and user
acceptance. It packages one approved result for multiple downstream consumers
without confusing a larger derivative with the native pixel authority.

## Failure mode

One file cannot optimally serve all uses. A native pixel master is ideal for
editing and verification, a platform may recompress a profile upload, a website
benefits from a compact lossless runtime image, and a reviewer may need a very
large image with an almost invisible pixel grid. If these roles are not named,
later work may edit the wrong derivative, upload a review grid as a profile
image, or call a nearest-neighbour enlargement a higher-resolution source.

## Authority hierarchy

1. Keep one native indexed PNG as the pixel authority.
2. Keep an RGB PNG only when broad tooling needs it; it must be pixel-equivalent
   to the indexed authority.
3. Accept an SVG as an editable archive only when it uses integer-grid geometry
   and round-trips to the authority pixel for pixel.
4. Treat every larger PNG, lossless WebP, circle crop, or grid preview as a
   derivative with a named consumer.
5. Never reconstruct or revise the authority from a derivative.

## Required delivery routes

| Consumer | Default asset | Gate |
|---|---|---|
| Pixel authority and future edits | native indexed PNG | fixed dimensions, finite palette, no partial alpha, recorded SHA-256 |
| Broad raster compatibility | native RGB PNG | decoded pixels exact to indexed authority |
| Profile service that may recompress | 2x or another justified integer-nearest PNG | exact integer nearest-neighbour derivation; circle/small-size review |
| Website runtime | native-size lossless WebP, with PNG fallback | decoded RGB exact to authority; browser render check at real CSS size |
| Lossless detail viewer or pixel inspection | large integer-nearest image with a subtle one-device-pixel grid | grid is invisible or unobtrusive at normal view, readable only after zoom; cell centers and all off-grid pixels remain exact |
| Editable archive | exact integer-grid SVG | no embedded raster, fractional geometry, transform, smoothing, or partial opacity; exact round-trip |
| Crop verification | circle or platform-shape preview | review-only unless the consumer explicitly requires a pre-cropped image |

The exact native size and upload multiplier are project decisions. A 2x upload
is a strong default when it preserves the native cells exactly and gives the
downstream platform enough resampling headroom. A larger export does not add
native detail.

## Packaging procedure

1. Freeze the accepted native authority and record its hash.
2. Generate every derivative directly from the authority using deterministic
   integer nearest-neighbour or lossless encoding.
3. Put files into explicit `masters`, `delivery`, and `review` groups.
4. Write a human README that answers "which file should I use?" before it
   explains the process.
5. Write a machine manifest with version, status, dimensions, role, derivation,
   source path, and SHA-256 for every archived asset.
6. Record current integration targets and whether integration is complete or
   intentionally deferred.
7. Validate file hashes, dimensions, decode equality, SVG round-trip, and all
   relative links before handoff.
8. Keep the accepted archive immutable. Any visual edit opens a new versioned
   task and produces a new archive.

## Usage decision

- If the interface supports lossless, zoomable artwork viewing and the user
  wants pixel inspection, use the subtle hidden-grid review asset.
- If the destination is an avatar service that will compress or crop the
  upload, use the integer-upscaled PNG prepared for that service.
- If the destination is a controlled website with a small rendered avatar,
  use the native-size lossless WebP and retain a PNG fallback.
- If the next action is editing, verification, or regeneration, use the native
  indexed PNG or the exact round-trip SVG, never the upload derivative.

## Hard gate

- **Trigger:** final, accepted pixel-avatar packaging or downstream integration.
- **Must:** name one pixel authority; name every derivative's consumer and
  derivation; verify lossless equality or exact integer-nearest scaling; write
  a hash manifest and crop/small-use review.
- **Blocks:** final archive, website integration, upload recommendation, or
  claims that a larger export is a higher-detail source while roles or equality
  remain unverified.
- **Check:** decode and compare raster pixels, validate dimensions and hashes,
  round-trip SVG when present, and inspect the actual small/circle use.
- **Repair:** return to the frozen native authority and regenerate only the
  failed derivative; do not patch a downstream export.
- **Waiver:** the user may waive a nonessential derivative, but not an
  unverified or missing native authority.
- **Scope:** approved pixel avatars and closely related square identity assets;
  it does not define delivery formats for animation atlases, tilemaps, or
  photographic artwork.

## Anti-patterns

- Calling a 4x or 8x nearest-neighbour export a new native master.
- Using a grid-review image as a small compressed avatar by accident.
- Choosing SVG for a platform merely because it is vector, without proving the
  platform's rasterization preserves the grid.
- Letting a website build pipeline silently convert the lossless asset to a
  lossy JPEG.
- Overwriting an accepted archive when a later integration needs a different
  filename or crop.
