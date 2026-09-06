#!/usr/bin/env python3
"""Create a PDF reading pack with the best local extractor available."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pdf_extract_text  # noqa: E402
import pdf_triage  # noqa: E402

DEEP_BACKENDS = [
    {
        "name": "docling",
        "module": "docling",
        "best_fit": "structured local conversion, tables, layout, OCR, RAG-ready exports",
        "status_note": "Optional heavy backend; not installed by this script.",
    },
    {
        "name": "marker",
        "module": "marker",
        "best_fit": "Markdown/JSON/HTML conversion for tables, forms, equations, and figures",
        "status_note": "Optional heavy backend; evaluate install size and hardware needs before enabling.",
    },
    {
        "name": "mineru",
        "module": "magic_pdf",
        "best_fit": "high-accuracy parsing with OCR/VLM-style pipelines",
        "status_note": "Optional heavy backend; check license and deployment policy before public use.",
    },
    {
        "name": "unstructured",
        "module": "unstructured",
        "best_fit": "strategy-based partitioning and table extraction",
        "status_note": "Optional heavy backend; hi_res paths can be dependency-heavy.",
    },
]


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def export_visuals_with_pymupdf(pdf: Path, out_dir: Path, max_pages: int, dpi: int) -> dict[str, Any]:
    import pymupdf  # type: ignore

    doc = pymupdf.open(str(pdf))
    pages_dir = out_dir / "pages"
    figures_dir = out_dir / "figures"
    pages_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)

    rendered_pages = 0
    extracted_images = 0
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    for page_index in range(min(doc.page_count, max_pages)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(str(pages_dir / f"page_{page_index + 1:03d}.png"))
        rendered_pages += 1

        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = image_info[0]
            try:
                image = doc.extract_image(xref)
            except Exception:
                continue
            ext = image.get("ext", "bin")
            image_bytes = image.get("image")
            if not image_bytes:
                continue
            image_path = figures_dir / f"page_{page_index + 1:03d}_image_{image_index:02d}.{ext}"
            image_path.write_bytes(image_bytes)
            extracted_images += 1
    total_pages = doc.page_count
    doc.close()
    return {
        "rendered_pages": rendered_pages,
        "total_pages": total_pages,
        "render_dpi": dpi,
        "extracted_images": extracted_images,
        "pages_dir": str(pages_dir.resolve()),
        "figures_dir": str(figures_dir.resolve()),
        "visual_warning": "Page rendering was capped; increase --max-render-pages for full visual coverage."
        if rendered_pages < total_pages
        else "",
    }


def export_tables_with_pymupdf(pdf: Path, out_dir: Path, max_pages: int | None = None) -> dict[str, Any]:
    import pymupdf  # type: ignore

    tables_dir = out_dir / "tables"
    tables_dir.mkdir(exist_ok=True)
    records = []
    errors = []
    doc = pymupdf.open(str(pdf))
    page_limit = doc.page_count if max_pages is None else min(doc.page_count, max_pages)
    for page_index in range(page_limit):
        page = doc.load_page(page_index)
        try:
            finder = page.find_tables()
        except Exception as exc:
            errors.append({"page": page_index + 1, "error": str(exc)})
            continue
        for table_index, table in enumerate(getattr(finder, "tables", []), start=1):
            csv_path = tables_dir / f"page_{page_index + 1:03d}_table_{table_index:02d}.csv"
            try:
                rows = table.extract()
                with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(rows)
                records.append(
                    {
                        "page": page_index + 1,
                        "table": table_index,
                        "rows": len(rows),
                        "columns": max((len(row) for row in rows), default=0),
                        "bbox": list(getattr(table, "bbox", [])),
                        "csv": str(csv_path.resolve()),
                    }
                )
            except Exception as exc:
                errors.append({"page": page_index + 1, "table": table_index, "error": str(exc)})
    total_pages = doc.page_count
    doc.close()
    payload = {
        "engine": "pymupdf.find_tables",
        "pages_scanned": page_limit,
        "total_pages": total_pages,
        "tables_found": len(records),
        "records": records,
        "errors": errors,
        "warning": "No tables were extracted; inspect rendered pages when table hints or dense columns are present."
        if not records
        else "",
    }
    (tables_dir / "tables_manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    lines = [
        "# PDF Table Extraction Report",
        "",
        f"- Engine: `{payload['engine']}`",
        f"- Pages scanned: {page_limit}/{total_pages}",
        f"- Tables found: {len(records)}",
    ]
    if records:
        lines.extend(["", "## Extracted Tables", ""])
        for record in records:
            lines.append(
                f"- Page {record['page']} table {record['table']}: "
                f"{record['rows']} rows x {record['columns']} columns -> `{Path(record['csv']).name}`"
            )
    if errors:
        lines.extend(["", "## Errors", ""])
        for error in errors[:20]:
            lines.append(f"- Page {error.get('page')}: {error.get('error')}")
    if payload["warning"]:
        lines.extend(["", "## Warning", "", f"- {payload['warning']}"])
    (tables_dir / "table_extraction_report.md").write_text("\n".join(lines), encoding="utf-8-sig")
    return payload


def extract_with_pymupdf4llm(pdf: Path, out_dir: Path) -> dict[str, Any]:
    import pymupdf  # type: ignore
    import pymupdf4llm  # type: ignore

    doc = pymupdf.open(str(pdf))
    page_count = doc.page_count
    doc.close()

    text = pymupdf4llm.to_markdown(str(pdf), page_chunks=False)
    if isinstance(text, list):
        markdown = "\n\n".join(str(item) for item in text)
    else:
        markdown = str(text)
    (out_dir / "extracted_text.md").write_text(markdown, encoding="utf-8-sig")
    return {
        "extractor": "pymupdf4llm",
        "page_count": page_count,
        "extracted_characters": len(markdown),
        "output": str((out_dir / "extracted_text.md").resolve()),
    }


def extract_with_stdlib(pdf: Path, out_dir: Path) -> dict[str, Any]:
    data = pdf.read_bytes()
    objects = pdf_extract_text.extract_objects(data)
    streams = pdf_extract_text.extract_streams(objects)
    cmap = pdf_extract_text.parse_cmaps(streams)
    text, stream_notes = pdf_extract_text.extract_text_from_streams(streams, cmap)
    page_count = pdf_extract_text.estimate_page_count(data)
    (out_dir / "extracted_text.md").write_text(text or "_No text extracted by stdlib fallback._\n", encoding="utf-8-sig")
    (out_dir / "basic_extraction_notes.md").write_text(
        pdf_extract_text.build_reading_notes(pdf, text, streams, cmap, page_count),
        encoding="utf-8-sig",
    )
    return {
        "extractor": "stdlib-fallback",
        "page_count": page_count,
        "object_count": len(objects),
        "stream_count": len(streams),
        "decoded_stream_count": sum(1 for s in streams if s["decoded"]),
        "text_stream_count": len(stream_notes),
        "to_unicode_entries": len(cmap),
        "extracted_characters": len(text),
        "output": str((out_dir / "extracted_text.md").resolve()),
        "warning": "Provisional extraction only; validate against rendered pages or use a PDF library/OCR.",
    }


def write_deep_backend_report(out_dir: Path) -> dict[str, Any]:
    backends = []
    for backend in DEEP_BACKENDS:
        available = importlib.util.find_spec(backend["module"]) is not None
        backends.append({**backend, "available": available})
    selected = next((item for item in backends if item["available"]), None)
    payload = {
        "mode": "deep",
        "selected_backend": selected["name"] if selected else None,
        "backends": backends,
        "policy": "Deep backends are optional. This script records availability and falls back to the robust local pack unless a backend wrapper has been explicitly implemented and validated.",
    }
    (out_dir / "deep_backend_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    lines = [
        "# Deep Backend Report",
        "",
        "Deep mode probes optional high-accuracy backends without installing or calling cloud services.",
        "",
        "## Backend Inventory",
        "",
    ]
    for item in backends:
        state = "available" if item["available"] else "missing"
        lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- Python module: `{item['module']}`",
                f"- Status: {state}",
                f"- Best fit: {item['best_fit']}",
                f"- Note: {item['status_note']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Decision",
            "",
            "- If no deep backend is available, use robust mode artifacts as the evidence pack.",
            "- If a backend is available, validate its output against `strategy_comparison.md`, rendered pages, and `confidence_report.md` before replacing `extracted_text.md`.",
        ]
    )
    (out_dir / "deep_backend_report.md").write_text("\n".join(lines), encoding="utf-8-sig")
    return payload


def run_strategy_compare(args: argparse.Namespace, ocr_auto: bool) -> int:
    import pdf_strategy_compare  # noqa: E402

    compare_args = [
        str(Path(args.pdf)),
        "--out",
        str(Path(args.out)),
        "--render-pages",
        "--max-render-pages",
        str(args.max_render_pages),
        "--render-dpi",
        str(args.render_dpi),
        "--max-table-pages",
        str(args.max_table_pages),
        "--max-table-probe-pages",
        str(args.max_table_probe_pages),
    ]
    if args.ocr_pages:
        compare_args.append("--ocr-pages")
    elif ocr_auto:
        compare_args.append("--ocr-auto")
    if args.table_structure_probe:
        compare_args.append("--table-structure-probe")
    return pdf_strategy_compare.main(compare_args)


def write_notes(pdf: Path, out_dir: Path, extraction: dict[str, Any], triage_record: dict[str, Any]) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# PDF Reading Pack",
        "",
        f"Created UTC: `{now}`",
        f"PDF: `{pdf.resolve()}`",
        f"Mode: `{extraction.get('mode', 'quick')}`",
        f"Extractor: `{extraction['extractor']}`",
        f"Estimated/actual pages: {extraction.get('page_count')}",
        f"Extracted characters: {extraction.get('extracted_characters')}",
        f"Rendered pages: {extraction.get('visuals', {}).get('rendered_pages', 0)}",
        f"Extracted images: {extraction.get('visuals', {}).get('extracted_images', 0)}",
        "",
        "## Recommended Lane",
        "",
    ]
    for lane in triage_record["recommended_lane"]:
        lines.append(f"- {lane}")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            "- Spot-check extracted text against rendered pages before using for final claims.",
            "- Use `sidecar_gold_test.py` or `reading_quality_test.py` when a same-content reference exists.",
            "- For image-heavy PDFs, add page screenshots or figure extraction before summarizing visuals.",
        ]
    )
    (out_dir / "reading_notes.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Create a PDF reading pack with local extractors.")
    parser.add_argument("pdf", help="PDF file")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument(
        "--mode",
        choices=["quick", "robust", "deep"],
        default="quick",
        help="quick: fast local text pack; robust: compare strategies/render pages/OCR when needed; deep: probe heavy backends then run robust",
    )
    parser.add_argument("--render-pages", action="store_true", help="Render page PNGs and extract embedded images when PyMuPDF is available")
    parser.add_argument("--ocr-pages", action="store_true", help="Run RapidOCR over rendered pages; robust/deep otherwise use OCR only when routing says it is needed")
    parser.add_argument("--max-render-pages", type=int, default=30, help="Maximum pages to render when --render-pages is set")
    parser.add_argument("--render-dpi", type=int, default=144, help="DPI for rendered page PNGs")
    parser.add_argument("--max-table-pages", type=int, default=80, help="Maximum pages to scan with table-aware extraction in robust/deep mode")
    parser.add_argument("--table-structure-probe", action="store_true", help="Probe rendered pages for ruled scanned-table structure evidence")
    parser.add_argument("--max-table-probe-pages", type=int, default=5, help="Maximum rendered pages/images to probe for ruled table structure")
    args = parser.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode in {"robust", "deep"}:
        if args.mode == "deep":
            write_deep_backend_report(out_dir)
        return run_strategy_compare(args, ocr_auto=not args.ocr_pages)

    tools = pdf_triage.tool_inventory()
    triage_record = pdf_triage.build_record(pdf, tools)
    pdf_triage.write_reports(out_dir, [triage_record], tools)

    if importlib.util.find_spec("pymupdf4llm") and importlib.util.find_spec("pymupdf"):
        extraction = extract_with_pymupdf4llm(pdf, out_dir)
        if args.render_pages:
            extraction["visuals"] = export_visuals_with_pymupdf(pdf, out_dir, args.max_render_pages, args.render_dpi)
    else:
        extraction = extract_with_stdlib(pdf, out_dir)
    extraction["mode"] = args.mode

    (out_dir / "extraction_metadata.json").write_text(json.dumps(extraction, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    write_notes(pdf, out_dir, extraction, triage_record)
    print(f"Wrote PDF reading pack: {out_dir}")
    print(f"Extractor: {extraction['extractor']}")
    print(f"Extracted characters: {extraction.get('extracted_characters')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
