#!/usr/bin/env python3
"""Inspect the durable lifecycle envelope for a material Q workflow task.

This is intentionally read-only. Authoritative transitions still go through the
personal-state workflow so a later journaled multi-file writer can replace it
without changing the validation contract.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, tempfile
from datetime import datetime
from pathlib import Path

from active_work_pointer import inspect_active_work
from workflow_task_state import (
    TaskStateError,
    inspect_task_record,
    release_receipt_errors as canonical_release_receipt_errors,
    resolve_task_record,
    task_event_log_path,
)

def home() -> Path: return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
def read_json(path: Path) -> dict:
    try: return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception: return {}
OID_RE = re.compile(r"^(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})$")


def release_receipt_errors(path: Path, pointer: dict[str, str], hub: Path) -> list[str]:
    return canonical_release_receipt_errors(path, pointer, hub)


def valid_release_receipt(path: Path, pointer: dict[str, str], hub: Path) -> bool:
    return not release_receipt_errors(path, pointer, hub)


def self_test() -> dict:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        hub = Path(temp) / "hub"
        receipt_root = hub / "reports" / "release-receipts"
        receipt_root.mkdir(parents=True)
        oid = "a" * 40
        pointer = {
            "release_remote": "origin",
            "release_branch": "main",
            "release_fetched_at": "2026-08-03T02:00:00+08:00",
            "release_target_oid": oid,
            "signoff_id": "SIGNOFF-1",
        }
        receipt = receipt_root / "receipt.json"
        valid = {
            "format_version": 1,
            "remote": "origin",
            "branch": "main",
            "fetched_at": "2026-08-03T02:00:00+08:00",
            "remote_head": oid,
            "target_oid": oid,
            "signoff_id": "SIGNOFF-1",
            "strict_readiness_status": "pass",
        }
        def write_receipt(payload: dict) -> None:
            receipt.write_text(json.dumps(payload), encoding="utf-8")
            pointer["release_receipt_sha256"] = hashlib.sha256(receipt.read_bytes()).hexdigest()

        write_receipt(valid)
        if not valid_release_receipt(receipt, pointer, hub):
            failures.append("valid bound receipt was rejected")
        wrong_remote = dict(valid, remote="upstream")
        write_receipt(wrong_remote)
        if not any("remote does not match" in item for item in release_receipt_errors(receipt, pointer, hub)):
            failures.append("remote mismatch was accepted")
        write_receipt(dict(valid, branch="release"))
        if not any("branch does not match" in item for item in release_receipt_errors(receipt, pointer, hub)):
            failures.append("branch mismatch was accepted")
        write_receipt(dict(valid, signoff_id="SIGNOFF-2"))
        if not any("signoff_id does not match" in item for item in release_receipt_errors(receipt, pointer, hub)):
            failures.append("signoff mismatch was accepted")
        write_receipt(dict(valid, remote_head="b" * 40))
        if not any("remote_head must equal target_oid" in item for item in release_receipt_errors(receipt, pointer, hub)):
            failures.append("remote-head mismatch was accepted")
        write_receipt(dict(valid, fetched_at="2026-08-03"))
        time_errors = release_receipt_errors(receipt, pointer, hub)
        if not any("fetched_at does not match" in item or "include a timezone" in item for item in time_errors):
            failures.append("timezone-free timestamp was accepted")
        write_receipt(dict(valid, target_oid="not-an-oid"))
        if valid_release_receipt(receipt, pointer, hub):
            failures.append("invalid object id was accepted")
        outside = Path(temp) / "outside.json"
        outside.write_text(json.dumps(valid), encoding="utf-8")
        pointer["release_receipt_sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
        if valid_release_receipt(outside, pointer, hub):
            failures.append("receipt outside authoritative reports root was accepted")
        single_pointer = Path(temp) / "ACTIVE_WORK_SINGLE.md"
        single_pointer.write_text("## Current Focus\n\n- Active task.\n\n## RECOVERY_POINTER v1\n\ntask_id: current\n", encoding="utf-8")
        if inspect_active_work(single_pointer)["pointer_heading_count"] != 1:
            failures.append("single RECOVERY_POINTER heading count was not detected")
        duplicate_pointer = Path(temp) / "ACTIVE_WORK_DUPLICATE.md"
        duplicate_pointer.write_text("## Current Focus\n\n- Active task.\n\n## RECOVERY_POINTER v1\n\ntask_id: current\n\n## RECOVERY_POINTER old\n\ntask_id: stale\n", encoding="utf-8")
        duplicate_state = inspect_active_work(duplicate_pointer)
        if duplicate_state["pointer_heading_count"] != 2 or not duplicate_state["errors"]:
            failures.append("duplicate RECOVERY_POINTER headings were not detected")
        idle = Path(temp) / "ACTIVE_WORK_IDLE.md"
        idle.write_text("## Current Focus\n\n- No active blocking focus.\n", encoding="utf-8")
        idle_state = inspect_active_work(idle)
        if idle_state["pointer_heading_count"] != 0 or idle_state["errors"]:
            failures.append("explicit idle ACTIVE_WORK was rejected")
        adversarial = {
            "empty-pointer": "## Current Focus\n\nActive.\n\n## RECOVERY_POINTER v1\n",
            "duplicate-key": "## Current Focus\n\nActive.\n\n## RECOVERY_POINTER v1\n\ntask_id: current\ntask_id: stale\n",
            "idle-plus-pointer": "## Current Focus\n\n- No active blocking focus.\n\n## RECOVERY_POINTER v1\n\ntask_id: stale\n",
            "empty-focus": "## Current Focus\n\n## RECOVERY_POINTER v1\n\ntask_id: current\n",
        }
        for label, content in adversarial.items():
            fixture = Path(temp) / f"ACTIVE_WORK_{label}.md"
            fixture.write_text(content, encoding="utf-8")
            if not inspect_active_work(fixture)["errors"]:
                failures.append(f"{label} ACTIVE_WORK was accepted")
        fenced = Path(temp) / "ACTIVE_WORK_FENCED_EXAMPLE.md"
        fenced.write_text("## Current Focus\n\nActive.\n\n```md\n## RECOVERY_POINTER example\ntask_id: example\n```\n\n## RECOVERY_POINTER v1\n\ntask_id: current\n", encoding="utf-8")
        fenced_state = inspect_active_work(fenced)
        if fenced_state["pointer_heading_count"] != 1 or fenced_state["errors"]:
            failures.append("fenced RECOVERY_POINTER example affected executable structure")
    return {"status": "pass" if not failures else "blocked", "failures": failures, "cases": 17}
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "text"), default="text")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--check-transition", nargs=2, metavar=("FROM", "TO"))
    parser.add_argument("--old-epoch", type=int)
    parser.add_argument("--new-epoch", type=int)
    parser.add_argument("--old-revision")
    parser.add_argument("--new-revision")
    parser.add_argument("--role-plan")
    parser.add_argument("--primary-status")
    parser.add_argument("--reviewer-status")
    parser.add_argument("--validator-status")
    parser.add_argument("--blocked-on")
    parser.add_argument("--error-code")
    selector = parser.add_mutually_exclusive_group()
    selector.add_argument("--task-id", help="Inspect one registered task without changing focus.")
    selector.add_argument("--trace-id", help="Resolve and inspect one registered task by trace id.")
    selector.add_argument("--record", type=Path, help="Inspect one task record under personal-state/tasks.")
    args = parser.parse_args()
    if args.self_test:
        payload = self_test()
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else f"workflow-lifecycle self-test: {payload['status']} cases={payload['cases']}")
        return 0 if payload["status"] == "pass" else 1
    contract = Path(__file__).resolve().parents[1] / "references" / "lifecycle-contract.json"
    if args.check_transition:
        source, target = args.check_transition
        data = read_json(contract)
        row = next((item for item in data.get("transitions", []) if isinstance(item, dict) and source in item.get("from", []) and target == item.get("to")), None)
        errors = []
        if row:
            event = row.get("event")
            if event == "start" and (not args.role_plan or args.primary_status not in {"planned", "running"}): errors.append("start requires role plan and planned/running primary")
            if event == "resume" and (args.old_epoch is None or args.new_epoch is None or args.new_epoch <= args.old_epoch or not args.old_revision or not args.new_revision or args.old_revision == args.new_revision): errors.append("resume requires incremented epoch and new revision")
            if event == "close" and (args.reviewer_status not in {"completed", "deferred"} or args.validator_status not in {"completed", "deferred"}): errors.append("close requires resolved reviewer and validator")
            if event == "block" and (not args.blocked_on or not args.error_code): errors.append("block requires blocked_on and error_code")
        valid = row is not None and not errors
        payload = {"format_version": 1, "from": source, "to": target, "event": row.get("event") if row else None, "allowed": valid, "guard_errors": errors, "status": "pass" if valid else "blocked"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else f"workflow-lifecycle transition: {payload['status']} {source}->{target}")
        return 0 if valid else 1
    profile = read_json(Path(os.environ.get("Q_PROFILE_PATH", str(home() / "q-profile.json"))))
    hub = Path(str(profile.get("hub", ""))).expanduser().resolve()
    active = hub / "personal-state" / "ACTIVE_WORK.md"
    active_state = inspect_active_work(active)
    pointer = dict(active_state["recovery_pointer"])
    explicit_selector = bool(args.task_id or args.trace_id or args.record)
    pointer_record = pointer.get("task_record_path")
    if explicit_selector or pointer_record:
        try:
            record_path = resolve_task_record(
                hub,
                task_id=args.task_id,
                trace_id=args.trace_id,
                record_path=args.record if explicit_selector else Path(str(pointer_record)),
            )
            event_log = task_event_log_path(hub)
            candidate = inspect_task_record(record_path, event_log)
            record = candidate.get("record") if isinstance(candidate.get("record"), dict) else {}
            bound_pointer = pointer if pointer.get("task_id") == record.get("task_id") else None
            if bound_pointer is not None:
                candidate = inspect_task_record(record_path, event_log, pointer=bound_pointer)
            invalid = list(candidate.get("errors", []))
            if not explicit_selector and active_state["errors"]:
                invalid = list(active_state["errors"]) + invalid
            payload = {
                "format_version": 2,
                "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "active": str(active),
                "pointer": pointer if bound_pointer is not None else {},
                "task_record": candidate,
                "verification_scope": "remote" if record.get("remote", {}).get("proven") is True else "local",
                "remote_status": record.get("remote", {}).get("status", "unproven"),
                "recovery_action": record.get("next_action", "Repair the registered task record and event binding."),
                "missing": [],
                "invalid": invalid,
                "status": "pass" if not invalid else "blocked",
            }
        except (OSError, TaskStateError, ValueError) as exc:
            payload = {
                "format_version": 2,
                "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "active": str(active),
                "pointer": pointer,
                "task_record": {},
                "verification_scope": "local",
                "remote_status": "unproven",
                "recovery_action": "Repair the task selector or task-registry binding.",
                "missing": [],
                "invalid": [str(exc)],
                "status": "blocked",
            }
        if args.format == "json":
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            task_id = payload.get("task_record", {}).get("record", {}).get("task_id", "unresolved")
            print(f"workflow-lifecycle: {payload['status']} task={task_id} invalid={len(payload['invalid'])}")
        return 0 if payload["status"] == "pass" or not args.strict else 1
    if active_state["explicit_idle"] and active_state["pointer_heading_count"] == 0 and not active_state["errors"]:
        payload = {"format_version": 1, "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"), "active": str(active), "pointer": {}, "verification_scope": "local", "remote_status": "unproven", "recovery_action": "Start or select a work item before resuming.", "missing": [], "invalid": [], "lifecycle_state": "idle", "status": "pass"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else "workflow-lifecycle: pass state=idle")
        return 0
    if active_state["errors"]:
        payload = {"format_version": 1, "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"), "active": str(active), "pointer": pointer, "verification_scope": "local", "remote_status": "unproven", "recovery_action": "Repair ACTIVE_WORK structure before reading lifecycle fields.", "missing": [], "invalid": list(active_state["errors"]), "status": "blocked"}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else f"workflow-lifecycle: blocked structural_errors={len(active_state['errors'])}")
        return 1 if args.strict else 0
    required = ("task_id", "trace_id", "execution_epoch", "state_revision", "authority_event", "work_state", "integrity_state", "release_state", "role_plan_id", "primary_owner", "primary_status", "reviewer_owner", "reviewer_status", "validator_owner", "validator_status", "remote_status", "remote_proven", "next_action", "updated_at")
    missing = [key for key in required if not pointer.get(key)]
    allowed = {
        "work_state": {"briefing","active","paused","blocked","validating","closed"},
        "integrity_state": {"unknown","clean","local-validated","offline-validated","stale","drift","conflicted","repairing"},
        "release_state": {"local-only","candidate","ready","released"},
    }
    invalid = [f"{key}={pointer.get(key)!r}" for key, values in allowed.items() if pointer.get(key) and pointer[key] not in values]
    event_text = (hub / "personal-state" / "RECOVERY_EVENTS.md").read_text(encoding="utf-8-sig") if (hub / "personal-state" / "RECOVERY_EVENTS.md").is_file() else ""
    marker = pointer.get("authority_event", "")
    event_section = event_text.split(marker, 1)[1].split("\n## ", 1)[0] if marker and marker in event_text else ""
    event_found = bool(event_section)
    if pointer.get("integrity_state") in {"stale", "drift", "conflicted"}: invalid.append("integrity state blocks a stable claim")
    if not event_found: invalid.append("authority_event not found in RECOVERY_EVENTS.md")
    for key in ("trace_id", "execution_epoch", "state_revision"):
        if pointer.get(key) and pointer[key] not in event_section: invalid.append(f"authority event does not bind {key}")
    expected_transition = {"active": ("briefing", "active"), "paused": ("active", "paused"), "validating": ("active", "validating"), "closed": ("validating", "closed")}
    if pointer.get("work_state") in expected_transition:
        for value in expected_transition[pointer["work_state"]]:
            if f"`{value}`" not in event_section: invalid.append(f"authority event lacks transition evidence for {value}")
    if pointer.get("remote_status") not in {"unproven", "proven"}: invalid.append("remote_status must be unproven or proven")
    if pointer.get("remote_proven") not in {"true", "false"}: invalid.append("remote_proven must be true or false")
    if pointer.get("remote_status") == "proven" and pointer.get("remote_proven") != "true": invalid.append("proven remote status requires remote_proven=true")
    if pointer.get("remote_status") == "unproven" and pointer.get("remote_proven") != "false": invalid.append("unproven remote status requires remote_proven=false")
    if pointer.get("release_state") in {"ready", "released"}:
        receipt = Path(pointer.get("release_receipt", ""))
        if pointer.get("remote_status") != "proven" or pointer.get("remote_proven") != "true":
            invalid.append("ready/released requires remote_status=proven and remote_proven=true")
        receipt_errors = release_receipt_errors(receipt, pointer, hub)
        invalid.extend(receipt_errors)
    resolved = {"completed", "deferred"}
    if pointer.get("primary_status") not in {"planned", "running", "completed", "deferred"}: invalid.append("primary_status must be planned/running/completed/deferred")
    if pointer.get("reviewer_status") not in {"pending", "completed", "deferred"}: invalid.append("reviewer_status must be pending/completed/deferred")
    if pointer.get("validator_status") not in {"pending", "completed", "deferred"}: invalid.append("validator_status must be pending/completed/deferred")
    if pointer.get("work_state") == "active" and pointer.get("primary_status") not in {"planned", "running", "completed", "deferred"}: invalid.append("active requires a primary plan status")
    if pointer.get("work_state") == "closed" and (pointer.get("reviewer_status") not in resolved or pointer.get("validator_status") not in resolved): invalid.append("closed requires resolved reviewer and validator")
    if pointer.get("work_state") == "closed" and (pointer.get("reviewer_owner") == pointer.get("primary_owner") or pointer.get("validator_owner") == pointer.get("primary_owner")): invalid.append("closed requires an independent reviewer and validator owner")
    if (pointer.get("reviewer_status") == "deferred" or pointer.get("validator_status") == "deferred") and pointer.get("release_state") != "local-only": invalid.append("deferred expert gate limits release_state to local-only")
    payload = {"format_version": 1, "checked_at": datetime.now().astimezone().isoformat(timespec="seconds"), "active": str(active), "pointer": pointer, "verification_scope": "remote" if pointer.get("remote_proven") == "true" else "local", "remote_status": pointer.get("remote_status", "unproven"), "recovery_action": pointer.get("next_action", "Read ACTIVE_WORK.md and repair the listed authority gap."), "missing": missing, "invalid": invalid, "status": "pass" if not missing and not invalid else "blocked"}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else f"workflow-lifecycle: {payload['status']} missing={len(missing)} invalid={len(invalid)}")
    return 0 if payload["status"] == "pass" or not args.strict else 1
if __name__ == "__main__": raise SystemExit(main())
