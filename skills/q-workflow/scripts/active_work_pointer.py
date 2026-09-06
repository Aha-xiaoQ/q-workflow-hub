"""Single owner for ACTIVE_WORK Current Focus and RECOVERY_POINTER structure."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

EXPLICIT_IDLE_FOCUS = "- No active blocking focus."
FOCUS_RE = re.compile(r"(?ms)^## Current Focus\s*$\s*(.*?)(?=^##\s+|\Z)")
POINTER_RE = re.compile(r"(?ms)^## RECOVERY_POINTER[^\n]*$\s*(.*?)(?=^##\s+|\Z)")
FENCE_START_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")

POINTER_KEY_ORDER = (
    "schema",
    "task_id",
    "trace_id",
    "execution_epoch",
    "state_revision",
    "authority_event",
    "work_state",
    "visibility_latch",
    "integrity_state",
    "release_state",
    "role_plan_id",
    "primary_owner",
    "primary_status",
    "reviewer_owner",
    "reviewer_status",
    "validator_owner",
    "validator_status",
    "blocked_on",
    "error_code",
    "remote_status",
    "remote_proven",
    "sync_state",
    "next_action",
    "updated_at",
    "work_item_path",
    "authority_path",
    "domain_work_state",
    "domain_integrity_state",
    "task_record_path",
    "task_record_sha256",
    "task_event_log",
)


class ActiveWorkPointerError(ValueError):
    """Raised when ACTIVE_WORK cannot provide an unambiguous recovery route."""


def _without_fenced_blocks(text: str) -> str:
    """Hide fenced examples so Markdown samples cannot become executable state."""
    visible: list[str] = []
    fence_char = ""
    fence_width = 0
    for line in text.splitlines():
        match = FENCE_START_RE.match(line)
        if not fence_char:
            if match:
                marker = match.group(1)
                fence_char, fence_width = marker[0], len(marker)
                visible.append("")
            else:
                visible.append(line)
            continue
        closing = re.match(rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_width},}}\s*$", line)
        if closing:
            fence_char, fence_width = "", 0
        visible.append("")
    return "\n".join(visible)


def inspect_active_work(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "authority": str(path),
        "current_focus": "",
        "current_focus_text": "",
        "recovery_pointer": {},
        "pointer_heading_count": 0,
        "explicit_idle": False,
        "errors": [],
    }
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        result["errors"].append(f"ACTIVE_WORK cannot be read: {path}: {exc}")
        return result

    structural_text = _without_fenced_blocks(text)
    focus_match = FOCUS_RE.search(structural_text)
    if not focus_match:
        result["errors"].append(f"ACTIVE_WORK lacks Current Focus: {path}")
        return result

    structural_focus = focus_match.group(1).strip()
    focus_text = _visible_section_body(text, "Current Focus")
    focus = " ".join(line.strip() for line in structural_focus.splitlines() if line.strip())
    result["current_focus"] = focus
    result["current_focus_text"] = focus_text
    result["explicit_idle"] = focus == EXPLICIT_IDLE_FOCUS
    if not focus:
        result["errors"].append("ACTIVE_WORK Current Focus must not be empty.")

    pointer_matches = list(POINTER_RE.finditer(structural_text))
    result["pointer_heading_count"] = len(pointer_matches)
    if len(pointer_matches) > 1:
        result["errors"].append(
            "ACTIVE_WORK contains multiple executable RECOVERY_POINTER headings; "
            "rename historical envelopes so they cannot match the recovery parser."
        )
        return result
    if not pointer_matches:
        if not result["explicit_idle"]:
            result["errors"].append(
                "ACTIVE_WORK has active Current Focus but no executable RECOVERY_POINTER heading."
            )
        return result

    if result["explicit_idle"]:
        result["errors"].append(
            "ACTIVE_WORK declares explicit idle Current Focus but also contains an executable RECOVERY_POINTER heading."
        )
        return result

    pointer: dict[str, str] = {}
    for line in pointer_matches[0].group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            if key in pointer:
                result["errors"].append(f"RECOVERY_POINTER contains duplicate key: {key}")
                continue
            pointer[key] = value.strip()
    result["recovery_pointer"] = pointer
    if not pointer.get("task_id"):
        result["errors"].append("RECOVERY_POINTER must contain a non-empty task_id.")
    return result


def require_active_work(path: Path) -> dict[str, Any]:
    state = inspect_active_work(path)
    if state["errors"]:
        raise ActiveWorkPointerError(" ".join(state["errors"]))
    return state


def _visible_level_two_sections(text: str) -> list[tuple[int, str]]:
    """Return line indexes and titles for level-two headings outside fences."""
    sections: list[tuple[int, str]] = []
    fence_char = ""
    fence_width = 0
    for index, line in enumerate(text.splitlines()):
        match = FENCE_START_RE.match(line)
        if not fence_char:
            if match:
                marker = match.group(1)
                fence_char, fence_width = marker[0], len(marker)
                continue
            heading = re.match(r"^##\s+(.+?)\s*$", line)
            if heading:
                sections.append((index, heading.group(1)))
            continue
        closing = re.match(rf"^ {{0,3}}{re.escape(fence_char)}{{{fence_width},}}\s*$", line)
        if closing:
            fence_char, fence_width = "", 0
    return sections


def _visible_section_body(text: str, title: str) -> str:
    """Slice one visible section from the original text, preserving fenced content."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    sections = _visible_level_two_sections(text)
    matches = [(index, heading) for index, heading in sections if heading == title]
    if len(matches) != 1:
        return ""
    start = matches[0][0]
    next_indexes = [index for index, _ in sections if index > start]
    end = min(next_indexes) if next_indexes else len(lines)
    return "\n".join(lines[start + 1 : end]).strip()


def _pointer_lines(pointer: dict[str, str]) -> list[str]:
    invalid = [key for key, value in pointer.items() if "\n" in str(value) or "\r" in str(value)]
    if invalid:
        raise ActiveWorkPointerError(f"RECOVERY_POINTER values must be single-line: {invalid}")
    ordered = [key for key in POINTER_KEY_ORDER if key in pointer]
    ordered.extend(sorted(key for key in pointer if key not in POINTER_KEY_ORDER))
    return [f"{key}: {pointer[key]}" for key in ordered]


def render_active_work(
    text: str,
    current_focus: str,
    pointer: dict[str, str],
    *,
    pointer_version: str = "v2",
    task_sections: dict[str, str] | None = None,
) -> str:
    """Replace the focus view and any explicitly supplied task-scoped guidance.

    Recovery rules and non-executable indexes describe the selected task. A
    cross-task transaction must replace them together with Current Focus and
    RECOVERY_POINTER; preserving another task's guidance creates a semantically
    mixed pointer even when hashes and event bindings are valid.
    """
    focus = current_focus.strip()
    if not focus:
        raise ActiveWorkPointerError("Current Focus must not be empty.")
    if focus == EXPLICIT_IDLE_FOCUS:
        raise ActiveWorkPointerError("Use the explicit idle template instead of rendering a pointer.")
    if not pointer.get("task_id"):
        raise ActiveWorkPointerError("RECOVERY_POINTER requires task_id before rendering.")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    initial = inspect_active_work_text(normalized)
    if initial["errors"]:
        raise ActiveWorkPointerError("Cannot render invalid ACTIVE_WORK: " + " ".join(initial["errors"]))
    if initial["explicit_idle"] and not initial["errors"] and initial["pointer_heading_count"] == 0:
        # A fresh idle hub has no bound task yet. Insert the first pointer slot;
        # never repair a malformed active pointer through this path.
        normalized = normalized.rstrip() + "\n\n## RECOVERY_POINTER v2\n\n"
    lines = normalized.splitlines()
    sections = _visible_level_two_sections(normalized)
    focus_matches = [item for item in sections if item[1] == "Current Focus"]
    pointer_matches = [item for item in sections if item[1].startswith("RECOVERY_POINTER")]
    if len(focus_matches) != 1 or len(pointer_matches) != 1:
        raise ActiveWorkPointerError(
            "ACTIVE_WORK rendering requires exactly one Current Focus and one executable RECOVERY_POINTER section."
        )

    replacements: list[tuple[int, int, list[str]]] = []
    for (start, title), kind in ((focus_matches[0], "focus"), (pointer_matches[0], "pointer")):
        next_indexes = [index for index, _ in sections if index > start]
        end = min(next_indexes) if next_indexes else len(lines)
        if kind == "focus":
            replacement = ["## Current Focus", "", *focus.splitlines(), ""]
        else:
            replacement = [f"## RECOVERY_POINTER {pointer_version}", "", *_pointer_lines(pointer), ""]
        replacements.append((start, end, replacement))

    missing_task_sections: list[tuple[str, str]] = []
    for title, body in (task_sections or {}).items():
        if not title.strip() or not body.strip():
            raise ActiveWorkPointerError("Task-scoped section titles and bodies must not be empty.")
        matches = [item for item in sections if item[1] == title]
        if len(matches) > 1:
            raise ActiveWorkPointerError(f"ACTIVE_WORK contains duplicate task-scoped section: {title}")
        if not matches:
            missing_task_sections.append((title, body.strip()))
            continue
        start = matches[0][0]
        next_indexes = [index for index, _ in sections if index > start]
        end = min(next_indexes) if next_indexes else len(lines)
        replacements.append((start, end, [f"## {title}", "", *body.strip().splitlines(), ""]))

    for start, end, replacement in sorted(replacements, reverse=True):
        lines[start:end] = replacement
    for title, body in missing_task_sections:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([f"## {title}", "", *body.splitlines(), ""])
    rendered = "\n".join(lines).rstrip() + "\n"
    candidate = inspect_active_work_text(rendered)
    if candidate["errors"]:
        raise ActiveWorkPointerError("Rendered ACTIVE_WORK failed readback: " + " ".join(candidate["errors"]))
    return rendered


def inspect_active_work_text(text: str) -> dict[str, Any]:
    """Inspect an in-memory candidate using the same structural rules as files."""
    result: dict[str, Any] = {
        "authority": "memory",
        "current_focus": "",
        "current_focus_text": "",
        "recovery_pointer": {},
        "pointer_heading_count": 0,
        "explicit_idle": False,
        "errors": [],
    }
    structural_text = _without_fenced_blocks(text)
    focus_match = FOCUS_RE.search(structural_text)
    if not focus_match:
        result["errors"].append("ACTIVE_WORK lacks Current Focus: memory")
        return result
    structural_focus = focus_match.group(1).strip()
    focus_text = _visible_section_body(text, "Current Focus")
    focus = " ".join(line.strip() for line in structural_focus.splitlines() if line.strip())
    result["current_focus"] = focus
    result["current_focus_text"] = focus_text
    result["explicit_idle"] = focus == EXPLICIT_IDLE_FOCUS
    if not focus:
        result["errors"].append("ACTIVE_WORK Current Focus must not be empty.")
    pointer_matches = list(POINTER_RE.finditer(structural_text))
    result["pointer_heading_count"] = len(pointer_matches)
    if not pointer_matches and result["explicit_idle"]:
        return result
    if pointer_matches and result["explicit_idle"]:
        result["errors"].append("ACTIVE_WORK declares idle but contains an executable RECOVERY_POINTER.")
        return result
    if len(pointer_matches) != 1:
        result["errors"].append("ACTIVE_WORK candidate must contain exactly one RECOVERY_POINTER.")
        return result
    pointer: dict[str, str] = {}
    for line in pointer_matches[0].group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in pointer:
            result["errors"].append(f"RECOVERY_POINTER contains duplicate key: {key}")
            continue
        pointer[key] = value.strip()
    result["recovery_pointer"] = pointer
    if not pointer.get("task_id"):
        result["errors"].append("RECOVERY_POINTER must contain a non-empty task_id.")
    return result
