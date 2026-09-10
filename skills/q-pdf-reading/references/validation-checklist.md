# PDF Reading Validation Checklist

Use this checklist before relying on a PDF-derived summary, PPT, dataset, or RAG
index. Apply checks to the requested scope: a bounded answer needs a verified
source, relevant page inspection, and anchors; durable packs and method
benchmarks need the additional recorded artifacts below. Do not create empty
reports merely to satisfy this checklist.

## Required Checks

- For a durable reading pack/dataset, source freeze records path, file size,
  hash, modified time, and extraction timestamp. For a focused answer, identify
  the source and pages without requiring a separate freeze file.
- Page count is known or explicitly marked as an estimate.
- Extraction lane is recorded: digital text, OCR, layout-aware, table-aware,
  visual/manual, or source-native sidecar.
- Unknown or high-risk PDFs have `strategy_comparison.md` with at least one
  primary strategy and one fallback attempt, or a recorded reason why comparison
  was unavailable.
- For high-risk or OCR-heavy reusable extraction, `confidence_report.md` exists
  or direct verification of the relevant claims and its limits are recorded.
  It identifies selected strategy confidence, source agreement, low-confidence
  OCR lines, and single-source domain tokens.
- For broad extraction, spot-check at least three available representative pages
  (first content, dense middle, table/figure); if fewer than three exist, inspect
  all available pages. A focused question requires its relevant pages, not an
  unrelated three-page quota. Increase coverage for consequential claims.
- Extracted text has no obvious mojibake, repeated headers overwhelming content,
  or broken reading order on multi-column pages.
- Tables used in the answer are preserved as table files or reviewed visually.
- Figures, block diagrams, screenshots, schematics, or charts used in the answer
  are linked to page numbers and image files when possible.
- Inspect every visually important page used in the answer, using rendered
  images or a supported native viewer; durable packs retain page images.
- For scanned/image PDFs, verify readable page images directly or use verified
  OCR. Missing OCR alone is not a blocker when the required content can be read
  reliably; unreadable required content remains blocking/degraded.
- Claims in final outputs include page or figure/table anchors when the user may
  review, share, or make decisions from them.

## Warning Levels

- **Blocking:** required content cannot be read by any available authorized
  method, inaccessible encrypted PDF, missing source, or visually important
  diagrams/schematics used without visual inspection.
- **Degraded:** text extracted but reading order/table structure is uncertain,
  or only a subset of pages was processed.
- **Informational:** source-native sidecar exists, page count is estimated, or
  figures were not needed for the requested output.

## Handoff Notes

Record unresolved warnings in `reading_notes.md` or the project handoff. Do not
hide extraction weakness inside a polished summary.
