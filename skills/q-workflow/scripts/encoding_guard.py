#!/usr/bin/env python3
"""Check UTF-8 files for common Windows/PowerShell mojibake.

This script is intentionally conservative: it reads files, reports invalid
UTF-8 and common double-decoded UTF-8 fragments, and does not edit anything.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".ps1",
    ".html",
    ".htm",
    ".css",
    ".js",
    ".csv",
}

MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u00e6\u20ac",
    "\u00e6\u00b2",
    "\u00e7\u00bb",
    "\u00e7\u201d",
    "\u00e7\u017d",
    "\u00e4\u00bd",
    "\u00e5\u00b0",
    "\u00e5\u00b7",
    "\u00e9\u00aa",
    "\u00c3",
    "\u00c2",
    "\u00ef\u00bc",
)

BASE_SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
DEFAULT_SKIP_DIRS = BASE_SKIP_DIRS | {"archive"}


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass



def load_q_profile(home: Path) -> dict[str, str]:
    profile_path = Path(os.environ.get("Q_PROFILE_PATH", str(home / ".codex" / "q-profile.json")))
    try:
        import json
        payload = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    return {str(key): value for key, value in payload.items() if isinstance(value, str) and value}


def default_personal_state(home: Path) -> Path:
    configured_state = os.environ.get("Q_PERSONAL_STATE")
    if configured_state:
        return Path(configured_state)
    profile = load_q_profile(home)
    for key in ("personal_state", "state", "personalState"):
        if profile.get(key):
            return Path(profile[key])
    for key in ("hub", "personal_hub", "workflow_hub"):
        if profile.get(key):
            return Path(profile[key]) / "personal-state"
    return home / "q-personal-hub" / "personal-state"


def iter_files(paths: list[Path], include_archive: bool = False) -> list[Path]:
    files: list[Path] = []
    skip_dirs = BASE_SKIP_DIRS if include_archive else DEFAULT_SKIP_DIRS
    for path in paths:
        if path.is_file():
            if path.suffix.lower() in TEXT_SUFFIXES:
                files.append(path)
            continue
        if path.is_dir():
            for root, dirs, names in os.walk(path):
                dirs[:] = [name for name in dirs if name not in skip_dirs]
                root_path = Path(root)
                for name in names:
                    candidate = root_path / name
                    if candidate.suffix.lower() in TEXT_SUFFIXES:
                        files.append(candidate)
    return sorted(set(files))


def check_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"read failed: {exc}"]

    if path.name.casefold() == "skill.md" and data.startswith(b"\xef\xbb\xbf"):
        findings.append("UTF-8 BOM before skill frontmatter; skill loaders may skip this file")

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"invalid UTF-8 at byte {exc.start}: {exc.reason}"]

    for line_no, line in enumerate(text.splitlines(), start=1):
        for marker in MOJIBAKE_MARKERS:
            if marker in line:
                snippet = line.strip().replace("|", "\\|")[:180]
                findings.append(f"line {line_no}: suspicious marker {marker!r}: {snippet}")
                break
        if "\r" in line:
            snippet = line.strip().replace("|", "\\|")[:180]
            findings.append(f"line {line_no}: embedded carriage return: {snippet}")
    return findings


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Files or directories to scan. Defaults to q-workflow runtime and hub state.")
    parser.add_argument("--warn-only", action="store_true", help="Always return zero even when findings exist.")
    parser.add_argument("--include-archive", action="store_true", help="Also scan archive folders. Default skips archives to keep current-state gates actionable.")
    args = parser.parse_args(argv)

    if args.paths:
        roots = args.paths
    else:
        home = Path(os.environ.get("USERPROFILE", str(Path.home())))
        roots = [
            home / ".codex" / "skills" / "q-workflow",
            default_personal_state(home),
        ]

    files = iter_files(roots, include_archive=args.include_archive)
    findings: list[tuple[Path, str]] = []
    for path in files:
        for finding in check_file(path):
            findings.append((path, finding))

    if findings:
        print(f"Encoding guard: ATTENTION ({len(findings)} findings in {len(files)} files checked)")
        for path, finding in findings:
            print(f"- {path}: {finding}")
    else:
        print(f"Encoding guard: PASS ({len(files)} files checked)")

    return 0 if args.warn_only or not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())
