#!/usr/bin/env python3
"""Validate that equivalent skill surfaces have identical file trees.

Use this for source/runtime/bootstrap drift checks. It intentionally compares
surfaces inside each declared group only; public and company variants should be
placed in separate groups when their names, metadata, or private style assets
are allowed to differ.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path


SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", "node_modules"}


@dataclass(frozen=True)
class Surface:
    label: str
    path: Path


def parse_surface(raw: str) -> Surface:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"surface must be label=path: {raw}")
    label, path = raw.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError(f"empty surface label: {raw}")
    return Surface(label=label, path=Path(path).resolve())


def parse_group(raw: str) -> tuple[str, list[Surface]]:
    if ":" not in raw:
        raise argparse.ArgumentTypeError(f"group must be name:label=path,label=path: {raw}")
    name, rest = raw.split(":", 1)
    surfaces = [parse_surface(item.strip()) for item in rest.split(",") if item.strip()]
    if len(surfaces) < 2:
        raise argparse.ArgumentTypeError(f"group needs at least two surfaces: {raw}")
    return name.strip(), surfaces


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_map(root: Path) -> dict[str, str]:
    if not root.is_dir():
        raise FileNotFoundError(f"surface not found: {root}")
    result: dict[str, str] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        result[rel.as_posix()] = sha256(path)
    return result


def compare_group(name: str, surfaces: list[Surface]) -> list[str]:
    failures: list[str] = []
    maps = [(surface, file_map(surface.path)) for surface in surfaces]
    baseline_surface, baseline_map = maps[0]
    print(f"## {name}")
    print(f"- Baseline: {baseline_surface.label} ({baseline_surface.path})")
    print(f"- Files: {len(baseline_map)}")
    for surface, current_map in maps[1:]:
        missing = sorted(set(baseline_map) - set(current_map))
        extra = sorted(set(current_map) - set(baseline_map))
        changed = sorted(rel for rel in set(baseline_map) & set(current_map) if baseline_map[rel] != current_map[rel])
        print(f"- Compare: {surface.label} ({surface.path})")
        print(f"  - missing: {len(missing)}")
        print(f"  - extra: {len(extra)}")
        print(f"  - changed: {len(changed)}")
        for label, rows in (("missing", missing), ("extra", extra), ("changed", changed)):
            for rel in rows[:20]:
                print(f"    {label}: {rel}")
            if len(rows) > 20:
                print(f"    ... {len(rows) - 20} more {label} file(s)")
        if missing or extra or changed:
            failures.append(f"{name}: {surface.label} differs from {baseline_surface.label}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", action="append", type=parse_group, required=True)
    args = parser.parse_args()
    failures: list[str] = []
    for name, surfaces in args.group:
        failures.extend(compare_group(name, surfaces))
    print("")
    if failures:
        print("Result: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Result: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
