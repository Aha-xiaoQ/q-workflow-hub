#!/usr/bin/env python3
"""Replay the four Xiao Q foundational command surfaces end to end."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


DETAIL_SECTION_PREFIXES = ("当前状态：", "下一步：", "证据：", "完成条件：")


def normalize_detail_layout(value: Any) -> str:
    """Join only the known Chinese detail sections; preserve other boundaries."""
    lines = [line.strip() for line in str(value).splitlines() if line.strip()]
    if not lines:
        return ""
    normalized = lines[0]
    for line in lines[1:]:
        if normalized.endswith(("。", "！", "？", "；")) and line.startswith(DETAIL_SECTION_PREFIXES):
            normalized += line
        else:
            normalized += "\n" + line
    return normalized


def run_json(script: Path, value: str, env: dict[str, str], open_ui: bool = False, extra_args: list[str] | None = None) -> dict[str, Any]:
    command = [sys.executable, str(script), "--input", value, "--format", "json"]
    if open_ui:
        command.append("--open-ui")
    if extra_args:
        command.extend(extra_args)
    completed = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=60,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"{value}: rc={completed.returncode}: {completed.stderr or completed.stdout}")
    return json.loads(completed.stdout)


def replay(root: Path) -> dict[str, Any]:
    script = root / "scripts" / "q_base_command.py"
    failures: list[str] = []
    if normalize_detail_layout("a\n b") == normalize_detail_layout("ab"):
        failures.append("detail layout normalization collapsed an ASCII word boundary")
    with tempfile.TemporaryDirectory(prefix="q-base-surface-replay-") as temp_dir:
        base = Path(temp_dir)
        codex_home = base / "codex-home"
        hub = base / "hub"
        state = hub / "personal-state"
        state.mkdir(parents=True)
        codex_home.mkdir(parents=True)
        (codex_home / "q-profile.json").write_text(json.dumps({"hub": str(hub)}), encoding="utf-8")
        (hub / "FIRST_RUN_GUIDE.zh-CN.html").write_text("<html><title>小Q工作流入门帮助</title></html>", encoding="utf-8")
        (state / "ASSISTANT_HELP.md").write_text("# 助手帮助\n", encoding="utf-8")
        (state / "TODO.md").write_text(
            "# TODO\n\nUpdated: 2026-07-13\n\n## Open\n"
            "- [ ] 2026-07-13 | first | First task. Next action: perform action one. Completion gate: evidence one.\n"
            "- [ ] 2026-07-13 | second | Second task. Next action: perform action two. Completion gate: evidence two.\n\n"
            "## Done\n",
            encoding="utf-8",
        )
        (state / "TODO_DISPLAY.zh-CN.json").write_text(
            json.dumps({
                "version": 1,
                "language": "zh-CN",
                "items": {
                    "first": {"name": "第一项待办", "summary": "下一步执行动作一；完成条件是证据一。", "detail": "当前状态：第一项待办。下一步：执行动作一。证据：证据一。完成条件：形成第一项闭环。", "source_fingerprint": hashlib.sha256("First task. Next action: perform action one. Completion gate: evidence one.".encode("utf-8")).hexdigest()},
                    "second": {"name": "第二项待办", "summary": "下一步执行动作二；完成条件是证据二。", "detail": "当前状态：第二项待办。下一步：执行动作二。证据：证据二。完成条件：形成第二项闭环。", "source_fingerprint": hashlib.sha256("Second task. Next action: perform action two. Completion gate: evidence two.".encode("utf-8")).hexdigest()},
                },
            }, ensure_ascii=False),
            encoding="utf-8",
        )
        (state / "ACTIVE_WORK.md").write_text(
            "# Active Work\n\n## Current Focus\n\nSurface replay.\n\n## RECOVERY_POINTER v1\n\n"
            "task_id: surface-replay\nwork_state: active\nintegrity_state: test\nrelease_state: local-only\n"
            "active_project: fixture\npath: C:\\\\fixture\nlatest_verified_note: fixture note\nnext_action: verify\n",
            encoding="utf-8",
        )
        receipt = base / "open-receipt.txt"
        env = os.environ.copy()
        env["CODEX_HOME"] = str(codex_home)
        env["Q_PROFILE_PATH"] = str(codex_home / "q-profile.json")
        env["Q_COMMAND_OPEN_RECEIPT"] = str(receipt)

        sync = subprocess.run(
            [sys.executable, str(script), "--sync-runtime", "--audit", "--format", "json"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=30,
            check=False,
            env=env,
        )
        if sync.returncode != 0:
            failures.append(f"runtime sync failed: {sync.stderr or sync.stdout}")

        todo = run_json(script, "TODO", env)
        todo_chat = todo.get("surface", {}).get("chat_text", "")
        if todo.get("open_count") != 2 or "Next action:" in todo_chat or "Completion gate:" in todo_chat:
            failures.append("TODO leaked raw English source descriptions")
        if "first / 第一项待办" not in todo_chat or "摘要：下一步执行动作一" not in todo_chat or "详情：当前状态：第一项待办" not in todo_chat:
            failures.append("TODO did not expose deterministic Chinese display metadata")
        if any(marker in todo_chat for marker in ("回复编号", "1~", "1～", "Recommended Next")):
            failures.append("TODO leaked a forbidden continuation menu")
        selected = run_json(script, "1", env, extra_args=["--context", "todo-list", "--context-token", todo["context_token"]])
        selected_chat = selected.get("surface", {}).get("chat_text", "")
        selected_display = selected.get("selected_display", {})
        selected_detail = selected.get("selected_detail", "")
        selection_localized = (
            selected_display.get("name") == "第一项待办"
            and isinstance(selected_detail, str)
            and bool(selected_detail.strip())
            and normalize_detail_layout(selected_display.get("detail", "")) == normalize_detail_layout(selected_detail)
            and normalize_detail_layout(selected_detail) in normalize_detail_layout(selected_chat)
            and "\n详情：\n" in selected_chat
            and "Next action:" not in selected_chat
        )
        if not selection_localized:
            failures.append("TODO numeric selection did not return the localized detail surface")
        todo_source = state / "TODO.md"
        todo_source.write_text(todo_source.read_text(encoding="utf-8").replace("evidence one.", "evidence one changed.", 1), encoding="utf-8")
        try:
            run_json(script, "TODO", env)
            failures.append("TODO accepted stale localized display metadata after source change")
        except RuntimeError:
            pass

        help_payload = run_json(script, "帮助", env, open_ui=True)
        help_chat = help_payload.get("surface", {}).get("chat_text", "")
        if help_payload.get("open_status") != "opened-test-receipt" or "一分钟试跑" not in help_chat:
            failures.append("Help did not open HTML and return complete chat text")

        token = run_json(script, "TOKEN", env, open_ui=True)
        token_chat = token.get("surface", {}).get("chat_text", "")
        if token.get("open_status") != "opened-test-receipt" or token_chat.count("\n") != 4:
            failures.append("TOKEN did not return a five-line summary and open receipt")
        if not Path(token.get("dashboard", "")).is_file():
            failures.append("TOKEN dashboard was not generated")

        quick = run_json(script, "小Q", env)
        quick_chat = quick.get("surface", {}).get("chat_text", "")
        if not quick_chat.startswith("【小Q工作流 | 快速恢复 】部分\n"):
            failures.append("Quick resume first line drifted")
        if "record_state: partial" not in quick_chat or "最近：" not in quick_chat or "边界：Phase A" not in quick_chat:
            failures.append("Quick resume evidence/status boundary is incomplete")

        opened_targets = receipt.read_text(encoding="utf-8").splitlines() if receipt.is_file() else []
        if str(hub / "FIRST_RUN_GUIDE.zh-CN.html") not in opened_targets:
            failures.append("Help HTML target missing from open receipt")
        if str(token.get("dashboard", "")) not in opened_targets:
            failures.append("TOKEN dashboard target missing from open receipt")

    return {"status": "pass" if not failures else "fail", "failures": failures, "cases": 4}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    args = parser.parse_args()
    result = replay(Path(args.root).resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
