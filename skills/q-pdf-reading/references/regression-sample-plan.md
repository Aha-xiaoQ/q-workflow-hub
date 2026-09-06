# PDF Regression Sample Plan

Use this plan when validating `q-pdf-reading` changes. Keep sample files local
unless they are explicitly public and sanitized.

## Sample Classes

| Class | What It Tests | Expected Pack Evidence |
|:---|:---|:---|
| Digital manual or datasheet | Text layer, headings, page count, figure references | `extracted_text.md`, `strategy_comparison.md`, `confidence_report.md` |
| Scanned or image-only document | OCR routing and low-confidence line reporting | `pages/`, `ocr/ocr_text.md`, `confidence_report.md` |
| Table-heavy report | Table hints, layout degradation, manual review notes | strategy scores plus table-review notes in `reading_notes.md` |
| Slide-export PDF | Mixed text and visuals, page screenshots | `pages/`, selected text, visual fallback warning when needed |
| Diagram or schematic PDF | Visual-first rule, drawing-heavy classification | rendered pages treated as primary evidence |

For public benchmark-backed testing, use `benchmark-datasets.md` to map each
dataset's ground truth format into text, layout, table, or OCR checks.

## Validation Matrix

Run each selected sample through:

```powershell
python <skill>\scripts\pdf_to_reading_pack.py <sample.pdf> --out <pack>\quick --mode quick
python <skill>\scripts\pdf_to_reading_pack.py <sample.pdf> --out <pack>\robust --mode robust
python <skill>\scripts\pdf_to_reading_pack.py <sample.pdf> --out <pack>\deep --mode deep
```

## Acceptance Notes

- Quick mode may be incomplete for visual-first PDFs, but it should finish and
  write a degraded pack.
- Robust mode should write `strategy_comparison.md` and `confidence_report.md`.
- Deep mode should write `deep_backend_report.md`; when no heavy backend is
  available, robust artifacts remain the handoff source.
- Record sample class, selected strategy, confidence grade, known misses, and
  next action before treating a parser change as validated.
