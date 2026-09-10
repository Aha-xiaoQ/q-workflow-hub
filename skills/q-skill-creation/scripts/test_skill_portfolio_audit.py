"""Regression tests for audit scope and false-positive severity (stdlib only)."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import skill_portfolio_audit as audit


class PortfolioAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "sample" / "SKILL.md"
        self.skill.parent.mkdir()
        self.base = "---\nname: sample\ndescription: Use when testing a skill.\n---\n# Default\nValidate output.\n"

    def issues(self, content):
        self.skill.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return {row["code"]: row["severity"] for row in audit.audit_skill("test", self.skill)["issues"]}

    def test_length_is_advisory(self):
        result = self.issues(self.base + "useful context\n" * 300)
        self.assertEqual(result["skill_md_too_large"], "warning")
        self.assertNotIn("blocker", result.values())

    def test_mixed_lf_crlf_is_advisory(self):
        self.assertEqual(self.issues(self.base.replace("# Default\n", "# Default\r\n"))["mixed_line_endings"], "warning")

    def test_bare_cr_is_blocking_even_with_other_endings(self):
        content = self.base.replace("# Default\n", "# Default\r\n") + "bare\rline\n"
        self.assertEqual(audit.line_ending_issue(content.encode()), "bare-cr")
        self.assertEqual(self.issues(content)["mixed_line_endings"], "blocker")

    def test_missing_required_reference_blocks(self):
        self.assertEqual(self.issues(self.base + "Read `references/required.md`.\n")["missing_referenced_file"], "blocker")

    def test_missing_frontmatter_fields_block(self):
        for content, key in [("# Missing\n", "frontmatter_missing"),
                             (self.base.replace("name: sample\n", ""), "name_missing"),
                             (self.base.replace("description: Use when testing a skill.\n", ""), "description_missing")]:
            with self.subTest(key=key):
                self.assertEqual(self.issues(content)[key], "blocker")

    def run_cli(self, *args, content=None, authority_errors=None):
        output = self.root / "report.json"
        self.issues(self.base if content is None else content)
        with patch.object(sys, "argv", ["audit", *args, "--json-out", str(output)]), \
             patch.object(audit, "profile_authority_errors", return_value=(self.root / "profile.json", authority_errors or [])), \
             patch.object(audit, "default_roots", return_value={"default": self.root}), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = audit.main()
        return code, json.loads(output.read_text(encoding="utf-8"))

    def test_only_roots_excludes_valid_profile_defaults(self):
        code, report = self.run_cli("--only-roots", "--root", f"chosen={self.root}")
        self.assertEqual(code, 0)
        self.assertEqual(set(report["roots"]), {"chosen"})
        self.assertEqual(report["authority"]["mode"], "explicit-roots")

    def test_explicit_root_isolation_and_dedup_remain(self):
        _, report = self.run_cli("--root", f"chosen={self.root}", "--root", f"alias={self.root}")
        self.assertEqual(set(report["roots"]), {"chosen", "alias"})
        self.assertEqual(report["roots"]["alias"]["duplicate_of"], "chosen")
        self.assertEqual(report["summary"]["skill_count"], 1)

    def test_warning_does_not_mask_required_failure_cli(self):
        for content in [self.base + "context\n" * 300 + "Read `references/missing.md`.\n",
                        self.base.replace("name: sample\n", "").replace("# Default\n", "# Default\r\n")]:
            with self.subTest(content=content[:80]):
                code, report = self.run_cli("--fail-on-blocker", content=content)
                self.assertEqual(code, 1)
                self.assertGreater(report["summary"]["severity_counts"]["blocker"], 0)

    def test_invalid_profile_explicit_root_fallback(self):
        code, report = self.run_cli("--root", f"chosen={self.root}", authority_errors=["missing profile"])
        self.assertEqual(code, 0)
        self.assertEqual(report["authority"]["mode"], "explicit-roots")
        self.assertEqual(set(report["roots"]), {"chosen"})

    def test_invalid_profile_without_roots_blocks(self):
        code, report = self.run_cli(authority_errors=["missing profile"])
        self.assertEqual(code, 2)
        self.assertEqual(report["failure_class"], "profile-authority")

    def test_only_roots_requires_root(self):
        with self.assertRaises(SystemExit) as error:
            self.run_cli("--only-roots")
        self.assertEqual(error.exception.code, 2)

    def test_invalid_explicit_roots_fail(self):
        for value in ["bad", "=path", "name=", "  =  ", f"missing={self.root / 'absent'}"]:
            with self.subTest(root=value), self.assertRaises(SystemExit):
                self.run_cli("--root", value)


if __name__ == "__main__":
    unittest.main()
