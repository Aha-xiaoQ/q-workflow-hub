#!/usr/bin/env python3
"""Compare skill files across source/runtime/hub surfaces.

This gate answers three questions before skill handoff, push, or runtime sync:
1. Do the named skill surfaces contain the same in-scope files?
2. Which file hashes differ, and where is the evidence?
3. Are repository surfaces locally ahead/behind their configured upstream?

Hash drift is allowed only when the handoff classifies it as intentional,
stale, blocked, or fixed. Use --fail-on-drift and --fail-on-upstream-drift for
release, push, and stable-runtime claims.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

COMMON_DEFAULT_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
]

SKILL_CREATION_DEFAULT_FILES = [
    *COMMON_DEFAULT_FILES,
    "workflows/create-skill.md",
    "workflows/update-skill.md",
    "references/quality-bar.md",
    "references/source-runtime-freshness.md",
    "references/skill-lifecycle-standard.md",
    "references/skill-taxonomy-schema.md",
    "scripts/surface_freshness_check.py",
]

IGNORE_DIRS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache"}
IGNORE_SUFFIXES = {".pyc", ".pyo"}


@dataclass
class FileState:
    root: str
    rel: str
    exists: bool
    sha256: str = ""
    size: int = 0
    mtime_utc: str = ""
    git_commit: str = ""


@dataclass
class GitState:
    repo: str
    branch: str = ""
    upstream: str = ""
    ahead: int = 0
    behind: int = 0
    dirty_count: int = 0
    available: bool = False
    error: str = ""


def expand_path(raw: str) -> Path:
    value = raw.strip().strip("`")
    value = value.replace("%USERPROFILE%", os.environ.get("USERPROFILE", ""))
    return Path(os.path.expandvars(value)).expanduser()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def find_git_root(path: Path) -> Path | None:
    try:
        current = path.resolve()
    except OSError:
        current = path
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


def run_git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def git_last_commit(repo: Path | None, file_path: Path) -> str:
    if repo is None:
        return ""
    try:
        rel = file_path.resolve().relative_to(repo.resolve()).as_posix()
    except (OSError, ValueError):
        return ""
    result = run_git(repo, ["log", "-1", "--format=%h", "--", rel])
    return result.stdout.strip() if result.returncode == 0 else ""


def git_state(repo: Path) -> GitState:
    state = GitState(repo=str(repo))
    if repo is None:
        return state
    branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if branch.returncode != 0:
        state.error = branch.stderr.strip() or branch.stdout.strip()
        return state
    state.available = True
    state.branch = branch.stdout.strip()

    upstream = run_git(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream.returncode == 0:
        state.upstream = upstream.stdout.strip()
        counts = run_git(repo, ["rev-list", "--left-right", "--count", "@{u}...HEAD"])
        if counts.returncode == 0:
            parts = counts.stdout.strip().split()
            if len(parts) == 2:
                state.behind = int(parts[0])
                state.ahead = int(parts[1])
    else:
        state.error = "no upstream configured"

    status = run_git(repo, ["status", "--porcelain=v1"])
    if status.returncode == 0:
        state.dirty_count = len([line for line in status.stdout.splitlines() if line.strip()])
    return state


def collect(root: Path, rel: str) -> FileState:
    path = root / rel
    if not path.exists():
        return FileState(root=str(root), rel=rel, exists=False)
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    return FileState(
        root=str(root),
        rel=rel,
        exists=True,
        sha256=sha256_file(path),
        size=stat.st_size,
        mtime_utc=mtime,
        git_commit=git_last_commit(find_git_root(root), path),
    )


def shorten(value: str, length: int = 12) -> str:
    return value[:length] if value else "-"


def default_files(skill: str) -> list[str]:
    if skill in {"q-skill-creation"}:
        return SKILL_CREATION_DEFAULT_FILES
    return COMMON_DEFAULT_FILES


def iter_skill_files(root: Path) -> Iterable[str]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.relative_to(root).parts):
            continue
        if path.suffix in IGNORE_SUFFIXES:
            continue
        yield path.relative_to(root).as_posix()


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    table_lines = [line for line in lines if line.lstrip().startswith("|")]
    if len(table_lines) < 2:
        return rows
    reader = csv.reader(StringIO("\n".join(table_lines)), delimiter="|")
    parsed = []
    for row in reader:
        cells = [cell.strip() for cell in row[1:-1]]
        if cells:
            parsed.append(cells)
    if len(parsed) < 2:
        return rows
    headers = parsed[0]
    for cells in parsed[2:]:
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def extract_paths(cell: str) -> list[Path]:
    # Prefer backticked paths so prose such as "Retired compatibility alias" does not
    # become a fake surface.
    candidates = re.findall(r"`([^`]+)`", cell)
    if not candidates and (":" in cell or "%USERPROFILE%" in cell):
        candidates = [cell]
    paths: list[Path] = []
    for candidate in candidates:
        if candidate.lower().startswith("retired"):
            continue
        path = expand_path(candidate)
        if str(path):
            paths.append(path)
    return paths


def roots_from_registry(registry: Path, skill: str) -> list[Path]:
    for row in parse_markdown_table(registry):
        if row.get("Skill") != skill:
            continue
        roots: list[Path] = []
        for key in ("Source / Maintenance Path", "Durable Source", "Installed Path", "Installed Copy"):
            if key in row:
                roots.extend(extract_paths(row[key]))
        return roots
    raise SystemExit(f"skill {skill!r} not found in registry {registry}")


def normalize_skill_roots(skill: str, roots: Iterable[Path]) -> list[Path]:
    normalized: list[Path] = []
    seen: set[str] = set()
    for base in roots:
        root = base if base.name == skill else base / skill
        key = str(root).lower()
        if key not in seen:
            normalized.append(root)
            seen.add(key)
    return normalized


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="Skill folder name")
    parser.add_argument(
        "--roots",
        nargs="+",
        help="Surface roots that contain the skill folder or are the skill folder",
    )
    parser.add_argument(
        "--registry",
        help="Markdown registry with Skill/Source/Installed columns, such as SKILL_REGISTRY.md",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        help="Relative files to compare under the skill folder; defaults are skill-aware core files",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Compare the union of all files under the skill folder",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Return non-zero when compared files differ or are missing",
    )
    parser.add_argument(
        "--check-git",
        action="store_true",
        help="Report repository branch, upstream, dirty count, ahead, and behind state",
    )
    parser.add_argument(
        "--fail-on-upstream-drift",
        action="store_true",
        help="Return non-zero when a repo surface is dirty, ahead, behind, or has no upstream",
    )
    parser.add_argument(
        "--json-out",
        help="Write machine-readable evidence JSON to this path",
    )
    args = parser.parse_args(argv)

    roots: list[Path] = []
    if args.registry:
        roots.extend(roots_from_registry(Path(args.registry), args.skill))
    if args.roots:
        roots.extend(expand_path(raw) for raw in args.roots)
    if not roots:
        raise SystemExit("provide --roots and/or --registry")

    skill_roots = normalize_skill_roots(args.skill, roots)
    rels = set(args.files if args.files is not None else default_files(args.skill))
    if args.all_files:
        rels = set()
        for root in skill_roots:
            if root.exists():
                rels.update(iter_skill_files(root))
    rels = sorted(rels)

    drift = False
    evidence: dict[str, object] = {
        "skill": args.skill,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "surfaces": [str(root) for root in skill_roots],
        "files": [],
        "git": [],
    }

    print(f"skill={args.skill}")
    print("surfaces:")
    for root in skill_roots:
        exists = "yes" if root.exists() else "no"
        print(f"  - {root} exists={exists}")
    print("")

    for rel in rels:
        states = [collect(root, rel) for root in skill_roots]
        signatures = {(s.exists, s.sha256) for s in states}
        file_drift = len(signatures) > 1
        drift = drift or file_drift
        marker = "DRIFT" if file_drift else "OK"
        print(f"[{marker}] {rel}")
        file_record = {"rel": rel, "status": marker, "states": [asdict(s) for s in states]}
        evidence["files"].append(file_record)
        for state in states:
            exists = "yes" if state.exists else "no"
            print(
                "  {root} exists={exists} sha={sha} size={size} mtime={mtime} git={git}".format(
                    root=state.root,
                    exists=exists,
                    sha=shorten(state.sha256),
                    size=state.size if state.exists else "-",
                    mtime=state.mtime_utc if state.exists else "-",
                    git=state.git_commit or "-",
                )
            )

    upstream_drift = False
    if args.check_git or args.fail_on_upstream_drift:
        print("\ngit-surfaces:")
        repos: list[Path] = []
        seen_repos: set[str] = set()
        for root in skill_roots:
            repo = find_git_root(root)
            if repo is None:
                continue
            key = str(repo).lower()
            if key not in seen_repos:
                repos.append(repo)
                seen_repos.add(key)
        for repo in repos:
            state = git_state(repo)
            repo_bad = bool(state.error) or state.ahead != 0 or state.behind != 0 or state.dirty_count != 0
            upstream_drift = upstream_drift or repo_bad
            marker = "DRIFT" if repo_bad else "OK"
            evidence["git"].append(asdict(state) | {"status": marker})
            print(
                f"[{marker}] {state.repo} branch={state.branch or '-'} upstream={state.upstream or '-'} "
                f"ahead={state.ahead} behind={state.behind} dirty={state.dirty_count} error={state.error or '-'}"
            )

    if args.json_out:
        out_path = expand_path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\njson_out={out_path}")

    if drift:
        print("\nresult=drift_detected")
    elif upstream_drift:
        print("\nresult=upstream_drift_detected")
    else:
        print("\nresult=all_checked_surfaces_match")
    return_code = 0
    if drift and args.fail_on_drift:
        return_code = max(return_code, 2)
    if upstream_drift and args.fail_on_upstream_drift:
        return_code = max(return_code, 3)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
