"""Validate the mandatory first line of a Phase B Chinese workflow update."""
from __future__ import annotations

import argparse
import re
import tempfile
from pathlib import Path

from active_work_pointer import inspect_active_work

PREFIX = "小Q工作流 / "
PATTERN = re.compile(r"^小Q工作流 / (q-[a-z0-9-]+(?: \+ q-[a-z0-9-]+)*) / (\S.*)$")
PHASE_B_STATES = {"active", "validating", "blocked"}


def registered_skills(skill_root: Path) -> set[str]:
    return {entry.name for entry in skill_root.iterdir() if entry.is_dir() and entry.name.startswith("q-") and (entry / "SKILL.md").is_file()}


def validate(text: str, skill_root: Path) -> tuple[bool, str]:
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first:
        return False, "missing first non-empty line"
    match = PATTERN.fullmatch(first)
    if not match:
        return False, "expected: 小Q工作流 / q-<skill-id> / <current action>"
    skill_ids = match.group(1).split(" + ")
    available = registered_skills(skill_root)
    missing = [skill_id for skill_id in skill_ids if skill_id not in available]
    if missing:
        return False, "unregistered skill: " + ", ".join(missing)
    return True, " + ".join(skill_ids)


def validate_active_latch(active_work: Path) -> tuple[bool, str]:
    state = inspect_active_work(active_work)
    if state.get("errors"):
        return False, "invalid ACTIVE_WORK: " + " | ".join(state["errors"])
    pointer = state.get("recovery_pointer", {})
    if not isinstance(pointer, dict):
        return False, "ACTIVE_WORK recovery pointer is unreadable"
    expected = "phase-b-required" if pointer.get("work_state") in PHASE_B_STATES else "not-required"
    actual = pointer.get("visibility_latch")
    if actual != expected:
        return False, f"visibility_latch={actual!r}; expected {expected!r}"
    return True, expected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--active-work", type=Path)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        root = args.skill_root
        cases = [
            ("小Q工作流 / q-workflow / 格式预检\n", True),
            ("小Q工作流 / q-workflow + q-skill-creation / 多技能格式预检\n", True),
            ("进度更新\n", False),
            ("小Q工作流 / workflow / 格式预检\n", False),
            ("小Q工作流 / q-not-a-registered-skill / 格式预检\n", False),
            ("小Q工作流 / q-workflow + q-not-a-registered-skill / 多技能注册预检\n", False),
        ]
        failures = [text for text, expected in cases if validate(text, root)[0] != expected]
        with tempfile.TemporaryDirectory() as temp_raw:
            active_path = Path(temp_raw) / "ACTIVE_WORK.md"
            active_fixture = (
                "# Active Work\n\n## Current Focus\n\nSelf test.\n\n## RECOVERY_POINTER v2\n\n"
                "schema: q-workflow-focus-v2\ntask_id: self-test\nwork_state: active\n"
                "visibility_latch: phase-b-required\n"
            )
            active_path.write_text(active_fixture, encoding="utf-8")
            if not validate_active_latch(active_path)[0]:
                failures.append("active Phase B latch fixture")
            active_path.write_text(active_fixture.replace("visibility_latch: phase-b-required\n", ""), encoding="utf-8")
            if validate_active_latch(active_path)[0]:
                failures.append("missing Phase B latch fixture")
            active_path.write_text(
                active_fixture.replace("work_state: active", "work_state: briefing").replace(
                    "visibility_latch: phase-b-required", "visibility_latch: not-required"
                ),
                encoding="utf-8",
            )
            if not validate_active_latch(active_path)[0]:
                failures.append("Phase A not-required latch fixture")
        total_cases = len(cases) + 3
        print(f"phase-b-output-preflight: {'PASS' if not failures else 'FAIL'} ({total_cases} cases)")
        return 0 if not failures else 1
    if args.text_file is None:
        parser.error("--text-file or --self-test is required")
    if args.active_work is not None:
        latch_ok, latch_detail = validate_active_latch(args.active_work)
        if not latch_ok:
            print(f"phase-b-output-preflight: FAIL ({latch_detail})")
            return 1
    ok, detail = validate(args.text_file.read_text(encoding="utf-8"), args.skill_root)
    print(f"phase-b-output-preflight: {'PASS' if ok else 'FAIL'} ({detail})")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
