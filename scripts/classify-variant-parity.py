#!/usr/bin/env python3
"""Classify q-workflow public/company variant parity audit findings.

This script consumes the Markdown emitted by audit-variant-parity.py and writes
a review-oriented classification draft. It does not modify either starter.
Policy comes from `docs/governance/VARIANT_MAP.json` when available.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SECTION_TITLES = {
    "### Canonical Mapping Collisions": "mapping_collisions",
    "### Missing In Company": "missing_in_company",
    "### Missing In Public": "missing_in_public",
    "### Changed Shared Text Files": "changed_text",
    "### Changed Shared Binary Files": "changed_binary",
}


@dataclass(frozen=True)
class Row:
    finding: str
    decision: str
    reason: str


def load_policy(path: Path | None, audit_path: Path) -> tuple[dict[str, Any], str]:
    candidates: list[Path] = []
    if path:
        candidates.append(path)
    for raw in audit_path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("- Variant map: `") and raw.endswith("`"):
            candidate = Path(raw.split("`", 2)[1])
            candidates.append(candidate)
            break
    for candidate in candidates:
        if candidate.is_file():
            return json.loads(candidate.read_text(encoding="utf-8-sig")), str(candidate.resolve())
    return {}, "<none>"


def entries(policy: dict[str, Any], key: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for entry in policy.get(key, []):
        if isinstance(entry, str):
            result.append({"prefix": entry, "decision": key, "reason": "Legacy string map entry."})
        elif isinstance(entry, dict):
            result.append({str(k): str(v) for k, v in entry.items()})
    return result


def match_prefix(value: str, items: list[dict[str, str]]) -> dict[str, str] | None:
    for entry in items:
        prefix = entry.get("prefix", "")
        if prefix and (value == prefix or value.startswith(prefix)):
            return entry
    return None


def match_pattern(value: str, items: list[dict[str, str]]) -> dict[str, str] | None:
    for entry in items:
        pattern = entry.get("pattern", "")
        if pattern and pattern in value:
            return entry
    return None


def parse_audit(path: Path) -> dict[str, list[str]]:
    current: str | None = None
    sections: dict[str, list[str]] = {key: [] for key in SECTION_TITLES.values()}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line in SECTION_TITLES:
            current = SECTION_TITLES[line]
            continue
        if line.startswith("### "):
            current = None
            continue
        if current and line.startswith("- `") and line.endswith("`"):
            item = line[3:-1]
            if item != "None":
                sections[current].append(item)
    return sections


def classify_collision(item: str) -> Row:
    return Row(item, "mapping-collision-review", "Multiple paths map to the same canonical key; inspect before trusting parity output.")


def classify_missing_in_company(item: str, policy: dict[str, Any]) -> Row:
    public_only = match_prefix(item, entries(policy, "public_only_prefixes"))
    if public_only:
        return Row(item, public_only.get("decision", "public-only"), public_only.get("reason", "Public-only surface."))
    generic = match_prefix(item, entries(policy, "generic_sync_prefixes"))
    if generic:
        return Row(item, generic.get("decision", "sync-required"), generic.get("reason", "Generic behavior should normally exist in company variant too."))
    return Row(item, "review", "Missing in company starter and not covered by the variant map.")


def classify_missing_in_public(item: str, policy: dict[str, Any]) -> Row:
    company_only = match_prefix(item, entries(policy, "company_only_prefixes"))
    if company_only:
        return Row(item, company_only.get("decision", "company-only"), company_only.get("reason", "Company-only surface."))
    generic = match_prefix(item, entries(policy, "generic_sync_prefixes"))
    if generic:
        return Row(item, "sanitize-to-public", generic.get("reason", "Looks generic enough to consider for public after public-safe scan and naming rewrite."))
    return Row(item, "review", "Missing in public starter and not covered by the variant map.")


def classify_changed(item: str, policy: dict[str, Any], binary: bool = False) -> Row:
    left = item.split(" <-> ", 1)[0]
    variant_text = match_prefix(left, entries(policy, "changed_text_review_prefixes"))
    if variant_text:
        return Row(item, variant_text.get("decision", "variant-text-allowed"), variant_text.get("reason", "Text difference is intentionally variant-specific."))
    if binary:
        return Row(item, "binary-review", "Binary or non-text difference; inspect manually before sync.")
    generic = match_prefix(left, entries(policy, "generic_sync_prefixes"))
    if generic:
        return Row(item, generic.get("decision", "sync-required"), generic.get("reason", "Generic shared surface changed; synchronize or record a pending parity item."))
    counterpart = match_pattern(item, entries(policy, "counterpart_review_patterns"))
    if counterpart:
        return Row(item, counterpart.get("decision", "counterpart-review"), counterpart.get("reason", "Mapped counterpart; align generic behavior intentionally."))
    return Row(item, "doc-or-text-review", "Shared text changed and is not covered by a counterpart pattern; classify as synchronized, variant-specific, or pending sync.")


def table(rows: list[Row]) -> str:
    if not rows:
        return "- None\n"
    lines = ["| Finding | Decision | Reason |", "|---|---|---|"]
    for row in rows:
        finding = row.finding.replace("|", "\\|")
        reason = row.reason.replace("|", "\\|")
        lines.append(f"| `{finding}` | `{row.decision}` | {reason} |")
    return "\n".join(lines) + "\n"


def build_classification(audit_path: Path, policy: dict[str, Any], policy_label: str) -> str:
    sections = parse_audit(audit_path)
    rows_collision = [classify_collision(item) for item in sections["mapping_collisions"]]
    rows_company = [classify_missing_in_company(item, policy) for item in sections["missing_in_company"]]
    rows_public = [classify_missing_in_public(item, policy) for item in sections["missing_in_public"]]
    rows_text = [classify_changed(item, policy) for item in sections["changed_text"]]
    rows_binary = [classify_changed(item, policy, binary=True) for item in sections["changed_binary"]]
    return "\n".join([
        "# Variant Parity Classification", "",
        f"Source audit: `{audit_path}`",
        f"Variant map: `{policy_label}`", "",
        "## Canonical Mapping Collisions", "", table(rows_collision),
        "## Missing In Company", "", table(rows_company),
        "## Missing In Public", "", table(rows_public),
        "## Changed Shared Text Files", "", table(rows_text),
        "## Changed Shared Binary Files", "", table(rows_binary),
        "## Required Expert Pass", "",
        "- `Workflow Distiller`: confirm the classification matches q-workflow parity policy and update durable state/TODOs.",
        "- `Code Auditor`: review any sync scripts, path handling, generated diffs, and validation failures before commit.",
        "- `Usability Validator`: review setup/onboarding/package usability when starter install paths, quick commands, or bundled skill sets changed.",
        "- Conditional: `Pagewright` for HTML/setup pages, `Visual Arbiter` for diagram/PPT visual surfaces, and `Doc Architect` for shared docs.", "",
        "## Policy", "",
        "This file is a draft. It does not prove a sync is safe by itself. For company-to-public movement, rewrite company-specific details into generic behavior and run the public scan before committing. Any `review`, `doc-or-text-review`, or `binary-review` row needs an owner, reason, and next action before release.", "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit_report", type=Path)
    parser.add_argument("--variant-map", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.audit_report.is_file():
        parser.error(f"audit report not found: {args.audit_report}")
    policy, policy_label = load_policy(args.variant_map.resolve() if args.variant_map else None, args.audit_report.resolve())
    result = build_classification(args.audit_report.resolve(), policy, policy_label)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result, encoding="utf-8", newline="\n")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
