#!/usr/bin/env python3
"""Fuse PDF extraction, OCR, and visual evidence into a confidence report."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-/.]{2,}|[\u4e00-\u9fff]{2,}")
NOISE_RE = re.compile(r"[\u00c3\u00c2\ufffd]|\u00e5\u00ae|\u00e9\u00aa|\u00e6\u2030|w\s*x\s*y|[A-Za-z]\s+[A-Za-z]\s+[A-Za-z]", re.IGNORECASE)
STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "page", "conf", "engine", "created", "utc"}


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(read_text(path))


def tokens(text: str, limit: int = 400) -> set[str]:
    raw = [match.group(0).lower().strip(".,;:()[]{}<>\"'") for match in TOKEN_RE.finditer(text)]
    raw = [item for item in raw if item and item not in STOPWORDS and len(item) >= 2]
    counts = Counter(raw)
    return {token for token, _ in counts.most_common(limit)}


def domain_like(token: str) -> bool:
    return bool(re.search(r"[A-Za-z]", token) and (re.search(r"\d|[-_/]", token) or token.upper() == token))


def source_metrics(path: Path) -> dict[str, Any]:
    text = read_text(path)
    return {
        "path": str(path.resolve()),
        "characters": len(text),
        "tokens": sorted(tokens(text)),
        "noise_hits": len(NOISE_RE.findall(text)),
        "heading_like_lines": len(re.findall(r"^\s{0,3}(?:#{1,6}\s+|\d+(?:\.\d+)*\s+)", text, flags=re.MULTILINE)),
    }


def collect_sources(pack_dir: Path) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    extracted = pack_dir / "extracted_text.md"
    if extracted.exists():
        sources["selected_extracted_text"] = source_metrics(extracted)
    strategies_dir = pack_dir / "strategies"
    if strategies_dir.exists():
        for path in sorted(strategies_dir.glob("*.md")):
            sources[path.stem] = source_metrics(path)
    ocr_text = pack_dir / "ocr" / "ocr_text.md"
    if ocr_text.exists():
        sources["rapidocr_pages"] = source_metrics(ocr_text)
    return sources


def jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def consensus(sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
    token_sources: dict[str, list[str]] = defaultdict(list)
    for name, metrics in sources.items():
        for token in metrics["tokens"]:
            token_sources[token].append(name)
    supported = {token: names for token, names in token_sources.items() if len(names) >= 2}
    single = {token: names for token, names in token_sources.items() if len(names) == 1}
    domain_single = sorted(token for token in single if domain_like(token))[:80]
    source_agreement = {}
    for name, metrics in sources.items():
        own = set(metrics["tokens"])
        overlaps = [jaccard(own, set(other["tokens"])) for other_name, other in sources.items() if other_name != name]
        source_agreement[name] = round(sum(overlaps) / len(overlaps), 4) if overlaps else 1.0
    return {
        "supported_token_count": len(supported),
        "single_source_token_count": len(single),
        "domain_single_source_tokens": domain_single,
        "source_agreement": source_agreement,
        "sample_supported_tokens": sorted(supported)[:80],
    }


def ocr_uncertainty(pack_dir: Path, low_conf: float) -> dict[str, Any]:
    data = load_json(pack_dir / "ocr" / "ocr_results.json")
    if not data:
        return {"available": False}
    low_lines = []
    weak_pages = []
    for record in data.get("records", []):
        page = record.get("page")
        avg = float(record.get("avg_score", 0.0) or 0.0)
        line_count = int(record.get("line_count", 0) or 0)
        if avg < low_conf or line_count == 0:
            weak_pages.append({"page": page, "avg_score": avg, "line_count": line_count})
        for text, score in zip(record.get("text", []), record.get("scores", [])):
            score_f = float(score)
            if score_f < low_conf:
                low_lines.append({"page": page, "score": round(score_f, 4), "text": text})
    return {
        "available": True,
        "engine": data.get("engine"),
        "page_count": data.get("page_count"),
        "total_lines": data.get("total_lines"),
        "avg_score": data.get("avg_score", 0.0),
        "low_confidence_threshold": low_conf,
        "low_confidence_line_count": len(low_lines),
        "low_confidence_lines": low_lines[:120],
        "weak_pages": weak_pages,
    }


def confidence_grade(strategy_data: dict[str, Any], source_consensus: dict[str, Any], ocr: dict[str, Any]) -> dict[str, Any]:
    selection = strategy_data.get("selection", {})
    strategies = strategy_data.get("strategies", [])
    selected_name = selection.get("selected")
    selected = next((item for item in strategies if item.get("name") == selected_name), {})
    combined = int(selected.get("combined_score", 0) or 0)
    cross = int(selected.get("cross_validation_score", 0) or 0)
    agreement = source_consensus.get("source_agreement", {}).get(f"strategy_{selected_name}", 0.0)
    if not agreement:
        agreement = source_consensus.get("source_agreement", {}).get("selected_extracted_text", 0.0)
    ocr_available = bool(ocr.get("available"))
    ocr_avg = float(ocr.get("avg_score", 0.0) or 0.0)
    low_count = int(ocr.get("low_confidence_line_count", 0) or 0)
    ocr_ok = (not ocr_available) or (ocr_avg >= 0.9 and low_count <= 30)
    ocr_points = 10 if not ocr_available else 15 if ocr_avg >= 0.95 else 10 if ocr_avg >= 0.9 else 5
    low_line_penalty = 5 if low_count > 30 else 0
    points = (
        min(45, int(combined * 0.6))
        + min(20, int(cross * 0.2))
        + min(20, int(float(agreement) * 20))
        + ocr_points
        - low_line_penalty
    )
    routing = strategy_data.get("routing", {})
    tables = routing.get("tables", {}) if isinstance(routing.get("tables", {}), dict) else {}
    table_probe = routing.get("table_structure_probe", {}) if isinstance(routing.get("table_structure_probe", {}), dict) else {}
    table_evidence = int(tables.get("tables_found", 0) or 0) > 0 or (
        int(table_probe.get("candidate_table_regions", 0) or 0) > 0
        and int(table_probe.get("max_grid_strength", 0) or 0) >= 45
    )
    selected_metrics = selected.get("metrics", {}) if isinstance(selected, dict) else {}
    selected_chars = int(selected_metrics.get("characters", 0) or 0)
    selected_noise = int(selected_metrics.get("mojibake_hits", 0) or 0)
    if table_evidence:
        points += 8
        if selected_chars >= 1000 and selected_noise == 0:
            points = max(points, 65)
        elif selected_chars >= 300 and selected_noise == 0:
            points = max(points, 58)
    if routing.get("pdf_type") in {"scanned-or-image-only", "scanned-or-image-heavy"} and ocr_available:
        weak_pages = len(ocr.get("weak_pages", []) or [])
        scanned_penalty = 0
        if low_count > 50:
            scanned_penalty += 20
        elif low_count > 20:
            scanned_penalty += 12
        elif low_count > 5:
            scanned_penalty += 5
        scanned_penalty += min(10, weak_pages * 3)
        ocr_primary_points = int(ocr_avg * 70) + min(15, int(combined * 0.3)) - scanned_penalty
        points = max(points, ocr_primary_points)
    grade = "high" if points >= 80 else "medium" if points >= 60 else "low"
    return {
        "grade": grade,
        "score": points,
        "selected_strategy": selected_name,
        "selected_combined_score": combined,
        "selected_cross_validation_score": cross,
        "selected_source_agreement": round(float(agreement), 4),
        "ocr_ok": ocr_ok,
        "ocr_points": ocr_points,
        "low_line_penalty": low_line_penalty,
        "table_evidence": table_evidence,
    }


def recommended_actions(grade: dict[str, Any], consensus_data: dict[str, Any], ocr: dict[str, Any], strategy_data: dict[str, Any]) -> list[str]:
    actions = []
    routing = strategy_data.get("routing", {})
    if grade["grade"] != "high":
        actions.append("Inspect rendered sample pages before using uncertain claims.")
    if ocr.get("available") and (float(ocr.get("avg_score", 1.0) or 1.0) < 0.9 or int(ocr.get("low_confidence_line_count", 0) or 0) > 20):
        actions.append("Rerun OCR on weak pages at higher DPI (216 or 300) and compare low-confidence lines.")
    if routing.get("pdf_type") in {"scanned-or-image-only", "scanned-or-image-heavy"} and not ocr.get("available"):
        actions.append("Run local OCR before summarizing; text extraction alone is not sufficient.")
    if routing.get("pdf_type") == "schematic-or-diagram":
        actions.append("Use rendered pages as primary evidence; extracted text may omit wiring, symbols, and visual relationships.")
    if routing.get("pdf_type") == "table-or-technical-report":
        tables = routing.get("tables", {})
        if not tables or int(tables.get("tables_found", 0) or 0) == 0:
            actions.append("Manually inspect rendered table pages or use a table-aware backend before relying on table values.")
    if routing.get("pdf_type") == "encrypted-readable":
        actions.append("Validate completeness because the PDF has encryption/permission flags even though local text extraction succeeded.")
    if consensus_data.get("single_source_token_count", 0) > consensus_data.get("supported_token_count", 0):
        actions.append("Review domain-like single-source tokens; they may be OCR mistakes or useful figure labels.")
    actions.append("Use selected extracted text for narrative, OCR text for image/page labels, and page PNGs for visual verification.")
    return actions


def write_report(pack_dir: Path, out_dir: Path, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "confidence_report.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    grade = payload["grade"]
    ocr = payload["ocr_uncertainty"]
    lines = [
        "# PDF Confidence Fusion Report",
        "",
        f"Created UTC: `{payload['created_utc']}`",
        f"Pack: `{pack_dir.resolve()}`",
        "",
        "## Overall",
        "",
        f"- Confidence grade: **{grade['grade']}**",
        f"- Confidence score: {grade['score']}/100",
        f"- Selected strategy: `{grade.get('selected_strategy')}`",
        f"- Selected combined score: {grade.get('selected_combined_score')}",
        f"- Selected cross-validation score: {grade.get('selected_cross_validation_score')}",
        "",
        "## OCR",
        "",
    ]
    if ocr.get("available"):
        lines.extend(
            [
                f"- Engine: `{ocr.get('engine')}`",
                f"- Pages/images: {ocr.get('page_count')}",
                f"- Total lines: {ocr.get('total_lines')}",
                f"- Average confidence: {ocr.get('avg_score')}",
                f"- Low-confidence lines: {ocr.get('low_confidence_line_count')} below {ocr.get('low_confidence_threshold')}",
            ]
        )
    else:
        lines.append("- OCR output not available.")
    lines.extend(["", "## Source Agreement", ""])
    for name, value in payload["consensus"]["source_agreement"].items():
        lines.append(f"- {name}: {value}")
    lines.extend(["", "## Domain-Like Single-Source Tokens", ""])
    for token in payload["consensus"]["domain_single_source_tokens"][:40]:
        lines.append(f"- `{token}`")
    if ocr.get("available") and ocr.get("low_confidence_lines"):
        lines.extend(["", "## Low-Confidence OCR Lines", ""])
        for item in ocr["low_confidence_lines"][:40]:
            lines.append(f"- Page {item['page']}, {item['score']}: {item['text']}")
    lines.extend(["", "## Recommended Actions", ""])
    for action in payload["recommended_actions"]:
        lines.append(f"- {action}")
    (out_dir / "confidence_report.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Fuse extraction/OCR confidence for a PDF reading pack.")
    parser.add_argument("pack_dir", help="Reading pack folder")
    parser.add_argument("--out", help="Output folder, defaults to pack_dir")
    parser.add_argument("--low-conf", type=float, default=0.85, help="Low OCR line confidence threshold")
    args = parser.parse_args(argv)

    pack_dir = Path(args.pack_dir)
    out_dir = Path(args.out) if args.out else pack_dir
    strategy_data = load_json(pack_dir / "strategy_comparison.json")
    sources = collect_sources(pack_dir)
    consensus_data = consensus(sources)
    ocr = ocr_uncertainty(pack_dir, args.low_conf)
    grade = confidence_grade(strategy_data, consensus_data, ocr)
    payload = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "pack_dir": str(pack_dir.resolve()),
        "sources": sources,
        "consensus": consensus_data,
        "ocr_uncertainty": ocr,
        "grade": grade,
        "recommended_actions": recommended_actions(grade, consensus_data, ocr, strategy_data),
    }
    write_report(pack_dir, out_dir, payload)
    print(f"Confidence grade: {grade['grade']} ({grade['score']}/100)")
    print(f"Wrote: {out_dir / 'confidence_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
