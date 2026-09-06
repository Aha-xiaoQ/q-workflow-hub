#!/usr/bin/env python3
r"""Print a compact pointer for a local Codex session.

This is read-only and dependency-free. It is meant for recovery after a
platform compact/session failure when the user wants the last visible request
without pasting a screenshot or reloading a long old session.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TEXT_PART_TYPES = {"input_text", "output_text", "text"}
IMAGE_TAG_RE = re.compile(r"<\/?image\b[^>]*>", re.IGNORECASE)
ENV_RE = re.compile(r"<environment_context>.*?</environment_context>", re.DOTALL)
WS_RE = re.compile(r"\s+")
INTERNAL_CONTROL_PREFIXES = (
    "<recommended_plugins>",
    "<environment_context>",
    "<permissions instructions>",
    "<app-context>",
    "<skills_instructions>",
    "<apps_instructions>",
    "<plugins_instructions>",
    "<collaboration_mode>",
)
EXACT_BASE_COMMANDS = {"todo", "help", "帮助", "token", "小q", "小ｑ", "xiaoq", "xiao q", "继续小q", "resume", "continue", "status", "状态", "checkpoint"}
SESSION_ID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$", re.IGNORECASE)
DEFAULT_TAIL_BYTES = 4 * 1024 * 1024


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


@dataclass
class Message:
    timestamp: str
    role: str
    text: str
    phase: str = ""


@dataclass
class SessionPointer:
    path: Path
    session_id: str = ""
    cwd: str = ""
    started_at: str = ""
    updated_at: float = 0.0
    source: str = ""
    cli_version: str = ""
    model: str = ""
    provider: str = ""
    messages: list[Message] = field(default_factory=list)
    parse_errors: int = 0


def default_codex_home() -> Path:
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def iso_from_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, timezone.utc).astimezone().isoformat(timespec="seconds")


def text_from_parts(parts: Any) -> str:
    if not isinstance(parts, list):
        return ""
    texts: list[str] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        if part.get("type") not in TEXT_PART_TYPES:
            continue
        value = part.get("text")
        if isinstance(value, str) and value:
            texts.append(value)
    return "\n".join(texts)


def clean_text(value: str, max_chars: int, *, preserve_tail: bool = False) -> str:
    value = ENV_RE.sub(" ", value)
    value = IMAGE_TAG_RE.sub(" ", value)
    value = value.replace("\x00", "")
    value = WS_RE.sub(" ", value).strip()
    if len(value) <= max_chars:
        return value
    if preserve_tail:
        if max_chars < 160:
            return "..." + value[-(max_chars - 3) :].lstrip()
        head_chars = max(60, min(120, max_chars // 3))
        tail_chars = max_chars - head_chars - 5
        return value[:head_chars].rstrip() + " ... " + value[-tail_chars:].lstrip()
    return value[: max_chars - 1].rstrip() + "..."


def _parse_session_line(pointer: SessionPointer, line: str, max_chars: int) -> None:
    line = line.strip()
    if not line:
        return
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        pointer.parse_errors += 1
        return

    if obj.get("type") == "session_meta":
        payload = obj.get("payload") or {}
        pointer.session_id = str(payload.get("id") or pointer.session_id)
        pointer.cwd = str(payload.get("cwd") or pointer.cwd)
        pointer.started_at = str(payload.get("timestamp") or pointer.started_at)
        pointer.source = str(payload.get("source") or pointer.source)
        pointer.cli_version = str(payload.get("cli_version") or pointer.cli_version)
        pointer.provider = str(payload.get("model_provider") or pointer.provider)
        model = payload.get("model")
        if isinstance(model, str):
            pointer.model = model
        return

    payload = obj.get("payload") or {}
    if obj.get("type") != "response_item" or payload.get("type") != "message":
        return
    role = payload.get("role")
    if role not in {"user", "assistant"}:
        return
    phase = str(payload.get("phase") or "")
    preserve_tail = role == "user" or (role == "assistant" and phase == "final_answer")
    text = clean_text(text_from_parts(payload.get("content")), max_chars, preserve_tail=preserve_tail)
    if text:
        pointer.messages.append(
            Message(
                timestamp=str(obj.get("timestamp") or ""),
                role=str(role),
                text=text,
                phase=phase,
            )
        )


def parse_session(path: Path, max_chars: int, *, tail_bytes: int | None = None) -> SessionPointer:
    pointer = SessionPointer(path=path, updated_at=path.stat().st_mtime)
    match = SESSION_ID_RE.search(path.stem)
    if match:
        pointer.session_id = match.group(1)
    try:
        with path.open("rb") as handle:
            if tail_bytes is not None:
                file_size = path.stat().st_size
                start = max(0, file_size - max(1, tail_bytes))
                if start:
                    handle.seek(start)
                    handle.seek(start - 1)
                    previous_byte = handle.read(1)
                    handle.seek(start)
                    if previous_byte != b"\n":
                        handle.readline()
            for raw_line in handle:
                _parse_session_line(pointer, raw_line.decode("utf-8", errors="replace"), max_chars)
    except OSError:
        pointer.parse_errors += 1
    return pointer


def find_sessions(codex_home: Path) -> list[Path]:
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.exists():
        return []
    return sorted(sessions_dir.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime)


def select_session(paths: list[Path], session_id: str, offset: int) -> Path | None:
    if not paths:
        return None
    if not session_id:
        candidates = list(reversed(paths))
        if offset < 0 or offset >= len(candidates):
            return None
        return candidates[offset]
    for path in paths:
        if session_id in path.name:
            return path
    return None


def message_dict(message: Message) -> dict[str, str]:
    return {
        "timestamp": message.timestamp,
        "role": message.role,
        "phase": message.phase,
        "text": message.text,
    }


def is_internal_control_message(message: Message) -> bool:
    stripped = message.text.strip().casefold()
    return any(stripped.startswith(prefix) for prefix in INTERNAL_CONTROL_PREFIXES)


def is_exact_base_command(message: Message) -> bool:
    stripped = message.text.strip().casefold()
    return stripped in EXACT_BASE_COMMANDS or bool(re.fullmatch(r"[1-9]\d*", stripped))


def filter_messages(messages: list[Message], users_only: bool, exclude_internal_control: bool, exclude_base_commands: bool) -> list[Message]:
    result = messages
    if users_only:
        result = [message for message in result if message.role == "user"]
    if exclude_internal_control:
        result = [message for message in result if not is_internal_control_message(message)]
    if exclude_base_commands:
        result = [message for message in result if not is_exact_base_command(message)]
    return result


def pointer_dict(pointer: SessionPointer, messages: list[Message]) -> dict[str, Any]:
    return {
        "session_id": pointer.session_id,
        "path": str(pointer.path),
        "cwd": pointer.cwd,
        "started_at": pointer.started_at,
        "updated_at": iso_from_mtime(pointer.updated_at),
        "source": pointer.source,
        "cli_version": pointer.cli_version,
        "provider": pointer.provider,
        "model": pointer.model,
        "parse_errors": pointer.parse_errors,
        "messages": [message_dict(message) for message in messages],
    }


def print_text(pointer: SessionPointer, messages: list[Message]) -> None:
    print("Codex session pointer")
    print(f"Session ID: {pointer.session_id or '(unknown)'}")
    print(f"Path: {pointer.path}")
    print(f"CWD: {pointer.cwd or '(unknown)'}")
    print(f"Updated: {iso_from_mtime(pointer.updated_at)}")
    if pointer.source or pointer.cli_version:
        print(f"Source: {pointer.source or '(unknown)'} / CLI {pointer.cli_version or '(unknown)'}")
    if pointer.parse_errors:
        print(f"Warning: {pointer.parse_errors} parse errors")
    print()
    print("Recent messages:")
    if not messages:
        print("- (none)")
        return
    for message in messages:
        phase = f" {message.phase}" if message.phase else ""
        print(f"- {message.timestamp} {message.role}{phase}: {message.text}")
    print()
    print("Recovery note: prefer durable state for work continuity. Use `codex resume --last` only when you explicitly want to reopen the old full session.")


def main() -> int:
    configure_output()
    parser = argparse.ArgumentParser(description="Print a compact local Codex session pointer.")
    parser.add_argument("--codex-home", default=str(default_codex_home()), help="Codex home directory.")
    parser.add_argument("--session-id", default="", help="Specific session id or id prefix from the filename.")
    parser.add_argument("--offset", type=int, default=0, help="Newest session offset; use 1 to skip the current fresh session.")
    parser.add_argument("--messages", type=int, default=6, help="Number of recent messages to print.")
    parser.add_argument("--users-only", action="store_true", help="Print only recent user messages.")
    parser.add_argument("--exclude-internal-control", action="store_true", help="Filter platform control envelopes before applying --messages.")
    parser.add_argument("--exclude-base-commands", action="store_true", help="Filter exact micro commands and numeric selections before applying --messages.")
    parser.add_argument("--best-user-session", action="store_true", help="Choose the session whose filtered user tail has the newest message timestamp, not merely the newest file mtime.")
    parser.add_argument("--tail-bytes", type=int, default=DEFAULT_TAIL_BYTES, help="Bounded bytes to read from the end of each candidate session when --best-user-session is used.")
    parser.add_argument("--max-chars", type=int, default=500, help="Maximum characters per message.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    args = parser.parse_args()

    paths = find_sessions(Path(args.codex_home).expanduser())
    pointer: SessionPointer | None = None
    messages: list[Message] = []
    if args.best_user_session and not args.session_id:
        best_key: tuple[str, float] | None = None
        for candidate in paths[-100:]:
            candidate_pointer = parse_session(candidate, max(80, args.max_chars), tail_bytes=max(1, args.tail_bytes))
            candidate_messages = filter_messages(candidate_pointer.messages, args.users_only, args.exclude_internal_control, args.exclude_base_commands)
            if not candidate_messages:
                continue
            key = (candidate_messages[-1].timestamp, candidate_pointer.updated_at)
            if best_key is None or key > best_key:
                best_key = key
                pointer = candidate_pointer
                messages = candidate_messages
    else:
        path = select_session(paths, args.session_id, args.offset)
        if path is not None:
            pointer = parse_session(path, max(80, args.max_chars))
            messages = filter_messages(pointer.messages, args.users_only, args.exclude_internal_control, args.exclude_base_commands)
    if pointer is None:
        print("No matching Codex session JSONL files found.")
        return 1
    messages = messages[-max(1, args.messages) :]

    if args.format == "json":
        print(json.dumps(pointer_dict(pointer, messages), ensure_ascii=False, indent=2))
    else:
        print_text(pointer, messages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
