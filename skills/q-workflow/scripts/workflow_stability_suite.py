#!/usr/bin/env python3
"""Run Xiao Q foundational workflow contracts.

Use --public-install for isolated public-distribution acceptance. The default
legacy personal-install mode inspects the configured personal installation and
requires its personal installer and populated state; it is not a cold-start gate.

This core suite intentionally excludes company variants, legacy standalone
copies, historical release packets, and signoff evidence. Those belong in
variant/release suites. Any foundational failure returns non-zero by default;
`--strict` remains as a compatibility flag and cannot turn failures into pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    evidence: str
    repair: str


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))


def profile_path() -> Path:
    return Path(os.environ.get("Q_PROFILE_PATH", str(codex_home() / "q-profile.json")))


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"JSON root must be object: {path}")
    return payload


def normalize_detail_layout(value: Any) -> str:
    """Ignore clause wrapping after Chinese punctuation; preserve other boundaries."""
    lines = [line.strip() for line in str(value).splitlines() if line.strip()]
    if not lines:
        return ""
    normalized = lines[0]
    for line in lines[1:]:
        if normalized.endswith(("。", "！", "？", "；")):
            normalized += line
        else:
            normalized += "\n" + line
    return normalized


def resolve_personal_hub(profile: dict[str, Any], profile_file: Path, state_hub: Path) -> Path:
    """Resolve the personal install/help hub independently from state authority."""
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
        raise RuntimeError(f"q-profile contains ambiguous personal hubs: {unique}")
    if existing:
        return existing[0]
    if not candidates:
        return state_hub
    raise RuntimeError(f"configured personal hub does not exist: {unique[0]} ({profile_file})")


def resolve_paths() -> dict[str, Path]:
    pfile = profile_path()
    profile = read_json(pfile)
    hub_value = profile.get("hub")
    if not isinstance(hub_value, str) or not hub_value.strip():
        raise RuntimeError(f"q-profile hub is missing: {pfile}")
    hub = Path(hub_value).resolve()
    if not hub.is_dir():
        raise RuntimeError(f"q-profile hub does not exist: {hub}")
    personal_hub = resolve_personal_hub(profile, pfile, hub)
    projects_value = profile.get("projects")
    projects = Path(projects_value).resolve() if isinstance(projects_value, str) and projects_value.strip() else hub.parent
    repos = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    workflow_repo = repos.get("q-workflow-hub") if isinstance(repos.get("q-workflow-hub"), dict) else {}
    workflow_value = workflow_repo.get("path") or workflow_repo.get("local_path") or workflow_repo.get("registry_path")
    workflow_root = Path(workflow_value).resolve() if isinstance(workflow_value, str) and workflow_value.strip() else projects / "q-workflow-hub"
    return {
        "profile": pfile,
        "hub": hub,
        "personal_hub": personal_hub,
        "workflow_root": workflow_root,
        "source_skills": workflow_root / "skills",
        "bootstrap_skills": personal_hub / "bootstrap" / "skills",
        "runtime_skills": codex_home() / "skills",
        "state_source": hub / "personal-state",
        "state_runtime": codex_home() / "q-personal-state",
        "assistant_source": personal_hub / "generated-skills" / "q-assistant-profile",
        "assistant_runtime": codex_home() / "skills" / "q-assistant-profile",
    }


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(root)).replace("\\", "/"): hash_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def compare_trees(check_id: str, source: Path, target: Path) -> Check:
    source_hashes = tree_hashes(source)
    target_hashes = tree_hashes(target)
    if not source_hashes:
        return Check(check_id, "fail", f"source missing or empty: {source}", "Restore the canonical source tree.")
    if source_hashes == target_hashes:
        return Check(check_id, "pass", f"{len(source_hashes)} files match: {source} -> {target}", "none")
    paths = sorted(set(source_hashes) | set(target_hashes))
    drift = [
        name for name in paths
        if source_hashes.get(name) != target_hashes.get(name)
    ]
    preview = ", ".join(drift[:8]) + (f" (+{len(drift) - 8})" if len(drift) > 8 else "")
    return Check(check_id, "fail", f"{len(drift)} file(s) drift: {preview}", f"Sync {source} to {target} and rerun.")


COMMAND_TIMEOUT_SECONDS = 60


def run_json(command: list[str]) -> tuple[int, dict[str, Any], str]:
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=COMMAND_TIMEOUT_SECONDS, check=False)
    text = completed.stdout.strip() or completed.stderr.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = {}
    return completed.returncode, payload, text


def check_base_command(paths: dict[str, Path], root: Path, suffix: str) -> list[Check]:
    script = root / "scripts" / "q_base_command.py"
    if not script.is_file():
        return [Check(f"base-script-{suffix}", "fail", f"missing: {script}", "Install the complete q-workflow tree.")]
    checks: list[Check] = []
    rc, payload, raw = run_json([sys.executable, str(script), "--self-test", "--format", "json"])
    self_test_passed = rc == 0 and payload.get("status") == "pass"
    checks.append(Check(
        f"base-self-test-{suffix}",
        "pass" if self_test_passed else "fail",
        f"rc={rc}; cases={payload.get('cases')}; failures={payload.get('failures', raw[:300])}",
        "none" if self_test_passed else "Repair registry/parser fixtures and rerun.",
    ))
    replay_script = root / "scripts" / "base_command_surface_replay.py"
    if replay_script.is_file():
        rc, payload, raw = run_json([sys.executable, str(replay_script), "--root", str(root)])
        replay_passed = rc == 0 and payload.get("status") == "pass" and payload.get("cases") == 4
        checks.append(Check(
            f"base-surface-replay-{suffix}",
            "pass" if replay_passed else "fail",
            f"rc={rc}; cases={payload.get('cases')}; failures={payload.get('failures', raw[:300])}",
            "none" if replay_passed else "Repair the four executable user-visible command surfaces and open receipts.",
        ))
    else:
        checks.append(Check(f"base-surface-replay-{suffix}", "fail", f"missing: {replay_script}", "Restore the four-command surface replay."))
    rc, payload, raw = run_json([sys.executable, str(script), "--input", "TODO", "--format", "json"])
    correct_authority = str(payload.get("authority", "")).lower() == str(paths["state_source"] / "TODO.md").lower()
    open_count = payload.get("open_count")
    mirror = payload.get("mirror") if isinstance(payload.get("mirror"), dict) else {}
    todo_chat = payload.get("surface", {}).get("chat_text", "")
    item_ids = [item.get("item_id") for item in payload.get("items", [])]
    display_items = payload.get("display_items", []) if isinstance(payload.get("display_items"), list) else []
    visible_items = all(f"\n{index}. {item_id} /" in todo_chat for index, item_id in enumerate(item_ids, 1))
    def compact_detail(detail: str) -> str:
        first_sentence = detail.split("。", 1)[0].strip() or detail.strip()
        return first_sentence if len(first_sentence) <= 76 else first_sentence[:76].rstrip() + "…"

    visible_details = all(
        isinstance(item, dict) and isinstance(item.get("detail"), str)
        and compact_detail(item["detail"]) in todo_chat
        for item in display_items
    )
    no_menu = all(phrase not in todo_chat for phrase in ("原始记录：", "回复编号", "1~", "1～", "Recommended Next", "Next action:", "Completion gate:"))
    token = payload.get("context_token")
    select_rc, select_payload, select_raw = run_json([
        sys.executable, str(script), "--input", "1", "--context", "todo-list", "--context-token", str(token), "--format", "json",
    ])
    selection_chat = select_payload.get("surface", {}).get("chat_text", "")
    selected_display = select_payload.get("selected_display")
    selected_detail = select_payload.get("selected_detail")
    selection_localized = (
        select_rc == 0
        and isinstance(selected_display, dict)
        and isinstance(selected_detail, str)
        and bool(selected_detail.strip())
        and normalize_detail_layout(selected_display.get("detail", "")) == normalize_detail_layout(selected_detail)
        and normalize_detail_layout(selected_detail) in normalize_detail_layout(selection_chat)
        and "\n详情：\n" in selection_chat
        and "原始记录：" not in selection_chat
        and "Next action:" not in selection_chat
    )
    passed = (
        rc == 0
        and correct_authority
        and isinstance(open_count, int)
        and open_count == len(item_ids)
        and mirror.get("match") is True
        and todo_chat.startswith("小Q工作流 / q-assistant-profile / TODO\n")
        and visible_items
        and visible_details
        and no_menu
        and selection_localized
    )
    checks.append(Check(
        f"todo-e2e-{suffix}",
        "pass" if passed else "fail",
        f"rc={rc}; authority={payload.get('authority')}; open={open_count}; mirror={mirror.get('match')}; visible={visible_items and visible_details}; no_menu={no_menu}; selection_localized={selection_localized}; raw={raw[:200]}; select={select_raw[:160]}",
        "none" if passed else "Resolve q-profile authority, rebuild runtime state mirror, and rerun.",
    ))
    e2e_cases = [
        ("help", lambda value: isinstance(value.get("commands"), list) and len(value["commands"]) >= 7),
        ("status", lambda value: bool(value.get("current_focus")) and value.get("authority", "").lower() == str(paths["state_source"] / "ACTIVE_WORK.md").lower()),
        ("小Q", lambda value: value.get("phase") == "A" and value.get("recency_checked") is False and value.get("pointer_confidence") == "partial" and bool(value.get("current_focus"))),
        ("checkpoint", lambda value: value.get("checkpoint_status") == "action-required" and value.get("write_status") == "not-written"),
        ("TOKEN", lambda value: value.get("command_id") == "token-dashboard" and Path(value.get("script", "")).is_file()),
        ("更新skill的标准", lambda value: value.get("required_skill") == "q-skill-creation"),
    ]
    e2e_cases = [
        ("帮助", lambda value: (
            value.get("guide_kind") == "html"
            and Path(value.get("guide", "")).is_file()
            and "一分钟试跑" in value.get("surface", {}).get("chat_text", "")
            and "1～" not in value.get("surface", {}).get("chat_text", "")
        )),
        ("status", lambda value: bool(value.get("current_focus")) and value.get("authority", "").lower() == str(paths["state_source"] / "ACTIVE_WORK.md").lower()),
        ("小Q", lambda value: (
            value.get("phase") == "A"
            and value.get("recency_checked") is True
            and value.get("pointer_confidence") in {"confirmed", "partial"}
            and value.get("surface", {}).get("chat_text", "").startswith("【小Q工作流 | 快速恢复 】")
            and "最近：" in value.get("surface", {}).get("chat_text", "")
        )),
        ("checkpoint", lambda value: value.get("checkpoint_status") == "action-required" and value.get("write_status") == "not-written"),
        ("TOKEN", lambda value: (
            value.get("command_id") == "token-dashboard"
            and Path(value.get("script", "")).is_file()
            and Path(value.get("dashboard", "")).is_file()
            and value.get("surface", {}).get("chat_text", "").startswith("小Q工作流 / q-workflow / TOKEN\n")
            and value.get("surface", {}).get("chat_text", "").count("\n") == 4
        )),
        ("更新skill的标准", lambda value: value.get("required_skill") == "q-skill-creation"),
    ]
    for value, predicate in e2e_cases:
        rc, payload, raw = run_json([sys.executable, str(script), "--input", value, "--format", "json"])
        passed = rc == 0 and predicate(payload)
        checks.append(Check(
            f"{payload.get('command_id', value)}-e2e-{suffix}",
            "pass" if passed else "fail",
            f"input={value}; rc={rc}; handler={payload.get('handler')}; raw={raw[:180]}",
            "none" if passed else "Repair the executable command handler and output contract.",
        ))
    token_script = script.parent / "token_usage.py"
    token_self_rc, token_self_payload, token_self_raw = run_json([
        sys.executable, str(token_script), "--self-test", "--format", "json",
    ])
    rc, payload, raw = run_json([sys.executable, str(token_script), "--codex-home", str(codex_home()), "--format", "json"])
    token_helper_ok = (
        token_self_rc == 0
        and token_self_payload.get("status") == "pass"
        and rc == 0
        and isinstance(payload.get("current"), dict)
    )
    checks.append(Check(
        f"token-helper-e2e-{suffix}",
        "pass" if token_helper_ok else "fail",
        f"self_test_rc={token_self_rc}; self_test={token_self_payload.get('status', token_self_raw[:80])}; rc={rc}; current={isinstance(payload.get('current'), dict)}; raw={raw[:180]}",
        "none" if token_helper_ok else "Repair token_usage.py runtime execution or return a structured unavailable result.",
    ))
    return checks


def check_state(paths: dict[str, Path]) -> list[Check]:
    checks = []
    for name in ("TODO.md", "TODO_DISPLAY.zh-CN.json", "ACTIVE_WORK.md"):
        source = paths["state_source"] / name
        runtime = paths["state_runtime"] / name
        if source.is_file() and runtime.is_file() and hash_file(source) == hash_file(runtime):
            checks.append(Check(f"state-{name}", "pass", f"hash match: {source} -> {runtime}", "none"))
        else:
            checks.append(Check(f"state-{name}", "fail", f"missing or drift: {source} -> {runtime}", "Run q_base_command.py --audit --sync-runtime."))
    manifest = paths["state_runtime"] / "runtime-manifest.json"
    try:
        data = read_json(manifest)
        rows = data.get("files") if isinstance(data.get("files"), list) else []
        row_map = {row.get("name"): row for row in rows if isinstance(row, dict)}
        expected_names = {"TODO.md", "TODO_DISPLAY.zh-CN.json", "ACTIVE_WORK.md"}
        hashes_valid = set(row_map) == expected_names
        for name in expected_names:
            source = paths["state_source"] / name
            runtime = paths["state_runtime"] / name
            row = row_map.get(name, {})
            hashes_valid = hashes_valid and source.is_file() and runtime.is_file()
            hashes_valid = hashes_valid and row.get("source_sha256") == hash_file(source)
            hashes_valid = hashes_valid and row.get("runtime_sha256") == hash_file(runtime)
        todo_text = (paths["state_source"] / "TODO.md").read_text(encoding="utf-8-sig")
        open_section = todo_text.split("## Open", 1)[1].split("## ", 1)[0]
        open_ids = [line.split("|", 2)[1].strip() for line in open_section.splitlines() if line.strip().startswith("- [ ]") and line.count("|") >= 2]
        valid = (
            data.get("policy") == "read-only-rebuildable-mirror"
            and data.get("authority") == str(paths["state_source"])
            and data.get("todo_open_ids") == open_ids
            and isinstance(data.get("source_revision"), str)
            and bool(data.get("source_revision"))
            and hashes_valid
        )
    except RuntimeError:
        valid = False
    checks.append(Check("state-manifest", "pass" if valid else "fail", str(manifest), "none" if valid else "Rebuild the runtime state manifest from q-profile authority."))
    return checks


def check_expert_registry(paths: dict[str, Path]) -> Check:
    registry = paths["source_skills"] / "q-agent-roster" / "references" / "expert-registry.json"
    human = paths["source_skills"] / "q-agent-roster" / "references" / "agent-registry.md"
    try:
        experts = read_json(registry).get("experts")
        text = human.read_text(encoding="utf-8-sig")
        roster_root = paths["source_skills"] / "q-agent-roster"
        active_text = "\n".join(
            path.read_text(encoding="utf-8-sig")
            for path in roster_root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml"}
        )
    except (RuntimeError, OSError) as exc:
        return Check("expert-identity", "fail", str(exc), "Restore machine and human expert registries.")
    failures = []
    if not isinstance(experts, list) or len(experts) != 7:
        failures.append("registry must contain seven experts")
    else:
        ids = set()
        for expert in experts:
            if not isinstance(expert, dict):
                failures.append("invalid expert row")
                continue
            expert_id = expert.get("id")
            english = expert.get("english")
            chinese = expert.get("chinese")
            if expert_id in ids or not all(isinstance(value, str) and value for value in (expert_id, english, chinese)):
                failures.append(f"invalid identity row: {expert}")
            ids.add(expert_id)
            if f"| {english} | {chinese} |" not in text:
                failures.append(f"human registry drift: {english}/{chinese}")
            pairs = set(re.findall(re.escape(english) + r"\s*\(([^)]+)\)", active_text))
            if pairs and pairs != {chinese}:
                failures.append(f"active roster identity drift: {english} -> {sorted(pairs)}")
            skill_text = (roster_root / "SKILL.md").read_text(encoding="utf-8-sig")
            if f"{english} ({chinese})" not in skill_text:
                failures.append(f"SKILL roster missing: {english} ({chinese})")
    return Check("expert-identity", "pass" if not failures else "fail", "; ".join(failures) or "seven stable identities match", "none" if not failures else "Align agent-registry.md to expert-registry.json.")


def check_skill_trigger(paths: dict[str, Path]) -> Check:
    skill = paths["source_skills"] / "q-skill-creation" / "SKILL.md"
    try:
        head = skill.read_text(encoding="utf-8-sig").split("---", 2)[1].casefold()
    except (OSError, IndexError) as exc:
        return Check("skill-maintenance-trigger", "fail", str(exc), "Restore q-skill-creation frontmatter.")
    terms = ("create", "update", "review", "stabilize", "release", "rename")
    missing = [term for term in terms if term not in head]
    return Check("skill-maintenance-trigger", "pass" if not missing else "fail", f"missing={missing}", "none" if not missing else "Make skill-maintenance intents discoverable in frontmatter.")


def windows_powershell_test_env() -> dict[str, str]:
    """Use native child-host module defaults without changing the parent."""
    return {
        key: value for key, value in os.environ.items()
        if os.name != "nt" or key.casefold() != "psmodulepath"
    }


def injected_failure_reached(result: subprocess.CompletedProcess, marker: str) -> bool:
    """An unrelated launch/import failure is not rollback evidence."""
    return result.returncode != 0 and marker in (
        (result.stdout or "") + "\n" + (result.stderr or "")
    )


def check_installer_transaction(paths: dict[str, Path]) -> list[Check]:
    installer = paths["personal_hub"] / "bootstrap" / "install-personal-skills.ps1"
    if not installer.is_file():
        return [Check("installer-transaction", "fail", f"missing: {installer}", "Restore the personal installer.")]
    with tempfile.TemporaryDirectory() as temp_dir:
        home = Path(temp_dir) / "codex-home"
        skills = home / "skills"
        skills.mkdir(parents=True)
        planned = sorted(path.name for path in paths["bootstrap_skills"].iterdir() if path.is_dir()) + ["q-assistant-profile"]
        for name in planned:
            target = skills / name
            target.mkdir()
            (target / "preinstall.marker").write_text(name, encoding="utf-8")
        profile = {
            "hub": str(paths["hub"]),
            "custom_top_level": {"preserve": True},
            "repositories": {
                "custom-repo": {
                    "path": "X:/custom",
                    "special": "keep",
                    "deep": {"one": {"two": {"three": {"four": {"five": [{"six": "keep"}]}}}}},
                },
                "q-workflow-hub": {"custom_nested": "keep"},
            },
        }
        (home / "q-profile.json").write_text(json.dumps(profile, ensure_ascii=False), encoding="utf-8")
        before = tree_hashes(skills)
        env = windows_powershell_test_env()
        env["Q_WORKFLOW_TEST_FAIL_AFTER_SKILL"] = "2"
        failed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(installer), "-CodexHome", str(home)],
            text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120, env=env, check=False,
        )
        after = tree_hashes(skills)
        rollback_reached = injected_failure_reached(failed, "Injected installer transaction failure after skill 2.")
        rollback_ok = rollback_reached and before == after
        rollback_check = Check(
            "installer-package-rollback", "pass" if rollback_ok else "fail",
            f"injected_rc={failed.returncode}; injection_reached={rollback_reached}; restored={before == after}",
            "none" if rollback_ok else "Retain all backups until the final gate and roll back in reverse order.",
        )
        env.pop("Q_WORKFLOW_TEST_FAIL_AFTER_SKILL", None)
        state_runtime = home / "q-personal-state"
        state_runtime.mkdir(parents=True, exist_ok=True)
        (state_runtime / "TODO.md").write_bytes((paths["state_source"] / "TODO.md").read_bytes())
        (state_runtime / "ACTIVE_WORK.md").write_text("# Active Work\n\n## Current Focus\n\nPre-install sentinel.\n", encoding="utf-8")
        before_state = tree_hashes(state_runtime)
        env["Q_WORKFLOW_TEST_FAIL_AFTER_STATE_SYNC"] = "1"
        state_failed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(installer), "-CodexHome", str(home)],
            text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120, env=env, check=False,
        )
        state_reached = injected_failure_reached(state_failed, "Injected installer transaction failure after runtime-state sync.")
        state_rollback_ok = state_reached and before_state == tree_hashes(state_runtime)
        state_rollback_check = Check(
            "installer-runtime-state-rollback", "pass" if state_rollback_ok else "fail",
            f"injected_rc={state_failed.returncode}; injection_reached={state_reached}; restored={before_state == tree_hashes(state_runtime)}",
            "none" if state_rollback_ok else "Include runtime personal state and manifest in installer rollback.",
        )
        env.pop("Q_WORKFLOW_TEST_FAIL_AFTER_STATE_SYNC", None)
        env["Q_WORKFLOW_TEST_FAIL_BACKUP_CLEANUP_AT"] = "2"
        succeeded = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(installer), "-CodexHome", str(home)],
            text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120, env=env, check=False,
        )
        try:
            installed_profile = read_json(home / "q-profile.json")
            repos = installed_profile.get("repositories", {})
            custom_repo = repos.get("custom-repo", {}) if isinstance(repos, dict) else {}
            managed_repo = repos.get("q-workflow-hub", {}) if isinstance(repos, dict) else {}
            preserve_ok = (
                succeeded.returncode == 0
                and installed_profile.get("custom_top_level") == {"preserve": True}
                and custom_repo.get("special") == "keep"
                and custom_repo.get("deep", {}).get("one", {}).get("two", {}).get("three", {}).get("four", {}).get("five") == [{"six": "keep"}]
                and managed_repo.get("custom_nested") == "keep"
                and all((skills / name).is_dir() and not (skills / name / "preinstall.marker").exists() for name in planned)
            )
        except RuntimeError:
            preserve_ok = False
        preservation_check = Check(
            "installer-profile-preservation", "pass" if preserve_ok else "fail",
            f"success_rc={succeeded.returncode}; unknown repository and nested fields preserved={preserve_ok}"
            + (f"; installation_error={(succeeded.stderr or succeeded.stdout)[-1200:]}" if succeeded.returncode != 0 else ""),
            "none" if preserve_ok else (
                "Resolve the installation execution error before judging profile preservation."
                if succeeded.returncode != 0 else "Merge managed fields into the existing repository registry."
            ),
        )
        return [rollback_check, state_rollback_check, preservation_check]


def check_operational_helpers(paths: dict[str, Path]) -> list[Check]:
    runtime = paths["runtime_skills"] / "q-workflow" / "scripts"
    audit = runtime / "workflow_audit.py"
    closure = runtime / "closure_ledger_check.py"
    manager = runtime / "q_workflow_manager.py"
    checks: list[Check] = []
    rc, payload, raw = run_json([sys.executable, str(audit), "--mode", "audit", "--format", "json"])
    audit_ok = rc == 0 and payload.get("status") == "pass" and payload.get("findings") == []
    checks.append(Check(
        "workflow-audit-smoke", "pass" if audit_ok else "fail",
        f"rc={rc}; status={payload.get('status')}; findings={len(payload.get('findings', [])) if isinstance(payload.get('findings'), list) else 'invalid'}; raw={raw[:180]}",
        "none" if audit_ok else "Repair structural audit dependencies or its authoritative-path checks.",
    ))
    rc, payload, raw = run_json([
        sys.executable, str(closure), "--task-id", "q-workflow-foundation-v3", "--expect", "closed", "--strict", "--format", "json",
    ])
    closure_ok = rc == 0 and payload.get("status") == "PASS"
    checks.append(Check(
        "closure-ledger-smoke", "pass" if closure_ok else "fail",
        f"rc={rc}; status={payload.get('status')}; raw={raw[:180]}",
        "none" if closure_ok else "Repair closure-ledger imports, authority paths, or stale completion records.",
    ))
    manager_result = subprocess.run(
        [sys.executable, str(manager), "--self-test", "--format", "json"],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    ) if manager.is_file() else None
    try:
        manager_payload = json.loads(manager_result.stdout) if manager_result is not None else {}
    except json.JSONDecodeError:
        manager_payload = {}
    manager_ok = manager_result is not None and manager_result.returncode == 0 and manager_payload.get("status") == "pass"
    checks.append(Check(
        "workflow-manager-transaction-self-test", "pass" if manager_ok else "fail",
        f"rc={manager_result.returncode if manager_result is not None else 'missing'}; status={manager_payload.get('status')}; cases={manager_payload.get('cases')}",
        "none" if manager_ok else "Repair the manager planning, compare-and-swap, rollback, readback, or surface-manifest path.",
    ))
    rc, payload, raw = run_json([
        sys.executable,
        str(manager),
        "--format",
        "json",
        "surfaces",
        "--tier",
        "core",
        "--strict",
    ]) if manager.is_file() else (127, {}, "manager missing")
    core_surface_ok = rc == 0 and payload.get("summary", {}).get("status") == "pass"
    checks.append(Check(
        "core-surface-registry", "pass" if core_surface_ok else "fail",
        f"rc={rc}; status={payload.get('summary', {}).get('status')}; failures={payload.get('summary', {}).get('failures')}; raw={raw[:180]}",
        "none" if core_surface_ok else "Reconcile every core skill through the profile-resolved surface registry.",
    ))
    return checks


def check_lifecycle_and_expert_routes(paths: dict[str, Path]) -> list[Check]:
    runtime = paths["runtime_skills"] / "q-workflow" / "scripts"
    lifecycle = runtime / "workflow_lifecycle.py"
    scenarios = runtime / "workflow_stability_scenarios.py"
    checks: list[Check] = []
    rc, payload, raw = run_json([sys.executable, str(lifecycle), "--strict", "--format", "json"])
    checks.append(Check("lifecycle-envelope", "pass" if rc == 0 and payload.get("status") == "pass" else "fail", f"rc={rc}; status={payload.get('status')}; missing={payload.get('missing')}; invalid={payload.get('invalid')}", "Add a complete RECOVERY_POINTER v1 and matching event before claiming a material task stable."))
    rc, payload, raw = run_json([sys.executable, str(scenarios)])
    checks.append(Check("stability-scenario-corpus", "pass" if rc == 0 and payload.get("status") == "pass" else "fail", f"rc={rc}; failures={payload.get('failures')}; remote={payload.get('remote_status')}; raw={raw[:180]}", "Repair the lifecycle contract or expert routing matrix; remote remains unproven without endpoint fetch evidence."))
    return checks


def check_public_updater_transaction(paths: dict[str, Path]) -> Check:
    updater = paths["workflow_root"] / "scripts" / "sync-workflow-bootstrap.ps1"
    if not updater.is_file():
        return Check("public-updater-rollback", "fail", f"missing: {updater}", "Restore the public bootstrap updater.")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        hub = root / "hub"
        home = root / "home"
        bootstrap = hub / "bootstrap" / "skills" / "q-workflow"
        runtime = home / "skills" / "q-workflow"
        bootstrap.mkdir(parents=True)
        runtime.mkdir(parents=True)
        (bootstrap / "marker.txt").write_text("bootstrap-before", encoding="utf-8")
        (runtime / "marker.txt").write_text("runtime-before", encoding="utf-8")
        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(updater),
             "-WorkflowHubPath", str(hub), "-CodexHome", str(home), "-InstallRuntime",
             "-Skills", "q-workflow", "q-agent-roster", "-TestFailAfterSwitch", "2"],
            text=True, capture_output=True, encoding="utf-8", errors="replace", timeout=120,
            env=windows_powershell_test_env(), check=False,
        )
        restored = (
            (bootstrap / "marker.txt").read_text(encoding="utf-8") == "bootstrap-before"
            and (runtime / "marker.txt").read_text(encoding="utf-8") == "runtime-before"
        )
        injection_reached = injected_failure_reached(result, "Injected package transaction failure after switch 2.")
        ok = injection_reached and restored
        return Check(
            "public-updater-rollback", "pass" if ok else "fail",
            f"injected_rc={result.returncode}; injection_reached={injection_reached}; restored={restored}",
            "none" if ok else "Stage and hash the whole package, then restore switched directories on failure.",
        )


def run_round(paths: dict[str, Path], index: int) -> list[Check]:
    checks: list[Check] = [
        compare_trees(f"q-workflow-source-bootstrap-r{index}", paths["source_skills"] / "q-workflow", paths["bootstrap_skills"] / "q-workflow"),
        compare_trees(f"q-workflow-bootstrap-runtime-r{index}", paths["bootstrap_skills"] / "q-workflow", paths["runtime_skills"] / "q-workflow"),
        compare_trees(f"assistant-source-runtime-r{index}", paths["assistant_source"], paths["assistant_runtime"]),
        compare_trees(f"agent-roster-source-bootstrap-r{index}", paths["source_skills"] / "q-agent-roster", paths["bootstrap_skills"] / "q-agent-roster"),
        compare_trees(f"agent-roster-bootstrap-runtime-r{index}", paths["bootstrap_skills"] / "q-agent-roster", paths["runtime_skills"] / "q-agent-roster"),
        compare_trees(f"skill-creation-source-bootstrap-r{index}", paths["source_skills"] / "q-skill-creation", paths["bootstrap_skills"] / "q-skill-creation"),
        compare_trees(f"skill-creation-bootstrap-runtime-r{index}", paths["bootstrap_skills"] / "q-skill-creation", paths["runtime_skills"] / "q-skill-creation"),
        check_expert_registry(paths),
        check_skill_trigger(paths),
    ]
    checks.extend(check_state(paths))
    checks.extend(check_base_command(paths, paths["source_skills"] / "q-workflow", f"source-r{index}"))
    checks.extend(check_base_command(paths, paths["runtime_skills"] / "q-workflow", f"runtime-r{index}"))
    return checks


def render_report(paths: dict[str, Path], rounds: int, checks: list[Check]) -> str:
    failures = [check for check in checks if check.status != "pass"]
    lines = [
        "# Q Workflow Foundational Contract Report",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Rounds: {rounds}",
        f"Status: {'pass' if not failures else 'blocked'}",
        f"Checks: {len(checks)} | Failures: {len(failures)}",
        f"Authority: {paths['state_source']}",
        "",
        "| Check | Status | Evidence | Repair |",
        "|---|---|---|---|",
    ]
    for check in checks:
        evidence = check.evidence.replace("|", "\\|").replace("\n", " ")
        repair = check.repair.replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {check.check_id} | {check.status} | {evidence} | {repair} |")
    lines.extend([
        "",
        "Foundational failures are never waived by omitting `--strict`. Variant, release,",
        "public/private, and signoff checks remain separate higher-tier suites.",
    ])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--status-output", type=Path)
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Compatibility flag; foundational failures are always strict.")
    parser.add_argument("--public-install", action="store_true", help="Run isolated public installer, recovery, updater and regression contracts.")
    parser.add_argument("--fixture-root", type=Path, help="Parent directory for disposable public-install fixtures (required in public mode).")
    args = parser.parse_args(argv)
    if args.rounds < 2:
        parser.error("--rounds must be at least 2")
    if args.public_install:
        if args.fixture_root is None:
            parser.error("--public-install requires --fixture-root; no implicit personal or system-temp writes")
        sys.dont_write_bytecode = True
        from workflow_public_install_suite import run_public_install
        return run_public_install(Path(__file__).resolve().parents[3], args)
    try:
        paths = resolve_paths()
        checks = []
        for index in range(1, args.rounds + 1):
            checks.extend(run_round(paths, index))
        checks.extend(check_installer_transaction(paths))
        checks.extend(check_operational_helpers(paths))
        checks.extend(check_lifecycle_and_expert_routes(paths))
        checks.append(check_public_updater_transaction(paths))
        report = render_report(paths, args.rounds, checks)
        failures = [check for check in checks if check.status != "pass"]
        status = {
            "status": "pass" if not failures else "blocked",
            "checks": len(checks),
            "failures": len(failures),
            "authority": str(paths["state_source"]),
        }
    except Exception as exc:  # noqa: BLE001 - foundational suite must fail closed
        report = f"# Q Workflow Foundational Contract Report\n\nStatus: blocked\n\nFatal: {exc}\n"
        status = {"status": "blocked", "checks": 0, "failures": 1, "error": str(exc)}
    if args.output and not args.check_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    if args.status_output and not args.check_only:
        args.status_output.parent.mkdir(parents=True, exist_ok=True)
        args.status_output.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.stdout or args.check_only:
        print(report, end="")
        print(json.dumps(status, ensure_ascii=False))
    return 0 if status["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
