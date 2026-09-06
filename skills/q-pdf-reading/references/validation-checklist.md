# PDF Reading Validation Checklist

Use this checklist before relying on a PDF-derived summary, PPT, dataset, or RAG
index.

## Required Checks

- Source freeze exists with path, file size, hash, modified time, and extraction
  timestamp.
- Page count is known or explicitly marked as an estimate.
- Extraction lane is recorded: digital text, OCR, layout-aware, table-aware,
  visual/manual, or source-native sidecar.
- Unknown or high-risk PDFs have `strategy_comparison.md` with at least one
  primary strategy and one fallback attempt, or a recorded reason why comparison
  was unavailable.
- `confidence_report.md` exists for high-risk, OCR-heavy, or user-facing output.
  It identifies selected strategy confidence, source agreement, low-confidence
  OCR lines, and single-source domain tokens.
- At least three representative pages are spot-checked against rendered pages:
  first content page, one dense middle page, and one table/figure-heavy page.
- Extracted text has no obvious mojibake, repeated headers overwhelming content,
  or broken reading order on multi-column pages.
- Tables used in the answer are preserved as table files or reviewed visually.
- Figures, block diagrams, screenshots, schematics, or charts used in the answer
  are linked to page numbers and image files when possible.
- For only-PDF inputs, page PNGs exist for every visually important page, or the
  missing render step is recorded as a degraded warning.
- For scanned/image PDFs, OCR output exists (`ocr/ocr_text.md`) or the missing
  OCR capability is recorded as blocking/degraded.
- Claims in final outputs include page or figure/table anchors when the user may
  review, share, or make decisions from them.

## Warning Levels

- **Blocking:** no readable text, no OCR/layout tool, encrypted PDF, missing
  source file, or content is mostly diagrams/schematics that were not rendered.
- **Degraded:** text extracted but reading order/table structure is uncertain,
  or only a subset of pages was processed.
- **Informational:** source-native sidecar exists, page count is estimated, or
  figures were not needed for the requested output.

## Handoff Notes

Record unresolved warnings in `reading_notes.md` or the project handoff. Do not
hide extraction weakness inside a polished summary.
