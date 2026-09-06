#!/usr/bin/env python3
"""Compare public and company q-workflow starter variants.

The script inventories two starter roots, applies counterpart path mappings,
and emits a Markdown report that separates missing files, changed common files,
and allowed variant-only surfaces. The policy is loaded from
`docs/governance/VARIANT_MAP.json` when available.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


SKIP_DIR_NAMES = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", "local-state"}
TEXT_EXTENSIONS = {".md", ".txt", ".ps1", ".py", ".json", ".yaml", ".yml", ".html", ".template"}

DEFAULT_POLICY: dict[str, Any] = {
    "canonical_mappings": {"public": {}, "company": {}},
    "public_only_prefixes": [],
    "company_only_prefixes": [],
}


@dataclass(frozen=True)
class FileInfo:
    rel: str
    size: int
    sha256: str
    text_like: bool


def normalize_rel(path: Path) -> str:
    return path.as_posix()


def load_policy(path: Path | None, public_root: Path, company_root: Path) -> tuple[dict[str, Any], Path | None]:
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    candidates.extend([
        public_root / "docs" / "governance" / "VARIANT_MAP.json",
        company_root / "docs" / "governance" / "VARIANT_MAP.json",
    ])
    for candidate in candidates:
        if candidate and candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8-sig")), candidate.resolve()
    return DEFAULT_POLICY, None


def entry_prefixes(policy: dict[str, Any], key: str) -> tuple[str, ...]:
    result: list[str] = []
    for entry in policy.get(key, []):
        if isinstance(entry, str):
            result.append(entry)
        elif isinstance(entry, dict) and entry.get("prefix"):
            result.append(str(entry["prefix"]))
    return tuple(result)


def validate_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    allowed = set(policy.get("waiver_policy", {}).get("allowed_decisions", []))
    if not isinstance(policy.get("canonical_mappings", {}), dict):
        errors.append("canonical_mappings must be an object")
    for variant in ("public", "company"):
        mappings = policy.get("canonical_mappings", {}).get(variant, {})
        if not isinstance(mappings, dict):
            errors.append(f"canonical_mappings.{variant} must be an object")
    for group_name, key_name in (("public_only_prefixes", "prefix"), ("company_only_prefixes", "prefix"), ("generic_sync_prefixes", "prefix"), ("counterpart_review_patterns", "pattern"), ("changed_text_review_prefixes", "prefix")):
        seen: set[str] = set()
        for index, entry in enumerate(policy.get(group_name, []), start=1):
            if not isinstance(entry, dict):
                errors.append(f"{group_name}[{index}] must be an object")
                continue
            key_value = str(entry.get(key_name, ""))
            if not key_value:
                errors.append(f"{group_name}[{index}] missing {key_name}")
            if key_value in seen:
                errors.append(f"{group_name}[{index}] duplicates {key_name} {key_value}")
            seen.add(key_value)
            decision = str(entry.get("decision", ""))
            if not decision:
                errors.append(f"{group_name}[{index}] missing decision")
            elif allowed and decision not in allowed:
                errors.append(f"{group_name}[{index}] decision {decision} not in waiver_policy.allowed_decisions")
            if not str(entry.get("reason", "")):
                errors.append(f"{group_name}[{index}] missing reason")
    return errors


def canonical_rel(rel: str, variant: str, policy: dict[str, Any]) -> str:
    mappings = policy.get("canonical_mappings", {}).get(variant, {})
    for variant_prefix, canonical_prefix in mappings.items():
        if rel.startswith(variant_prefix):
            return canonical_prefix + rel[len(variant_prefix):]
    return rel


def is_skipped(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    return any(part in SKIP_DIR_NAMES for part in parts)


def is_text_like(path: Path) -> bool:
    name = path.name.lower()
    if name.endswith(".md.template") or name.endswith(".html.template"):
        return True
    if name in {".gitignore", ".gitattributes"}:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> dict[str, FileInfo]:
    result: dict[str, FileInfo] = {}
    for path in root.rglob("*"):
        if not path.is_file() or is_skipped(path, root):
            continue
        rel = normalize_rel(path.relative_to(root))
        result[rel] = FileInfo(rel=rel, size=path.stat().st_size, sha256=hash_file(path), text_like=is_text_like(path))
    return result


def has_prefix(rel: str, prefixes: tuple[str, ...]) -> bool:
    return any(rel == prefix or rel.startswith(prefix) for prefix in prefixes)


def canonical_inventory(files: dict[str, FileInfo], variant: str, policy: dict[str, Any]) -> tuple[dict[str, FileInfo], list[str]]:
    grouped: dict[str, list[FileInfo]] = {}
    for rel, info in files.items():
        grouped.setdefault(canonical_rel(rel, variant, policy), []).append(info)
    collapsed: dict[str, FileInfo] = {}
    collisions: list[str] = []
    for key, infos in grouped.items():
        ordered = sorted(infos, key=lambda item: item.rel)
        collapsed[key] = ordered[0]
        if len(ordered) > 1:
            names = " | ".join(item.rel for item in ordered)
            hashes = ",".join(sorted({item.sha256[:12] for item in ordered}))
            collisions.append(f"{variant}:{key} <= {names} [sha12={hashes}]")
    return collapsed, collisions


def md_list(items: list[str], limit: int | None = None) -> str:
    if not items:
        return "- None\n"
    visible = items if limit is None else items[:limit]
    lines = [f"- `{item}`" for item in visible]
    if limit is not None and len(items) > limit:
        lines.append(f"- ... {len(items) - limit} more")
    return "\n".join(lines) + "\n"


def build_report(public_root: Path, company_root: Path, policy: dict[str, Any], policy_path: Path | None) -> str:
    public_files = inventory(public_root)
    company_files = inventory(company_root)
    public_by_key, public_collisions = canonical_inventory(public_files, "public", policy)
    company_by_key, company_collisions = canonical_inventory(company_files, "company", policy)
    mapping_collisions = public_collisions + company_collisions
    company_only_prefixes = entry_prefixes(policy, "company_only_prefixes")
    public_only_prefixes = entry_prefixes(policy, "public_only_prefixes")

    missing_in_company: list[str] = []
    missing_in_public: list[str] = []
    changed_common: list[str] = []
    changed_binary: list[str] = []

    for key in sorted(set(public_by_key) | set(company_by_key)):
        public_info = public_by_key.get(key)
        company_info = company_by_key.get(key)
        if public_info is None:
            rel = company_info.rel if company_info else key
            if not has_prefix(rel, company_only_prefixes):
                missing_in_public.append(rel)
            continue
        if company_info is None:
            rel = public_info.rel
            if not has_prefix(rel, public_only_prefixes):
                missing_in_company.append(rel)
            continue
        if public_info.sha256 != company_info.sha256:
            item = f"{public_info.rel} <-> {company_info.rel}"
            if public_info.text_like and company_info.text_like:
                changed_common.append(item)
            else:
                changed_binary.append(item)

    company_only_allowed = sorted(rel for rel in company_files if has_prefix(rel, company_only_prefixes))
    public_only_allowed = sorted(rel for rel in public_files if has_prefix(rel, public_only_prefixes))
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    policy_label = str(policy_path) if policy_path else "<none; fallback empty policy>"
    lines = [
        "# Variant Parity Audit", "",
        f"- Generated: {now}",
        f"- Public root: `{public_root}`",
        f"- Company root: `{company_root}`",
        f"- Variant map: `{policy_label}`",
        f"- Map status: `{policy.get('status', 'unknown')}`",
        f"- Public files scanned: {len(public_files)}",
        f"- Company files scanned: {len(company_files)}", "",
        "## Blocking Review Candidates", "",
        "These are not automatically wrong. They require a sync decision before a shared release.", "",
        "### Canonical Mapping Collisions", "", md_list(mapping_collisions),
        "### Missing In Company", "", md_list(missing_in_company),
        "### Missing In Public", "", md_list(missing_in_public),
        "### Changed Shared Text Files", "", md_list(changed_common),
        "### Changed Shared Binary Files", "", md_list(changed_binary),
        "## Allowed Variant-Only Surfaces", "",
        "### Company Only", "", md_list(company_only_allowed),
        "### Public Only", "", md_list(public_only_allowed),
        "## Review Rules", "",
        "- Raw company artifacts with organization-specific marks, internal paths, template binaries, customer/project material, or local active-state data must not be copied to public.",
        "- Generic workflow behavior, setup/onboarding improvements, quick commands, validation gates, and sanitized UI mechanisms should be propagated or recorded as a pending parity TODO.",
        "- A changed shared text file is acceptable only when the difference is named in `docs/governance/VARIANT_MAP.json`, `docs/governance/COMPANY_DELTA.md`, `docs/governance/PUBLIC_SYNC.md`, or the current work report with owner, reason, and next action.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-root", required=True, type=Path)
    parser.add_argument("--company-root", required=True, type=Path)
    parser.add_argument("--variant-map", type=Path, help="Machine-readable variant policy JSON. Defaults to docs/governance/VARIANT_MAP.json when present.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    public_root = args.public_root.resolve()
    company_root = args.company_root.resolve()
    if not public_root.is_dir():
        parser.error(f"public root does not exist: {public_root}")
    if not company_root.is_dir():
        parser.error(f"company root does not exist: {company_root}")
    policy, policy_path = load_policy(args.variant_map.resolve() if args.variant_map else None, public_root, company_root)
    policy_errors = validate_policy(policy)
    if policy_errors:
        for error in policy_errors:
            print(f"variant map error: {error}", file=sys.stderr)
        return 2
    report = build_report(public_root, company_root, policy, policy_path)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8", newline="\n")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
