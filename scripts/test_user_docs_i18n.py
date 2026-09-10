"""Check user-guide language pairs and local navigation without changing files.

Run: python scripts/test_user_docs_i18n.py [--root PATH] [--self-test]
Scope: root Markdown, docs/**/*.md, and assets/README*.md.
Skill instructions and template inputs are intentionally outside this check.
"""

from __future__ import annotations

import argparse
from html import unescape
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import unquote, urlsplit


def guides(root: Path) -> list[Path]:
    return sorted(set(root.glob("*.md")) | set((root / "docs").rglob("*.md"))
                  | set((root / "assets").glob("README*.md")))


def paired(path: Path) -> Path:
    if path.name.endswith(".zh-CN.md"):
        return path.with_name(path.name.replace(".zh-CN.md", ".md"))
    return path.with_name(path.stem + ".zh-CN.md")


def prose(text: str) -> str:
    # Exclude fenced examples, including commands containing placeholder paths.
    return re.sub(r"(?m)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text, flags=re.S)


def links(text: str) -> list[str]:
    clean = prose(text)
    markdown = re.findall(r"!?\[[^\]\n]*\]\(<?([^\s)>]+)>?(?:\s+[^)]*)?\)", clean)
    html = re.findall(r'(?:href|src)=[\"\']([^\"\']+)[\"\']', clean)
    return markdown + html


def language_choices(text: str) -> set[str]:
    return {href for label, href in re.findall(r"\[([^]\n]+)\]\(([^)\s]+)\)", prose(text))
            if re.search(r"English|Chinese|英文|中文", label, re.I)}


def anchors(text: str) -> set[str]:
    found = set(re.findall(r'(?:id|name)=[\"\']([^\"\']+)[\"\']', text))
    duplicates: dict[str, int] = {}
    for title in re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", prose(text)):
        title = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", title)
        title = unescape(re.sub(r"<[^>]*>", "", title)).lower().replace("`", "")
        title = "".join(c for c in title if c in "-_ " or not unicodedata.category(c).startswith(("P", "S")))
        slug = title.replace(" ", "-")
        count = duplicates.get(slug, 0)
        duplicates[slug] = count + 1
        found.add(slug if not count else f"{slug}-{count}")
    return found


def check(root: Path) -> tuple[list[str], int]:
    root = root.resolve()
    if not root.is_dir():
        return [f"not a directory: {root}"], 0
    paths = guides(root)
    if not paths:
        return [f"no user documents found: {root}"], 0
    errors: list[str] = []
    texts: dict[Path, str] = {}
    for path in paths:
        try:
            texts[path.resolve()] = path.read_text(encoding="utf-8-sig", errors="strict")
        except UnicodeError as exc:
            errors.append(f"{path.relative_to(root)}: invalid UTF-8: {exc}")
    for path, text in texts.items():
        label = path.relative_to(root).as_posix()
        peer = paired(path)
        if not peer.exists():
            errors.append(f"{label}: missing counterpart {peer.name}")
        elif peer.name not in links("\n".join(text.splitlines()[:24])):
            errors.append(f"{label}: missing top language switch to {peer.name}")
        if "\ufffd" in text:
            errors.append(f"{label}: Unicode replacement character")
        for href in links(text):
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc:
                continue
            target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
            if not target.is_relative_to(root):
                errors.append(f"{label}: link escapes repository: {href}")
                continue
            if not target.exists():
                errors.append(f"{label}: missing target: {href}")
                continue
            if target in texts and parsed.fragment and unquote(parsed.fragment) not in anchors(texts[target]):
                errors.append(f"{label}: missing fragment: {href}")
            if target in texts and target != peer:
                if (path.name.endswith(".zh-CN.md") != target.name.endswith(".zh-CN.md")
                        and href not in language_choices(text)):
                    errors.append(f"{label}: cross-language navigation: {href}")
    return errors, len(paths)


def self_test() -> None:
    with tempfile.TemporaryDirectory(prefix="q-docs-i18n-") as directory:
        root = Path(directory)
        assert any("not a directory" in e for e in check(root / "missing")[0])
        assert any("no user documents" in e for e in check(root)[0])
        en = root / "README.md"
        zh = root / "README.zh-CN.md"
        en.write_text("# Guide\n\n[Simplified Chinese](README.zh-CN.md)\n\n## What's next?\n", encoding="utf-8")
        assert any("not a directory" in e for e in check(en)[0])
        zh.write_text("# 指南\n\n[English](README.md)\n\n## 下一步？\n", encoding="utf-8")
        assert not check(root)[0]
        assert "whats-next" in anchors(en.read_text(encoding="utf-8"))
        assert "下一步" in anchors(zh.read_text(encoding="utf-8"))
        original = en.read_text(encoding="utf-8")
        en.write_text(original + "\n[Broken](missing.md)\n[Bad fragment](#absent)\n", encoding="utf-8")
        errors, _ = check(root)
        assert any("missing target" in e for e in errors)
        assert any("missing fragment" in e for e in errors)
        en.write_text(original, encoding="utf-8")
        extra = root / "OTHER.md"
        extra_zh = root / "OTHER.zh-CN.md"
        extra.write_text("# Other\n\n[Chinese](OTHER.zh-CN.md)\n[Wrong](README.zh-CN.md)\n", encoding="utf-8")
        extra_zh.write_text("# 其他\n\n[English](OTHER.md)\n", encoding="utf-8")
        assert any("cross-language navigation" in e for e in check(root)[0])
        extra.write_text("# Other\n\n[Chinese](OTHER.zh-CN.md)\n[Chinese guide](README.zh-CN.md)\n", encoding="utf-8")
        assert not check(root)[0]
        extra.unlink()
        extra_zh.unlink()
        zh.write_text("# 指南\n", encoding="utf-8")
        assert any("missing top language switch" in e for e in check(root)[0])
        zh.unlink()
        assert any("missing counterpart" in e for e in check(root)[0])
        en.write_text("# Guide\n\n```text\n[Example](missing.md)\n```\n", encoding="utf-8")
        assert not links(en.read_text(encoding="utf-8"))
    print("PASS: negative controls and heading/fixture checks")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    errors, count = check(args.root)
    for error in errors:
        print("ERROR:", error)
    print(f"{'FAIL' if errors else 'PASS'}: {count} user documents; {len(errors)} errors")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
