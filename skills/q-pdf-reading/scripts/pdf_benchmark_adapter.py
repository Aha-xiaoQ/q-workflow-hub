#!/usr/bin/env python3
"""Create q-pdf-reading benchmark manifests from local/public dataset layouts."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8-sig")


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return value.strip("-") or "sample"


def relpath(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def text_from_tokens(values: list[str], limit: int = 2000) -> str:
    clean = [item.strip() for item in values if isinstance(item, str) and item.strip()]
    if not clean:
        return ""
    counts = Counter(clean)
    ordered = [term for term, _ in counts.most_common(limit)]
    return "\n".join(ordered) + "\n"


def image_to_pdf(image: Path, out_pdf: Path) -> bool:
    try:
        from PIL import Image  # type: ignore
    except Exception:
        return False
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(image) as im:
        if im.mode in {"RGBA", "P"}:
            im = im.convert("RGB")
        im.save(out_pdf, "PDF")
    return True


def find_matching_source(stem: str, roots: list[Path]) -> Path | None:
    for root in roots:
        if not root.exists():
            continue
        for suffix in [".pdf", *sorted(IMAGE_EXTS)]:
            candidate = root / f"{stem}{suffix}"
            if candidate.exists():
                return candidate
        matches = sorted(p for p in root.rglob("*") if p.is_file() and p.stem == stem and (p.suffix.lower() == ".pdf" or p.suffix.lower() in IMAGE_EXTS))
        if matches:
            return matches[0]
    return None


def source_to_pdf(source: Path, out_dir: Path, sample_id: str) -> Path | None:
    if source.suffix.lower() == ".pdf":
        return source
    if source.suffix.lower() in IMAGE_EXTS:
        out_pdf = out_dir / "generated_pdfs" / f"{sample_id}.pdf"
        if image_to_pdf(source, out_pdf):
            return out_pdf
    return None


def default_manifest(name: str, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "version": 0,
        "name": name,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "defaults": {
            "mode": "robust",
            "max_render_pages": args.max_render_pages,
            "max_table_pages": args.max_table_pages,
            "max_table_probe_pages": args.max_table_probe_pages,
            "render_dpi": args.render_dpi,
        },
        "samples": [],
    }


def local_folder(args: argparse.Namespace, out_dir: Path) -> tuple[dict[str, Any], list[str]]:
    root = Path(args.input)
    manifest = default_manifest(args.name or f"local-folder-{root.name}", args)
    warnings = []
    pdfs = sorted(root.rglob("*.pdf"))
    if args.limit:
        pdfs = pdfs[: args.limit]
    for pdf in pdfs:
        sample_id = slug(pdf.stem)
        manifest["samples"].append(
            {
                "id": sample_id,
                "pdf": str(pdf.resolve()),
                "class": "local-pdf",
                "modes": [args.mode],
                "expected": {
                    "min_confidence_grade": "low",
                    "require_artifacts": ["extracted_text.md", "reading_notes.md"],
                },
            }
        )
    if not pdfs:
        warnings.append(f"No PDFs found under {root}")
    return manifest, warnings


def extract_funsd_text(annotation: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    words: list[str] = []
    labels = Counter()
    links = 0
    for item in annotation.get("form", []):
        text = item.get("text")
        if text:
            words.append(str(text))
        labels[str(item.get("label", "unknown"))] += 1
        links += len(item.get("linking", []) or [])
        for word in item.get("words", []) or []:
            if isinstance(word, dict) and word.get("text"):
                words.append(str(word["text"]))
    return words, {"entity_labels": dict(labels), "link_count": links, "word_count": len(words)}


def funsd(args: argparse.Namespace, out_dir: Path) -> tuple[dict[str, Any], list[str]]:
    root = Path(args.input)
    annotation_files = sorted((root / "annotations").glob("*.json"))
    if not annotation_files:
        annotation_files = sorted(root.rglob("*.json"))
    manifest = default_manifest(args.name or f"funsd-{root.name}", args)
    warnings = []
    roots = [root / "images", root]
    if args.pdf_root:
        roots.insert(0, Path(args.pdf_root))
    if args.limit:
        annotation_files = annotation_files[: args.limit]
    for annotation_path in annotation_files:
        sample_id = slug(annotation_path.stem)
        annotation = read_json(annotation_path)
        words, ocr_payload = extract_funsd_text(annotation)
        expected_dir = out_dir / "expected" / sample_id
        text_path = expected_dir / "expected_text.md"
        ocr_path = expected_dir / "expected_ocr.json"
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(text_from_tokens(words), encoding="utf-8-sig")
        write_json(ocr_path, ocr_payload)
        source = find_matching_source(annotation_path.stem, roots)
        if not source:
            warnings.append(f"Missing FUNSD image/PDF for {annotation_path.name}")
            continue
        pdf = source_to_pdf(source, out_dir, sample_id)
        if not pdf:
            warnings.append(f"Could not convert image to PDF for {source}")
            continue
        manifest["samples"].append(
            {
                "id": sample_id,
                "pdf": relpath(pdf, out_dir),
                "class": "funsd-scanned-form",
                "modes": [args.mode],
                "options": {"ocr_pages": True},
                "expected": {
                    "pdf_type": ["scanned-or-image-only", "scanned-or-image-heavy", "schematic-or-diagram", "digital-text-unknown-layout"],
                    "min_confidence_grade": "low",
                    "min_text_token_coverage": 0.2,
                    "ground_truth": {
                        "text": relpath(text_path, out_dir),
                        "ocr": relpath(ocr_path, out_dir),
                    },
                    "require_artifacts": ["pages", "ocr/ocr_text.md", "confidence_report.md"],
                },
            }
        )
    return manifest, warnings


def parse_ctdar_xml(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    tables = []
    for table in root.iter():
        if table.tag.lower().endswith("table"):
            cells = [node for node in table.iter() if node.tag.lower().endswith("cell")]
            tables.append({"cell_count": len(cells)})
    if not tables and root.tag.lower().endswith("table"):
        cells = [node for node in root.iter() if node.tag.lower().endswith("cell")]
        tables.append({"cell_count": len(cells)})
    return {"table_count": len(tables), "tables": tables}


def ctdar(args: argparse.Namespace, out_dir: Path) -> tuple[dict[str, Any], list[str]]:
    root = Path(args.input)
    xml_files = sorted(root.rglob("*.xml"))
    manifest = default_manifest(args.name or f"ctdar-{root.name}", args)
    warnings = []
    roots = [root]
    if args.pdf_root:
        roots.insert(0, Path(args.pdf_root))
    if args.limit:
        xml_files = xml_files[: args.limit]
    for xml_path in xml_files:
        sample_id = slug(xml_path.stem)
        expected_tables = parse_ctdar_xml(xml_path)
        expected_dir = out_dir / "expected" / sample_id
        tables_path = expected_dir / "expected_tables.json"
        write_json(tables_path, expected_tables)
        source = find_matching_source(xml_path.stem, roots)
        if not source:
            warnings.append(f"Missing cTDaR image/PDF for {xml_path.name}")
            continue
        pdf = source_to_pdf(source, out_dir, sample_id)
        if not pdf:
            warnings.append(f"Could not convert image to PDF for {source}")
            continue
        expected = {
            "min_confidence_grade": "low",
            "ground_truth": {"tables": relpath(tables_path, out_dir)},
            "require_artifacts": ["pages", "reading_notes.md", "confidence_report.md"],
        }
        if source.suffix.lower() == ".pdf" and expected_tables["table_count"]:
            expected["min_tables"] = 1
            expected["require_artifacts"].append("tables/table_extraction_report.md")
        elif args.require_table_structure_probe and expected_tables["table_count"]:
            expected["min_table_structure_regions"] = 1
            expected_cells = sum(int(table.get("cell_count", 0) or 0) for table in expected_tables.get("tables", []))
            if expected_cells:
                expected["min_table_structure_cells"] = max(1, int(expected_cells * 0.5))
            expected["require_artifacts"].append("tables/table_structure_probe_report.md")
        manifest["samples"].append(
            {
                "id": sample_id,
                "pdf": relpath(pdf, out_dir),
                "class": "ctdar-table",
                "modes": [args.mode],
                "options": {"table_structure_probe": True} if args.require_table_structure_probe else {},
                "expected": expected,
            }
        )
    if not xml_files:
        warnings.append(f"No XML ground truth files found under {root}")
    return manifest, warnings


def collect_strings(value: Any, keys: set[str], out: list[str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_l = str(key).lower()
            if key_l in keys and isinstance(item, str):
                out.append(item)
            else:
                collect_strings(item, keys, out)
    elif isinstance(value, list):
        for item in value:
            collect_strings(item, keys, out)


def count_label_like(value: Any, label_terms: set[str]) -> Counter:
    counts: Counter = Counter()
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {"type", "label", "category", "category_name"} and isinstance(item, str):
                item_l = item.lower()
                for term in label_terms:
                    if term in item_l:
                        counts[term] += 1
            counts.update(count_label_like(item, label_terms))
    elif isinstance(value, list):
        for item in value:
            counts.update(count_label_like(item, label_terms))
    return counts


def generic_json(args: argparse.Namespace, out_dir: Path) -> tuple[dict[str, Any], list[str]]:
    root = Path(args.input)
    json_files = [root] if root.is_file() else sorted(root.rglob("*.json"))
    manifest = default_manifest(args.name or f"generic-json-{root.stem}", args)
    warnings = []
    roots = [root.parent if root.is_file() else root]
    if args.pdf_root:
        roots.insert(0, Path(args.pdf_root))
    if args.limit:
        json_files = json_files[: args.limit]
    for json_path in json_files:
        data = read_json(json_path)
        records = data if isinstance(data, list) else data.get("data") if isinstance(data, dict) and isinstance(data.get("data"), list) else [data]
        for index, record in enumerate(records):
            record_id = str(record.get("id") or record.get("image_id") or record.get("page_id") or f"{json_path.stem}-{index + 1}") if isinstance(record, dict) else f"{json_path.stem}-{index + 1}"
            sample_id = slug(record_id)
            texts: list[str] = []
            collect_strings(record, {"text", "content", "html", "latex", "transcription"}, texts)
            labels = count_label_like(record, {"table", "figure", "formula", "text", "title"})
            expected_dir = out_dir / "expected" / sample_id
            text_path = expected_dir / "expected_text.md"
            tables_path = expected_dir / "expected_tables.json"
            layout_path = expected_dir / "expected_layout.json"
            text_path.parent.mkdir(parents=True, exist_ok=True)
            text_path.write_text(text_from_tokens(texts), encoding="utf-8-sig")
            write_json(tables_path, {"table_count": int(labels.get("table", 0)), "source": str(json_path)})
            write_json(layout_path, {"label_counts": dict(labels), "source": str(json_path)})
            source_name = Path(str(record.get("pdf") or record.get("file_name") or record.get("image") or record_id)).stem if isinstance(record, dict) else sample_id
            source = find_matching_source(source_name, roots)
            if not source:
                warnings.append(f"Missing PDF/image for generic record {record_id}")
                continue
            pdf = source_to_pdf(source, out_dir, sample_id)
            if not pdf:
                warnings.append(f"Could not convert source to PDF for {source}")
                continue
            expected: dict[str, Any] = {
                "min_confidence_grade": "low",
                "ground_truth": {
                    "text": relpath(text_path, out_dir),
                    "layout": relpath(layout_path, out_dir),
                },
                "require_artifacts": ["strategy_comparison.md", "confidence_report.md", "reading_notes.md"],
            }
            options: dict[str, Any] = {}
            if labels.get("table", 0):
                expected["ground_truth"]["tables"] = relpath(tables_path, out_dir)
                if args.require_table_structure_probe:
                    expected["min_table_structure_regions"] = 1
                    expected["require_artifacts"].append("tables/table_structure_probe_report.md")
                    options["table_structure_probe"] = True
                else:
                    expected["min_tables"] = 1
            sample: dict[str, Any] = {
                "id": sample_id,
                "pdf": relpath(pdf, out_dir),
                "class": "generic-json",
                "modes": [args.mode],
                "expected": expected,
            }
            if options:
                sample["options"] = options
            manifest["samples"].append(sample)
    return manifest, warnings


def write_reports(out_dir: Path, manifest: dict[str, Any], warnings: list[str]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "benchmark_manifest.json"
    write_json(manifest_path, manifest)
    lines = [
        "# PDF Benchmark Adapter Report",
        "",
        f"Created UTC: `{manifest.get('created_utc')}`",
        f"Manifest: `{manifest_path.resolve()}`",
        f"Samples: {len(manifest.get('samples', []))}",
        "",
        "## Warnings",
        "",
    ]
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- none")
    (out_dir / "adapter_report.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Adapt public/local benchmark data into q-pdf-reading manifests.")
    parser.add_argument("--kind", required=True, choices=["local-folder", "funsd", "ctdar", "generic-json"], help="Input dataset layout")
    parser.add_argument("--input", required=True, help="Input folder or JSON file")
    parser.add_argument("--out", required=True, help="Output folder for manifest and expected files")
    parser.add_argument("--pdf-root", help="Optional root containing matching PDFs/images")
    parser.add_argument("--name", help="Manifest name")
    parser.add_argument("--mode", default="robust", choices=["quick", "robust", "deep"], help="Mode to put in generated samples")
    parser.add_argument("--max-render-pages", type=int, default=3, help="Default max rendered pages in generated manifests")
    parser.add_argument("--render-dpi", type=int, default=144, help="Default render DPI in generated manifests")
    parser.add_argument("--max-table-pages", type=int, default=30, help="Default max table-scan pages in generated manifests")
    parser.add_argument("--max-table-probe-pages", type=int, default=5, help="Default max pages for rendered-image table-structure probing")
    parser.add_argument("--require-table-structure-probe", action="store_true", help="For cTDaR image samples, require at least one ruled table-structure region")
    parser.add_argument("--limit", type=int, help="Maximum annotation/PDF records to adapt")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    if args.kind == "local-folder":
        manifest, warnings = local_folder(args, out_dir)
    elif args.kind == "funsd":
        manifest, warnings = funsd(args, out_dir)
    elif args.kind == "ctdar":
        manifest, warnings = ctdar(args, out_dir)
    else:
        manifest, warnings = generic_json(args, out_dir)
    write_reports(out_dir, manifest, warnings)
    print(f"Wrote manifest: {out_dir / 'benchmark_manifest.json'}")
    print(f"Samples: {len(manifest.get('samples', []))}")
    print(f"Warnings: {len(warnings)}")
    return 0 if manifest.get("samples") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
