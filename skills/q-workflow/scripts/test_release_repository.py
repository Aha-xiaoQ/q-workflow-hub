"""Release project binding: no network or real profile writes."""
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from q_workflow_manager import live_remote_receipt_errors
from workflow_task_state import flatten_task_record, release_receipt_errors


class ReleaseRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.profile = {"repositories": {
            "q-workflow-hub": {"path": ".", "remote": "https://example.test/workflow.git"},
            "demo": {"path": ".", "remote": "https://example.test/demo.git"}}}
        self.binding = {"release_repository": "demo", "release_remote": "https://example.test/demo.git",
                        "release_branch": "main", "release_target_oid": "a" * 40}

    def test_explicit_project_not_workflow_remote(self):
        with patch("q_workflow_manager.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "a"*40+"\trefs/heads/main\n", "")) as run:
            self.assertEqual(live_remote_receipt_errors(self.profile, self.binding), [])
            self.assertIn("https://example.test/demo.git", run.call_args.args[0])
            self.assertNotIn("https://example.test/workflow.git", run.call_args.args[0])

    def test_legacy_binding_is_preserved(self):
        b = dict(self.binding, release_remote="https://example.test/workflow.git")
        del b["release_repository"]
        with patch("q_workflow_manager.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "a"*40+"\trefs/heads/main\n", "")):
            self.assertEqual(live_remote_receipt_errors(self.profile, b), [])

    def test_unknown_or_empty_repository_does_not_contact_network(self):
        for key in ("unknown", "", None):
            with patch("q_workflow_manager.subprocess.run") as run:
                self.assertTrue(live_remote_receipt_errors(self.profile, dict(self.binding, release_repository=key)))
                run.assert_not_called()

    def test_other_registered_repo_url_still_rejected(self):
        with patch("q_workflow_manager.subprocess.run") as run:
            self.assertTrue(live_remote_receipt_errors(self.profile, dict(self.binding, release_remote="https://example.test/workflow.git")))
            run.assert_not_called()

    def test_named_remote_must_match_registered_url(self):
        responses = [subprocess.CompletedProcess([], 0, "https://example.test/demo.git\n", ""),
                     subprocess.CompletedProcess([], 0, "a"*40+"\trefs/heads/main\n", "")]
        with patch("q_workflow_manager.subprocess.run", side_effect=responses):
            self.assertEqual(live_remote_receipt_errors(self.profile, dict(self.binding, release_remote="origin")), [])

    def test_stale_oid_rejected(self):
        with patch("q_workflow_manager.subprocess.run", return_value=subprocess.CompletedProcess([], 0, "b"*40+"\trefs/heads/main\n", "")):
            self.assertTrue(live_remote_receipt_errors(self.profile, self.binding))

    def test_flatten_preserves_explicit_repository(self):
        self.assertEqual(flatten_task_record({"remote": self.binding})["release_repository"], "demo")

    def test_receipt_is_bound_to_project_even_with_valid_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            hub = Path(temp)
            (hub/"reports").mkdir()
            path = hub/"reports"/"receipt.json"
            data = dict(format_version=1, strict_readiness_status="pass", repository="demo",
                        remote=self.binding["release_remote"], branch="main", target_oid="a"*40,
                        remote_head="a"*40, fetched_at="2026-09-08T00:00:00+00:00", signoff_id="test")
            path.write_text(json.dumps(data), encoding="utf-8")
            b = dict(self.binding, release_receipt_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     release_fetched_at=data["fetched_at"], signoff_id="test")
            self.assertEqual(release_receipt_errors(path, b, hub), [])
            self.assertTrue(release_receipt_errors(path, dict(b, release_repository="q-workflow-hub"), hub))
            del b["release_repository"]
            self.assertTrue(release_receipt_errors(path, b, hub))


if __name__ == "__main__":
    unittest.main()
