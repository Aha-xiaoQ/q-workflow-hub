# PDF Parsing Skill Prior-Art Study

Use this reference when improving `q-pdf-reading` or preparing a public/promotion
version. It records mechanisms learned from public skills and document parsing
toolchains. It uses ideas and patterns only; do not copy third-party code,
prompts, schemas, text, or assets unless license compatibility and attribution
are explicitly handled.

## Learning Question

How should a PDF reading skill become robust across digital PDFs, scanned PDFs,
manuals, slide exports, tables, forms, diagrams, and RAG inputs without
pretending that one parser can handle every case?

## Source Roles

| Source family | Role | Useful mechanism | Local decision |
|:---|:---|:---|:---|
| Official/general PDF skills | Boundary source | Broad PDF manipulation trigger and file-operation coverage | Keep `q-pdf-reading` narrower: reading, evidence, OCR, parsing quality |
| Community pdf-extract skills | Workflow reference | Detect machine-readable text first, OCR only when needed, assert counts | Promote detect-then-OCR and page-count validation |
| PDF-to-Markdown skills | Implementation pattern | Digital-first Markdown output, heading preservation, tests around hierarchy | Keep PyMuPDF4LLM as fast local text path |
| MinerU/Marker/Docling/Unstructured | Toolchain reference | Complex layout, tables, formulas, image extraction, OCR, structured JSON/Markdown | Add optional high-accuracy backends rather than making them required |
| LlamaParse/cloud parsers | Boundary/upgrade path | Production layout-aware parsing, visual citations, charts/tables/handwriting | Keep approval-gated for sensitive data |
| Multi-tool Markdown converters | Quality strategy | Quick mode vs heavy mode, parallel extraction, validation reports, selective reprocessing | Add explicit modes and confidence reports |

## Mechanisms To Keep

1. **Complexity router before extraction.** Lightweight scan should classify the
   PDF before choosing tools: digital text, scanned/image, illustrated manual,
   table/report, form, diagram/schematic, or slide export.
2. **Mode ladder.** Support at least three modes:
   - `quick`: fast local text extraction, no OCR unless needed;
   - `robust`: strategy comparison, page rendering, OCR fallback;
   - `deep`: high-accuracy parser/OCR/layout backend when installed or approved.
3. **Evidence pack contract.** Always produce rebuildable artifacts:
   `source_freeze.json`, `triage_report.md`, `strategy_comparison.md`,
   `extracted_text.md`, `pages/`, `figures/`, `ocr/`, and
   `confidence_report.md` when applicable.
4. **Cross-source confidence.** Treat agreement among PyMuPDF4LLM, PyMuPDF text,
   OCR, and rendered pages as confidence evidence. Single-source identifiers are
   not automatically wrong, but they need review.
5. **Visual-first degradation rule.** For diagrams, schematics, screenshots, and
   image-heavy pages, text extraction alone is never sufficient.
6. **Selective reprocessing.** Do not rerun the heaviest OCR/parser over the
   whole PDF by default. Reprocess weak pages or low-confidence lines first.
7. **Promotion-ready UX.** A public-facing skill should explain output folders,
   quality grades, known limitations, and when cloud parsing requires approval.

## Optional Backends To Evaluate

| Backend | Best fit | Caution |
|:---|:---|:---|
| PyMuPDF4LLM | Fast local Markdown for digital PDFs and technical manuals | Not enough for scanned/image-only PDFs |
| RapidOCR | Local OCR fallback for Chinese/English screenshots and scans | OCR line confidence still needs review |
| Docling | Structured local conversion, tables, layout, OCR, RAG integrations | Heavier install/runtime than PyMuPDF path |
| Marker | Markdown/JSON/chunks/HTML, tables/forms/equations/images | Evaluate install size and hardware needs |
| MinerU | High-accuracy parsing with hybrid/VLM+OCR options | License/deployment choice must be checked before public bundling |
| Unstructured | Strategy-based partitioning and table extraction | `hi_res` can be slower and dependency-heavy |
| LlamaParse/cloud APIs | Complex production parsing, visual citations, handwriting/charts | Data sensitivity, cost, and network approval |

## Promotion Bar

Before calling `q-pdf-reading` promotion-ready:

- Test at least five PDF classes: digital manual, scanned document, table-heavy
  report, slide-export PDF, and diagram/schematic PDF.
- Record quality reports for each class with selected strategy, fallback path,
  low-confidence items, and handoff guidance.
- Keep all third-party dependencies optional or documented. Do not require cloud
  parsing for normal company/private documents.
- Provide a small sample command set and a stable output folder contract.
- Add license notes for any copied code or vendored asset. Idea-only learning
  does not require vendored notices, but record sources in the study log.

## Current Local Status

- Implemented: triage, PDF type routing, PyMuPDF4LLM, PyMuPDF text fallback,
  standard-library fallback, RapidOCR OCR, page/image extraction, strategy
  comparison, reading-quality test, confidence fusion, and
  `--mode quick|robust|deep` in the reading-pack entry point.
- Needs more evidence: scanned-only PDF, table-heavy PDF, schematic/diagram PDF,
  and a hard slide-export PDF with low text layer.
- Candidate next patch: add backend-specific wrappers only after a regression
  sample proves the local robust pack is insufficient and license/deployment
  checks are complete.
