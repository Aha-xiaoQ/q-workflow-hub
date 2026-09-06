#!/usr/bin/env python3
"""Shared task-record, transition, event, and pointer contracts for q-workflow."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


TASK_SCHEMA = "q-workflow-task-v1"
TASK_FORMAT_VERSION = 1
TRACE_ID_MAX_LENGTH = 200
STATE_REVISION_MAX_LENGTH = 240
TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
EVENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$")
OID_RE = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")
PRIMARY_STATUSES = {"planned", "running", "completed", "deferred"}
GATE_STATUSES = {"pending", "completed", "deferred"}
RESOLVED_GATE_STATUSES = {"completed", "deferred"}
BLOCKING_INTEGRITY_STATES = {"stale", "drift", "conflicted"}
TASK_EVENTS_NAME = "TASK_EVENTS.jsonl"


class TaskStateError(ValueError):
    """Raised when a task record, event, pointer, or transition is invalid."""


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TaskStateError(f"Cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise TaskStateError(f"JSON root must be an object: {path}")
    return value


def load_lifecycle_contract(path: Path | None = None) -> dict[str, Any]:
    return read_json_object(path or skill_root() / "references" / "lifecycle-contract.json")


def task_record_bytes(record: dict[str, Any]) -> bytes:
    return (json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timezone_timestamp(value: Any) -> bool:
    if not _nonempty_string(value):
        return False
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def lifecycle_axes(contract: dict[str, Any] | None = None) -> dict[str, set[str]]:
    data = contract or load_lifecycle_contract()
    axes = data.get("axes") if isinstance(data.get("axes"), dict) else {}
    return {
        "work_state": set(axes.get("work", [])),
        "integrity_state": set(axes.get("integrity", [])),
        "release_state": set(axes.get("release", [])),
    }


def _role(record: dict[str, Any], name: str) -> dict[str, Any]:
    plan = record.get("role_plan")
    if not isinstance(plan, dict):
        return {}
    row = plan.get(name)
    return row if isinstance(row, dict) else {}


def validate_task_record(
    record: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> list[str]:
    """Validate the portable task contract without consulting mutable state."""
    errors: list[str] = []
    data = contract or load_lifecycle_contract()
    axes = lifecycle_axes(data)

    if record.get("format_version") != TASK_FORMAT_VERSION:
        errors.append("format_version must equal 1")
    if record.get("schema") != TASK_SCHEMA:
        errors.append(f"schema must equal {TASK_SCHEMA}")
    task_id = record.get("task_id")
    if not _nonempty_string(task_id) or not TASK_ID_RE.fullmatch(str(task_id)):
        errors.append("task_id must be a portable slug of 1-128 characters")
    if not _nonempty_string(record.get("trace_id")):
        errors.append("trace_id is required")
    elif len(str(record["trace_id"])) > TRACE_ID_MAX_LENGTH:
        errors.append(f"trace_id must be at most {TRACE_ID_MAX_LENGTH} characters")
    epoch = record.get("execution_epoch")
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 1:
        errors.append("execution_epoch must be an integer >= 1")
    if not _nonempty_string(record.get("state_revision")):
        errors.append("state_revision is required")
    elif len(str(record["state_revision"])) > STATE_REVISION_MAX_LENGTH:
        errors.append(f"state_revision must be at most {STATE_REVISION_MAX_LENGTH} characters")
    event_id = record.get("authority_event")
    if not _nonempty_string(event_id) or not EVENT_ID_RE.fullmatch(str(event_id)):
        errors.append("authority_event must be a portable slug of 1-160 characters")

    for field, values in axes.items():
        if record.get(field) not in values:
            errors.append(f"{field}={record.get(field)!r} is outside the lifecycle contract")

    role_plan = record.get("role_plan")
    if not isinstance(role_plan, dict):
        errors.append("role_plan must be an object")
    elif not _nonempty_string(role_plan.get("id")):
        errors.append("role_plan.id is required")
    for name in ("primary", "reviewer", "validator"):
        role = _role(record, name)
        if not role:
            errors.append(f"role_plan.{name} must be an object")
            continue
        if not _nonempty_string(role.get("owner")):
            errors.append(f"role_plan.{name}.owner is required")
        allowed = PRIMARY_STATUSES if name == "primary" else GATE_STATUSES
        if role.get("status") not in allowed:
            errors.append(f"role_plan.{name}.status={role.get('status')!r} is invalid")

    remote = record.get("remote")
    if not isinstance(remote, dict):
        errors.append("remote must be an object")
        remote = {}
    remote_status = remote.get("status")
    remote_proven = remote.get("proven")
    if remote_status not in {"unproven", "proven"}:
        errors.append("remote.status must be unproven or proven")
    if not isinstance(remote_proven, bool):
        errors.append("remote.proven must be boolean")
    if remote_status == "proven" and remote_proven is not True:
        errors.append("remote.status=proven requires remote.proven=true")
    if remote_status == "unproven" and remote_proven is not False:
        errors.append("remote.status=unproven requires remote.proven=false")

    if not _nonempty_string(record.get("next_action")):
        errors.append("next_action is required")
    if not _timezone_timestamp(record.get("updated_at")):
        errors.append("updated_at must be an ISO-8601 timestamp with timezone")
    focus = record.get("focus")
    if not isinstance(focus, dict) or not _nonempty_string(focus.get("summary")):
        errors.append("focus.summary is required")
    detail = record.get("detail")
    if detail is not None and not isinstance(detail, dict):
        errors.append("detail must be an object when present")

    work_state = record.get("work_state")
    integrity_state = record.get("integrity_state")
    release_state = record.get("release_state")
    primary = _role(record, "primary")
    reviewer = _role(record, "reviewer")
    validator = _role(record, "validator")

    if work_state == "blocked":
        if not _nonempty_string(record.get("blocked_on")):
            errors.append("blocked work_state requires blocked_on")
        if not _nonempty_string(record.get("error_code")):
            errors.append("blocked work_state requires error_code")
    if work_state == "closed":
        if reviewer.get("status") not in RESOLVED_GATE_STATUSES:
            errors.append("closed work_state requires a resolved reviewer")
        if validator.get("status") not in RESOLVED_GATE_STATUSES:
            errors.append("closed work_state requires a resolved validator")
        if reviewer.get("owner") and reviewer.get("owner") == primary.get("owner"):
            errors.append("closed work_state requires an independent reviewer owner")
        if validator.get("owner") and validator.get("owner") == primary.get("owner"):
            errors.append("closed work_state requires an independent validator owner")
    if reviewer.get("status") == "deferred" or validator.get("status") == "deferred":
        if release_state != "local-only":
            errors.append("deferred reviewer or validator limits release_state to local-only")
    if integrity_state in BLOCKING_INTEGRITY_STATES and release_state != "local-only":
        errors.append(f"integrity_state={integrity_state} limits release_state to local-only")
    if release_state in {"ready", "released"} and not (
        remote_status == "proven" and remote_proven is True
    ):
        errors.append("ready/released requires proven remote evidence")
    if release_state in {"ready", "released"}:
        required_evidence = (
            "release_receipt",
            "release_receipt_sha256",
            "release_remote",
            "release_branch",
            "release_fetched_at",
            "release_target_oid",
            "signoff_id",
        )
        for key in required_evidence:
            if not _nonempty_string(remote.get(key)):
                errors.append(f"ready/released requires remote.{key}")
        if _nonempty_string(remote.get("release_receipt_sha256")) and not re.fullmatch(
            r"[0-9a-fA-F]{64}", str(remote["release_receipt_sha256"])
        ):
            errors.append("remote.release_receipt_sha256 must be a SHA-256 digest")
        if _nonempty_string(remote.get("release_target_oid")) and not OID_RE.fullmatch(
            str(remote["release_target_oid"])
        ):
            errors.append("remote.release_target_oid must be a 40- or 64-character hexadecimal object id")
        if _nonempty_string(remote.get("release_fetched_at")) and not _timezone_timestamp(
            remote.get("release_fetched_at")
        ):
            errors.append("remote.release_fetched_at must include a timezone")
    return errors


def task_record_path(hub: Path, task_id: str) -> Path:
    if not TASK_ID_RE.fullmatch(task_id):
        raise TaskStateError(f"Unsafe task_id: {task_id!r}")
    root = (hub / "personal-state" / "tasks").resolve()
    candidate = (root / f"{task_id}.json").resolve()
    if candidate.parent != root:
        raise TaskStateError("Task record path escaped the task registry root")
    return candidate


def task_event_log_path(hub: Path) -> Path:
    return hub / "personal-state" / TASK_EVENTS_NAME


def resolve_task_record(
    hub: Path,
    *,
    task_id: str | None = None,
    trace_id: str | None = None,
    record_path: Path | None = None,
) -> Path:
    selectors = sum(value is not None for value in (task_id, trace_id, record_path))
    if selectors != 1:
        raise TaskStateError("Choose exactly one of task_id, trace_id, or record_path")
    root = (hub / "personal-state" / "tasks").resolve()
    if record_path is not None:
        candidate = record_path if record_path.is_absolute() else hub / record_path
        candidate = candidate.resolve()
        if candidate.parent != root:
            raise TaskStateError(f"Task record must live directly under {root}")
        return candidate
    if task_id is not None:
        return task_record_path(hub, task_id)
    matches: list[Path] = []
    if root.is_dir():
        for path in sorted(root.glob("*.json")):
            try:
                value = read_json_object(path)
            except TaskStateError:
                continue
            if value.get("trace_id") == trace_id:
                matches.append(path)
    if len(matches) != 1:
        raise TaskStateError(f"trace_id={trace_id!r} resolved to {len(matches)} task records")
    return matches[0]


def _derived_sync_state(integrity_state: str) -> str:
    if integrity_state in {"clean", "local-validated", "offline-validated"}:
        return "local-validated"
    return "stale"


def flatten_task_record(
    record: dict[str, Any],
    *,
    record_path: Path | None = None,
    record_sha256: str | None = None,
    event_log: Path | None = None,
) -> dict[str, str]:
    """Render the compatibility fields consumed by quick-resume surfaces."""
    primary = _role(record, "primary")
    reviewer = _role(record, "reviewer")
    validator = _role(record, "validator")
    remote = record.get("remote") if isinstance(record.get("remote"), dict) else {}
    focus = record.get("focus") if isinstance(record.get("focus"), dict) else {}
    detail = record.get("detail") if isinstance(record.get("detail"), dict) else {}
    values = {
        "schema": "q-workflow-focus-v2",
        "task_id": str(record.get("task_id", "")),
        "trace_id": str(record.get("trace_id", "")),
        "execution_epoch": str(record.get("execution_epoch", "")),
        "state_revision": str(record.get("state_revision", "")),
        "authority_event": str(record.get("authority_event", "")),
        "work_state": str(record.get("work_state", "")),
        "visibility_latch": (
            "phase-b-required"
            if str(record.get("work_state", "")) in {"active", "validating", "blocked"}
            else "not-required"
        ),
        "integrity_state": str(record.get("integrity_state", "")),
        "release_state": str(record.get("release_state", "")),
        "role_plan_id": str(record.get("role_plan", {}).get("id", "")),
        "primary_owner": str(primary.get("owner", "")),
        "primary_status": str(primary.get("status", "")),
        "reviewer_owner": str(reviewer.get("owner", "")),
        "reviewer_status": str(reviewer.get("status", "")),
        "validator_owner": str(validator.get("owner", "")),
        "validator_status": str(validator.get("status", "")),
        "remote_status": str(remote.get("status", "")),
        "remote_proven": "true" if remote.get("proven") is True else "false",
        "sync_state": _derived_sync_state(str(record.get("integrity_state", ""))),
        "next_action": str(record.get("next_action", "")),
        "updated_at": str(record.get("updated_at", "")),
    }
    for key in ("blocked_on", "error_code"):
        if _nonempty_string(record.get(key)):
            values[key] = str(record[key])
    for key in ("work_item_path", "authority_path"):
        if _nonempty_string(focus.get(key)):
            values[key] = str(focus[key])
    for key in (
        "release_receipt",
        "release_receipt_sha256",
        "release_remote",
        "release_branch",
        "release_fetched_at",
        "release_target_oid",
        "signoff_id",
    ):
        if _nonempty_string(remote.get(key)):
            values[key] = str(remote[key])
    if _nonempty_string(detail.get("domain_work_state")):
        values["domain_work_state"] = str(detail["domain_work_state"])
    if _nonempty_string(detail.get("domain_integrity_state")):
        values["domain_integrity_state"] = str(detail["domain_integrity_state"])
    if record_path is not None:
        values["task_record_path"] = record_path.as_posix()
    if record_sha256:
        values["task_record_sha256"] = record_sha256.upper()
    if event_log is not None:
        values["task_event_log"] = event_log.as_posix()
    return values


def release_receipt_errors(path: Path, binding: dict[str, str], hub: Path) -> list[str]:
    """Validate one release receipt and every task/pointer field bound to it."""
    errors: list[str] = []
    if not path.is_absolute():
        return ["release_receipt must be an absolute path"]
    if not path.is_file():
        return [f"release_receipt is missing: {path}"]
    try:
        resolved = path.resolve(strict=True)
        evidence_root = (hub / "reports").resolve(strict=True)
        if not resolved.is_relative_to(evidence_root):
            errors.append("release_receipt must be stored under the authoritative hub reports root")
    except OSError as exc:
        errors.append(f"release_receipt path cannot be resolved: {exc}")
    try:
        actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        actual_hash = ""
        errors.append(f"release_receipt cannot be hashed: {exc}")
    expected_hash = binding.get("release_receipt_sha256", "")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_hash):
        errors.append("task is missing a valid release_receipt_sha256")
    elif actual_hash.casefold() != expected_hash.casefold():
        errors.append("release_receipt SHA-256 does not match the task")
    try:
        data = read_json_object(path)
    except TaskStateError as exc:
        errors.append(str(exc))
        data = {}
    if data.get("format_version") != 1:
        errors.append("release_receipt format_version must equal 1")
    if data.get("strict_readiness_status") != "pass":
        errors.append("release_receipt strict_readiness_status must equal pass")
    bindings = {
        "remote": "release_remote",
        "branch": "release_branch",
        "fetched_at": "release_fetched_at",
        "target_oid": "release_target_oid",
        "signoff_id": "signoff_id",
    }
    for receipt_key, task_key in bindings.items():
        if not binding.get(task_key):
            errors.append(f"task is missing {task_key}")
        elif data.get(receipt_key) != binding.get(task_key):
            errors.append(f"release_receipt {receipt_key} does not match task {task_key}")
    target_oid = str(data.get("target_oid", ""))
    remote_head = str(data.get("remote_head", ""))
    if not OID_RE.fullmatch(target_oid):
        errors.append("release_receipt target_oid must be a 40- or 64-character hexadecimal object id")
    if not OID_RE.fullmatch(remote_head):
        errors.append("release_receipt remote_head must be a 40- or 64-character hexadecimal object id")
    if target_oid and remote_head and target_oid.casefold() != remote_head.casefold():
        errors.append("release_receipt remote_head must equal target_oid")
    fetched_at = str(data.get("fetched_at", ""))
    if not _timezone_timestamp(fetched_at):
        errors.append("release_receipt fetched_at must be an ISO-8601 timestamp with timezone")
    return errors


def validate_transition(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> list[str]:
    if previous is None:
        expected = (
            current.get("work_state") == "briefing"
            and current.get("integrity_state") == "local-validated"
            and current.get("release_state") == "local-only"
        )
        detail = current.get("detail") if isinstance(current.get("detail"), dict) else {}
        migration = detail.get("migration") == "legacy-recovery-pointer-to-task-record-v1"
        migration = migration and "migration" in str(current.get("authority_event", "")).casefold()
        migration = migration and current.get("work_state") in {"active", "paused", "blocked", "validating"}
        migration = migration and current.get("integrity_state") == "local-validated"
        migration = migration and current.get("release_state") == "local-only"
        if not expected and not migration:
            return [
                "new task registration must start at briefing/local-validated/local-only; "
                "legacy migration requires the declared migration marker and a migration authority_event"
            ]
        return []
    errors: list[str] = []
    data = contract or load_lifecycle_contract()
    if previous.get("task_id") != current.get("task_id"):
        errors.append("task_id cannot change within one task record")
    if previous.get("trace_id") != current.get("trace_id"):
        errors.append("trace_id cannot change within one task record")
    old_epoch = previous.get("execution_epoch")
    new_epoch = current.get("execution_epoch")
    if isinstance(old_epoch, int) and isinstance(new_epoch, int) and new_epoch < old_epoch:
        errors.append("execution_epoch cannot decrease")

    source = previous.get("work_state")
    target = current.get("work_state")
    if source != target:
        transition = next(
            (
                row
                for row in data.get("transitions", [])
                if isinstance(row, dict) and source in row.get("from", []) and target == row.get("to")
            ),
            None,
        )
        if transition is None:
            errors.append(f"work_state transition {source!r}->{target!r} is not allowed")
        else:
            event_name = transition.get("event")
            if previous.get("state_revision") == current.get("state_revision"):
                errors.append(f"{event_name} requires a new state_revision")
            if previous.get("authority_event") == current.get("authority_event"):
                errors.append(f"{event_name} requires a new authority_event")
            primary_status = _role(current, "primary").get("status")
            if event_name == "start" and primary_status not in {"planned", "running"}:
                errors.append("start requires primary status planned or running")
            if event_name == "validate" and primary_status not in {"completed", "deferred"}:
                errors.append("validate requires primary status completed or deferred")
            if event_name == "block":
                if not _nonempty_string(current.get("blocked_on")):
                    errors.append("block requires blocked_on")
                if not _nonempty_string(current.get("error_code")):
                    errors.append("block requires error_code")
            if event_name == "resume":
                if not isinstance(old_epoch, int) or not isinstance(new_epoch, int) or new_epoch <= old_epoch:
                    errors.append("resume requires execution_epoch to increase")
            if event_name == "close":
                if _role(current, "reviewer").get("status") not in RESOLVED_GATE_STATUSES:
                    errors.append("close requires a resolved reviewer")
                if _role(current, "validator").get("status") not in RESOLVED_GATE_STATUSES:
                    errors.append("close requires a resolved validator")
    elif task_record_bytes(previous) != task_record_bytes(current):
        if previous.get("state_revision") == current.get("state_revision"):
            errors.append("a changed task record requires a new state_revision")
        if previous.get("authority_event") == current.get("authority_event"):
            errors.append("a changed task record requires a new authority_event")
    return errors


def transition_event_name(
    previous: dict[str, Any] | None,
    current: dict[str, Any],
    contract: dict[str, Any] | None = None,
) -> str:
    if previous is None:
        return "register"
    source = previous.get("work_state")
    target = current.get("work_state")
    if source == target:
        return "update"
    data = contract or load_lifecycle_contract()
    row = next(
        (
            item
            for item in data.get("transitions", [])
            if isinstance(item, dict) and source in item.get("from", []) and target == item.get("to")
        ),
        None,
    )
    return str(row.get("event")) if row else "invalid-transition"


def build_task_event(
    record: dict[str, Any],
    previous: dict[str, Any] | None,
    record_sha256: str,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "format_version": 1,
        "event_id": record["authority_event"],
        "event_type": transition_event_name(previous, record, contract),
        "task_id": record["task_id"],
        "trace_id": record["trace_id"],
        "execution_epoch": record["execution_epoch"],
        "state_revision": record["state_revision"],
        "record_sha256": record_sha256.upper(),
        "from": None
        if previous is None
        else {
            "work_state": previous.get("work_state"),
            "integrity_state": previous.get("integrity_state"),
            "release_state": previous.get("release_state"),
            "state_revision": previous.get("state_revision"),
        },
        "to": {
            "work_state": record.get("work_state"),
            "integrity_state": record.get("integrity_state"),
            "release_state": record.get("release_state"),
            "state_revision": record.get("state_revision"),
        },
        "written_at": record["updated_at"],
    }


def event_line(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def read_event_log(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.is_file():
        return [], [f"task event log is missing: {path}"]
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as exc:
        return [], [f"task event log cannot be read: {path}: {exc}"]
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"task event log line {index} is invalid JSON: {exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"task event log line {index} is not an object")
            continue
        events.append(value)
    return events, errors


def _expected_event_type(source: str | None, target: str | None, contract: dict[str, Any]) -> str | None:
    if source is None:
        return "register"
    if source == target:
        return "update"
    row = next(
        (
            item
            for item in contract.get("transitions", [])
            if isinstance(item, dict) and source in item.get("from", []) and target == item.get("to")
        ),
        None,
    )
    return str(row.get("event")) if row else None


def validate_event_ledger(events: list[dict[str, Any]], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    by_task: dict[str, list[dict[str, Any]]] = {}
    axes = lifecycle_axes(contract)
    for index, event in enumerate(events, start=1):
        prefix = f"task event line {index}"
        event_id = event.get("event_id")
        if not _nonempty_string(event_id) or not EVENT_ID_RE.fullmatch(str(event_id)):
            errors.append(f"{prefix} has an invalid event_id")
        elif str(event_id) in seen_ids:
            errors.append(f"duplicate task event_id={event_id!r}")
        else:
            seen_ids.add(str(event_id))
        if event.get("format_version") != 1:
            errors.append(f"{prefix} format_version must equal 1")
        for key in ("task_id", "trace_id", "state_revision", "record_sha256", "written_at"):
            if not _nonempty_string(event.get(key)):
                errors.append(f"{prefix} is missing {key}")
        if _nonempty_string(event.get("record_sha256")) and not re.fullmatch(
            r"[0-9a-fA-F]{64}", str(event["record_sha256"])
        ):
            errors.append(f"{prefix} record_sha256 is invalid")
        if not isinstance(event.get("execution_epoch"), int) or isinstance(event.get("execution_epoch"), bool) or event.get("execution_epoch", 0) < 1:
            errors.append(f"{prefix} execution_epoch must be an integer >= 1")
        if not _timezone_timestamp(event.get("written_at")):
            errors.append(f"{prefix} written_at must include a timezone")
        raw_target = event.get("to")
        raw_source = event.get("from")
        target = raw_target if isinstance(raw_target, dict) else {}
        source = raw_source if isinstance(raw_source, dict) else None
        if raw_source is not None and not isinstance(raw_source, dict):
            errors.append(f"{prefix} from must be null or an object")
        if not target:
            errors.append(f"{prefix} must contain a to object")
        else:
            for field, values in axes.items():
                if target.get(field) not in values:
                    errors.append(f"{prefix} to.{field} is outside the lifecycle contract")
            if target.get("state_revision") != event.get("state_revision"):
                errors.append(f"{prefix} to.state_revision does not match state_revision")
        if source is not None:
            for field, values in axes.items():
                if source.get(field) not in values:
                    errors.append(f"{prefix} from.{field} is outside the lifecycle contract")
            if not _nonempty_string(source.get("state_revision")):
                errors.append(f"{prefix} from.state_revision is required")
        expected_type = _expected_event_type(
            source.get("work_state") if source else None,
            target.get("work_state"),
            contract,
        )
        legacy_migration_registration = (
            source is None
            and "migration" in str(event_id).casefold()
            and target.get("work_state") in {"active", "paused", "blocked", "validating"}
            and target.get("integrity_state") == "local-validated"
            and target.get("release_state") == "local-only"
        )
        normal_registration = (
            source is None
            and target.get("work_state") == "briefing"
            and target.get("integrity_state") == "local-validated"
            and target.get("release_state") == "local-only"
        )
        if source is None and not normal_registration and not legacy_migration_registration:
            errors.append(
                f"{prefix} non-migration registration must start at briefing/local-validated/local-only"
            )
        if expected_type is None:
            errors.append(f"{prefix} encodes an invalid work_state transition")
        elif event.get("event_type") != expected_type:
            errors.append(f"{prefix} event_type={event.get('event_type')!r} must equal {expected_type!r}")
        task_id = str(event.get("task_id", ""))
        if task_id:
            by_task.setdefault(task_id, []).append(event)

    for task_id, rows in by_task.items():
        previous: dict[str, Any] | None = None
        trace_id: str | None = None
        previous_epoch: int | None = None
        for position, event in enumerate(rows, start=1):
            event_trace = str(event.get("trace_id", ""))
            if trace_id is None:
                trace_id = event_trace
            elif event_trace != trace_id:
                errors.append(f"task_id={task_id!r} changes trace_id within its event chain")
            source = event.get("from") if isinstance(event.get("from"), dict) else None
            if position == 1 and source is not None:
                errors.append(f"task_id={task_id!r} first event must have from=null")
            if previous is not None:
                prior_target = previous.get("to") if isinstance(previous.get("to"), dict) else {}
                if source is None:
                    errors.append(f"task_id={task_id!r} event {position} is missing from state")
                else:
                    for key in ("work_state", "integrity_state", "release_state", "state_revision"):
                        if source.get(key) != prior_target.get(key):
                            errors.append(f"task_id={task_id!r} event {position} from.{key} breaks chain continuity")
            epoch = event.get("execution_epoch")
            if isinstance(epoch, int) and previous_epoch is not None and epoch < previous_epoch:
                errors.append(f"task_id={task_id!r} execution_epoch decreases in its event chain")
            if (
                event.get("event_type") == "resume"
                and isinstance(epoch, int)
                and previous_epoch is not None
                and epoch <= previous_epoch
            ):
                errors.append(
                    f"task_id={task_id!r} resume event must increment execution_epoch"
                )
            if isinstance(epoch, int):
                previous_epoch = epoch
            previous = event
    return errors


def validate_task_event(
    record: dict[str, Any],
    event_log: Path,
    record_sha256: str,
) -> list[str]:
    events, errors = read_event_log(event_log)
    contract = load_lifecycle_contract()
    errors.extend(validate_event_ledger(events, contract))
    matches = [event for event in events if event.get("event_id") == record.get("authority_event")]
    if len(matches) != 1:
        errors.append(
            f"authority_event={record.get('authority_event')!r} resolved to {len(matches)} JSONL events"
        )
        return errors
    event = matches[0]
    bindings = {
        "task_id": record.get("task_id"),
        "trace_id": record.get("trace_id"),
        "execution_epoch": record.get("execution_epoch"),
        "state_revision": record.get("state_revision"),
        "record_sha256": record_sha256.upper(),
    }
    for key, expected in bindings.items():
        actual = event.get(key)
        if isinstance(expected, str) and key == "record_sha256":
            actual = str(actual).upper()
        if actual != expected:
            errors.append(f"task event {key}={actual!r} does not match record {expected!r}")
    if event.get("written_at") != record.get("updated_at"):
        errors.append("task event written_at does not match record updated_at")
    target = event.get("to") if isinstance(event.get("to"), dict) else {}
    for key in ("work_state", "integrity_state", "release_state", "state_revision"):
        if target.get(key) != record.get(key):
            errors.append(f"task event to.{key} does not match the task record")
    task_events = [row for row in events if row.get("task_id") == record.get("task_id")]
    if task_events:
        first_event = task_events[0]
        first_target = first_event.get("to") if isinstance(first_event.get("to"), dict) else {}
        if first_target.get("work_state") != "briefing":
            detail = record.get("detail") if isinstance(record.get("detail"), dict) else {}
            if (
                detail.get("migration") != "legacy-recovery-pointer-to-task-record-v1"
                or "migration" not in str(first_event.get("event_id", "")).casefold()
            ):
                errors.append("non-briefing first task event lacks the bounded legacy migration marker")
    if task_events and task_events[-1].get("event_id") != record.get("authority_event"):
        errors.append("task record authority_event is not the latest event for its task_id")
    return errors


def validate_pointer_binding(
    pointer: dict[str, str],
    record: dict[str, Any],
    record_path: Path,
    record_sha256: str,
    event_log: Path,
) -> list[str]:
    expected = flatten_task_record(
        record,
        record_path=record_path,
        record_sha256=record_sha256,
        event_log=event_log,
    )
    errors: list[str] = []
    for key, value in expected.items():
        actual = pointer.get(key)
        if key in {"task_record_path", "task_event_log"} and actual:
            try:
                if Path(actual).resolve() == Path(value).resolve():
                    continue
            except OSError:
                pass
        if actual != value:
            errors.append(f"focus pointer {key}={actual!r} does not match task record {value!r}")
    return errors


def inspect_task_record(
    record_path: Path,
    event_log: Path,
    *,
    pointer: dict[str, str] | None = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        record = read_json_object(record_path)
    except TaskStateError as exc:
        return {
            "record_path": str(record_path),
            "record": {},
            "record_sha256": "",
            "event_log": str(event_log),
            "errors": [str(exc)],
            "status": "blocked",
        }
    record_bytes_value = record_path.read_bytes()
    record_sha = sha256_bytes(record_bytes_value)
    errors.extend(validate_task_record(record, contract))
    task_id = record.get("task_id")
    if _nonempty_string(task_id) and record_path.name != f"{task_id}.json":
        errors.append(
            f"task record filename {record_path.name!r} does not match task_id={task_id!r}"
        )
    errors.extend(validate_task_event(record, event_log, record_sha))
    if record.get("release_state") in {"ready", "released"}:
        inferred_hub = record_path.resolve().parents[2]
        binding = flatten_task_record(record)
        errors.extend(
            release_receipt_errors(
                Path(binding.get("release_receipt", "")),
                binding,
                inferred_hub,
            )
        )
    if pointer is not None:
        errors.extend(validate_pointer_binding(pointer, record, record_path, record_sha, event_log))
    return {
        "record_path": str(record_path),
        "record": record,
        "record_sha256": record_sha,
        "event_log": str(event_log),
        "errors": errors,
        "status": "pass" if not errors else "blocked",
    }


def duplicate_event_ids(events: Iterable[dict[str, Any]]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for event in events:
        event_id = str(event.get("event_id", ""))
        if event_id in seen:
            duplicates.add(event_id)
        seen.add(event_id)
    return duplicates


def self_test() -> dict[str, Any]:
    failures: list[str] = []
    valid = {
        "format_version": 1,
        "schema": TASK_SCHEMA,
        "task_id": "sample-task",
        "trace_id": "SAMPLE-TRACE",
        "execution_epoch": 1,
        "state_revision": "sample-r1",
        "authority_event": "sample-register-r1",
        "work_state": "active",
        "integrity_state": "local-validated",
        "release_state": "local-only",
        "role_plan": {
            "id": "sample-role-plan",
            "primary": {"owner": "main", "status": "running"},
            "reviewer": {"owner": "reviewer", "status": "pending"},
            "validator": {"owner": "validator", "status": "pending"},
        },
        "remote": {"status": "unproven", "proven": False},
        "next_action": "Continue the bounded sample.",
        "updated_at": "2026-08-09T20:00:00+08:00",
        "focus": {"summary": "Sample task."},
        "detail": {"domain_work_state": "sample-domain-stage"},
    }
    if validate_task_record(valid):
        failures.append("valid task record was rejected")
    invalid_axis = dict(valid, work_state="sample-domain-stage")
    if not any("work_state" in error for error in validate_task_record(invalid_axis)):
        failures.append("domain work state was accepted as a generic axis")
    blocked = dict(valid, work_state="blocked", state_revision="sample-r2")
    if not any("blocked_on" in error for error in validate_task_record(blocked)):
        failures.append("blocked task without blocker fields was accepted")
    closed = json.loads(json.dumps(valid))
    closed.update(work_state="closed", state_revision="sample-r3")
    closed["role_plan"]["primary"] = {"owner": "same", "status": "completed"}
    closed["role_plan"]["reviewer"] = {"owner": "same", "status": "completed"}
    closed["role_plan"]["validator"] = {"owner": "validator", "status": "completed"}
    if not any("independent reviewer" in error for error in validate_task_record(closed)):
        failures.append("closed task with self-review was accepted")
    illegal = dict(valid, work_state="closed", state_revision="sample-r4")
    if not any("not allowed" in error for error in validate_transition(valid, illegal)):
        failures.append("illegal active-to-closed transition was accepted")
    pointer = flatten_task_record(valid)
    if pointer.get("domain_work_state") != "sample-domain-stage":
        failures.append("domain detail was not preserved in the compatibility pointer")
    if not validate_transition(None, valid):
        failures.append("new active task bypassed the required briefing registration state")
    migration = json.loads(json.dumps(valid))
    migration["authority_event"] = "sample-legacy-migration-r1"
    migration["detail"]["migration"] = "legacy-recovery-pointer-to-task-record-v1"
    if validate_transition(None, migration):
        failures.append("explicit legacy migration registration was rejected")
    ready = json.loads(json.dumps(valid))
    ready["release_state"] = "ready"
    ready["remote"] = {"status": "proven", "proven": True}
    if not any("release_receipt" in error for error in validate_task_record(ready)):
        failures.append("ready task without receipt evidence was accepted")
    too_long = dict(valid, trace_id="x" * 201)
    if not any("200" in error for error in validate_task_record(too_long)):
        failures.append("trace_id longer than the published schema was accepted")
    forged_event = {
        "format_version": 999,
        "event_id": "forged-event",
        "event_type": "close",
        "task_id": "forged-task",
        "trace_id": "FORGED",
        "execution_epoch": 1,
        "state_revision": "forged-r1",
        "record_sha256": "a" * 64,
        "from": {"work_state": "released-impossible"},
        "to": {
            "work_state": "active",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "forged-r1",
        },
        "written_at": "2026-08-09T20:00:00+08:00",
    }
    if not validate_event_ledger([forged_event], load_lifecycle_contract()):
        failures.append("forged event semantics were accepted")
    chain_states = {
        "briefing": {
            "work_state": "briefing",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "resume-r1",
        },
        "active": {
            "work_state": "active",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "resume-r2",
        },
        "paused": {
            "work_state": "paused",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "resume-r3",
        },
        "resumed": {
            "work_state": "briefing",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "resume-r4",
        },
    }
    resume_chain: list[dict[str, Any]] = []
    event_rows = (
        ("resume-register", "register", None, chain_states["briefing"], "2026-08-09T20:00:01+08:00"),
        ("resume-start", "start", chain_states["briefing"], chain_states["active"], "2026-08-09T20:00:02+08:00"),
        ("resume-pause", "pause", chain_states["active"], chain_states["paused"], "2026-08-09T20:00:03+08:00"),
        ("resume-without-epoch", "resume", chain_states["paused"], chain_states["resumed"], "2026-08-09T20:00:04+08:00"),
    )
    for event_id, event_type, source, target, written_at in event_rows:
        resume_chain.append(
            {
                "format_version": 1,
                "event_id": event_id,
                "event_type": event_type,
                "task_id": "resume-task",
                "trace_id": "RESUME-TRACE",
                "execution_epoch": 1,
                "state_revision": target["state_revision"],
                "record_sha256": "b" * 64,
                "from": source,
                "to": target,
                "written_at": written_at,
            }
        )
    if not any(
        "resume event must increment execution_epoch" in error
        for error in validate_event_ledger(resume_chain, load_lifecycle_contract())
    ):
        failures.append("resume without an execution_epoch increment was accepted")
    briefing = json.loads(json.dumps(valid))
    briefing.update(work_state="briefing", state_revision="start-r1", authority_event="start-register-r1")
    briefing["role_plan"]["primary"]["status"] = "planned"
    invalid_start = json.loads(json.dumps(briefing))
    invalid_start.update(work_state="active", state_revision="start-r2", authority_event="start-r2")
    invalid_start["role_plan"]["primary"]["status"] = "completed"
    if not any("start requires primary" in error for error in validate_transition(briefing, invalid_start)):
        failures.append("briefing-to-active accepted a completed primary")
    invalid_validate = json.loads(json.dumps(valid))
    invalid_validate.update(work_state="validating", state_revision="validate-r2", authority_event="validate-r2")
    if not any("validate requires primary" in error for error in validate_transition(valid, invalid_validate)):
        failures.append("active-to-validating accepted a running primary")
    direct_active_registration = {
        "format_version": 1,
        "event_id": "direct-active-register",
        "event_type": "register",
        "task_id": "direct-active-task",
        "trace_id": "DIRECT-ACTIVE",
        "execution_epoch": 1,
        "state_revision": "direct-active-r1",
        "record_sha256": "c" * 64,
        "from": None,
        "to": {
            "work_state": "active",
            "integrity_state": "local-validated",
            "release_state": "local-only",
            "state_revision": "direct-active-r1",
        },
        "written_at": "2026-08-09T20:00:05+08:00",
    }
    direct_errors = validate_event_ledger([direct_active_registration], load_lifecycle_contract())
    if not any("non-migration registration" in error for error in direct_errors):
        failures.append("first register event bypassed the briefing invariant")
    migration_registration = dict(direct_active_registration, event_id="legacy-migration-register")
    if validate_event_ledger([migration_registration], load_lifecycle_contract()):
        failures.append("bounded legacy migration registration was rejected")
    schema = read_json_object(skill_root() / "references" / "task-record.schema.json")
    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    schema_axes = {
        "work_state": set(properties.get("work_state", {}).get("enum", [])),
        "integrity_state": set(properties.get("integrity_state", {}).get("enum", [])),
        "release_state": set(properties.get("release_state", {}).get("enum", [])),
    }
    if (
        schema_axes != lifecycle_axes()
        or properties.get("trace_id", {}).get("maxLength") != TRACE_ID_MAX_LENGTH
        or properties.get("state_revision", {}).get("maxLength") != STATE_REVISION_MAX_LENGTH
    ):
        failures.append("published task schema drifted from the runtime lifecycle constraints")
    return {
        "status": "pass" if not failures else "blocked",
        "cases": 17,
        "failures": failures,
    }


if __name__ == "__main__":
    result = self_test()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "pass" else 1)
