# PDF Benchmark Datasets

Use this reference when choosing public validation data for `q-pdf-reading`.
Do not copy dataset files into this skill. Keep downloads and derived packs in a
separate local report or project folder, and follow each dataset license.

## Recommended Sources

| Dataset | Best Use | Ground Truth Shape | Fit For This Skill |
|:---|:---|:---|:---|
| OmniDocBench | End-to-end document parsing across diverse PDF pages | JSON annotations for text, formulas, tables, layout, reading order | Best broad benchmark for parser routing and confidence reports |
| SCORE-Bench | Real-world enterprise-style document parsing | Expert annotations and evaluation data | Best stress set for messy production PDFs |
| DocLayNet | Layout segmentation | COCO-style bounding boxes across layout classes | Good for page-type and visual evidence routing |
| PubTables-1M | Table detection and structure recognition | Table boxes, structure, headers, and locations | Good for table extraction/report quality |
| FUNSD | Noisy scanned forms | OCR/entity/relation annotations | Good for OCR fallback and form-reading limitations |
| ICDAR cTDaR | Table detection and recognition | XML table region and structure ground truth | Good for table-specific regression |

## How To Adapt Them

Different datasets use different ground truth formats. Convert them into a
small skill-local evaluation contract rather than hard-coding each benchmark:

- `expected_text.md` for content coverage and reading-order checks.
- `expected_layout.json` for page regions, labels, and visual-first routing.
- `expected_tables.json` or `expected_tables.html` for table structure checks.
- `expected_ocr.json` for scanned forms or image-only pages.
- `sample_manifest.json` for source, license, class, and expected checks.

## Manifest Runner

Use `scripts/pdf_benchmark_runner.py` to run local samples or small public
benchmark subsets. The runner calls `pdf_to_reading_pack.py`, then checks
observed routing, selected strategy, confidence, table count, and required
artifacts.

Use `scripts/pdf_benchmark_adapter.py` first when the dataset provides
annotation JSON/XML instead of a ready-to-run manifest. It supports local PDF
folders, FUNSD-style folders, cTDaR XML, and generic JSON annotations. For
scanned ruled-table JSON samples, pass `--require-table-structure-probe` to
require visual table-structure evidence rather than PDF-native `min_tables`
extraction.

Minimal manifest:

```json
{
  "version": 0,
  "name": "pdf-benchmark-subset",
  "defaults": {
    "mode": "robust",
    "max_render_pages": 3,
    "max_table_pages": 30
  },
  "samples": [
    {
      "id": "sample-001",
      "pdf": "samples/sample-001.pdf",
      "class": "table-heavy-report",
      "modes": ["robust"],
      "expected": {
        "pdf_type": "table-or-technical-report",
        "min_confidence_grade": "medium",
        "min_tables": 1,
        "require_artifacts": [
          "strategy_comparison.md",
          "confidence_report.md",
          "reading_notes.md",
          "tables/table_extraction_report.md"
        ]
      }
    }
  ]
}
```

Supported expectation keys:

- `pdf_type`: string or list of allowed router types.
- `selected_strategy`: string or list of allowed selected strategies.
- `min_confidence_grade`: `low`, `medium`, or `high`.
- `min_confidence_score`: numeric minimum confidence score.
- `min_tables`: minimum extracted table count.
- `min_table_structure_regions`: minimum candidate ruled-table regions from
  rendered-page visual probing; this is evidence of visual table structure, not
  full CSV/cell extraction.
- `min_table_structure_cells`: minimum estimated ruled-grid cells from the
  table-structure probe; use as a rough scale check for scanned table images.
- `require_artifacts`: paths expected inside the generated pack; use `pages`
  to require at least one rendered page PNG.

## Practical Validation Ladder

1. Start with 5-10 local smoke samples to catch route and artifact bugs quickly.
2. Add a small public benchmark subset for each weak area: document parsing,
   layout, OCR/forms, and tables.
3. Score each sample at the level the ground truth supports. Do not force every
   benchmark into a single Markdown comparison.
4. Record failures as parser/routing defects, confidence-report defects, or
   evidence-contract defects.
5. Add backend-specific wrappers only when a benchmark failure proves the local
   robust path is insufficient.

## Current Evidence

The first real public cTDaR sample (`cTDaR_s001`) validates the benchmark
adapter chain and also exposes a limitation. The image+XML sample adapts into a
manifest and passes the evidence-level runner checks: rendered pages,
confidence report, reading notes, and table ground truth are present. However,
the local robust path classifies it as `scanned-or-image-only`, selects
`rapidocr_pages`, and reports low confidence. Raising render DPI from 144 to 216
improved the confidence score only slightly, from 16/100 to 19/100, and produced
a large-image warning. This means scanned table structure recovery should be a
separate backend upgrade path, not a PyMuPDF table-extraction expectation.

The intermediate local gate is `pdf_table_structure_probe.py`: it scans
rendered pages with OpenCV for horizontal/vertical ruling lines, intersections,
candidate table regions, and rough Hough-line grid size. Enable it explicitly with
`--table-structure-probe` or adapter `table_structure_probe` options when a
scanned-table sample should prove visual table-structure evidence before adding
a heavier backend. Do not treat it as final cell reconstruction; form boxes can
also create line-structure signals.

## License And Safety

- Check dataset license before redistribution or publishing derived artifacts.
- Keep company/private PDFs out of public benchmark packs.
- Prefer sample manifests and reproduction commands over vendoring large
  datasets into the skill repository.
