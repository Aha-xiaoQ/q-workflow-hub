#!/usr/bin/env python3
"""Lightweight static checks for generated HTML interfaces."""

from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys


BLOCKER_PATTERNS = [
    ("negative letter-spacing", re.compile(r"letter-spacing\s*:\s*-\s*[\d.]+", re.I)),
    ("viewport-scaled font-size", re.compile(r"font-size\s*:\s*[^;{}]*(?:vw|vh|vmin|vmax)", re.I)),
]

DECORATIVE_CLASS_PATTERN = re.compile(
    r"(?:class|id)\s*=\s*[\"'][^\"']*\b(?:orb|blob|bokeh)\b", re.I
)

WARN_PATTERNS = [
    ("large border radius", re.compile(r"border-radius\s*:\s*(?:[1-9]\d+|9)px", re.I)),
    ("CSS transform scale", re.compile(r"transform\s*:\s*[^;{}]*scale\s*\(", re.I)),
    ("animation without reduced-motion guard", re.compile(r"animation\s*:", re.I)),
    ("outline disabled", re.compile(r"outline\s*:\s*(?:0|none)\b", re.I)),
]


class StructureParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.has_lang = False
        self.has_title = False
        self.has_viewport = False
        self.has_charset = False
        self.has_main = False
        self.interactive = 0
        self.focusable = 0
        self.card_depth = 0
        self.max_card_depth = 0
        self.labels = 0
        self.inputs = 0
        self.images = 0
        self.images_without_alt = 0
        self.tables = 0
        self.tables_without_header = 0
        self.table_stack: list[bool] = []
        self.card_stack: list[tuple[str, bool]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        self.tags.append(tag)
        if tag == "html" and attrs_dict.get("lang"):
            self.has_lang = True
        if tag == "meta":
            if attrs_dict.get("name", "").lower() == "viewport":
                self.has_viewport = True
            if "charset" in attrs_dict:
                self.has_charset = True
        if tag == "title":
            self.has_title = True
        if tag == "main":
            self.has_main = True
        if tag in {"button", "a", "input", "select", "textarea"}:
            self.interactive += 1
        if tag in {"input", "select", "textarea"}:
            self.inputs += 1
        if tag == "label":
            self.labels += 1
        if tag == "img":
            self.images += 1
            if "alt" not in attrs_dict:
                self.images_without_alt += 1
        if tag == "table":
            self.tables += 1
            self.table_stack.append(False)
        if tag == "th" and self.table_stack:
            self.table_stack[-1] = True
        if tag in {"button", "a", "input", "select", "textarea"} or "tabindex" in attrs_dict:
            self.focusable += 1
        class_value = attrs_dict.get("class", "")
        is_card = "card" in class_value.split()
        if is_card:
            if any(self.card_stack):
                self.max_card_depth = max(self.max_card_depth, 2)
            self.card_depth += 1
            self.max_card_depth = max(self.max_card_depth, self.card_depth)
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}:
            self.card_stack.append((tag, is_card))

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.has_title = True
        if tag == "table" and self.table_stack:
            has_header = self.table_stack.pop()
            if not has_header:
                self.tables_without_header += 1
        if self.card_stack:
            while self.card_stack:
                open_tag, ended_card = self.card_stack.pop()
                if ended_card and self.card_depth:
                    self.card_depth -= 1
                if open_tag == tag:
                    break
        if self.tags:
            self.tags.pop()


def collect_files(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            found.extend(sorted(path.rglob("*.html")))
            found.extend(sorted(path.rglob("*.htm")))
        else:
            found.append(path)
    return found


def check_file(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    parser = StructureParser()
    parser.feed(text)

    errors: list[str] = []
    warnings: list[str] = []

    if "<!doctype html" not in lower[:200]:
        errors.append("missing <!doctype html>")
    if not parser.has_lang:
        warnings.append("missing html lang attribute")
    if not parser.has_charset:
        errors.append("missing charset meta")
    if not parser.has_viewport:
        errors.append("missing viewport meta")
    if not parser.has_title:
        warnings.append("missing title")
    if not parser.has_main:
        warnings.append("missing main landmark")
    if "@media" not in text and len(text) > 3000:
        warnings.append("no responsive @media rule found")
    if ":focus" not in text and parser.focusable:
        warnings.append("interactive page has no visible focus CSS selector")
    if parser.inputs and parser.labels < max(1, parser.inputs // 2):
        warnings.append("form controls may be under-labeled")
    if parser.images_without_alt:
        warnings.append(f"{parser.images_without_alt} image(s) without alt attribute")
    if parser.tables_without_header:
        warnings.append(f"{parser.tables_without_header} table(s) without header cells")
    if parser.max_card_depth > 1:
        errors.append("possible nested .card elements")
    if re.search(r"<canvas\b", text, re.I) and not re.search(r"getContext|requestAnimationFrame", text):
        warnings.append("canvas present but drawing code was not detected")
    if re.search(r"class=[\"'][^\"']*mermaid", text, re.I) and "mermaid.initialize" not in text:
        warnings.append("Mermaid block present but renderer initialization not detected")
    if re.search(r"<svg\b", text, re.I) and not re.search(r"viewBox=", text):
        warnings.append("SVG present without viewBox")
    if "prefers-reduced-motion" not in text and re.search(r"animation\s*:", text, re.I):
        warnings.append("animation present without prefers-reduced-motion guard")

    for label, pattern in BLOCKER_PATTERNS:
        if pattern.search(text):
            errors.append(label)
    if DECORATIVE_CLASS_PATTERN.search(text):
        errors.append("decorative orb/blob/bokeh class or id")
    for label, pattern in WARN_PATTERNS:
        if pattern.search(text):
            warnings.append(label)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Check generated HTML UI quality.")
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("No HTML files found.", file=sys.stderr)
        return 2

    total_errors = 0
    total_warnings = 0
    for path in files:
        errors, warnings = check_file(path)
        total_errors += len(errors)
        total_warnings += len(warnings)
        status = "ERROR" if errors else "WARN" if warnings else "OK"
        print(f"{status} {path}")
        for item in errors:
            print(f"  error: {item}")
        for item in warnings:
            print(f"  warn: {item}")

    print(f"checked={len(files)} errors={total_errors} warnings={total_warnings}")
    return 1 if total_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
