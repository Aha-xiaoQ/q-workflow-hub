---
name: q-pdf-reading
description: Triage, extract, verify, and read PDF documents with evidence-backed outputs. Use when Codex needs to understand PDFs, scanned manuals, slide-export PDFs, datasheets, schematics, papers, reports, or PDF source material before summarizing, generating PPTs, building RAG chunks, extracting tables/figures, or citing page-grounded facts.
---

# Q PDF Reading

Use this skill to turn PDFs into a reliable reading pack before asking an LLM
to summarize or reuse the content. The default posture is evidence-first: keep
page anchors, preserve figures/tables when they matter, and validate extraction
quality before trusting the text.

## Workflow

1. **Triage first.** Run `scripts/pdf_triage.py` for a quick inventory or
   `scripts/pdf_strategy_compare.py` when the PDF type is unknown. The strategy
   comparison does a lightweight scan before full parsing.
2. **Choose the lane by PDF type.**
   - Digital text PDF: extract text with page markers, then inspect layout risk.
   - Scanned or image-heavy PDF: use OCR/layout extraction before summarizing.
   - Tables/forms: use table-aware extraction and preserve CSV/HTML/Markdown.
   - Schematics/CAD/diagrams: render page images and review visually; text alone
     is insufficient.
   - Slide-export PDFs: prefer original PPTX if available; otherwise extract
     text plus page screenshots.
3. **Compare viable local strategies.** When more than one extractor is
   available, compare PyMuPDF4LLM, PyMuPDF text extraction, and the standard
   library fallback. Keep strategy outputs under `strategies/`, write
   `strategy_comparison.md`, and copy the selected output to
   `extracted_text.md`.
4. **Create a reading pack.** Store outputs in a dedicated folder:
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
   pages. Use `scripts/pdf_confidence_fusion.py` to produce
   `confidence_report.md` with source agreement, OCR low-confidence lines, and
   single-source domain tokens.
   For repeated validation, use `scripts/pdf_benchmark_runner.py` with a
   manifest that declares sample PDFs, expected PDF type, minimum confidence,
   required artifacts, and table/OCR/layout expectations.
   Use `scripts/pdf_benchmark_adapter.py` to convert local folders, FUNSD-style
   folders, cTDaR XML, or generic JSON annotations into those manifests.
6. **Read with citations.** Summaries, PPT content, and technical claims should
   cite page numbers or figure/table anchors. If evidence is missing, say so and
   inspect the rendered page or source file instead of guessing.

When a same-content Markdown, DOCX, or other sidecar exists, treat it as a
gold/reference source for closed-loop testing. For Markdown sidecars, run
`scripts/sidecar_gold_test.py` to score source discovery, lane selection, asset
discovery, and content-map coverage. Run `scripts/reading_quality_test.py` to
score PDF-only extracted text against the reference after extraction.

## Tool Choice

Prefer local source-native files over PDF extraction when available. If a
neighboring `.md`, `.docx`, `.pptx`, `.html`, source repository, or figure folder
matches the PDF, use that as the primary text source and keep the PDF as original
evidence.

Use `references/pdf-reading-methods.md` when choosing among local libraries,
cloud OCR/layout APIs, table extraction, figure extraction, or RAG chunking.

Use `references/pdf-type-router.md` when the PDF type is unclear or when text,
tables, diagrams, and scanned pages may require different paths.

Use `references/prior-art-study.md` when improving the skill, preparing a
public/promotion version, or deciding whether to add heavier backends such as
Docling, Marker, MinerU, Unstructured, or cloud layout parsers.

Use `references/regression-sample-plan.md` when preparing closed-loop regression
coverage across digital text, scanned, table-heavy, slide-export, and
diagram/schematic PDFs.

Use `references/benchmark-datasets.md` when selecting public benchmark datasets
or converting their ground truth into local regression checks.

Use `references/benchmark-manifest-schema.md` when writing or reviewing a
`pdf_benchmark_runner.py` manifest.

Use `references/validation-checklist.md` before handing off a PDF-derived answer,
deck, report, or dataset.

## Safety Rules

- Do not treat raw binary search inside a PDF as reading the document.
- Do not summarize a scanned or diagram-heavy PDF from text extraction alone.
- Do not discard page numbers when the output may be reviewed or cited later.
- Do not install or call cloud OCR/layout tools without user approval and an
  explicit data-sensitivity check.
- Prefer local OCR for company/private PDFs. RapidOCR is the default local OCR
  option when installed; cloud OCR remains approval-gated.
- For confidential or company material, default to local extraction and record
  any missing capability as a blocker or degraded warning.

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
