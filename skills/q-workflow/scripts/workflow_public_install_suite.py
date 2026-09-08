"""Isolated public-distribution contracts; never consult the caller's profile.

Every round starts from the public installer. Temporary directories, subprocess
homes, profiles and bytecode policy are explicitly scoped to --fixture-root.
This is a local public-install gate, not remote proof or human-agent UX signoff.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts}


def run_public_install(repo: Path, args) -> int:
    checks = []
    root = args.fixture_root.resolve()
    root.mkdir(parents=True, exist_ok=True)

    def check(name, passed, evidence):
        checks.append({"id": name, "status": "pass" if passed else "fail", "evidence": evidence})

    for round_no in range(1, args.rounds + 1):
        label = f"r{round_no}"
        try:
            with tempfile.TemporaryDirectory(prefix="public-install-", dir=root) as raw:
                fixture = Path(raw)
                workspace, home = fixture / "workspace", fixture / "codex"
                hub, temp = workspace / "workflow-hub", fixture / "temp"
                temp.mkdir()
                home.mkdir()
                env = os.environ.copy()
                # Strip caller-specific routing and fault injection. Only children
                # receive these settings; the suite's process environment is unchanged.
                for key in list(env):
                    if key.startswith(("Q_", "CODEX_")):
                        env.pop(key)
                env.update({"CODEX_HOME": str(home), "Q_PROFILE_PATH": str(home / "q-profile.json"),
                            "HOME": str(fixture), "USERPROFILE": str(fixture),
                            "APPDATA": str(fixture / "appdata"), "LOCALAPPDATA": str(fixture / "localappdata"),
                            "TMP": str(temp), "TEMP": str(temp), "TMPDIR": str(temp),
                            "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
                # Avoid importing a caller's PowerShell 7/user modules into the
                # Windows PowerShell 5.1 installer process after home redirection.
                system_modules = Path(env.get("SystemRoot", "C:/Windows")) / "System32/WindowsPowerShell/v1.0/Modules"
                env["PSModulePath"] = str(system_modules)

                def run(command):
                    return subprocess.run([str(x) for x in command], cwd=fixture, env=env,
                                          capture_output=True, text=True, encoding="utf-8",
                                          errors="replace", timeout=120, check=False)

                def probe(name, command, predicate=lambda p: p.get("status") == "pass"):
                    result = run(command)
                    try:
                        payload = json.loads(result.stdout)
                    except (ValueError, TypeError):
                        payload = {}
                    passed = result.returncode == 0 and isinstance(payload, dict) and predicate(payload)
                    cases = payload.get("cases") if isinstance(payload, dict) else None
                    count = len(cases) if isinstance(cases, list) else cases
                    check(f"{label}-{name}", passed,
                          {"rc": result.returncode, "cases": count,
                           "detail": "" if passed else (result.stdout + result.stderr)[-2400:]})
                    return payload

                ps = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"]
                language = "en" if round_no % 2 else "zh"
                result = run([*ps, repo / "scripts/init-user.ps1", "-UserName", "Public Fixture",
                              "-WorkspaceRoot", workspace, "-WorkflowHubPath", hub,
                              "-CodexHome", home, "-RequireExplicitPaths", "-Language", language])
                check(f"{label}-fresh-install-{language}", result.returncode == 0,
                      {"rc": result.returncode, "detail": (result.stdout + result.stderr)[-1400:]})
                if result.returncode:
                    continue
                state = hub / "personal-state"
                scripts = home / "skills/q-workflow/scripts"
                base = [sys.executable, "-B", scripts / "q_base_command.py", "--format", "json"]
                manager = [sys.executable, "-B", scripts / "q_workflow_manager.py", "--format", "json"]
                profile_path = home / "q-profile.json"
                profile = json.loads(profile_path.read_text(encoding="utf-8-sig"))
                check(f"{label}-profile-authority", Path(profile["hub"]) == hub and
                      Path(profile["projects"]) == workspace, "all explicit paths preserved")
                probe("empty-todo", [*base, "--input", "TODO"],
                      lambda p: p.get("open_count") == 0 and p.get("items") == [] and
                      Path(p.get("authority", "")) == state / "TODO.md")
                probe("fresh-resume", [*base, "--input", "小Q"],
                      lambda p: p.get("command_id") == "quick-resume" and p.get("phase") == "A"
                      and bool(p.get("current_focus")))
                probe("seed-todo", [*base, "--input", "TODO:public-fixture | Verify the isolated resume flow.", "--commit"],
                      lambda p: p.get("command_id") == "todo-add")
                # TODO commit changes authority only. Rebuild its read-only mirror
                # through the supported explicit operation, never fixture writes.
                probe("todo-mirror-preflight", [*base, "--preflight-sync"])
                listed = probe("seeded-todo", [*base, "--input", "TODO", "--sync-runtime"],
                               lambda p: p.get("open_count") == 1 and len(p.get("items", [])) == 1
                               and p.get("mirror", {}).get("match") is True)
                probe("todo-select", [*base, "--input", "1", "--context", "todo-list",
                                      "--context-token", str(listed.get("context_token", ""))],
                      lambda p: p.get("command_id") == "todo-select" and bool(p.get("selected_detail")))

                # Register the fixture through the actual plan/apply interface,
                # never hand-write an authoritative task/event binding.
                record = {"format_version": 1, "schema": "q-workflow-task-v1", "task_id": "public-fixture",
                          "trace_id": "PUBLIC-FIXTURE", "execution_epoch": 1, "state_revision": "fixture-r1",
                          "authority_event": "fixture-register-r1", "work_state": "briefing",
                          "integrity_state": "local-validated", "release_state": "local-only",
                          "role_plan": {"id": "fixture-role-plan", "primary": {"owner": "main", "status": "planned"},
                                        "reviewer": {"owner": "reviewer", "status": "pending"},
                                        "validator": {"owner": "validator", "status": "pending"}},
                          "remote": {"status": "unproven", "proven": False},
                          "next_action": "Verify the isolated public fixture.", "updated_at": "2026-01-01T00:00:00+00:00",
                          "focus": {"summary": "Public install fixture."},
                          "detail": {"recovery_rules": ["Resume this isolated fixture only."],
                                     "non_executable_index": ["No external task state is executable."]}}
                candidate, focus, plan = fixture / "candidate.json", fixture / "focus.md", fixture / "plan.json"
                candidate.write_text(json.dumps(record), encoding="utf-8")
                focus.write_text("Public install fixture.", encoding="utf-8")
                probe("task-plan", [*manager, "task", "plan", "--record", candidate, "--focus-file", focus, "--output", plan],
                      lambda p: plan.is_file())
                probe("task-apply", [*manager, "task", "apply", "--plan", plan, "--yes"],
                      lambda p: (state / "tasks/public-fixture.json").is_file())
                probe("task-binding", [*manager, "task", "validate", "--task-id", "public-fixture"])
                probe("seeded-resume", [*base, "--input", "小Q"],
                      lambda p: p.get("phase") == "A" and "Public install fixture" in str(p.get("current_focus")))
                probe("lifecycle-bound-task", [sys.executable, "-B", scripts / "workflow_lifecycle.py", "--strict", "--format", "json"],
                      lambda p: p.get("status") == "pass" and p.get("task_record", {}).get("record", {}).get("task_id") == "public-fixture")
                probe("state-mirror-audit", [*base, "--audit"])
                for command, expected in (("help", "help"), ("status", "status"), ("checkpoint", "checkpoint"), ("TOKEN", "token-dashboard")):
                    probe(f"base-{command}", [*base, "--input", command], lambda p, e=expected: p.get("command_id") == e)

                registry = json.loads((repo / "skills/q-workflow/references/surface-registry.json").read_text(encoding="utf-8-sig"))
                names = sorted(row["id"] for row in registry["skills"] if row["canonical_surface"] == "source" and "bootstrap" in row["expected_surfaces"])

                def parity(stage):
                    for name in names:
                        expected = hashes(repo / "skills" / name)
                        for surface, directory in (("bootstrap", hub / "bootstrap/skills"), ("runtime", home / "skills")):
                            check(f"{label}-{stage}-{name}-{surface}", bool(expected) and expected == hashes(directory / name), "recursive SHA-256 parity")
                    check(f"{label}-{stage}-profile-parity", hashes(hub / "generated-skills/q-assistant-profile") ==
                          hashes(home / "skills/q-assistant-profile"), "generated profile SHA-256 parity")

                parity("fresh")
                probe("registered-surfaces", [*manager, "surfaces", "--tier", "all", "--strict"],
                      lambda p: p.get("summary", {}).get("status") == "pass")

                profile["custom_public_fixture"] = {"deep": {"preserve": [1, 2, 3]}}
                profile["repositories"]["custom-fixture"] = {"path": str(fixture / "custom"), "unknown": "preserve"}
                profile_path.write_text(json.dumps(profile), encoding="utf-8")
                protected = {p: p.read_bytes() if p.is_file() else None for p in
                             (profile_path, state / "TODO.md", state / "ACTIVE_WORK.md", state / "TASK_EVENTS.jsonl")}
                def private_state_unchanged():
                    return all((p.read_bytes() if p.is_file() else None) == data for p, data in protected.items())
                # Deliberate installed-only marker makes rollback distinguishable
                # from a successful replace; never alter source to inject drift.
                marker = home / "skills/q-workflow/rollback-fixture.txt"
                marker.write_text("must survive failed update", encoding="utf-8")
                before_boot, before_runtime = hashes(hub / "bootstrap/skills"), hashes(home / "skills")
                updater = [*ps, repo / "scripts/sync-workflow-bootstrap.ps1", "-WorkflowHubPath", hub,
                           "-CodexHome", home, "-InstallRuntime"]
                result = run([*updater, "-TestFailAfterSwitch", str(len(names) + 1)])
                check(f"{label}-updater-fault-reached", result.returncode != 0 and "Injected package transaction failure" in result.stderr,
                      {"rc": result.returncode, "detail": result.stderr[-1400:]})
                check(f"{label}-updater-rollback", before_boot == hashes(hub / "bootstrap/skills") and before_runtime == hashes(home / "skills")
                      and private_state_unchanged(), "all skill bytes, custom profile and authoritative state restored")
                result = run(updater)
                check(f"{label}-updater-success", result.returncode == 0 and not marker.exists(), {"rc": result.returncode, "detail": result.stderr[-1400:]})
                check(f"{label}-updater-preserves-private-state", private_state_unchanged(), "unknown fields, TODO, focus and events unchanged")
                parity("updated")

                for name in ("q_workflow_manager", "workflow_pilot", "q_base_command", "workflow_lifecycle"):
                    probe(name + "-self-test", [sys.executable, "-B", scripts / (name + ".py"), "--self-test", "--format", "json"])
                for name in ("q_standard_check", "phase_b_output_preflight"):
                    result = run([sys.executable, "-B", scripts / (name + ".py"), "--self-test"])
                    check(f"{label}-{name}-self-test", result.returncode == 0 and ": PASS" in result.stdout,
                          {"rc": result.returncode, "detail": (result.stdout + result.stderr)[-1800:]})
                probe("stability-scenarios", [sys.executable, "-B", scripts / "workflow_stability_scenarios.py"])
                result = run([sys.executable, "-B", scripts / "test_release_v11_regressions.py"])
                check(f"{label}-release-regressions", result.returncode == 0 and "Ran 10 tests" in result.stderr and "OK" in result.stderr,
                      {"rc": result.returncode, "detail": result.stderr[-1800:]})
                for test_name in ("test_execution_policy.py", "test_release_repository.py", "test_task_transaction_recovery.py"):
                    result = run([sys.executable, "-B", scripts / test_name])
                    check(f"{label}-{Path(test_name).stem}", result.returncode == 0 and "Ran " in result.stderr and "OK" in result.stderr,
                          {"rc": result.returncode, "detail": result.stderr[-1800:]})
        except Exception as exc:
            check(f"{label}-fatal", False, str(exc))

    failures = [c for c in checks if c["status"] != "pass"]
    status = {"mode": "public-install", "status": "pass" if not failures else "blocked",
              "rounds": args.rounds, "checks": len(checks), "failures": len(failures),
              "remote_status": "unproven", "fixture_root": str(root), "results": checks}
    report = "# Public Installation Contract Report\n\n" + json.dumps(status, ensure_ascii=False, indent=2) + "\n"
    if not args.check_only:
        for path, content in ((args.output, report), (args.status_output, json.dumps(status, ensure_ascii=False, indent=2) + "\n")):
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
    if args.stdout or args.check_only:
        print(report)
    return 1 if failures else 0
