#!/usr/bin/env python3
"""Optional PP-StructureV3 table extraction backend for q-pdf-reading.

This script is intentionally optional. It requires PaddleOCR, PaddleX OCR
extras, PaddlePaddle, and model files. It writes page-grounded JSON/Markdown,
HTML table, and XLSX artifacts when the backend is available.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _configure_runtime(args: argparse.Namespace) -> None:
    os.environ.setdefault("SETUPTOOLS_USE_DISTUTILS", "stdlib")
    if not args.enable_mkldnn:
        os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
        os.environ.setdefault("FLAGS_use_mkldnn", "false")
    if args.model_source:
        os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", args.model_source)
    if args.skip_model_source_check:
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")


def _rel_files(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(
        str(path.relative_to(root)).replace("\\", "/")
        for path in root.rglob("*")
        if path.is_file()
    )


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _table_blocks(result: dict[str, Any]) -> list[Any]:
    blocks = result.get("parsing_res_list") or []
    return [
        block
        for block in blocks
        if (_value(block, "block_label") or _value(block, "label")) == "table"
    ]


def _render_pdf_pages(pdf: Path, out_dir: Path, dpi: int, max_pages: int) -> list[Path]:
    try:
        import pymupdf  # type: ignore
    except Exception as exc:
        raise SystemExit(f"PyMuPDF is required for --render-pdf-pages: {exc}") from exc

    pages_dir = out_dir / "rendered_pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    rendered: list[Path] = []
    for page_index in range(min(doc.page_count, max_pages)):
        page = doc.load_page(page_index)
        out_path = pages_dir / f"page_{page_index + 1:03d}_{dpi}dpi.png"
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pix.save(str(out_path))
        rendered.append(out_path)
    doc.close()
    return rendered


def _prediction_inputs(src: Path, out_dir: Path, args: argparse.Namespace) -> tuple[list[Path], dict[str, Any]]:
    if src.suffix.lower() == ".pdf" and args.render_pdf_pages:
        rendered = _render_pdf_pages(src, out_dir, args.render_dpi, args.max_pages)
        return rendered, {
            "input_mode": "rendered_pdf_pages",
            "render_dpi": args.render_dpi,
            "rendered_pages": [str(path) for path in rendered],
        }
    return [src], {
        "input_mode": "native_pdf_or_image",
        "render_dpi": None,
        "rendered_pages": [],
    }


def _flatten_results(pipeline: Any, inputs: list[Path]) -> list[Any]:
    results: list[Any] = []
    for item in inputs:
        predicted = pipeline.predict(str(item))
        results.extend(predicted)
    return results


def _save_result(result: Any, out_dir: Path) -> list[dict[str, str]]:
    saves: list[dict[str, str]] = []
    for name, method_name in (
        ("json", "save_to_json"),
        ("markdown", "save_to_markdown"),
        ("html", "save_to_html"),
        ("xlsx", "save_to_xlsx"),
    ):
        method = getattr(result, method_name, None)
        if method is None:
            saves.append({"artifact": name, "status": "missing-method"})
            continue
        try:
            method(str(out_dir))
            saves.append({"artifact": name, "status": "saved"})
        except Exception as exc:  # Keep partial backend output instead of losing evidence.
            saves.append({"artifact": name, "status": "failed", "error": str(exc)})
    return saves


def _write_summary(out_dir: Path, summary: dict[str, Any]) -> None:
    (out_dir / "ppstructure_table_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# PP-Structure Table Extraction Summary",
        "",
        f"Input: `{summary['input']}`",
        f"Input mode: `{summary['input_mode']}`",
        f"Pages/results: {summary['result_count']}",
        f"Detected table blocks: {summary['table_block_count']}",
        "",
        "## Runtime",
        "",
    ]
    for item in summary["runtime_notes"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Page Results", ""])
    for page in summary["pages"]:
        lines.append(f"Page result {page['index']}")
        lines.append(f"Source input: `{page['source_input']}`")
        lines.append(f"Tables: {page['table_blocks']}")
        lines.append(f"Layout boxes: {page['layout_boxes']}")
        if page.get("table_html_preview"):
            lines.append(f"HTML preview: `{page['table_html_preview']}`")
        lines.append("")
    lines.extend(["## Artifacts", ""])
    for artifact in summary["artifacts"]:
        lines.append(f"- `{artifact}`")
    (out_dir / "ppstructure_table_summary.md").write_text(
        "\n".join(lines).rstrip() + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(
        description="Run optional PaddleOCR PP-StructureV3 table extraction over a PDF or image."
    )
    parser.add_argument("input", help="Input PDF or page image.")
    parser.add_argument("--out", required=True, help="Output directory for JSON/Markdown/HTML/XLSX artifacts.")
    parser.add_argument("--lang", default="en", help="PaddleOCR language code. Use 'ch' for Chinese-heavy documents.")
    parser.add_argument("--model-source", default="bos", help="PaddleX model source, for example bos, huggingface, aistudio, or modelscope.")
    parser.add_argument("--render-pdf-pages", action="store_true", help="Render PDF pages to high-DPI images before PP-Structure. Better for vector, scanned, or tiny-text PDFs.")
    parser.add_argument("--render-dpi", type=int, default=300, help="DPI used with --render-pdf-pages.")
    parser.add_argument("--max-pages", type=int, default=30, help="Maximum PDF pages to render/process.")
    parser.add_argument("--enable-mkldnn", action="store_true", help="Keep Paddle CPU MKLDNN/oneDNN enabled. Default disables it for Windows stability.")
    parser.add_argument("--no-skip-model-source-check", dest="skip_model_source_check", action="store_false", help="Run PaddleX model source connectivity checks.")
    parser.set_defaults(skip_model_source_check=True)
    args = parser.parse_args(argv)

    src = Path(args.input)
    out_dir = Path(args.out)
    if not src.exists():
        print(f"Input does not exist: {src}", file=sys.stderr)
        return 2
    if src.suffix.lower() not in IMAGE_EXTS and src.suffix.lower() != ".pdf":
        print(f"Unsupported input type: {src.suffix}", file=sys.stderr)
        return 2
    out_dir.mkdir(parents=True, exist_ok=True)

    _configure_runtime(args)

    try:
        from paddleocr import PPStructureV3
    except Exception as exc:
        print("PP-StructureV3 backend is unavailable.", file=sys.stderr)
        print("Install example: pip install paddleocr paddlepaddle paddlex[ocr]", file=sys.stderr)
        print(f"Import error: {exc}", file=sys.stderr)
        return 3

    inputs, input_meta = _prediction_inputs(src, out_dir, args)
    pipeline = PPStructureV3(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_table_recognition=True,
        use_formula_recognition=False,
        use_chart_recognition=False,
        use_seal_recognition=False,
        lang=args.lang,
    )
    results = _flatten_results(pipeline, inputs)

    pages: list[dict[str, Any]] = []
    table_block_count = 0
    save_status: list[dict[str, str]] = []
    for index, result in enumerate(results):
        save_status.extend(_save_result(result, out_dir))
        tables = _table_blocks(result)
        table_block_count += len(tables)
        layout_boxes = len((result.get("layout_det_res") or {}).get("boxes") or [])
        preview = ""
        if tables:
            preview = (
                _value(tables[0], "block_content") or _value(tables[0], "content") or ""
            ).replace("\n", " ")[:240]
        source_input = str(inputs[min(index, len(inputs) - 1)]) if inputs else str(src)
        pages.append(
            {
                "index": index,
                "source_input": source_input,
                "table_blocks": len(tables),
                "layout_boxes": layout_boxes,
                "table_html_preview": preview,
            }
        )

    summary = {
        "input": str(src),
        "output_dir": str(out_dir),
        "input_mode": input_meta["input_mode"],
        "render_dpi": input_meta["render_dpi"],
        "rendered_pages": input_meta["rendered_pages"],
        "result_count": len(results),
        "table_block_count": table_block_count,
        "pages": pages,
        "save_status": save_status,
        "artifacts": _rel_files(out_dir),
        "runtime_notes": [
            f"lang={args.lang}",
            f"model_source={args.model_source or 'default'}",
            f"mkldnn={'enabled' if args.enable_mkldnn else 'disabled'}",
            f"render_pdf_pages={args.render_pdf_pages}",
            f"render_dpi={args.render_dpi if args.render_pdf_pages else 'n/a'}",
            "PP-StructureV3 may download model files on first use.",
        ],
    }
    _write_summary(out_dir, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
