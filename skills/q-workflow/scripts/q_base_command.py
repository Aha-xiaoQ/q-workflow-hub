#!/usr/bin/env python3
"""Resolve Xiao Q base commands against one q-profile authority.

The q-profile hub is authoritative. Runtime personal state is a read-only,
rebuildable mirror. Reads fail closed when profile authority or Markdown shape
is invalid; they never silently fall back to an unrelated legacy directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from active_work_pointer import ActiveWorkPointerError, require_active_work
from runtime_state_manifest import (
    STATE_MIRROR_FILES,
    RuntimeManifestError,
    build_runtime_manifest,
    runtime_manifest_bytes,
    validate_runtime_manifest,
)
from workflow_file_ops import (
    WorkflowFileLockError,
    acquire_lock,
    atomic_replace_bytes,
    release_lock,
)
from workflow_task_state import (
    TaskStateError,
    inspect_task_record,
    resolve_task_record,
    task_event_log_path,
    task_record_path,
)


EXIT_OK = 0
EXIT_INVALID = 2
EXIT_DRIFT = 3
RECENCY_TIMEOUT_SECONDS = 20
STATE_MIRROR_FILES = list(STATE_MIRROR_FILES)
SUPPORTED_SURFACE_SHAPES = {
    "slash-header", "open-count", "three-lines-per-item", "chinese-name-and-summary", "compact-localized-detail", "full-localized-description", "labeled-multiline-detail",
    "latest-turn", "context-pressure", "cache-health", "cumulative", "dashboard-receipt",
    "html-receipt", "purpose", "one-minute-trial", "commands", "project-entry", "capabilities",
    "permission-boundary", "blocked-recovery", "exact-first-line", "evidence", "status", "pointer",
    "recent", "next-action", "phase-boundary",
}


@dataclass(frozen=True)
class TodoItem:
    index: int
    date: str
    item_id: str
    description: str
    raw: str


class ContractError(RuntimeError):
    pass


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def read_bytes_stable(path: Path, attempts: int = 50) -> bytes:
    for attempt in range(attempts):
        try:
            return path.read_bytes()
        except PermissionError:
            if attempt + 1 == attempts:
                raise
            time.sleep(0.01)
    raise AssertionError("unreachable")


def read_text_stable(path: Path, encoding: str = "utf-8-sig", attempts: int = 50) -> str:
    for attempt in range(attempts):
        try:
            return path.read_text(encoding=encoding)
        except PermissionError:
            if attempt + 1 == attempts:
                raise
            time.sleep(0.01)
    raise AssertionError("unreachable")


def sha256(path: Path) -> str:
    return hashlib.sha256(read_bytes_stable(path)).hexdigest().upper()


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def profile_path() -> Path:
    return Path(os.environ.get("Q_PROFILE_PATH", str(codex_home() / "q-profile.json")))


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing JSON file: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"invalid JSON file: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError(f"JSON root must be an object: {path}")
    return data


def resolve_hub(profile: dict[str, Any], profile_file: Path) -> Path:
    direct = profile.get("hub")
    if isinstance(direct, str) and direct.strip():
        authoritative = Path(direct.strip())
        if not authoritative.is_dir():
            raise ContractError(f"configured authoritative hub does not exist: {authoritative}")
        return authoritative.resolve()

    candidates: list[str] = []
    repos = profile.get("repositories")
    if isinstance(repos, dict):
        personal = repos.get("q-personal-hub")
        if isinstance(personal, dict):
            for key in ("path", "local_path", "registry_path"):
                value = personal.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value.strip())
    unique = []
    for value in candidates:
        path = str(Path(value))
        if path.lower() not in {item.lower() for item in unique}:
            unique.append(path)
    if not unique:
        raise ContractError(f"q-profile does not define a personal hub: {profile_file}")
    existing = [Path(value) for value in unique if Path(value).is_dir()]
    if not existing:
        raise ContractError(f"configured fallback personal hub does not exist: {unique[0]}")
    canonical = existing[0].resolve()
    if len({str(path.resolve()).lower() for path in existing}) > 1:
        raise ContractError(f"q-profile contains ambiguous personal hubs: {unique}")
    return canonical


def resolve_personal_hub(profile: dict[str, Any], profile_file: Path, state_hub: Path) -> Path:
    """Resolve help/install content without changing the authoritative state hub."""
    candidates: list[str] = []
    direct = profile.get("personal_hub")
    if isinstance(direct, str) and direct.strip():
        candidates.append(direct.strip())
    repos = profile.get("repositories")
    if isinstance(repos, dict):
        personal = repos.get("q-personal-hub")
        if isinstance(personal, dict):
            for key in ("path", "local_path", "registry_path"):
                value = personal.get(key)
                if isinstance(value, str) and value.strip():
                    candidates.append(value.strip())
    unique: list[Path] = []
    for value in candidates:
        candidate = Path(value).resolve()
        if str(candidate).casefold() not in {str(item).casefold() for item in unique}:
            unique.append(candidate)
    existing = [path for path in unique if path.is_dir()]
    if len({str(path).casefold() for path in existing}) > 1:
        raise ContractError(f"q-profile contains ambiguous personal hubs: {unique}")
    if existing:
        return existing[0]
    if not candidates:
        return state_hub
    raise ContractError(f"configured personal hub does not exist: {unique[0]} ({profile_file})")


def authority() -> tuple[Path, Path, Path]:
    pfile = profile_path()
    profile = read_json(pfile)
    hub = resolve_hub(profile, pfile)
    state = hub / "personal-state"
    if not state.is_dir():
        raise ContractError(f"personal-state directory is missing: {state}")
    return pfile, hub, state


def contract_path() -> Path:
    return Path(__file__).resolve().parent.parent / "references" / "base-command-contract.json"


def load_contract() -> dict[str, Any]:
    data = read_json(contract_path())
    if data.get("version") != 3 or not isinstance(data.get("commands"), list):
        raise ContractError(f"unsupported command contract: {contract_path()}")
    surfaces = data.get("surfaces")
    if not isinstance(surfaces, dict):
        raise ContractError(f"command contract lacks executable surfaces: {contract_path()}")
    for command in data["commands"]:
        surface_id = command.get("output_contract")
        if surface_id not in surfaces:
            raise ContractError(f"command {command.get('id')} references missing surface {surface_id!r}")
    for surface_id, spec in surfaces.items():
        if not isinstance(spec, dict):
            raise ContractError(f"surface {surface_id} must be an object")
        unknown_shapes = set(spec.get("required_shape", [])) - SUPPORTED_SURFACE_SHAPES
        if unknown_shapes:
            raise ContractError(f"surface {surface_id} uses unsupported shape tokens: {sorted(unknown_shapes)}")
    return data


def parse_todo(path: Path) -> list[TodoItem]:
    try:
        text = read_text_stable(path)
    except FileNotFoundError as exc:
        raise ContractError(f"authoritative TODO is missing: {path}") from exc
    except OSError as exc:
        raise ContractError(f"authoritative TODO cannot be read: {path}: {exc}") from exc
    open_match = re.search(r"(?m)^## Open\s*$", text)
    if not open_match:
        raise ContractError(f"TODO lacks '## Open': {path}")
    tail = text[open_match.end():]
    next_section = re.search(r"(?m)^##\s+", tail)
    section = tail[: next_section.start()] if next_section else tail
    if re.search(r"(?m)^\s*-\s*\[[xX]\]", section):
        raise ContractError(f"checked item found inside Open section: {path}")
    items: list[TodoItem] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        match = re.match(r"^\s*-\s*\[\s\]\s*(.+?)\s*$", line)
        if not match:
            raise ContractError(f"unexpected non-empty line in Open section: {line.strip()}")
        raw = match.group(1).strip()
        cells = [cell.strip() for cell in raw.split("|", 2)]
        if (
            len(cells) != 3
            or not cells[0]
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[0])
            or not cells[1]
            or not cells[2]
        ):
            raise ContractError(f"invalid Open TODO row: {line.strip()}")
        try:
            datetime.strptime(cells[0], "%Y-%m-%d")
        except ValueError as exc:
            raise ContractError(f"invalid Open TODO date: {line.strip()}") from exc
        items.append(TodoItem(len(items) + 1, cells[0], cells[1], cells[2], raw))
    ids = [item.item_id for item in items]
    if len(ids) != len(set(ids)):
        raise ContractError(f"duplicate Open TODO ids: {path}")
    return items


def has_cjk_text(value: str) -> bool:
    return len(re.findall(r"[\u3400-\u9fff]", value)) >= 4


def todo_source_fingerprint(description: str) -> str:
    return hashlib.sha256(description.encode("utf-8")).hexdigest()


def todo_list_detail(detail: str, limit: int = 76) -> str:
    """Use one stable, concise sentence in the TODO list; selection shows full detail."""
    first_sentence = detail.split("。", 1)[0].strip()
    if not first_sentence:
        first_sentence = detail.strip()
    return first_sentence if len(first_sentence) <= limit else first_sentence[:limit].rstrip() + "…"


def todo_selection_detail(detail: str) -> str:
    """Render selected TODO detail as readable labeled clauses, one per line."""
    clauses = [part.strip() for part in re.split(r"(?<=[。！？])\s*", detail.strip()) if part.strip()]
    if len(clauses) == 1:
        clauses = [part.strip() for part in re.split(r"(?<=；)\s*", detail.strip()) if part.strip()]
    return "\n".join(clauses)


def load_todo_display(state_root: Path, items: list[TodoItem]) -> list[dict[str, str]]:
    path = state_root / "TODO_DISPLAY.zh-CN.json"
    if not path.is_file():
        raise ContractError(f"authoritative TODO display metadata is missing: {path}")
    data = read_json(path)
    if data.get("version") != 1 or data.get("language") != "zh-CN" or not isinstance(data.get("items"), dict):
        raise ContractError(f"invalid TODO display schema: {path}")
    result = []
    open_ids = {item.item_id for item in items}
    display_ids = set(data["items"])
    if open_ids != display_ids:
        raise ContractError(
            "TODO/display id mismatch: missing="
            + ",".join(sorted(open_ids - display_ids))
            + "; extra="
            + ",".join(sorted(display_ids - open_ids))
        )
    for item in items:
        display = data["items"].get(item.item_id)
        if (
            not isinstance(display, dict)
            or not all(isinstance(display.get(field), str) and display[field].strip() for field in ("name", "summary", "detail"))
            # Names preserve user text (including English and short Chinese).
            # Only the explanatory framework is required to be localized.
            or not all(has_cjk_text(display[field]) for field in ("summary", "detail"))
            or display.get("source_fingerprint") != todo_source_fingerprint(item.description)
        ):
            raise ContractError(f"TODO display metadata missing for Open id: {item.item_id}")
        result.append({
            "item_id": item.item_id,
            "name": display["name"].strip(),
            "summary": display["summary"].strip(),
            "detail": display["detail"].strip(),
        })
    return result


def route_command(value: str, context: str | None, contract: dict[str, Any]) -> dict[str, Any]:
    original = value
    normalized = value.strip()
    for command in contract["commands"]:
        mode = command["match"]
        aliases = command["aliases"]
        hit = False
        if mode == "exact":
            hit = normalized in aliases
        elif mode == "exact-case-insensitive":
            hit = normalized.casefold() in {str(alias).casefold() for alias in aliases}
        elif mode == "prefix":
            hit = any(normalized.startswith(alias) and len(normalized) > len(alias) for alias in aliases)
        elif mode == "contextual":
            hit = bool(re.fullmatch(r"[1-9]\d*", normalized)) and context == command.get("required_context")
        if hit:
            return {
                "status": "routed",
                "input": original,
                "normalized": normalized,
                "command_id": command["id"],
                "handler": command["handler"],
                "required_skill": command["required_skill"],
                "state_source": command["state_source"],
                "output_contract": command["output_contract"],
            }
    if re.fullmatch(r"[1-9]\d*", normalized):
        raise ContractError("numeric selection requires current context 'todo-list'")
    folded = normalized.casefold()
    for route in contract.get("required_skill_routes", []):
        intents = route.get("intents", [])
        if any(str(intent).casefold() in folded for intent in intents):
            return {
                "status": "routed",
                "input": original,
                "normalized": normalized,
                "command_id": route["id"],
                "handler": "required_skill",
                "required_skill": route["required_skill"],
                "state_source": "none",
                "output_contract": "skill-route-proof",
            }
    raise ContractError(
        f"unregistered base command: {original!r}. Use help/帮助 to list supported "
        f"commands or inspect {contract_path()}."
    )


def runtime_state_root() -> Path:
    return codex_home() / "q-personal-state"


def mirror_status(source: Path, runtime: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "source": str(source),
        "runtime": str(runtime),
        "source_exists": source.is_file(),
        "runtime_exists": runtime.is_file(),
        "match": False,
    }
    if source.is_file():
        result["source_sha256"] = sha256(source)
    if runtime.is_file():
        result["runtime_sha256"] = sha256(runtime)
    result["match"] = (
        result["source_exists"]
        and result["runtime_exists"]
        and result.get("source_sha256") == result.get("runtime_sha256")
    )
    return result


def managed_task_binding_status(state_root: Path, pointer: dict[str, Any]) -> dict[str, Any]:
    """Validate that a managed focus pointer resolves to its task record and event."""
    required = pointer.get("schema") == "q-workflow-focus-v2" or bool(pointer.get("task_record_path"))
    result: dict[str, Any] = {
        "required": required,
        "status": "legacy-unmanaged" if not required else "blocked",
        "task_id": pointer.get("task_id"),
        "errors": [],
    }
    if not required:
        return result
    expected_latch = (
        "phase-b-required"
        if pointer.get("work_state") in {"active", "validating", "blocked"}
        else "not-required"
    )
    if pointer.get("visibility_latch") != expected_latch:
        result["errors"].append(
            f"managed RECOVERY_POINTER visibility_latch={pointer.get('visibility_latch')!r}; expected {expected_latch!r}"
        )
    task_id = pointer.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        result["errors"].append("managed RECOVERY_POINTER is missing task_id")
        return result
    hub = state_root.parent
    try:
        if pointer.get("task_record_path"):
            record_path = resolve_task_record(hub, record_path=Path(str(pointer["task_record_path"])))
        else:
            record_path = task_record_path(hub, task_id)
        inspection = inspect_task_record(record_path, task_event_log_path(hub), pointer=pointer)
    except TaskStateError as exc:
        result["record_path"] = str(state_root / "tasks" / f"{task_id}.json")
        result["errors"].append(str(exc))
        return result
    result["record_path"] = str(record_path)
    result["errors"].extend(list(inspection.get("errors", [])))
    result["status"] = "pass" if inspection.get("status") == "pass" and not result["errors"] else "blocked"
    return result


def atomic_replace(temp_path: Path, destination: Path, attempts: int = 50) -> None:
    """Tolerate Windows sharing violations around an otherwise atomic swap."""
    for attempt in range(attempts):
        try:
            os.replace(temp_path, destination)
            return
        except PermissionError:
            if attempt + 1 == attempts:
                raise
            time.sleep(0.01)

def sync_runtime_state(
    state_root: Path,
    allow_state_drop: bool = False,
    *,
    _test_fail_after_write: int = 0,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    runtime_root = runtime_root if runtime_root is not None else runtime_state_root()
    names = STATE_MIRROR_FILES
    for name in names:
        source = state_root / name
        if not source.is_file():
            raise ContractError(f"cannot mirror missing authoritative state: {source}")
    source_items = parse_todo(state_root / "TODO.md")
    load_todo_display(state_root, source_items)
    runtime_todo = runtime_root / "TODO.md"
    if runtime_todo.is_file():
        runtime_items = parse_todo(runtime_todo)
        source_ids = {item.item_id for item in source_items}
        runtime_only = [item.item_id for item in runtime_items if item.item_id not in source_ids]
        if runtime_only and not allow_state_drop:
            raise ContractError(
                "runtime TODO contains Open ids absent from authority; refusing possible data loss: "
                + ", ".join(runtime_only)
                + ". Reconcile source/Git first or rerun with --allow-state-drop after explicit review."
            )
    candidates = {
        runtime_root / name: (state_root / name).read_bytes()
        for name in names
    }
    manifest_path = runtime_root / "runtime-manifest.json"
    try:
        manifest_payload = build_runtime_manifest(
            state_root,
            runtime_root,
            overrides=candidates,
        )
    except RuntimeManifestError as exc:
        raise ContractError(str(exc)) from exc
    candidates[manifest_path] = runtime_manifest_bytes(manifest_payload)

    lock_path = state_root / ".q-workflow-manager.lock"
    try:
        lock_descriptor = acquire_lock(lock_path)
    except WorkflowFileLockError as exc:
        raise ContractError(str(exc)) from exc
    originals: dict[Path, bytes | None] = {}
    written: list[Path] = []
    try:
        for target, candidate in candidates.items():
            originals[target] = target.read_bytes() if target.is_file() else None
            atomic_replace_bytes(target, candidate)
            written.append(target)
            if _test_fail_after_write > 0 and len(written) == _test_fail_after_write:
                raise ContractError(f"Injected runtime-state transaction failure after write {len(written)}")
        for name in names:
            if (runtime_root / name).read_bytes() != (state_root / name).read_bytes():
                raise ContractError(f"runtime mirror readback failed for {name}")
        manifest_errors = validate_runtime_manifest(
            read_json(manifest_path),
            state_root,
            runtime_root,
        )
        if manifest_errors:
            raise ContractError("runtime manifest readback failed: " + " | ".join(manifest_errors))
        return {"synced": names, "manifest": str(manifest_path)}
    except Exception:
        for target in reversed(written):
            original = originals.get(target)
            if original is None:
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass
            else:
                atomic_replace_bytes(target, original)
        raise
    finally:
        release_lock(lock_path, lock_descriptor)


def preflight_runtime_state(state_root: Path, allow_state_drop: bool = False) -> dict[str, Any]:
    for name in STATE_MIRROR_FILES:
        source = state_root / name
        if not source.is_file():
            raise ContractError(f"authoritative state is missing: {source}")
    source_items = parse_todo(state_root / "TODO.md")
    load_todo_display(state_root, source_items)
    runtime_todo = runtime_state_root() / "TODO.md"
    runtime_items = parse_todo(runtime_todo) if runtime_todo.is_file() else []
    source_ids = {item.item_id for item in source_items}
    runtime_only = [item.item_id for item in runtime_items if item.item_id not in source_ids]
    if runtime_only and not allow_state_drop:
        raise ContractError(
            "runtime TODO contains Open ids absent from authority; refusing possible data loss: "
            + ", ".join(runtime_only)
        )
    return {
        "status": "pass",
        "authority": str(state_root),
        "source_open_ids": [item.item_id for item in source_items],
        "runtime_only_ids": runtime_only,
        "allow_state_drop": allow_state_drop,
    }


def todo_context_token(todo_path: Path, display_path: Path) -> str:
    digest = hashlib.sha256()
    for path in (todo_path, display_path):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()[:16]


def slugify_todo_id(content: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", content.casefold()).strip("-")[:48]
    return slug or datetime.now().strftime("todo-%Y%m%d-%H%M%S")


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as handle:
        handle.write(text)
        temp_path = Path(handle.name)
    atomic_replace(temp_path, path)


@contextmanager
def shared_state_lock(state_root: Path):
    """Serialize every authoritative state writer on the shared workflow lock."""
    lock_path = state_root / ".q-workflow-manager.lock"
    try:
        descriptor = acquire_lock(lock_path)
    except WorkflowFileLockError as exc:
        raise ContractError(str(exc)) from exc
    try:
        yield
    finally:
        release_lock(lock_path, descriptor)


def localized_todo_description(content: str) -> str:
    return (
        f"{content}。下一步：选择该事项后补充执行范围、证据和完成条件。"
        "完成条件：形成可验证结果或明确关闭记录。"
    )


def todo_display_from_content(content: str, description: str | None = None) -> dict[str, str]:
    compact = " ".join(content.split())
    description = description or localized_todo_description(content)
    name = compact[:32] + ("…" if len(compact) > 32 else "")
    summary = (
        f"{compact}；下一步：选择该事项后补充执行范围、证据和完成条件。"
        "完成条件：形成可验证结果或明确关闭记录。"
    )
    detail = (
        f"事项：{compact}。下一步：选择该事项后补充执行范围、证据和完成条件。"
        "完成条件：形成可验证结果或明确关闭记录。"
    )
    return {
        "name": name,
        "summary": summary,
        "detail": detail,
        "source_fingerprint": todo_source_fingerprint(description),
    }


def append_todo(path: Path, content: str, display_path: Path) -> TodoItem:
    with shared_state_lock(path.parent):
        items = parse_todo(path)
        display_data = read_json(display_path)
        load_todo_display(path.parent, items)
        if any(item.description.casefold().startswith(content.casefold()) for item in items):
            raise ContractError("an equivalent Open TODO already exists")
        base_id = slugify_todo_id(content)
        item_id = base_id
        suffix = 2
        ids = {item.item_id for item in items}
        while item_id in ids:
            item_id = f"{base_id}-{suffix}"
            suffix += 1
        date = datetime.now().astimezone().date().isoformat()
        description = localized_todo_description(content)
        row = f"- [ ] {date} | {item_id} | {description}"
        original_todo = read_text_stable(path)
        original_display = read_text_stable(display_path)
        text = original_todo
        open_match = re.search(r"(?m)^## Open\s*$", text)
        if not open_match:
            raise ContractError(f"TODO lacks '## Open': {path}")
        insert_at = open_match.end()
        updated = text[:insert_at] + "\n" + row + text[insert_at:]
        updated = re.sub(r"(?m)^Updated:\s*.*$", f"Updated: {date}", updated, count=1)
        display_data["items"][item_id] = todo_display_from_content(content, description)
        updated_display = json.dumps(display_data, ensure_ascii=False, indent=2) + "\n"
        try:
            atomic_write_text(display_path, updated_display)
            atomic_write_text(path, updated)
            committed_items = parse_todo(path)
            load_todo_display(path.parent, committed_items)
            created = next((item for item in committed_items if item.item_id == item_id), None)
            if created is None:
                raise ContractError("TODO commit verification failed")
            return created
        except Exception:
            atomic_write_text(path, original_todo)
            atomic_write_text(display_path, original_display)
            raise


def parse_active_work(path: Path) -> dict[str, Any]:
    try:
        state = require_active_work(path)
    except ActiveWorkPointerError as exc:
        raise ContractError(str(exc)) from exc
    return {
        "authority": state["authority"],
        "current_focus": state["current_focus"],
        "recovery_pointer": state["recovery_pointer"],
    }


def surface(chat_text: str, artifacts: list[dict[str, Any]] | None = None, actions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "chat_text": chat_text,
        "artifacts": artifacts or [],
        "actions": actions or [],
    }


def format_number(value: int | float) -> str:
    return f"{int(value):,}"


def open_artifact(path: Path, enabled: bool) -> dict[str, Any]:
    result = {"type": "open", "target": str(path), "requested": enabled, "status": "not-requested"}
    if not enabled:
        return result
    if not path.is_file():
        result["status"] = "missing"
        return result
    receipt_path = os.environ.get("Q_COMMAND_OPEN_RECEIPT")
    if receipt_path:
        receipt = Path(receipt_path)
        previous = receipt.read_text(encoding="utf-8-sig") if receipt.is_file() else ""
        atomic_write_text(receipt, previous + str(path) + "\n")
        result["status"] = "opened-test-receipt"
        return result
    try:
        if os.name == "nt":
            os.startfile(str(path))
        else:
            import webbrowser
            if not webbrowser.open(path.resolve().as_uri()):
                raise OSError("default browser rejected the request")
        result["status"] = "opened"
    except OSError as exc:
        result["status"] = "open-failed"
        result["error"] = str(exc)
    return result


def render_help_chat(guide: Path, action: dict[str, Any], guide_kind: str) -> str:
    opened = action.get("status") in {"opened", "opened-test-receipt"}
    state = "已打开" if opened else ("已找到，未请求打开" if action.get("status") == "not-requested" else "打开失败")
    detail_surface = "该 HTML 帮助页" if guide_kind == "html" else "该 Markdown 兜底帮助"
    return "\n".join([
        "小Q工作流 / q-assistant-profile / 帮助",
        f"帮助页面：{state} {guide}",
        "用途：把项目状态、待办、验证证据、版本边界和专家协作沉淀为可恢复的工作流。",
        "一分钟试跑：输入“小Q”恢复主线 → 用“TODO”查看完整待办 → 给出具体任务后执行、验证并记录。",
        "常用指令：小Q/继续小Q、状态、TODO、TODO：<内容>、TOKEN、checkpoint、workflow-health/体检。",
        "项目入口：可以登记现有项目、创建可恢复项目，或指定项目继续；恢复时以聊天尾部与 ACTIVE_WORK 双重核对。",
        "能力范围：项目管理、代码与 Git 交付、文档/PPT/HTML/图表制作、研究发现、专家协同与质量验收。",
        "权限边界：默认不推送、不发布、不删除、不覆盖未授权内容；高影响操作必须得到明确批准。",
        f"卡住时：保留现状并说明阻塞、证据与可选恢复路径；完整说明和示例见{detail_surface}。",
    ])


def execute_help(route: dict[str, Any], contract: dict[str, Any], hub: Path, open_ui: bool = False) -> dict[str, Any]:
    guide = hub / "FIRST_RUN_GUIDE.zh-CN.html"
    fallback = hub / "personal-state" / "ASSISTANT_HELP.md"
    target = guide if guide.is_file() else fallback
    if not target.is_file():
        raise ContractError(f"help surfaces are missing: {guide}; {fallback}")
    action = open_artifact(target, open_ui)
    commands = [
        {"id": command["id"], "aliases": command["aliases"], "required_skill": command["required_skill"]}
        for command in contract["commands"]
    ]
    guide_kind = "html" if target.suffix.casefold() == ".html" else "markdown-fallback"
    chat_text = render_help_chat(target, action, guide_kind)
    return {
        **route,
        "commands": commands,
        "guide": str(target),
        "guide_kind": guide_kind,
        "open_status": action["status"],
        "surface": surface(chat_text, [{"type": "help", "path": str(target)}], [action]),
        "next_action": "向用户原样展示 surface.chat_text；不得附加 TODO 编号菜单。",
    }


def canonical_recency_anchors(text: str) -> set[str]:
    folded = text.casefold()
    aliases = {
        "todo": ["todo", "待办"],
        "help": ["help", "帮助"],
        "token": ["token"],
        "xiaoq": ["小q", "小ｑ", "xiao q", "xiaoq"],
        "workflow": ["workflow", "工作流"],
        "expert": ["expert", "专家"],
        "format": ["format", "格式"],
    }
    return {key for key, values in aliases.items() if any(value in folded for value in values)}


def is_internal_control_message(text: str) -> bool:
    stripped = text.strip().casefold()
    control_tags = (
        "<recommended_plugins>",
        "<environment_context>",
        "<permissions instructions>",
        "<app-context>",
        "<skills_instructions>",
        "<apps_instructions>",
        "<plugins_instructions>",
        "<collaboration_mode>",
    )
    return any(stripped.startswith(tag) for tag in control_tags)


def select_latest_concrete_user_message(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    ignored = {"todo", "help", "帮助", "token", "小q", "小ｑ", "xiaoq", "xiao q", "继续小q", "resume", "continue", "status", "状态", "checkpoint"}
    concrete = [
        item for item in messages
        if isinstance(item, dict)
        and isinstance(item.get("text"), str)
        and item["text"].strip().casefold() not in ignored
        and not re.fullmatch(r"[1-9]\d*", item["text"].strip())
        and not is_internal_control_message(item["text"])
    ]
    return concrete[-1] if concrete else None


def recent_chat_evidence(pointer: dict[str, str]) -> dict[str, Any]:
    helper = Path(__file__).resolve().parent / "session_pointer.py"
    if not helper.is_file():
        return {"checked": False, "confidence": "partial", "reason": "缺少 session_pointer.py"}
    try:
        completed = subprocess.run(
            [sys.executable, str(helper), "--codex-home", str(codex_home()), "--best-user-session", "--messages", "10", "--users-only", "--exclude-internal-control", "--exclude-base-commands", "--max-chars", "800", "--format", "json"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=RECENCY_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"checked": False, "confidence": "partial", "reason": f"聊天尾部读取超过 {RECENCY_TIMEOUT_SECONDS} 秒，已降级为部分恢复"}
    except OSError as exc:
        return {"checked": False, "confidence": "partial", "reason": f"聊天尾部读取失败：{exc}"}
    if completed.returncode != 0:
        return {"checked": False, "confidence": "partial", "reason": completed.stderr.strip() or completed.stdout.strip() or "聊天尾部不可用"}
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {"checked": False, "confidence": "partial", "reason": f"聊天指针 JSON 无效：{exc}"}
    messages = [item for item in data.get("messages", []) if isinstance(item, dict) and isinstance(item.get("text"), str)]
    latest = select_latest_concrete_user_message(messages)
    if latest is None:
        return {"checked": True, "confidence": "partial", "session_id": data.get("session_id"), "reason": "没有找到可核对的具体用户消息"}
    pointer_text = " ".join([
        pointer.get("latest_chat_override", ""),
        pointer.get("latest_verified_note", ""),
        pointer.get("current_focus", ""),
        pointer.get("task_id", ""),
    ])
    latest_anchors = canonical_recency_anchors(latest["text"])
    pointer_anchors = canonical_recency_anchors(pointer_text)
    overlap = sorted(latest_anchors & pointer_anchors)
    confidence = "confirmed" if len(overlap) >= 2 else "partial"
    return {
        "checked": True,
        "confidence": confidence,
        "session_id": data.get("session_id"),
        "session_updated_at": data.get("updated_at"),
        "latest_timestamp": latest.get("timestamp"),
        "latest_text": latest["text"],
        "anchor_overlap": overlap,
        "reason": "最近指令与持久指针的命令/主题锚点一致" if confidence == "confirmed" else "已读取最近聊天，但与持久指针的匹配证据不足",
    }


def execute_status(route: dict[str, Any], state_root: Path, quick_resume: bool = False, check_recency: bool = True) -> dict[str, Any]:
    payload = {**route, **parse_active_work(state_root / "ACTIVE_WORK.md")}
    pointer = payload.get("recovery_pointer", {})
    binding = managed_task_binding_status(state_root, pointer if isinstance(pointer, dict) else {})
    payload["task_binding"] = binding
    if quick_resume:
        payload["phase"] = "A"
        recency = recent_chat_evidence(pointer) if check_recency else {"checked": False, "confidence": "partial", "reason": "recency disabled by isolated fixture"}
        payload["recency_checked"] = recency["checked"]
        binding_blocked = binding["required"] and binding["status"] != "pass"
        payload["pointer_confidence"] = "blocked" if binding_blocked else recency["confidence"]
        payload["recency_evidence"] = recency
        payload["recency_requirement"] = "A confident resume target requires a readable recent concrete user message that matches durable pointer anchors."
        payload["execution_boundary"] = "Brief and lock the current state; do not enter project execution without a concrete current command."
        status = "/".join([
            pointer.get("work_state", "unknown"),
            pointer.get("integrity_state", "unknown"),
            pointer.get("release_state", "unknown"),
        ])
        confidence_zh = "阻断" if binding_blocked else ("已确认" if recency["confidence"] == "confirmed" else "部分")
        record_state = "stale" if binding_blocked else ("confirmed" if recency["confidence"] == "confirmed" else "partial")
        latest_text = recency.get("latest_text", "未取得可核对的具体用户消息")
        if len(latest_text) > 220:
            latest_text = latest_text[:217] + "..."
        evidence = (
            f"已读取聊天尾部 session {recency.get('session_id')} 与 ACTIVE_WORK/RECOVERY_POINTER；record_state: {record_state}。"
            if recency["checked"]
            else f"已读取 ACTIVE_WORK/RECOVERY_POINTER；聊天尾部不可用（{recency.get('reason')}），record_state: partial。"
        )
        if binding_blocked:
            binding_error = "; ".join(binding.get("errors", [])[:2]) or "managed task binding failed"
            evidence += f" 任务实体/事件绑定失败（{binding_error}）；record_state: stale。"
        next_action = (
            "先修复 RECOVERY_POINTER 对应的任务 JSON、authority event 与运行时镜像，再恢复项目执行。"
            if binding_blocked
            else pointer.get("next_action", "先核对最新聊天，再确认唯一恢复目标。")
        )
        chat_text = "\n".join([
            f"【小Q工作流 | 快速恢复 】{confidence_zh}",
            f"证据：{evidence}",
            f"状态：{status}",
            f"目标：{pointer.get('current_focus_override', payload.get('current_focus', 'unknown'))}",
            f"指针：{pointer.get('task_id', 'unknown')} / {pointer.get('active_project', payload.get('current_focus', 'unknown'))} / {pointer.get('path', payload['authority'])}",
            f"最近：{latest_text}；与持久指针关系：{recency.get('reason')}。",
            f"下一步：{next_action}",
            "边界：Phase A；没有当前执行指令时不进入 Phase B。",
        ])
        payload["surface"] = surface(chat_text)
    return payload


def execute_checkpoint(route: dict[str, Any], state_root: Path) -> dict[str, Any]:
    """Do not misrepresent a read-only command as a durable checkpoint."""
    return {
        **route,
        **parse_active_work(state_root / "ACTIVE_WORK.md"),
        "checkpoint_status": "action-required",
        "write_status": "not-written",
        "next_action": "Provide a concrete work-item/state update through q-workflow; checkpoint without explicit state must not claim a durable write.",
    }


def execute_todo(route: dict[str, Any], state_root: Path, context: str | None, context_token: str | None, commit: bool) -> dict[str, Any]:
    source = state_root / "TODO.md"
    items = parse_todo(source)
    display_items = load_todo_display(state_root, items)
    runtime = runtime_state_root() / "TODO.md"
    result = dict(route)
    result.update({
        "authority": str(source),
        "open_count": len(items),
        "items": [asdict(item) for item in items],
        "display_items": display_items,
        "mirror": mirror_status(source, runtime),
        "context_token": todo_context_token(source, state_root / "TODO_DISPLAY.zh-CN.json"),
    })
    if route["handler"] == "todo_list":
        lines = ["小Q工作流 / q-assistant-profile / TODO", f"当前共 {len(items)} 项待办："]
        display_by_id = {item["item_id"]: item for item in display_items}
        for item in items:
            display = display_by_id[item.item_id]
            lines.append(f"{item.index}. {item.item_id} / {display['name']}")
            lines.append(f"   摘要：{display['summary']}")
            lines.append(f"   详情：{todo_list_detail(display['detail'])}")
        result["surface"] = surface("\n".join(lines))
    if route["handler"] == "todo_select":
        expected_token = todo_context_token(source, state_root / "TODO_DISPLAY.zh-CN.json")
        if not context_token or context_token != expected_token:
            raise ContractError("TODO selection context token is missing or stale; list TODO again")
        index = int(route["normalized"])
        if index > len(items):
            raise ContractError(f"TODO selection {index} exceeds Open count {len(items)}")
        selected = items[index - 1]
        selected_display = next(item for item in display_items if item["item_id"] == selected.item_id)
        result["selected"] = asdict(selected)
        result["selected_display"] = selected_display
        formatted_detail = todo_selection_detail(selected_display["detail"])
        result["selected_detail"] = formatted_detail
        result["surface"] = surface("\n".join([
            "小Q工作流 / q-assistant-profile / TODO 选择",
            f"已定位：{selected.item_id} / {selected_display['name']}",
            "详情：",
            *[f"   {line}" for line in formatted_detail.splitlines()],
        ]))
    elif route["handler"] == "todo_add":
        prefix = re.match(r"^TODO[:：]|^todo[:：]", route["normalized"])
        content = route["normalized"][prefix.end():].strip() if prefix else ""
        if not content:
            raise ContractError("TODO add content is empty")
        result["content"] = content
        if commit:
            created = append_todo(source, content, state_root / "TODO_DISPLAY.zh-CN.json")
            result["write_status"] = "committed"
            result["created"] = asdict(created)
            result["open_count"] = len(parse_todo(source))
            result["items"] = [asdict(item) for item in parse_todo(source)]
            result["context_token"] = todo_context_token(source, state_root / "TODO_DISPLAY.zh-CN.json")
            result["mirror"] = mirror_status(source, runtime)
            result["next_action"] = "Rebuild the runtime mirror after the authoritative commit."
        else:
            result["write_status"] = "preview-only"
            result["next_action"] = "Re-run with --commit to append atomically to the authoritative hub."
    return result


def token_pressure_label(pressure: float) -> str:
    if pressure >= 80:
        return "高"
    if pressure >= 60:
        return "注意"
    return "正常"


def token_cache_label(data: dict[str, Any]) -> str:
    ratio = float(data["latest_turn"]["metrics"].get("cached_input_ratio", 0.0) or 0.0)
    trend = data.get("efficiency_trend") if isinstance(data.get("efficiency_trend"), dict) else {}
    spread = float(trend.get("cache_ratio_spread", 0.0) or 0.0)
    if ratio < 50.0:
        return "偏低"
    if spread >= 35.0:
        return "波动较大"
    if ratio >= 80.0:
        return "健康"
    return "一般"


def render_token_chat(data: dict[str, Any], dashboard: Path, action: dict[str, Any]) -> str:
    latest = data["latest_turn"]
    metrics = latest["metrics"]
    pressure = float(latest["context_pressure"])
    health = data.get("health", [])
    warn_count = sum(1 for item in health if item.get("level") == "warn")
    danger_count = sum(1 for item in health if item.get("level") == "danger")
    if danger_count:
        health_text = f"临界（{danger_count} 项高风险，{warn_count} 项提醒）"
    elif warn_count:
        health_text = f"关注（{warn_count} 项提醒）"
    else:
        health_text = "稳定"
    opened = action.get("status") in {"opened", "opened-test-receipt"}
    open_text = "已打开" if opened else ("已生成，未请求打开" if action.get("status") == "not-requested" else "打开失败")
    return "\n".join([
        "小Q工作流 / q-workflow / TOKEN",
        f"本轮：{format_number(latest['tokens']['total_tokens'])} tokens；上下文：{format_number(latest['tokens']['total_tokens'])}/{format_number(latest['context_window'])}（{pressure:.1f}%，{token_pressure_label(pressure)}）。",
        f"缓存：{metrics['cached_input_ratio']:.1f}%（{token_cache_label(data)}）；未缓存输入：{format_number(metrics['uncached_input_tokens'])}。",
        f"累计：当前会话 {format_number(data['current']['tokens']['total_tokens'])}；当前项目 {format_number(data['project']['tokens']['total_tokens'])}；全部会话 {format_number(data['total']['tokens']['total_tokens'])}。",
        f"健康：{health_text}；仪表盘：{open_text} {dashboard}",
    ])


def execute_token(route: dict[str, Any], open_ui: bool = False) -> dict[str, Any]:
    token_script = Path(__file__).resolve().parent / "token_usage.py"
    completed = subprocess.run(
        [sys.executable, str(token_script), "--codex-home", str(codex_home()), "--format", "json"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=45,
        check=False,
    )
    if completed.returncode != 0:
        raise ContractError(f"token helper failed: {completed.stderr.strip() or completed.stdout.strip()}")
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ContractError(f"token helper returned invalid JSON: {exc}") from exc
    dashboard = codex_home() / "reports" / "token_dashboard.html"
    spec = importlib.util.spec_from_file_location("q_token_usage_runtime", token_script)
    if spec is None or spec.loader is None:
        raise ContractError(f"cannot load token dashboard renderer: {token_script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.write_html_dashboard(data, dashboard)
    action = open_artifact(dashboard, open_ui)
    chat_text = render_token_chat(data, dashboard, action)
    return {
        **route,
        "script": str(token_script),
        "dashboard": str(dashboard),
        "open_status": action["status"],
        "summary": {
            "latest_turn_tokens": data["latest_turn"]["tokens"]["total_tokens"],
            "context_pressure": data["latest_turn"]["context_pressure"],
            "cached_input_ratio": data["latest_turn"]["metrics"]["cached_input_ratio"],
            "health": data.get("health", []),
        },
        "surface": surface(chat_text, [{"type": "token-dashboard", "path": str(dashboard)}], [action]),
        "next_action": "向用户原样展示 surface.chat_text；仪表盘与简表不可二选一。",
    }


def nested_value(payload: dict[str, Any], dotted: str) -> Any:
    value: Any = payload
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ContractError(f"output surface lacks required field: {dotted}")
        value = value[part]
    return value


def validate_output_surface(route: dict[str, Any], payload: dict[str, Any], contract: dict[str, Any], open_ui: bool) -> None:
    surface_id = route["output_contract"]
    spec = contract["surfaces"].get(surface_id)
    if spec is None:
        if route.get("handler") == "required_skill":
            return
        raise ContractError(f"missing executable output surface: {surface_id}")
    for field in spec.get("required_fields", []):
        nested_value(payload, field)
    chat_text = payload.get("surface", {}).get("chat_text")
    if "surface.chat_text" in spec.get("required_fields", []) and (not isinstance(chat_text, str) or not chat_text.strip()):
        raise ContractError(f"empty user-visible surface for {route['command_id']}")
    if isinstance(chat_text, str):
        for phrase in spec.get("forbidden_phrases", []):
            if phrase in chat_text:
                raise ContractError(f"forbidden phrase {phrase!r} in {route['command_id']} surface")
        max_lines = spec.get("max_chat_lines")
        if isinstance(max_lines, int) and len(chat_text.splitlines()) > max_lines:
            raise ContractError(f"{route['command_id']} surface exceeds {max_lines} lines")
    if route["command_id"] == "todo-list":
        expected = payload.get("items", [])
        if len(expected) != payload.get("open_count"):
            raise ContractError("TODO surface count differs from authoritative items")
        if not chat_text.startswith("小Q工作流 / q-assistant-profile / TODO\n"):
            raise ContractError("TODO surface header drifted")
        if "原始记录：" in chat_text:
            raise ContractError("TODO surface must not render raw source descriptions")
        if not all(
            item["name"] in chat_text and item["summary"] in chat_text and todo_list_detail(item["detail"]) in chat_text
            for item in payload.get("display_items", [])
        ):
            raise ContractError("TODO surface omitted deterministic Chinese compact detail")
    elif route["command_id"] == "todo-select":
        selected_display = payload.get("selected_display")
        formatted_detail = todo_selection_detail(selected_display.get("detail", "")) if isinstance(selected_display, dict) else ""
        if (
            not isinstance(selected_display, dict)
            or not chat_text.startswith("小Q工作流 / q-assistant-profile / TODO 选择\n")
            or selected_display.get("name") not in chat_text
            or not formatted_detail
            or not all(line in chat_text for line in formatted_detail.splitlines())
            or "\n详情：\n" not in chat_text
            or "原始记录：" in chat_text
        ):
            raise ContractError("TODO selection must expose the localized detail surface")
    elif route["command_id"] == "help":
        if not chat_text.startswith("小Q工作流 / q-assistant-profile / 帮助\n") or "一分钟试跑" not in chat_text:
            raise ContractError("Help surface is incomplete")
    elif route["command_id"] == "token-dashboard":
        if not chat_text.startswith("小Q工作流 / q-workflow / TOKEN\n") or len(chat_text.splitlines()) != 5:
            raise ContractError("TOKEN surface must be the fixed five-line summary")
        if not Path(payload["dashboard"]).is_file():
            raise ContractError("TOKEN surface references a missing dashboard")
    elif route["command_id"] == "quick-resume":
        required = ["证据：", "状态：", "目标：", "指针：", "最近：", "下一步：", "边界：Phase A"]
        if not re.match(r"^【小Q工作流 \| 快速恢复 】(?:已确认|部分|阻断)\n", chat_text) or any(marker not in chat_text for marker in required):
            raise ContractError("Quick Resume fixed panel is incomplete")
    if open_ui and route["command_id"] in {"help", "token-dashboard"}:
        actions = payload.get("surface", {}).get("actions", [])
        if not actions or actions[0].get("requested") is not True or actions[0].get("status") == "not-requested":
            raise ContractError(f"{route['command_id']} open action was not attempted")


def audit_state(state_root: Path) -> tuple[dict[str, Any], bool]:
    runtime = runtime_state_root()
    items = parse_todo(state_root / "TODO.md")
    load_todo_display(state_root, items)
    checks = [mirror_status(state_root / name, runtime / name) for name in STATE_MIRROR_FILES]
    active = parse_active_work(state_root / "ACTIVE_WORK.md")
    pointer = active.get("recovery_pointer", {}) if isinstance(active, dict) else {}
    binding = managed_task_binding_status(state_root, pointer if isinstance(pointer, dict) else {})
    binding_ok = not binding["required"] or binding["status"] == "pass"
    mirror_ok = all(check["match"] for check in checks)
    ok = mirror_ok and binding_ok
    return {
        "status": "pass" if ok else ("blocked" if not binding_ok else "drift"),
        "authority": str(state_root),
        "open_count": len(items),
        "open_ids": [item.item_id for item in items],
        "mirrors": checks,
        "task_binding": binding,
    }, ok


def self_test() -> dict[str, Any]:
    contract = load_contract()
    route_cases = {
        "TODO": "todo-list",
        "todo": "todo-list",
        "Todo": "todo-list",
        "TODO:new": "todo-add",
        "TODO：新事项": "todo-add",
        "TOKEN": "token-dashboard",
        "token usage": "token-dashboard",
        "help": "help",
        "帮助": "help",
        "status": "status",
        "状态": "status",
        "checkpoint": "checkpoint",
        "小Q": "quick-resume",
        "继续小Q": "quick-resume",
        "更新skill的标准": "skill-maintenance",
        "请专家审查": "expert-review",
    }
    failures = []
    for value, expected in route_cases.items():
        actual = route_command(value, None, contract)["command_id"]
        if actual != expected:
            failures.append(f"{value!r}: expected {expected}, got {actual}")
    recency_fixture = [
        {"text": "请修复 TODO、帮助、TOKEN 和小Q格式，并做专家审核"},
        {"text": "<recommended_plugins>injected plugin catalog</recommended_plugins>"},
    ]
    selected_recency = select_latest_concrete_user_message(recency_fixture)
    if selected_recency is None or not selected_recency["text"].startswith("请修复"):
        failures.append("Quick Resume internal-control message filter failed")
    if route_command("1", "todo-list", contract)["command_id"] != "todo-select":
        failures.append("contextual TODO selection failed")
    try:
        route_command("1", None, contract)
        failures.append("bare numeric command did not fail closed")
    except ContractError:
        pass
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        valid = root / "TODO.md"
        valid.write_text("# TODO\n\n## Open\n- [ ] 2026-07-12 | one | next action\n\n## Done\n", encoding="utf-8")
        if [item.item_id for item in parse_todo(valid)] != ["one"]:
            failures.append("valid TODO parse failed")
        empty = root / "empty.md"
        empty.write_text("# TODO\n\n## Open\n\n## Done\n", encoding="utf-8")
        if parse_todo(empty) != []:
            failures.append("empty TODO parse failed")
        malformed = root / "malformed.md"
        malformed.write_text("# TODO\n\n- [ ] bad\n", encoding="utf-8")
        try:
            parse_todo(malformed)
            failures.append("malformed TODO did not fail closed")
        except ContractError:
            pass
        malformed_open = root / "malformed-open.md"
        malformed_open.write_text("# TODO\n\n## Open\n- bad row\n\n## Done\n", encoding="utf-8")
        try:
            parse_todo(malformed_open)
            failures.append("malformed Open row did not fail closed")
        except ContractError:
            pass
        invalid_rows = {
            "empty-date": "- [ ]  | empty-date | description",
            "bad-date": "- [ ] 2026-02-30 | bad-date | description",
            "empty-description": "- [ ] 2026-07-12 | empty-description | ",
        }
        for name, row in invalid_rows.items():
            invalid = root / f"{name}.md"
            invalid.write_text(f"# TODO\n\n## Open\n{row}\n\n## Done\n", encoding="utf-8")
            try:
                parse_todo(invalid)
                failures.append(f"{name} TODO row did not fail closed")
            except ContractError:
                pass
        select_route = route_command("1", "todo-list", contract)
        selected = execute_todo(select_route, root, "todo-list", todo_context_token(valid, root / "TODO_DISPLAY.zh-CN.json"), False)
        if selected.get("selected", {}).get("item_id") != "one" or "详情：" not in selected.get("surface", {}).get("chat_text", ""):
            failures.append("context-token TODO selection failed")
        try:
            execute_todo(select_route, root, "todo-list", "STALE", False)
            failures.append("stale TODO context token did not fail closed")
        except ContractError:
            pass
        created = append_todo(valid, "new regression reminder")
        if created.item_id != "new-regression-reminder" or len(parse_todo(valid)) != 2:
            failures.append("atomic TODO append failed")
        concurrent_hub = root / "concurrent-hub"
        concurrent_state = concurrent_hub / "personal-state"
        concurrent_state.mkdir(parents=True)
        concurrent_todo = concurrent_state / "TODO.md"
        concurrent_todo.write_text("# TODO\n\nUpdated: 2026-07-12\n\n## Open\n\n## Done\n", encoding="utf-8")
        (concurrent_state / "ACTIVE_WORK.md").write_text("# Active Work\n\n## Current Focus\n\nTest.\n", encoding="utf-8")
        concurrent_home = root / "concurrent-home"
        concurrent_home.mkdir()
        (concurrent_home / "q-profile.json").write_text(json.dumps({"hub": str(concurrent_hub)}), encoding="utf-8")
        concurrent_env = os.environ.copy()
        concurrent_env["CODEX_HOME"] = str(concurrent_home)
        writers = [
            subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--input", f"TODO:{name}", "--commit", "--format", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=concurrent_env,
            )
            for name in ("concurrent alpha", "concurrent beta")
        ]
        writer_results = [writer.communicate(timeout=15) + (writer.returncode,) for writer in writers]
        concurrent_ids = {item.item_id for item in parse_todo(concurrent_todo)}
        if any(result[2] != 0 for result in writer_results) or concurrent_ids != {"concurrent-alpha", "concurrent-beta"}:
            failures.append(f"concurrent TODO writers lost data: ids={sorted(concurrent_ids)}; writers={writer_results}")
        missing = root / "missing.md"
        status = mirror_status(missing, missing)
        if status["match"]:
            failures.append("dual-missing mirror incorrectly matched")

        source_state = root / "source" / "personal-state"
        runtime_home = root / "runtime-home"
        runtime_state = runtime_home / "q-personal-state"
        source_state.mkdir(parents=True)
        runtime_state.mkdir(parents=True)
        (source_state / "TODO.md").write_text("# TODO\n\n## Open\n\n## Done\n", encoding="utf-8")
        (source_state / "ACTIVE_WORK.md").write_text("# Active Work\n\n## Current Focus\n\nNone.\n", encoding="utf-8")
        (runtime_state / "TODO.md").write_text("# TODO\n\n## Open\n- [ ] 2026-07-12 | preserved | keep\n\n## Done\n", encoding="utf-8")
        (runtime_state / "ACTIVE_WORK.md").write_text("# Active Work\n\n## Current Focus\n\nOld.\n", encoding="utf-8")
        previous_codex_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(runtime_home)
        try:
            try:
                sync_runtime_state(source_state)
                failures.append("runtime-only TODO id was overwritten without explicit allow-state-drop")
            except ContractError:
                pass
        finally:
            if previous_codex_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_codex_home
    return {"status": "pass" if not failures else "fail", "failures": failures, "cases": len(route_cases) + 15}


def self_test_v2() -> dict[str, Any]:
    contract = load_contract()
    route_cases = {
        "TODO": "todo-list",
        "todo": "todo-list",
        "Todo": "todo-list",
        "TODO:new": "todo-add",
        "TODO：新事项": "todo-add",
        "TOKEN": "token-dashboard",
        "token usage": "token-dashboard",
        "help": "help",
        "帮助": "help",
        "status": "status",
        "状态": "status",
        "checkpoint": "checkpoint",
        "小Q": "quick-resume",
        "继续小Q": "quick-resume",
        "更新skill的标准": "skill-maintenance",
        "请专家审查": "expert-review",
    }
    failures: list[str] = []
    for value, expected in route_cases.items():
        try:
            actual = route_command(value, None, contract)["command_id"]
        except ContractError as exc:
            failures.append(f"{value!r}: routing blocked: {exc}")
            continue
        if actual != expected:
            failures.append(f"{value!r}: expected {expected}, got {actual}")
    try:
        if route_command("1", "todo-list", contract)["command_id"] != "todo-select":
            failures.append("contextual TODO selection failed")
        route_command("1", None, contract)
        failures.append("bare numeric command did not fail closed")
    except ContractError:
        pass

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        explicit_hub = root / "explicit-hub"
        fallback_hub = root / "fallback-hub"
        explicit_hub.mkdir()
        fallback_hub.mkdir()
        explicit_profile = {
            "hub": str(explicit_hub),
            "repositories": {"q-personal-hub": {"path": str(fallback_hub)}},
        }
        if resolve_hub(explicit_profile, root / "q-profile.json") != explicit_hub.resolve():
            failures.append("explicit top-level hub did not override a different fallback repository path")
        missing_profile = {
            "hub": str(root / "missing-explicit-hub"),
            "repositories": {"q-personal-hub": {"path": str(fallback_hub)}},
        }
        try:
            resolve_hub(missing_profile, root / "q-profile.json")
            failures.append("missing explicit top-level hub silently fell back to a repository path")
        except ContractError as exc:
            if "configured authoritative hub does not exist" not in str(exc):
                failures.append(f"missing explicit hub failed for the wrong reason: {exc}")
        fallback_profile = {
            "repositories": {"q-personal-hub": {"path": str(fallback_hub)}},
        }
        if resolve_hub(fallback_profile, root / "q-profile.json") != fallback_hub.resolve():
            failures.append("single repository fallback was not used when top-level hub was absent")
        ambiguous_profile = {
            "repositories": {
                "q-personal-hub": {"path": str(explicit_hub), "local_path": str(fallback_hub)}
            },
        }
        try:
            resolve_hub(ambiguous_profile, root / "q-profile.json")
            failures.append("different existing fallback hub paths did not fail closed")
        except ContractError as exc:
            if "ambiguous personal hubs" not in str(exc):
                failures.append(f"ambiguous fallback hubs failed for the wrong reason: {exc}")
        todo = root / "TODO.md"
        todo.write_text(
            "# TODO\n\nUpdated: 2026-07-13\n\n## Open\n"
            "- [ ] 2026-07-12 | one | Do one. Next action: act. Completion gate: evidence.\n\n## Done\n",
            encoding="utf-8",
        )
        (root / "TODO_DISPLAY.zh-CN.json").write_text(
            json.dumps({
                "version": 1,
                "language": "zh-CN",
                "items": {"one": {"name": "第一项待办", "summary": "下一步执行并保存证据。", "detail": "当前执行第一项；下一步执行并保存证据；完成条件是形成闭环。", "source_fingerprint": todo_source_fingerprint("Do one. Next action: act. Completion gate: evidence.")}},
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        active = root / "ACTIVE_WORK.md"
        active.write_text(
            "# Active Work\n\n## Current Focus\n\nRepair.\n\n## RECOVERY_POINTER v1\n\n"
            "task_id: repair\nwork_state: active\nintegrity_state: in-progress\nrelease_state: local-only\n"
            "active_project: q-workflow\npath: C:\\\\q\nlatest_verified_note: fixture\nnext_action: validate\n",
            encoding="utf-8",
        )
        duplicate_active = root / "ACTIVE_WORK_DUPLICATE.md"
        duplicate_active.write_text(
            active.read_text(encoding="utf-8")
            + "\n## RECOVERY_POINTER historical-copy\n\ntask_id: stale\n",
            encoding="utf-8",
        )
        try:
            parse_active_work(duplicate_active)
            failures.append("multiple executable RECOVERY_POINTER headings did not fail closed")
        except ContractError as exc:
            if "RECOVERY_POINTER" not in str(exc):
                failures.append(f"duplicate RECOVERY_POINTER failed for the wrong reason: {exc}")
        missing_pointer = root / "ACTIVE_WORK_MISSING_POINTER.md"
        missing_pointer.write_text("# Active Work\n\n## Current Focus\n\nRepair.\n", encoding="utf-8")
        try:
            parse_active_work(missing_pointer)
            failures.append("missing executable RECOVERY_POINTER did not fail closed")
        except ContractError as exc:
            if "RECOVERY_POINTER" not in str(exc):
                failures.append(f"missing RECOVERY_POINTER failed for the wrong reason: {exc}")
        idle_active = root / "ACTIVE_WORK_IDLE.md"
        idle_active.write_text("# Active Work\n\n## Current Focus\n\n- No active blocking focus.\n", encoding="utf-8")
        if parse_active_work(idle_active).get("recovery_pointer") != {}:
            failures.append("explicit idle ACTIVE_WORK did not allow zero RECOVERY_POINTER headings")
        adversarial = {
            "empty pointer": "# Active Work\n\n## Current Focus\n\nRepair.\n\n## RECOVERY_POINTER v1\n",
            "duplicate key": "# Active Work\n\n## Current Focus\n\nRepair.\n\n## RECOVERY_POINTER v1\n\ntask_id: current\ntask_id: stale\n",
            "idle plus pointer": "# Active Work\n\n## Current Focus\n\n- No active blocking focus.\n\n## RECOVERY_POINTER v1\n\ntask_id: stale\n",
        }
        for label, content in adversarial.items():
            fixture = root / f"ACTIVE_WORK_{label.replace(' ', '_').upper()}.md"
            fixture.write_text(content, encoding="utf-8")
            try:
                parse_active_work(fixture)
                failures.append(f"{label} ACTIVE_WORK did not fail closed")
            except ContractError:
                pass
        todo_payload = execute_todo(route_command("TODO", None, contract), root, None, None, False)
        todo_chat = todo_payload.get("surface", {}).get("chat_text", "")
        if todo_chat.count("\n1. one /") != 1 or "详情：当前执行第一项" not in todo_chat or "Next action: act" in todo_chat or "回复编号" in todo_chat:
            failures.append("TODO user-visible two-line surface contract failed")
        token = todo_context_token(todo, root / "TODO_DISPLAY.zh-CN.json")
        selected = execute_todo(route_command("1", "todo-list", contract), root, "todo-list", token, False)
        selected_chat = selected.get("surface", {}).get("chat_text", "")
        if (
            selected.get("selected", {}).get("item_id") != "one"
            or "当前执行第一项" not in selected_chat
            or "\n详情：\n" not in selected_chat
            or selected_chat.count("\n") < 5
        ):
            failures.append("context-token TODO selection failed")
        display_path = root / "TODO_DISPLAY.zh-CN.json"
        shared_lock_path = root / ".q-workflow-manager.lock"
        shared_descriptor = acquire_lock(shared_lock_path)
        try:
            try:
                append_todo(todo, "must remain blocked by the shared state lock", display_path)
                failures.append("TODO append bypassed the shared workflow state lock")
            except ContractError as exc:
                if "holds" not in str(exc):
                    failures.append(f"shared TODO lock failed for the wrong reason: {exc}")
        finally:
            release_lock(shared_lock_path, shared_descriptor)
        crash_probe = (
            "import os,sys; from pathlib import Path; "
            "sys.path.insert(0,sys.argv[1]); "
            "from workflow_file_ops import acquire_lock; "
            "held=acquire_lock(Path(sys.argv[2])); os._exit(0)"
        )
        crashed = subprocess.run(
            [sys.executable, "-c", crash_probe, str(Path(__file__).resolve().parent), str(shared_lock_path)],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        if crashed.returncode != 0:
            failures.append(f"crash-release lock fixture failed: {crashed.stderr or crashed.stdout}")
        else:
            try:
                recovered_descriptor = acquire_lock(shared_lock_path)
                release_lock(shared_lock_path, recovered_descriptor)
            except WorkflowFileLockError as exc:
                failures.append(f"OS lock remained stale after process exit: {exc}")
        changed_display = read_json(display_path)
        changed_display["items"]["one"]["detail"] = "当前执行第一项；展示内容已更新；完成条件是形成闭环。"
        atomic_write_text(display_path, json.dumps(changed_display, ensure_ascii=False, indent=2) + "\n")
        try:
            execute_todo(route_command("1", "todo-list", contract), root, "todo-list", token, False)
            failures.append("display change did not invalidate TODO selection token")
        except ContractError:
            pass
        pseudo_localized_display = read_json(display_path)
        pseudo_localized_display["items"]["one"]["summary"] = "Mostly English 中文"
        atomic_write_text(display_path, json.dumps(pseudo_localized_display, ensure_ascii=False, indent=2) + "\n")
        try:
            execute_todo(route_command("TODO", None, contract), root, None, None, False)
            failures.append("pseudo-localized TODO display passed the Chinese content gate")
        except ContractError:
            pass
        changed_display["items"]["one"]["detail"] = "当前执行第一项；展示内容已更新；完成条件是形成闭环。"
        atomic_write_text(display_path, json.dumps(changed_display, ensure_ascii=False, indent=2) + "\n")
        try:
            execute_todo(route_command("1", "todo-list", contract), root, "todo-list", "STALE", False)
            failures.append("stale TODO context token did not fail closed")
        except ContractError:
            pass

        active_before_dangling = active.read_text(encoding="utf-8")
        active.write_text(
            "# Active Work\n\n## Current Focus\n\nManaged missing task.\n\n"
            "## RECOVERY_POINTER v2\n\nschema: q-workflow-focus-v2\n"
            "task_id: missing-managed-task\nwork_state: active\nvisibility_latch: phase-b-required\n"
            "integrity_state: local-validated\n"
            "release_state: local-only\nnext_action: repair\n",
            encoding="utf-8",
        )
        blocked_quick = execute_status(route_command("小Q", None, contract), root, quick_resume=True, check_recency=False)
        blocked_chat = blocked_quick.get("surface", {}).get("chat_text", "")
        if (
            blocked_quick.get("task_binding", {}).get("status") != "blocked"
            or not blocked_chat.startswith("【小Q工作流 | 快速恢复 】阻断\n")
            or "record_state: stale" not in blocked_chat
        ):
            failures.append("managed dangling task binding did not block Quick Resume")
        active.write_text(
            active.read_text(encoding="utf-8").replace("visibility_latch: phase-b-required\n", ""),
            encoding="utf-8",
        )
        missing_latch_quick = execute_status(route_command("小Q", None, contract), root, quick_resume=True, check_recency=False)
        if not any(
            "visibility_latch" in error
            for error in missing_latch_quick.get("task_binding", {}).get("errors", [])
        ):
            failures.append("managed Phase B pointer without visibility latch did not block Quick Resume")
        active.write_text(active_before_dangling, encoding="utf-8")

        quick_payload = execute_status(route_command("小Q", None, contract), root, quick_resume=True, check_recency=False)
        quick_chat = quick_payload.get("surface", {}).get("chat_text", "")
        if not quick_chat.startswith("【小Q工作流 | 快速恢复 】部分\n") or "record_state: partial" not in quick_chat or "目标：" not in quick_chat or "最近：" not in quick_chat:
            failures.append("quick-resume fixed surface contract failed")

        session_home = root / "session-home"
        session_dir = session_home / "sessions" / "2026" / "07"
        session_dir.mkdir(parents=True)
        session_rows = [{
            "type": "session_meta",
            "payload": {"id": "fixture-session", "cwd": str(root), "timestamp": "2026-07-13T00:00:00Z"},
        }]
        def user_row(timestamp: str, text: str) -> dict[str, Any]:
            return {
                "timestamp": timestamp,
                "type": "response_item",
                "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]},
            }
        real_request = "请修复 TODO、帮助、TOKEN 和小Q格式，并做专家审核"
        session_rows.append(user_row("2026-07-13T00:00:01Z", real_request))
        for index in range(12):
            session_rows.append(user_row(f"2026-07-13T00:00:{index + 2:02d}Z", f"<recommended_plugins>control-{index}</recommended_plugins>"))
        for index, command in enumerate(("TODO", "帮助", "TOKEN", "小Q"), 20):
            session_rows.append(user_row(f"2026-07-13T00:00:{index:02d}Z", command))
        (session_dir / "rollout-fixture-session.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in session_rows) + "\n",
            encoding="utf-8",
        )
        older_fork_rows = [
            {"type": "session_meta", "payload": {"id": "older-fork", "cwd": str(root), "timestamp": "2026-07-12T00:00:00Z"}},
            user_row("2026-07-12T23:59:59Z", "赶紧查资料、专家审查，工作流骨架再次大幅改进"),
        ]
        (session_dir / "rollout-newer-mtime-older-message.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in older_fork_rows) + "\n",
            encoding="utf-8",
        )
        previous_codex_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(session_home)
        try:
            recency_result = recent_chat_evidence({"latest_chat_override": real_request})
            if recency_result.get("latest_text") != real_request or recency_result.get("confidence") != "confirmed":
                failures.append("Quick Resume source-filter-before-window integration failed")
        finally:
            if previous_codex_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_codex_home

        add_route = route_command("TODO：新增回归事项", None, contract)
        added = execute_todo(add_route, root, None, None, commit=True)
        if added.get("write_status") != "committed" or not added.get("created", {}).get("item_id", "").startswith("todo-"):
            failures.append("TODO/display atomic add did not commit")
        listed_after_add = execute_todo(route_command("TODO", None, contract), root, None, None, False)
        if listed_after_add.get("open_count") != 2 or "新增回归事项" not in listed_after_add.get("surface", {}).get("chat_text", ""):
            failures.append("TODO add -> list display lifecycle failed")
        previous_codex_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(root / "runtime-home")
        try:
            sync_result = sync_runtime_state(root)
            audit_payload, audit_ok = audit_state(root)
            if "TODO_DISPLAY.zh-CN.json" not in sync_result.get("synced", []) or not audit_ok or audit_payload.get("status") != "pass":
                failures.append("TODO add -> sync lifecycle failed")
            runtime_root = runtime_state_root()
            guarded_paths = [runtime_root / name for name in STATE_MIRROR_FILES] + [runtime_root / "runtime-manifest.json"]
            runtime_before = {path: path.read_bytes() for path in guarded_paths}
            source_todo = root / "TODO.md"
            source_todo_before = source_todo.read_bytes()
            source_todo.write_bytes(source_todo_before + b"\n<!-- runtime rollback fixture -->\n")
            try:
                sync_runtime_state(root, _test_fail_after_write=2)
                failures.append("runtime-state injected transaction failure was accepted")
            except ContractError as exc:
                if "Injected" not in str(exc):
                    failures.append(f"runtime-state rollback failed for the wrong reason: {exc}")
            finally:
                source_todo.write_bytes(source_todo_before)
            runtime_after = {path: path.read_bytes() for path in guarded_paths}
            if runtime_after != runtime_before:
                failures.append("runtime-state injected transaction failure did not restore all mirror targets")
        finally:
            if previous_codex_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_codex_home

        help_hub = root / "help-hub"
        (help_hub / "personal-state").mkdir(parents=True)
        (help_hub / "FIRST_RUN_GUIDE.zh-CN.html").write_text("<html>help</html>", encoding="utf-8")
        help_payload = execute_help(route_command("帮助", None, contract), contract, help_hub, open_ui=False)
        help_chat = help_payload.get("surface", {}).get("chat_text", "")
        if help_payload.get("guide_kind") != "html" or "一分钟试跑" not in help_chat or "1～7" in help_chat or "1~7" in help_chat:
            failures.append("HTML-first help surface contract failed")
        (help_hub / "FIRST_RUN_GUIDE.zh-CN.html").unlink()
        (help_hub / "personal-state" / "ASSISTANT_HELP.md").write_text("# fallback", encoding="utf-8")
        fallback_help = execute_help(route_command("帮助", None, contract), contract, help_hub, open_ui=False)
        fallback_chat = fallback_help.get("surface", {}).get("chat_text", "")
        if fallback_help.get("guide_kind") != "markdown-fallback" or "Markdown 兜底帮助" not in fallback_chat or "HTML 帮助页" in fallback_chat:
            failures.append("Help Markdown fallback receipt drifted")

        synthetic_token = {
            "latest_turn": {
                "tokens": {"total_tokens": 2500},
                "context_window": 10000,
                "context_pressure": 25.0,
                "metrics": {"cached_input_ratio": 90.0, "uncached_input_tokens": 250},
            },
            "current": {"tokens": {"total_tokens": 10000}},
            "project": {"tokens": {"total_tokens": 20000}},
            "total": {"tokens": {"total_tokens": 30000}},
            "health": [{"level": "ok"}],
        }
        token_chat = render_token_chat(synthetic_token, root / "token.html", {"status": "opened-test-receipt"})
        if token_chat.count("\n") != 4 or "本轮：2,500" not in token_chat or "仪表盘：已打开" not in token_chat:
            failures.append("TOKEN concise summary surface contract failed")
        synthetic_token["latest_turn"]["metrics"]["cached_input_ratio"] = 25.0
        if "缓存：25.0%（偏低）" not in render_token_chat(synthetic_token, root / "token.html", {"status": "opened-test-receipt"}):
            failures.append("TOKEN low-cache semantic label failed")
        synthetic_token["latest_turn"]["metrics"]["cached_input_ratio"] = 90.0
        synthetic_token["efficiency_trend"] = {"cache_ratio_spread": 40.0}
        if "缓存：90.0%（波动较大）" not in render_token_chat(synthetic_token, root / "token.html", {"status": "opened-test-receipt"}):
            failures.append("TOKEN cache-volatility semantic label failed")

        negative_surfaces = []
        bad_todo = json.loads(json.dumps(todo_payload, ensure_ascii=False))
        bad_todo["surface"]["chat_text"] = "小Q工作流 / q-assistant-profile / TODO\n1. one\n回复编号继续"
        negative_surfaces.append((route_command("TODO", None, contract), bad_todo, "bare-title TODO"))
        bad_help = json.loads(json.dumps(help_payload, ensure_ascii=False))
        bad_help["surface"]["chat_text"] = "小Q工作流 / q-assistant-profile / 帮助\n1～7 继续对应待办"
        negative_surfaces.append((route_command("帮助", None, contract), bad_help, "menu-only Help"))
        token_route = route_command("TOKEN", None, contract)
        bad_token = {
            **token_route,
            "dashboard": str(root / "token.html"),
            "open_status": "opened-test-receipt",
            "summary": {},
            "surface": surface("小Q工作流 / q-workflow / TOKEN\n仪表盘已打开"),
        }
        (root / "token.html").write_text("dashboard", encoding="utf-8")
        negative_surfaces.append((token_route, bad_token, "dashboard-only TOKEN"))
        bad_quick = json.loads(json.dumps(quick_payload, ensure_ascii=False))
        bad_quick["surface"]["chat_text"] = "【小Q工作流 | 快速恢复 】部分\n状态：active"
        negative_surfaces.append((route_command("小Q", None, contract), bad_quick, "incomplete Quick Resume"))
        for negative_route, negative_payload, label in negative_surfaces:
            try:
                validate_output_surface(negative_route, negative_payload, contract, open_ui=False)
                failures.append(f"negative surface was accepted: {label}")
            except ContractError:
                pass

        malformed = root / "malformed.md"
        malformed.write_text("# TODO\n\n## Open\n- bad row\n\n## Done\n", encoding="utf-8")
        try:
            parse_todo(malformed)
            failures.append("malformed Open row did not fail closed")
        except ContractError:
            pass
        missing = root / "missing.md"
        if mirror_status(missing, missing)["match"]:
            failures.append("dual-missing mirror incorrectly matched")

    return {"status": "pass" if not failures else "fail", "failures": failures, "cases": len(route_cases) + 20}


def print_result(payload: dict[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    chat_text = payload.get("surface", {}).get("chat_text")
    if isinstance(chat_text, str) and chat_text:
        print(chat_text)
        return
    print(json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", help="Exact command text to route and, for TODO, execute read-only.")
    parser.add_argument("--context", choices=("todo-list",), help="Current valid contextual command source.")
    parser.add_argument("--context-token", help="Hash token returned by the current TODO list.")
    parser.add_argument("--commit", action="store_true", help="Commit TODO:<text> atomically to the authoritative hub.")
    parser.add_argument("--format", choices=("json", "chat", "text"), default="json")
    parser.add_argument("--open-ui", action="store_true", help="Open the Help or TOKEN HTML artifact and return an action receipt.")
    parser.add_argument("--audit", action="store_true", help="Audit authoritative personal state versus runtime mirrors.")
    parser.add_argument("--preflight-sync", action="store_true", help="Validate a runtime mirror rebuild without writing files.")
    parser.add_argument("--sync-runtime", action="store_true", help="Rebuild runtime TODO/ACTIVE_WORK mirrors from q-profile authority.")
    parser.add_argument("--allow-state-drop", action="store_true", help="Allow reviewed removal of runtime-only Open TODO ids during mirror rebuild.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            payload = self_test_v2()
            print_result(payload, args.format)
            return EXIT_OK if payload["status"] == "pass" else EXIT_INVALID
        pfile, hub, state_root = authority()
        profile = read_json(pfile)
        if args.preflight_sync:
            payload = preflight_runtime_state(state_root, allow_state_drop=args.allow_state_drop)
            payload.update({"profile": str(pfile), "hub": str(hub)})
            print_result(payload, args.format)
            return EXIT_OK
        if args.sync_runtime:
            sync_result = sync_runtime_state(state_root, allow_state_drop=args.allow_state_drop)
        else:
            sync_result = None
        if args.audit:
            payload, ok = audit_state(state_root)
            payload.update({"profile": str(pfile), "hub": str(hub), "sync": sync_result})
            print_result(payload, args.format)
            return EXIT_OK if ok else EXIT_DRIFT
        if not args.input:
            parser.error("--input is required unless --audit or --self-test is used")
        contract = load_contract()
        route = route_command(args.input, args.context, contract)
        if route["handler"].startswith("todo_"):
            payload = execute_todo(route, state_root, args.context, args.context_token, args.commit)
        elif route["handler"] == "help":
            help_hub = resolve_personal_hub(profile, pfile, hub)
            payload = execute_help(route, contract, help_hub, open_ui=args.open_ui)
        elif route["handler"] == "status":
            payload = execute_status(route, state_root)
        elif route["handler"] == "checkpoint":
            payload = execute_checkpoint(route, state_root)
        elif route["handler"] == "quick_resume":
            payload = execute_status(route, state_root, quick_resume=True)
        elif route["handler"] == "token_dashboard":
            payload = execute_token(route, open_ui=args.open_ui)
        else:
            payload = {**route, "profile": str(pfile), "hub": str(hub)}
        validate_output_surface(route, payload, contract, open_ui=args.open_ui)
        payload["sync"] = sync_result
        print_result(payload, args.format)
        return EXIT_OK
    except ContractError as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
