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

    def run_cli(self, *args, content=None, authority_errors=None, defaults=None):
        output = self.root / "report.json"
        self.issues(self.base if content is None else content)
        with patch.object(sys, "argv", ["audit", *args, "--json-out", str(output)]), \
             patch.object(audit, "profile_authority_errors", return_value=(self.root / "profile.json", authority_errors or [])), \
             patch.object(audit, "default_roots", return_value={"default": self.root} if defaults is None else defaults), \
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
        for value in ["bad", "=path", "name=", "  =  "]:
            with self.subTest(root=value), self.assertRaises(SystemExit):
                self.run_cli("--root", value)

    def document(self, relative, text="Reviewed instructions.\n", base=None):
        path = (base or self.skill.parent) / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_original_four_missing_reference_forms_are_not_silent(self):
        forms = ["Read `references/missing.md`.",
                 "Read [the guide](references/missing.md).",
                 "Run `scripts/missing.py --check`.",
                 "Read `q-workflow/references/missing.md`."]
        for form in forms:
            with self.subTest(form=form):
                self.issues(self.base + form + "\n")
                result = audit.audit_skill("test", self.skill)
                self.assertEqual(result["metrics"]["missing_required_refs"], 1)
                self.assertEqual(result["refs"][0]["status"], "missing")
        self.assertEqual(result["refs"][0]["owner"], "cross-skill:q-workflow")

    def test_existing_paths_commands_spaces_and_explicit_cross_owner(self):
        self.document("references/guide with spaces.md")
        self.document("scripts/check thing.py", "raise AssertionError('must not execute')\n")
        cross = self.document("q-other/references/guide.md", base=self.root)
        self.document("q-other/SKILL.md", self.base.replace("sample", "q-other"), base=self.root)
        content = self.base + '\n'.join([
            'Read [guide](<references/guide with spaces.md>).',
            'Read [encoded](references/guide%20with%20spaces.md "title").',
            'Run `python "scripts/check thing.py" --input references/not-an-instruction.md`.',
            'Read `q-other/references/guide.md`.',
            'Read [external](https://example.invalid/anything.md) and [section](#section).',
        ])
        self.issues(content)
        result = audit.audit_skill("test", self.skill)
        self.assertEqual(result["metrics"]["missing_required_refs"], 0)
        self.assertEqual(len(result["refs"]), 6)
        self.assertIn(str(cross.resolve()), result["reference_scan"]["visited_files"])
        command = next(r for r in result["refs"] if r["ref"].endswith(".py"))
        self.assertEqual(command["status"], "ok")

    def test_missing_non_q_cross_skill_owner_is_explicit(self):
        refs = audit.referenced_paths(self.skill.parent, "Read `text-format-hygiene/references/regression-ledger.md`.\n")
        self.assertEqual(refs[0]["owner"], "cross-skill:text-format-hygiene")
        self.assertEqual(refs[0]["target"], str((self.root / "text-format-hygiene/references/regression-ledger.md").resolve()))
        self.assertEqual(refs[0]["status"], "missing")

    def test_recursive_missing_and_cycle_preserve_source_line(self):
        first = self.document("workflows/start.md", "Read [next](../references/next.md).\n")
        second = self.document("references/next.md", "Read [back](../workflows/start.md).\nRead `scripts/deep-missing.py --check`.\n")
        self.issues(self.base + "Read `workflows/start.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual(len(result["reference_scan"]["visited_files"]), 3)
        self.assertEqual(result["metrics"]["missing_required_refs"], 1)
        missing = next(r for r in result["refs"] if r["status"] == "missing")
        self.assertEqual(missing["source"], str(second.resolve()))
        self.assertEqual(missing["line"], 2)
        self.assertEqual(missing["target"], str((self.skill.parent / "scripts/deep-missing.py").resolve()))

    def test_link_containing_directory_vs_inline_skill_directory(self):
        local = self.document("workflows/references/local.md")
        root_ref = self.document("references/root.md")
        self.document("workflows/start.md", "Read [local](references/local.md).\nRead `references/root.md`.\nRead `./references/local.md`.\n")
        self.issues(self.base + "Read `workflows/start.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual(result["metrics"]["missing_required_refs"], 0)
        targets = {ref["target"] for ref in result["refs"]}
        self.assertTrue({str(local.resolve()), str(root_ref.resolve())} <= targets)
        # A Markdown link must not silently fall back to the skill root.
        self.document("workflows/start.md", "Read [wrong local](references/root.md).\n")
        self.assertEqual(audit.audit_skill("test", self.skill)["metrics"]["missing_required_refs"], 1)

    def test_optional_context_is_local_and_uncertainty_is_reported(self):
        self.issues(self.base + "Read `references/optional.md` when available; read `references/required.md`.\nRead `references/<topic>.md`.\nRead [unhandled](custom://guide).\nWrite `OUTPUT.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual([r["status"] for r in result["refs"]],
                         ["optional-missing", "missing", "dynamic", "unsupported-scheme", "role-uncertain"])
        self.assertEqual(result["metrics"]["missing_required_refs"], 1)
        self.assertEqual(result["reference_scan"]["status"], "partial")

    def test_optional_existing_ref_is_traversed_and_missing_child_still_required(self):
        self.document("references/optional.md", "Read `references/required.md`.\n")
        self.issues(self.base + "Read `references/optional.md` if available.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual(result["refs"][0]["status"], "ok")
        self.assertEqual(result["refs"][1]["status"], "missing")

    def test_optional_qualification_cannot_leak_across_sentences_or_from_filename(self):
        for separator in [". ", "! ", "? ", "\u3002"]:
            with self.subTest(separator=separator):
                content = self.base + "Read `references/optional.md` when available" + separator + "Read `references/required.md`.\n"
                code, report = self.run_cli("--fail-on-blocker", content=content)
                self.assertEqual(code, 1)
                self.assertEqual([r["status"] for r in report["skills"][0]["refs"]], ["optional-missing", "missing"])
        refs = audit.referenced_paths(self.skill.parent, "Read `references/optional.md`.\n")
        self.assertEqual(refs[0]["status"], "missing")


    def test_ambiguous_optional_clause_is_partial_not_a_definite_waiver(self):
        self.issues(self.base + "Read `references/one.md` when available, then read `references/two.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual([r["status"] for r in result["refs"]], ["qualification-uncertain", "qualification-uncertain"])
        self.assertEqual(result["reference_scan"]["status"], "partial")
        self.assertTrue(all(not r["optional"] for r in result["refs"]))


    def test_file_shaped_directory_target_never_receives_complete_ok(self):
        (self.skill.parent / "references/required.md").mkdir(parents=True)
        for form in ["Read [required](references/required.md).\n", "Read `references/required.md`.\n"]:
            with self.subTest(form=form):
                self.issues(self.base + form)
                result = audit.audit_skill("test", self.skill)
                self.assertEqual(result["refs"][0]["status"], "not-a-file")
                self.assertEqual(result["reference_scan"]["status"], "partial")
                self.assertIn("reference_scan_partial", {i["code"] for i in result["issues"]})

    def test_skill_basename_directory_and_output_mentions_do_not_invent_missing_files(self):
        self.document("references/guide.md", "Inspect `SKILL.md`.\nPack assets under `assets/` or `schemas/`.\nAttribution belongs in `THIRD_PARTY_NOTICES.md`.\nRead `required.md`.\n")
        self.issues(self.base + "Read `references/guide.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual([ref["status"] for ref in result["refs"]],
                         ["ok", "ok", "directory-mention", "directory-mention", "role-uncertain", "missing"])
        self.assertEqual(result["metrics"]["missing_required_refs"], 1)

    def test_dynamic_root_alias_and_arbitrary_code_boundaries(self):
        self.document("scripts/check.py", "not executed\n")
        self.issues(self.base + "Run `python <skill-root>/scripts/check.py --check`.\n"
                    "Read `<project>/rules.md`.\n"
                    '`x = "references/not-a-ref.md"`\n'
                    "```python\nvalue = 'references/not-a-ref.md'\n```\n"
                    "<!-- Read `references/comment.md`. -->\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual([r["status"] for r in result["refs"]], ["ok", "dynamic"])
        self.assertEqual(result["reference_scan"]["excluded_fenced_blocks"], 1)

    def test_traversal_limit_is_partial_and_reports_unvisited_paths(self):
        target = self.document("references/next.md", "Read `references/missing.md`.\n")
        self.issues(self.base + "Read `references/next.md`.\n")
        result = audit.audit_skill("test", self.skill, max_reference_files=1)
        scan = result["reference_scan"]
        self.assertEqual(scan["status"], "partial")
        self.assertEqual(scan["skipped_files"], [{"path": str(target.resolve()), "reason": "traversal-limit"}])
        self.assertEqual(result["metrics"]["missing_required_refs"], 0)

    def test_unreadable_reference_is_partial_not_a_fabricated_missing_file(self):
        target = self.document("references/bad.md")
        target.write_bytes(b"\xff\xfe\x00")
        self.issues(self.base + "Read `references/bad.md`.\n")
        result = audit.audit_skill("test", self.skill)
        self.assertEqual(result["reference_scan"]["status"], "partial")
        self.assertEqual(result["reference_scan"]["skipped_files"][0]["reason"], "unreadable")
        self.assertEqual(result["metrics"]["missing_required_refs"], 0)

    def test_required_missing_roots_fail_even_without_fail_on_blocker(self):
        for extra in [(), ("--fail-on-blocker",)]:
            with self.subTest(extra=extra):
                code, report = self.run_cli(*extra, defaults={"required": self.root / "absent"})
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(report["roots"]["required"]["status"], "missing")
                self.assertEqual(report["summary"]["missing_required_scope_count"], 1)
        code, report = self.run_cli("--only-roots", "--root", f"requested={self.root / 'absent'}")
        self.assertEqual(code, 2)
        self.assertEqual(report["scope"]["missing"][0]["reason"], "required-root-missing")

    def test_optional_roots_skip_and_required_alias_cannot_hide_absence(self):
        absent = self.root / "absent"
        code, report = self.run_cli("--only-roots", "--optional-root", f"optional={absent}")
        self.assertEqual(code, 0)
        self.assertEqual(report["roots"]["optional"]["status"], "optional-missing")
        self.assertEqual(report["status"], "completed-with-skips")
        code, report = self.run_cli("--only-roots", "--root", f"needed={absent}", "--optional-root", f"optional={absent}")
        self.assertEqual(code, 2)
        self.assertEqual(report["roots"]["optional"]["duplicate_of"], "needed")

    def test_repeated_root_paths_and_conflicting_labels(self):
        _, report = self.run_cli("--only-roots", "--root", f"one={self.root}", "--root", f"one={self.root}", "--root", f"two={self.root}")
        self.assertEqual(report["summary"]["skill_count"], 1)
        self.assertEqual(len(report["scope"]["requests"]), 3)
        self.assertEqual(report["roots"]["two"]["status"], "duplicate")
        with self.assertRaises(SystemExit):
            self.run_cli("--root", f"one={self.root}", "--root", f"one={self.root / 'other'}")

    def test_system_discovery_is_opt_in_and_reported(self):
        nested = self.document(".system/system-sample/SKILL.md", self.base, base=self.root)
        _, report = self.run_cli("--only-roots", "--root", f"chosen={self.root}")
        self.assertEqual(report["summary"]["skill_count"], 1)
        skipped = next(r for r in report["scope"]["skipped"] if r["reason"] == "system-not-selected")
        self.assertIn(str(nested), skipped["entries"])
        _, report = self.run_cli("--only-roots", "--root", f"chosen={self.root}", "--include-system")
        self.assertEqual(report["summary"]["skill_count"], 2)
        self.assertIn(str(nested), report["roots"]["chosen"]["visited_entries"])

    def test_profile_defaults_include_personal_generated_root(self):
        profile = self.root / "q-profile.json"
        profile.write_text(json.dumps({"hub": str(self.root / "personal"), "repositories": {"q-workflow-hub": {"path": str(self.root / "source")}}}), encoding="utf-8")
        with patch.dict(audit.os.environ, {"Q_PROFILE_PATH": str(profile)}):
            roots = audit.default_roots()
        self.assertEqual(roots["personal_generated"], self.root / "personal/generated-skills")

    def test_agents_has_coverage_and_reference_checks_without_skill_frontmatter(self):
        agents = self.document("AGENTS.md", "Read [guide](instructions/guide.md).\n", base=self.root)
        guide = self.document("instructions/guide.md", "Read [missing](missing.md).\n", base=self.root)
        code, report = self.run_cli("--only-roots", "--agents", str(agents), "--fail-on-blocker")
        self.assertEqual(code, 1)
        self.assertEqual(report["summary"]["skill_count"], 0)
        self.assertEqual(report["summary"]["agents_count"], 1)
        self.assertEqual({i["code"] for i in report["agents"][0]["issues"]}, {"missing_referenced_file"})
        self.assertIn(str(guide.resolve()), report["agents"][0]["reference_scan"]["visited_files"])
        code, report = self.run_cli("--only-roots", "--agents", str(self.root / "absent.md"))
        self.assertEqual(code, 2)
        self.assertEqual(report["scope"]["missing"][0]["reason"], "required-agents-missing")

    def test_markdown_report_records_scope(self):
        markdown = self.root / "report.md"
        code, report = self.run_cli("--only-roots", "--optional-root", f"optional={self.root / 'absent'}", "--markdown-out", str(markdown))
        self.assertEqual(code, 0)
        text = markdown.read_text(encoding="utf-8")
        self.assertIn("optional-missing", text)
        self.assertIn("Other nested layouts are not searched", text)

    def test_public_explicit_inputs_never_read_profile_or_defaults(self):
        self.issues(self.base)
        agents = self.document("AGENTS.md", "Keep user work.\n", base=self.root)
        variants = [("--root", f"chosen={self.root}"),
                    ("--optional-root", f"chosen={self.root}"),
                    ("--agents", str(agents))]
        for args in variants:
            with self.subTest(args=args), \
                 patch.object(sys, "argv", ["audit", *args]), \
                 patch.object(audit, "profile_authority_errors", side_effect=AssertionError("profile read")), \
                 patch.object(audit, "default_roots", side_effect=AssertionError("default scan")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 0)

    def test_bad_reference_limit_is_rejected(self):
        with self.assertRaises(SystemExit):
            self.run_cli("--max-reference-files", "0")


if __name__ == "__main__":
    unittest.main()
