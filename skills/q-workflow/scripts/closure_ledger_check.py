#!/usr/bin/env python3
r"""Check that a completed task did not leave stale recovery ledger entries.

The checker is intentionally bounded and read-only. It compares one task id or
objective against the personal state ledger surfaces used by q-workflow:
ACTIVE_WORK, TODO, PAUSED_WORK, matching work items, and runtime mirrors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import workflow_audit


COMPLETED_WORDS = ("completed", "complete", "closed", "done", "已完成", "关闭", "完成")
ACTIVE_WORDS = ("active", "in progress", "open", "paused", "pending", "blocked", "进行中", "暂停", "阻塞")


@dataclass(frozen=True)
class Finding:
    status: str
    surface: str
    evidence: str
    action: str


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest().upper()[:12]
    except OSError:
        return "MISSING"


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def compact(value: str, limit: int = 180) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "..."


def task_terms(task_id: str, objective: str) -> list[str]:
    terms: list[str] = []
    for value in (task_id, objective):
        value = value.strip()
        if value:
            terms.append(value)

    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = normalize(term)
        if key and key not in seen:
            seen.add(key)
            deduped.append(term)
    return deduped


def contains_any(text: str, terms: list[str]) -> bool:
    lowered = normalize(text)
    return any(normalize(term) in lowered for term in terms if term)


def matching_lines(text: str, terms: list[str]) -> list[str]:
    return [line for line in text.splitlines() if contains_any(line, terms)]


def extract_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    start = -1
    for index, line in enumerate(lines):
        if line.strip().lower() == heading.lower():
            start = index + 1
            break
    if start < 0:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def todo_section(text: str, heading: str) -> str:
    return extract_section(text, f"## {heading}")


def work_item_status(text: str) -> str:
    for line in text.splitlines()[:40]:
        if re.search(r"(?i)\bstatus\b\s*[:|-]\s*", line):
            lowered = normalize(line)
            if any(word in lowered for word in COMPLETED_WORDS):
                return "completed"
            if any(word in lowered for word in ACTIVE_WORDS):
                return "active"
    lowered = normalize(text[:2000])
    if any(word in lowered for word in COMPLETED_WORDS):
        return "completed"
    if any(word in lowered for word in ACTIVE_WORDS):
        return "active"
    return "unknown"


def find_work_items(state_dir: Path, terms: list[str]) -> list[tuple[Path, str]]:
    work_items = state_dir / "work-items"
    if not work_items.exists():
        return []
    matches: list[tuple[Path, str]] = []
    for path in sorted(work_items.glob("*.md")):
        text = read_text(path)
        if contains_any(path.name, terms) or contains_any(text, terms):
            matches.append((path, work_item_status(text)))
    return matches


def check_state_pair(hub_path: Path, runtime_path: Path, label: str, findings: list[Finding]) -> None:
    if not hub_path.exists():
        findings.append(Finding("BLOCKED", label, f"missing hub file: {hub_path}", "Restore the authoritative hub state file."))
        return
    if not runtime_path.exists():
        findings.append(Finding("WARN", label, f"missing runtime mirror: {runtime_path}", "Refresh or explicitly defer the runtime mirror."))
        return
    if file_hash(hub_path) != file_hash(runtime_path):
        findings.append(
            Finding(
                "WARN",
                label,
                f"hub hash {file_hash(hub_path)} != runtime hash {file_hash(runtime_path)}",
                "Refresh the affected runtime mirror before claiming closure.",
            )
        )


def evaluate_closed(paths: dict[str, Path], terms: list[str], findings: list[Finding]) -> None:
    hub_state = paths["hub_personal_state"]
    runtime_state = paths["runtime_personal_state"]
    active_path = hub_state / "ACTIVE_WORK.md"
    todo_path = hub_state / "TODO.md"
    paused_path = hub_state / "PAUSED_WORK.md"

    active_text = read_text(active_path)
    current_focus = extract_section(active_text, "## Current Focus")
    if contains_any(current_focus, terms):
        findings.append(
            Finding(
                "BLOCKED",
                "ACTIVE_WORK Current Focus",
                compact("; ".join(matching_lines(current_focus, terms))),
                "Remove completed task text from Current Focus or replace it with a concrete remaining action.",
            )
        )

    todo_text = read_text(todo_path)
    open_todo = todo_section(todo_text, "Open")
    if contains_any(open_todo, terms):
        findings.append(
            Finding(
                "BLOCKED",
                "TODO Open",
                compact("; ".join(matching_lines(open_todo, terms))),
                "Move the matching TODO to Done or leave it Open with an explicit remaining-action reason.",
            )
        )

    paused_text = read_text(paused_path)
    if contains_any(paused_text, terms):
        findings.append(
            Finding(
                "WARN",
                "PAUSED_WORK",
                compact("; ".join(matching_lines(paused_text, terms))),
                "Remove stale paused entries or mark why the completed task is still intentionally paused.",
            )
        )

    items = find_work_items(hub_state, terms)
    for path, status in items:
        if status != "completed":
            findings.append(
                Finding(
                    "WARN",
                    "work item",
                    f"{path} status={status}",
                    "Mark the work item Completed/Closed, archive it, or document the remaining work.",
                )
            )

    # The foundational runtime mirror deliberately owns only route-critical
    # ACTIVE_WORK/TODO; PAUSED_WORK and work items remain hub-only records.
    for name in ("ACTIVE_WORK.md", "TODO.md"):
        check_state_pair(hub_state / name, runtime_state / name, name, findings)


def evaluate_active(paths: dict[str, Path], terms: list[str], findings: list[Finding]) -> None:
    hub_state = paths["hub_personal_state"]
    active_text = read_text(hub_state / "ACTIVE_WORK.md")
    todo_text = read_text(hub_state / "TODO.md")
    work_items = find_work_items(hub_state, terms)
    found = contains_any(active_text, terms) or contains_any(todo_text, terms) or bool(work_items)
    if not found:
        findings.append(
            Finding(
                "WARN",
                "ledger presence",
                "task was not found in ACTIVE_WORK, TODO, or work-items",
                "Create or update a work item before relying on recovery for this active task.",
            )
        )


def render_text(expect: str, terms: list[str], findings: list[Finding]) -> str:
    blockers = [item for item in findings if item.status == "BLOCKED"]
    warnings = [item for item in findings if item.status == "WARN"]
    status = "PASS" if not blockers and not warnings else "ATTENTION"
    lines = [
        "Closure ledger check",
        f"Expectation: {expect}",
        f"Terms: {', '.join(terms)}",
        f"Status: {status}",
        f"Blockers: {len(blockers)}",
        f"Warnings: {len(warnings)}",
    ]
    if findings:
        lines.append("")
        lines.append("Findings:")
        for item in findings:
            lines.append(f"- {item.status} | {item.surface} | {item.evidence} | {item.action}")
    return "\n".join(lines) + "\n"


def render_json(expect: str, terms: list[str], findings: list[Finding]) -> str:
    blockers = [item for item in findings if item.status == "BLOCKED"]
    warnings = [item for item in findings if item.status == "WARN"]
    payload = {
        "expectation": expect,
        "terms": terms,
        "status": "PASS" if not blockers and not warnings else "ATTENTION",
        "blockers": len(blockers),
        "warnings": len(warnings),
        "findings": [item.__dict__ for item in findings],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", default="", help="Task id, TODO id, or work-item id to check.")
    parser.add_argument("--objective", default="", help="Human-readable objective text to match.")
    parser.add_argument("--expect", choices=("closed", "active"), default="closed", help="Expected ledger state.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blockers or warnings exist.")
    args = parser.parse_args(argv)

    terms = task_terms(args.task_id, args.objective)
    if not terms:
        parser.error("--task-id or --objective is required")

    paths = workflow_audit.default_paths()
    findings: list[Finding] = []
    if args.expect == "closed":
        evaluate_closed(paths, terms, findings)
    else:
        evaluate_active(paths, terms, findings)

    output = render_json(args.expect, terms, findings) if args.format == "json" else render_text(args.expect, terms, findings)
    sys.stdout.write(output)
    if not args.strict:
        return 0
    return 1 if any(item.status in {"BLOCKED", "WARN"} for item in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
