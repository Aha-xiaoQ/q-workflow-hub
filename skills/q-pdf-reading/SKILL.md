---
name: q-pdf-reading
description: Triage, extract, verify, and read PDF documents with evidence-backed outputs. Use when Codex needs to understand PDFs, scanned manuals, slide-export PDFs, datasheets, schematics, papers, reports, or PDF source material before summarizing, generating PPTs, building RAG chunks, extracting tables/figures, or citing page-grounded facts.
---

# Q PDF Reading

Use this skill to read PDFs with evidence proportional to the task. Keep
page anchors, preserve figures/tables when they matter, and validate extraction
quality before trusting the text.

## Effort Routing

- Focused question or short readable PDF: inspect the relevant pages directly,
  verify text/layout and cite pages. A reading pack, competing extractors, and
  benchmark reports are not prerequisites for an accurate bounded answer.
- Complex, high-risk, batch, or reusable extraction: use the robust workflow
  below and the applicable parts of the validation checklist.
- Evaluating/promoting an extraction method: use strategy comparisons and
  closed-loop benchmarks. Do not turn ordinary document reading into a benchmark.

## Default Reading Path

1. Identify the source and relevant pages. Prefer a matching native `.md`,
   `.docx`, `.pptx` or `.html` for text after checking PDF page anchors.
2. Inspect requested pages, choosing text extraction for readable digital text
   and rendered pages for scans, figures, tables, schematics or layout risks.
   Verify uncertain OCR and consequential names/numbers against the page.
3. Answer with page or figure/table anchors. State unreadable content, partial
   coverage and extraction uncertainty; never guess from raw binary search.
4. Apply `references/validation-checklist.md` to the requested scope before
   handoff. A focused answer does not require a separate pack or report.

For complex, high-risk or reusable extraction, read
`workflows/extract-and-benchmark.md`. Its comparison, confidence and benchmark
steps are conditional on extraction risk or method/default evaluation; a
matching sidecar does not itself trigger a benchmark.

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
