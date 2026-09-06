#!/usr/bin/env python3
"""Score extracted PDF text against a same-content Markdown reference."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any


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


def normalize(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+", "", text)
    return text.lower()


def headings(markdown: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^#{1,6}\s+(.+)$", markdown, flags=re.MULTILINE)]


def image_refs(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)


def candidate_terms(markdown: str, limit: int = 16) -> list[str]:
    tokens = [match.group(0) for match in TOKEN_RE.finditer(markdown)]
    filtered = [token for token in tokens if token.lower() not in STOPWORDS]
    counts = Counter(filtered)
    return [term for term, _ in counts.most_common(limit)]


def candidate_phrases(markdown: str, limit: int = 8) -> list[str]:
    phrases = []
    for raw_line in markdown.splitlines():
        line = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", raw_line)
        line = re.sub(r"\[[^\]]+\]\([^)]+\)", " ", line)
        line = re.sub(r"^[#>\-\s\d.]+", "", line).strip()
        line = re.sub(r"\s+", " ", line)
        if 12 <= len(line) <= 80 and len(TOKEN_RE.findall(line)) >= 2:
            phrases.append(line)
        if len(phrases) >= limit:
            break
    return phrases


def contains_near(text_norm: str, target: str) -> bool:
    target_norm = normalize(target)
    if not target_norm:
        return False
    if target_norm in text_norm:
        return True
    compact = re.sub(r"[_\\/\-:：，。,.;；\"'“”‘’()（）\[\]]+", "", target_norm)
    return bool(compact and compact in text_norm)


def score(reference: str, extracted: str, pack_dir: Path, key_terms: list[str]) -> tuple[int, list[dict[str, Any]]]:
    ref_norm = normalize(reference)
    ext_norm = normalize(extracted)
    checks: list[dict[str, Any]] = []

    def add(name: str, points: int, earned: int, detail: str) -> None:
        checks.append({"name": name, "points": points, "earned": earned, "detail": detail})

    length_ratio = len(ext_norm) / max(1, len(ref_norm))
    length_points = 15 if 0.65 <= length_ratio <= 2.3 else 8 if 0.35 <= length_ratio <= 3.0 else 2
    add("content volume", 15, length_points, f"extracted/reference normalized length ratio {length_ratio:.2f}")

    ref_headings = headings(reference)
    matched_headings = [h for h in ref_headings if contains_near(ext_norm, h)]
    heading_points = int(25 * len(matched_headings) / max(1, len(ref_headings)))
    add("heading coverage", 25, heading_points, f"{len(matched_headings)}/{len(ref_headings)} headings matched")

    terms = key_terms or candidate_terms(reference)
    found_terms = [term for term in terms if contains_near(ext_norm, term)]
    term_points = 20 if not terms else int(20 * len(found_terms) / len(terms))
    add("key term coverage", 20, term_points, f"{len(found_terms)}/{len(terms)} terms: {found_terms}")

    chinese_phrases = ["开发板", "硬件", "软件", "串口", "联网", "大模型", "环境配置", "完整代码"]
    chinese_phrases = candidate_phrases(reference)
    found_phrases = [phrase for phrase in chinese_phrases if contains_near(ext_norm, phrase)]
    phrase_points = 15 if not chinese_phrases else int(15 * len(found_phrases) / len(chinese_phrases))
    add("reference phrase coverage", 15, phrase_points, f"{len(found_phrases)}/{len(chinese_phrases)} phrases matched")

    images = image_refs(reference)
    image_names = [Path(img).name for img in images]
    found_images = [name for name in image_names if contains_near(ext_norm, Path(name).stem)]
    rendered_pages = list((pack_dir / "pages").glob("page_*.png")) if (pack_dir / "pages").exists() else []
    extracted_images = [p for p in (pack_dir / "figures").glob("*") if p.is_file()] if (pack_dir / "figures").exists() else []
    if not images:
        image_points = 10
    elif len(extracted_images) >= len(images) or rendered_pages:
        image_points = 10
    else:
        image_points = int(10 * len(found_images) / len(images))
    add(
        "visual evidence coverage",
        10,
        image_points,
        f"{len(found_images)}/{len(images)} image names in text, {len(extracted_images)} extracted images, {len(rendered_pages)} rendered pages",
    )

    mojibake_hits = len(re.findall(r"[\u00c3\u00c2\ufffd]|\u00e5\u00ae|\u00e9\u00aa|\u00e6\u2030|w\s*x\s*y", extracted, flags=re.IGNORECASE))
    quality_points = 15 if mojibake_hits == 0 else 8 if mojibake_hits < 10 else 2
    add("encoding/noise quality", 15, quality_points, f"{mojibake_hits} obvious noise hits")

    return sum(item["earned"] for item in checks), checks


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Score extracted PDF text against Markdown reference.")
    parser.add_argument("extracted_text", help="extracted_text.md generated from PDF only")
    parser.add_argument("reference_markdown", help="same-content Markdown reference")
    parser.add_argument("--out", required=True, help="Output folder")
    parser.add_argument("--pack-dir", help="Reading pack folder containing pages/ and figures/. Defaults to extracted_text parent.")
    parser.add_argument("--key-term", action="append", default=[], help="Important term expected in the extracted text; can be repeated")
    args = parser.parse_args(argv)

    extracted_path = Path(args.extracted_text)
    reference_path = Path(args.reference_markdown)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted = read_text(extracted_path)
    reference = read_text(reference_path)
    pack_dir = Path(args.pack_dir) if args.pack_dir else extracted_path.parent
    total, checks = score(reference, extracted, pack_dir, args.key_term)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {
        "created_utc": now,
        "score": total,
        "max_score": 100,
        "extracted_text": str(extracted_path.resolve()),
        "reference_markdown": str(reference_path.resolve()),
        "checks": checks,
    }
    (out_dir / "reading_quality_score.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    lines = [
        "# PDF Reading Quality Test",
        "",
        f"Created UTC: `{now}`",
        f"Score: **{total}/100**",
        "",
        "## Checks",
        "",
    ]
    for check in checks:
        lines.append(f"- {check['name']}: {check['earned']}/{check['points']} - {check['detail']}")
    (out_dir / "reading_quality_report.md").write_text("\n".join(lines), encoding="utf-8-sig")
    print(f"Reading quality score: {total}/100")
    print(f"Wrote: {out_dir / 'reading_quality_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
