# PDF Benchmark Manifest Schema

This is the stable input contract for `scripts/pdf_benchmark_runner.py`.

## Top-Level Fields

| Field | Required | Meaning |
|:---|:---:|:---|
| `version` | yes | Must be `0`. |
| `name` | recommended | Human-readable benchmark name. |
| `defaults` | no | Default runner options inherited by samples. |
| `samples` | yes | List of sample objects. |

## Defaults And Sample Options

Defaults and per-sample `options` support:

| Field | Default | Meaning |
|:---|:---|:---|
| `mode` | `robust` | Reading-pack mode. |
| `max_render_pages` | `30` | Maximum rendered pages. |
| `render_dpi` | `144` | Render DPI for page PNGs. |
| `max_table_pages` | `80` | Maximum pages scanned by table extraction. |
| `max_table_probe_pages` | `5` | Maximum rendered pages/images scanned by the ruled table-structure probe. |
| `ocr_pages` | `false` | Force OCR even when auto-routing would skip it. |
| `render_pages` | `false` | Force rendering in quick mode. |
| `table_structure_probe` | `false` | Force OpenCV ruled-table structure probing over rendered pages/images. |

## Sample Fields

| Field | Required | Meaning |
|:---|:---:|:---|
| `id` | recommended | Stable sample id used for output folders. |
| `pdf` | yes | PDF path; relative paths resolve from the manifest folder. |
| `class` | no | Human label for the sample class. |
| `modes` | no | Modes to run; defaults to `defaults.mode` or `robust`. |
| `options` | no | Per-sample overrides. |
| `expected` | no | Assertions checked after pack generation. |

## Expected Fields

| Field | Type | Meaning |
|:---|:---|:---|
| `pdf_type` | string or list | Expected router type. |
| `selected_strategy` | string or list | Expected selected text/OCR strategy. |
| `min_confidence_grade` | string | Minimum grade: `low`, `medium`, or `high`. |
| `min_confidence_score` | number | Minimum numeric confidence score. |
| `min_tables` | number | Minimum table count from `tables_manifest.json`. |
| `min_table_structure_regions` | number | Minimum candidate ruled-table regions from `tables/table_structure_probe.json`. This checks visual table structure evidence, not CSV extraction. |
| `min_table_structure_cells` | number | Minimum estimated ruled-grid cells from the table-structure probe. This is a rough grid-size gate, not final cell text extraction. |
| `check_table_count` | boolean | When true, compare extracted table count against `ground_truth.tables` even if `min_tables` is omitted. |
| `require_artifacts` | list | Paths required inside the generated pack. |
| `ground_truth` | object | Optional paths to `text`, `layout`, `tables`, or `ocr` ground-truth files. Relative paths resolve from the manifest folder. |
| `min_text_token_coverage` | number | Minimum token overlap between `ground_truth.text` and `extracted_text.md`; default is `0.35`. |

Use `pages` in `require_artifacts` to require at least one rendered page PNG.

## Adapter Script

`scripts/pdf_benchmark_adapter.py` creates manifests and expected files from
local folders or common benchmark annotation layouts:

```powershell
python <skill>\scripts\pdf_benchmark_adapter.py --kind local-folder --input <pdf-folder> --out <adapter-output>
python <skill>\scripts\pdf_benchmark_adapter.py --kind funsd --input <funsd-root> --out <adapter-output>
python <skill>\scripts\pdf_benchmark_adapter.py --kind ctdar --input <ctdar-root> --pdf-root <pdf-or-image-root> --out <adapter-output> --render-dpi 216
python <skill>\scripts\pdf_benchmark_adapter.py --kind generic-json --input <annotations.json> --pdf-root <pdf-or-image-root> --out <adapter-output>
```

Supported adapter kinds:

- `local-folder`: scans PDFs and creates low-bar smoke samples.
- `funsd`: reads FUNSD-style `annotations/*.json`, converts matching images to
  PDFs when Pillow is installed, and writes `expected_text.md` plus
  `expected_ocr.json`.
- `ctdar`: reads cTDaR-style XML and writes `expected_tables.json`.
  If the matched source is an image, the adapter requires rendered-page and
  confidence evidence but does not require local table-structure extraction.
  If the matched source is a PDF, it also requires `min_tables: 1`.
  Add `--require-table-structure-probe` when a ruled-table image sample should
  enable `table_structure_probe` and require at least one candidate visual
  table region. When XML cell counts are available, the adapter also sets a
  rough `min_table_structure_cells` gate at 50% of the expected cell count.
- `generic-json`: recursively extracts text/html/latex/transcription fields and
  table/figure/formula labels from JSON records, useful for OmniDocBench-like
  annotations or small custom subsets. When the JSON labels a scanned ruled
  table, add `--require-table-structure-probe` so the manifest checks
  visual table-structure evidence instead of requiring PDF-native table
  extraction.

Adapter CLI options `--max-render-pages`, `--render-dpi`, and
`--max-table-pages` control defaults written into the generated manifest.
For scanned table images, increasing render DPI may improve OCR slightly but can
create very large rendered pages; treat high-DPI warnings as a signal to use a
specialized table/OCR backend rather than blindly increasing DPI.
