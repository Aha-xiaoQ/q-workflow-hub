#!/usr/bin/env python3
"""Dependency-free contract check for this skill's taxonomy metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "skill_id", "display_name", "variant", "category", "status",
    "publish_profile", "source_of_truth", "runtime_paths",
    "activation_contract", "output_contract", "dependencies",
    "composition_boundary", "encoding_guard", "validation",
    "review_ownership", "sync_notes",
}
ALLOWED = {
    "variant": {"generic", "company", "project", "runtime", "external"},
    "category": {"router", "workflow", "domain", "tool", "intake", "review", "profile", "project", "orchestration"},
    "status": {"candidate", "pilot", "stable", "deprecated", "archived"},
    "publish_profile": {"private", "company", "public"},
    "encoding_guard": {"required", "optional", "not-applicable"},
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("metadata", type=Path)
    ns = ap.parse_args()
    values: dict[str, str] = {}
    for raw in ns.metadata.read_text(encoding="utf-8").splitlines():
        if not raw or raw[0].isspace() or raw.lstrip().startswith("#"):
            continue
        key, sep, value = raw.partition(":")
        if sep:
            values[key.strip()] = value.strip()
    errors = [f"missing top-level key: {key}" for key in sorted(REQUIRED-values.keys())]
    for key, choices in ALLOWED.items():
        if key in values and values[key] not in choices:
            errors.append(f"{key}={values[key]!r} not in {sorted(choices)}")
    result = {"status": "PASS" if not errors else "FAIL", "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
