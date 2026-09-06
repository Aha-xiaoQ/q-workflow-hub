#!/usr/bin/env python3
"""Build and validate the q-workflow runtime personal-state manifest."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Mapping


STATE_MIRROR_FILES = ("TODO.md", "TODO_DISPLAY.zh-CN.json", "ACTIVE_WORK.md")


class RuntimeManifestError(ValueError):
    """Raised when the mirror inputs cannot produce a trustworthy manifest."""


def _bytes(path: Path, overrides: Mapping[Path, bytes]) -> bytes:
    resolved = path.resolve()
    if resolved in overrides:
        return overrides[resolved]
    try:
        return path.read_bytes()
    except OSError as exc:
        raise RuntimeManifestError(f"Cannot read manifest input {path}: {exc}") from exc


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def parse_open_todo_ids(value: bytes) -> list[str]:
    try:
        text = value.decode("utf-8-sig")
    except UnicodeError as exc:
        raise RuntimeManifestError(f"TODO is not valid UTF-8: {exc}") from exc
    match = re.search(r"(?m)^## Open\s*$", text)
    if not match:
        raise RuntimeManifestError("TODO lacks an Open section")
    tail = text[match.end() :]
    next_section = re.search(r"(?m)^##\s+", tail)
    section = tail[: next_section.start()] if next_section else tail
    ids: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        row = re.match(r"^\s*-\s*\[\s\]\s*(.+?)\s*$", line)
        if not row:
            raise RuntimeManifestError(f"Unexpected TODO Open row: {stripped}")
        cells = [cell.strip() for cell in row.group(1).split("|", 2)]
        if len(cells) != 3 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0]) or not cells[1] or not cells[2]:
            raise RuntimeManifestError(f"Invalid TODO Open row: {stripped}")
        try:
            datetime.strptime(cells[0], "%Y-%m-%d")
        except ValueError as exc:
            raise RuntimeManifestError(f"Invalid TODO date: {stripped}") from exc
        ids.append(cells[1])
    if len(ids) != len(set(ids)):
        raise RuntimeManifestError("TODO Open section has duplicate ids")
    return ids


def git_revision(repository: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value or None


def build_runtime_manifest(
    state_root: Path,
    runtime_root: Path,
    *,
    overrides: Mapping[Path, bytes] | None = None,
    generated_at: str | None = None,
) -> dict:
    normalized = {path.resolve(): value for path, value in (overrides or {}).items()}
    rows = []
    for name in STATE_MIRROR_FILES:
        source = state_root / name
        runtime = runtime_root / name
        source_bytes = _bytes(source, normalized)
        runtime_bytes = _bytes(runtime, normalized)
        rows.append(
            {
                "name": name,
                "source": str(source),
                "runtime": str(runtime),
                "source_sha256": _sha(source_bytes),
                "runtime_sha256": _sha(runtime_bytes),
            }
        )
    todo_bytes = _bytes(state_root / "TODO.md", normalized)
    return {
        "version": 1,
        "policy": "read-only-rebuildable-mirror",
        "generated_at": generated_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "authority": str(state_root),
        "source_revision": git_revision(state_root.parent),
        "todo_open_ids": parse_open_todo_ids(todo_bytes),
        "files": rows,
    }


def runtime_manifest_bytes(payload: dict) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def validate_runtime_manifest(
    payload: dict,
    state_root: Path,
    runtime_root: Path,
    *,
    overrides: Mapping[Path, bytes] | None = None,
) -> list[str]:
    expected = build_runtime_manifest(
        state_root,
        runtime_root,
        overrides=overrides,
        generated_at=str(payload.get("generated_at", "")),
    )
    errors: list[str] = []
    for key in ("version", "policy", "authority", "source_revision", "todo_open_ids", "files"):
        if payload.get(key) != expected.get(key):
            errors.append(f"runtime manifest {key} does not match current mirror state")
    return errors
