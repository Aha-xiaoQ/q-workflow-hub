"""Isolated regressions for the v1.1 candidate review; never access real state."""

import argparse
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import q_workflow_manager as manager
import workflow_pilot as pilot
import active_work_pointer as pointers
import q_base_command as base


class ReleaseRegressions(unittest.TestCase):
    def test_first_idle_task_pointer(self):
        idle = "# Active Work\n\n## Current Focus\n\n- No active blocking focus.\n\n## Recovery Rule\n\nKeep this guidance.\n"
        rendered = pointers.render_active_work(idle, "Fixture task", {"task_id": "fixture"})
        self.assertEqual(pointers.inspect_active_work_text(rendered)["errors"], [])
        self.assertIn("Keep this guidance.", rendered)
        for malformed in (idle.replace("- No active blocking focus.", "Active task"),
                          idle + "\n## Current Focus\n\nDuplicate\n",
                          idle + "\n## RECOVERY_POINTER v2\n\ntask_id: old\n"):
            with self.subTest(malformed=malformed), self.assertRaises(pointers.ActiveWorkPointerError):
                pointers.render_active_work(malformed, "New task", {"task_id": "new"})

    def test_todo_names_preserve_english_and_short_chinese(self):
        for content in ("Verify the isolated resume flow.", "网站", "修复", "A"):
            description = base.localized_todo_description(content)
            display = base.todo_display_from_content(content, description)
            item = base.TodoItem(1, "2026-09-06", "fixture", description, "")
            with self.subTest(content=content), patch.object(Path, "is_file", return_value=True), patch.object(base, "read_json", return_value={
                "version": 1, "language": "zh-CN", "items": {"fixture": display}
            }):
                self.assertEqual(base.load_todo_display(Path("fixture"), [item])[0]["name"], content[:32] + ("…" if len(content) > 32 else ""))

    def task_list(self, present):
        pointer = {
            "schema": "q-workflow-focus-v2", "task_id": "active-task",
            "work_state": "active", "visibility_latch": "phase-b-required",
        }
        with ExitStack() as stack:
            stack.enter_context(patch.object(manager, "load_profile", return_value=(Path("fixture.json"), {})))
            stack.enter_context(patch.object(manager, "personal_hub", return_value=Path("fixture")))
            stack.enter_context(patch.object(manager, "inspect_active_work", return_value={"errors": [], "recovery_pointer": pointer}))
            stack.enter_context(patch.object(Path, "is_dir", return_value=True))
            stack.enter_context(patch.object(Path, "glob", return_value=[Path("active-task.json")] if present else []))
            stack.enter_context(patch.object(manager, "inspect_task_record", return_value={
                "status": "pass", "errors": [], "record": {"task_id": "active-task", "work_state": "active"},
            }))
            return manager.task_list_report(Path("fixture.json"), work_state="paused")

    def test_filtered_focus_is_not_missing(self):
        result = self.task_list(True)
        self.assertEqual(result["focus_errors"], [])
        self.assertEqual(result["summary"], {"count": 0, "failures": 0, "status": "pass"})

    def test_filtered_list_still_detects_missing_focus(self):
        result = self.task_list(False)
        self.assertEqual(len(result["focus_errors"]), 1)
        self.assertEqual(result["summary"]["status"], "attention")

    def probe(self, output, code=0):
        completed = SimpleNamespace(returncode=code, stdout=output, stderr="")
        with patch.object(pilot.subprocess, "run", return_value=completed):
            return pilot.run_manager_probe("doctor", ["doctor"], manager=Path("fake.py"), profile=Path("fake.json"), timeout_seconds=1)

    def test_invalid_probe_output_fails_closed(self):
        for output, expected in [
            ("", "empty-output"), ("not JSON", "invalid-json"),
            ("{}", "invalid-status"), ('{"status":"unknown"}', "invalid-status"),
            ("[]", "invalid-status"),
        ]:
            with self.subTest(output=output):
                result = self.probe(output)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["failure_class"], expected)

    def test_explicit_probe_success_and_failure(self):
        for output in ['{"status":"pass"}', '{"summary":{"status":"pass"}}']:
            with self.subTest(output=output):
                self.assertEqual(self.probe(output)["status"], "pass")
                self.assertEqual(self.probe(output, code=1)["status"], "blocked")
        self.assertEqual(self.probe('{"status":"blocked","failure_class":"timeout"}')["failure_class"], "timeout")

    def mutate(self, before, command="resume", band="GREEN", rows=None):
        state = {
            "format_version": 1, "pilot_id": "test", "trace_id": "test",
            "run_state": before, "system_volume": "fake", "system_volume_band": band,
            "automation": {"scheduled_runs": 7, "automation_delete": "verified"},
            "sampling": {}, "authority": {}, "preserved_focus": {}, "resume_condition": "test",
        }
        with ExitStack() as stack:
            stack.enter_context(patch.object(pilot, "acquire_lock", return_value=1))
            stack.enter_context(patch.object(pilot, "release_lock"))
            stack.enter_context(patch.object(pilot, "load_json", return_value=state))
            stack.enter_context(patch.object(pilot, "load_samples", return_value=rows or []))
            stack.enter_context(patch.object(pilot, "volume_snapshot", return_value={"band": band, "free_bytes": 10**10, "free_gib": 9.31}))
            write = stack.enter_context(patch.object(pilot, "atomic_replace_bytes"))
            try:
                return pilot.mutate_state(argparse.Namespace(pilot_dir=Path("fixture"), yes=True, command=command, reason="test"))
            except pilot.PilotError:
                write.assert_not_called()
                raise

    def test_only_user_and_resource_pauses_resume(self):
        for before in ["PAUSED_USER", "PAUSED_RESOURCE"]:
            with self.subTest(before=before):
                payload, code = self.mutate(before)
                self.assertEqual(code, 0)
                self.assertEqual(payload["transition"]["to"], "ACTIVE")

    def test_terminal_cleanup_and_active_states_cannot_resume(self):
        for before in ["COMPLETE", "STOPPED", "STOPPING", "PAUSED_AUTOMATION_CLEANUP", "ACTIVE", "UNKNOWN"]:
            with self.subTest(before=before), self.assertRaises(pilot.PilotError):
                self.mutate(before)

    def test_cleanup_cannot_bypass_guard_via_pause(self):
        for before in ["STOPPING", "PAUSED_AUTOMATION_CLEANUP"]:
            with self.subTest(before=before), self.assertRaises(pilot.PilotError):
                self.mutate(before, command="pause")

    def test_resume_retains_resource_and_completion_guards(self):
        with self.assertRaises(pilot.PilotError):
            self.mutate("PAUSED_RESOURCE", band="YELLOW")
        with self.assertRaises(pilot.PilotError):
            self.mutate("PAUSED_USER", rows=[{"source": "scheduled", "status": "pass"}] * 7)


if __name__ == "__main__":
    unittest.main()
