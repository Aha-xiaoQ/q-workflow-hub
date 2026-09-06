#!/usr/bin/env python3
"""Audit local folder, registry/profile, and Git remote identity alignment."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


BROAD_KEYS = {"project", "projects", "repo", "repos", "skills", "test", "demo", "tmp"}


@dataclass
class Finding:
    level: str
    code: str
    path: str
    message: str


@dataclass
class RegistryEntry:
    project: str
    local_path: str
    remote: str
    resume_skill: str
    status: str


def add(findings: list[Finding], level: str, code: str, path: Path | str, message: str) -> None:
    findings.append(Finding(level, code, str(path), message))


def strip_cell(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`") and len(value) >= 2:
        value = value[1:-1]
    return value.strip()


def run_git(root: Path, args: list[str]) -> str | None:
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


def normalize_remote(remote: str) -> str:
    if not remote:
        return ""
    value = remote.strip().replace("\\", "/").rstrip("/")
    if value.startswith("git@") and ":" in value:
        host = value[4:].split(":", 1)[0]
        path = value.split(":", 1)[1]
        value = f"{host}/{path}"
    else:
        parsed = urlparse(value)
        host = parsed.netloc.split("@")[-1].lower()
        path = parsed.path.strip("/")
        value = f"{host}/{path}" if host else path
    if value.endswith(".git"):
        value = value[:-4]
    return value.lower()


def repo_slug(remote: str) -> str:
    norm = normalize_remote(remote)
    if not norm:
        return ""
    return norm.rsplit("/", 1)[-1].lower()


def load_q_profile(path: Path | None) -> dict:
    if not path or not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def read_registry(path: Path | None) -> list[RegistryEntry]:
    entries: list[RegistryEntry] = []
    if not path or not path.is_file():
        return entries
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return entries
    for line in lines:
        if not line.strip().startswith("|") or line.lstrip().startswith("|---"):
            continue
        cells = [strip_cell(cell) for cell in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] == "Project":
            continue
        entries.append(RegistryEntry(cells[0], cells[2], cells[3], cells[4], cells[5]))
    return entries


def same_path(a: str, b: Path) -> bool:
    if not a:
        return False
    try:
        return str(Path(a).resolve()).lower() == str(b.resolve()).lower()
    except OSError:
        return False


def profile_entry_for_path(profile: dict, root: Path) -> tuple[str | None, dict | None]:
    repos = profile.get("repositories")
    if not isinstance(repos, dict):
        return None, None
    for key, entry in repos.items():
        if not isinstance(entry, dict):
            continue
        for field in ("path", "local_path", "registry_path"):
            if same_path(str(entry.get(field, "")), root):
                return key, entry
    return None, None


def registry_entry_for_path(entries: list[RegistryEntry], root: Path) -> RegistryEntry | None:
    for entry in entries:
        if same_path(entry.local_path, root):
            return entry
    return None


def collect_aliases(entry: dict | None) -> tuple[list[str], list[str]]:
    aliases: list[str] = []
    defects: list[str] = []
    if not entry:
        return aliases, defects
    raw_aliases = entry.get("aliases", [])
    if isinstance(raw_aliases, list):
        for item in raw_aliases:
            if isinstance(item, dict):
                required = ["old_name", "new_name", "reason", "retirement_condition", "validated_at"]
                missing = [field for field in required if not item.get(field)]
                if missing:
                    defects.append("alias object missing " + ",".join(missing))
                for field in ("old_name", "new_name", "path"):
                    if item.get(field):
                        aliases.append(str(item[field]).lower())
            else:
                aliases.append(str(item).lower())
    for field in ("path", "local_path", "registry_path"):
        if entry.get(field):
            aliases.append(str(entry[field]).lower())
    return sorted(set(item for item in aliases if item)), defects


def audit_one(root: Path, profile: dict, registry: list[RegistryEntry], expected_slug: str | None, allow_unregistered: bool, findings: list[Finding]) -> dict:
    root = root.resolve()
    result = {
        "path": str(root),
        "folder": root.name,
        "git": False,
        "remote": "",
        "remote_identity": "",
        "remote_slug": "",
        "canonical_slug": "",
        "expected_remote_identity": "",
        "profile_key": None,
        "registry_key": None,
        "profile_aliases": [],
        "status": "error",
    }

    if not root.exists():
        add(findings, "error", "missing-root", root, "Repository path does not exist.")
        return result
    if not root.is_dir():
        add(findings, "error", "root-not-directory", root, "Repository path is not a directory.")
        return result

    top = run_git(root, ["rev-parse", "--show-toplevel"])
    if not top:
        add(findings, "error", "not-git-repo", root, "Path is not inside a Git worktree.")
        return result
    root = Path(top).resolve()
    result["path"] = str(root)
    result["folder"] = root.name
    result["git"] = True

    remote = run_git(root, ["remote", "get-url", "origin"]) or ""
    result["remote"] = remote
    result["remote_identity"] = normalize_remote(remote)
    result["remote_slug"] = repo_slug(remote)

    profile_key, profile_entry = profile_entry_for_path(profile, root)
    registry_entry = registry_entry_for_path(registry, root)
    aliases, alias_defects = collect_aliases(profile_entry)
    result["profile_key"] = profile_key
    result["registry_key"] = registry_entry.project if registry_entry else None
    result["profile_aliases"] = aliases

    canonical = (expected_slug or profile_key or (registry_entry.project if registry_entry else "") or "").lower()
    expected_remote = ""
    if profile_entry and profile_entry.get("remote"):
        expected_remote = str(profile_entry["remote"])
    elif registry_entry and registry_entry.remote and not registry_entry.remote.lower().startswith("deleted remote"):
        expected_remote = registry_entry.remote
    result["canonical_slug"] = canonical
    result["expected_remote_identity"] = normalize_remote(expected_remote)

    if not canonical:
        level = "warning" if allow_unregistered else "error"
        add(findings, level, "unregistered-repository", root, "Repository is not in q-profile or PROJECT_REGISTRY; canonical identity is not authoritative.")
        canonical = result["remote_slug"] or root.name.lower()
        result["canonical_slug"] = canonical

    if canonical in BROAD_KEYS:
        add(findings, "error", "broad-canonical-key", root, f"Canonical key {canonical} is too broad for active recovery.")

    if alias_defects:
        add(findings, "warning", "alias-metadata-incomplete", root, "; ".join(alias_defects))

    if not remote:
        add(findings, "warning", "missing-origin", root, "Git repo has no origin remote; remote identity cannot be verified.")
    else:
        if result["remote_slug"] != canonical:
            add(findings, "warning", "remote-slug-mismatch", root, f"Remote slug {result['remote_slug']} differs from canonical slug {canonical}.")
        if expected_remote and result["remote_identity"] != result["expected_remote_identity"]:
            add(findings, "error", "remote-identity-mismatch", root, f"Origin {result['remote_identity']} differs from expected {result['expected_remote_identity']}.")

    folder = root.name.lower()
    folder_matches = folder == canonical
    alias_matches = folder in aliases or str(root).lower() in aliases
    if not folder_matches and not alias_matches:
        add(findings, "warning", "undocumented-local-alias", root, f"Local folder {root.name} differs from canonical slug {canonical} and is not recorded as an alias.")

    if not profile_key:
        level = "warning" if allow_unregistered else "error"
        add(findings, level, "not-in-profile", root, "Repository path is not recorded in q-profile repositories.")
    if not registry_entry and not profile_key:
        add(findings, "warning", "not-in-registry", root, "Repository path is not recorded in PROJECT_REGISTRY.")

    result["status"] = "pass"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local/remote repository naming identity.")
    parser.add_argument("--root", action="append", required=True, help="Repository root to audit. Repeat for multiple repos.")
    parser.add_argument("--q-profile", default=None, help="q-profile.json path. Defaults to USERPROFILE/.codex/q-profile.json when available.")
    parser.add_argument("--project-registry", default=None, help="PROJECT_REGISTRY.md path. Defaults to <q-profile hub>/PROJECT_REGISTRY.md when available.")
    parser.add_argument("--expected-slug", default=None, help="Canonical slug for a single --root audit.")
    parser.add_argument("--allow-unregistered", action="store_true", help="Downgrade unregistered repositories from error to warning for external/link-only probes.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when warnings exist.")
    args = parser.parse_args()

    profile_path = Path(args.q_profile) if args.q_profile else Path.home() / ".codex" / "q-profile.json"
    profile = load_q_profile(profile_path)
    registry_path = Path(args.project_registry) if args.project_registry else None
    if registry_path is None and profile.get("hub"):
        registry_path = Path(str(profile["hub"])) / "PROJECT_REGISTRY.md"
    registry = read_registry(registry_path)

    findings: list[Finding] = []
    repos = [audit_one(Path(root), profile, registry, args.expected_slug, args.allow_unregistered, findings) for root in args.root]

    errors = sum(1 for item in findings if item.level == "error")
    warnings = sum(1 for item in findings if item.level == "warning")
    result = {
        "status": "error" if errors else ("warning" if warnings else "pass"),
        "errors": errors,
        "warnings": warnings,
        "q_profile": str(profile_path),
        "project_registry": str(registry_path) if registry_path else "",
        "repositories": repos,
        "findings": [asdict(item) for item in findings],
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Repository identity audit: {result['status'].upper()} ({errors} errors, {warnings} warnings)")
        for repo in repos:
            print(f"- {repo['folder']}: canonical={repo['canonical_slug'] or '(none)'} remote={repo['remote_identity'] or '(none)'} profile_key={repo['profile_key'] or '(none)'} registry_key={repo['registry_key'] or '(none)'}")
        for item in findings:
            print(f"[{item.level.upper()}] {item.code}: {item.path} - {item.message}")

    if errors:
        return 1
    if args.strict and warnings:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
