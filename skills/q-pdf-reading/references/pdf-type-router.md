# PDF Type Router

Use this reference when a PDF does not clearly fit a single extraction path.
The goal is to avoid total failure by routing to the strongest available method
and keeping fallbacks.

## Lightweight Scan Signals

| Signal | Meaning | Preferred path |
|:---|:---|:---|
| High text chars/page, few images | Digital text PDF | Layout Markdown, then spot-check |
| Low text chars/page, many image pages | Scanned/image PDF | Render pages, OCR/layout if allowed |
| Text plus many images | Manual, slide export, tutorial | Layout Markdown plus page PNGs/images |
| Many drawings, little text | Schematic, CAD, diagram, waveform | Render pages first; text is secondary |
| Table hints or dense aligned text | Table/report/register map | Layout Markdown plus table-aware check |
| Sidecar `.md/.docx/.pptx/.html` exists | Source-native material likely better | Use sidecar as primary, PDF as evidence |

## Cross-Validation Rules

- Run at least two local text strategies when available.
- Prefer the strategy with high text volume, low encoding noise, heading
  preservation, and token overlap with other strategies.
- Keep every attempted strategy output under `strategies/`; do not delete failed
  or weaker outputs, because they help diagnose extraction gaps.
- For visual-first PDFs, a high text score is not enough. Require page PNGs or
  figure extraction before summarizing diagrams, screenshots, waveforms, board
  photos, schematics, or chart-heavy pages.
- If local strategies disagree strongly, mark the reading pack degraded and
  inspect rendered sample pages before using the content.
- If text density is low and RapidOCR is installed, run `--ocr-pages` and keep
  OCR output as either the primary text source or a fallback, depending on text
  extractor quality.
- Generate `confidence_report.md` after strategy comparison. Treat tokens
  supported by multiple sources as higher confidence; review domain-like tokens
  seen in only one source, especially part numbers, signal names, API names,
  register names, file paths, and URLs.
- For OCR, page-level average confidence is not enough. Review low-confidence
  lines and rerun weak pages at higher DPI or with preprocessing before relying
  on exact identifiers.

## OCR Quality Ladder

Use the cheapest step that resolves the uncertainty:

1. Render page PNGs at 144-200 DPI and run RapidOCR.
2. For weak pages, rerender at 216 or 300 DPI and rerun OCR only on those pages.
3. Use grayscale, threshold, or deskew preprocessing when scans are blurry,
   skewed, low contrast, or photographed.
4. If tables, forms, or layout are the real issue, escalate to Docling,
   Unstructured, PaddleOCR/PP-Structure, or a cloud layout API after
   data-sensitivity review.

## Escalation Options

Use these only after data-sensitivity review:

- Local install: PyMuPDF4LLM, Docling, Unstructured, pdfplumber, OCR tools.
- Cloud/layout APIs: Azure Document Intelligence, Google Document AI/Gemini,
  Adobe PDF Extract, or Mistral OCR.
