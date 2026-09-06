from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def resolve_python() -> Path:
    configured = os.environ.get("Q_WORKFLOW_PYTHON")
    if configured:
        return Path(configured).expanduser()
    return Path(sys.executable)


PYTHON = resolve_python()


@dataclass
class Step:
    step_id: str
    title: str
    command: list[str] | None
    tier: str
    required: bool = True
    manual: str = ""


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def env_path(name: str, default: Path | None = None) -> Path | None:
    value = os.environ.get(name)
    if value:
        return Path(value).expanduser()
    return default


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def sibling_repo(current: Path, name: str) -> Path | None:
    for parent in [current.parent, *current.parents]:
        candidate = parent / name
        if candidate.exists():
            return candidate
    return None


def paths() -> dict[str, Path | None]:
    home = Path.home()
    current = repo_root()
    codex_home = env_path("CODEX_HOME") or env_path("Q_CODEX_HOME") or home / ".codex"
    skills_root = codex_home / "skills"
    return {
        "current": current,
        "runtime": skills_root,
        "q_workflow_public_runtime": env_path("Q_WORKFLOW_PUBLIC_ROOT")
        or (current if current.name == "q-workflow" else skills_root / "q-workflow"),
        "q_workflow_runtime": env_path("Q_WORKFLOW_ROOT")
        or (current if current.name == "q-workflow" else skills_root / "q-workflow"),
        "q_skill_creation_runtime": env_path("Q_SKILL_CREATION_ROOT")
        or skills_root / "q-skill-creation",
        "text_runtime": env_path("Q_TEXT_FORMAT_HYGIENE_ROOT")
        or skills_root / "text-format-hygiene",
        "workflow_hub": env_path("Q_WORKFLOW_HUB") or sibling_repo(current, "q-workflow-hub"),
        "public_hub": env_path("Q_WORKFLOW_PUBLIC_HUB") or sibling_repo(current, "q-workflow-hub-public") or home / "q-workflow-hub-public",
        "personal_hub": env_path("Q_PERSONAL_HUB"),
    }


def script(root: Path | None, relative: str) -> Path | None:
    if root is None:
        return None
    return root / "scripts" / relative


def command_for(root: Path | None, relative: str, *args: str) -> list[str] | None:
    target = script(root, relative)
    if target is None:
        return None
    return [str(PYTHON), str(target), *args]


def same_path(left: Path | None, right: Path | None) -> bool:
    if left is None or right is None:
        return left is right
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return str(left).casefold() == str(right).casefold()


def release_command(root: Path | None, target: str, evidence: dict[str, Path] | None) -> list[str] | None:
    args = ["--target", target, "--stdout", "--strict"]
    option_names = {
        "scenario_dir": "--scenario-dir",
        "usability_report": "--usability-report",
        "signoff_file": "--signoff-file",
        "recovery_regression_report": "--recovery-regression-report",
    }
    for key, option in option_names.items():
        value = (evidence or {}).get(key)
        if value is not None:
            args.extend([option, str(value)])
    return command_for(root, "release_readiness.py", *args)


def step_catalog(level: str, scenario: str, release_evidence: dict[str, Path] | None = None) -> list[Step]:
    p = paths()
    q_workflow_public = p["q_workflow_public_runtime"]
    q_workflow = p["q_workflow_runtime"]
    steps: list[Step] = [
        Step("S01", "Workflow structural audit", command_for(q_workflow, "workflow_audit.py", "--mode", "audit", "--strict"), "core"),
        Step("S02", "Skill portfolio observation", command_for(p["q_skill_creation_runtime"], "skill_portfolio_audit.py"), "core", False),
        Step("S03", "Current q-standard self-test", command_for(q_workflow, "q_standard_check.py", "--root", str(q_workflow), "--self-test"), "core"),
    ]
    if not same_path(q_workflow_public, q_workflow):
        steps.append(Step("S04", "Distinct public q-standard self-test", command_for(q_workflow_public, "q_standard_check.py", "--root", str(q_workflow_public), "--self-test"), "core"))
    steps.extend([
        Step("S05", "Strict lifecycle envelope", command_for(q_workflow, "workflow_lifecycle.py", "--strict", "--format", "json"), "core"),
        Step("S06", "Lifecycle receipt self-test", command_for(q_workflow, "workflow_lifecycle.py", "--self-test", "--format", "json"), "core"),
        Step("S07", "Phase B output preflight self-test", command_for(q_workflow, "phase_b_output_preflight.py", "--self-test"), "core"),
        Step("S08", "Release evidence parser self-test", command_for(q_workflow, "release_readiness.py", "--self-test"), "core"),
        Step("S09", "Workflow release readiness observation", release_command(q_workflow, "pilot", release_evidence), "core", False),
    ])
    if level in {"full", "release"}:
        steps.extend([
            Step("F02", "Runtime encoding guard", command_for(q_workflow, "encoding_guard.py", str(p["runtime"])), "full"),
            Step("F04", "Workflow foundational contract suite", command_for(q_workflow, "workflow_stability_suite.py", "--rounds", "2", "--check-only", "--strict", "--stdout"), "full"),
            Step("F05", "Workflow cold-start and expert-routing scenarios", command_for(q_workflow, "workflow_stability_scenarios.py"), "full"),
        ])
    if level == "release":
        steps.append(Step("R00", "Strict public workflow release readiness", release_command(q_workflow, "public", release_evidence), "release"))
        steps.append(Step("R01", "Legacy extended evidence observation", command_for(q_workflow, "workflow_extended_suite.py", "--rounds", "2", "--check-only", "--strict", "--stdout"), "release", False))
    manual_required = level == "release"
    if scenario in {"personal-pull", "github-personal"}:
        steps.append(Step("M01", "User personal endpoint pull/recovery observation", None, "manual", manual_required, "On the personal endpoint: pull GitHub, restart/recover Xiao Q, run exact `小Q`, `TODO`, and workflow test trigger; record whether state, encoding, and repo locator behave correctly."))
    if scenario in {"remote-promotion", "promotion-install"}:
        steps.append(Step("M02", "Promotion/internal Git remote install observation", None, "manual", manual_required, "On the promotion endpoint: install/load from internal Git remote, run exact `小Q`, `workflow-test core`, and a repo locator check; record missing paths, stale runtime, or encoding issues."))
    return steps


def command_missing(command: list[str] | None) -> str:
    if command is None:
        return "No command configured for this step"
    if len(command) >= 2 and command[1].endswith((".py", ".ps1")) and not Path(command[1]).exists():
        return f"Missing script: {command[1]}"
    if command and not Path(command[0]).exists():
        return f"Missing Python executable: {command[0]}"
    return ""


def load_feedback_statuses(path: Path | None, scenario: str, allowed_step_ids: set[str]) -> tuple[dict[str, str], list[str]]:
    if path is None:
        return {}, []
    if not path.is_file():
        return {}, [f"feedback receipt is missing: {path}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except json.JSONDecodeError as exc:
        return {}, [f"feedback receipt is not valid JSON: {exc}"]
    errors: list[str] = []
    if payload.get("format_version") != 1:
        errors.append("feedback format_version must equal 1")
    trace_id = payload.get("trace_id")
    if not isinstance(trace_id, str) or len(trace_id.strip()) < 8:
        errors.append("feedback trace_id must be a non-empty durable identifier")
    if payload.get("scenario") != scenario:
        errors.append(f"feedback scenario must equal {scenario}")
    endpoint = payload.get("endpoint")
    if not isinstance(endpoint, str) or not endpoint.strip():
        errors.append("feedback endpoint is required")
    executed_at = payload.get("executed_at")
    try:
        parsed = datetime.fromisoformat(str(executed_at).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            errors.append("feedback executed_at must include a timezone")
    except ValueError:
        errors.append("feedback executed_at must be an ISO-8601 timestamp")
    steps = payload.get("steps")
    if not isinstance(steps, list):
        return {}, errors + ["feedback steps must be a list"]
    statuses: dict[str, str] = {}
    for index, row in enumerate(steps):
        if not isinstance(row, dict):
            errors.append(f"feedback step {index} must be an object")
            continue
        step_id = row.get("id")
        if step_id not in allowed_step_ids:
            errors.append(f"feedback contains unknown step id: {step_id!r}")
            continue
        if step_id in statuses:
            errors.append(f"feedback contains duplicate step id: {step_id}")
            continue
        status = row.get("user_status")
        if status not in {"pass", "partial", "fail", "not-tested"}:
            errors.append(f"feedback {step_id} has invalid user_status")
            continue
        evidence = row.get("evidence")
        note = row.get("note")
        if status == "pass":
            if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
                errors.append(f"feedback {step_id} pass requires non-empty evidence paths or command receipts")
            if not isinstance(note, str) or not note.strip():
                errors.append(f"feedback {step_id} pass requires a note")
        statuses[step_id] = status
    return ({} if errors else statuses), errors


def run_step(step: Step, timeout: int, feedback_statuses: dict[str, str] | None = None) -> dict:
    if step.command is None:
        user_status = (feedback_statuses or {}).get(step.step_id)
        if user_status == "pass":
            return {
                "step_id": step.step_id,
                "title": step.title,
                "status": "pass",
                "score": 100.0,
                "summary": "Endpoint feedback explicitly recorded as pass.",
                "command": "",
                "required": step.required,
            }
        failed_status = user_status in {"partial", "fail", "not-tested"}
        return {
            "step_id": step.step_id,
            "title": step.title,
            "status": ("fail" if failed_status else "missing") if step.required else "manual",
            "score": 0.0 if step.required else 75.0,
            "summary": (f"Endpoint feedback recorded as {user_status}. " if user_status else "") + (step.manual or "No command configured for this step"),
            "command": "",
            "required": step.required,
        }
    missing = command_missing(step.command)
    if missing:
        return {
            "step_id": step.step_id,
            "title": step.title,
            "status": "missing" if step.required else "advisory",
            "score": 0.0 if step.required else 75.0,
            "summary": missing,
            "command": " ".join(step.command),
            "required": step.required,
        }
    try:
        proc = subprocess.run(step.command, text=True, encoding="utf-8", errors="replace", capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"step_id": step.step_id, "title": step.title, "status": "timeout" if step.required else "advisory", "score": 0.0 if step.required else 75.0, "summary": f"Timed out after {timeout}s", "command": " ".join(step.command), "required": step.required}
    output = (proc.stdout + "\n" + proc.stderr).strip()
    summary = " | ".join(line.strip() for line in output.splitlines()[-4:] if line.strip())
    status = "pass" if proc.returncode == 0 else ("fail" if step.required else "advisory")
    return {
        "step_id": step.step_id,
        "title": step.title,
        "status": status,
        "score": 100.0 if proc.returncode == 0 else (0.0 if step.required else 75.0),
        "summary": summary[:900],
        "command": " ".join(step.command),
        "required": step.required,
    }


def feedback_template(results: list[dict], scenario: str) -> str:
    manual_steps = [result for result in results if not result.get("command")]
    payload = {
        "format_version": 1,
        "trace_id": "",
        "scenario": scenario,
        "endpoint": "",
        "executed_at": "",
        "steps": [
            {
                "id": result["step_id"],
                "user_status": "not-tested",
                "evidence": [],
                "note": "",
            }
            for result in manual_steps
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_report(level: str, scenario: str, results: list[dict], feedback_path: Path | None) -> str:
    auto_scores = [r["score"] for r in results]
    overall = sum(auto_scores) / len(auto_scores) if auto_scores else 0.0
    blockers = [r for r in results if r["required"] and r["status"] in {"missing", "fail", "timeout"}]
    advisories = [r for r in results if not r["required"] and r["status"] == "advisory"]
    lines = [
        "# Workflow Test Flow Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Level: {level}",
        f"Scenario: {scenario}",
        f"Automatic workflow score (includes advisory/manual placeholders): {overall:.1f}",
        f"Blocking automatic failures: {len(blockers)}",
        f"Advisories (not release claims): {len(advisories)}",
        "",
        "## Step Results",
        "",
        "| Step | Required | Status | Score | Summary |",
        "|---|---:|---|---:|---|",
    ]
    for result in results:
        summary = result["summary"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {result['step_id']} {result['title']} | {result['required']} | {result['status']} | {result['score']:.1f} | {summary} |")
    lines.extend([
        "",
        "## User Feedback",
        "",
        "This report is not complete until Xiao Q records endpoint feedback for any manual steps.",
        "A manual score of 75 is a pending placeholder, not a pass or remote evidence.",
    ])
    if feedback_path:
        lines.append(f"Feedback template: `{feedback_path}`")
    lines.extend([
        "",
        "## Boundary",
        "",
        "- This flow does not push, publish, delete, change credentials, or change release signoff.",
        "- A local core/full PASS does not imply release readiness; review every advisory and use the release level for a strict readiness verdict.",
        "- Remote rebuild claims still require endpoint-specific evidence from GitHub or internal Git remote.",
        "- Use environment variables such as `CODEX_HOME`, `Q_WORKFLOW_PUBLIC_ROOT`, `Q_WORKFLOW_ROOT`, and `Q_SKILL_CREATION_ROOT` when testing a nonstandard install layout.",
    ])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    temp_root = Path(tempfile.gettempdir())
    parser = argparse.ArgumentParser(description="Run Xiao Q workflow test flow with scored levels and feedback handoff.")
    parser.add_argument("--level", choices=["smoke", "core", "full", "release"], default="core")
    parser.add_argument("--scenario", choices=["local", "personal-pull", "github-personal", "remote-promotion", "promotion-install"], default="local")
    parser.add_argument("--output", type=Path, default=temp_root / "qwf_workflow_test_flow_report.md")
    parser.add_argument("--feedback-template", type=Path, default=temp_root / "qwf_workflow_test_feedback.json")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--feedback-input", type=Path, help="Completed JSON endpoint receipt to satisfy required release endpoint steps on a replay run.")
    parser.add_argument("--release-scenario-dir", type=Path, help="Directory with the required explicit-pass top-task scenario logs for release readiness.")
    parser.add_argument("--usability-report", type=Path, help="Trace-bound Usability Validator report with an explicit standalone pass verdict.")
    parser.add_argument("--signoff-file", type=Path, help="Release signoff file containing affirmative approval for the exact release scope.")
    parser.add_argument("--recovery-regression-report", type=Path, help="JSON replay evidence for the active/paused/closed/recommendation recovery contract.")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def self_test() -> dict:
    failures: list[str] = []
    core = step_catalog("core", "local")
    core_ids = {step.step_id for step in core}
    if not {"S05", "S06", "S07", "S08"}.issubset(core_ids):
        failures.append("core is missing lifecycle, Phase B, or release-evidence hard gates")
    q_standard_steps = [step for step in core if "q-standard" in step.title]
    if same_path(paths()["q_workflow_public_runtime"], paths()["q_workflow_runtime"]) and len(q_standard_steps) != 1:
        failures.append("identical q-standard roots were not deduplicated")
    release_remote = step_catalog("release", "remote-promotion")
    if not next(step for step in release_remote if step.step_id == "M02").required:
        failures.append("release endpoint feedback is not blocking")
    if next(step for step in release_remote if step.step_id == "R01").required:
        failures.append("legacy extended suite still blocks the modern release path")
    release_readiness = next(step for step in release_remote if step.step_id == "R00")
    if "public" not in release_readiness.command or "--target" not in release_readiness.command:
        failures.append("release flow does not enforce public sanitization readiness")
    full_remote = step_catalog("full", "remote-promotion")
    if next(step for step in full_remote if step.step_id == "M02").required:
        failures.append("full endpoint observation should remain advisory")
    with tempfile.TemporaryDirectory() as temp:
        feedback = Path(temp) / "feedback.json"
        valid_receipt = {
            "format_version": 1,
            "trace_id": "WORKFLOW-TEST-RECEIPT-1",
            "scenario": "remote-promotion",
            "endpoint": "promotion-host-1",
            "executed_at": "2026-08-03T02:00:00+08:00",
            "steps": [{"id": "M02", "user_status": "pass", "evidence": ["logs/workflow-core.json"], "note": "cold install and exact commands passed"}],
        }
        feedback.write_text(json.dumps(valid_receipt), encoding="utf-8")
        statuses, errors = load_feedback_statuses(feedback, "remote-promotion", {"M02"})
        if errors:
            failures.append(f"valid endpoint feedback was rejected: {errors}")
        result = run_step(next(step for step in release_remote if step.step_id == "M02"), 1, statuses)
        if result["status"] != "pass":
            failures.append("explicit endpoint pass feedback was not accepted")
        minimal = Path(temp) / "minimal.json"
        minimal.write_text(json.dumps({"format_version": 1, "scenario": "remote-promotion", "steps": [{"id": "M02", "user_status": "pass"}]}), encoding="utf-8")
        if not load_feedback_statuses(minimal, "remote-promotion", {"M02"})[1]:
            failures.append("minimal unbound pass receipt was accepted")
        duplicate = dict(valid_receipt, steps=valid_receipt["steps"] * 2)
        feedback.write_text(json.dumps(duplicate), encoding="utf-8")
        if not load_feedback_statuses(feedback, "remote-promotion", {"M02"})[1]:
            failures.append("duplicate endpoint step was accepted")
        feedback.write_text(json.dumps(dict(valid_receipt, scenario="personal-pull")), encoding="utf-8")
        if not load_feedback_statuses(feedback, "remote-promotion", {"M02"})[1]:
            failures.append("wrong-scenario endpoint receipt was accepted")
    return {"status": "pass" if not failures else "blocked", "failures": failures, "cases": 8}


def main() -> int:
    configure_output()
    args = parse_args()
    if args.self_test:
        payload = self_test()
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] == "pass" else 1
    if args.level == "release" and args.scenario == "local":
        raise SystemExit("release level requires an endpoint scenario; choose personal-pull, github-personal, remote-promotion, or promotion-install")
    release_evidence = {
        key: value
        for key, value in {
            "scenario_dir": args.release_scenario_dir,
            "usability_report": args.usability_report,
            "signoff_file": args.signoff_file,
            "recovery_regression_report": args.recovery_regression_report,
        }.items()
        if value is not None
    }
    effective_level = "core" if args.level == "smoke" else args.level
    steps = step_catalog(effective_level, args.scenario, release_evidence)
    if args.level == "smoke":
        steps = steps[:2]
    manual_ids = {step.step_id for step in steps if step.command is None}
    feedback_statuses, feedback_errors = load_feedback_statuses(args.feedback_input, args.scenario, manual_ids)
    results = [run_step(step, args.timeout, feedback_statuses) for step in steps]
    if feedback_errors:
        results.append({
            "step_id": "M00",
            "title": "Endpoint feedback receipt validation",
            "status": "fail" if args.level == "release" else "advisory",
            "score": 0.0 if args.level == "release" else 75.0,
            "summary": "; ".join(feedback_errors),
            "command": "",
            "required": args.level == "release",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.feedback_template.parent.mkdir(parents=True, exist_ok=True)
    args.feedback_template.write_text(feedback_template(results, args.scenario), encoding="utf-8", newline="\n")
    args.output.write_text(render_report(args.level, args.scenario, results, args.feedback_template), encoding="utf-8", newline="\n")
    payload = {"level": args.level, "scenario": args.scenario, "results": results, "report": str(args.output), "feedback_template": str(args.feedback_template), "feedback_input": str(args.feedback_input) if args.feedback_input else None}
    if args.json_out:
        args.json_out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    failures = [r for r in results if r["required"] and r["status"] in {"missing", "fail", "timeout"}]
    score = sum(r["score"] for r in results) / len(results) if results else 0.0
    print(f"workflow-test-flow: {'PASS' if not failures else 'FAIL'} score={score:.1f} failures={len(failures)}")
    print(f"report={args.output}")
    print(f"feedback_template={args.feedback_template}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
