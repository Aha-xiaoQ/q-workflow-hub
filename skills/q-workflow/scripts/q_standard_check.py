#!/usr/bin/env python3
"""Minimal q-workflow standard contract checker."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory


SLASH_GRAMMAR = "\u5c0fQ\u5de5\u4f5c\u6d41 / <skill-id> / <current-action>"
GOOD_STATUS = "\u5c0fQ\u5de5\u4f5c\u6d41 / q-agent-roster / \u4e13\u5bb6\u8c03\u7528\u534f\u8bae\u4fee\u590d"
BAD_STATUS = "\u5c0fQ\u5de5\u4f5c\u6d41 / Workflow Distiller (\u6c89\u70bc) / blocked-pending-approval"
BAD_ROUTE_STATUS = "\u5c0fQ\u5de5\u4f5c\u6d41 / validation / \u683c\u5f0f\u95e8\u7981\u590d\u6d4b"
BAD_SCRIPT_ROUTE_STATUS = "\u5c0fQ\u5de5\u4f5c\u6d41 / source-runtime-audit / \u540c\u6b65\u9a8c\u8bc1"
STATUS_RE = re.compile(r"^\u5c0fQ\u5de5\u4f5c\u6d41 / (?P<route>[a-z0-9][a-z0-9-]*) / (?P<action>[^/\r\n]+)$")
STATUS_LINE_CANDIDATE_RE = re.compile(r"^\u5c0fQ\u5de5\u4f5c\u6d41 / .+ / .+$")
BAD_ACTION_STATES = {"done", "partial", "blocked", "pending-approval", "confirmed", "stale", "conflict"}
BASE_STATUS_SKILLS = {"q-workflow"}
INVALID_SKILL_SLOT_WORDS = {
    "audit",
    "build",
    "check",
    "closure",
    "commit",
    "format",
    "handoff",
    "health",
    "release",
    "review",
    "source-runtime-audit",
    "sync",
    "test",
    "validation",
}
INVALID_SKILL_SLOT_SUFFIXES = ("-audit", "-check", "-gate", "-test", "-validation")
INVALID_SKILL_SLOT_SUBSTRINGS = ("script", "runner", "smoke")

MOJIBAKE_MARKERS = ("\ufffd", "\u00e5\u00b0", "\u00e4\u00bd", "\u00e6\u00b5", "\u00e7\u201d", "\u00e6\u00b2", "\u00e9\u00aa", "\u00e8", "\u00c3", "\u00c2")
STABLE_EXPERTS = {
    "Visual Arbiter": "\u7248\u8861",
    "Source Scout": "\u5bfb\u6e90",
    "Pagewright": "\u9875\u5320",
    "Doc Architect": "\u6587\u6784",
    "Code Auditor": "\u7801\u9274",
    "Workflow Distiller": "\u6c89\u70bc",
    "Usability Validator": "\u9a8c\u7528",
}
INVALID_EXPERT_SKILL_SLOT_WORDS = {alias.lower().replace(" ", "-") for alias in STABLE_EXPERTS}
EXPERT_CARD_FIELDS = [
    "Expert role",
    "English name",
    "Chinese name",
    "Run instance",
    "Mode",
    "Mission",
    "Permissions",
    "Boundaries",
]
REQUIRED_RULE_FIELDS = [
    "rule_id",
    "status",
    "level",
    "trigger",
    "scope",
    "requirement",
    "blocks",
    "check",
    "repair",
    "waiver",
    "owner",
    "test",
]
VALID_RULE_STATUS = {"draft", "candidate", "stable", "deprecated"}
VALID_RULE_LEVEL = {"MUST", "MUST_NOT", "MUST NOT", "SHOULD", "MAY"}
NEXT_OPTIONS_GUIDE_MARKERS = ("## Handoff Next Options", "**Recommended Next**", "(Recommended)")
NEXT_OPTION_RE = re.compile(r"^\s*(?P<num>\d+)\.\s+(?P<body>\S.*)\s*$")
FORMAT_GATE_DOC_TERMS = (
    "Format Defect Gate",
    "text-format-hygiene",
    "text_format_guard.py",
    "encoding_guard.py",
    "q_standard_check.py",
    "git diff --check",
    "regression-ledger.md",
    "surfaces_checked",
    "skipped_surfaces",
)
FORMAT_REPLAY_REQUIRED_FIELDS = (
    "defect_class:",
    "fix:",
    "evidence:",
    "ledger:",
    "surfaces_checked:",
    "skipped_surfaces:",
)
FORMAT_REPLAY_EVIDENCE_TERMS = (
    "text_format_guard.py",
    "encoding_guard.py",
    "q_standard_check.py",
    "git diff --check",
    "readback",
)
ZH_FORBIDDEN_INTERNAL_LABELS = (
    "Project summary:",
    "Adaptive details:",
    "Project registration plan:",
    "HardwareDetail:",
    "FirmwareOrSoftwareDetail:",
    "DocumentDetail:",
    "RegistryAction:",
    "WillCopyProjectContent:",
    "WillRunGitPush:",
)


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


@dataclass
class Finding:
    severity: str
    code: str
    path: str
    message: str


def add(findings: list[Finding], severity: str, code: str, path: Path | str, message: str) -> None:
    findings.append(Finding(severity, code, str(path), message))


def read_utf8(path: Path, findings: list[Finding]) -> str | None:
    try:
        data = path.read_bytes()
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        add(findings, "fatal", "invalid-utf8", path, f"File is not valid UTF-8: {exc}")
        return None
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(marker in line for marker in MOJIBAKE_MARKERS):
            add(findings, "blocker", "mojibake-marker", path, f"Suspicious mojibake marker on line {line_no}: {line[:100]}")
            break
    return text


def discover_status_skills(extra_roots: list[Path] | None = None) -> set[str]:
    skills = set(BASE_STATUS_SKILLS)
    roots = [
        Path.home() / ".codex" / "skills",
        Path(__file__).resolve().parents[2],
    ]
    if extra_roots:
        roots.extend(extra_roots)
    for root in roots:
        if not root.is_dir():
            continue
        for child in root.iterdir():
            if child.is_dir() and (child / "SKILL.md").is_file():
                skills.add(child.name)
    return skills


def status_skill_slot_error(skill: str, allowed_skills: set[str] | None = None) -> str | None:
    if skill in INVALID_SKILL_SLOT_WORDS or skill in INVALID_EXPERT_SKILL_SLOT_WORDS:
        return "second slot must be a skill id, not a temporary action/check/expert label"
    if skill.endswith(INVALID_SKILL_SLOT_SUFFIXES) or any(token in skill for token in INVALID_SKILL_SLOT_SUBSTRINGS):
        return "second slot must be a skill id, not a script, test, audit, check, gate, or validation label"
    skills = allowed_skills or discover_status_skills()
    if skill not in skills:
        return "second slot must be a registered skill id; put route details, script/check names, and task labels in the action slot"
    return None


def validate_status_line(line: str, allowed_skills: set[str] | None = None) -> str | None:
    normalized_line = line.strip().lstrip("\ufeff")
    match = STATUS_RE.match(normalized_line)
    if not match:
        return f"status line must be: {SLASH_GRAMMAR}"
    skill = match.group("route")
    action = match.group("action").strip()
    if "(" in skill or ")" in skill or " " in skill:
        return "second slot must be a skill id, not an expert role or platform nickname"
    skill_error = status_skill_slot_error(skill, allowed_skills)
    if skill_error:
        return skill_error
    if action.lower() in BAD_ACTION_STATES:
        return "action slot must be the current action; put state on the next line"
    return None


def first_nonempty_line(text: str) -> tuple[int, str]:
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip().lstrip("\ufeff")
        if stripped:
            return line_no, stripped
    return 0, ""


def validate_chat_output(text: str, allow_lightweight: bool = False) -> list[str]:
    line_no, first = first_nonempty_line(text)
    if not first:
        return ["chat output is empty"]
    error = validate_status_line(first)
    if error is None:
        return []
    if allow_lightweight:
        lowered = text.lower()
        workflow_markers = (
            "小q工作流",
            "q-workflow",
            "validation",
            "验证",
            "测试",
            "修复",
            "推送",
            "github",
            "bitbucket",
            "skill",
            "runtime",
            "source/runtime",
            "recommended next",
            "**recommended next**",
        )
        if not any(marker in lowered for marker in workflow_markers):
            return []
    return [f"first non-empty line {line_no} must be `{SLASH_GRAMMAR}`; {error}"]


def parse_card_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for raw in text.splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key = key.strip()
        if key in EXPERT_CARD_FIELDS:
            fields[key] = value.strip()
    return fields


def validate_expert_card(text: str) -> list[str]:
    errors: list[str] = []
    fields = parse_card_fields(text)
    for field in EXPERT_CARD_FIELDS:
        if not fields.get(field):
            errors.append(f"missing {field}")
    english = fields.get("English name", "")
    chinese = fields.get("Chinese name", "")
    role = fields.get("Expert role", "")
    if english not in STABLE_EXPERTS:
        errors.append("English name is not a stable expert alias")
        return errors
    expected_chinese = STABLE_EXPERTS[english]
    expected_role = f"{english} ({expected_chinese})"
    if chinese != expected_chinese:
        errors.append(f"Chinese name for {english} must be {expected_chinese}")
    if role != expected_role:
        errors.append(f"Expert role must be {expected_role}")
    run_instance = fields.get("Run instance", "")
    if run_instance == "local-pass" or run_instance.endswith("/pending"):
        # pending is acceptable only for a plan card. The text must say Subagent plan.
        if "Subagent plan" not in text:
            errors.append("pending Run instance is allowed only in Subagent plan before spawn")
    return errors


def parse_rule_blocks(text: str) -> list[tuple[int, dict[str, str]]]:
    blocks: list[tuple[int, dict[str, str]]] = []
    current: dict[str, str] | None = None
    start_line = 0
    fence = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            fence = not fence
            continue
        if not fence:
            continue
        if stripped.startswith("rule_id:"):
            if current:
                blocks.append((start_line, current))
            current = {"rule_id": stripped.split(":", 1)[1].strip()}
            start_line = line_no
            continue
        if current is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip()
            if key in REQUIRED_RULE_FIELDS:
                current[key] = value.strip()
    if current:
        blocks.append((start_line, current))
    return blocks


def check_rule_blocks(path: Path, text: str, findings: list[Finding]) -> None:
    blocks = parse_rule_blocks(text)
    if not blocks:
        add(findings, "blocker", "no-rule-blocks", path, "No fenced rule_id blocks found.")
        return
    seen: set[str] = set()
    for start_line, block in blocks:
        rule_id = block.get("rule_id", f"line-{start_line}")
        if rule_id in seen:
            add(findings, "blocker", "duplicate-rule-id", path, f"Duplicate rule_id {rule_id}.")
        seen.add(rule_id)
        missing = [field for field in REQUIRED_RULE_FIELDS if not block.get(field)]
        if missing:
            add(findings, "blocker", "incomplete-rule-block", path, f"Rule {rule_id} at line {start_line} missing fields: {', '.join(missing)}")
        status = block.get("status", "")
        if status.startswith("<") and status.endswith(">"):
            continue
        if status and status not in VALID_RULE_STATUS:
            add(findings, "blocker", "invalid-rule-status", path, f"Rule {rule_id} has invalid status {status}.")
        level = block.get("level", "")
        if level.startswith("<") and level.endswith(">"):
            continue
        if level and level not in VALID_RULE_LEVEL:
            add(findings, "blocker", "invalid-rule-level", path, f"Rule {rule_id} has invalid level {level}.")


def scan_status_examples(path: Path, text: str, findings: list[Finding]) -> None:
    for line_no, line in enumerate(text.splitlines(), start=1):
        if STATUS_LINE_CANDIDATE_RE.match(line.strip()):
            error = validate_status_line(line.strip())
            if error:
                all_lines = text.splitlines()
                context_start = max(0, line_no - 5)
                context = "\n".join(all_lines[context_start:line_no]).lower()
                if "invalid" in context or "invalid:" in context or "<route-or-skill-id>" in line or "<skill-id>" in line:
                    continue
                add(findings, "blocker", "bad-status-line-example", path, f"Line {line_no}: {error}")


def validate_recommended_next_block(text: str) -> list[str]:
    errors: list[str] = []
    lines = [line.rstrip() for line in text.splitlines()]
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == "**Recommended Next**")
    except StopIteration:
        return ["missing **Recommended Next** heading"]

    options: list[tuple[int, str]] = []
    for line in lines[start + 1:]:
        stripped = line.strip()
        if not stripped:
            if options:
                break
            continue
        match = NEXT_OPTION_RE.match(stripped)
        if not match:
            if options:
                break
            continue
        options.append((int(match.group("num")), match.group("body").strip()))

    if not (2 <= len(options) <= 4):
        errors.append("Recommended Next must contain 2-4 numbered options")
    expected_numbers = list(range(1, len(options) + 1))
    actual_numbers = [number for number, _ in options]
    if actual_numbers != expected_numbers:
        errors.append("Recommended Next option numbers must be consecutive from 1")
    if options and "(Recommended)" not in options[0][1]:
        errors.append("Recommended Next option 1 must be marked (Recommended)")
    if any(not body for _, body in options):
        errors.append("Recommended Next options must not be empty")
    return errors


def validate_format_defect_gate_replay(text: str) -> list[str]:
    errors: list[str] = []
    lower = text.lower()
    missing = [field for field in FORMAT_REPLAY_REQUIRED_FIELDS if field not in lower]
    if missing:
        errors.append("format replay missing fields: " + ", ".join(missing))
    if not any(term.lower() in lower for term in FORMAT_REPLAY_EVIDENCE_TERMS):
        errors.append("format replay evidence must name a replayable guard/readback")
    if "ledger: none" in lower and "user-found" in lower:
        errors.append("user-found format defects need a ledger entry or explicit non-recurring reason")
    return errors


def validate_lightweight_no_menu(text: str) -> list[str]:
    if "**Recommended Next**" in text:
        return ["lightweight answers must not force a Recommended Next menu"]
    return []


def validate_user_language_surface(text: str, language: str) -> list[str]:
    errors: list[str] = []
    normalized = language.lower()
    if normalized.startswith("zh"):
        forbidden = [label for label in ZH_FORBIDDEN_INTERNAL_LABELS if label in text]
        if forbidden:
            errors.append("Chinese user-facing output must translate internal tool labels: " + ", ".join(forbidden))
        if not re.search(r"[\u4e00-\u9fff]", text):
            errors.append("Chinese user-facing output must contain Chinese prose or labels")
    elif normalized.startswith("en"):
        if re.search(r"[\u4e00-\u9fff]", text):
            errors.append("English user-facing output should not contain untranslated Chinese prose")
    return errors


def check_format_defect_gate(root: Path, findings: list[Finding]) -> None:
    standard = root / "references" / "testing-standard.md"
    if not standard.is_file():
        add(findings, "blocker", "missing-testing-standard", standard, "testing-standard.md is required for format defect gates.")
        return
    text = read_utf8(standard, findings)
    if text is None:
        return
    missing = [term for term in FORMAT_GATE_DOC_TERMS if term not in text]
    if missing:
        add(findings, "blocker", "missing-format-gate-term", standard, "Missing format gate terms: " + ", ".join(missing))


def check_handoff_next_options(root: Path, findings: list[Finding]) -> None:
    guide = root / "references" / "full-guide.md"
    if not guide.is_file():
        add(findings, "blocker", "missing-full-guide", guide, "full-guide.md is required for handoff next-options guidance.")
        return
    text = read_utf8(guide, findings)
    if text is None:
        return
    missing = [marker for marker in NEXT_OPTIONS_GUIDE_MARKERS if marker not in text]
    if missing:
        add(findings, "blocker", "missing-next-options-guidance", guide, "Missing handoff next-options markers: " + ", ".join(missing))
    if "lightweight" not in text.lower() or "direct command result" not in text.lower():
        add(findings, "warning", "missing-lightweight-exception", guide, "Next-options guidance should preserve a lightweight path for small tasks.")
    block_errors = validate_recommended_next_block(text)
    if block_errors:
        add(findings, "blocker", "invalid-next-options-example", guide, "; ".join(block_errors))


def check_contract(root: Path, findings: list[Finding]) -> None:
    contract = root / "references" / "q-standard-contract.md"
    if not contract.is_file():
        add(findings, "fatal", "missing-contract", contract, "q-standard-contract.md is required.")
        return
    text = read_utf8(contract, findings)
    if text is None:
        return
    for token in ["MUST", "MUST NOT", "SHOULD", "MAY", "fatal", "blocker", "warning", "info"]:
        if token not in text:
            add(findings, "blocker", "missing-standard-token", contract, f"Missing standard token {token}.")
    for field in [f"{item}:" for item in REQUIRED_RULE_FIELDS]:
        if field not in text:
            add(findings, "blocker", "missing-rule-field", contract, f"Missing rule field {field}")
    blocks = parse_rule_blocks(text)
    parsed_ids = {block.get("rule_id", "") for _, block in blocks}
    required_real_rules = {
        "q-output-slash-status-line",
        "expert-dispatch-card-before-spawn",
        "warning-promotion-after-user-found-defect",
        "partial-work-ledger",
        "q-handoff-next-options",
        "format-defect-gate",
        "source-runtime-bidirectional-sync-before-stable",
        "q-user-language-surface",
        "q-human-loop-test-reusability",
    }
    missing_real_rules = sorted(required_real_rules - parsed_ids)
    if missing_real_rules:
        add(findings, "blocker", "missing-real-rule-block", contract, "Missing parsed real rule blocks: " + ", ".join(missing_real_rules))
    for _, block in blocks:
        if block.get("rule_id") == "q-handoff-next-options" and block.get("level") != "MUST":
            add(findings, "blocker", "next-options-not-must", contract, "q-handoff-next-options must be a MUST-level rule for substantial handoffs.")
    check_rule_blocks(contract, text, findings)
    scan_status_examples(contract, text, findings)
    check_handoff_next_options(root, findings)
    check_format_defect_gate(root, findings)


def check_base_command_contract(root: Path, findings: list[Finding]) -> None:
    path = root / "references" / "base-command-contract.json"
    if not path.is_file():
        add(findings, "blocker", "missing-base-command-contract", path, "Base command contract is required.")
        return
    text = read_utf8(path, findings)
    if text is None:
        return
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        add(findings, "blocker", "invalid-base-command-contract", path, str(exc))
        return
    if data.get("version") != 3 or data.get("surface_schema_version") != 1:
        add(findings, "blocker", "stale-base-command-contract", path, "Expected contract v3 with surface schema v1.")
        return
    surfaces = data.get("surfaces") if isinstance(data.get("surfaces"), dict) else {}
    required = {"todo-two-line", "selected-todo-item", "help-html-first", "token-dashboard-summary", "quick-resume-fixed-panel"}
    missing = sorted(required - set(surfaces))
    if missing:
        add(findings, "blocker", "missing-base-command-surfaces", path, ", ".join(missing))
    for surface_id in required & set(surfaces):
        spec = surfaces[surface_id]
        if not isinstance(spec, dict) or "required_fields" not in spec or "side_effect" not in spec:
            add(findings, "blocker", "incomplete-base-command-surface", path, surface_id)
            continue
        if not isinstance(spec.get("required_shape"), list) or not spec["required_shape"]:
            add(findings, "blocker", "missing-base-command-shape", path, surface_id)
    todo_surface = surfaces.get("todo-two-line", {})
    if "chinese-name-and-summary" not in todo_surface.get("required_shape", []) or "compact-localized-detail" not in todo_surface.get("required_shape", []):
        add(findings, "blocker", "incomplete-todo-language-contract", path, "TODO list must combine deterministic Chinese display metadata with a compact localized detail; full detail belongs to numeric selection.")
    selected_surface = surfaces.get("selected-todo-item", {})
    if "full-localized-description" not in selected_surface.get("required_shape", []) or "labeled-multiline-detail" not in selected_surface.get("required_shape", []):
        add(findings, "blocker", "incomplete-todo-selection-format-contract", path, "TODO selection must render full localized detail as labeled multiline clauses.")
    token_surface = surfaces.get("token-dashboard-summary", {})
    if token_surface.get("max_chat_lines") != 5 or "cache-health" not in token_surface.get("required_shape", []):
        add(findings, "blocker", "incomplete-token-summary-contract", path, "TOKEN requires a five-line cache-aware summary.")
    command_ids = {item.get("id") for item in data.get("commands", []) if isinstance(item, dict)}
    if not {"todo-list", "help", "token-dashboard", "quick-resume"}.issubset(command_ids):
        add(findings, "blocker", "missing-base-command-routes", path, "Four foundational routes are required.")
    fast_paths = root / "references" / "command-fast-paths.md"
    fast_text = read_utf8(fast_paths, findings) if fast_paths.is_file() else None
    if fast_text is None:
        add(findings, "blocker", "missing-command-fast-paths", fast_paths, "Command fast paths are required.")
    else:
        forbidden_help_rules = ["is a zero-tool micro path", "answer directly in 6 lines or fewer"]
        for phrase in forbidden_help_rules:
            if phrase in fast_text:
                add(findings, "blocker", "conflicting-help-rule", fast_paths, f"Obsolete Help rule remains: {phrase}")
        if fast_text.count("HTML-first") < 2:
            add(findings, "blocker", "missing-html-first-help-rule", fast_paths, "Both default and detailed Help sections must stay HTML-first.")


def resolve_agent_roster_root(root: Path) -> Path | None:
    candidates = [
        root.parent / "q-agent-roster",
        Path.home() / ".codex" / "skills" / "q-agent-roster",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def check_output_protocol(root: Path, findings: list[Finding]) -> None:
    roster_root = resolve_agent_roster_root(root)
    protocol = (roster_root / "references" / "output-protocol.md") if roster_root else (root.parent / "q-agent-roster" / "references" / "output-protocol.md")
    if not protocol.is_file():
        add(findings, "blocker", "missing-output-protocol", protocol, "Output protocol is required for q-standard gates.")
        return
    text = read_utf8(protocol, findings)
    if text is None:
        return
    bad = "Xiao Q workflow / <route-or-skill> / <confirmed|partial|blocked|done>"
    if bad in text:
        add(findings, "blocker", "old-status-grammar", protocol, "Old compact status grammar mixes route and state slots.")
    if SLASH_GRAMMAR not in text:
        add(findings, "blocker", "missing-status-grammar", protocol, "Missing canonical Chinese slash status grammar.")
    lower_text = text.lower()
    if "status belongs on the next line" not in lower_text and "state belongs on the next line" not in lower_text:
        add(findings, "warning", "missing-status-separation", protocol, "Protocol should state that status is separate from the slash line.")
    scan_status_examples(protocol, text, findings)


def check_dispatch_policy(root: Path, findings: list[Finding]) -> None:
    roster_root = resolve_agent_roster_root(root)
    policy = (roster_root / "references" / "auto-dispatch-policy.md") if roster_root else (root.parent / "q-agent-roster" / "references" / "auto-dispatch-policy.md")
    if not policy.is_file():
        add(findings, "blocker", "missing-dispatch-policy", policy, "Auto dispatch policy is required for q-standard gates.")
        return
    text = read_utf8(policy, findings)
    if text is None:
        return
    if "Always announce the dispatch card before spawning" not in text:
        add(findings, "blocker", "dispatch-card-not-before", policy, "Dispatch policy must require card before real subagent spawn.")
    if "Run instance" not in text or "Chinese name" not in text:
        add(findings, "blocker", "dispatch-card-fields", policy, "Dispatch card must include Run instance and Chinese name.")
    required_dispatch_terms = {
        "one dispatch card per real subagent",
        "retry after a failed spawn",
        "backfill the final mapping",
    }
    missing_terms = sorted(term for term in required_dispatch_terms if term not in text)
    if missing_terms:
        add(findings, "blocker", "dispatch-card-per-subagent-missing", policy, "Dispatch policy missing multi-agent card hardening terms: " + ", ".join(missing_terms))


def run_self_test(findings: list[Finding]) -> None:
    if validate_status_line(GOOD_STATUS) is not None:
        add(findings, "fatal", "selftest-good-status", "self-test", "Valid status line was rejected.")
    if validate_status_line(BAD_STATUS) is None:
        add(findings, "fatal", "selftest-bad-status", "self-test", "Invalid status line was accepted.")
    if validate_status_line(BAD_ROUTE_STATUS) is None:
        add(findings, "fatal", "selftest-bad-route-status", "self-test", "Invalid temporary non-skill second slot was accepted.")
    if validate_status_line(BAD_SCRIPT_ROUTE_STATUS) is None:
        add(findings, "fatal", "selftest-bad-script-route-status", "self-test", "Invalid script/check non-skill second slot was accepted.")
    skill_slot_valid = [
        "q-workflow",
        "q-agent-roster",
    ]
    skill_slot_invalid = [
        "validation",
        "sync",
        "release",
        "source-runtime-audit",
        "format-check",
        "human-loop-test",
        "workflow-audit",
        "q-standard-check",
        "release-readiness",
        "test-runner",
        "workflow-distiller",
        "q-unregistered-workflow-fixture",
        "q-unregistered-format-fixture",
        "gmppt-study-workflow",
    ]
    for skill in skill_slot_valid:
        sample = f"小Q工作流 / {skill} / 格式门禁复测"
        if validate_status_line(sample) is not None:
            add(findings, "fatal", f"selftest-skill-slot-valid-{skill}", "self-test", f"Valid skill id was rejected: {skill}")
    for skill in skill_slot_invalid:
        sample = f"小Q工作流 / {skill} / 格式门禁复测"
        if validate_status_line(sample) is None:
            add(findings, "fatal", f"selftest-skill-slot-invalid-{skill}", "self-test", f"Invalid non-skill second slot was accepted: {skill}")
    chinese = STABLE_EXPERTS["Workflow Distiller"]
    good_card = f"""Subagent plan
Expert role: Workflow Distiller ({chinese})
English name: Workflow Distiller
Chinese name: {chinese}
Run instance: explorer/pending
Mode: subagent-as-tool
Mission: Review workflow standard contract
Permissions: read-only
Boundaries: no push/publish/credentials
"""
    bad_card = """Subagent start
Expert role: Archimedes
English name: Archimedes
Run instance: explorer/Archimedes/019
"""
    incomplete_card = f"""Subagent start
Expert role: Workflow Distiller ({chinese})
English name: Workflow Distiller
Chinese name: {chinese}
Run instance: explorer/Peirce/019
"""
    if validate_expert_card(good_card):
        add(findings, "fatal", "selftest-good-card", "self-test", "Valid expert card was rejected.")
    if not validate_expert_card(bad_card):
        add(findings, "fatal", "selftest-bad-card", "self-test", "Invalid expert card was accepted.")
    if not validate_expert_card(incomplete_card):
        add(findings, "fatal", "selftest-incomplete-card", "self-test", "Incomplete expert card was accepted.")

    with TemporaryDirectory() as tmp:
        fixture = Path(tmp) / "rule.md"
        fixture.write_text("```text\nrule_id: x\nlevel: MUST\n```\n", encoding="utf-8")
        local_findings: list[Finding] = []
        check_rule_blocks(fixture, fixture.read_text(encoding="utf-8"), local_findings)
        if not any(item.code == "incomplete-rule-block" for item in local_findings):
            add(findings, "fatal", "selftest-rule-fields", "self-test", "Incomplete rule block was accepted.")
        status_fixture = Path(tmp) / "status.md"
        status_fixture.write_text(GOOD_STATUS + "\n" + BAD_STATUS + "\n", encoding="utf-8")
        local_findings = []
        scan_status_examples(status_fixture, status_fixture.read_text(encoding="utf-8"), local_findings)
        if not any(item.code == "bad-status-line-example" for item in local_findings):
            add(findings, "fatal", "selftest-status-scan", "self-test", "Bad status example scan did not fire.")
        valid_next_two = """**Recommended Next**
1. A (Recommended)
2. B
"""
        valid_next_four = """**Recommended Next**
1. Continue GitHub fresh-clone validation. (Recommended)
2. Continue remaining independent test items.
3. Run 1 then 2 in order.
4. Give a different direction.
"""
        invalid_next_missing_heading = """Next
1. Continue. (Recommended)
2. Stop.
"""
        invalid_next_one = """**Recommended Next**
1. Continue GitHub fresh-clone validation. (Recommended)
"""
        invalid_next_five = """**Recommended Next**
1. A (Recommended)
2. B
3. C
4. D
5. E
"""
        invalid_next_nonconsecutive = """**Recommended Next**
1. A (Recommended)
3. C
"""
        invalid_next_missing_recommended = """**Recommended Next**
1. A
2. B
"""
        tiny_answer = "Handled; validation was not needed for this one-line answer."
        tiny_with_menu = tiny_answer + "\n\n" + valid_next_four
        for label, sample in (("two", valid_next_two), ("four", valid_next_four)):
            errors = validate_recommended_next_block(sample)
            if errors:
                add(findings, "fatal", f"selftest-good-next-options-{label}", "self-test", "Valid Recommended Next block was rejected: " + "; ".join(errors))
        for label, sample in (
            ("missing-heading", invalid_next_missing_heading),
            ("one-option", invalid_next_one),
            ("five-options", invalid_next_five),
            ("nonconsecutive", invalid_next_nonconsecutive),
            ("missing-recommended", invalid_next_missing_recommended),
        ):
            if not validate_recommended_next_block(sample):
                add(findings, "fatal", f"selftest-bad-next-options-{label}", "self-test", "Invalid Recommended Next block was accepted.")
        if validate_lightweight_no_menu(tiny_answer):
            add(findings, "fatal", "selftest-lightweight-answer", "self-test", "Lightweight answer without menu was rejected.")
        if not validate_lightweight_no_menu(tiny_with_menu):
            add(findings, "fatal", "selftest-lightweight-menu", "self-test", "Lightweight answer with forced menu was accepted.")
        good_zh_card = """项目识别摘要
- 项目：smart-sensor-board
- Git：main，https://github.com/example/smart-sensor-board.git

详细信息
- 硬件：hardware/sensor_board.kicad_sch
- 固件/软件：firmware/src/main.c
- 文档/PPT：docs/demo-slides.pptx

登记写入计划
- 写入目标：PROJECT_REGISTRY.md
- 是否复制项目内容：否
- 是否 push：否
"""
        bad_zh_card = """Project summary:
  Name: smart-sensor-board

Adaptive details:
  HardwareDetail: hardware/sensor_board.kicad_sch
  FirmwareOrSoftwareDetail: firmware/src/main.c
  DocumentDetail: docs/demo-slides.pptx
"""
        if validate_user_language_surface(good_zh_card, "zh"):
            add(findings, "fatal", "selftest-good-zh-language-surface", "self-test", "Valid Chinese language surface was rejected.")
        if not validate_user_language_surface(bad_zh_card, "zh"):
            add(findings, "fatal", "selftest-bad-zh-language-surface", "self-test", "English internal labels in Chinese output were accepted.")
        good_en_card = "Project summary\n- Project: smart-sensor-board\n"
        bad_en_card = "Project summary\n- 项目: smart-sensor-board\n"
        if validate_user_language_surface(good_en_card, "en"):
            add(findings, "fatal", "selftest-good-en-language-surface", "self-test", "Valid English language surface was rejected.")
        if not validate_user_language_surface(bad_en_card, "en"):
            add(findings, "fatal", "selftest-bad-en-language-surface", "self-test", "Chinese prose in English output was accepted.")
        good_format_replay = """defect_class: user-found output grammar regression
fix: patched q_standard_check fixture and owner source
evidence: q_standard_check.py --self-test; text_format_guard.py readback
ledger: q-text-format-hygiene/references/regression-ledger.md#handoff-next-options-fixture-false-pass
surfaces_checked: source/runtime/bootstrap
skipped_surfaces: none
"""
        missing_ledger_replay = """defect_class: user-found output grammar regression
fix: patched q_standard_check fixture and owner source
evidence: q_standard_check.py --self-test
surfaces_checked: source/runtime
skipped_surfaces: none
"""
        missing_evidence_replay = """defect_class: output grammar regression
fix: patched owner source
evidence: done
ledger: none
surfaces_checked: source/runtime
skipped_surfaces: bootstrap not applicable
"""
        if validate_format_defect_gate_replay(good_format_replay):
            add(findings, "fatal", "selftest-good-format-defect-replay", "self-test", "Valid format defect replay was rejected.")
        if not validate_format_defect_gate_replay(missing_ledger_replay):
            add(findings, "fatal", "selftest-format-replay-missing-ledger", "self-test", "Format replay without ledger field was accepted.")
        if not validate_format_defect_gate_replay(missing_evidence_replay):
            add(findings, "fatal", "selftest-format-replay-missing-evidence", "self-test", "Format replay without replayable evidence was accepted.")
        good_chat = "小Q工作流 / q-workflow / 格式硬化验证\n状态：done\n"
        bad_chat = "已完成格式硬化验证。\n\n**Recommended Next**\n1. 继续（Recommended）\n2. 暂停\n"
        tiny_chat = "可以，已记录。"
        if validate_chat_output(good_chat):
            add(findings, "fatal", "selftest-good-chat-output-status-line", "self-test", "Valid chat output status line was rejected.")
        if not validate_chat_output(bad_chat):
            add(findings, "fatal", "selftest-bad-chat-output-status-line", "self-test", "Workflow chat output without slash status line was accepted.")
        if validate_chat_output(tiny_chat, allow_lightweight=True):
            add(findings, "fatal", "selftest-lightweight-chat-output", "self-test", "Lightweight natural chat output was rejected with allow_lightweight.")
        raw_agent_packet = "AGENT-REPORT v1\nprotocol: Q-AGENT-PACKET\nstatus: done\n"
        wrapped_agent_packet = "小Q工作流 / q-agent-roster / 汇总独立审计\n\n" + raw_agent_packet
        if not validate_chat_output(raw_agent_packet):
            add(findings, "fatal", "selftest-user-visible-raw-agent-packet", "self-test", "Raw AGENT-REPORT was accepted as a user-visible update without the parent wrapper.")
        if validate_chat_output(wrapped_agent_packet):
            add(findings, "fatal", "selftest-wrapped-agent-packet", "self-test", "Parent-wrapped AGENT-REPORT was rejected as user-visible output.")
        good_handoff_chat = "\u5c0fQ\u5de5\u4f5c\u6d41 / q-workflow / \u683c\u5f0f\u95e8\u7981\u5b8c\u6210\n\u72b6\u6001\uff1adone\n\n**Recommended Next**\n1. \u5ba1\u67e5\u672c\u8f6e\u6539\u52a8 (Recommended)\n2. \u7ee7\u7eed\u5269\u4f59\u6d4b\u8bd5\n"
        missing_next_handoff_chat = "\u5c0fQ\u5de5\u4f5c\u6d41 / q-workflow / \u683c\u5f0f\u95e8\u7981\u5b8c\u6210\n\u72b6\u6001\uff1adone\n"
        bad_next_handoff_chat = "\u5c0fQ\u5de5\u4f5c\u6d41 / q-workflow / \u683c\u5f0f\u95e8\u7981\u5b8c\u6210\n\u72b6\u6001\uff1adone\n\n**Recommended Next**\n1. \u7ee7\u7eed\n"
        if validate_chat_output(good_handoff_chat) or validate_recommended_next_block(good_handoff_chat):
            add(findings, "fatal", "selftest-good-handoff-chat-output", "self-test", "Valid handoff chat output with Recommended Next was rejected.")
        if not validate_recommended_next_block(missing_next_handoff_chat):
            add(findings, "fatal", "selftest-missing-next-handoff-chat-output", "self-test", "Substantial handoff without Recommended Next was accepted.")
        if not validate_recommended_next_block(bad_next_handoff_chat):
            add(findings, "fatal", "selftest-bad-next-handoff-chat-output", "self-test", "Malformed Recommended Next handoff was accepted.")
        mojibake_fixture = Path(tmp) / "mojibake.md"
        mojibake_fixture.write_text("Broken replacement marker: \ufffd\n", encoding="utf-8")
        local_findings = []
        read_utf8(mojibake_fixture, local_findings)
        if not any(item.code == "mojibake-marker" for item in local_findings):
            add(findings, "fatal", "selftest-replacement-character", "self-test", "Replacement-character mojibake was accepted.")


def main() -> int:
    configure_output()
    parser = argparse.ArgumentParser(description="Check q-workflow standard contract and protocol gates.")
    parser.add_argument("--root", default=None, help="Path to skills/q-workflow root.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in regression fixtures.")
    parser.add_argument("--format-replay", default=None, help="Validate a format-defect replay handoff/report file.")
    parser.add_argument("--chat-output", default=None, help="Validate a user-visible workflow chat output file starts with the slash status line.")
    parser.add_argument("--handoff-output", default=None, help="Validate a substantial handoff/final output: slash status line plus required Recommended Next block.")
    parser.add_argument("--allow-lightweight", action="store_true", help="Allow natural-language tiny outputs for --chat-output only when no workflow markers appear.")
    parser.add_argument("--require-next-options", action="store_true", help="Require a valid Recommended Next block for substantial workflow handoff chat outputs.")
    parser.add_argument("--language-output", default=None, help="Validate a user-facing output file against --language.")
    parser.add_argument("--language", default="zh", help="Preferred output language for --language-output, for example zh or en.")
    args = parser.parse_args()

    findings: list[Finding] = []
    if args.root:
        root = Path(args.root).resolve()
        check_contract(root, findings)
        check_base_command_contract(root, findings)
        check_output_protocol(root, findings)
        check_dispatch_policy(root, findings)
    if args.self_test:
        run_self_test(findings)
    if args.format_replay:
        replay_path = Path(args.format_replay).resolve()
        replay_text = read_utf8(replay_path, findings)
        if replay_text is not None:
            for error in validate_format_defect_gate_replay(replay_text):
                add(findings, "blocker", "invalid-format-replay", replay_path, error)
    if args.language_output:
        output_path = Path(args.language_output).resolve()
        output_text = read_utf8(output_path, findings)
        if output_text is not None:
            for error in validate_user_language_surface(output_text, args.language):
                add(findings, "blocker", "invalid-language-surface", output_path, error)
    if args.chat_output:
        chat_path = Path(args.chat_output).resolve()
        chat_text = read_utf8(chat_path, findings)
        if chat_text is not None:
            for error in validate_chat_output(chat_text, allow_lightweight=args.allow_lightweight):
                add(findings, "blocker", "invalid-chat-output-status-line", chat_path, error)
            if args.require_next_options:
                for error in validate_recommended_next_block(chat_text):
                    add(findings, "blocker", "invalid-chat-output-next-options", chat_path, error)
    if args.handoff_output:
        handoff_path = Path(args.handoff_output).resolve()
        handoff_text = read_utf8(handoff_path, findings)
        if handoff_text is not None:
            for error in validate_chat_output(handoff_text, allow_lightweight=False):
                add(findings, "blocker", "invalid-handoff-output-status-line", handoff_path, error)
            for error in validate_recommended_next_block(handoff_text):
                add(findings, "blocker", "invalid-handoff-output-next-options", handoff_path, error)
    if not args.root and not args.self_test and not args.format_replay and not args.language_output and not args.chat_output and not args.handoff_output:
        parser.error("provide --root, --self-test, --format-replay, --language-output, --chat-output, --handoff-output, or a combination")

    order = {"fatal": 0, "blocker": 1, "warning": 2, "info": 3}
    findings.sort(key=lambda item: (order.get(item.severity, 9), item.code, item.path))
    fatal = sum(1 for item in findings if item.severity == "fatal")
    blocker = sum(1 for item in findings if item.severity == "blocker")
    warning = sum(1 for item in findings if item.severity == "warning")
    status = "FAIL" if fatal or blocker else "PASS"
    print(f"q-standard-check: {status} ({fatal} fatal, {blocker} blocker, {warning} warning)")
    for item in findings:
        safe_message = item.message.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        print(f"[{item.severity.upper()}] {item.code}: {item.path} - {safe_message}".encode("utf-8", errors="replace").decode("utf-8", errors="replace"))
    return 1 if fatal or blocker else 0


if __name__ == "__main__":
    raise SystemExit(main())
