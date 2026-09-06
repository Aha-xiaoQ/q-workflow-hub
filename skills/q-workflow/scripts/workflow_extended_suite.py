#!/usr/bin/env python3
r"""Run the legacy extended q-workflow stability/release evidence suite.

Local-only runner. It checks per-file assertions, sync parity, hash stability,
release-gate replay, and recorded scenario evidence. It does not edit workflow
source unless the caller asks it to write reports; it never commits, pushes,
publishes, changes signoff, or accesses credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from statistics import mean


@dataclass(frozen=True)
class CheckResult:
    scenario: str
    dimension: str
    severity: str
    score: float
    evidence: str
    recommendation: str


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    dimension: str
    name: str
    required_by_file: dict[str, tuple[str, ...]] = field(default_factory=dict)
    required_regex_by_file: dict[str, tuple[str, ...]] = field(default_factory=dict)
    forbidden_regex_by_file: dict[str, tuple[str, ...]] = field(default_factory=dict)
    max_lines_by_file: dict[str, int] = field(default_factory=dict)
    pass_marker_files: tuple[str, ...] = ()
    equal_hash_groups: tuple[tuple[str, ...], ...] = ()


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


def line_count(path: Path) -> int:
    text = read_text(path)
    return len(text.splitlines()) if text else 0


def user_home() -> Path:
    return Path(os.environ.get("USERPROFILE", str(Path.home())))


def load_profile(home: Path) -> dict[str, str]:
    profile_path = Path(os.environ.get("Q_PROFILE_PATH", str(home / ".codex" / "q-profile.json")))
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {str(k): v for k, v in payload.items() if isinstance(v, str) and v}


def configured_path(env_name: str, profile: dict[str, str], profile_key: str, fallback: Path) -> Path:
    value = os.environ.get(env_name) or profile.get(profile_key)
    return Path(value) if value else fallback


def first_existing_path(*paths: Path) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def default_paths() -> dict[str, Path]:
    home = user_home()
    profile = load_profile(home)
    projects = configured_path("Q_WORKFLOW_PROJECTS_ROOT", profile, "projects", home / "Q_projects")
    hub = configured_path("Q_PERSONAL_HUB", profile, "hub", home / "q-personal-hub")
    runtime = home / ".codex" / "skills" / "q-workflow"
    starter = Path(os.environ.get("Q_WORKFLOW_HUB_SOURCE", str(projects / "q-workflow-hub" / "skills" / "q-workflow")))
    standalone = Path(os.environ.get("Q_WORKFLOW_SOURCE", str(projects / "q-workflow")))
    reports = Path(os.environ.get("Q_WORKFLOW_REPORTS", str(hub / "reports")))
    return {
        "home": home,
        "runtime": runtime,
        "starter": starter,
        "standalone": standalone,
        "assistant": home / ".codex" / "skills" / "q-assistant-profile",
        "agent_roster": home / ".codex" / "skills" / "q-agent-roster",
        "text_hygiene": home / ".codex" / "skills" / "text-format-hygiene",
        "hub_state": hub / "personal-state",
        "runtime_state": home / ".codex" / "q-personal-state",
        "reports": reports,
        "team_packet": reports / "release_readiness_scenarios" / "team_ready_packet_20260627",
    }


def resolve(paths: dict[str, Path], spec: str) -> Path:
    root, _, rel = spec.partition("/")
    base = paths[root]
    return base / rel if rel else base


def scenario_catalog() -> list[Scenario]:
    return [
        Scenario(
            "S01", "stability", "RECOVERY_POINTER first-read authority",
            required_by_file={
                "hub_state/ACTIVE_WORK.md": ("RECOVERY_POINTER v0.1", "authority_event", "sync_state", "stale_audit_trigger"),
                "hub_state/RECOVERY_EVENTS.md": ("recovery-20260627-001", "sync_result", "synced", "V1.1 firmware pin-map/resource-map update"),
                "runtime/SKILL.md": ("RECOVERY_POINTER v0.1",),
                "assistant/SKILL.md": ("RECOVERY_POINTER v0.1",),
                "team_packet/team-scenario-01-quick-resume-pointer-stability.md": ("Status: pass", "active/synced", "V1.1 firmware pin-map/resource-map update"),
            },
        ),
        Scenario(
            "S02", "stability", "stale-pointer mismatch audit",
            required_by_file={
                "hub_state/RECOVERY_EVENTS.md": ("sync_result", "mismatch"),
                "runtime/references/recovery-routing.md": ("stale-pointer audit", "RECOVERY_EVENTS.md", "mismatch"),
            },
        ),
        Scenario(
            "S03", "stability", "numbered choice high-risk gate",
            required_by_file={
                "runtime/references/command-fast-paths.md": ("Numbered Choice Confirmation", "exact action", "target object", "scope", "likely impact", "not authorization"),
                "starter/references/command-fast-paths.md": ("Numbered Choice Confirmation", "exact action", "target object", "scope", "likely impact", "not authorization"),
                "standalone/references/command-fast-paths.md": ("Numbered Choice Confirmation", "exact action", "target object", "scope", "likely impact", "not authorization"),
            },
            forbidden_regex_by_file={
                "runtime/references/command-fast-paths.md": (r"bare\s+`?1\.?\s*执行[^\n]{0,80}\bis\s+authorization\b",),
                "starter/references/command-fast-paths.md": (r"bare\s+`?1\.?\s*执行[^\n]{0,80}\bis\s+authorization\b",),
                "standalone/references/command-fast-paths.md": (r"bare\s+`?1\.?\s*执行[^\n]{0,80}\bis\s+authorization\b",),
            },
            equal_hash_groups=(("runtime/references/command-fast-paths.md", "starter/references/command-fast-paths.md", "standalone/references/command-fast-paths.md"),),
        ),
        Scenario(
            "S04", "stability", "interruption LIFO stack",
            required_by_file={
                "runtime/references/command-fast-paths.md": ("LIFO stack", "lightweight interruption node", "durable interruption stack"),
                "runtime/references/recovery-routing.md": ("LIFO stack", "lightweight interruption node", "durable interruption stack", "ACTIVE_WORK.md", "PAUSED_WORK.md"),
                "team_packet/team-scenario-03-interruption-stack-return.md": ("Status: pass", "isolated-subagent-live-multiturn", "LIFO order"),
            },
        ),
        Scenario(
            "E01", "efficiency", "router size budget",
            required_by_file={
                "runtime/SKILL.md": ("First-Read Router",),
                "starter/SKILL.md": ("First-Read Router",),
                "standalone/SKILL.md": ("First-Read Router",),
                "assistant/SKILL.md": ("RECOVERY_POINTER v0.1",),
            },
            max_lines_by_file={"runtime/SKILL.md": 180, "starter/SKILL.md": 180, "standalone/SKILL.md": 180, "assistant/SKILL.md": 140},
        ),
        Scenario(
            "E02", "efficiency", "TODO micro path avoids broad scans",
            required_by_file={
                "runtime/SKILL.md": ("TODO", "Micro"),
                "assistant/SKILL.md": ("Exact TODO / todo", "personal-state\\TODO.md", "not a menu", "If the TODO file cannot be read", "two-line item shape"),
                "runtime/references/command-fast-paths.md": ("`TODO` is a micro", "q-profile.json", "personal-state\\TODO.md", "Do not scan project repos"),
                "team_packet/team-scenario-04-todo-micro-path.md": ("Status: pass", "no project scan", "no writes were performed"),
            },
        ),
        Scenario(
            "E03", "efficiency", "TOKEN and context budget routes stay bounded",
            required_by_file={
                "runtime/SKILL.md": ("token_usage.py", "context_governor.py"),
                "runtime/references/command-fast-paths.md": ("token_usage.py", "Cache Stability Protocol"),
            },
        ),
        Scenario(
            "R01", "reproducibility", "critical refs synchronized across copies",
            required_by_file={
                "runtime/references/release-readiness.md": ("Signoff approval is also strict",),
                "starter/references/release-readiness.md": ("Signoff approval is also strict",),
                "standalone/references/release-readiness.md": ("Signoff approval is also strict",),
            },
            equal_hash_groups=(
                ("runtime/references/command-fast-paths.md", "starter/references/command-fast-paths.md", "standalone/references/command-fast-paths.md"),
                ("runtime/references/release-readiness.md", "starter/references/release-readiness.md", "standalone/references/release-readiness.md"),
                ("runtime/scripts/release_readiness.py", "starter/scripts/release_readiness.py", "standalone/scripts/release_readiness.py"),
            ),
        ),
        Scenario(
            "R02", "reproducibility", "release readiness report evidence",
            required_by_file={
                "runtime/scripts/release_readiness.py": ("approved = re.search", "find_latest_explicit_pass"),
                "starter/scripts/release_readiness.py": ("approved = re.search", "find_latest_explicit_pass"),
                "standalone/scripts/release_readiness.py": ("approved = re.search", "find_latest_explicit_pass"),
                "reports/workflow_release_readiness_20260627_team_evidence_packet.md": ("Label decision: team-ready blocked", "Blocked: 1", "Usability Validator", "Top-task scenario logs"),
            },
        ),
        Scenario(
            "R03", "reproducibility", "team-ready isolated scenario packet",
            required_by_file={
                "team_packet/team-scenario-01-quick-resume-pointer-stability.md": ("Status: pass", "Evidence type: isolated-subagent-cold-start", "Result: pass"),
                "team_packet/team-scenario-02-numbered-choice-confirmation.md": ("Status: pass", "Evidence type: isolated-subagent-cold-start", "Result: pass"),
                "team_packet/team-scenario-03-interruption-stack-return.md": ("Status: pass", "Evidence type: isolated-subagent-live-multiturn", "Result: pass"),
                "team_packet/team-scenario-04-todo-micro-path.md": ("Status: pass", "Evidence type: isolated-subagent-cold-start", "Result: pass"),
                "team_packet/team-scenario-05-release-readiness-gate.md": ("Status: pass", "Evidence type: isolated-subagent-cold-start", "Result: pass"),
                "team_packet/usability-validator-team-ready-20260627.md": ("Status: pass", "Score: 88/100", "usability-pass-with-recorded-limitations"),
            },
            pass_marker_files=(
                "team_packet/team-scenario-01-quick-resume-pointer-stability.md",
                "team_packet/team-scenario-02-numbered-choice-confirmation.md",
                "team_packet/team-scenario-03-interruption-stack-return.md",
                "team_packet/team-scenario-04-todo-micro-path.md",
                "team_packet/team-scenario-05-release-readiness-gate.md",
                "team_packet/usability-validator-team-ready-20260627.md",
            ),
        ),
        Scenario(
            "M01", "modularity", "skill ownership boundaries",
            required_by_file={
                "runtime/SKILL.md": ("text-format-hygiene", "Use sub-agents through bounded orchestration contracts"),
                "agent_roster/SKILL.md": ("Usability Validator", "Code Auditor"),
                "text_hygiene/SKILL.md": ("Text format hygiene",),
            },
        ),
        Scenario(
            "M02", "modularity", "release readiness separate from public sync",
            required_by_file={
                "runtime/references/release-readiness.md": ("public-ready", "sanitization", "public-sync approval"),
                "runtime/references/cross-profile-policy.md": ("public-safe", "Do not import `ACTIVE_WORK`", "GitHub"),
                "hub_state/SKILL_SYNC.md": ("public-ready requires separate sanitization", "Do not import personal active work"),
            },
        ),
    ]


def text_has(text: str, term: str) -> bool:
    return term.lower() in text.lower()


def regex_has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) is not None


def check_scenario(paths: dict[str, Path], scenario: Scenario, round_index: int) -> CheckResult:
    evidence_bits: list[str] = []
    score_cap = 100.0

    for spec, terms in scenario.required_by_file.items():
        path = resolve(paths, spec)
        text = read_text(path)
        if not text:
            return CheckResult(scenario.scenario_id, scenario.dimension, "P1", 0.0, f"round {round_index}: missing or empty file {spec}", "Restore required file before relying on this workflow.")
        missing = [term for term in terms if not text_has(text, term)]
        if missing:
            return CheckResult(scenario.scenario_id, scenario.dimension, "P2", 72.0, f"round {round_index}: {spec} missing terms: {', '.join(missing)}", "Patch the owning file or scenario evidence, then rerun the suite.")
        evidence_bits.append(f"{spec}: terms ok")

    for spec, patterns in scenario.required_regex_by_file.items():
        text = read_text(resolve(paths, spec))
        missing = [pattern for pattern in patterns if not regex_has(text, pattern)]
        if missing:
            return CheckResult(scenario.scenario_id, scenario.dimension, "P2", 72.0, f"round {round_index}: {spec} missing regex: {', '.join(missing)}", "Patch the behavior wording or test evidence.")

    for spec, patterns in scenario.forbidden_regex_by_file.items():
        text = read_text(resolve(paths, spec))
        hits = [pattern for pattern in patterns if regex_has(text, pattern)]
        if hits:
            return CheckResult(scenario.scenario_id, scenario.dimension, "P1", 40.0, f"round {round_index}: {spec} matched forbidden regex: {', '.join(hits)}", "Remove unsafe wording or narrow it so risky actions cannot be authorized by vague choices.")

    for spec, limit in scenario.max_lines_by_file.items():
        lines = line_count(resolve(paths, spec))
        if lines > limit:
            return CheckResult(scenario.scenario_id, scenario.dimension, "P2", 82.0, f"round {round_index}: {spec} has {lines} lines > {limit}", "Move rare detail into references and keep routers concise.")

    for group in scenario.equal_hash_groups:
        hashes = {spec: file_hash(resolve(paths, spec)) for spec in group}
        if len(set(hashes.values())) != 1:
            joined = ", ".join(f"{spec}={digest}" for spec, digest in hashes.items())
            return CheckResult(scenario.scenario_id, scenario.dimension, "P2", 80.0, f"round {round_index}: hash mismatch: {joined}", "Sync intentional peer copies or record a compatibility exception.")
        evidence_bits.append("hash group ok: " + ", ".join(group))

    for spec in scenario.pass_marker_files:
        text = read_text(resolve(paths, spec))
        if not re.search(r"(?im)^\s*(status|verdict|result)\s*:\s*pass\s*$", text):
            return CheckResult(scenario.scenario_id, scenario.dimension, "P2", 84.0, f"round {round_index}: {spec} lacks standalone pass marker", "Complete isolated scenario evidence before marking the suite complete.")

    if scenario.scenario_id == "R03":
        aggregate = read_text(resolve(paths, "team_packet/usability-validator-team-ready-20260627.md"))
        match = re.search(r"(?im)^\s*Score\s*:\s*(\d+)\s*/\s*100\s*$", aggregate)
        if not match:
            return CheckResult("R03", "reproducibility", "P2", 84.0, f"round {round_index}: aggregate usability score missing", "Record aggregate score and limitations.")
        usability_score = int(match.group(1))
        if usability_score < 80:
            return CheckResult("R03", "reproducibility", "P2", float(usability_score), f"round {round_index}: aggregate usability score {usability_score}/100", "Improve scenario evidence before treating it as stable.")
        if usability_score < 90:
            score_cap = min(score_cap, 96.0)
            evidence_bits.append(f"aggregate usability limitation carried: {usability_score}/100")

    evidence = f"round {round_index}: " + "; ".join(evidence_bits[:4])
    if len(evidence_bits) > 4:
        evidence += f"; +{len(evidence_bits) - 4} more checks"
    return CheckResult(scenario.scenario_id, scenario.dimension, "OK", score_cap, evidence, "Keep as regression coverage.")


def run_release_gate(paths: dict[str, Path], round_index: int) -> CheckResult:
    script = paths["runtime"] / "scripts" / "release_readiness.py"
    command = [
        sys.executable,
        str(script),
        "--target", "team",
        "--scenario-dir", str(paths["reports"] / "release_readiness_scenarios"),
        "--signoff-file", str(paths["hub_state"] / "RELEASE_SIGNOFF.md"),
        "--stdout",
    ]
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    try:
        completed = subprocess.run(command, cwd=str(paths["runtime"]), env=env, text=True, capture_output=True, timeout=20, check=False)
    except Exception as exc:  # noqa: BLE001 - report any runner failure as evidence
        return CheckResult("R05", "reproducibility", "P1", 0.0, f"round {round_index}: release gate replay failed: {exc}", "Fix the release gate replay before claiming reproducibility.")
    output = completed.stdout + "\n" + completed.stderr
    required = (
        "Label decision: team-ready blocked",
        "Blocked: 1",
        "PASS | Mechanical audit",
        "PASS | Standard contract",
        "PASS | Encoding guard",
        "PASS | Experiment validation",
        "PASS | Hook visibility",
        "PASS | Recovery resume UX regression",
        "PASS | Top-task scenario logs",
        "PASS | Usability Validator",
        "N/A | Public sanitization",
        "BLOCKED | Release signoff",
    )
    forbidden = (
        "BLOCKED | Mechanical audit",
        "BLOCKED | Standard contract",
        "BLOCKED | Encoding guard",
        "BLOCKED | Experiment validation",
        "BLOCKED | Hook visibility",
        "BLOCKED | Recovery resume UX regression",
        "BLOCKED | Top-task scenario logs",
        "BLOCKED | Usability Validator",
        "WARN |",
    )
    missing = [term for term in required if term not in output]
    blocked_unexpected = [term for term in forbidden if term in output]
    if completed.returncode != 0 or missing or blocked_unexpected:
        return CheckResult("R05", "reproducibility", "P1", 60.0, f"round {round_index}: release gate replay unexpected rc={completed.returncode}; missing={missing}; blocked_unexpected={blocked_unexpected}", "Rerun release_readiness.py and repair evidence or runner expectations.")
    return CheckResult("R05", "reproducibility", "OK", 100.0, f"round {round_index}: release gate replay matched mechanical pass plus signoff-only block", "Keep release gate replay in the suite.")


def critical_hashes(paths: dict[str, Path]) -> dict[str, str]:
    specs = [
        "runtime/SKILL.md",
        "runtime/references/command-fast-paths.md",
        "starter/references/command-fast-paths.md",
        "standalone/references/command-fast-paths.md",
        "runtime/references/recovery-routing.md",
        "runtime/references/release-readiness.md",
        "starter/references/release-readiness.md",
        "standalone/references/release-readiness.md",
        "runtime/scripts/release_readiness.py",
        "starter/scripts/release_readiness.py",
        "standalone/scripts/release_readiness.py",
        "runtime/scripts/workflow_stability_suite.py",
        "starter/scripts/workflow_stability_suite.py",
        "standalone/scripts/workflow_stability_suite.py",
        "team_packet/usability-validator-team-ready-20260627.md",
    ]
    return {spec: file_hash(resolve(paths, spec)) for spec in specs}


def run_suite(paths: dict[str, Path], rounds: int) -> tuple[list[CheckResult], list[dict[str, str]]]:
    results: list[CheckResult] = []
    hashes: list[dict[str, str]] = []
    scenarios = scenario_catalog()
    for idx in range(1, rounds + 1):
        hashes.append(critical_hashes(paths))
        for scenario in scenarios:
            results.append(check_scenario(paths, scenario, idx))
        results.append(run_release_gate(paths, idx))
    if len(hashes) >= 2:
        baseline = hashes[0]
        for idx, current in enumerate(hashes[1:], start=2):
            drift = [spec for spec, digest in baseline.items() if current.get(spec) != digest]
            if drift:
                results.append(CheckResult("R04", "reproducibility", "P2", 80.0, f"round {idx}: critical hashes drifted: {', '.join(drift)}", "Stabilize generated outputs or record why the round intentionally changed files."))
            else:
                results.append(CheckResult("R04", "reproducibility", "OK", 100.0, f"round {idx}: critical hashes stable", "Keep hash stability check."))
    return results, hashes


def severity_rank(severity: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "OK": 4}.get(severity, 9)


def aggregate_scores(results: list[CheckResult]) -> dict[str, float]:
    dims = sorted({result.dimension for result in results})
    scores = {dim: mean([result.score for result in results if result.dimension == dim]) for dim in dims}
    scores["overall"] = mean([result.score for result in results]) if results else 0.0
    return scores


def final_label(results: list[CheckResult], scores: dict[str, float]) -> str:
    blockers = [result for result in results if result.severity in {"P0", "P1", "P2"}]
    if blockers:
        return "blocked"
    if scores.get("overall", 0.0) >= 98.0 and all(value >= 96.0 for key, value in scores.items() if key != "overall"):
        return "stable-loop-pass"
    return "watch"


def escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_report(results: list[CheckResult], hashes: list[dict[str, str]], rounds: int) -> str:
    scores = aggregate_scores(results)
    label = final_label(results, scores)
    blockers = [result for result in results if result.severity in {"P0", "P1", "P2"}]
    lines = [
        "# Workflow Stability Loop Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Rounds: {rounds}",
        f"Final status: {label}",
        "",
        "## Method Basis",
        "",
        "- Trace-style workflow evaluation: check end-to-end observable behavior and gate outputs, not only isolated text.",
        "- Multi-turn eval pattern: include interruption and recovery scenarios with explicit pass/fail criteria.",
        "- Regression assertion pattern: use deterministic per-file assertions, forbidden-rule checks, and repeatable scoring.",
        "- Agent observability pattern: separately score tool/gate replay, plan/route adherence, efficiency, and source-copy parity.",
        "- Local q-research rubric: scenario realism, observable success criteria, evidence quality, improvement loop, and durability.",
        "",
        "## Scorecard",
        "",
        "| Dimension | Score |",
        "|---|---:|",
    ]
    for dim in sorted(key for key in scores if key != "overall"):
        lines.append(f"| {dim} | {scores[dim]:.1f} |")
    lines.append(f"| overall | {scores.get('overall', 0.0):.1f} |")
    lines.extend([
        "",
        "## Gate Summary",
        "",
        f"- P0/P1/P2 findings: {len(blockers)}",
        f"- Total checks: {len(results)}",
        "- Checks are per-file/per-copy where behavior parity is claimed; release readiness is replayed with a read-only subprocess.",
        "- No push, publish, public sync, credential access, destructive cleanup, or release signoff change was performed.",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Dimension | Severity | Score | Evidence | Recommendation |",
        "|---|---|---|---:|---|---|",
    ])
    for result in sorted(results, key=lambda item: (severity_rank(item.severity), item.scenario, item.evidence)):
        lines.append(f"| {result.scenario} | {result.dimension} | {result.severity} | {result.score:.1f} | {escape(result.evidence)} | {escape(result.recommendation)} |")
    lines.extend(["", "## Hash Stability", ""])
    for idx, digest_map in enumerate(hashes, start=1):
        lines.append(f"### Round {idx}")
        lines.append("")
        lines.append("| File | Hash |")
        lines.append("|---|---|")
        for spec, digest in sorted(digest_map.items()):
            lines.append(f"| `{spec}` | `{digest}` |")
        lines.append("")
    lines.extend([
        "## Interpretation",
        "",
        "- `stable-loop-pass` means deterministic multi-round coverage passed with no P0/P1/P2 and near-full scores.",
        "- Aggregate usability limitations are carried into the score instead of being hidden by pass markers.",
        "- This is local workflow stability evidence, not authorization to push, publish, public-sync, or change release signoff.",
        "- Team-ready release labeling still follows `release_readiness.py`; if signoff is pending, team-ready remains blocked even when this stability suite passes.",
    ])
    return "\n".join(lines) + "\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def status_text(results: list[CheckResult], rounds: int, report: Path) -> str:
    scores = aggregate_scores(results)
    label = final_label(results, scores)
    blockers = [result for result in results if result.severity in {"P0", "P1", "P2"}]
    return "\n".join([
        "# Workflow Stability Loop Final Status",
        "",
        f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Status: {label}",
        f"Rounds: {rounds}",
        f"P0/P1/P2 findings: {len(blockers)}",
        f"Overall score: {scores.get('overall', 0.0):.1f}",
        f"Report: {report}",
        "Boundary: local stability evidence only; no commit, push, publish, public sync, or release signoff authorization.",
        "",
    ])


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--status-output", type=Path)
    parser.add_argument("--stdout", action="store_true")
    parser.add_argument("--check-only", action="store_true", help="Run checks and print summary without writing reports.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    if args.rounds < 2:
        parser.error("--rounds must be at least 2")
    paths = default_paths()
    results, hashes = run_suite(paths, args.rounds)
    report = args.output or (paths["reports"] / "workflow_stability_loop_20260627.md")
    markdown = render_report(results, hashes, args.rounds)
    if not args.check_only:
        write(report, markdown)
        write(args.status_output or (paths["reports"] / "workflow_stability_loop_20260627_status.md"), status_text(results, args.rounds, report))
    if args.stdout:
        sys.stdout.write(markdown)
    scores = aggregate_scores(results)
    label = final_label(results, scores)
    blockers = [result for result in results if result.severity in {"P0", "P1", "P2"}]
    target = "check-only" if args.check_only else str(report)
    print(f"Workflow stability suite report: {target}")
    print(f"Final status: {label}; overall score: {scores.get('overall', 0.0):.1f}; P0/P1/P2: {len(blockers)}")
    return 1 if label != "stable-loop-pass" else 0


if __name__ == "__main__":
    raise SystemExit(main())
