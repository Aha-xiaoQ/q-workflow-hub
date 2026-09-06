#!/usr/bin/env python3
"""Validate q-workflow skill release gates for fresh install and upgrade paths."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROFILE_TERMS = {
    "wake_route": "When the user says only",
    "quick_resume_first_line": "Quick Resume first-line format",
    "quick_resume_shape": "【",
    "execution_status_line": "Execution status line format",
    "execution_status_shape": "小Q工作流 / <route-or-skill-id> / <current-action>",
    "todo_exact": "Exact `TODO` / `todo`",
    "todo_output": "TODO output must start with",
    "q_profile_route": "q-profile.json",
    "active_work_route": "ACTIVE_WORK.md",
    "first_run_guide_route": "FIRST_RUN_GUIDE",
}

TODO_TERMS = {
    "numbered_list": "numbered `1.`",
    "two_line": "stable two-line item",
    "no_extra_blank": "not insert an extra blank line",
    "fullwidth_todo": "TODO\uff1a<content>",
}

BAD_MARKERS = {
    "old_status_placeholder": "?Q / <route-or-skill>",
    "replacement_char": "\ufffd",
    "mojibake_todo_colon": "TODO\u00ef\u00bc",
    "mojibake_xiaoq": "\u00e5\u00b0",
    "mojibake_health": "\u00e4\u00bd",
    "mojibake_left_bracket": "\u00e3\u20ac",
    "mojibake_common_zh": "\u00e6\u00b5",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_required(path: Path, terms: dict[str, str], label: str, failures: list[str]) -> None:
    if not path.exists():
        failures.append(f"{label} missing: {path}")
        return
    try:
        text = read_text(path)
    except UnicodeDecodeError as exc:
        failures.append(f"{label} is not strict UTF-8: {path}: {exc}")
        return
    for name, term in terms.items():
        if term not in text:
            failures.append(f"{label} missing {name}: {term!r} in {path}")
    for name, marker in BAD_MARKERS.items():
        if marker in text:
            failures.append(f"{label} contains bad marker {name}: {marker!r} in {path}")


def run_init(repo_root: Path, workspace: Path, hub: Path, codex: Path) -> subprocess.CompletedProcess[str]:
    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-NoProfile",
        "-File",
        str(repo_root / "scripts" / "init-user.ps1"),
        "-UserName",
        "GateUser",
        "-WorkspaceRoot",
        str(workspace),
        "-WorkflowHubPath",
        str(hub),
        "-CodexHome",
        str(codex),
        "-WorkflowLabel",
        "q-workflow",
        "-Language",
        "zh",
    ]
    return subprocess.run(cmd, cwd=str(repo_root), text=True, encoding="utf-8", errors="replace", capture_output=True)


def run_smoke(repo_root: Path, failures: list[str]) -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="qwf-release-gate-"))
    try:
        workspace = temp_root / "workspace"
        hub = workspace / "workflow-hub"
        codex = temp_root / "codex"
        workspace.mkdir(parents=True, exist_ok=True)
        codex.mkdir(parents=True, exist_ok=True)

        result = run_init(repo_root, workspace, hub, codex)
        if result.returncode != 0:
            failures.append("fresh init-user.ps1 failed:\n" + result.stdout + result.stderr)
            return

        generated_profile = hub / "generated-skills" / "q-assistant-profile" / "SKILL.md"
        runtime_profile = codex / "skills" / "q-assistant-profile" / "SKILL.md"
        hub_todo = hub / "personal-state" / "TODO.md"
        q_profile_path = codex / "q-profile.json"

        check_required(generated_profile, PROFILE_TERMS, "generated q-assistant-profile", failures)
        check_required(runtime_profile, PROFILE_TERMS, "runtime q-assistant-profile", failures)
        check_required(hub_todo, TODO_TERMS, "hub TODO", failures)

        registry = json.loads((repo_root / "skills/q-workflow/references/surface-registry.json").read_text(encoding="utf-8-sig"))
        expected_skills = {
            row["id"] for row in registry["skills"]
            if row["canonical_surface"] == "source" and "bootstrap" in row["expected_surfaces"]
        }
        for skill_id in sorted(expected_skills):
            for surface in (hub / "bootstrap/skills", codex / "skills"):
                if not (surface / skill_id / "SKILL.md").is_file():
                    failures.append(f"fresh install missing registered skill: {surface / skill_id}")

        if not q_profile_path.exists():
            failures.append(f"q-profile.json missing after install: {q_profile_path}")
        else:
            try:
                profile = json.loads(q_profile_path.read_text(encoding="utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                failures.append(f"q-profile.json is invalid: {exc}")
            else:
                if Path(profile.get("hub", "")) != hub:
                    failures.append(f"q-profile.json hub mismatch: {profile.get('hub')!r} != {str(hub)!r}")
                if Path(profile.get("projects", "")) != workspace:
                    failures.append(f"q-profile.json projects mismatch: {profile.get('projects')!r} != {str(workspace)!r}")

        sentinel = "\n<!-- QWF_RELEASE_GATE_SENTINEL -->\n"
        if hub_todo.exists():
            hub_todo.write_text(hub_todo.read_text(encoding="utf-8") + sentinel, encoding="utf-8")
        result = run_init(repo_root, workspace, hub, codex)
        if result.returncode != 0:
            failures.append("upgrade init-user.ps1 failed:\n" + result.stdout + result.stderr)
            return
        for label, path in (("hub TODO", hub_todo),):
            if sentinel.strip() not in path.read_text(encoding="utf-8"):
                failures.append(f"upgrade did not preserve {label} sentinel: {path}")
        check_required(codex / "skills" / "q-assistant-profile" / "SKILL.md", PROFILE_TERMS, "upgraded runtime q-assistant-profile", failures)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    default_repo_root = Path(__file__).resolve().parents[1]

    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(default_repo_root))
    parser.add_argument("--skip-smoke", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []

    check_required(repo_root / "templates" / "skills" / "q-assistant-profile" / "SKILL.md.template", PROFILE_TERMS, "q-assistant-profile template", failures)
    check_required(repo_root / "templates" / "workflow-hub" / "personal-state" / "TODO.md.template", TODO_TERMS, "TODO template", failures)

    init_path = repo_root / "scripts" / "init-user.ps1"
    if init_path.exists():
        init_text = read_text(init_path)
        for term in ("q-profile.json", "WorkflowHubPath", "templates\\workflow-hub", "q-assistant-profile"):
            if term not in init_text:
                failures.append(f"init-user.ps1 missing release gate term: {term}")
    else:
        failures.append(f"init-user.ps1 missing: {init_path}")

    smoke_ran = not args.skip_smoke
    if smoke_ran:
        run_smoke(repo_root, failures)

    if failures:
        print("Release skill gates: FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Release skill gates: PASS")
    if smoke_ran:
        print("Checked profile template, workflow-hub TODO template, q-profile route, fresh install, runtime profile install, and hub TODO upgrade preservation.")
    else:
        print("Checked profile template, workflow-hub TODO template, and q-profile route. Fresh install and upgrade smoke were skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
