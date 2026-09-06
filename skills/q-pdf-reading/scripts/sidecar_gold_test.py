#!/usr/bin/env python3
"""Score a PDF reading pack against a same-content Markdown sidecar."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pdf_triage  # noqa: E402

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{3,}|[\u4e00-\u9fff]{2,}")
STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "page", "http", "https"}


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


def find_sidecar(pdf: Path) -> Path | None:
    for suffix in (".md", ".markdown", ".txt"):
        candidate = pdf.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def candidate_terms(text: str, limit: int = 12) -> dict[str, int]:
    tokens = [match.group(0) for match in TOKEN_RE.finditer(text)]
    filtered = [token for token in tokens if token.lower() not in STOPWORDS]
    return dict(Counter(filtered).most_common(limit))


def analyze_markdown(markdown: Path) -> dict[str, Any]:
    text = read_text(markdown)
    headings = []
    for match in re.finditer(r"^(#{1,6})\s+(.+)$", text, flags=re.MULTILINE):
        headings.append({"level": len(match.group(1)), "title": match.group(2).strip()})
    images = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
    links = re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text)
    code_fences = len(re.findall(r"^```", text, flags=re.MULTILINE)) // 2
    terms = candidate_terms(text)
    return {
        "path": str(markdown.resolve()),
        "characters": len(text),
        "headings": headings,
        "heading_count": len(headings),
        "images": images,
        "image_count": len(images),
        "links": links,
        "link_count": len(links),
        "code_fence_count": code_fences,
        "key_terms": terms,
    }


def score(record: dict[str, Any], md: dict[str, Any], pack_dir: Path) -> tuple[int, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, points: int, earned: int, detail: str) -> None:
        checks.append({"name": name, "points": points, "earned": earned, "detail": detail})

    exact_sidecars = [Path(p).resolve() for p in record["siblings"]["exact_sidecars"]]
    sidecar_found = Path(md["path"]).resolve() in exact_sidecars
    add("same-content sidecar discovered", 25, 25 if sidecar_found else 0, "exact Markdown sidecar found" if sidecar_found else "exact Markdown sidecar not found")

    readable = md["characters"] > 1000 and md["heading_count"] >= 4
    add("sidecar content readable", 15, 15 if readable else 5 if md["characters"] > 0 else 0, f"{md['characters']} chars, {md['heading_count']} headings")

    image_dir_count = sum(item.get("image_count", 0) for item in record["siblings"]["image_dirs"])
    image_score = 15 if image_dir_count >= md["image_count"] and md["image_count"] else 10 if image_dir_count else 0
    add("visual assets discovered", 15, image_score, f"{image_dir_count} nearby images, {md['image_count']} Markdown image refs")

    lane = " | ".join(record["recommended_lane"])
    lane_ok = "source-native sidecar first" in lane
    add("correct lane selected", 15, 15 if lane_ok else 0, lane)

    pack_files = ["source_freeze.json", "triage_report.md", "page_inventory.csv"]
    existing = [name for name in pack_files if (pack_dir / name).exists()]
    add("reading pack files created", 10, int(10 * len(existing) / len(pack_files)), f"found {existing}")

    important_terms = [term for term, count in md["key_terms"].items() if count > 0]
    add("gold content map built", 10, 10 if len(important_terms) >= 5 else len(important_terms), f"terms present: {important_terms}")

    no_text_parser = "no PDF extraction library detected" in lane
    honest_warning = no_text_parser and any("degraded" in item for item in record["recommended_lane"])
    add("capability gap reported honestly", 10, 10 if honest_warning else 5 if lane_ok else 0, "local parser gap recorded" if honest_warning else "no degraded warning")

    total = sum(item["earned"] for item in checks)
    return total, checks


def write_outputs(out_dir: Path, pdf: Path, sidecar: Path, record: dict[str, Any], md: dict[str, Any], total: int, checks: list[dict[str, Any]]) -> None:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {
        "created_utc": now,
        "pdf": str(pdf.resolve()),
        "sidecar": str(sidecar.resolve()),
        "score": total,
        "max_score": 100,
        "checks": checks,
        "markdown_metrics": md,
        "triage_lane": record["recommended_lane"],
    }
    (out_dir / "closed_loop_score.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8-sig")

    lines = [
        "# Sidecar Gold Closed-Loop Test",
        "",
        f"Created UTC: `{now}`",
        f"Score: **{total}/100**",
        "",
        "## Gold Source",
        "",
        f"- PDF: `{pdf.resolve()}`",
        f"- Markdown: `{sidecar.resolve()}`",
        f"- Markdown characters: {md['characters']}",
        f"- Headings: {md['heading_count']}",
        f"- Image refs: {md['image_count']}",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- {check['name']}: {check['earned']}/{check['points']} - {check['detail']}")
    lines.extend(["", "## Markdown Content Map", ""])
    for heading in md["headings"]:
        indent = "  " * max(0, heading["level"] - 1)
        lines.append(f"- {indent}{'#' * heading['level']} {heading['title']}")
    lines.extend(["", "## Image References", ""])
    for image in md["images"]:
        lines.append(f"- `{image}`")
    (out_dir / "closed_loop_report.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Validate PDF triage against a same-content Markdown sidecar.")
    parser.add_argument("pdf", help="PDF file")
    parser.add_argument("--sidecar", help="Same-content Markdown sidecar")
    parser.add_argument("--out", required=True, help="Reading pack / output folder")
    args = parser.parse_args(argv)

    pdf = Path(args.pdf)
    if not pdf.exists():
        raise SystemExit(f"Missing PDF: {pdf}")
    sidecar = Path(args.sidecar) if args.sidecar else find_sidecar(pdf)
    if not sidecar or not sidecar.exists():
        raise SystemExit("Missing same-content Markdown sidecar")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tools = pdf_triage.tool_inventory()
    record = pdf_triage.build_record(pdf, tools)
    pdf_triage.write_reports(out_dir, [record], tools)
    md = analyze_markdown(sidecar)
    total, checks = score(record, md, out_dir)
    write_outputs(out_dir, pdf, sidecar, record, md, total, checks)
    print(f"Closed-loop score: {total}/100")
    print(f"Wrote: {out_dir / 'closed_loop_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
