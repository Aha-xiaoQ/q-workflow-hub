#!/usr/bin/env python3
"""Route a PDF through multiple local reading strategies and pick a primary output."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pdf_confidence_fusion  # noqa: E402
import pdf_extract_text  # noqa: E402
import pdf_ocr_pages  # noqa: E402
import pdf_table_structure_probe  # noqa: E402
import pdf_to_reading_pack  # noqa: E402
import pdf_triage  # noqa: E402


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}")
MOJIBAKE_RE = re.compile(r"[\u00c3\u00c2\ufffd]|\u00e5\u00ae|\u00e9\u00aa|\u00e6\u2030|w\s*x\s*y", re.IGNORECASE)


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str, limit: int = 250) -> set[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    stop = {"the", "and", "for", "with", "from", "this", "that", "page"}
    counts = Counter(token for token in tokens if token not in stop)
    return {token for token, _ in counts.most_common(limit)}


def text_quality(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)
    chars = len(normalized)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", normalized))
    ascii_word = len(re.findall(r"[A-Za-z0-9]", normalized))
    mojibake = len(MOJIBAKE_RE.findall(normalized))
    headings = len(re.findall(r"^\s{0,3}#{1,6}\s+|^\s{0,3}\d+(?:\.\d+)*\s+[\u4e00-\u9fffA-Za-z]", text, flags=re.MULTILINE))
    code_blocks = len(re.findall(r"```", text)) // 2
    pictures = len(re.findall(r"picture|image|figure|图片|图\s*\d*", text, flags=re.IGNORECASE))
    token_count = len(token_set(text))
    if chars == 0:
        quality = 0
    else:
        content_score = min(35, chars // 250)
        language_score = min(20, (cjk + ascii_word) * 20 // max(chars, 1))
        heading_score = min(15, headings * 2)
        code_score = min(5, code_blocks)
        image_signal = min(5, pictures)
        token_score = min(10, token_count // 20)
        noise_penalty = min(25, mojibake * 5)
        quality = max(0, content_score + language_score + heading_score + code_score + image_signal + token_score - noise_penalty)
    return {
        "characters": chars,
        "cjk_characters": cjk,
        "ascii_word_characters": ascii_word,
        "mojibake_hits": mojibake,
        "heading_like_lines": headings,
        "code_blocks": code_blocks,
        "visual_markers": pictures,
        "token_count": token_count,
        "quality_score": quality,
    }


def scan_with_pymupdf(pdf: Path) -> dict[str, Any] | None:
    if not importlib.util.find_spec("pymupdf"):
        return None
    import pymupdf  # type: ignore

    doc = pymupdf.open(str(pdf))
    page_stats = []
    total_chars = 0
    total_images = 0
    total_drawings = 0
    table_hint_pages = 0
    for index in range(doc.page_count):
        page = doc.load_page(index)
        text = page.get_text("text") or ""
        images = len(page.get_images(full=True))
        try:
            drawings = len(page.get_drawings())
        except Exception:
            drawings = 0
        table_hints = len(re.findall(r"\btable\b|表\s*\d|^\s*\|", text, flags=re.IGNORECASE | re.MULTILINE))
        page_stats.append(
            {
                "page": index + 1,
                "text_characters": len(normalize_text(text)),
                "images": images,
                "drawings": drawings,
                "table_hints": table_hints,
            }
        )
        total_chars += len(normalize_text(text))
        total_images += images
        total_drawings += drawings
        if table_hints:
            table_hint_pages += 1
    page_count = doc.page_count
    doc.close()
    avg_chars = total_chars / max(page_count, 1)
    image_pages = sum(1 for item in page_stats if item["images"] > 0)
    drawing_pages = sum(1 for item in page_stats if item["drawings"] > 20)
    return {
        "engine": "pymupdf",
        "page_count": page_count,
        "total_text_characters": total_chars,
        "avg_text_characters_per_page": round(avg_chars, 1),
        "total_images": total_images,
        "image_pages": image_pages,
        "total_drawings": total_drawings,
        "drawing_heavy_pages": drawing_pages,
        "table_hint_pages": table_hint_pages,
        "sample_pages": page_stats[: min(10, len(page_stats))],
    }


def classify_pdf(scan: dict[str, Any] | None, triage_record: dict[str, Any]) -> dict[str, Any]:
    signals = triage_record["signals"]
    siblings = triage_record["siblings"]
    reasons = []
    if siblings["exact_sidecars"] or siblings["loose_sidecars"]:
        reasons.append("source-native sidecar exists")
    if signals["encrypted"]:
        if scan and scan.get("total_text_characters", 0) > 0:
            reasons.append("PDF has encryption/permission flags but readable text layer")
        else:
            return {"pdf_type": "encrypted", "recommended_strategy": "unlock-or-password", "reasons": ["PDF is encrypted"]}
    if scan:
        page_count = scan["page_count"]
        avg = scan["avg_text_characters_per_page"]
        image_ratio = scan["image_pages"] / max(page_count, 1)
        drawing_ratio = scan["drawing_heavy_pages"] / max(page_count, 1)
        if signals["encrypted"]:
            return {"pdf_type": "encrypted-readable", "recommended_strategy": "layout-markdown-plus-permission-warning", "reasons": reasons + ["validate extraction permission and completeness"]}
        if drawing_ratio > 0.5 and scan["total_drawings"] > max(1000, page_count * 150):
            if page_count <= 3 or avg < 300 or image_ratio < 0.2:
                return {"pdf_type": "schematic-or-diagram", "recommended_strategy": "render-pages-primary", "reasons": reasons + ["many vector drawings"]}
            return {"pdf_type": "illustrated-manual-or-slide-export", "recommended_strategy": "pymupdf4llm-plus-render", "reasons": reasons + ["many vector drawings", "multi-page text and visuals both important"]}
        if avg < 50 and image_ratio > 0.6:
            return {"pdf_type": "scanned-or-image-only", "recommended_strategy": "render-plus-ocr", "reasons": reasons + ["low text density", "most pages contain images"]}
        if drawing_ratio > 0.5 and avg < 250:
            return {"pdf_type": "schematic-or-diagram", "recommended_strategy": "render-pages-primary", "reasons": reasons + ["many vector drawings", "limited text"]}
        if image_ratio > 0.4 and avg > 120:
            return {"pdf_type": "illustrated-manual-or-slide-export", "recommended_strategy": "pymupdf4llm-plus-render", "reasons": reasons + ["text and visuals both important"]}
        if scan["table_hint_pages"] > 0:
            return {"pdf_type": "table-or-technical-report", "recommended_strategy": "layout-markdown-plus-table-check", "reasons": reasons + ["table hints detected"]}
        if avg > 300:
            return {"pdf_type": "digital-text", "recommended_strategy": "layout-markdown", "reasons": reasons + ["strong text layer"]}
    if signals.get("scanned_or_image_heavy_hint"):
        return {"pdf_type": "scanned-or-image-heavy", "recommended_strategy": "render-plus-ocr", "reasons": reasons + ["binary scan suggests image-heavy PDF"]}
    if signals.get("text_operator_count_estimate", 0) > 0:
        return {"pdf_type": "digital-text-unknown-layout", "recommended_strategy": "compare-local-text-extractors", "reasons": reasons + ["text operators detected"]}
    return {"pdf_type": "unknown", "recommended_strategy": "render-and-install-parser", "reasons": reasons + ["insufficient readable signals"]}


def promote_table_route_from_probe(routing: dict[str, Any], table_probe: dict[str, Any]) -> bool:
    if not table_probe or table_probe.get("status") != "ok":
        return False
    candidate_regions = int(table_probe.get("candidate_table_regions", 0) or 0)
    grid_strength = int(table_probe.get("max_grid_strength", 0) or 0)
    grid_cells = int(table_probe.get("estimated_grid_cells", 0) or 0)
    if candidate_regions <= 0 or grid_strength < 45 or grid_cells < 12:
        return False
    if routing.get("pdf_type") in {"schematic-or-diagram", "scanned-or-image-only", "scanned-or-image-heavy", "encrypted"}:
        return False
    if routing.get("pdf_type") != "table-or-technical-report":
        routing["pdf_type"] = "table-or-technical-report"
        routing["recommended_strategy"] = "layout-markdown-plus-table-check"
    reasons = routing.setdefault("reasons", [])
    reason = "table-structure probe detected ruled table regions"
    if reason not in reasons:
        reasons.append(reason)
    return True


def run_pymupdf4llm(pdf: Path, out_dir: Path) -> dict[str, Any] | None:
    if not importlib.util.find_spec("pymupdf4llm"):
        return None
    import pymupdf4llm  # type: ignore

    target = out_dir / "strategy_pymupdf4llm.md"
    try:
        result = pymupdf4llm.to_markdown(str(pdf), page_chunks=False)
        text = "\n\n".join(str(item) for item in result) if isinstance(result, list) else str(result)
        target.write_text(text, encoding="utf-8-sig")
        metrics = text_quality(text)
        return {"name": "pymupdf4llm", "status": "ok", "path": str(target.resolve()), "metrics": metrics}
    except Exception as exc:
        return {"name": "pymupdf4llm", "status": "failed", "error": str(exc), "metrics": text_quality("")}


def run_pymupdf_text(pdf: Path, out_dir: Path) -> dict[str, Any] | None:
    if not importlib.util.find_spec("pymupdf"):
        return None
    import pymupdf  # type: ignore

    target = out_dir / "strategy_pymupdf_text.md"
    try:
        doc = pymupdf.open(str(pdf))
        parts = []
        for index in range(doc.page_count):
            text = doc.load_page(index).get_text("text") or ""
            parts.append(f"\n\n<!-- page {index + 1} -->\n{text.strip()}")
        doc.close()
        combined = "\n".join(parts)
        target.write_text(combined, encoding="utf-8-sig")
        return {"name": "pymupdf_text", "status": "ok", "path": str(target.resolve()), "metrics": text_quality(combined)}
    except Exception as exc:
        return {"name": "pymupdf_text", "status": "failed", "error": str(exc), "metrics": text_quality("")}


def run_stdlib(pdf: Path, out_dir: Path) -> dict[str, Any]:
    target = out_dir / "strategy_stdlib_fallback.md"
    try:
        data = pdf.read_bytes()
        objects = pdf_extract_text.extract_objects(data)
        streams = pdf_extract_text.extract_streams(objects)
        cmap = pdf_extract_text.parse_cmaps(streams)
        text, _ = pdf_extract_text.extract_text_from_streams(streams, cmap)
        target.write_text(text or "_No text extracted by stdlib fallback._\n", encoding="utf-8-sig")
        return {"name": "stdlib_fallback", "status": "ok", "path": str(target.resolve()), "metrics": text_quality(text)}
    except Exception as exc:
        return {"name": "stdlib_fallback", "status": "failed", "error": str(exc), "metrics": text_quality("")}


def compare_strategies(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ok = [item for item in results if item.get("status") == "ok" and item.get("path")]
    texts = {}
    for item in ok:
        try:
            texts[item["name"]] = Path(item["path"]).read_text(encoding="utf-8-sig", errors="replace")
        except Exception:
            texts[item["name"]] = ""
    token_sets = {name: token_set(text) for name, text in texts.items()}
    for item in results:
        if item.get("status") != "ok":
            item["cross_validation_score"] = 0
            item["combined_score"] = item["metrics"]["quality_score"]
            continue
        name = item["name"]
        overlaps = []
        for other_name, other_tokens in token_sets.items():
            if other_name == name:
                continue
            own = token_sets.get(name, set())
            union = len(own | other_tokens)
            overlap = len(own & other_tokens) / union if union else 0
            overlaps.append(overlap)
        cross = int(round((sum(overlaps) / len(overlaps)) * 100)) if overlaps else 50
        item["cross_validation_score"] = cross
        item["combined_score"] = int(round(item["metrics"]["quality_score"] * 0.75 + cross * 0.25))
    return results


def select_strategy(results: list[dict[str, Any]], routing: dict[str, Any]) -> dict[str, Any]:
    ok = [item for item in results if item.get("status") == "ok" and item["metrics"]["characters"] > 0]
    if not ok:
        return {"selected": None, "reason": "no text extraction strategy produced content"}
    by_score = sorted(ok, key=lambda item: (item.get("combined_score", 0), item["metrics"]["characters"]), reverse=True)
    selected = by_score[0]
    if routing["recommended_strategy"] in {"render-plus-ocr", "render-pages-primary"}:
        return {
            "selected": selected["name"],
            "reason": "text extraction is secondary; visual/OCR route is required for this PDF type",
            "path": selected["path"],
        }
    return {"selected": selected["name"], "reason": "highest combined quality and cross-validation score", "path": selected["path"]}


def write_reading_notes(
    out_dir: Path,
    pdf: Path,
    routing: dict[str, Any],
    selection: dict[str, Any],
    visuals: dict[str, Any],
    tables: dict[str, Any],
    table_probe: dict[str, Any],
) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        "# PDF Reading Notes",
        "",
        f"Created UTC: `{now}`",
        f"PDF: `{pdf.resolve()}`",
        f"PDF type: `{routing.get('pdf_type')}`",
        f"Recommended strategy: `{routing.get('recommended_strategy')}`",
        f"Selected text strategy: `{selection.get('selected')}`",
        "",
        "## Evidence Priority",
        "",
    ]
    pdf_type = routing.get("pdf_type")
    if pdf_type in {"schematic-or-diagram", "scanned-or-image-only", "scanned-or-image-heavy"}:
        lines.append("- Treat rendered pages as primary evidence; extracted text is only labels or search aid.")
    elif pdf_type in {"table-or-technical-report"}:
        lines.append("- Treat table extraction/report and rendered pages as required evidence for numeric/table claims.")
    elif pdf_type == "encrypted-readable":
        lines.append("- Text is readable despite encryption/permission flags; validate completeness before final claims.")
    else:
        lines.append("- Use selected extracted text for narrative claims, then spot-check rendered pages for layout-sensitive content.")
    lines.extend(["", "## Artifacts", ""])
    if visuals:
        lines.append(f"- Rendered pages: {visuals.get('rendered_pages', 0)}/{visuals.get('total_pages', 0)}")
        lines.append(f"- Extracted images: {visuals.get('extracted_images', 0)}")
        if visuals.get("visual_warning"):
            lines.append(f"- Visual warning: {visuals['visual_warning']}")
    else:
        lines.append("- Rendered pages: not available")
    if tables:
        lines.append(f"- Tables found: {tables.get('tables_found', 0)}")
        if tables.get("warning"):
            lines.append(f"- Table warning: {tables['warning']}")
    if table_probe:
        lines.append(f"- Table-structure probe regions: {table_probe.get('candidate_table_regions', 0)}")
        if table_probe.get("warning"):
            lines.append(f"- Table-structure warning: {table_probe['warning']}")
    lines.extend(
        [
            "",
            "## Validation Before Use",
            "",
            "- Read `strategy_comparison.md` and `confidence_report.md` before summarizing.",
            "- For low or medium confidence, inspect sample page PNGs.",
            "- For table, schematic, form, or slide claims, cite page/figure/table evidence rather than text alone.",
        ]
    )
    (out_dir / "reading_notes.md").write_text("\n".join(lines), encoding="utf-8-sig")


def write_reports(out_dir: Path, pdf: Path, scan: dict[str, Any] | None, routing: dict[str, Any], results: list[dict[str, Any]], selection: dict[str, Any]) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "created_utc": now,
        "pdf": str(pdf.resolve()),
        "scan": scan,
        "routing": routing,
        "strategies": results,
        "selection": selection,
    }
    (out_dir / "strategy_comparison.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    lines = [
        "# PDF Strategy Comparison",
        "",
        f"Created UTC: `{now}`",
        f"PDF: `{pdf.resolve()}`",
        "",
        "## Lightweight Scan",
        "",
        f"- Type: `{routing['pdf_type']}`",
        f"- Recommended strategy: `{routing['recommended_strategy']}`",
        f"- Reasons: {', '.join(routing['reasons']) if routing['reasons'] else 'none'}",
    ]
    if scan:
        lines.extend(
            [
                f"- Pages: {scan['page_count']}",
                f"- Avg text chars/page: {scan['avg_text_characters_per_page']}",
                f"- Image pages: {scan['image_pages']}",
                f"- Drawing-heavy pages: {scan['drawing_heavy_pages']}",
                f"- Table-hint pages: {scan['table_hint_pages']}",
            ]
        )
    lines.extend(["", "## Strategy Scores", ""])
    for item in sorted(results, key=lambda row: row.get("combined_score", 0), reverse=True):
        metrics = item["metrics"]
        lines.append(
            f"- {item['name']}: status={item['status']}, combined={item.get('combined_score', 0)}, "
            f"quality={metrics['quality_score']}, cross={item.get('cross_validation_score', 0)}, "
            f"chars={metrics['characters']}, noise={metrics['mojibake_hits']}"
        )
    lines.extend(
        [
            "",
            "## Selection",
            "",
            f"- Selected: `{selection.get('selected')}`",
            f"- Reason: {selection.get('reason')}",
            f"- Path: `{selection.get('path', '')}`",
            "",
            "## Fallback Rule",
            "",
            "- If selected text is weak or the PDF type is visual-first, inspect `pages/` and `figures/` before summarizing.",
            "- If all local text strategies fail, use page rendering plus OCR/layout tooling after data-sensitivity approval.",
        ]
    )
    (out_dir / "strategy_comparison.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Compare available local PDF reading strategies and select a primary output.")
    parser.add_argument("pdf", help="PDF file")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--render-pages", action="store_true", help="Render page PNGs and extract embedded images with PyMuPDF")
    parser.add_argument("--ocr-pages", action="store_true", help="Run RapidOCR over rendered pages and add OCR as a fallback strategy")
    parser.add_argument("--ocr-auto", action="store_true", help="Run OCR only when routing says the PDF is visual/image-first and RapidOCR is available")
    parser.add_argument("--max-render-pages", type=int, default=30)
    parser.add_argument("--render-dpi", type=int, default=144)
    parser.add_argument("--max-table-pages", type=int, default=80, help="Maximum pages to scan with table-aware extraction")
    parser.add_argument("--table-structure-probe", action="store_true", help="Probe rendered pages for ruled table structure evidence")
    parser.add_argument("--max-table-probe-pages", type=int, default=5, help="Maximum rendered pages/images to probe for ruled table structure")
    args = parser.parse_args(argv)

    pdf = Path(args.pdf)
    out_dir = Path(args.out)
    strategies_dir = out_dir / "strategies"
    strategies_dir.mkdir(parents=True, exist_ok=True)

    tools = pdf_triage.tool_inventory()
    triage_record = pdf_triage.build_record(pdf, tools)
    pdf_triage.write_reports(out_dir, [triage_record], tools)
    scan = scan_with_pymupdf(pdf)
    routing = classify_pdf(scan, triage_record)

    results = []
    for runner in (run_pymupdf4llm, run_pymupdf_text):
        result = runner(pdf, strategies_dir)
        if result:
            results.append(result)
    results.append(run_stdlib(pdf, strategies_dir))
    results = compare_strategies(results)
    selection = select_strategy(results, routing)
    if selection.get("path"):
        shutil.copyfile(selection["path"], out_dir / "extracted_text.md")
    if args.render_pages and importlib.util.find_spec("pymupdf"):
        visuals = pdf_to_reading_pack.export_visuals_with_pymupdf(pdf, out_dir, args.max_render_pages, args.render_dpi)
    else:
        visuals = {}
    visual_first = routing["recommended_strategy"] in {"render-plus-ocr", "render-pages-primary"}
    should_run_ocr = args.ocr_pages or (args.ocr_auto and visual_first)
    if should_run_ocr and importlib.util.find_spec("rapidocr"):
        ocr_target = Path(visuals.get("pages_dir", "")) if visuals else pdf
        ocr_out = out_dir / "ocr"
        if ocr_target.exists():
            images = pdf_ocr_pages.discover_images(ocr_target)
        else:
            images = []
        if not images and pdf.suffix.lower() == ".pdf":
            images = pdf_ocr_pages.render_pdf_pages(pdf, ocr_out / "ocr_pages", args.max_render_pages, args.render_dpi)
        from rapidocr import RapidOCR  # type: ignore

        ocr = RapidOCR()
        records = []
        for idx, image_path in enumerate(images[: args.max_render_pages], start=1):
            result = ocr(str(image_path))
            records.append(pdf_ocr_pages.result_to_record(idx, image_path, result))
        ocr_out.mkdir(parents=True, exist_ok=True)
        pdf_ocr_pages.write_outputs(ocr_out, records, ocr_target if ocr_target.exists() else pdf, "rapidocr")
        ocr_text = ocr_out / "ocr_text.md"
        if ocr_text.exists():
            text = ocr_text.read_text(encoding="utf-8-sig", errors="replace")
            ocr_result = {
                "name": "rapidocr_pages",
                "status": "ok",
                "path": str(ocr_text.resolve()),
                "metrics": text_quality(text),
            }
            results.append(ocr_result)
            results = compare_strategies(results)
            selection = select_strategy(results, routing)
            if selection.get("path") and Path(selection["path"]).exists():
                shutil.copyfile(selection["path"], out_dir / "extracted_text.md")
            routing["ocr"] = {"engine": "rapidocr", "pages": len(records), "out_dir": str(ocr_out.resolve())}
    elif should_run_ocr:
        routing["ocr"] = {"engine": "rapidocr", "status": "missing", "warning": "RapidOCR is not installed; OCR fallback was skipped."}
    tables = {}
    table_probe = {}
    should_probe_tables = args.table_structure_probe
    if should_probe_tables and visuals.get("pages_dir"):
        probe_images = pdf_table_structure_probe.discover_images(Path(visuals["pages_dir"]))[: args.max_table_probe_pages]
        if probe_images:
            table_probe = pdf_table_structure_probe.probe_images(probe_images, out_dir / "tables")
            routing["table_structure_probe"] = table_probe
            promote_table_route_from_probe(routing, table_probe)
    if importlib.util.find_spec("pymupdf") and routing["pdf_type"] in {"table-or-technical-report", "encrypted-readable"}:
        tables = pdf_to_reading_pack.export_tables_with_pymupdf(pdf, out_dir, args.max_table_pages)
        routing["tables"] = tables
    if visuals:
        routing["visuals"] = visuals
    write_reports(out_dir, pdf, scan, routing, results, selection)
    pdf_confidence_fusion.main([str(out_dir)])
    write_reading_notes(out_dir, pdf, routing, selection, visuals, tables, table_probe)
    print(f"Wrote PDF strategy comparison: {out_dir}")
    print(f"PDF type: {routing['pdf_type']}")
    print(f"Selected: {selection.get('selected')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
