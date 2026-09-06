#!/usr/bin/env python3
"""Audit source skill folders against installed runtime mirrors.

This narrow gate compares recursive file lists and SHA-256 hashes for
source/runtime skill pairs. A runtime file that is newer or different is a
blocker because it may contain behavior that never returned to durable source.
Intentional differences can be waived only through an explicit JSON waiver file;
waived findings stay visible in the report.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
P1_TYPES = {"missing-source", "missing-runtime", "runtime-extra", "runtime-missing"}


@dataclass(frozen=True)
class FileInfo:
    rel: str
    path: Path
    sha256: str
    size: int
    mtime: float


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        yield path


def inventory(root: Path) -> dict[str, FileInfo]:
    result: dict[str, FileInfo] = {}
    for path in iter_files(root):
        rel = path.relative_to(root).as_posix()
        stat = path.stat()
        result[rel] = FileInfo(rel=rel, path=path, sha256=sha256(path), size=stat.st_size, mtime=stat.st_mtime)
    return result


def fmt_time(ts: float) -> str:
    return _dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def today() -> _dt.date:
    return _dt.datetime.now().date()


def base_finding(level: str, kind: str, file: str = "", **extra: str) -> dict:
    finding = {"level": level, "type": kind}
    if file:
        finding["file"] = file
    finding.update(extra)
    return finding


def load_waivers(paths: list[str]) -> tuple[list[dict], list[str]]:
    waivers: list[dict] = []
    errors: list[str] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if not path.is_file():
            errors.append(f"waiver file not found: {path}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - report parse failures as gate evidence
            errors.append(f"cannot parse waiver file {path}: {exc}")
            continue
        entries = data.get("waivers") if isinstance(data, dict) else data
        if not isinstance(entries, list):
            errors.append(f"waiver file must be a list or object with waivers list: {path}")
            continue
        for index, entry in enumerate(entries, start=1):
            if not isinstance(entry, dict):
                errors.append(f"{path}#{index}: waiver entry must be an object")
                continue
            entry = dict(entry)
            entry["_source"] = str(path)
            entry["_index"] = index
            waivers.append(entry)
    return waivers, errors


def waiver_value_matches(pattern: str | None, value: str) -> bool:
    if pattern in (None, "", "*"):
        return True
    return fnmatch.fnmatchcase(value, pattern)


def waiver_expired(waiver: dict) -> bool:
    expires = str(waiver.get("expires", "")).strip()
    if not expires:
        return False
    try:
        return _dt.date.fromisoformat(expires) < today()
    except ValueError:
        return True


def waiver_matches(waiver: dict, pair_name: str, finding: dict) -> bool:
    if waiver_expired(waiver):
        return False
    file_value = str(finding.get("file", ""))
    if not file_value:
        return False
    return (
        waiver_value_matches(str(waiver.get("pair", "*")), pair_name)
        and waiver_value_matches(str(waiver.get("file", "")), file_value)
        and waiver_value_matches(str(waiver.get("type", "*")), str(finding.get("type", "")))
        and waiver_value_matches(str(waiver.get("direction", "*")), str(finding.get("direction", "")))
    )


def validate_waiver(waiver: dict, finding: dict) -> str:
    reason = str(waiver.get("reason", "")).strip()
    if len(reason) < 12:
        return "waiver reason must be at least 12 characters"
    if finding.get("level") == "P1" or finding.get("direction") == "runtime-newer":
        approved_by = str(waiver.get("approved_by", "")).strip()
        if not approved_by:
            return "P1/runtime-newer waiver requires approved_by"
    if waiver_expired(waiver):
        return "waiver is expired or has invalid expires date"
    return ""


def apply_waivers(pair_name: str, findings: list[dict], waivers: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    active: list[dict] = []
    waived: list[dict] = []
    invalid: list[dict] = []
    for finding in findings:
        matches = [waiver for waiver in waivers if waiver_matches(waiver, pair_name, finding)]
        if not matches:
            active.append(finding)
            continue
        waiver = matches[0]
        error = validate_waiver(waiver, finding)
        if error:
            failed = dict(finding)
            failed["waiver_error"] = error
            failed["waiver_source"] = f"{waiver.get('_source')}#{waiver.get('_index')}"
            invalid.append(failed)
            active.append(finding)
            continue
        marked = dict(finding)
        marked["waiver_reason"] = str(waiver.get("reason", "")).strip()
        marked["waiver_source"] = f"{waiver.get('_source')}#{waiver.get('_index')}"
        if waiver.get("approved_by"):
            marked["approved_by"] = str(waiver.get("approved_by"))
        waived.append(marked)
    return active, waived, invalid


def audit_pair(name: str, source: Path, runtime: Path, waivers: list[dict] | None = None) -> dict:
    item = {"name": name, "source": str(source), "runtime": str(runtime), "status": "PASS", "findings": [], "waived_findings": [], "invalid_waivers": []}
    raw_findings: list[dict] = []
    if not source.exists():
        raw_findings.append(base_finding("P1", "missing-source", detail=str(source)))
    if not runtime.exists():
        raw_findings.append(base_finding("P1", "missing-runtime", detail=str(runtime)))
    if raw_findings:
        item["findings"] = raw_findings
        item["status"] = "BLOCKED"
        return item
    src = inventory(source)
    run = inventory(runtime)
    rels = sorted(set(src) | set(run))
    for rel in rels:
        s = src.get(rel)
        r = run.get(rel)
        if s is None:
            raw_findings.append(base_finding("P1", "runtime-extra", rel, runtime_mtime=fmt_time(r.mtime) if r else ""))
            continue
        if r is None:
            raw_findings.append(base_finding("P1", "runtime-missing", rel, source_mtime=fmt_time(s.mtime)))
            continue
        if s.sha256 != r.sha256:
            direction = "runtime-newer" if r.mtime > s.mtime else "source-newer" if s.mtime > r.mtime else "same-mtime"
            level = "P1" if direction == "runtime-newer" else "P2"
            raw_findings.append(base_finding(
                level,
                "hash-mismatch",
                rel,
                direction=direction,
                source_sha16=s.sha256[:16],
                runtime_sha16=r.sha256[:16],
                source_mtime=fmt_time(s.mtime),
                runtime_mtime=fmt_time(r.mtime),
            ))
    active, waived, invalid = apply_waivers(name, raw_findings, waivers or [])
    item["findings"] = active
    item["waived_findings"] = waived
    item["invalid_waivers"] = invalid
    if active or invalid:
        item["status"] = "BLOCKED"
    item["source_file_count"] = len(src)
    item["runtime_file_count"] = len(run)
    return item


def render_finding(finding: dict) -> str:
    bits = [f"{finding.get('level', 'P?')} {finding.get('type', 'finding')}"]
    if finding.get("direction"):
        bits.append(f"direction={finding['direction']}")
    if finding.get("file"):
        bits.append(f"file=`{finding['file']}`")
    if finding.get("source_sha16"):
        bits.append(f"source={finding['source_sha16']}")
    if finding.get("runtime_sha16"):
        bits.append(f"runtime={finding['runtime_sha16']}")
    if finding.get("waiver_error"):
        bits.append(f"waiver_error={finding['waiver_error']}")
    if finding.get("waiver_source"):
        bits.append(f"waiver={finding['waiver_source']}")
    if finding.get("approved_by"):
        bits.append(f"approved_by={finding['approved_by']}")
    if finding.get("waiver_reason"):
        bits.append(f"reason={finding['waiver_reason']}")
    return "; ".join(bits)


def render_markdown(report: dict) -> str:
    lines = ["# Source/Runtime Sync Audit", "", f"Generated: {report['generated']}", ""]
    lines.append(f"Verdict: {report['verdict']}")
    lines.append(f"Blockers: {report['blockers']}")
    lines.append(f"Waived findings: {report['waived_count']}")
    lines.append("")
    if report.get("waiver_files"):
        lines.append("## Waiver Files")
        for path in report["waiver_files"]:
            lines.append(f"- `{path}`")
        if report.get("waiver_errors"):
            lines.append("- Waiver file errors:")
            for error in report["waiver_errors"]:
                lines.append(f"  - {error}")
        lines.append("")
    for pair in report["pairs"]:
        lines.append(f"## {pair['name']}")
        lines.append(f"- Source: `{pair['source']}`")
        lines.append(f"- Runtime: `{pair['runtime']}`")
        lines.append(f"- Status: {pair['status']}")
        lines.append(f"- Files: source {pair.get('source_file_count', 0)} / runtime {pair.get('runtime_file_count', 0)}")
        findings = pair.get("findings", [])
        if not findings:
            lines.append("- Findings: none")
        else:
            lines.append("- Findings:")
            for finding in findings[:80]:
                lines.append("  - " + render_finding(finding))
            if len(findings) > 80:
                lines.append(f"  - ... {len(findings) - 80} more findings omitted")
        invalid = pair.get("invalid_waivers", [])
        if invalid:
            lines.append("- Invalid waivers:")
            for finding in invalid[:40]:
                lines.append("  - " + render_finding(finding))
        waived = pair.get("waived_findings", [])
        if waived:
            lines.append("- Waived findings:")
            for finding in waived[:80]:
                lines.append("  - " + render_finding(finding))
        lines.append("")
    lines.append("## Rule")
    lines.append("Any runtime-newer mismatch must be backfilled into durable source or waived with a file-specific reason and approver before claiming latest/stable/release-ready.")
    return "\n".join(lines) + "\n"


def default_pair_from_repo(repo: Path, skill_name: str, runtime_root: Path) -> tuple[str, Path, Path]:
    return (skill_name, repo / "skills" / skill_name, runtime_root / skill_name)


def parse_pair(value: str) -> tuple[str, Path, Path]:
    parts = value.split("=", 1)
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("pair must be NAME=SOURCE|RUNTIME")
    name, rest = parts
    paths = rest.split("|", 1)
    if len(paths) != 2:
        raise argparse.ArgumentTypeError("pair must be NAME=SOURCE|RUNTIME")
    return (name, Path(paths[0]).expanduser(), Path(paths[1]).expanduser())


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source skill folders against runtime mirrors.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for default --skill-name pair.")
    parser.add_argument("--runtime-root", default=str(Path.home() / ".codex" / "skills"), help="Installed runtime skills root.")
    parser.add_argument("--skill-name", default="q-workflow", help="Default skill folder name under repo skills/.")
    parser.add_argument("--pair", action="append", default=[], type=parse_pair, help="Additional/explicit NAME=SOURCE|RUNTIME pair. Can repeat.")
    parser.add_argument("--waiver-file", action="append", default=[], help="JSON waiver file. Can repeat. Waived findings remain visible in reports.")
    parser.add_argument("--output", default="", help="Markdown report path.")
    parser.add_argument("--json-output", default="", help="JSON report path.")
    args = parser.parse_args()

    repo = Path(args.repo_root).expanduser().resolve()
    runtime_root = Path(args.runtime_root).expanduser().resolve()
    pairs = list(args.pair) if args.pair else [default_pair_from_repo(repo, args.skill_name, runtime_root)]
    waivers, waiver_errors = load_waivers(args.waiver_file)
    results = [audit_pair(name, source.resolve(), runtime.resolve(), waivers) for name, source, runtime in pairs]
    blockers = sum(1 for pair in results for finding in pair.get("findings", [])) + sum(1 for pair in results for finding in pair.get("invalid_waivers", [])) + len(waiver_errors)
    waived_count = sum(1 for pair in results for finding in pair.get("waived_findings", []))
    report = {
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "verdict": "PASS" if blockers == 0 else "BLOCKED",
        "blockers": blockers,
        "waived_count": waived_count,
        "waiver_files": [str(Path(path).expanduser()) for path in args.waiver_file],
        "waiver_errors": waiver_errors,
        "pairs": results,
    }
    if args.json_output:
        out = Path(args.json_output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown = render_markdown(report)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8", newline="\n")
    print(markdown)
    return 0 if blockers == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
