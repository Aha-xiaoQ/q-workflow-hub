#!/usr/bin/env python3
"""Run local OCR over PDF-rendered pages or an image folder."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def render_pdf_pages(pdf: Path, pages_dir: Path, max_pages: int, dpi: int) -> list[Path]:
    if not importlib.util.find_spec("pymupdf"):
        raise SystemExit("PyMuPDF is required to render PDF pages for OCR")
    import pymupdf  # type: ignore

    pages_dir.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(pdf))
    zoom = dpi / 72.0
    matrix = pymupdf.Matrix(zoom, zoom)
    paths = []
    for page_index in range(min(doc.page_count, max_pages)):
        page = doc.load_page(page_index)
        out_path = pages_dir / f"page_{page_index + 1:03d}.png"
        if not out_path.exists():
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            pix.save(str(out_path))
        paths.append(out_path)
    doc.close()
    return paths


def discover_images(target: Path) -> list[Path]:
    if target.is_file() and target.suffix.lower() in IMAGE_EXTS:
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    return []


def result_to_record(page_num: int, image_path: Path, result: Any) -> dict[str, Any]:
    txts = list(getattr(result, "txts", []) or [])
    scores = list(getattr(result, "scores", []) or [])
    boxes = getattr(result, "boxes", None)
    avg_score = sum(float(s) for s in scores) / len(scores) if scores else 0.0
    return {
        "page": page_num,
        "image": str(image_path.resolve()),
        "line_count": len(txts),
        "avg_score": round(avg_score, 4),
        "elapsed_seconds": float(getattr(result, "elapse", 0.0) or 0.0),
        "text": txts,
        "scores": [round(float(s), 4) for s in scores],
        "has_boxes": boxes is not None,
    }


def write_outputs(out_dir: Path, records: list[dict[str, Any]], target: Path, engine: str) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "created_utc": now,
        "target": str(target.resolve()),
        "engine": engine,
        "page_count": len(records),
        "total_lines": sum(item["line_count"] for item in records),
        "avg_score": round(
            sum(item["avg_score"] for item in records if item["line_count"]) / max(1, sum(1 for item in records if item["line_count"])),
            4,
        ),
        "records": records,
    }
    (out_dir / "ocr_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")

    lines = ["# OCR Text", "", f"Created UTC: `{now}`", f"Engine: `{engine}`", ""]
    for record in records:
        lines.append(f"## Page {record['page']:03d}")
        lines.append("")
        for text, score in zip(record["text"], record["scores"]):
            lines.append(f"- {text}  <!-- conf={score:.4f} -->")
        lines.append("")
    (out_dir / "ocr_text.md").write_text("\n".join(lines), encoding="utf-8-sig")

    summary = [
        "# OCR Summary",
        "",
        f"Created UTC: `{now}`",
        f"Target: `{target.resolve()}`",
        f"Engine: `{engine}`",
        f"Pages/images processed: {len(records)}",
        f"Total OCR lines: {payload['total_lines']}",
        f"Average confidence: {payload['avg_score']}",
        "",
        "Use OCR output as primary evidence only for scanned/image PDFs. For digital PDFs, use it as visual cross-check.",
    ]
    (out_dir / "ocr_summary.md").write_text("\n".join(summary), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Run local RapidOCR over PDF pages or images.")
    parser.add_argument("target", help="PDF file, image file, or folder of rendered page images")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--render-dpi", type=int, default=144)
    parser.add_argument("--text-score", type=float, default=None, help="Optional RapidOCR text score threshold")
    args = parser.parse_args(argv)

    if not importlib.util.find_spec("rapidocr"):
        raise SystemExit("RapidOCR is not installed. Install with: python -m pip install rapidocr")
    from rapidocr import RapidOCR  # type: ignore

    target = Path(args.target)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if target.is_file() and target.suffix.lower() == ".pdf":
        images = render_pdf_pages(target, out_dir / "ocr_pages", args.max_pages, args.render_dpi)
    else:
        images = discover_images(target)[: args.max_pages]
    if not images:
        raise SystemExit(f"No OCR input images found: {target}")

    ocr = RapidOCR()
    records = []
    for idx, image_path in enumerate(images, start=1):
        result = ocr(str(image_path), text_score=args.text_score)
        records.append(result_to_record(idx, image_path, result))
        print(f"OCR page/image {idx}/{len(images)}: {records[-1]['line_count']} lines, avg={records[-1]['avg_score']}")
    write_outputs(out_dir, records, target, "rapidocr")
    print(f"Wrote OCR output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
