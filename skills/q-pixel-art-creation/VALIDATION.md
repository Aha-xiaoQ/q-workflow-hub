# Pixel Art Validation

This skill is a lab candidate. Historical private training artifacts and
maintainer review paths are not included in this distribution.

For each new artifact:

1. Run `scripts/validate_metadata.py` against the skill metadata.
2. Inspect `scripts/validate_pixel_art.py --help` with Pillow >=9.1 installed.
3. Check native dimensions and integer nearest-neighbor preview fidelity.
4. Exercise wrong-size negative cases and applicable semantic-mask checks.
5. Inspect native-size and enlarged gridded views, then obtain independent
   visual review before accepting or publishing.

Numerical validation is not evidence of visual quality. Record actual inputs,
commands, outcomes, limitations and reviewer decisions in the owning project.
