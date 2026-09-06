#!/usr/bin/env python3
r"""Build a conservative q-workflow release readiness report.

This gate is intentionally evidence-first. It does not publish, push, edit, or
promote anything. It aggregates mechanical audit status and release evidence so
`pilot-ready`, `team-ready`, and `public-ready` labels are not inferred from
confidence alone.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import workflow_audit


@dataclass(frozen=True)
class GateResult:
    status: str
    gate: str
    evidence: str
    next_action: str


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


def escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def status_rank(status: str) -> int:
    return {"BLOCKED": 0, "WARN": 1, "INFO": 2, "PASS": 3, "N/A": 4}.get(status, 9)


def has_explicit_pass(text: str) -> bool:
    lowered = text.lower()
    if re.search(r"(?m)^\s*evidence type\s*:\s*.*(proxy|template)", lowered):
        return False
    if re.search(r"(?m)^\s*status\s*:\s*.*(proxy|template)", lowered):
        return False
    explicit_pass = re.search(r"(?m)^\s*(status|verdict|result)\s*:\s*pass\s*$", lowered) is not None
    explicit_fail = re.search(r"(?m)^\s*(status|verdict|result)\s*:\s*(fail|blocked)\s*$", lowered) is not None
    return explicit_pass and not explicit_fail


def find_latest(root: Path, patterns: tuple[str, ...]) -> Path | None:
    if not root.exists():
        return None
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(path for path in root.rglob(pattern) if path.is_file())
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


def find_latest_explicit_pass(root: Path, patterns: tuple[str, ...]) -> Path | None:
    if not root.exists():
        return None
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(path for path in root.rglob(pattern) if path.is_file())
    if not matches:
        return None
    passed = [path for path in matches if has_explicit_pass(read_text(path))]
    if passed:
        return max(passed, key=lambda path: path.stat().st_mtime)
    return max(matches, key=lambda path: path.stat().st_mtime)



def command_snippet(result: subprocess.CompletedProcess[str]) -> str:
    combined = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part and part.strip())
    if not combined:
        return f"exit={result.returncode}"
    return combined.replace("\r", "").replace("\n", " | ")[:700]


def run_command_gate(gate: str, command: list[str], next_action: str, cwd: Path | None = None, timeout: int = 60) -> GateResult:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return GateResult("BLOCKED", gate, f"command not found: {exc}", next_action)
    except subprocess.TimeoutExpired:
        return GateResult("BLOCKED", gate, f"timeout after {timeout}s: {' '.join(command)}", next_action)
    status = "PASS" if result.returncode == 0 else "BLOCKED"
    return GateResult(status, gate, command_snippet(result), next_action)


def source_runtime_sync_gate(paths: dict[str, Path]) -> GateResult:
    source = paths["starter_q_workflow"]
    runtime = paths["runtime_q_workflow"]
    script = source / "scripts" / "audit_source_runtime_sync.py"
    if not source.is_dir():
        return GateResult("BLOCKED", "Source/runtime sync", f"missing source skill folder: {source}", "Set Q_WORKFLOW_HUB_SOURCE to the durable q-workflow source skill before release labeling.")
    if not runtime.is_dir():
        return GateResult("BLOCKED", "Source/runtime sync", f"missing runtime skill folder: {runtime}", "Install or refresh the runtime q-workflow skill before release labeling.")
    if not script.is_file():
        return GateResult("BLOCKED", "Source/runtime sync", f"missing {script}", "Restore audit_source_runtime_sync.py to source/runtime before release labeling.")
    return run_command_gate(
        "Source/runtime sync",
        [
            sys.executable,
            str(script),
            "--repo-root",
            str(source.parent.parent),
            "--skill-name",
            source.name,
            "--runtime-root",
            str(runtime.parent),
        ],
        "Backfill runtime-newer changes to source or refresh runtime from source before release labeling.",
        timeout=60,
    )


def standard_contract_gate(paths: dict[str, Path]) -> GateResult:
    script = paths["runtime_q_workflow"] / "scripts" / "q_standard_check.py"
    if not script.is_file():
        return GateResult("BLOCKED", "Standard contract", f"missing {script}", "Restore q_standard_check.py to runtime/source/starter.")
    return run_command_gate(
        "Standard contract",
        [sys.executable, str(script), "--root", str(paths["runtime_q_workflow"]), "--self-test"],
        "Fix q-standard-contract, output protocol, or expert dispatch protocol blockers before release labeling.",
        timeout=60,
    )


def encoding_release_gate(paths: dict[str, Path]) -> GateResult:
    script = paths["runtime_q_workflow"] / "scripts" / "encoding_guard.py"
    targets = [
        paths["runtime_q_workflow"] / "SKILL.md",
        paths["runtime_q_workflow"] / "references" / "command-fast-paths.md",
        paths["standalone_q_workflow"] / "SKILL.md",
        paths["standalone_q_workflow"] / "references" / "command-fast-paths.md",
        paths["starter_q_workflow"] / "SKILL.md",
        paths["starter_q_workflow"] / "references" / "command-fast-paths.md",
        paths["hub_personal_state"] / "ACTIVE_WORK.md",
        paths["runtime_personal_state"] / "ACTIVE_WORK.md",
    ]
    missing = [str(path) for path in [script, *targets] if not path.exists()]
    if missing:
        return GateResult("BLOCKED", "Encoding guard", "missing: " + "; ".join(missing), "Restore missing text surfaces or narrow the release scope.")
    return run_command_gate(
        "Encoding guard",
        [sys.executable, str(script), *[str(path) for path in targets]],
        "Repair mojibake or invalid UTF-8 before release labeling.",
        timeout=60,
    )


def experiment_validation_gate(paths: dict[str, Path]) -> GateResult:
    script = paths["runtime_q_workflow"] / "scripts" / "validate_experiments.py"
    if not script.is_file():
        return GateResult("BLOCKED", "Experiment validation", f"missing {script}", "Restore validate_experiments.py before release labeling.")
    return run_command_gate(
        "Experiment validation",
        [sys.executable, str(script)],
        "Fix experiment schema/dependencies before release labeling.",
        cwd=paths["runtime_q_workflow"],
        timeout=60,
    )


def configured_hook_events(hook_root: Path) -> tuple[set[str], str | None]:
    hooks_json = workflow_audit.default_user_home() / ".codex" / "hooks.json"
    text = read_text(hooks_json)
    if not text:
        return set(), f"missing or unreadable {hooks_json}"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return set(), f"invalid JSON in {hooks_json}: {exc}"
    expected = str(hook_root / "q-workflow-hook.ps1").lower()
    events = payload.get("hooks", {})
    if not isinstance(events, dict):
        return set(), f"hooks.json has no hooks mapping: {hooks_json}"
    matched: set[str] = set()
    for event, entries in events.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for hook in entry.get("hooks", []):
                if not isinstance(hook, dict):
                    continue
                command = str(hook.get("command", "")).lower()
                if expected in command:
                    matched.add(str(event))
    return matched, None

def hook_visibility_gate(paths: dict[str, Path]) -> GateResult:
    hook_root = paths["hub_personal_state"] / "hooks"
    status_script = hook_root / "hook-status.ps1"
    smoke_script = hook_root / "hook-smoke.ps1"
    missing = [str(path) for path in (status_script, smoke_script, hook_root / "q-workflow-hook.ps1") if not path.is_file()]
    if missing:
        return GateResult("BLOCKED", "Hook visibility", "missing: " + "; ".join(missing), "Install or document hook status/smoke scripts before team-ready labeling.")
    matched_events, config_error = configured_hook_events(hook_root)
    if config_error:
        return GateResult("BLOCKED", "Hook visibility", config_error, "Fix .codex/hooks.json before team-ready labeling.")
    required_events = {"UserPromptSubmit", "PreCompact", "PostCompact", "Stop"}
    missing_events = sorted(required_events.difference(matched_events))
    if missing_events:
        return GateResult("BLOCKED", "Hook visibility", "hooks.json missing q-workflow-hook.ps1 for events: " + ", ".join(missing_events), "Fix .codex/hooks.json before team-ready labeling.")
    status_gate = run_command_gate(
        "Hook visibility",
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(status_script), "-Summary"],
        "Fix hook status visibility before team-ready labeling.",
        timeout=60,
    )
    if status_gate.status != "PASS":
        return status_gate
    smoke_gate = run_command_gate(
        "Hook visibility",
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(smoke_script)],
        "Fix hook smoke test before team-ready labeling.",
        timeout=60,
    )
    if smoke_gate.status != "PASS":
        return smoke_gate
    return GateResult("PASS", "Hook visibility", "hooks.json events=" + ",".join(sorted(matched_events)) + " ; " + status_gate.evidence + " ; " + smoke_gate.evidence, "Keep hook status and smoke evidence with release report.")

def mechanical_audit_gate() -> GateResult:
    paths = workflow_audit.default_paths()
    checks = (
        ("audit", workflow_audit.run_checks),
        ("hygiene", workflow_audit.run_checks),
        ("regression", workflow_audit.run_regression_checks),
    )
    summaries: list[str] = []
    blockers = 0
    for name, runner in checks:
        _inventory, findings = runner(paths)
        count = len([item for item in findings if item.severity in {"P0", "P1"}])
        blockers += count
        summaries.append(f"{name}: P0/P1={count}, findings={len(findings)}")
    if blockers:
        return GateResult("BLOCKED", "Mechanical audit", "; ".join(summaries), "Fix P0/P1 audit findings before release labeling.")
    return GateResult("PASS", "Mechanical audit", "; ".join(summaries), "Keep this gate in the release report.")


def scenario_gate(scenario_dir: Path, min_scenarios: int) -> GateResult:
    if not scenario_dir.exists():
        return GateResult(
            "BLOCKED",
            "Top-task scenario logs",
            f"Missing scenario directory: {scenario_dir}",
            f"Record at least {min_scenarios} colleague top-task scenario logs.",
        )
    candidates = [path for path in scenario_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".md", ".json", ".txt"}]
    passed = [path for path in candidates if has_explicit_pass(read_text(path))]
    if len(passed) >= min_scenarios:
        return GateResult("PASS", "Top-task scenario logs", f"{len(passed)} passing logs in {scenario_dir}", "Keep scenario evidence with the release report.")
    return GateResult(
        "BLOCKED",
        "Top-task scenario logs",
        f"{len(passed)}/{min_scenarios} passing logs found in {scenario_dir}",
        "Run cold-start colleague scenarios and mark each result explicitly as pass or blocked.",
    )


def usability_gate(report_path: Path | None, reports_root: Path, require_explicit: bool = False) -> GateResult:
    if require_explicit and report_path is None:
        return GateResult(
            "BLOCKED",
            "Usability Validator",
            "Team/public release requires an explicitly selected trace-bound usability report.",
            "Pass --usability-report for the exact release candidate; do not rely on an unrelated latest report.",
        )
    path = report_path or find_latest_explicit_pass(reports_root, ("*usability*validator*.md", "*usability*.md"))
    if path is None:
        return GateResult(
            "BLOCKED",
            "Usability Validator",
            f"No usability report found under {reports_root}",
            "Run Usability Validator from a cold-start colleague perspective.",
        )
    text = read_text(path)
    if has_explicit_pass(text):
        return GateResult("PASS", "Usability Validator", str(path), "Keep the validator report with release evidence.")
    return GateResult("BLOCKED", "Usability Validator", f"No explicit pass in {path}", "Update or rerun the validator report with an explicit verdict.")


def signoff_gate(signoff_path: Path) -> GateResult:
    text = read_text(signoff_path)
    if not text:
        return GateResult(
            "BLOCKED",
            "Release signoff",
            f"Missing or empty signoff file: {signoff_path}",
            "Create a signoff file with scope, approver, approval status, limitations, commit IDs, and push status.",
        )
    approved = re.search(r"(?im)^\s*(approval|approved|xiao q approval)\s*:\s*yes\s*$", text) is not None
    approved = approved or re.search(r"(?im)^\s*xiao q\s*:\s*approved\s*$", text) is not None
    if approved:
        return GateResult("PASS", "Release signoff", str(signoff_path), "Keep signoff immutable for this release candidate.")
    return GateResult("BLOCKED", "Release signoff", f"No explicit Xiao Q approval in {signoff_path}", "Add explicit approval only after Xiao Q approves this release candidate.")


def public_sanitization_gate(target: str, signoff_path: Path, reports_root: Path) -> GateResult:
    if target != "public":
        return GateResult("N/A", "Public sanitization", f"Target is {target}", "Run this gate only for public-ready or GitHub-bound release candidates.")
    text = read_text(signoff_path)
    latest = find_latest(reports_root, ("*public*sanit*.md", "*public*scan*.md", "*secret*scan*.md"))
    combined = text + "\n" + (read_text(latest) if latest else "")
    if has_explicit_pass(combined) and "public" in combined.lower():
        evidence = str(latest or signoff_path)
        return GateResult("PASS", "Public sanitization", evidence, "Keep the public scan report with release evidence.")
    return GateResult("BLOCKED", "Public sanitization", "No explicit public sanitization pass found", "Run public-safe rewrite, secret scan, licensing review, and approval before public-ready.")



RECOVERY_REGRESSION_CASES = {
    "active-conflict-numbered-choice",
    "paused-conflict-numbered-choice",
    "closed-thread-context-only",
    "recommendation-only-context-only",
    "explicit-reopen-allowed",
}


def recovery_surface_hashes(root: Path) -> dict[str, str]:
    relative_paths = ("SKILL.md", "references/recovery-routing.md")
    hashes: dict[str, str] = {}
    for relative in relative_paths:
        target = root / relative
        if target.is_file():
            hashes[relative] = hashlib.sha256(target.read_bytes()).hexdigest()
    return hashes


def validate_recovery_regression_report(path: Path | None, paths: dict[str, Path] | None = None) -> tuple[bool, str]:
    if path is None:
        return False, "No explicit recovery regression report selected."
    if not path.is_file():
        return False, f"Recovery regression report is missing: {path}"
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        return False, f"Recovery regression report is not valid JSON: {path} ({exc})"

    cases = payload.get("cases")
    if payload.get("format_version") != 1 or payload.get("status") != "pass" or not isinstance(cases, list):
        return False, f"Recovery regression report must have format_version=1, status=pass, and a cases list: {path}"
    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or len(trace_id.strip()) < 8:
        return False, f"Recovery regression report requires a durable trace_id: {path}"
    generated_at = payload.get("generated_at")
    try:
        parsed = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return False, f"Recovery regression generated_at must include a timezone: {path}"
    except ValueError:
        return False, f"Recovery regression generated_at must be ISO-8601: {path}"
    if not isinstance(payload.get("generator"), str) or not payload["generator"].strip():
        return False, f"Recovery regression report requires a generator id: {path}"
    if not isinstance(payload.get("command"), str) or not payload["command"].strip():
        return False, f"Recovery regression report requires the replay command: {path}"
    if paths is not None:
        expected_source = recovery_surface_hashes(paths["starter_q_workflow"])
        expected_runtime = recovery_surface_hashes(paths["runtime_q_workflow"])
        if payload.get("source_hashes") != expected_source:
            return False, f"Recovery regression source_hashes do not match current authority: {path}"
        if payload.get("runtime_hashes") != expected_runtime:
            return False, f"Recovery regression runtime_hashes do not match current runtime: {path}"
        if expected_source != expected_runtime:
            return False, "Recovery regression cannot pass while source/runtime recovery surfaces differ."
    passed = {
        row.get("id")
        for row in cases
        if isinstance(row, dict) and row.get("pass") is True
    }
    missing = sorted(RECOVERY_REGRESSION_CASES - passed)
    if missing:
        return False, f"Recovery regression report is missing passing cases {missing}: {path}"
    return True, str(path)


def recovery_report_self_test() -> dict[str, object]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "source"
        runtime = root / "runtime"
        for skill_root in (source, runtime):
            (skill_root / "references").mkdir(parents=True)
            (skill_root / "SKILL.md").write_text("---\nname: q-workflow\n---\n", encoding="utf-8")
            (skill_root / "references" / "recovery-routing.md").write_text("recovery contract", encoding="utf-8")
        test_paths = {"starter_q_workflow": source, "runtime_q_workflow": runtime}
        modern = root / "modern.json"
        modern.write_text(json.dumps({
            "format_version": 1,
            "status": "pass",
            "trace_id": "RECOVERY-REGRESSION-SELFTEST",
            "generated_at": "2026-08-03T02:00:00+08:00",
            "generator": "release-readiness-self-test",
            "command": "python workflow_recovery_regression.py",
            "source_hashes": recovery_surface_hashes(source),
            "runtime_hashes": recovery_surface_hashes(runtime),
            "cases": [{"id": case_id, "pass": True} for case_id in sorted(RECOVERY_REGRESSION_CASES)],
        }), encoding="utf-8")
        if not validate_recovery_regression_report(modern, test_paths)[0]:
            failures.append("valid modern recovery report was rejected")
        incomplete = root / "incomplete.json"
        incomplete.write_text(modern.read_text(encoding="utf-8").replace('"pass": true', '"pass": false', 1), encoding="utf-8")
        if validate_recovery_regression_report(incomplete, test_paths)[0]:
            failures.append("incomplete recovery case set was accepted")
        stale = json.loads(modern.read_text(encoding="utf-8"))
        stale["source_hashes"]["SKILL.md"] = "0" * 64
        modern.write_text(json.dumps(stale), encoding="utf-8")
        if validate_recovery_regression_report(modern, test_paths)[0]:
            failures.append("stale recovery source hash was accepted")
        invalid = root / "invalid.json"
        invalid.write_text("not-json", encoding="utf-8")
        if validate_recovery_regression_report(invalid, test_paths)[0]:
            failures.append("invalid JSON report was accepted")
        if validate_recovery_regression_report(root / "missing.json", test_paths)[0]:
            failures.append("missing report was accepted")
    return {"status": "pass" if not failures else "blocked", "failures": failures, "cases": 5}


def recovery_resume_ux_gate(paths: dict[str, Path], report_path: Path | None) -> GateResult:
    """Gate the closed/recommended-thread resume contract and selected replay evidence."""
    required_sources = [
        paths["starter_q_workflow"] / "SKILL.md",
        paths["starter_q_workflow"] / "references" / "recovery-routing.md",
        paths["runtime_q_workflow"] / "SKILL.md",
        paths["runtime_q_workflow"] / "references" / "recovery-routing.md",
    ]
    missing_files = [str(path) for path in required_sources if not read_text(path)]
    if missing_files:
        return GateResult(
            "BLOCKED",
            "Recovery resume UX regression",
            "Missing rule file(s): " + "; ".join(missing_files),
            "Restore source/runtime q-workflow recovery files before release labeling.",
        )

    combined = "\n".join(read_text(path).lower() for path in required_sources)
    required_terms = [
        "active",
        "paused",
        "closed",
        "completed",
        "recommendation-only",
        "reopens or promotes",
        "do not turn it into an equal option",
        "must not create a numbered choice",
    ]
    missing_terms = [term for term in required_terms if term not in combined]
    if missing_terms:
        return GateResult(
            "BLOCKED",
            "Recovery resume UX regression",
            "Missing required recovery semantics: " + ", ".join(missing_terms),
            "Reapply the Q3 closed/recommended-thread recovery rule to source and runtime mirrors.",
        )

    passed, evidence = validate_recovery_regression_report(report_path, paths)
    if not passed:
        return GateResult(
            "BLOCKED",
            "Recovery resume UX regression",
            evidence,
            "Run the current recovery regression corpus and pass its JSON report explicitly with --recovery-regression-report.",
        )
    return GateResult(
        "PASS",
        "Recovery resume UX regression",
        f"Required recovery rules and explicit regression evidence pass: {evidence}",
        "Keep this gate when changing resume, RECOVERY_POINTER, or Active Execution Thread behavior.",
    )

def render_markdown(target: str, gates: list[GateResult], paths: dict[str, Path]) -> str:
    blockers = [gate for gate in gates if gate.status == "BLOCKED"]
    warnings = [gate for gate in gates if gate.status == "WARN"]
    status = "PASS" if not blockers and not warnings else "ATTENTION"
    if blockers:
        label = f"{target}-ready blocked"
    elif warnings:
        label = f"{target}-ready needs review"
    else:
        label = f"{target}-ready evidence complete"

    lines = [
        "# Workflow Release Readiness Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Target: {target}",
        f"Status: {status}",
        f"Label decision: {label}",
        "",
        "## Summary",
        "",
        f"- Gates: {len(gates)}",
        f"- Blocked: {len(blockers)}",
        f"- Warnings: {len(warnings)}",
        f"- Hub state: `{paths['hub_personal_state']}`",
        f"- Reports root: `{paths['reports']}`",
        "",
        "## Gate Results",
        "",
        "| Status | Gate | Evidence | Next Action |",
        "|---|---|---|---|",
    ]
    for gate in sorted(gates, key=lambda item: (status_rank(item.status), item.gate)):
        lines.append(f"| {gate.status} | {escape_cell(gate.gate)} | {escape_cell(gate.evidence)} | {escape_cell(gate.next_action)} |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        "- Do not promote `team-ready` or `public-ready` while any gate is BLOCKED.",
        "- `pilot-ready` remains acceptable for bounded Xiao Q use when mechanical gates pass but colleague evidence is incomplete.",
        "- Public-ready always requires a separate public sanitization and licensing review.",
    ])
    return "\n".join(lines) + "\n"


def write_report(markdown: str, reports_dir: Path, output: Path | None) -> Path:
    if output is None:
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output = reports_dir / f"workflow_release_readiness_{stamp}.md"
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8", newline="\n")
    return output


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("pilot", "team", "public"), default="team", help="Release label to evaluate.")
    parser.add_argument("--scenario-dir", type=Path, help="Directory containing top-task scenario logs.")
    parser.add_argument("--min-scenarios", type=int, default=5, help="Minimum passing scenario logs for team-ready.")
    parser.add_argument("--usability-report", type=Path, help="Usability Validator report path. Defaults to latest matching report.")
    parser.add_argument("--signoff-file", type=Path, help="Release signoff file. Defaults to personal-state/RELEASE_SIGNOFF.md.")
    parser.add_argument("--recovery-regression-report", type=Path, help="Explicit JSON replay evidence for the current recovery routing contract.")
    parser.add_argument("--output", type=Path, help="Markdown report path. Defaults to profile hub reports folder.")
    parser.add_argument("--stdout", action="store_true", help="Print the Markdown report to stdout and do not write a report file.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any gate is BLOCKED.")
    parser.add_argument("--self-test", action="store_true", help="Run recovery evidence parser regression fixtures.")
    args = parser.parse_args(argv)
    if args.stdout and args.output:
        parser.error("--stdout cannot be combined with --output")
    if args.self_test:
        payload = recovery_report_self_test()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "pass" else 1

    paths = workflow_audit.default_paths()
    reports_root = paths["reports"]
    scenario_dir = args.scenario_dir or reports_root / "release_readiness_scenarios"
    signoff_file = args.signoff_file or paths["hub_personal_state"] / "RELEASE_SIGNOFF.md"

    gates = [
        mechanical_audit_gate(),
        source_runtime_sync_gate(paths),
        standard_contract_gate(paths),
        encoding_release_gate(paths),
        experiment_validation_gate(paths),
        hook_visibility_gate(paths),
        recovery_resume_ux_gate(paths, args.recovery_regression_report),
        scenario_gate(scenario_dir, args.min_scenarios),
        usability_gate(args.usability_report, reports_root, require_explicit=args.target in {"team", "public"}),
        signoff_gate(signoff_file),
        public_sanitization_gate(args.target, signoff_file, reports_root),
    ]
    markdown = render_markdown(args.target, gates, paths)

    if args.stdout:
        sys.stdout.write(markdown)
        report_target = "stdout"
        status_stream = sys.stderr
    else:
        report_target = str(write_report(markdown, reports_root, args.output))
        status_stream = sys.stdout

    blocked = [gate for gate in gates if gate.status == "BLOCKED"]
    print(f"Workflow release readiness report: {report_target}", file=status_stream)
    print(f"Target: {args.target}; blocked gates: {len(blocked)}", file=status_stream)
    for gate in blocked:
        print(f"BLOCKED {gate.gate}: {gate.evidence}", file=status_stream)
    return 1 if args.strict and blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
