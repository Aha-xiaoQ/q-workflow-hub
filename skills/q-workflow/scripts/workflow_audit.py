#!/usr/bin/env python3
"""Portable structural audit primitives shared by closure and release gates.

This module deliberately owns only local, reproducible checks. Release
evidence, human approval, and remote endpoint proof stay in release_readiness.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from active_work_pointer import inspect_active_work
from workflow_task_state import (
    TaskStateError,
    inspect_task_record,
    resolve_task_record,
    task_event_log_path,
)


@dataclass(frozen=True)
class Finding:
    severity: str
    area: str
    evidence: str
    repair: str


def missing_profile_references(text: str, skill_roots: list[Path]) -> list[str]:
    """Check explicit ``q-skill `references/file.md``` recovery references."""
    missing = []
    for skill, relative in re.findall(r"\b(q-[a-z0-9-]+)\s+`(references/[^`\r\n]+)`", text):
        found = False
        for root in skill_roots:
            base = (root / skill).resolve()
            target = (base / relative).resolve()
            if target.is_relative_to(base) and target.is_file():
                found = True
                break
        if not found:
            missing.append(f"{skill}/{relative}")
    return sorted(set(missing))


def default_user_home() -> Path:
    return Path(os.environ.get("USERPROFILE") or Path.home())


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or default_user_home() / ".codex")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)).replace("\\", "/"): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def default_paths() -> dict[str, Path]:
    profile = read_json(Path(os.environ.get("Q_PROFILE_PATH") or codex_home() / "q-profile.json"))
    this_skill = Path(__file__).resolve().parents[1]
    workflow_root = this_skill.parents[2]
    hub = Path(str(profile.get("hub") or workflow_root.parent / "q-personal-hub")).expanduser()
    repos = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    source_row = repos.get("q-workflow-hub") if isinstance(repos.get("q-workflow-hub"), dict) else {}
    source_value = source_row.get("path") or source_row.get("local_path") or source_row.get("registry_path")
    source_root = Path(source_value).expanduser() if isinstance(source_value, str) and source_value else workflow_root
    source_skill = source_root / "skills" / "q-workflow"
    if not source_skill.is_dir():
        source_skill = this_skill
    return {
        "profile": Path(os.environ.get("Q_PROFILE_PATH") or codex_home() / "q-profile.json"),
        "hub": hub,
        "hub_personal_state": hub / "personal-state",
        "runtime_personal_state": codex_home() / "q-personal-state",
        "runtime_q_workflow": codex_home() / "skills" / "q-workflow",
        "starter_q_workflow": source_skill,
        "standalone_q_workflow": source_skill,
        "reports": hub / "reports",
        "assistant_source": hub / "generated-skills" / "q-assistant-profile",
        "assistant_runtime": codex_home() / "skills" / "q-assistant-profile",
    }


def run_checks(paths: dict[str, Path] | None = None) -> tuple[dict[str, str], list[Finding]]:
    paths = paths or default_paths()
    inventory = {name: str(path) for name, path in paths.items()}
    findings: list[Finding] = []
    required = {
        "profile": paths["profile"],
        "authority state": paths["hub_personal_state"],
        "source q-workflow": paths["starter_q_workflow"],
        "runtime q-workflow": paths["runtime_q_workflow"],
        "base command contract": paths["starter_q_workflow"] / "references" / "base-command-contract.json",
        "closure ledger checker": paths["runtime_q_workflow"] / "scripts" / "closure_ledger_check.py",
        "workflow audit module": paths["runtime_q_workflow"] / "scripts" / "workflow_audit.py",
        "lifecycle contract": paths["starter_q_workflow"] / "references" / "lifecycle-contract.json",
        "lifecycle inspector": paths["runtime_q_workflow"] / "scripts" / "workflow_lifecycle.py",
    }
    for label, path in required.items():
        if not path.exists():
            findings.append(Finding("P1", label, f"missing: {path}", "Restore the declared foundational surface and refresh runtime."))
    for name in ("TODO.md", "TODO_DISPLAY.zh-CN.json", "ACTIVE_WORK.md"):
        source = paths["hub_personal_state"] / name
        runtime = paths["runtime_personal_state"] / name
        if not source.is_file() or not runtime.is_file():
            findings.append(Finding("P1", f"state mirror {name}", f"missing source/runtime pair: {source} -> {runtime}", "Rebuild the runtime mirror from q-profile authority."))
        elif sha256(source) != sha256(runtime):
            findings.append(Finding("P1", f"state mirror {name}", "source and runtime SHA-256 differ", "Run q_base_command.py --audit --sync-runtime."))
    source_tree = tree_hashes(paths["starter_q_workflow"])
    runtime_tree = tree_hashes(paths["runtime_q_workflow"])
    if source_tree and runtime_tree and source_tree != runtime_tree:
        findings.append(Finding("P1", "q-workflow source/runtime", "recursive hashes differ", "Refresh runtime from source after reviewing runtime-newer changes."))
    profile_text = (paths["assistant_source"] / "SKILL.md").read_text(encoding="utf-8-sig") if (paths["assistant_source"] / "SKILL.md").is_file() else ""
    for reference in missing_profile_references(profile_text, [paths["starter_q_workflow"].parent, paths["runtime_q_workflow"].parent]):
        findings.append(Finding("P1", "assistant recovery reference", f"generated profile points at absent skill reference: {reference}", "Restore the referenced skill file or route recovery to an available contract."))
    active = paths["hub_personal_state"] / "ACTIVE_WORK.md"
    if active.is_file():
        active_state = inspect_active_work(active)
        pointer_heading_count = active_state["pointer_heading_count"]
        for error in active_state["errors"]:
            findings.append(Finding(
                "P1",
                "recovery pointer uniqueness",
                error,
                "Keep exactly one executable RECOVERY_POINTER for active focus; allow zero only for the explicit idle template; rename historical envelopes so they cannot match the recovery parser.",
            ))
        pointer = active_state["recovery_pointer"]
        valid_states = {"synced", "local-validated", "stale"}
        if pointer_heading_count == 1 and pointer.get("sync_state") and pointer.get("sync_state") not in valid_states:
            findings.append(Finding("P1", "recovery pointer state", f"sync_state={pointer.get('sync_state')!r}", "Use one declared state: synced, local-validated, or stale."))
        material = pointer.get("task_id")
        if material:
            required_pointer = {"trace_id", "execution_epoch", "state_revision", "authority_event", "work_state", "integrity_state", "release_state", "next_action", "updated_at"}
            missing = sorted(key for key in required_pointer if not pointer.get(key))
            if missing:
                findings.append(Finding("P1", "lifecycle envelope", f"task_id={material}; missing={missing}", "Complete RECOVERY_POINTER v1 and write the matching recovery event."))
            if pointer.get("task_record_path"):
                try:
                    record_path = resolve_task_record(
                        paths["hub"],
                        record_path=Path(pointer["task_record_path"]),
                    )
                    inspection = inspect_task_record(
                        record_path,
                        task_event_log_path(paths["hub"]),
                        pointer=pointer,
                    )
                    for error in inspection["errors"]:
                        findings.append(Finding(
                            "P1",
                            "registered task state",
                            error,
                            "Repair the canonical task record/event binding, then regenerate the ACTIVE_WORK focus view transactionally.",
                        ))
                except (OSError, TaskStateError, ValueError) as exc:
                    findings.append(Finding(
                        "P1",
                        "registered task state",
                        str(exc),
                        "Keep task records directly under personal-state/tasks and regenerate the focus view with q_workflow_manager.py.",
                    ))
            else:
                allowed = {
                    "work_state": {"briefing", "active", "paused", "blocked", "validating", "closed"},
                    "integrity_state": {"unknown", "clean", "local-validated", "offline-validated", "stale", "drift", "conflicted", "repairing"},
                    "release_state": {"local-only", "candidate", "ready", "released"},
                }
                for key, values in allowed.items():
                    if pointer.get(key) and pointer[key] not in values:
                        findings.append(Finding(
                            "P1",
                            "legacy lifecycle axis",
                            f"{key}={pointer[key]!r}",
                            "Use the generic lifecycle axis and preserve domain-specific state under task-record detail.",
                        ))
    return inventory, findings


def run_regression_checks(paths: dict[str, Path] | None = None) -> tuple[dict[str, str], list[Finding]]:
    paths = paths or default_paths()
    inventory, findings = run_checks(paths)
    contract = read_json(paths["starter_q_workflow"] / "references" / "base-command-contract.json")
    commands = contract.get("commands") if isinstance(contract.get("commands"), list) else []
    ids = {row.get("id") for row in commands if isinstance(row, dict)}
    required_ids = {"todo-list", "todo-add", "todo-select", "token-dashboard", "help", "status", "quick-resume"}
    if not required_ids.issubset(ids):
        findings.append(Finding("P1", "base command coverage", f"missing={sorted(required_ids - ids)}", "Restore every exact base-command registration."))
    return inventory, findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("audit", "hygiene", "regression"), default="audit")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    runner = run_regression_checks if args.mode == "regression" else run_checks
    inventory, findings = runner()
    payload = {"mode": args.mode, "status": "pass" if not findings else "attention", "inventory": inventory, "findings": [asdict(item) for item in findings]}
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"workflow-audit: {payload['status']} mode={args.mode} findings={len(findings)}")
        for item in findings:
            print(f"{item.severity} | {item.area} | {item.evidence} | {item.repair}")
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
