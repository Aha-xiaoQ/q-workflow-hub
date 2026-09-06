#!/usr/bin/env python3
"""Validate structural contracts for pixel-semantic annotation JSON.

The executable gate checks schema, types, side/count consistency, bounds,
unions, completeness, and final status. It never claims visual-semantic truth;
final approval still requires per-sample native/grid review.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


class InputReadError(RuntimeError):
    """The validator could not read required external evidence."""


def union(boxes: list[list[int]]) -> list[int]:
    x0 = min(b[0] for b in boxes)
    y0 = min(b[1] for b in boxes)
    x1 = max(b[0] + b[2] for b in boxes)
    y1 = max(b[1] + b[3] for b in boxes)
    return [x0, y0, x1 - x0, y1 - y0]


def valid_box(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 4
        and all(type(v) is int for v in value)
        and value[0] >= 0
        and value[1] >= 0
        and value[2] > 0
        and value[3] > 0
    )


def side_complete(value: object, visible_sides: set[str]) -> tuple[bool, str | None]:
    if value is True:
        return True, None
    if not isinstance(value, dict) or not value:
        return False, "must be true or a non-empty left/right object"
    unknown = set(value) - {"left", "right"}
    if unknown:
        return False, f"contains unknown keys {sorted(unknown)}"
    for side in visible_sides:
        if value.get(side) is not True:
            return False, f"visible side {side} must be true"
    for side in {"left", "right"} - visible_sides:
        if side in value and not (
            value[side] is None
            or value[side] is False
            or value[side] == "not-applicable"
        ):
            return False, f"invisible side {side} must be null, false, not-applicable, or absent"
    return True, None


def declared_half_open(data: dict[str, Any]) -> bool:
    if data.get("box_semantics") == "xywh-half-open":
        return True
    box_format = data.get("box_format")
    if isinstance(box_format, str) and box_format.strip().lower() in {
        "xywh-half-open",
        "xywh half-open",
        "xywh; x/y inclusive; right/bottom exclusive",
    }:
        return True
    rules = data.get("annotation_rules")
    coordinates = rules.get("coordinates") if isinstance(rules, dict) else None
    return isinstance(coordinates, str) and coordinates.strip().lower() in {
        "xywh-half-open",
        "x/y inclusive; right/bottom exclusive",
    }


def parse_face_size(sample: dict[str, Any], faces_dir: Path | None) -> tuple[int, int] | None:
    value = sample.get("face_size")
    if isinstance(value, list) and len(value) == 2 and all(type(v) is int and v > 0 for v in value):
        return value[0], value[1]
    if faces_dir is None:
        return None
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise InputReadError("Pillow is required with --faces-dir") from exc
    path = faces_dir / f"{sample.get('id', '')}.png"
    try:
        with Image.open(path) as opened:
            return opened.size
    except (OSError, ValueError) as exc:
        raise InputReadError(f"cannot read face image {path}: {exc}") from exc


def validate_payload(
    data: object,
    *,
    expected_count: int | None = None,
    faces_dir: Path | None = None,
    final_gate: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["root JSON must be an object"]
    if data.get("schema") != "eye-semantic-manual-v1":
        errors.append("schema must be eye-semantic-manual-v1")
    if data.get("coordinate_space") != "face-crop-native-pixels":
        errors.append("coordinate_space must be face-crop-native-pixels")
    if data.get("eye_side_convention") != "screen-left/screen-right":
        errors.append("eye_side_convention must be screen-left/screen-right")
    if not declared_half_open(data):
        errors.append("box coordinates must declare xywh half-open semantics")
    samples = data.get("samples")
    if not isinstance(samples, list):
        errors.append("samples must be a list")
        return errors
    if not samples:
        errors.append("samples must contain at least one item")
    if expected_count is not None and len(samples) != expected_count:
        errors.append(f"sample count {len(samples)} != {expected_count}")
    seen: set[str] = set()
    for i, sample in enumerate(samples):
        prefix = f"samples[{i}]"
        if not isinstance(sample, dict):
            errors.append(f"{prefix} must be an object")
            continue
        sid = sample.get("id")
        normalized_sid = sid.strip() if isinstance(sid, str) else ""
        safe_sid = bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", normalized_sid)) and ".." not in normalized_sid
        label = normalized_sid or prefix
        if not isinstance(sid, str) or not sid.strip():
            errors.append(f"{prefix}.id must be a non-blank string")
        elif not safe_sid:
            errors.append(f"{prefix}.id must be a safe basename without whitespace or path traversal")
        elif normalized_sid in seen:
            errors.append(f"duplicate id after trimming: {normalized_sid}")
        else:
            seen.add(normalized_sid)

        visible: dict[str, list[int]] = {}
        for side, field in (("left", "screen_left_eye_box"), ("right", "screen_right_eye_box")):
            box = sample.get(field)
            if box is None:
                continue
            if not valid_box(box):
                errors.append(f"{label}.{field} must be four non-boolean integers with non-negative x/y and positive w/h, or null")
            else:
                visible[side] = box
        if not visible:
            errors.append(f"{label}: at least one visible eye box is required")
        declared_count = sample.get("visible_eye_count")
        if final_gate and type(declared_count) is not int:
            errors.append(f"{label}.visible_eye_count is required for final gate")
        if declared_count is not None and (type(declared_count) is not int or declared_count != len(visible)):
            errors.append(f"{label}.visible_eye_count must equal non-null box count {len(visible)}")
        if "left" in visible and "right" in visible:
            lc = visible["left"][0] + visible["left"][2] / 2
            rc = visible["right"][0] + visible["right"][2] / 2
            if lc >= rc:
                errors.append(f"{label}: screen-left eye center must be left of screen-right eye center")
        if len(visible) == 1 and final_gate:
            reasons = (
                sample.get("not_visible_reason"),
                sample.get("occlusion_reason"),
                sample.get("occlusion_by_hair"),
                sample.get("notes"),
            )
            if not any(isinstance(reason, str) and reason.strip() for reason in reasons):
                errors.append(f"{label}: single-eye final annotation requires a not-visible or occlusion reason")

        merged = sample.get("merged_eye_box")
        if not valid_box(merged):
            errors.append(f"{label}.merged_eye_box is invalid")
        elif visible and merged != union(list(visible.values())):
            errors.append(f"{label}.merged_eye_box must equal exact union {union(list(visible.values()))}")

        visible_sides = set(visible)
        for field in ("visible_eye_complete", "upper_lid_complete"):
            ok, reason = side_complete(sample.get(field), visible_sides)
            if not ok:
                errors.append(f"{label}.{field} {reason}")

        status = sample.get("status")
        if status not in {"annotated", "needs-review"}:
            errors.append(f"{label}.status must be annotated or needs-review")
        elif final_gate and status != "annotated":
            errors.append(f"{label}.status must be annotated at final gate")

        raw_face_size = sample.get("face_size")
        if raw_face_size is not None and not (
            isinstance(raw_face_size, list)
            and len(raw_face_size) == 2
            and all(type(v) is int and v > 0 for v in raw_face_size)
        ):
            errors.append(f"{label}.face_size must be two positive non-boolean integers")
        size = parse_face_size(sample, faces_dir if safe_sid else None)
        if final_gate and size is None:
            errors.append(f"{label}: final gate requires --faces-dir or a valid face_size")
        if size:
            width, height = size
            for field, box in (("screen_left_eye_box", sample.get("screen_left_eye_box")), ("screen_right_eye_box", sample.get("screen_right_eye_box")), ("merged_eye_box", merged)):
                if valid_box(box) and (box[0] + box[2] > width or box[1] + box[3] > height):
                    errors.append(f"{label}.{field} exceeds face bounds {width}x{height}")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("annotation", type=Path)
    ap.add_argument("--expected-count", type=int)
    ap.add_argument("--faces-dir", type=Path)
    ap.add_argument("--final-gate", action="store_true")
    ns = ap.parse_args()
    try:
        data = json.loads(ns.annotation.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "ERROR", "errors": [str(exc)], "semantic_authority": False}, ensure_ascii=False))
        return 2
    try:
        errors = validate_payload(data, expected_count=ns.expected_count, faces_dir=ns.faces_dir, final_gate=ns.final_gate)
    except InputReadError as exc:
        print(json.dumps({"status": "ERROR", "errors": [str(exc)], "semantic_authority": False}, ensure_ascii=False))
        return 2
    except Exception as exc:  # defensive boundary for automation callers
        print(json.dumps({"status": "ERROR", "errors": [f"unexpected runtime error: {exc}"], "semantic_authority": False}, ensure_ascii=False))
        return 3
    result = {
        "status": "PASS" if not errors else "FAIL",
        "annotation": str(ns.annotation),
        "samples": len(data.get("samples", [])) if isinstance(data, dict) and isinstance(data.get("samples"), list) else 0,
        "final_gate": ns.final_gate,
        "errors": errors,
        "semantic_authority": False,
        "note": "Structural validation cannot replace per-sample native/grid visual review.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
