#!/usr/bin/env python3
"""Compare OCR/table outputs and propose technical-token normalization.

This is a post-processing helper for OCR-heavy technical PDFs. It does not
modify original extraction artifacts. It writes candidate corrections, source
votes, and normalized table previews so reviewers can audit every change.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Any


TOKEN_RE = re.compile(r"[A-Za-z0-9_./+\-]+")


@dataclass
class SourceSpec:
    name: str
    path: Path


class TableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._table: list[list[str]] = []
        self._row: list[str] = []
        self._cell_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._in_table = True
            self._table = []
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._row = []
        elif self._in_table and self._in_row and tag in {"td", "th"}:
            self._in_cell = True
            self._cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._in_cell and tag in {"td", "th"}:
            self._row.append(_clean_text("".join(self._cell_parts)))
            self._cell_parts = []
            self._in_cell = False
        elif self._in_row and tag == "tr":
            self._table.append(self._row)
            self._row = []
            self._in_row = False
        elif self._in_table and tag == "table":
            self.tables.append(self._table)
            self._table = []
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._cell_parts.append(data)


def _configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _clean_text(text: str) -> str:
    return " ".join(text.replace("\xa0", " ").split())


def _parse_sources(items: list[str]) -> list[SourceSpec]:
    specs: list[SourceSpec] = []
    for index, item in enumerate(items, start=1):
        if "=" in item:
            name, raw_path = item.split("=", 1)
            name = name.strip() or f"source{index}"
        else:
            raw_path = item
            name = Path(item).name or f"source{index}"
        path = Path(raw_path)
        if not path.exists():
            raise SystemExit(f"Source path does not exist: {path}")
        specs.append(SourceSpec(name=name, path=path))
    return specs


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def _tokens_from_text(text: str) -> list[str]:
    return [token.strip(".,;:()[]{}<>") for token in TOKEN_RE.findall(text) if token.strip(".,;:()[]{}<>")]


def _tables_from_html(path: Path) -> list[list[list[str]]]:
    parser = TableHTMLParser()
    parser.feed(_read_text(path))
    return parser.tables


def _source_documents(spec: SourceSpec) -> list[tuple[str, str]]:
    docs: list[tuple[str, str]] = []
    if spec.path.is_file():
        if spec.path.suffix.lower() in {".html", ".md", ".json"}:
            docs.append((spec.path.name, _read_text(spec.path)))
        return docs
    for pattern in ("*.html", "*.md"):
        for path in sorted(spec.path.glob(pattern)):
            docs.append((path.name, _read_text(path)))
    ocr_json = spec.path / "ocr_results.json"
    if ocr_json.exists():
        try:
            payload = json.loads(_read_text(ocr_json))
            texts: list[str] = []
            for record in payload.get("records", []):
                texts.extend(str(item) for item in record.get("text", []) if item)
            docs.append((ocr_json.name, "\n".join(texts)))
        except Exception:
            pass
    return docs


def _normalize_token(token: str) -> tuple[str, list[str]]:
    normalized = token
    rules: list[str] = []

    replacements = [
        ("ADCO", "ADC0", "ADCO->ADC0"),
        ("PWMO", "PWM0", "PWMO->PWM0"),
        ("FLEXI00", "FLEXIO0", "FLEXI00->FLEXIO0"),
        ("FLEXIOO", "FLEXIO0", "FLEXIOO->FLEXIO0"),
        ("12C", "I2C", "12C->I2C"),
        ("0UT", "OUT", "0UT->OUT"),
    ]
    for old, new, note in replacements:
        if old in normalized:
            normalized = normalized.replace(old, new)
            rules.append(note)

    contextual = [
        (r"(?<=PWM0_)AO\b", "A0", "PWM0_AO->PWM0_A0"),
        (r"(?<=ADC0_)AO\b", "A0", "ADC0_AO->ADC0_A0"),
        (r"(?<=Arduino_A)O\b", "0", "Arduino_AO->Arduino_A0"),
        (r"(?<=Arduino_D)O\b", "0", "Arduino_DO->Arduino_D0"),
        (r"(?<=SCL_)O\b", "0", "SCL_O->SCL_0"),
        (r"(?<=SDA_)O\b", "0", "SDA_O->SDA_0"),
    ]
    for pattern, repl, note in contextual:
        new_value = re.sub(pattern, repl, normalized)
        if new_value != normalized:
            normalized = new_value
            rules.append(note)

    return normalized, rules


def _confidence(raw: str, normalized: str, rules: list[str], canonical_counts: Counter[str]) -> str:
    if raw == normalized:
        return "raw"
    if canonical_counts[normalized] > 0:
        return "high"
    high_rules = {"ADCO->ADC0", "PWMO->PWM0", "12C->I2C", "0UT->OUT", "FLEXI00->FLEXIO0"}
    if any(rule in high_rules for rule in rules):
        return "medium"
    return "low"


def _collect_votes(sources: list[SourceSpec]) -> tuple[dict[str, Counter[str]], dict[str, Counter[str]], dict[str, set[str]]]:
    raw_by_source: dict[str, Counter[str]] = {}
    source_by_raw: dict[str, set[str]] = defaultdict(set)
    canonical_forms: dict[str, Counter[str]] = defaultdict(Counter)
    for spec in sources:
        counter: Counter[str] = Counter()
        for _doc_name, text in _source_documents(spec):
            counter.update(_tokens_from_text(text))
        raw_by_source[spec.name] = counter
        for raw, count in counter.items():
            normalized, _rules = _normalize_token(raw)
            canonical_forms[normalized][raw] += count
            source_by_raw[raw].add(spec.name)
    return raw_by_source, canonical_forms, source_by_raw


def _write_candidates(
    out_dir: Path,
    canonical_forms: dict[str, Counter[str]],
    source_by_raw: dict[str, set[str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_global = Counter()
    for forms in canonical_forms.values():
        raw_global.update(forms)
    for canonical, forms in sorted(canonical_forms.items()):
        for raw, count in sorted(forms.items()):
            normalized, rules = _normalize_token(raw)
            if raw == normalized:
                continue
            rows.append(
                {
                    "raw": raw,
                    "candidate": normalized,
                    "raw_count": count,
                    "candidate_raw_count": raw_global[normalized],
                    "sources": ",".join(sorted(source_by_raw.get(raw, set()))),
                    "candidate_sources": ",".join(sorted(source_by_raw.get(normalized, set()))),
                    "confidence": _confidence(raw, normalized, rules, raw_global),
                    "rules": ",".join(rules),
                }
            )
    rows.sort(key=lambda row: (row["confidence"] != "high", row["candidate"], row["raw"]))
    tsv_path = out_dir / "technical_token_candidates.tsv"
    with tsv_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = ["raw", "candidate", "raw_count", "candidate_raw_count", "sources", "candidate_sources", "confidence", "rules"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def _markdown_table(rows: list[list[str]]) -> str:
    if not rows:
        return "_Empty table._\n"
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]
    header = padded[0]
    body = padded[1:]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * width) + " |"]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def _normalize_cell(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        normalized, _rules = _normalize_token(match.group(0))
        return normalized

    return TOKEN_RE.sub(repl, text)


def _write_preferred_tables(out_dir: Path, preferred: SourceSpec | None) -> None:
    if preferred is None or not preferred.path.exists():
        return
    lines = ["# Preferred Normalized Table Preview", "", f"Source: `{preferred.name}`", ""]
    table_index = 0
    html_files = [preferred.path] if preferred.path.is_file() and preferred.path.suffix.lower() == ".html" else sorted(preferred.path.glob("*_table_*.html"))
    for path in html_files:
        for table in _tables_from_html(path):
            table_index += 1
            normalized = [[_normalize_cell(cell) for cell in row] for row in table]
            lines.extend([f"## Table {table_index}: `{path.name}`", "", _markdown_table(normalized), ""])
    if table_index == 0:
        lines.append("No HTML tables found in preferred source.\n")
    (out_dir / "preferred_normalized_tables.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_report(
    out_dir: Path,
    sources: list[SourceSpec],
    raw_by_source: dict[str, Counter[str]],
    canonical_forms: dict[str, Counter[str]],
    candidates: list[dict[str, Any]],
) -> None:
    high = [row for row in candidates if row["confidence"] == "high"]
    medium = [row for row in candidates if row["confidence"] == "medium"]
    conflicts = [
        (canonical, forms)
        for canonical, forms in canonical_forms.items()
        if len(forms) > 1 and sum(forms.values()) > 1
    ]
    conflicts.sort(key=lambda item: sum(item[1].values()), reverse=True)

    lines = [
        "# Technical Token Vote Report",
        "",
        "This report preserves raw OCR/table output and proposes separate normalization candidates.",
        "",
        "## Sources",
        "",
    ]
    for spec in sources:
        lines.append(f"- `{spec.name}`: `{spec.path}` ({sum(raw_by_source[spec.name].values())} tokens)")
    lines.extend([
        "",
        "## Candidate Summary",
        "",
        f"- High-confidence candidates with source vote evidence: {len(high)}",
        f"- Medium-confidence rule candidates: {len(medium)}",
        f"- Total candidate rows: {len(candidates)}",
        "",
        "## High-Confidence Candidates",
        "",
    ])
    if high:
        lines.append("| Raw | Candidate | Raw count | Candidate raw count | Sources | Candidate sources | Rules |")
        lines.append("|---|---|---:|---:|---|---|---|")
        for row in high[:80]:
            lines.append(
                f"| `{row['raw']}` | `{row['candidate']}` | {row['raw_count']} | {row['candidate_raw_count']} | "
                f"{row['sources']} | {row['candidate_sources']} | {row['rules']} |"
            )
    else:
        lines.append("_No high-confidence candidates._")
    lines.extend(["", "## Top Variant Groups", ""])
    lines.append("| Canonical | Raw forms | Total count |")
    lines.append("|---|---|---:|")
    for canonical, forms in conflicts[:80]:
        form_text = ", ".join(f"`{raw}`:{count}" for raw, count in forms.most_common())
        lines.append(f"| `{canonical}` | {form_text} | {sum(forms.values())} |")
    lines.extend([
        "",
        "## Files",
        "",
        "- `technical_token_candidates.tsv`: all proposed token-level candidates.",
        "- `preferred_normalized_tables.md`: normalized preview for the preferred source, if provided.",
    ])
    (out_dir / "technical_token_vote_report.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    _configure_stdout()
    parser = argparse.ArgumentParser(description="Vote and normalize technical OCR tokens across multiple extraction outputs.")
    parser.add_argument("--source", action="append", required=True, help="Source as name=path or path. Can be repeated.")
    parser.add_argument("--preferred", help="Preferred source name for normalized table preview.")
    parser.add_argument("--out", required=True, help="Output directory.")
    args = parser.parse_args(argv)

    sources = _parse_sources(args.source)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_by_source, canonical_forms, source_by_raw = _collect_votes(sources)
    candidates = _write_candidates(out_dir, canonical_forms, source_by_raw)
    preferred = next((spec for spec in sources if spec.name == args.preferred), None)
    _write_preferred_tables(out_dir, preferred)
    _write_report(out_dir, sources, raw_by_source, canonical_forms, candidates)
    summary = {
        "sources": {spec.name: str(spec.path) for spec in sources},
        "candidate_count": len(candidates),
        "high_confidence_count": sum(1 for row in candidates if row["confidence"] == "high"),
        "medium_confidence_count": sum(1 for row in candidates if row["confidence"] == "medium"),
        "outputs": [
            str(out_dir / "technical_token_candidates.tsv"),
            str(out_dir / "technical_token_vote_report.md"),
            str(out_dir / "preferred_normalized_tables.md"),
        ],
    }
    (out_dir / "technical_token_vote_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
