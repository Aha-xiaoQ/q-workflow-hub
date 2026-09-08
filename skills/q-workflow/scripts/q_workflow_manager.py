#!/usr/bin/env python3
"""Unified local manager for q-workflow health, surfaces, and task state.

Read-only commands are the default. Task writes require a generated plan,
compare-and-swap hashes, an exclusive lock, explicit --yes, readback
validation, and a transaction receipt.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from active_work_pointer import inspect_active_work, render_active_work
from runtime_state_manifest import (
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
    transaction_journal_path,
)
from workflow_task_state import (
    TASK_ID_RE,
    TASK_SCHEMA,
    TaskStateError,
    build_task_event,
    event_line,
    flatten_task_record,
    inspect_task_record,
    read_event_log,
    read_json_object,
    release_receipt_errors,
    resolve_task_record,
    sha256_bytes,
    sha256_file,
    task_event_log_path,
    task_record_bytes,
    task_record_path,
    validate_task_record,
    validate_transition,
)


SURFACE_TIERS = {"core", "flagship", "lab"}
SURFACE_RESOLVERS = {"profile-repository", "personal-hub", "codex-home"}
REQUIRED_SURFACE_ROOTS = {"source", "bootstrap", "runtime", "personal-source"}
REQUIRED_CORE_SKILLS = {
    "q-workflow",
    "q-agent-roster",
    "q-skill-creation",
    "q-research-discovery",
    "q-assistant-profile",
}
APPROVED_IGNORED_DIRECTORIES = {".git", "__pycache__", "node_modules", ".venv", "venv", ".tmp"}
APPROVED_IGNORED_SUFFIXES = {".pyc", ".pyo"}


MISSING_HASH = "MISSING"
PLAN_SCHEMA = "q-workflow-task-plan-v1"
RECEIPT_SCHEMA = "q-workflow-task-transaction-v1"
DEFAULT_COMMAND_TIMEOUT_SECONDS = 120


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def default_profile_path() -> Path:
    return Path(os.environ.get("Q_PROFILE_PATH", str(codex_home() / "q-profile.json")))


def load_profile(path: Path | None = None) -> tuple[Path, dict[str, Any]]:
    profile_path = (path or default_profile_path()).resolve()
    return profile_path, read_json_object(profile_path)


def personal_hub(profile: dict[str, Any]) -> Path:
    raw = profile.get("hub")
    if not isinstance(raw, str) or not raw.strip():
        raise TaskStateError("q-profile does not declare hub")
    hub = Path(raw).expanduser().resolve()
    if not hub.is_dir():
        raise TaskStateError(f"Personal hub does not exist: {hub}")
    return hub


def _remote_ref_oid(output: str, remote_ref: str) -> tuple[str | None, str | None]:
    matches = []
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[1] == remote_ref:
            matches.append(fields[0])
    if len(matches) != 1:
        return None, f"live remote verification expected one {remote_ref} result, found {len(matches)}"
    return matches[0], None


def live_remote_receipt_errors(
    profile: dict[str, Any],
    binding: dict[str, str],
    *,
    timeout_seconds: int = 20,
) -> list[str]:
    """Verify the release receipt's bound ref against the named remote."""
    repositories = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    repository_id = binding.get("release_repository", "q-workflow-hub")
    if not isinstance(repository_id, str) or not repository_id.strip():
        return ["release_repository must name a registered repository"]
    repository = repositories.get(repository_id)
    if not isinstance(repository, dict):
        return [f"q-profile lacks registered repository {repository_id!r} for live remote verification"]
    raw_path = repository.get("path") or repository.get("registry_path") or repository.get("local_path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return [f"q-profile {repository_id} path is missing for live remote verification"]
    repository_path = Path(raw_path).resolve()
    remote = binding.get("release_remote", "").strip()
    expected_remote = str(repository.get("remote", "")).strip()
    branch = binding.get("release_branch", "").strip()
    target_oid = binding.get("release_target_oid", "").strip()
    if not remote or not branch or not target_oid:
        return ["release remote, branch, and target OID are required for live verification"]
    if not expected_remote:
        return [f"q-profile {repository_id} remote is missing for live remote verification"]
    if remote != expected_remote:
        if remote in {".", ".."} or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", remote) is None:
            return ["release_remote must equal the configured URL or name a configured Git remote"]
        try:
            configured = subprocess.run(
                ["git", "-C", str(repository_path), "remote", "get-url", "--all", remote],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return [f"configured remote lookup failed: {exc}"]
        configured_urls = [line.strip() for line in configured.stdout.splitlines() if line.strip()]
        if configured.returncode != 0 or configured_urls != [expected_remote]:
            return ["release_remote is not bound to the q-profile configured remote URL"]
    remote_ref = branch if branch.startswith("refs/") else f"refs/heads/{branch}"
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_path), "ls-remote", "--exit-code", expected_remote, remote_ref],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [f"live remote verification failed: {exc}"]
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        return [f"live remote verification returned {completed.returncode}: {detail or 'no matching remote ref'}"]
    remote_oid, parse_error = _remote_ref_oid(completed.stdout, remote_ref)
    if parse_error:
        return [parse_error]
    if str(remote_oid).casefold() != target_oid.casefold():
        return [f"live remote {remote_ref} is {remote_oid}, expected {target_oid}"]
    return []


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def canonical_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def path_hash(path: Path) -> str:
    return sha256_file(path) if path.is_file() else MISSING_HASH


def encode_bytes(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def decode_bytes(value: str) -> bytes:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True)
    except (ValueError, UnicodeError) as exc:
        raise TaskStateError(f"Invalid base64 candidate payload: {exc}") from exc


def _existing_record(path: Path) -> dict[str, Any] | None:
    return read_json_object(path) if path.is_file() else None


def _event_candidate(path: Path, event: dict[str, Any]) -> bytes:
    existing = path.read_bytes() if path.is_file() else b""
    events, errors = read_event_log(path) if path.is_file() else ([], [])
    if errors:
        raise TaskStateError(" ".join(errors))
    matches = [row for row in events if row.get("event_id") == event.get("event_id")]
    if matches:
        if len(matches) == 1 and matches[0] == event:
            return existing
        raise TaskStateError(f"authority_event collision: {event.get('event_id')}")
    if existing and not existing.endswith(b"\n"):
        existing += b"\n"
    return existing + event_line(event).encode("utf-8")


def _target_row(path: Path, candidate: bytes) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "expected_sha256": path_hash(path),
        "candidate_sha256": sha256_bytes(candidate),
        "candidate_base64": encode_bytes(candidate),
    }


def current_focus_text_for_record(profile_path: Path, record: dict[str, Any]) -> str:
    """Return current focus prose only when the candidate already owns focus.

    Preserving prose while changing task identity creates a semantically mixed
    pointer even if every hash and event binding is valid. Cross-task focus
    switches must therefore provide a complete replacement via --focus-file.
    """
    _, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    active_state = inspect_active_work(hub / "personal-state" / "ACTIVE_WORK.md")
    if active_state["errors"]:
        raise TaskStateError("Cannot preserve an invalid ACTIVE_WORK focus: " + " ".join(active_state["errors"]))
    active_task_id = str((active_state.get("recovery_pointer") or {}).get("task_id", "")).strip()
    candidate_task_id = str(record.get("task_id", "")).strip()
    if active_task_id and active_task_id != candidate_task_id:
        raise TaskStateError(
            "--focus-current cannot switch task identity while preserving another task's prose: "
            f"active={active_task_id}, candidate={candidate_task_id}. Use --focus-file for an explicit full focus switch, "
            "or omit both focus options to update the non-focus task only."
        )
    focus_text = str(active_state.get("current_focus_text", "")).strip()
    if not focus_text:
        raise TaskStateError("ACTIVE_WORK has no current focus prose to preserve")
    return focus_text


def task_sections_for_record(record: dict[str, Any], *, required: bool) -> dict[str, str]:
    """Render task-scoped ACTIVE_WORK guidance from the canonical task record."""
    detail = record.get("detail") if isinstance(record.get("detail"), dict) else {}
    raw_rules = detail.get("recovery_rules")
    raw_index = detail.get("non_executable_index")

    def normalized_lines(value: Any, field: str) -> list[str]:
        if value is None:
            return []
        if not isinstance(value, list) or not value or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise TaskStateError(f"detail.{field} must be a non-empty array of non-empty strings")
        return [item.strip() for item in value]

    rules = normalized_lines(raw_rules, "recovery_rules")
    index = normalized_lines(raw_index, "non_executable_index")
    if required and (not rules or not index):
        raise TaskStateError(
            "Cross-task focus switches require detail.recovery_rules and detail.non_executable_index so "
            "ACTIVE_WORK cannot retain another task's guidance."
        )
    sections: dict[str, str] = {}
    if rules:
        sections["Recovery Rules"] = "\n".join(
            f"{number}. {line}" for number, line in enumerate(rules, 1)
        )
    if index:
        sections["Non-Executable Index"] = "\n".join(f"- {line}" for line in index)
    return sections


def build_task_plan(
    profile_path: Path,
    record: dict[str, Any],
    *,
    focus_text: str | None,
) -> dict[str, Any]:
    profile_path, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    task_path = task_record_path(hub, str(record.get("task_id", "")))
    event_path = task_event_log_path(hub)
    errors = validate_task_record(record)
    if record.get("release_state") in {"ready", "released"}:
        binding = flatten_task_record(record)
        errors.extend(
            release_receipt_errors(
                Path(binding.get("release_receipt", "")),
                binding,
                hub,
            )
        )
        errors.extend(live_remote_receipt_errors(profile, binding))
    previous = _existing_record(task_path)
    errors.extend(validate_transition(previous, record))
    if errors:
        raise TaskStateError("Task record cannot be planned: " + " | ".join(errors))

    record_payload = task_record_bytes(record)
    record_sha = sha256_bytes(record_payload)
    event = build_task_event(record, previous, record_sha)
    event_payload = _event_candidate(event_path, event)
    targets: dict[str, dict[str, Any]] = {
        "task_record": _target_row(task_path, record_payload),
        "task_events": _target_row(event_path, event_payload),
    }

    update_focus = focus_text is not None
    if update_focus:
        active_source = hub / "personal-state" / "ACTIVE_WORK.md"
        if not active_source.is_file():
            raise TaskStateError(f"ACTIVE_WORK is missing: {active_source}")
        active_state = inspect_active_work(active_source)
        if active_state["errors"]:
            raise TaskStateError("ACTIVE_WORK cannot be safely rendered: " + " ".join(active_state["errors"]))
        pointer = flatten_task_record(
            record,
            record_path=task_path,
            record_sha256=record_sha,
            event_log=event_path,
        )
        active_task_id = str((active_state.get("recovery_pointer") or {}).get("task_id", "")).strip()
        candidate_task_id = str(record.get("task_id", "")).strip()
        cross_task_switch = bool(active_task_id and active_task_id != candidate_task_id)
        task_sections = task_sections_for_record(record, required=cross_task_switch)
        rendered = render_active_work(
            active_source.read_text(encoding="utf-8-sig"),
            focus_text or "",
            pointer,
            task_sections=task_sections or None,
        ).encode("utf-8")
        active_runtime = codex_home() / "q-personal-state" / "ACTIVE_WORK.md"
        targets["active_source"] = _target_row(active_source, rendered)
        targets["active_runtime"] = _target_row(active_runtime, rendered)
        manifest_path = active_runtime.parent / "runtime-manifest.json"
        manifest = build_runtime_manifest(
            hub / "personal-state",
            active_runtime.parent,
            overrides={active_source: rendered, active_runtime: rendered},
            generated_at=str(record["updated_at"]),
        )
        targets["runtime_manifest"] = _target_row(manifest_path, runtime_manifest_bytes(manifest))

    body: dict[str, Any] = {
        "format_version": 1,
        "schema": PLAN_SCHEMA,
        "created_at": now_iso(),
        "profile_path": str(profile_path),
        "hub": str(hub),
        "codex_home": str(codex_home().resolve()),
        "task_id": record["task_id"],
        "trace_id": record["trace_id"],
        "record": record,
        "update_focus": update_focus,
        "focus_text": focus_text if update_focus else None,
        "targets": targets,
        "event": event,
        "safety": {
            "default": "plan-only",
            "apply_requires": ["explicit --yes", "matching plan_id", "CAS hashes", "exclusive lock"],
            "push_publish": "never",
        },
    }
    body["plan_id"] = sha256_bytes(canonical_json_bytes(body))
    return body


def write_plan(path: Path, plan: dict[str, Any]) -> None:
    atomic_replace_bytes(path.resolve(), (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def verify_plan_identity(plan: dict[str, Any]) -> None:
    plan_id = plan.get("plan_id")
    body = dict(plan)
    body.pop("plan_id", None)
    expected = sha256_bytes(canonical_json_bytes(body))
    if plan_id != expected:
        raise TaskStateError(f"Plan identity mismatch: expected {expected}, found {plan_id}")


def _allowed_transaction_paths(profile_path: Path, plan: dict[str, Any]) -> set[Path]:
    _, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    record = plan.get("record") if isinstance(plan.get("record"), dict) else {}
    allowed = {
        task_record_path(hub, str(record.get("task_id", ""))).resolve(),
        task_event_log_path(hub).resolve(),
    }
    if plan.get("update_focus") is True:
        allowed.add((hub / "personal-state" / "ACTIVE_WORK.md").resolve())
        allowed.add((codex_home() / "q-personal-state" / "ACTIVE_WORK.md").resolve())
        allowed.add((codex_home() / "q-personal-state" / "runtime-manifest.json").resolve())
    return allowed


def _transaction_receipt_path(hub: Path, plan_id: str) -> Path:
    return hub / "personal-state" / "transactions" / f"{plan_id}.json"


def _targets_already_applied(targets: dict[str, Any]) -> bool:
    return all(
        Path(str(row.get("path"))).is_file()
        and path_hash(Path(str(row.get("path")))) == row.get("candidate_sha256")
        for row in targets.values()
        if isinstance(row, dict)
    )


def _write_transaction_journal(path: Path, plan: dict, originals: dict, receipt: dict | None = None) -> None:
    body = {"version": 1, "plan": plan, "originals": originals, "receipt": receipt}
    body["sha256"] = sha256_bytes(canonical_json_bytes(body))
    atomic_replace_bytes(path, canonical_json_bytes(body))


def recover_task_transaction(profile_path: Path, *, yes: bool) -> dict[str, Any]:
    """Restore a stopped transaction, only if every target still matches a known version.

    This covers process interruption, not guaranteed durability across power loss.
    Validation of all entries precedes the first restore; a failed restore leaves
    the journal in place so all cooperative writers remain blocked.
    """
    if not yes:
        raise TaskStateError("Task recovery requires explicit --yes")
    profile_path, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    lock_path = hub / "personal-state" / ".q-workflow-manager.lock"
    descriptor = acquire_lock(lock_path, recovery=True)
    journal_path = transaction_journal_path(lock_path)
    try:
        if not journal_path.exists():
            return {"status": "no-pending-transaction"}
        journal = read_json_object(journal_path)
        digest = journal.pop("sha256", None)
        if journal.get("version") != 1 or digest != sha256_bytes(canonical_json_bytes(journal)):
            raise TaskStateError("Transaction journal integrity mismatch")
        plan = journal.get("plan")
        if not isinstance(plan, dict):
            raise TaskStateError("Transaction journal plan is invalid")
        verify_plan_identity(plan)
        if (plan.get("schema") != PLAN_SCHEMA or plan.get("format_version") != 1
                or Path(str(plan.get("profile_path", ""))).resolve() != profile_path
                or Path(str(plan.get("hub", ""))).resolve() != hub
                or Path(str(plan.get("codex_home", ""))).resolve() != codex_home().resolve()):
            raise TaskStateError("Transaction journal authority mismatch")
        targets = plan.get("targets")
        originals = journal.get("originals")
        if not isinstance(targets, dict) or not targets or not isinstance(originals, dict) or set(originals) != set(targets):
            raise TaskStateError("Transaction journal target inventory mismatch")
        allowed = _allowed_transaction_paths(profile_path, plan)
        restores = []
        seen = set()
        for name, row in targets.items():
            if not isinstance(row, dict):
                raise TaskStateError("Transaction journal target is invalid")
            target = Path(str(row.get("path", ""))).resolve()
            if target not in allowed or target in seen:
                raise TaskStateError("Transaction journal target escaped or duplicates its boundary")
            seen.add(target)
            original = originals[name]
            before = None if original is None else decode_bytes(str(original))
            before_hash = MISSING_HASH if before is None else sha256_bytes(before)
            candidate = decode_bytes(str(row.get("candidate_base64", "")))
            if before_hash != row.get("expected_sha256") or sha256_bytes(candidate) != row.get("candidate_sha256"):
                raise TaskStateError("Transaction journal payload hash mismatch")
            if path_hash(target) not in {before_hash, row["candidate_sha256"]}:
                raise TaskStateError(f"Transaction recovery refuses external drift: {target}")
            restores.append((target, before))
        receipt_path = _transaction_receipt_path(hub, str(plan["plan_id"]))
        receipt = journal.get("receipt")
        if receipt is not None:
            if not isinstance(receipt, dict) or receipt.get("path") != str(receipt_path):
                raise TaskStateError("Transaction receipt boundary mismatch")
            candidate = decode_bytes(str(receipt.get("candidate_base64", "")))
            if sha256_bytes(candidate) != receipt.get("candidate_sha256"):
                raise TaskStateError("Transaction receipt hash mismatch")
            if path_hash(receipt_path) not in {MISSING_HASH, receipt["candidate_sha256"]}:
                raise TaskStateError("Transaction recovery refuses receipt drift")
            restores.append((receipt_path, None))
        elif receipt_path.exists():
            raise TaskStateError("Unexpected receipt exists during transaction recovery")
        for target, before in reversed(restores):
            if before is None:
                target.unlink(missing_ok=True)
            else:
                atomic_replace_bytes(target, before)
        journal_path.unlink()
        return {"status": "recovered", "plan_id": plan["plan_id"], "restored": len(restores)}
    finally:
        release_lock(lock_path, descriptor)


def apply_task_plan(
    profile_path: Path,
    plan: dict[str, Any],
    *,
    yes: bool,
    _test_after_lock: Callable[[], None] | None = None,
    _test_fail_after_write: int = 0,
) -> dict[str, Any]:
    started = time.perf_counter()
    if not yes:
        raise TaskStateError("Task apply requires explicit --yes")
    verify_plan_identity(plan)
    if plan.get("schema") != PLAN_SCHEMA or plan.get("format_version") != 1:
        raise TaskStateError("Unsupported task plan schema")
    resolved_profile_path, profile = load_profile(profile_path)
    if Path(str(plan.get("profile_path", ""))).resolve() != resolved_profile_path:
        raise TaskStateError("Plan was generated for a different q-profile")
    hub = personal_hub(profile)
    if Path(str(plan.get("hub", ""))).resolve() != hub:
        raise TaskStateError("Plan was generated for a different personal hub")
    if Path(str(plan.get("codex_home", ""))).resolve() != codex_home().resolve():
        raise TaskStateError("Plan was generated for a different CODEX_HOME")

    record = plan.get("record") if isinstance(plan.get("record"), dict) else {}
    errors = validate_task_record(record)
    if record.get("release_state") in {"ready", "released"}:
        binding = flatten_task_record(record)
        errors.extend(
            release_receipt_errors(
                Path(binding.get("release_receipt", "")),
                binding,
                hub,
            )
        )
        errors.extend(live_remote_receipt_errors(profile, binding))
    if errors:
        raise TaskStateError("Plan embeds an invalid task record: " + " | ".join(errors))
    targets = plan.get("targets") if isinstance(plan.get("targets"), dict) else {}
    allowed_paths = _allowed_transaction_paths(resolved_profile_path, plan)
    if not targets:
        raise TaskStateError("Plan has no targets")
    for name, row in targets.items():
        if not isinstance(row, dict):
            raise TaskStateError(f"Invalid target row: {name}")
        target = Path(str(row.get("path", ""))).resolve()
        if target not in allowed_paths:
            raise TaskStateError(f"Plan target escaped the transaction boundary: {target}")
        candidate = decode_bytes(str(row.get("candidate_base64", "")))
        if sha256_bytes(candidate) != row.get("candidate_sha256"):
            raise TaskStateError(f"Candidate hash mismatch in plan target: {name}")

    receipt_path = _transaction_receipt_path(hub, str(plan["plan_id"]))
    lock_path = hub / "personal-state" / ".q-workflow-manager.lock"
    lock_descriptor = acquire_lock(lock_path)
    originals: dict[Path, bytes | None] = {}
    written: list[Path] = []
    journal_path = transaction_journal_path(lock_path)
    journal_originals: dict[str, str | None] = {}
    committed = False
    try:
        if _test_after_lock is not None:
            _test_after_lock()
        if receipt_path.is_file() and _targets_already_applied(targets):
            receipt = read_json_object(receipt_path)
            receipt["idempotent_replay"] = True
            return receipt
        for name, row in targets.items():
            target = Path(str(row["path"]))
            actual = path_hash(target)
            if actual != row.get("expected_sha256"):
                raise TaskStateError(
                    f"CAS mismatch for {name}: expected {row.get('expected_sha256')}, found {actual}"
                )
            journal_originals[name] = encode_bytes(target.read_bytes()) if target.is_file() else None
        if receipt_path.exists():
            raise TaskStateError("Existing receipt does not match applied targets")
        _write_transaction_journal(journal_path, plan, journal_originals)
        for row in targets.values():
            target = Path(str(row["path"]))
            candidate = decode_bytes(str(row["candidate_base64"]))
            originals[target] = target.read_bytes() if target.is_file() else None
            if path_hash(target) == row["candidate_sha256"]:
                continue
            written.append(target)
            atomic_replace_bytes(target, candidate)
            if _test_fail_after_write > 0 and len(written) == _test_fail_after_write:
                raise TaskStateError(f"Injected task transaction failure after write {len(written)}")

        task_path = task_record_path(hub, str(record["task_id"]))
        event_path = task_event_log_path(hub)
        pointer = None
        if plan.get("update_focus") is True:
            active_state = inspect_active_work(hub / "personal-state" / "ACTIVE_WORK.md")
            if active_state["errors"]:
                raise TaskStateError("Written ACTIVE_WORK failed structural readback: " + " ".join(active_state["errors"]))
            pointer = active_state["recovery_pointer"]
        inspection = inspect_task_record(task_path, event_path, pointer=pointer)
        if inspection["status"] != "pass":
            raise TaskStateError("Written task state failed readback: " + " | ".join(inspection["errors"]))
        if plan.get("update_focus") is True:
            runtime_root = codex_home() / "q-personal-state"
            manifest = read_json_object(runtime_root / "runtime-manifest.json")
            manifest_errors = validate_runtime_manifest(manifest, hub / "personal-state", runtime_root)
            if manifest_errors:
                raise TaskStateError("Written runtime manifest failed readback: " + " | ".join(manifest_errors))
        for name, row in targets.items():
            actual = path_hash(Path(str(row["path"])))
            if actual != row["candidate_sha256"]:
                raise TaskStateError(f"Post-write hash mismatch for {name}")

        receipt = {
            "format_version": 1,
            "schema": RECEIPT_SCHEMA,
            "plan_id": plan["plan_id"],
            "task_id": record["task_id"],
            "trace_id": record["trace_id"],
            "applied_at": now_iso(),
            "profile_path": str(resolved_profile_path),
            "hub": str(hub),
            "targets": {
                name: {
                    "path": row["path"],
                    "before_sha256": row["expected_sha256"],
                    "after_sha256": row["candidate_sha256"],
                }
                for name, row in targets.items()
            },
            "validation": "task-record/event/pointer/hash readback passed",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "pushed_or_published": False,
            "idempotent_replay": False,
        }
        receipt_bytes = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _write_transaction_journal(journal_path, plan, journal_originals, _target_row(receipt_path, receipt_bytes))
        originals[receipt_path] = None
        written.append(receipt_path)
        atomic_replace_bytes(receipt_path, receipt_bytes)
        # The data and receipt are complete. An interruption while removing the
        # journal must not begin an unjournaled rollback after unlink succeeds.
        committed = True
        journal_path.unlink()
        return receipt
    except BaseException:
        if committed:
            raise
        for target in reversed(written):
            original = originals.get(target)
            if original is None:
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass
            else:
                atomic_replace_bytes(target, original)
        journal_path.unlink(missing_ok=True)
        raise
    finally:
        release_lock(lock_path, lock_descriptor)


def validate_surface_registry(registry: dict[str, Any], *, label: str = "surface registry") -> None:
    errors: list[str] = []
    if registry.get("format_version") != 1:
        errors.append("format_version must equal 1")
    roots = registry.get("roots")
    if not isinstance(roots, dict) or not roots:
        errors.append("roots must be a nonempty object")
        roots = {}
    missing_roots = sorted(REQUIRED_SURFACE_ROOTS - set(roots))
    if missing_roots:
        errors.append("missing required roots: " + ", ".join(missing_roots))
    for name, row in roots.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(row, dict):
            errors.append(f"invalid root row: {name!r}")
            continue
        resolver = row.get("resolver")
        if resolver not in SURFACE_RESOLVERS:
            errors.append(f"root {name!r} has invalid resolver={resolver!r}")
        relative = row.get("relative")
        if not isinstance(relative, str) or not relative.strip():
            errors.append(f"root {name!r} requires a relative path")
        else:
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                errors.append(f"root {name!r} relative path must remain inside its resolver")
        if resolver == "profile-repository" and not isinstance(row.get("repository"), str):
            errors.append(f"root {name!r} requires a repository id")
        if not isinstance(row.get("authority"), str) or not str(row.get("authority", "")).strip():
            errors.append(f"root {name!r} requires an authority label")

    skills = registry.get("skills")
    if not isinstance(skills, list) or not skills:
        errors.append("skills must be a nonempty list")
        skills = []
    seen_ids: set[str] = set()
    core_ids: set[str] = set()
    for index, skill in enumerate(skills, start=1):
        prefix = f"skill row {index}"
        if not isinstance(skill, dict):
            errors.append(f"{prefix} must be an object")
            continue
        skill_id = skill.get("id")
        if not isinstance(skill_id, str) or not TASK_ID_RE.fullmatch(skill_id):
            errors.append(f"{prefix} has an invalid id")
            continue
        if skill_id in seen_ids:
            errors.append(f"duplicate skill id={skill_id!r}")
        seen_ids.add(skill_id)
        tier = skill.get("tier")
        if tier not in SURFACE_TIERS:
            errors.append(f"skill {skill_id!r} has invalid tier={tier!r}")
        elif tier == "core":
            core_ids.add(skill_id)
        if not isinstance(skill.get("category"), str) or not str(skill.get("category", "")).strip():
            errors.append(f"skill {skill_id!r} requires a category")
        expected = skill.get("expected_surfaces")
        if (
            not isinstance(expected, list)
            or not expected
            or any(not isinstance(value, str) or value not in roots for value in expected)
            or len(set(expected)) != len(expected)
        ):
            errors.append(f"skill {skill_id!r} has invalid expected_surfaces")
            expected = []
        canonical = skill.get("canonical_surface")
        if not isinstance(canonical, str) or canonical not in expected:
            errors.append(f"skill {skill_id!r} canonical_surface must be one expected surface")
    missing_core = sorted(REQUIRED_CORE_SKILLS - core_ids)
    if missing_core:
        errors.append("missing required core skills: " + ", ".join(missing_core))
    ignore = registry.get("ignore")
    if not isinstance(ignore, dict):
        errors.append("ignore must be an object")
    else:
        ignored_directories = ignore.get("directories")
        if (
            not isinstance(ignored_directories, list)
            or any(not isinstance(value, str) for value in ignored_directories)
            or len(set(ignored_directories)) != len(ignored_directories)
            or set(ignored_directories) != APPROVED_IGNORED_DIRECTORIES
        ):
            errors.append(
                "ignore.directories must exactly match the approved transient-directory allowlist"
            )
        ignored_suffixes = ignore.get("suffixes")
        if (
            not isinstance(ignored_suffixes, list)
            or any(not isinstance(value, str) for value in ignored_suffixes)
            or len(set(ignored_suffixes)) != len(ignored_suffixes)
            or set(ignored_suffixes) != APPROVED_IGNORED_SUFFIXES
        ):
            errors.append(
                "ignore.suffixes must exactly match the approved compiled-cache allowlist"
            )
    if errors:
        raise TaskStateError(f"Malformed {label}: " + " | ".join(errors))


def load_surface_registry(path: Path | None = None) -> dict[str, Any]:
    registry_path = path or Path(__file__).resolve().parents[1] / "references" / "surface-registry.json"
    registry = read_json_object(registry_path)
    validate_surface_registry(registry, label=str(registry_path))
    return registry


def resolve_surface_roots(profile: dict[str, Any], registry: dict[str, Any]) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    repositories = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    hub = personal_hub(profile)
    for name, row in registry["roots"].items():
        if not isinstance(row, dict):
            raise TaskStateError(f"Invalid surface root row: {name}")
        resolver = row.get("resolver")
        relative = Path(str(row.get("relative", "")))
        if resolver == "profile-repository":
            repository = repositories.get(row.get("repository"))
            if not isinstance(repository, dict):
                raise TaskStateError(f"q-profile lacks repository {row.get('repository')}")
            raw = repository.get("path") or repository.get("registry_path") or repository.get("local_path")
            if not isinstance(raw, str) or not raw:
                raise TaskStateError(f"Repository path is missing for {row.get('repository')}")
            root = Path(raw).expanduser() / relative
        elif resolver == "personal-hub":
            root = hub / relative
        elif resolver == "codex-home":
            root = codex_home() / relative
        else:
            raise TaskStateError(f"Unknown surface resolver: {resolver}")
        roots[name] = root.resolve()
    return roots


def tree_hashes(root: Path, registry: dict[str, Any]) -> dict[str, str]:
    ignore = registry.get("ignore") if isinstance(registry.get("ignore"), dict) else {}
    ignored_dirs = set(ignore.get("directories", []))
    ignored_suffixes = set(ignore.get("suffixes", []))
    if not root.is_dir():
        return {}
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in ignored_dirs for part in relative.parts):
            continue
        if path.suffix in ignored_suffixes:
            continue
        values[relative.as_posix()] = sha256_file(path)
    return values


def manifest_digest(values: dict[str, str]) -> str:
    payload = "".join(f"{path}\0{value}\n" for path, value in sorted(values.items())).encode("utf-8")
    return sha256_bytes(payload)


def surface_report(
    profile: dict[str, Any],
    registry: dict[str, Any],
    *,
    tier: str = "all",
) -> dict[str, Any]:
    validate_surface_registry(registry)
    roots = resolve_surface_roots(profile, registry)
    resolved_to_name: dict[Path, str] = {}
    duplicate_roots: list[dict[str, str]] = []
    for name, path in roots.items():
        if path in resolved_to_name:
            duplicate_roots.append({"root": name, "duplicate_of": resolved_to_name[path], "path": str(path)})
        else:
            resolved_to_name[path] = name
    rows: list[dict[str, Any]] = []
    registered: set[str] = set()
    for skill in registry["skills"]:
        if not isinstance(skill, dict):
            continue
        if tier != "all" and skill.get("tier") != tier:
            continue
        skill_id = str(skill.get("id", ""))
        registered.add(skill_id)
        surfaces: dict[str, Any] = {}
        hashes_by_surface: dict[str, dict[str, str]] = {}
        for surface in skill.get("expected_surfaces", []):
            root = roots.get(surface)
            if root is None:
                surfaces[surface] = {"status": "missing-root", "path": "", "file_count": 0, "digest": ""}
                continue
            path = root / skill_id
            hashes = tree_hashes(path, registry)
            hashes_by_surface[surface] = hashes
            surfaces[surface] = {
                "status": "present" if path.is_dir() else "missing",
                "path": str(path),
                "file_count": len(hashes),
                "digest": manifest_digest(hashes) if path.is_dir() else "",
            }
        canonical_surface = str(skill.get("canonical_surface", ""))
        canonical = hashes_by_surface.get(canonical_surface, {})
        differences: list[dict[str, Any]] = []
        for surface, values in hashes_by_surface.items():
            if surface == canonical_surface:
                continue
            all_files = sorted(set(canonical) | set(values))
            drift = [path for path in all_files if canonical.get(path) != values.get(path)]
            if drift:
                differences.append({"surface": surface, "count": len(drift), "preview": drift[:8]})
        missing = [name for name, row in surfaces.items() if row["status"] != "present"]
        status = "missing" if missing else "drift" if differences else "pass"
        rows.append(
            {
                "skill_id": skill_id,
                "tier": skill.get("tier"),
                "canonical_surface": canonical_surface,
                "status": status,
                "missing_surfaces": missing,
                "differences": differences,
                "surfaces": surfaces,
            }
        )

    unregistered: dict[str, list[str]] = {}
    if tier == "all":
        registered = {str(skill.get("id")) for skill in registry["skills"] if isinstance(skill, dict)}
        for name, root in roots.items():
            if not root.is_dir():
                continue
            extras = sorted(
                path.name
                for path in root.iterdir()
                if path.is_dir() and path.name.startswith("q-") and (path / "SKILL.md").is_file() and path.name not in registered
            )
            if extras:
                unregistered[name] = extras
    failures = sum(row["status"] != "pass" for row in rows) + len(duplicate_roots) + sum(len(v) for v in unregistered.values())
    return {
        "format_version": 1,
        "checked_at": now_iso(),
        "tier": tier,
        "roots": {name: str(path) for name, path in roots.items()},
        "duplicate_roots": duplicate_roots,
        "skills": rows,
        "unregistered": unregistered,
        "summary": {"skills": len(rows), "failures": failures, "status": "pass" if failures == 0 else "attention"},
    }


def run_probe(
    name: str,
    command: list[str],
    *,
    timeout: int = DEFAULT_COMMAND_TIMEOUT_SECONDS,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=env,
        )
        output = (completed.stdout or completed.stderr).strip()
        try:
            payload: Any = json.loads(output)
        except json.JSONDecodeError:
            payload = None
            for line in reversed(output.splitlines()):
                candidate = line.strip()
                if not candidate.startswith("{"):
                    continue
                try:
                    payload = json.loads(candidate)
                    break
                except json.JSONDecodeError:
                    continue
        return {
            "name": name,
            "status": "pass" if completed.returncode == 0 else "blocked",
            "failure_class": None if completed.returncode == 0 else "nonzero-exit",
            "returncode": completed.returncode,
            "payload": payload,
            "output": output[-6000:],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "status": "blocked",
            "failure_class": "timeout",
            "returncode": 124,
            "payload": None,
            "output": f"timeout after {exc.timeout}s",
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }
    except OSError as exc:
        return {
            "name": name,
            "status": "blocked",
            "failure_class": "spawn-error",
            "returncode": 127,
            "payload": None,
            "output": str(exc),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        }


def doctor_report(profile_path: Path, *, full: bool, rounds: int) -> dict[str, Any]:
    profile_path, profile = load_profile(profile_path)
    probe_env = os.environ.copy()
    probe_env["Q_PROFILE_PATH"] = str(profile_path)
    root = Path(__file__).resolve().parents[1]
    skills_root = root.parent
    probes = [
        run_probe("workflow-audit", [sys.executable, str(root / "scripts" / "workflow_audit.py"), "--mode", "audit", "--strict", "--format", "json"], env=probe_env),
        run_probe("lifecycle", [sys.executable, str(root / "scripts" / "workflow_lifecycle.py"), "--strict", "--format", "json"], env=probe_env),
        run_probe("q-standard", [sys.executable, str(root / "scripts" / "q_standard_check.py"), "--self-test"], env=probe_env),
        run_probe("role-plan", [sys.executable, str(skills_root / "q-agent-roster" / "scripts" / "task_role_plan.py"), "--self-test"], env=probe_env),
        run_probe("portfolio", [sys.executable, str(skills_root / "q-skill-creation" / "scripts" / "skill_portfolio_audit.py"), "--fail-on-blocker"], env=probe_env),
    ]
    surface_started = time.perf_counter()
    surfaces = surface_report(profile, load_surface_registry(), tier="core")
    surface_elapsed = round((time.perf_counter() - surface_started) * 1000, 3)
    if surfaces["summary"]["status"] != "pass":
        probes.append({"name": "core-surfaces", "status": "blocked", "failure_class": "surface-drift", "returncode": 1, "payload": surfaces, "output": "", "elapsed_ms": surface_elapsed})
    else:
        probes.append({"name": "core-surfaces", "status": "pass", "failure_class": None, "returncode": 0, "payload": surfaces, "output": "", "elapsed_ms": surface_elapsed})
    tasks_started = time.perf_counter()
    tasks = task_list_report(profile_path)
    tasks_ok = tasks["summary"]["status"] == "pass"
    probes.append(
        {
            "name": "registered-tasks",
            "status": "pass" if tasks_ok else "blocked",
            "failure_class": None if tasks_ok else "task-registry-invalid",
            "returncode": 0 if tasks_ok else 1,
            "payload": tasks,
            "output": "",
            "elapsed_ms": round((time.perf_counter() - tasks_started) * 1000, 3),
        }
    )
    if full:
        probes.append(
            run_probe(
                "foundational-stability",
                [
                    sys.executable,
                    str(root / "scripts" / "workflow_stability_suite.py"),
                    "--rounds",
                    str(rounds),
                    "--check-only",
                    "--strict",
                    "--stdout",
                ],
                timeout=max(300, rounds * 180),
                env=probe_env,
            )
        )
    failures = [probe["name"] for probe in probes if probe["status"] != "pass"]
    return {
        "format_version": 1,
        "checked_at": now_iso(),
        "profile_path": str(profile_path),
        "scope": "full" if full else "quick",
        "status": "pass" if not failures else "blocked",
        "failures": failures,
        "probes": probes,
    }


def status_report(profile_path: Path) -> dict[str, Any]:
    profile_path, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    active_path = hub / "personal-state" / "ACTIVE_WORK.md"
    active = inspect_active_work(active_path)
    tasks_root = hub / "personal-state" / "tasks"
    current_task: dict[str, Any] | None = None
    pointer = active.get("recovery_pointer", {})
    focus_task_id = pointer.get("task_id") if isinstance(pointer, dict) else None
    managed_pointer = isinstance(pointer, dict) and (
        pointer.get("schema") == "q-workflow-focus-v2" or bool(pointer.get("task_record_path"))
    )
    latch_errors: list[str] = []
    if managed_pointer:
        expected_latch = (
            "phase-b-required"
            if pointer.get("work_state") in {"active", "validating", "blocked"}
            else "not-required"
        )
        if pointer.get("visibility_latch") != expected_latch:
            latch_errors.append(
                f"managed focus visibility_latch={pointer.get('visibility_latch')!r}; expected {expected_latch!r}"
            )
    if managed_pointer and focus_task_id:
        try:
            if pointer.get("task_record_path"):
                record_path = resolve_task_record(hub, record_path=Path(pointer["task_record_path"]))
            else:
                record_path = task_record_path(hub, str(focus_task_id))
            current_task = inspect_task_record(record_path, task_event_log_path(hub), pointer=pointer)
        except TaskStateError as exc:
            current_task = {"status": "blocked", "errors": [str(exc)]}
    if latch_errors:
        if current_task is None:
            current_task = {"status": "blocked", "errors": []}
        current_task["status"] = "blocked"
        current_task.setdefault("errors", []).extend(latch_errors)
    surfaces = surface_report(profile, load_surface_registry(), tier="core")
    status = "pass"
    if active.get("errors") or (current_task and current_task.get("status") != "pass"):
        status = "blocked"
    elif surfaces["summary"]["status"] != "pass":
        status = "attention"
    return {
        "format_version": 1,
        "checked_at": now_iso(),
        "status": status,
        "profile_path": str(profile_path),
        "hub": str(hub),
        "active": active,
        "current_task": current_task,
        "task_count": len(list(tasks_root.glob("*.json"))) if tasks_root.is_dir() else 0,
        "core_surfaces": surfaces["summary"],
        "remote_status": "unproven",
    }


def task_list_report(profile_path: Path, *, work_state: str | None = None) -> dict[str, Any]:
    profile_path, profile = load_profile(profile_path)
    hub = personal_hub(profile)
    tasks_root = hub / "personal-state" / "tasks"
    event_log = task_event_log_path(hub)
    active = inspect_active_work(hub / "personal-state" / "ACTIVE_WORK.md")
    pointer = active.get("recovery_pointer", {}) if isinstance(active.get("recovery_pointer"), dict) else {}
    focus_task_id = pointer.get("task_id")
    rows: list[dict[str, Any]] = []
    rows_by_task_id: dict[str, list[dict[str, Any]]] = {}
    registered_task_ids: set[str] = set()
    if tasks_root.is_dir():
        for record_path in sorted(tasks_root.glob("*.json")):
            inspection = inspect_task_record(
                record_path,
                event_log,
                pointer=pointer if record_path.stem == focus_task_id else None,
            )
            record = inspection.get("record") if isinstance(inspection.get("record"), dict) else {}
            if isinstance(record.get("task_id"), str):
                registered_task_ids.add(record["task_id"])
            if work_state and record.get("work_state") != work_state:
                continue
            row = {
                "focus": record.get("task_id") == focus_task_id,
                "task_id": record.get("task_id", record_path.stem),
                "trace_id": record.get("trace_id"),
                "work_state": record.get("work_state"),
                "integrity_state": record.get("integrity_state"),
                "release_state": record.get("release_state"),
                "updated_at": record.get("updated_at"),
                "next_action": record.get("next_action"),
                "status": inspection.get("status"),
                "errors": list(inspection.get("errors", [])),
                "record_path": str(record_path),
            }
            rows.append(row)
            row_task_id = row.get("task_id")
            if isinstance(row_task_id, str) and row_task_id:
                rows_by_task_id.setdefault(row_task_id, []).append(row)
    for task_id, matches in rows_by_task_id.items():
        if len(matches) <= 1:
            continue
        duplicate_error = f"duplicate task_id={task_id!r} appears in {len(matches)} registry files"
        for row in matches:
            row["errors"].append(duplicate_error)
            row["status"] = "blocked"
    failures = sum(row["status"] != "pass" for row in rows)
    managed_pointer = isinstance(pointer, dict) and (
        pointer.get("schema") == "q-workflow-focus-v2" or bool(pointer.get("task_record_path"))
    )
    focus_errors: list[str] = []
    if managed_pointer and focus_task_id and focus_task_id not in registered_task_ids:
        focus_errors.append(
            f"managed focus task_id={focus_task_id!r} has no canonical task record under personal-state/tasks"
        )
    if managed_pointer:
        expected_latch = (
            "phase-b-required"
            if pointer.get("work_state") in {"active", "validating", "blocked"}
            else "not-required"
        )
        if pointer.get("visibility_latch") != expected_latch:
            focus_errors.append(
                f"managed focus visibility_latch={pointer.get('visibility_latch')!r}; expected {expected_latch!r}"
            )
    return {
        "format_version": 1,
        "checked_at": now_iso(),
        "profile_path": str(profile_path),
        "hub": str(hub),
        "focus_task_id": focus_task_id,
        "filter": {"work_state": work_state},
        "tasks": rows,
        "focus_errors": focus_errors,
        "summary": {
            "count": len(rows),
            "failures": failures + len(focus_errors),
            "status": "pass" if failures == 0 and not focus_errors and not active.get("errors") else "attention",
        },
    }


def self_test() -> dict[str, Any]:
    failures: list[str] = []
    cases = 0
    with tempfile.TemporaryDirectory() as temp_raw:
        temp = Path(temp_raw)
        hub = temp / "personal-hub"
        state = hub / "personal-state"
        runtime = temp / "codex" / "q-personal-state"
        source_repo = temp / "workflow-hub"
        state.mkdir(parents=True)
        runtime.mkdir(parents=True)
        (source_repo / "skills").mkdir(parents=True)
        focus_fixture = (
            "Legacy focus.\n\n- preserve first bullet\n- preserve second bullet\n\n"
            "```powershell\nWrite-Output 'preserve fenced command'\n```"
        )
        active_text = (
            f"# Active Work\n\n## Current Focus\n\n{focus_fixture}\n\n"
            "## RECOVERY_POINTER v1\n\ntask_id: legacy\n\n## Recovery Rules\n\n1. Preserve.\n"
        )
        active_source = state / "ACTIVE_WORK.md"
        active_runtime = runtime / "ACTIVE_WORK.md"
        active_source.write_text(active_text, encoding="utf-8")
        active_runtime.write_text(active_text, encoding="utf-8")
        todo_text = "# TODO\n\n## Open\n\n- [ ] 2026-08-09 | manager-self-test | Verify the manager transaction.\n\n## Closed\n"
        display_text = "{}\n"
        (state / "TODO.md").write_text(todo_text, encoding="utf-8")
        (runtime / "TODO.md").write_text(todo_text, encoding="utf-8")
        (state / "TODO_DISPLAY.zh-CN.json").write_text(display_text, encoding="utf-8")
        (runtime / "TODO_DISPLAY.zh-CN.json").write_text(display_text, encoding="utf-8")
        profile = temp / "q-profile.json"
        profile.write_text(
            json.dumps(
                {
                    "hub": str(hub),
                    "repositories": {
                        "q-workflow-hub": {
                            "path": str(source_repo),
                            "remote": "https://example.invalid/q-workflow.git",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        previous_home = os.environ.get("CODEX_HOME")
        os.environ["CODEX_HOME"] = str(temp / "codex")
        try:
            dangling_text = (
                "# Active Work\n\n## Current Focus\n\nManaged but missing.\n\n"
                "## RECOVERY_POINTER v2\n\nschema: q-workflow-focus-v2\n"
                "task_id: missing-managed-task\nwork_state: active\n"
                "visibility_latch: phase-b-required\n\n## Recovery Rules\n\n1. Preserve.\n"
            )
            active_source.write_text(dangling_text, encoding="utf-8")
            active_runtime.write_text(dangling_text, encoding="utf-8")
            dangling_status = status_report(profile)
            dangling_list = task_list_report(profile)
            if (
                dangling_status.get("status") != "blocked"
                or (dangling_status.get("current_task") or {}).get("status") != "blocked"
                or dangling_list.get("summary", {}).get("status") != "attention"
                or not dangling_list.get("focus_errors")
            ):
                failures.append("managed dangling focus pointer did not fail closed")
            active_source.write_text(active_text, encoding="utf-8")
            active_runtime.write_text(active_text, encoding="utf-8")
            cases += 1

            missing_latch_text = dangling_text.replace("visibility_latch: phase-b-required\n", "")
            active_source.write_text(missing_latch_text, encoding="utf-8")
            active_runtime.write_text(missing_latch_text, encoding="utf-8")
            missing_latch_status = status_report(profile)
            if not any(
                "visibility_latch" in error
                for error in (missing_latch_status.get("current_task") or {}).get("errors", [])
            ):
                failures.append("managed Phase B focus without visibility latch did not fail closed")
            active_source.write_text(active_text, encoding="utf-8")
            active_runtime.write_text(active_text, encoding="utf-8")
            cases += 1

            record = {
                "format_version": 1,
                "schema": TASK_SCHEMA,
                "task_id": "manager-self-test",
                "trace_id": "MANAGER-SELF-TEST",
                "execution_epoch": 1,
                "state_revision": "manager-self-test-r1",
                "authority_event": "manager-self-test-register-r1",
                "work_state": "briefing",
                "integrity_state": "local-validated",
                "release_state": "local-only",
                "role_plan": {
                    "id": "manager-self-test-role-plan",
                    "primary": {"owner": "main", "status": "planned"},
                    "reviewer": {"owner": "reviewer", "status": "pending"},
                    "validator": {"owner": "validator", "status": "pending"},
                },
                "remote": {"status": "unproven", "proven": False},
                "next_action": "Complete the isolated manager self-test.",
                "updated_at": "2026-08-09T20:00:00+08:00",
                "focus": {"summary": "Manager self-test."},
                "detail": {
                    "domain_work_state": "isolated-fixture",
                    "recovery_rules": ["Resume only the manager self-test."],
                    "non_executable_index": ["Legacy task guidance is historical only."],
                },
            }
            cases += 1
            try:
                current_focus_text_for_record(profile, record)
                failures.append("focus-current allowed a cross-task pointer/prose mix")
            except TaskStateError as exc:
                if "cannot switch task identity" not in str(exc):
                    failures.append(f"focus-current cross-task block returned the wrong error: {exc}")
            cases += 1
            plan = build_task_plan(profile, record, focus_text=focus_fixture)
            if active_source.read_text(encoding="utf-8") != active_text:
                failures.append("plan mutated ACTIVE_WORK")
            cases += 1
            receipt = apply_task_plan(profile, plan, yes=True)
            if receipt.get("validation") != "task-record/event/pointer/hash readback passed":
                failures.append("apply did not return a validated receipt")
            if inspect_active_work(active_source).get("current_focus_text") != focus_fixture:
                failures.append("focus-current preservation flattened Markdown structure")
            switched_text = active_source.read_text(encoding="utf-8")
            if "1. Preserve." in switched_text or "1. Resume only the manager self-test." not in switched_text:
                failures.append("cross-task switch retained stale Recovery Rules")
            if "- Legacy task guidance is historical only." not in switched_text:
                failures.append("cross-task switch did not install the candidate Non-Executable Index")
            cases += 1
            if current_focus_text_for_record(profile, record) != focus_fixture:
                failures.append("focus-current did not preserve prose for the task that already owns focus")
            cases += 1
            task_path = task_record_path(hub, record["task_id"])
            inspection = inspect_task_record(
                task_path,
                task_event_log_path(hub),
                pointer=inspect_active_work(active_source)["recovery_pointer"],
            )
            if inspection["status"] != "pass":
                failures.append("applied state failed independent inspection")
            cases += 1
            replay = apply_task_plan(profile, plan, yes=True)
            if replay.get("idempotent_replay") is not True:
                failures.append("identical plan replay was not idempotent")
            cases += 1

            background = json.loads(json.dumps(record))
            background.update(
                task_id="manager-background-task",
                trace_id="MANAGER-BACKGROUND-TEST",
                state_revision="manager-background-r1",
                authority_event="manager-background-register-r1",
                updated_at="2026-08-09T20:00:30+08:00",
            )
            background["role_plan"]["id"] = "manager-background-role-plan"
            background["focus"]["summary"] = "Background task remains independently inspectable."
            focus_before_background = active_source.read_bytes()
            background_plan = build_task_plan(profile, background, focus_text=None)
            apply_task_plan(profile, background_plan, yes=True)
            background_check = inspect_task_record(
                task_record_path(hub, background["task_id"]),
                task_event_log_path(hub),
            )
            if background_check["status"] != "pass" or active_source.read_bytes() != focus_before_background:
                failures.append("background task registration changed focus or failed inspection")
            cases += 1

            alias_path = task_path.with_name("manager-self-test-alias.json")
            alias_path.write_bytes(task_path.read_bytes())
            alias_report = task_list_report(profile)
            alias_errors = [
                error
                for row in alias_report.get("tasks", [])
                for error in row.get("errors", [])
            ]
            if (
                alias_report.get("summary", {}).get("status") != "attention"
                or not any("filename" in error for error in alias_errors)
                or not any("duplicate task_id" in error for error in alias_errors)
            ):
                failures.append("task registry accepted a filename/task_id alias or duplicate task id")
            alias_path.unlink()
            cases += 1

            record_a = json.loads(json.dumps(record))
            record_a.update(
                state_revision="manager-self-test-lock-a",
                authority_event="manager-self-test-lock-a",
                updated_at="2026-08-09T20:01:00+08:00",
            )
            record_b = json.loads(json.dumps(record_a))
            record_b.update(
                state_revision="manager-self-test-lock-b",
                authority_event="manager-self-test-lock-b",
                updated_at="2026-08-09T20:01:01+08:00",
            )
            plan_a = build_task_plan(profile, record_a, focus_text=None)
            plan_b = build_task_plan(profile, record_b, focus_text=None)
            competing_blocked = False
            def attempt_competing_apply() -> None:
                nonlocal competing_blocked
                try:
                    apply_task_plan(profile, plan_b, yes=True)
                except (TaskStateError, WorkflowFileLockError) as exc:
                    competing_blocked = "holds" in str(exc)
            apply_task_plan(profile, plan_a, yes=True, _test_after_lock=attempt_competing_apply)
            final_after_lock = read_json_object(task_record_path(hub, record["task_id"]))
            if not competing_blocked or final_after_lock.get("state_revision") != record_a["state_revision"]:
                failures.append("competing plan was not blocked before locked CAS")
            cases += 1

            rollback_record = json.loads(json.dumps(record_a))
            rollback_record.update(
                state_revision="manager-self-test-rollback",
                authority_event="manager-self-test-rollback",
                updated_at="2026-08-09T20:01:30+08:00",
            )
            rollback_plan = build_task_plan(profile, rollback_record, focus_text=None)
            rollback_before = {
                name: path_hash(Path(row["path"]))
                for name, row in rollback_plan["targets"].items()
            }
            try:
                apply_task_plan(profile, rollback_plan, yes=True, _test_fail_after_write=1)
                failures.append("injected task transaction failure was accepted")
            except TaskStateError as exc:
                if "Injected" not in str(exc):
                    failures.append(f"rollback injection failed for the wrong reason: {exc}")
            rollback_after = {
                name: path_hash(Path(row["path"]))
                for name, row in rollback_plan["targets"].items()
            }
            if rollback_after != rollback_before:
                failures.append("injected task transaction failure did not restore every target")
            cases += 1

            record2 = json.loads(json.dumps(record_a))
            record2["state_revision"] = "manager-self-test-r2"
            record2["authority_event"] = "manager-self-test-update-r2"
            record2["updated_at"] = "2026-08-09T20:02:00+08:00"
            plan2 = build_task_plan(profile, record2, focus_text="Manager self-test focus r2.")
            active_before_cas = active_source.read_bytes()
            active_source.write_bytes(active_before_cas + b"\n")
            try:
                apply_task_plan(profile, plan2, yes=True)
                failures.append("CAS drift was accepted")
            except TaskStateError as exc:
                if "CAS mismatch" not in str(exc):
                    failures.append(f"CAS drift failed for the wrong reason: {exc}")
            active_source.write_bytes(active_before_cas)
            cases += 1
            doctor = doctor_report(profile, full=False, rounds=1)
            audit_probe = next((row for row in doctor.get("probes", []) if row.get("name") == "workflow-audit"), {})
            audit_inventory = audit_probe.get("payload", {}).get("inventory", {}) if isinstance(audit_probe.get("payload"), dict) else {}
            if (
                Path(str(audit_inventory.get("profile", ""))).resolve() != profile.resolve()
                or Path(str(audit_inventory.get("hub", ""))).resolve() != hub.resolve()
            ):
                failures.append("doctor probes ignored the explicitly requested profile")
            cases += 1
            left = temp / "left"
            right = temp / "right"
            left.mkdir()
            right.mkdir()
            (left / "a.txt").write_text("same", encoding="utf-8")
            (right / "a.txt").write_text("same", encoding="utf-8")
            registry = load_surface_registry()
            if manifest_digest(tree_hashes(left, registry)) != manifest_digest(tree_hashes(right, registry)):
                failures.append("identical surface manifests differed")
            (right / "a.txt").write_text("changed", encoding="utf-8")
            if manifest_digest(tree_hashes(left, registry)) == manifest_digest(tree_hashes(right, registry)):
                failures.append("surface manifest drift was missed")
            truncated_registry = {"format_version": 1, "roots": {}, "skills": []}
            try:
                surface_report({}, truncated_registry, tier="core")
                failures.append("truncated surface registry failed open")
            except TaskStateError:
                pass
            cases += 1
            invalid_canonical = json.loads(json.dumps(registry))
            invalid_canonical["skills"][0]["expected_surfaces"] = ["bootstrap", "runtime"]
            try:
                validate_surface_registry(invalid_canonical)
                failures.append("surface registry accepted a canonical surface outside expected_surfaces")
            except TaskStateError:
                pass
            cases += 1
            invalid_ignore = json.loads(json.dumps(registry))
            invalid_ignore["ignore"]["directories"] = ["scripts"]
            invalid_ignore["ignore"]["suffixes"] = [".py"]
            try:
                validate_surface_registry(invalid_ignore)
                failures.append("surface registry accepted managed code in its ignore policy")
            except TaskStateError:
                pass
            cases += 1
            remote_ref = "refs/heads/main"
            remote_oid = "a" * 40
            parsed_oid, parse_error = _remote_ref_oid(f"{remote_oid}\t{remote_ref}\n", remote_ref)
            if parse_error or parsed_oid != remote_oid:
                failures.append("live remote ref parser rejected one exact ref")
            if _remote_ref_oid(f"{remote_oid}\trefs/heads/other\n", remote_ref)[1] is None:
                failures.append("live remote ref parser accepted a missing bound ref")
            cases += 1
            untrusted_remote_errors = live_remote_receipt_errors(
                load_profile(profile)[1],
                {
                    "release_remote": ".",
                    "release_branch": "main",
                    "release_target_oid": remote_oid,
                },
            )
            if not any("configured URL" in error for error in untrusted_remote_errors):
                failures.append("live remote verification accepted an unconfigured local target")
            cases += 1
        finally:
            if previous_home is None:
                os.environ.pop("CODEX_HOME", None)
            else:
                os.environ["CODEX_HOME"] = previous_home
    return {"status": "pass" if not failures else "blocked", "cases": cases, "failures": failures}


def render_text(payload: dict[str, Any]) -> str:
    if payload.get("schema") == "q-workflow-surface-registry-validation-v1":
        return (
            f"q-workflow registry: {payload['status']} "
            f"roots={payload['roots']} skills={payload['skills']} core={payload['core_skills']}"
        )
    if "probes" in payload:
        lines = [f"q-workflow doctor: {payload['status']} ({payload['scope']})"]
        for probe in payload["probes"]:
            evidence = ""
            probe_payload = probe.get("payload") if isinstance(probe.get("payload"), dict) else {}
            if isinstance(probe_payload.get("checks"), int):
                evidence = f" checks={probe_payload['checks']} failures={probe_payload.get('failures')}"
            lines.append(f"- {probe['name']}: {probe['status']}{evidence} ({probe.get('elapsed_ms', 0)} ms)")
        if payload.get("failures"):
            lines.append("repair: " + ", ".join(payload["failures"]))
        return "\n".join(lines)
    if "skills" in payload and "summary" in payload:
        lines = [f"q-workflow surfaces: {payload['summary']['status']} skills={payload['summary']['skills']} failures={payload['summary']['failures']}"]
        for row in payload["skills"]:
            lines.append(f"- {row['skill_id']}: {row['status']}")
        if payload["summary"]["status"] != "pass":
            lines.append("advisory: inspect JSON details; use --strict when drift must fail the command.")
        return "\n".join(lines)
    if "tasks" in payload and "summary" in payload:
        lines = [f"q-workflow tasks: {payload['summary']['status']} count={payload['summary']['count']} failures={payload['summary']['failures']}"]
        for error in payload.get("focus_errors", []):
            lines.append(f"focus error: {error}")
        for row in payload["tasks"]:
            marker = "*" if row.get("focus") else "-"
            lines.append(
                f"{marker} {row.get('task_id')} | {row.get('work_state')}/{row.get('integrity_state')}/{row.get('release_state')} | {row.get('updated_at')}"
            )
            lines.append(f"  trace: {row.get('trace_id')} | validation: {row.get('status')}")
        return "\n".join(lines)
    if "active" in payload and "core_surfaces" in payload:
        active = payload["active"]
        pointer = active.get("recovery_pointer", {}) if isinstance(active, dict) else {}
        lines = [
            f"q-workflow status: {payload['status']}",
            f"hub: {payload['hub']}",
            f"focus task: {pointer.get('task_id', 'none')}",
            f"registered tasks: {payload['task_count']}",
            f"visibility latch: {pointer.get('visibility_latch', 'missing')}",
            f"core surfaces: {payload['core_surfaces']['status']}",
            "remote: unproven",
        ]
        current_task = payload.get("current_task")
        if isinstance(current_task, dict) and current_task.get("status") != "pass":
            lines.append("focus binding: blocked")
            lines.extend(f"- {error}" for error in current_task.get("errors", [])[:4])
        return "\n".join(lines)
    if "record_path" in payload and "record" in payload:
        record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
        lines = [
            f"q-workflow task: {payload.get('status')} {record.get('task_id', 'unresolved')}",
            f"trace: {record.get('trace_id', 'unknown')}",
            f"state: {record.get('work_state', 'unknown')}/{record.get('integrity_state', 'unknown')}/{record.get('release_state', 'unknown')}",
            f"record: {payload.get('record_path')}",
            f"event log: {payload.get('event_log', 'unknown')}",
            f"errors: {len(payload.get('errors', []))}",
        ]
        lines.extend(f"- {error}" for error in payload.get("errors", [])[:8])
        return "\n".join(lines)
    if payload.get("status") == "planned":
        return "\n".join(
            [
                f"q-workflow task plan: ready {payload.get('task_id')}",
                f"plan: {payload.get('plan_path')}",
                f"plan id: {payload.get('plan_id')}",
                f"focus update: {payload.get('update_focus')}",
                f"targets: {len(payload.get('targets', {}))}",
                str(payload.get("next_action", "Review and explicitly apply the plan.")),
            ]
        )
    if payload.get("status") == "applied" and isinstance(payload.get("receipt"), dict):
        receipt = payload["receipt"]
        return "\n".join(
            [
                f"q-workflow task apply: pass {receipt.get('task_id')}",
                f"plan id: {receipt.get('plan_id')}",
                f"targets: {len(receipt.get('targets', {}))}",
                f"validation: {receipt.get('validation')}",
                f"elapsed_ms: {receipt.get('elapsed_ms', 'n/a')}",
            ]
        )
    if payload.get("status") == "blocked" and payload.get("error"):
        return f"q-workflow: blocked\nfailure: {payload['error']}\nrepair: review the command help or authoritative state, then retry."
    return json.dumps(payload, ensure_ascii=False, indent=2)


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=default_profile_path())
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true")
    subcommands = parser.add_subparsers(dest="command")

    subcommands.add_parser("status", help="Show authority, focus, task, and core-surface status.")
    doctor = subcommands.add_parser("doctor", help="Run the unified workflow health probes.")
    doctor.add_argument("--full", action="store_true", help="Also run the foundational stability suite.")
    doctor.add_argument("--rounds", type=positive_int, default=2, help="Positive stability-suite round count (default: 2).")
    surfaces = subcommands.add_parser("surfaces", help="Compare registered source/bootstrap/runtime manifests.")
    surfaces.add_argument("--tier", choices=("core", "flagship", "lab", "all"), default="all")
    surfaces.add_argument("--registry", type=Path)
    surfaces.add_argument("--strict", action="store_true", help="Exit non-zero when a registered surface is missing or has drift.")

    registry_parser = subcommands.add_parser("registry", help="Validate the managed-surface registry contract.")
    registry_commands = registry_parser.add_subparsers(dest="registry_command", required=True)
    registry_validate = registry_commands.add_parser("validate", help="Validate registry structure and the required core baseline without syncing.")
    registry_validate.add_argument("--registry", type=Path, help="Registry JSON path; defaults to the q-workflow source registry.")

    task = subcommands.add_parser("task", help="Validate or transact one versioned task record.")
    task_commands = task.add_subparsers(dest="task_command", required=True)
    listing = task_commands.add_parser("list", help="List every registered task and mark the active focus.")
    listing.add_argument("--work-state", choices=("briefing", "active", "paused", "blocked", "validating", "closed"))
    validate = task_commands.add_parser("validate", help="Validate one task record and its bound event chain.")
    selectors = validate.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--record", type=Path, help="Record path directly under personal-state/tasks.")
    selectors.add_argument("--task-id", help="Portable registered task id.")
    selectors.add_argument("--trace-id", help="Trace id that resolves to exactly one registered task.")
    plan = task_commands.add_parser("plan", help="Create a non-authoritative, hash-bound write plan for review.")
    plan.add_argument("--record", type=Path, required=True, help="Candidate task-record JSON file.")
    focus = plan.add_mutually_exclusive_group()
    focus.add_argument("--focus-file", type=Path, help="Select the task and replace Current Focus with this UTF-8 text.")
    focus.add_argument(
        "--focus-current",
        action="store_true",
        help="Preserve Current Focus only when the candidate task already owns focus; cross-task switches require --focus-file.",
    )
    plan.add_argument("--output", type=Path, required=True, help="Private path for the reviewable plan JSON.")
    apply = task_commands.add_parser("apply", help="Apply a reviewed plan with lock, CAS, rollback, and readback.")
    apply.add_argument("--plan", type=Path, required=True, help="Plan JSON produced by task plan.")
    apply.add_argument("--yes", action="store_true", help="Required explicit non-interactive confirmation.")
    recovery = task_commands.add_parser("recover", help="Restore an interrupted transaction after validating journal paths and hashes.")
    recovery.add_argument("--yes", action="store_true", help="Required confirmation to restore the journaled original state.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            payload = self_test()
            print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else f"q-workflow-manager self-test: {payload['status']} cases={payload['cases']}")
            return 0 if payload["status"] == "pass" else 1
        if args.command == "status":
            payload = status_report(args.profile)
            code = 0 if payload["status"] == "pass" else 1
        elif args.command == "doctor":
            payload = doctor_report(args.profile, full=args.full, rounds=args.rounds)
            code = 0 if payload["status"] == "pass" else 1
        elif args.command == "surfaces":
            _, profile = load_profile(args.profile)
            payload = surface_report(profile, load_surface_registry(args.registry), tier=args.tier)
            code = 1 if args.strict and payload["summary"]["status"] != "pass" else 0
        elif args.command == "registry" and args.registry_command == "validate":
            registry = load_surface_registry(args.registry)
            payload = {
                "format_version": 1,
                "schema": "q-workflow-surface-registry-validation-v1",
                "status": "pass",
                "registry": str((args.registry or Path(__file__).resolve().parents[1] / "references" / "surface-registry.json").resolve()),
                "roots": len(registry["roots"]),
                "skills": len(registry["skills"]),
                "core_skills": sum(skill.get("tier") == "core" for skill in registry["skills"]),
            }
            code = 0
        elif args.command == "task" and args.task_command == "list":
            payload = task_list_report(args.profile, work_state=args.work_state)
            code = 0 if payload["summary"]["status"] == "pass" else 1
        elif args.command == "task" and args.task_command == "validate":
            hub = personal_hub(load_profile(args.profile)[1])
            record_path = resolve_task_record(hub, record_path=args.record, task_id=args.task_id, trace_id=args.trace_id)
            payload = inspect_task_record(record_path, task_event_log_path(hub))
            code = 0 if payload["status"] == "pass" else 1
        elif args.command == "task" and args.task_command == "plan":
            record = read_json_object(args.record)
            if args.focus_file:
                focus_text = args.focus_file.read_text(encoding="utf-8-sig").strip()
            elif args.focus_current:
                focus_text = current_focus_text_for_record(args.profile, record)
            else:
                focus_text = None
            payload = build_task_plan(args.profile, record, focus_text=focus_text)
            write_plan(args.output, payload)
            payload = {
                "status": "planned",
                "plan_id": payload["plan_id"],
                "plan_path": str(args.output.resolve()),
                "task_id": payload["task_id"],
                "update_focus": payload["update_focus"],
                "targets": {
                    name: {key: value for key, value in row.items() if key != "candidate_base64"}
                    for name, row in payload["targets"].items()
                },
                "next_action": "Review the plan, then run task apply --plan <path> --yes.",
            }
            code = 0
        elif args.command == "task" and args.task_command == "recover":
            payload = recover_task_transaction(args.profile, yes=args.yes)
            code = 0
        elif args.command == "task" and args.task_command == "apply":
            plan = read_json_object(args.plan)
            receipt = apply_task_plan(args.profile, plan, yes=args.yes)
            payload = {"status": "applied", "receipt": receipt}
            code = 0
        else:
            parser.print_help()
            return 2
    except (TaskStateError, RuntimeManifestError, WorkflowFileLockError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, (TaskStateError, RuntimeManifestError, WorkflowFileLockError)):
            failure_class = "contract"
        elif isinstance(exc, json.JSONDecodeError):
            failure_class = "invalid-json"
        elif isinstance(exc, UnicodeError):
            failure_class = "invalid-encoding"
        else:
            failure_class = "io-error"
        payload = {"status": "blocked", "failure_class": failure_class, "error": str(exc)}
        code = 1
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
