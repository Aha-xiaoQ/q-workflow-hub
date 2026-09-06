#!/usr/bin/env python3
"""Small executable gate for native pixel-art PNGs.

Requires Pillow. It validates dimensions, palette size, alpha-corner behavior,
and optionally proves that a review preview is an exact nearest-neighbor
integer enlargement of the native image.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None


def emit(status: str, errors: list[str], **extra: object) -> int:
    report = {**extra, "status": status, "errors": errors}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else (1 if status == "FAIL" else 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--max-colors", type=int, default=256)
    ap.add_argument("--zoom-preview", type=Path)
    ap.add_argument("--require-transparent-corners", action="store_true")
    ns = ap.parse_args()

    if Image is None:
        return emit("ERROR", ["Pillow>=9.1.0 is required"], image=str(ns.image))
    argument_errors = []
    if ns.width is not None and ns.width <= 0:
        argument_errors.append("--width must be > 0")
    if ns.height is not None and ns.height <= 0:
        argument_errors.append("--height must be > 0")
    if ns.max_colors <= 0:
        argument_errors.append("--max-colors must be > 0")
    if argument_errors:
        return emit("ERROR", argument_errors, image=str(ns.image))
    if ns.image.suffix.lower() != ".png":
        return emit("FAIL", ["input must be a .png file"], image=str(ns.image))
    try:
        with Image.open(ns.image) as opened:
            if opened.format != "PNG":
                return emit(
                    "FAIL", [f"input content format is {opened.format}, expected PNG"],
                    image=str(ns.image),
                )
            im = opened.convert("RGBA")
    except (OSError, ValueError) as exc:
        return emit("ERROR", [f"cannot read input image: {exc}"], image=str(ns.image))
    errors: list[str] = []
    if ns.width is not None and im.width != ns.width:
        errors.append(f"width {im.width} != {ns.width}")
    if ns.height is not None and im.height != ns.height:
        errors.append(f"height {im.height} != {ns.height}")
    raw = im.tobytes()
    normalized_colors = set()
    for i in range(0, len(raw), 4):
        rgba = tuple(raw[i:i + 4])
        normalized_colors.add((0, 0, 0, 0) if rgba[3] == 0 else rgba)
    color_count = len(normalized_colors)
    if color_count > ns.max_colors:
        errors.append(f"palette {color_count} > {ns.max_colors}")
    corners = [im.getpixel((0, 0))[3], im.getpixel((im.width - 1, 0))[3],
               im.getpixel((0, im.height - 1))[3],
               im.getpixel((im.width - 1, im.height - 1))[3]]
    transparent_corners = all(alpha == 0 for alpha in corners)
    if ns.require_transparent_corners and not transparent_corners:
        errors.append(f"corner alpha values are {corners}, expected all 0")

    zoom_scale = None
    if ns.zoom_preview:
        if ns.zoom_preview.suffix.lower() != ".png":
            return emit("FAIL", ["zoom preview must be a .png file"], image=str(ns.image), zoom_preview=str(ns.zoom_preview))
        try:
            with Image.open(ns.zoom_preview) as opened:
                if opened.format != "PNG":
                    return emit(
                        "FAIL", [f"zoom preview content format is {opened.format}, expected PNG"],
                        image=str(ns.image), zoom_preview=str(ns.zoom_preview),
                    )
                zoom = opened.convert("RGBA")
        except (OSError, ValueError) as exc:
            return emit("ERROR", [f"cannot read zoom preview: {exc}"], image=str(ns.image), zoom_preview=str(ns.zoom_preview))
        if zoom.width % im.width or zoom.height % im.height:
            errors.append("zoom preview is not an integer multiple")
        else:
            sx, sy = zoom.width // im.width, zoom.height // im.height
            if sx != sy or sx < 2:
                errors.append(f"invalid zoom scale {sx}x{sy}")
            else:
                expected = im.resize(zoom.size, Image.Resampling.NEAREST)
                if expected.tobytes() != zoom.tobytes():
                    errors.append("zoom preview is not an exact nearest-neighbor copy")
                zoom_scale = sx

    return emit(
        "PASS" if not errors else "FAIL", errors, image=str(ns.image),
        size=[im.width, im.height], colors=color_count,
        zoom_scale=zoom_scale, transparent_corners=transparent_corners,
    )


if __name__ == "__main__":
    raise SystemExit(main())
