#!/usr/bin/env python3
"""Read-only q-workflow project structure audit."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


CORE_FILES = [
    "README.md",
    "PROJECT_STATE.md",
    "TASKS.md",
    "DECISIONS.md",
    "CONTINUATION_PROMPT.md",
    "ENVIRONMENT.md",
    "PROJECT_OVERVIEW.md",
    ".gitignore",
]

LIFECYCLE_DIRS = [
    "00-project",
    "01-inputs",
    "02-research",
    "03-work",
    "04-outputs",
    "05-validation",
    "06-handoff",
    "90-archive",
]

OPTIONAL_ROOT = {
    ".git",
    ".gitattributes",
    "PROJECT_OVERVIEW.html",
    "skills",
    "99-local-state",
    # Legacy roots are allowed during staged migrations, but reported separately.
    "docs",
    "reports",
    "scripts",
    "assets",
    "archive",
    "local-state",
}

PROFILE_DIRS = {
    "generic": [],
    "document-only": [
        "01-inputs",
        "02-research",
        "03-work/docs",
        "04-outputs/reports",
        "05-validation/document-review",
    ],
    "research-deck": [
        "01-inputs/papers",
        "01-inputs/templates",
        "01-inputs/source-ppts",
        "02-research/literature-notes",
        "02-research/template-reverse",
        "02-research/expert-review",
        "03-work/decks",
        "03-work/diagrams",
        "03-work/scripts",
        "04-outputs/decks",
        "04-outputs/reports",
        "04-outputs/figures",
        "05-validation/ppt-visual-review",
        "05-validation/structure-audit",
    ],
    "software-tool": [
        "03-work/software",
        "04-outputs/releases",
        "05-validation/test-results",
        "05-validation/lint",
    ],
    "firmware-board": [
        "01-inputs/vendor-docs",
        "01-inputs/bsp-references",
        "01-inputs/requirements",
        "02-research/porting-notes",
        "02-research/board-analysis",
        "03-work/firmware",
        "03-work/hardware",
        "03-work/tools",
        "04-outputs/builds",
        "04-outputs/demos",
        "04-outputs/release-packages",
        "05-validation/build-logs",
        "05-validation/debug-logs",
        "05-validation/test-results",
    ],
    "hardware-design": [
        "01-inputs/datasheets",
        "01-inputs/requirements",
        "03-work/hardware",
        "03-work/diagrams",
        "04-outputs/fabrication",
        "04-outputs/assembly",
        "04-outputs/figures",
        "05-validation/erc-drc",
        "05-validation/design-review",
    ],
    "external-based": [
        "01-inputs/external",
        "02-research/external-review",
        "03-work/adapted-project",
        "03-work/patches",
        "06-handoff/external-sync",
    ],
    "workflow-or-skill": [
        "skills",
        "references",
        "03-work/scripts",
        "03-work/templates",
        "04-outputs/packages",
        "05-validation/audits",
        "05-validation/parity",
        "05-validation/release",
    ],
}

LEGACY_ROOTS = {"docs", "reports", "scripts", "assets", "archive", "local-state"}
TRANSIENT_NAMES = {"__pycache__", ".pytest_cache", "node_modules", "dist", "build", "tmp", "temp"}
TRANSIENT_PATTERNS = [re.compile(r"slides?_png$", re.IGNORECASE), re.compile(r"^slide_\d+\.png$", re.IGNORECASE)]


@dataclass
class Finding:
    level: str
    code: str
    path: str
    message: str


def add(findings: list[Finding], level: str, code: str, path: Path | str, message: str) -> None:
    findings.append(Finding(level, code, str(path), message))


def git(root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def is_slug(name: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name))


def file_mentions_deferred(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return False
    return "defer" in text or "deferred" in text or "omitted" in text or "迁移" in text or "暂缓" in text


def check_required(root: Path, profile: str, findings: list[Finding], relaxed: bool) -> None:
    for name in CORE_FILES:
        path = root / name
        if not path.is_file():
            add(findings, "error", "missing-core-file", path, f"Missing durable root file {name}.")

    structure_doc = root / "00-project" / "PROJECT_STRUCTURE.md"
    readme = root / "README.md"
    deferral_recorded = file_mentions_deferred(structure_doc) or file_mentions_deferred(readme)

    for name in LIFECYCLE_DIRS:
        path = root / name
        if path.is_dir():
            continue
        if relaxed:
            level = "warning" if not deferral_recorded else "info"
            add(findings, level, "missing-lifecycle-dir-relaxed", path, f"Lifecycle directory {name}/ is deferred in relaxed mode.")
        else:
            add(findings, "error", "missing-lifecycle-dir", path, f"Missing lifecycle directory {name}/.")

    for rel in PROFILE_DIRS[profile]:
        path = root / rel
        if not path.exists():
            add(findings, "warning", "missing-profile-path", path, f"Recommended {profile} path is absent.")

    if not structure_doc.exists():
        add(findings, "warning", "missing-structure-doc", structure_doc, "Nontrivial projects should define 00-project/PROJECT_STRUCTURE.md.")


def check_gitignore(root: Path, findings: list[Finding]) -> None:
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return
    try:
        text = gitignore.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
    except OSError as exc:
        add(findings, "warning", "gitignore-unreadable", gitignore, f"Could not read .gitignore: {exc}")
        return
    required_patterns = ["99-local-state/", "local-state/"]
    if not any(pattern in text for pattern in required_patterns):
        add(findings, "error", "missing-local-state-ignore", gitignore, ".gitignore should ignore 99-local-state/ for machine-local scratch.")


def check_root(root: Path, profile: str, findings: list[Finding], expected_slug: str | None) -> None:
    slug = expected_slug or root.name
    if not is_slug(root.name):
        add(findings, "error", "root-slug", root, "Project root folder should use lower-kebab-case.")
    if expected_slug and root.name != expected_slug:
        add(findings, "warning", "expected-slug", root, f"Root folder does not match expected slug {expected_slug}.")

    allowed = set(CORE_FILES) | set(LIFECYCLE_DIRS) | OPTIONAL_ROOT | {item.split("/", 1)[0] for item in PROFILE_DIRS[profile]}
    for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if child.name in LEGACY_ROOTS:
            add(findings, "warning", "legacy-root-layout", child, "Legacy root directory remains; migrate or document as compatibility alias.")
        elif child.name not in allowed:
            add(findings, "warning", "unclassified-root-item", child, "Root item is outside the standard lifecycle/profile layout.")

    remote = git(root, ["remote", "get-url", "origin"])
    if remote:
        remote_slug = remote.rstrip("/").rsplit("/", 1)[-1]
        if remote_slug.endswith(".git"):
            remote_slug = remote_slug[:-4]
        if remote_slug and remote_slug != slug:
            add(findings, "warning", "remote-slug-mismatch", root, f"Origin slug {remote_slug} differs from expected slug {slug}.")


def check_skills(root: Path, findings: list[Finding]) -> None:
    skills = root / "skills"
    if not skills.is_dir():
        return
    expected = f"{root.name}-workflow"
    candidate = skills / expected
    if not candidate.exists():
        add(findings, "warning", "project-skill-name", skills, f"Project-local skill should usually be skills/{expected}/.")
    for path in skills.iterdir():
        if path.is_dir() and path.name == "skills":
            add(findings, "error", "nested-skills", path, "Do not nest skills/skills; project-local skills belong directly under root skills/.")


def check_transient(root: Path, findings: list[Finding]) -> None:
    for path in root.rglob("*"):
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        rel_text = str(rel).replace("\\", "/")
        if rel_text.startswith(".git/") or rel_text.startswith("99-local-state/") or rel_text.startswith("local-state/"):
            continue
        if path.name in TRANSIENT_NAMES:
            add(findings, "warning", "transient-tracked-location", path, "Transient folder should normally be ignored or moved to 99-local-state/.")
        if any(pattern.search(path.name) for pattern in TRANSIENT_PATTERNS):
            add(findings, "warning", "raw-export-location", path, "Raw generated export should normally live under ignored 99-local-state/.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a q-workflow project layout without modifying files.")
    parser.add_argument("--root", required=True, help="Project root to audit.")
    parser.add_argument("--profile", choices=sorted(PROFILE_DIRS), default="generic")
    parser.add_argument("--expected-slug", default=None)
    parser.add_argument("--relaxed", action="store_true", help="Treat missing lifecycle directories as warnings for tiny or staged projects.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings exist.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings: list[Finding] = []
    if not root.exists():
        add(findings, "error", "missing-root", root, "Project root does not exist.")
    elif not root.is_dir():
        add(findings, "error", "root-not-directory", root, "Project root is not a directory.")
    else:
        check_root(root, args.profile, findings, args.expected_slug)
        check_required(root, args.profile, findings, args.relaxed)
        check_gitignore(root, findings)
        check_skills(root, findings)
        check_transient(root, findings)

    status = git(root, ["status", "--short", "--branch"]) if root.exists() else None
    errors = sum(1 for item in findings if item.level == "error")
    warnings = sum(1 for item in findings if item.level == "warning")
    infos = sum(1 for item in findings if item.level == "info")
    result = {
        "status": "error" if errors else ("warning" if warnings else "pass"),
        "project_root": str(root),
        "profile": args.profile,
        "errors": errors,
        "warnings": warnings,
        "infos": infos,
        "git_status": status,
        "findings": [asdict(item) for item in findings],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Project structure audit: {result['status'].upper()} ({errors} errors, {warnings} warnings, {infos} info)")
        if status:
            print(f"Git: {status.splitlines()[0]}")
        for item in findings:
            print(f"[{item.level.upper()}] {item.code}: {item.path} - {item.message}")

    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
