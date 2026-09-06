#!/usr/bin/env python3
"""Validate a q-ppt-intake/v1 request with standard-library checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_KEYS = {
    "schemaVersion",
    "createdAt",
    "profile",
    "deck",
    "content",
    "structure",
    "style",
    "validation",
    "output",
    "handoff",
    "extensions",
}

DECK_KEYS = {
    "title",
    "subtitle",
    "audience",
    "purpose",
    "deliveryFormat",
    "language",
    "density",
    "targetSlideCount",
    "notesMode",
}

DENSITY_RANGES = {
    "short": (6, 8),
    "standard": (10, 14),
    "sharing": (18, 22),
}

PRIVATE_FIELD_HINTS = {
    "classification",
    "templateclassification",
    "templatepath",
    "templatepathhint",
    "company",
    "organization",
    "vendor",
    "internal",
    "confidential",
    "restricted",
    "secret",
}


def as_object(value: Any, path: str, errors: list[str]) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    errors.append(f"{path} must be an object")
    return {}


def require_text(obj: dict[str, Any], key: str, path: str, errors: list[str]) -> None:
    if not isinstance(obj.get(key), str) or not obj[key].strip():
        errors.append(f"{path}.{key} is required")


def validate_private_field_leaks(node: Any, path: str, errors: list[str]) -> None:
    if path.startswith("extensions"):
        return
    if isinstance(node, dict):
        for key, value in node.items():
            compact = key.lower().replace("_", "").replace("-", "")
            if compact in PRIVATE_FIELD_HINTS:
                errors.append(f"{path}.{key} must move under extensions.<namespace>")
            validate_private_field_leaks(value, f"{path}.{key}", errors)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            validate_private_field_leaks(value, f"{path}[{index}]", errors)


def validate_request(data: dict[str, Any], actual_slide_count: int | None) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    unknown_root = sorted(set(data) - ROOT_KEYS)
    if unknown_root:
        errors.append(f"unknown top-level keys: {', '.join(unknown_root)}")

    if data.get("schemaVersion") != "q-ppt-intake/v1":
        errors.append("schemaVersion must be q-ppt-intake/v1")

    deck = as_object(data.get("deck"), "deck", errors)
    unknown_deck = sorted(set(deck) - DECK_KEYS)
    if unknown_deck:
        errors.append(f"unknown deck keys: {', '.join(unknown_deck)}")
    for key in ("title", "audience", "purpose", "deliveryFormat", "language", "density"):
        require_text(deck, key, "deck", errors)

    density = deck.get("density")
    if density not in DENSITY_RANGES:
        errors.append("deck.density must be one of short, standard, sharing")

    target_slide_count = deck.get("targetSlideCount")
    if target_slide_count is not None and not isinstance(target_slide_count, int):
        errors.append("deck.targetSlideCount must be an integer or null")
    if isinstance(target_slide_count, int) and target_slide_count <= 0:
        errors.append("deck.targetSlideCount must be positive")

    content = as_object(data.get("content"), "content", errors)
    source_materials = content.get("sourceMaterials", [])
    if not isinstance(source_materials, list):
        errors.append("content.sourceMaterials must be a list")

    validation = as_object(data.get("validation"), "validation", errors)
    for key in ("runStructuralReadback", "runVisualReview", "openFinalPpt"):
        if not isinstance(validation.get(key), bool):
            errors.append(f"validation.{key} must be boolean")

    extensions = data.get("extensions", {})
    if extensions is not None and not isinstance(extensions, dict):
        errors.append("extensions must be an object when present")

    validate_private_field_leaks(data, "request", errors)

    if actual_slide_count is not None:
        if isinstance(target_slide_count, int):
            if actual_slide_count != target_slide_count:
                errors.append(
                    f"actual slide count {actual_slide_count} does not match targetSlideCount {target_slide_count}"
                )
            else:
                notes.append(f"slide count matched exact target {target_slide_count}")
        elif density in DENSITY_RANGES:
            low, high = DENSITY_RANGES[density]
            if not low <= actual_slide_count <= high:
                errors.append(
                    f"actual slide count {actual_slide_count} outside {density} range {low}-{high}"
                )
            else:
                notes.append(f"slide count {actual_slide_count} inside {density} range {low}-{high}")
    elif density in DENSITY_RANGES and not isinstance(target_slide_count, int):
        low, high = DENSITY_RANGES[density]
        notes.append(f"density {density} maps to {low}-{high} slides")

    notes.append(f"source materials: {len(source_materials) if isinstance(source_materials, list) else 0}")
    return errors, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path)
    parser.add_argument("--actual-slide-count", type=int)
    args = parser.parse_args()

    try:
        data = json.loads(args.request.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR failed to read JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(data, dict):
        print("ERROR request JSON must be an object", file=sys.stderr)
        return 2

    errors, notes = validate_request(data, args.actual_slide_count)
    for note in notes:
        print(f"NOTE {note}")
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 1

    print("OK q-ppt-intake/v1 request is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
