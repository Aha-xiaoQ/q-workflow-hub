#!/usr/bin/env python3
"""Probe rendered page images for ruled table structure evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def discover_images(target: Path) -> list[Path]:
    if target.is_file() and target.suffix.lower() in IMAGE_EXTS:
        return [target]
    if target.is_dir():
        return sorted(p for p in target.glob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTS)
    return []


def _component_count(binary: Any, min_area: int = 4) -> int:
    import cv2  # type: ignore

    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
    kept = 0
    for idx in range(1, count):
        if int(stats[idx, cv2.CC_STAT_AREA]) >= min_area:
            kept += 1
    return kept


def _box_intersections(intersections: Any, box: tuple[int, int, int, int]) -> int:
    import cv2  # type: ignore

    x, y, w, h = box
    region = intersections[y : y + h, x : x + w]
    return _component_count(region, min_area=2) if region.size else 0


def _merge_centers(values: list[int], gap: int) -> list[int]:
    if not values:
        return []
    values = sorted(values)
    groups: list[list[int]] = []
    for value in values:
        if not groups or value - groups[-1][-1] > gap:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [round(sum(group) / len(group)) for group in groups]


def probe_image(image_path: Path, max_dimension: int = 2500) -> dict[str, Any]:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return {"image": str(image_path.resolve()), "status": "failed", "error": "image could not be read"}

    original_height, original_width = image.shape[:2]
    scale = 1.0
    largest = max(original_width, original_height)
    if largest > max_dimension:
        scale = max_dimension / float(largest)
        image = cv2.resize(image, (int(original_width * scale), int(original_height * scale)), interpolation=cv2.INTER_AREA)
    height, width = image.shape[:2]

    blurred = cv2.GaussianBlur(image, (3, 3), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

    h_kernel_len = max(20, width // 35)
    v_kernel_len = max(20, height // 35)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_kernel_len, 1))
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_kernel_len))
    horizontal = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    vertical = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=1)
    intersections = cv2.bitwise_and(horizontal, vertical)
    grid = cv2.bitwise_or(horizontal, vertical)
    grid = cv2.dilate(grid, np.ones((3, 3), np.uint8), iterations=1)

    contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    min_w = width * 0.12
    min_h = height * 0.04
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w < min_w or h < min_h:
            continue
        area_ratio = (w * h) / float(width * height)
        if area_ratio < 0.003:
            continue
        box_intersections = _box_intersections(intersections, (x, y, w, h))
        if box_intersections < 4:
            continue
        candidates.append(
            {
                "bbox": [
                    round(x / scale),
                    round(y / scale),
                    round((x + w) / scale),
                    round((y + h) / scale),
                ],
                "scaled_bbox": [x, y, x + w, y + h],
                "intersection_count": box_intersections,
                "area_ratio": round(area_ratio, 4),
            }
        )

    candidates.sort(key=lambda item: (item["intersection_count"], item["area_ratio"]), reverse=True)
    horizontal_components = _component_count(horizontal, min_area=max(8, width // 20))
    vertical_components = _component_count(vertical, min_area=max(8, height // 20))
    intersection_count = _component_count(intersections, min_area=2)
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    min_line_length = max(40, int(min(width, height) * 0.08))
    max_line_gap = max(10, int(min(width, height) * 0.01))
    hough_lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=min_line_length, maxLineGap=max_line_gap)
    h_centers: list[int] = []
    v_centers: list[int] = []
    if hough_lines is not None:
        for line in hough_lines[:, 0, :]:
            x1, y1, x2, y2 = [int(value) for value in line]
            dx = x2 - x1
            dy = y2 - y1
            if not dx and not dy:
                continue
            angle = abs(math.degrees(math.atan2(dy, dx)))
            if angle < 8 or angle > 172:
                h_centers.append((y1 + y2) // 2)
            elif 82 < angle < 98:
                v_centers.append((x1 + x2) // 2)
    merge_gap = max(8, int(min(width, height) * 0.008))
    horizontal_grid_lines = _merge_centers(h_centers, merge_gap)
    vertical_grid_lines = _merge_centers(v_centers, merge_gap)
    estimated_rows = max(0, len(horizontal_grid_lines) - 1)
    estimated_columns = max(0, len(vertical_grid_lines) - 1)
    estimated_cells = estimated_rows * estimated_columns
    grid_strength = min(100, horizontal_components * 3 + vertical_components * 3 + min(40, intersection_count))
    return {
        "image": str(image_path.resolve()),
        "status": "ok",
        "original_size": {"width": original_width, "height": original_height},
        "working_size": {"width": width, "height": height},
        "scale": round(scale, 4),
        "horizontal_line_components": horizontal_components,
        "vertical_line_components": vertical_components,
        "intersection_count": intersection_count,
        "hough_horizontal_grid_lines": len(horizontal_grid_lines),
        "hough_vertical_grid_lines": len(vertical_grid_lines),
        "estimated_grid_rows": estimated_rows,
        "estimated_grid_columns": estimated_columns,
        "estimated_grid_cells": estimated_cells,
        "hough_horizontal_centers": horizontal_grid_lines[:50],
        "hough_vertical_centers": vertical_grid_lines[:50],
        "candidate_table_regions": len(candidates),
        "grid_strength": grid_strength,
        "candidates": candidates[:20],
    }


def probe_images(images: list[Path], out_dir: Path, max_dimension: int = 2500) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    available = importlib.util.find_spec("cv2") is not None and importlib.util.find_spec("numpy") is not None
    if not available:
        payload = {
            "created_utc": now,
            "engine": "opencv-line-probe",
            "status": "missing-dependency",
            "warning": "OpenCV and NumPy are required for local table-structure probing.",
            "pages_processed": 0,
            "candidate_table_regions": 0,
            "records": [],
        }
    else:
        records = [probe_image(image, max_dimension=max_dimension) for image in images]
        ok_records = [record for record in records if record.get("status") == "ok"]
        payload = {
            "created_utc": now,
            "engine": "opencv-line-probe",
            "status": "ok",
            "pages_processed": len(ok_records),
            "candidate_table_regions": sum(int(record.get("candidate_table_regions", 0)) for record in ok_records),
            "estimated_grid_cells": max((int(record.get("estimated_grid_cells", 0)) for record in ok_records), default=0),
            "max_grid_strength": max((int(record.get("grid_strength", 0)) for record in ok_records), default=0),
            "records": records,
            "warning": "This is a ruled-table evidence probe, not full table cell extraction.",
        }
    (out_dir / "table_structure_probe.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")

    lines = [
        "# Table Structure Probe Report",
        "",
        f"Created UTC: `{now}`",
        f"Engine: `{payload['engine']}`",
        f"Status: `{payload['status']}`",
        f"Pages processed: {payload.get('pages_processed', 0)}",
        f"Candidate table regions: {payload.get('candidate_table_regions', 0)}",
        f"Estimated grid cells: {payload.get('estimated_grid_cells', 0)}",
        f"Max grid strength: {payload.get('max_grid_strength', 0)}",
        "",
        "## Notes",
        "",
        f"- {payload.get('warning', 'No warning.')}",
    ]
    if payload.get("records"):
        lines.extend(["", "## Pages", ""])
        for index, record in enumerate(payload["records"], start=1):
            lines.append(
                f"- Page/image {index}: status={record.get('status')}, "
                f"regions={record.get('candidate_table_regions', 0)}, "
                f"grid={record.get('estimated_grid_rows', 0)}x{record.get('estimated_grid_columns', 0)}, "
                f"cells={record.get('estimated_grid_cells', 0)}, "
                f"h_lines={record.get('horizontal_line_components', 0)}, "
                f"v_lines={record.get('vertical_line_components', 0)}, "
                f"intersections={record.get('intersection_count', 0)}, "
                f"grid_strength={record.get('grid_strength', 0)}"
            )
    (out_dir / "table_structure_probe_report.md").write_text("\n".join(lines), encoding="utf-8-sig")
    return payload


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Probe page images for ruled table structure evidence.")
    parser.add_argument("target", help="Image file or folder of rendered page images")
    parser.add_argument("--out", required=True, help="Output folder, usually a reading pack tables/ directory")
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--max-dimension", type=int, default=2500)
    args = parser.parse_args(argv)

    images = discover_images(Path(args.target))[: args.max_pages]
    if not images:
        raise SystemExit(f"No images found: {args.target}")
    payload = probe_images(images, Path(args.out), max_dimension=args.max_dimension)
    print(f"Wrote table structure probe: {Path(args.out) / 'table_structure_probe_report.md'}")
    print(f"Candidate table regions: {payload.get('candidate_table_regions', 0)}")
    return 0 if payload.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
