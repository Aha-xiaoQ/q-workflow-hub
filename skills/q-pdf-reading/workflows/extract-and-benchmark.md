# Extract and Benchmark PDFs

Use for reusable reading packs, complex extraction, extraction anomalies, or method evaluation. Select only steps justified by the requested output and PDF type. The entry owns the direct-reading lane.

## Workflow

1. **Triage the relevant scope.** For a simple known PDF, inspect its page count
   and requested pages directly. Run `scripts/pdf_triage.py` for an inventory or
   `scripts/pdf_strategy_compare.py` when the PDF type is unknown. The strategy
   comparison does a lightweight scan before full parsing.
2. **Choose the lane by PDF type.**
   - Digital text PDF: extract text with page markers, then inspect layout risk.
   - Scanned or image-heavy PDF: inspect page images; use OCR/layout extraction
     when it improves coverage or reusable text is needed. Verify uncertain OCR.
   - Tables/forms: use table-aware extraction and preserve CSV/HTML/Markdown.
   - Schematics/CAD/diagrams: render page images and review visually; text alone
     is insufficient.
   - Slide-export PDFs: prefer original PPTX if available; otherwise extract
     text plus page screenshots.
3. **Compare strategies when evidence requires it.** For extraction anomalies,
   high-risk disagreement, or method evaluation, compare viable extractors such
   as PyMuPDF4LLM, PyMuPDF text extraction, and the standard
   library fallback. Keep strategy outputs under `strategies/`, write
   `strategy_comparison.md`, and copy the selected output to
   `extracted_text.md`.
4. **Create a reading pack when reusable artifacts are needed.** Store applicable outputs in a dedicated folder:
   `source_freeze.json`, `triage_report.md`, `extracted_text.md`,
   `page_inventory.csv`, `figures/`, `tables/`, and `reading_notes.md` as
   applicable.
   Run `scripts/pdf_to_reading_pack.py` to use the best local extractor
   available. Use `--mode quick` for fast local text extraction, `--mode robust`
   for strategy comparison plus page rendering and OCR only when routing says
   the PDF is visual/image-first, and `--mode deep` to probe optional heavy
   backends before falling back to robust artifacts. The quick path prefers
   PyMuPDF4LLM when installed and falls back to `scripts/pdf_extract_text.py`
   for a provisional standard-library extraction.
   For PDFs with diagrams, screenshots, tables, or figures, add
   `--render-pages` so the reading pack keeps page PNGs and embedded images as
   visual evidence.
   For scanned/image PDFs, add `--ocr-pages` to run local RapidOCR over rendered
   pages and keep `ocr/ocr_text.md` as an OCR fallback strategy.
   For scanned table images, add `--table-structure-probe` and use the generated
   `tables/table_structure_probe_report.md` as evidence that ruled table
   regions exist; this probe does not replace full table cell extraction.
5. **Validate before using.** Check page count, encoding, sample pages, heading
   order, table/figure references, and whether extracted text matches rendered
   pages. For OCR-heavy/high-risk reusable extraction, use `scripts/pdf_confidence_fusion.py` to produce
   `confidence_report.md` with source agreement, OCR low-confidence lines, and
   single-source domain tokens.
   For extraction-method evaluation, use `scripts/pdf_benchmark_runner.py` with a
   manifest that declares sample PDFs, expected PDF type, minimum confidence,
   required artifacts, and table/OCR/layout expectations.
   Use `scripts/pdf_benchmark_adapter.py` to convert local folders, FUNSD-style
   folders, cTDaR XML, or generic JSON annotations into those manifests.
6. **Read with citations.** Summaries, PPT content, and technical claims should
   cite page numbers or figure/table anchors. If evidence is missing, say so and
   inspect the rendered page or source file instead of guessing.

When evaluating extraction quality, a verified same-content Markdown, DOCX, or
other sidecar can serve as a reference for closed-loop testing. For Markdown sidecars, run
`scripts/sidecar_gold_test.py` to score source discovery, lane selection, asset
discovery, and content-map coverage. Run `scripts/reading_quality_test.py` to
score PDF-only extracted text against the reference after extraction. Ordinary
reading may use the matching sidecar after checking relevant PDF page anchors;
the existence of a sidecar does not itself require benchmark runs.

## Quick Commands

```powershell
python <skill>\scripts\pdf_triage.py <pdf-or-folder> --out <reading-pack-folder>
python <skill>\scripts\pdf_strategy_compare.py <pdf> --out <reading-pack-folder> --render-pages --ocr-pages
python <skill>\scripts\pdf_to_reading_pack.py <pdf> --out <reading-pack-folder> --mode quick
python <skill>\scripts\pdf_to_reading_pack.py <pdf> --out <reading-pack-folder> --mode robust
python <skill>\scripts\pdf_to_reading_pack.py <pdf> --out <reading-pack-folder> --mode deep
python <skill>\scripts\pdf_to_reading_pack.py <pdf> --out <reading-pack-folder> --mode robust --table-structure-probe
python <skill>\scripts\pdf_ocr_pages.py <pdf-or-pages-folder> --out <reading-pack-folder>\ocr
python <skill>\scripts\pdf_table_structure_probe.py <pages-folder> --out <reading-pack-folder>\tables
python <skill>\scripts\pdf_confidence_fusion.py <reading-pack-folder>
python <skill>\scripts\pdf_extract_text.py <pdf> --out <reading-pack-folder>
python <skill>\scripts\sidecar_gold_test.py <pdf> --out <reading-pack-folder>
python <skill>\scripts\reading_quality_test.py <reading-pack-folder>\extracted_text.md <reference.md> --out <reading-pack-folder>
python <skill>\scripts\pdf_benchmark_adapter.py --kind local-folder --input <pdf-folder> --out <adapter-output-folder>
python <skill>\scripts\pdf_benchmark_runner.py <manifest.json> --out <benchmark-output-folder>
```
