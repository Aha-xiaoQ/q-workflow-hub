#!/usr/bin/env python3
"""Create a lightweight PDF reading triage pack using only the standard library."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any


SIDECAR_EXTS = [".md", ".markdown", ".txt", ".docx", ".pptx", ".html", ".htm"]
IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp", ".svg"]
PY_MODULES = [
    "pymupdf4llm",
    "fitz",
    "pymupdf",
    "marker",
    "magic_pdf",
    "docling",
    "unstructured",
    "pdfplumber",
    "pdfminer",
    "pypdf",
    "PyPDF2",
    "pytesseract",
    "PIL",
]
COMMANDS = ["pdftotext", "pdftoppm", "mutool", "tesseract", "magick"]


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_prefix(path: Path, limit: int = 8 * 1024 * 1024) -> bytes:
    with path.open("rb") as f:
        return f.read(limit)


def estimate_pdf_signals(path: Path) -> dict[str, Any]:
    data = read_prefix(path)
    full_small = path.stat().st_size <= 64 * 1024 * 1024
    full_data = path.read_bytes() if full_small else data
    decoded = data.decode("latin-1", errors="ignore")
    page_count = len(re.findall(rb"/Type\s*/Page\b", full_data))
    image_count = len(re.findall(rb"/Subtype\s*/Image\b", full_data))
    stream_count = len(re.findall(rb"\bstream\b", full_data))
    obj_count = len(re.findall(rb"\bobj\b", full_data))
    text_ops = len(re.findall(rb"\bBT\b|\bET\b|Tj|TJ", full_data))
    encrypted = b"/Encrypt" in full_data[:4096] or b"/Encrypt" in data
    return {
        "page_count_estimate": page_count or None,
        "image_object_count_estimate": image_count,
        "stream_count_estimate": stream_count,
        "object_count_estimate": obj_count,
        "text_operator_count_estimate": text_ops,
        "has_to_unicode": "/ToUnicode" in decoded,
        "has_font_objects": "/Font" in decoded,
        "has_images": image_count > 0,
        "has_object_streams": "/ObjStm" in decoded,
        "has_flate_decode": "/FlateDecode" in decoded,
        "encrypted": encrypted,
        "scanned_or_image_heavy_hint": bool(page_count and image_count >= page_count and text_ops < page_count * 3),
        "binary_search_warning": "Raw PDF string search is not reliable; compressed streams and layout order require PDF-aware tools.",
    }


def library_page_count(path: Path) -> int | None:
    if importlib.util.find_spec("pymupdf"):
        try:
            import pymupdf  # type: ignore

            doc = pymupdf.open(str(path))
            count = doc.page_count
            doc.close()
            return count
        except Exception:
            return None
    if importlib.util.find_spec("fitz"):
        try:
            import fitz  # type: ignore

            doc = fitz.open(str(path))
            count = doc.page_count
            doc.close()
            return count
        except Exception:
            return None
    return None


def sibling_candidates(pdf: Path) -> dict[str, Any]:
    parent = pdf.parent
    stem = pdf.stem.lower()
    exact_sidecars = []
    loose_sidecars = []
    image_dirs = []
    nearby_images = []

    for child in parent.iterdir():
        if child == pdf:
            continue
        if child.is_file():
            suffix = child.suffix.lower()
            child_stem = child.stem.lower()
            if suffix in SIDECAR_EXTS:
                if child_stem == stem:
                    exact_sidecars.append(str(child))
                elif stem in child_stem or child_stem in stem:
                    loose_sidecars.append(str(child))
            if suffix in IMAGE_EXTS:
                nearby_images.append(str(child))
        elif child.is_dir():
            name = child.name.lower()
            if name in {"figures", "figure", "images", "imgs", "assets"} or "figure" in name or "image" in name:
                count = sum(1 for p in child.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
                image_dirs.append({"path": str(child), "image_count": count})

    return {
        "exact_sidecars": exact_sidecars,
        "loose_sidecars": loose_sidecars[:20],
        "image_dirs": image_dirs,
        "nearby_images": nearby_images[:30],
    }


def tool_inventory() -> dict[str, Any]:
    modules = {name: importlib.util.find_spec(name) is not None for name in PY_MODULES}
    commands = {name: shutil.which(name) is not None for name in COMMANDS}
    return {"python_modules": modules, "commands": commands}


def choose_lane(signals: dict[str, Any], siblings: dict[str, Any], tools: dict[str, Any]) -> list[str]:
    lanes: list[str] = []
    if siblings["exact_sidecars"] or siblings["loose_sidecars"]:
        lanes.append("source-native sidecar first")
    if signals["encrypted"]:
        lanes.append("blocking: encrypted PDF needs password or unlocked copy")
        return lanes
    modules = tools["python_modules"]
    if signals["scanned_or_image_heavy_hint"]:
        if modules.get("docling") or modules.get("unstructured") or modules.get("pytesseract") or tools["commands"].get("tesseract"):
            lanes.append("OCR/layout extraction")
        else:
            lanes.append("blocking/degraded: image-heavy PDF but no OCR/layout tool detected")
    elif modules.get("pymupdf4llm"):
        lanes.append("local layout-aware Markdown via pymupdf4llm")
    elif modules.get("docling"):
        lanes.append("local structured conversion via Docling")
    elif modules.get("unstructured"):
        lanes.append("local partition_pdf extraction")
    elif modules.get("pdfplumber") or modules.get("pypdf") or modules.get("PyPDF2") or tools["commands"].get("pdftotext"):
        lanes.append("simple local text extraction, then visual spot check")
    else:
        lanes.append("degraded: no PDF extraction library detected; use sidecar or install local parser")
    if signals["has_images"] or siblings["image_dirs"]:
        lanes.append("render or reuse figures for visual evidence")
    return lanes


def discover_pdfs(target: Path) -> list[Path]:
    if target.is_file():
        if target.suffix.lower() != ".pdf":
            raise SystemExit(f"Not a PDF: {target}")
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*.pdf") if p.is_file())
    raise SystemExit(f"Missing path: {target}")


def write_reports(out_dir: Path, records: list[dict[str, Any]], tools: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    freeze = {"created_utc": now, "records": records, "tool_inventory": tools}
    (out_dir / "source_freeze.json").write_text(json.dumps(freeze, indent=2, ensure_ascii=False), encoding="utf-8-sig")

    lines = [
        "# PDF Triage Report",
        "",
        f"Created UTC: `{now}`",
        "",
        "## Tool Inventory",
        "",
    ]
    for name, ok in tools["python_modules"].items():
        lines.append(f"- Python `{name}`: {'available' if ok else 'missing'}")
    for name, ok in tools["commands"].items():
        lines.append(f"- Command `{name}`: {'available' if ok else 'missing'}")
    lines.extend(["", "## PDFs", ""])
    for record in records:
        lines.extend([
            f"### {record['name']}",
            "",
            f"- Path: `{record['path']}`",
            f"- Size: {record['size_bytes']} bytes",
            f"- SHA256: `{record['sha256']}`",
            f"- Modified UTC: `{record['modified_utc']}`",
            f"- Page count estimate: {record['signals']['page_count_estimate']}",
            f"- Image object estimate: {record['signals']['image_object_count_estimate']}",
            f"- Text operator estimate: {record['signals']['text_operator_count_estimate']}",
            f"- Encrypted: {record['signals']['encrypted']}",
            f"- Recommended lane: {', '.join(record['recommended_lane'])}",
            "",
            "Sidecars and visual assets:",
            f"- Exact sidecars: {record['siblings']['exact_sidecars'] or 'none'}",
            f"- Loose sidecars: {record['siblings']['loose_sidecars'] or 'none'}",
            f"- Image dirs: {record['siblings']['image_dirs'] or 'none'}",
            "",
        ])
    (out_dir / "triage_report.md").write_text("\n".join(lines), encoding="utf-8-sig")

    with (out_dir / "page_inventory.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["pdf", "page", "status", "notes"],
        )
        writer.writeheader()
        for record in records:
            page_count = record["signals"]["page_count_estimate"] or 0
            if page_count:
                for page in range(1, page_count + 1):
                    writer.writerow({"pdf": record["name"], "page": page, "status": "unreviewed", "notes": ""})
            else:
                writer.writerow({"pdf": record["name"], "page": "", "status": "unknown", "notes": "page count not detected"})


def build_record(pdf: Path, tools: dict[str, Any]) -> dict[str, Any]:
    stat = pdf.stat()
    signals = estimate_pdf_signals(pdf)
    page_count = library_page_count(pdf)
    if page_count:
        signals["page_count_estimate"] = page_count
        signals["page_count_source"] = "library"
    else:
        signals["page_count_source"] = "binary-estimate"
    siblings = sibling_candidates(pdf)
    return {
        "name": pdf.name,
        "path": str(pdf.resolve()),
        "size_bytes": stat.st_size,
        "modified_utc": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat(),
        "sha256": sha256_file(pdf),
        "signals": signals,
        "siblings": siblings,
        "recommended_lane": choose_lane(signals, siblings, tools),
    }


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Create a PDF triage reading pack.")
    parser.add_argument("target", help="PDF file or folder containing PDFs")
    parser.add_argument("--out", required=True, help="Output folder for triage report")
    args = parser.parse_args(argv)

    target = Path(args.target)
    out_dir = Path(args.out)
    tools = tool_inventory()
    pdfs = discover_pdfs(target)
    if not pdfs:
        raise SystemExit(f"No PDFs found in {target}")
    records = [build_record(pdf, tools) for pdf in pdfs]
    write_reports(out_dir, records, tools)
    print(f"Wrote PDF triage pack: {out_dir}")
    for record in records:
        print(f"- {record['name']}: {', '.join(record['recommended_lane'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
