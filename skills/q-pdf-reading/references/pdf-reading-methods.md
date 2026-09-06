# PDF Reading Methods

Use this reference after triage to choose an extraction path. The goal is not
to find one universal PDF parser. The goal is to match the parser to the PDF
type and preserve enough evidence for review.

## Method Matrix

| PDF situation | Preferred path | Why |
|:---|:---|:---|
| Source-native file exists nearby (`.md`, `.docx`, `.pptx`, `.html`) | Use the source-native file as primary text; keep PDF as evidence | Usually preserves headings, lists, speaker notes, and images better than PDF extraction |
| Simple digital PDF with selectable text | Local text extraction, then page-marked Markdown | Fast, private, and usually sufficient |
| Multi-column paper, datasheet, or manual | Layout-aware Markdown/JSON extraction | Reading order and headings matter |
| Scanned manual or photo PDF | OCR/layout extraction plus rendered page QA | Text layer may be absent or misleading |
| Tables, register maps, BOMs, financial statements | Table-aware extraction to CSV/HTML/Markdown plus visual spot check | Plain text usually corrupts row/column structure |
| Schematics, diagrams, CAD, waveforms, slide screenshots | Render page images and inspect visually; extract text only as support | Meaning is spatial and image-based |
| Large PDF corpus for RAG/search | Layout-aware chunks with page anchors and table/figure references | Retrieval needs stable chunks and evidence anchors |

## Local-First Options

- `pymupdf4llm`: good default when available for local Markdown/JSON/text
  aimed at LLM/RAG workflows. Useful for multi-column text, tables, images, and
  page-aware extraction.
- `Docling`: strong candidate for local document conversion when layout
  analysis, table structure, OCR, and unified structured output matter.
- `Unstructured partition_pdf`: useful when element classification matters.
  `fast` is for simple digital PDFs; `hi_res` is for layout-sensitive PDFs;
  `ocr_only` is for image-based files.
- `pdfplumber`: useful for targeted table/text inspection, especially when a
  deterministic local table pass is enough.
- `pypdf` or `PyPDF2`: use only for simple metadata/page/text tasks or PDF
  manipulation. Do not rely on it for layout-heavy reading.
- `scripts/pdf_to_reading_pack.py`: preferred local command in this skill. It
  uses PyMuPDF4LLM when installed and writes `extracted_text.md`,
  `triage_report.md`, `source_freeze.json`, and `reading_notes.md`.
- `scripts/pdf_strategy_compare.py`: router command for unknown or risky PDFs.
  It lightweight-scans the file, classifies the PDF type, runs multiple local
  extractors, scores quality and cross-strategy overlap, and selects a primary
  `extracted_text.md` while keeping fallbacks.
- `scripts/pdf_extract_text.py`: last-resort standard-library fallback. It
  decompresses easy Flate streams, reads simple ToUnicode maps, and extracts
  `Tj/TJ` text operators. Use it to decide whether a digital PDF has usable
  text, not to certify full comprehension.
- `scripts/pdf_ocr_pages.py`: local OCR path using RapidOCR when installed.
  Use it for scanned/image PDFs or as a visual cross-check for screenshot-heavy
  manuals and slide exports.
- `scripts/pdf_confidence_fusion.py`: confidence report for reading packs. It
  compares source agreement, OCR confidence, low-confidence lines, and
  single-source domain tokens.

## Cloud or Model-Based Options

Use only after a data-sensitivity check and user approval for company or private
documents.

- Azure Document Intelligence Layout: useful for structured extraction of pages,
  paragraphs, lines, words, tables, figures, sections, and Markdown output.
- Google Document AI Layout Parser: useful for OCR plus Gemini-powered layout
  parsing, advanced table parsing, layout annotation, and layout-aware chunks.
- Gemini document understanding: useful when direct multimodal reasoning over
  PDF pages, charts, diagrams, and tables is more important than deterministic
  extraction artifacts.
- Adobe PDF Extract API: useful when PDF-native element structure, JSON output,
  table/figure renditions, and high-fidelity asset extraction matter.
- Mistral OCR: useful for OCR-to-Markdown style extraction from PDFs/images when
  external processing is allowed.

## Local OCR Choice

Default to RapidOCR for the local workflow when OCR is needed. It is
offline after installation, works through Python, uses ONNXRuntime, and defaults
to Chinese/English recognition. Use PaddleOCR PP-StructureV3 through
`scripts/pdf_ppstructure_table_extract.py` when scanned or image-only tables
need full cell-level HTML/XLSX output; it is a heavy optional backend that may
download model files and can need Windows runtime flags such as disabled MKLDNN.
Consider Tesseract only when a system-level OCR binary and language packs are
acceptable.

## Chunking Rules for LLM/RAG

1. Chunk by semantic boundaries first: headings, sections, procedures, tables,
   figures, appendices, and page ranges.
2. Keep page anchors inside every chunk: `source`, `page_start`, `page_end`,
   `heading`, and optional `figure/table ids`.
3. Do not split a procedure step list, register table, API description, or figure
   caption away from its context unless the chunk keeps a backlink.
4. Store tables separately when row/column fidelity matters, then insert a short
   table summary into the text chunk.
5. For PPT generation, make a `source_freeze.json` and `slide_evidence.md` before
   writing slide copy.

## Research Basis

This skill uses ideas from public documentation and papers only; it does not copy
third-party code or prompts. Useful sources reviewed include PyMuPDF4LLM,
Docling, Unstructured, Azure Document Intelligence, Google Document AI/Gemini,
Adobe PDF Extract API, and Mistral OCR documentation.
