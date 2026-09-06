#!/usr/bin/env python3
"""Isolated regression test for bounded Xiao Q quick wake.

The fixture intentionally contains a large JSONL session tail. The test never
touches the real Codex home, workflow hub, or user state.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
POINTER = ROOT / "session_pointer.py"
BASE_COMMAND = ROOT / "q_base_command.py"
sys.path.insert(0, str(ROOT))
import session_pointer as session_pointer_module


def write_message(handle, timestamp: str, role: str, text: str) -> None:
    row = {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": role,
            "content": [{"type": "input_text" if role == "user" else "output_text", "text": text}],
        },
    }
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_large_session(path: Path, session_id: str, user_timestamp: str, user_text: str, noise_lines: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({
            "timestamp": "2026-07-31T00:00:00Z",
            "type": "session_meta",
            "payload": {"id": session_id, "cwd": "D:\\isolated", "timestamp": "2026-07-31T00:00:00Z"},
        }, ensure_ascii=False) + "\n")
        write_message(handle, "2026-07-31T00:01:00Z", "user", "旧的用户请求")
        filler = "x" * 220
        for index in range(noise_lines):
            handle.write(json.dumps({
                "timestamp": f"2026-07-31T00:02:{index % 60:02d}Z",
                "type": "event_msg",
                "payload": {"type": "tool_output", "text": filler},
            }) + "\n")
        write_message(handle, user_timestamp, "user", user_text)


def write_state(root: Path) -> Path:
    hub = root / "hub"
    state = hub / "personal-state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "TODO.md").write_text("# TODO\n\n## Open\n\n## Done\n", encoding="utf-8")
    (state / "TODO_DISPLAY.zh-CN.json").write_text(
        json.dumps({"version": 1, "language": "zh-CN", "items": {}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (state / "ACTIVE_WORK.md").write_text(
        "# Active Work\n\n## Current Focus\n\n隔离唤醒测试。\n\n"
        "## RECOVERY_POINTER v1\n\n"
        "sync_state: synced\n"
        "authority_event: isolated-test\n"
        "task_id: isolated-quick-wake\n"
        "work_state: active\n"
        "integrity_state: local-validated\n"
        "release_state: local-only\n"
        "active_project: isolated\n"
        "path: D:\\isolated\n"
        "latest_chat_override: 隔离唤醒测试\n"
        "latest_verified_note: 隔离唤醒测试\n"
        "next_action: 验证小Q唤醒\n",
        encoding="utf-8",
    )
    profile = root / "q-profile.json"
    profile.write_text(json.dumps({"hub": str(hub)}, ensure_ascii=False) + "\n", encoding="utf-8")
    return profile


def run_json(command: list[str], env: dict[str, str], timeout: float) -> tuple[dict, float]:
    started = time.perf_counter()
    completed = subprocess.run(command, env=env, capture_output=True, text=True, encoding="utf-8", timeout=timeout, check=False)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        raise AssertionError(f"command failed ({completed.returncode}) after {elapsed:.2f}s: {completed.stderr or completed.stdout}")
    try:
        return json.loads(completed.stdout), elapsed
    except json.JSONDecodeError as exc:
        raise AssertionError(f"invalid JSON after {elapsed:.2f}s: {exc}: {completed.stdout[:500]}") from exc


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="qwf-quick-wake-") as temp:
        root = Path(temp)
        sessions = root / "sessions" / "2026" / "08" / "01"
        latest = sessions / "rollout-2026-08-01T01-00-00-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.jsonl"
        decoy = sessions / "rollout-2026-08-01T02-00-00-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.jsonl"
        write_large_session(latest, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "2026-08-01T01:00:00Z", "隔离唤醒测试", 24000)
        write_large_session(decoy, "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "2026-07-31T23:00:00Z", "较旧的分支请求", 24000)
        boundary = sessions / "rollout-2026-08-01T03-00-00-cccccccc-cccc-4ccc-8ccc-cccccccccccc.jsonl"
        with boundary.open("w", encoding="utf-8", newline="\n") as boundary_handle:
            write_message(boundary_handle, "2026-07-30T02:59:00Z", "user", "尾部边界旧消息")
            write_message(boundary_handle, "2026-07-30T03:00:00Z", "user", "尾部边界最新消息")
        boundary_bytes = boundary.read_bytes()
        boundary_start = boundary_bytes.rfind(b'{"timestamp"')
        assert boundary_start > 0
        boundary_pointer = session_pointer_module.parse_session(
            boundary, 800, tail_bytes=len(boundary_bytes) - boundary_start
        )
        boundary_messages = session_pointer_module.filter_messages(
            boundary_pointer.messages, users_only=True, exclude_internal_control=False, exclude_base_commands=False
        )
        assert boundary_messages and boundary_messages[-1].text == "尾部边界最新消息", boundary_messages
        profile = write_state(root)

        pointer, pointer_seconds = run_json([
            sys.executable, str(POINTER), "--codex-home", str(root), "--best-user-session", "--messages", "10",
            "--users-only", "--exclude-internal-control", "--exclude-base-commands", "--max-chars", "800", "--format", "json",
        ], os.environ.copy(), 10)
        messages = pointer.get("messages", [])
        assert messages and messages[-1].get("text") == "隔离唤醒测试", pointer

        env = os.environ.copy()
        env["CODEX_HOME"] = str(root)
        env["Q_PROFILE_PATH"] = str(profile)
        wake, wake_seconds = run_json([
            sys.executable, str(BASE_COMMAND), "--input", "小Q", "--format", "json",
        ], env, 10)
        chat_text = wake.get("surface", {}).get("chat_text", "")
        assert chat_text.startswith("【小Q工作流 | 快速恢复 】"), chat_text
        assert wake.get("phase") == "A", wake
        assert wake.get("command_id") == "quick-resume", wake

        print(json.dumps({
            "status": "pass",
            "fixture": {"session_files": 3, "large_session_noise_lines_each": 24000},
            "pointer_seconds": round(pointer_seconds, 3),
            "wake_seconds": round(wake_seconds, 3),
            "first_line": chat_text.splitlines()[0],
            "record_state": "partial-or-confirmed",
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
