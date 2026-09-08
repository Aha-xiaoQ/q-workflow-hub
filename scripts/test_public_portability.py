"""Regression checks for portable public validation and conservative defaults."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/q-workflow/scripts"))
from workflow_audit import missing_profile_references


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class PublicPortabilityTests(unittest.TestCase):
    def test_quickstarts_do_not_reinstall_withdrawn_tag(self):
        for name in ('QUICKSTART.md', 'QUICKSTART.zh-CN.md'):
            with self.subTest(guide=name):
                guide = (ROOT / name).read_text(encoding='utf-8')
                self.assertIn('git clone --branch main --depth 1', guide)
                self.assertNotIn('git clone --branch v1.1-beta', guide)
                self.assertNotIn('git switch --detach v1.1-beta', guide)
                self.assertIn('git rev-parse HEAD', guide)

    def test_default_policy_has_no_implicit_waivers(self):
        policy = json.loads((ROOT / "docs/governance/VARIANT_MAP.json").read_text())
        for side in ("public", "company"):
            self.assertEqual(policy["canonical_mappings"][side], {})
        for key in ("public_only_prefixes", "company_only_prefixes", "changed_text_review_prefixes"):
            self.assertEqual(policy[key], [])

    def test_parity_report_roundtrip_and_collision(self):
        policy = json.loads((ROOT / "docs/governance/VARIANT_MAP.json").read_text())
        for index, prefix in enumerate(("scripts", "skills/q-workflow/scripts")):
            with self.subTest(copy=prefix), tempfile.TemporaryDirectory() as tmp:
                audit = load(f"parity_audit_{index}", ROOT / prefix / "audit-variant-parity.py")
                classify = load(f"parity_classify_{index}", ROOT / prefix / "classify-variant-parity.py")
                self.assertEqual(audit.validate_policy(policy), [])
                folder = Path(tmp)
                public, company = folder / "public", folder / "company"
                public.mkdir(); company.mkdir()
                (public / "public-only.md").write_text("public")
                (company / "private-only.md").write_text("private")
                (public / "common.md").write_text("before")
                (company / "common.md").write_text("after")
                report = folder / "report.md"
                report.write_text(audit.build_report(public, company, policy, None), encoding="utf-8")
                rows = classify.parse_audit(report)
                self.assertEqual(rows["missing_in_company"], ["public-only.md"])
                self.assertEqual(rows["missing_in_public"], ["private-only.md"])
                self.assertEqual(rows["changed_text"], ["common.md <-> common.md"])
                self.assertEqual(classify.classify_missing_in_public("private-only.md", policy).decision, "review")
                collision_policy = {"canonical_mappings": {"public": {"public-only.md": "common.md"}, "company": {}}}
                report.write_text(audit.build_report(public, company, collision_policy, None), encoding="utf-8")
                self.assertEqual(len(classify.parse_audit(report)["mapping_collisions"]), 1)

    def test_missing_reference_and_installed_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = "Use q-example `references/recovery.md` to resume."
            self.assertEqual(missing_profile_references(text, [root]), ["q-example/references/recovery.md"])
            target = root / "q-example/references/recovery.md"
            target.parent.mkdir(parents=True); target.write_text("Recovery steps")
            self.assertEqual(missing_profile_references(text, [root]), [])

    def test_reference_cannot_escape_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "outside.md").write_text("outside")
            text = "q-example `references/../../outside.md`"
            self.assertTrue(missing_profile_references(text, [root]))

    def test_generic_private_field_rejection(self):
        intake = load("public_intake", ROOT / "skills/q-ppt-creation/scripts/validate_intake_request.py")
        for key in ("company", "organization", "vendor", "internal", "confidential", "template_path"):
            with self.subTest(key=key):
                errors = []
                intake.validate_private_field_leaks({"nested": {key: "example"}}, "request", errors)
                self.assertTrue(errors)

    def test_unvalidated_skills_are_not_distributed_or_registered(self):
        registry = json.loads((ROOT / "skills/q-workflow/references/surface-registry.json").read_text(encoding="utf-8"))
        registered = {item["id"] for item in registry["skills"]}
        for name in ("q-pixel-art-creation", "q-game-canvas-iteration", "q-html-interface-design", "q-font-design", "q-game-production", "q-arduino-ach-release", "q-public-content-review"):
            with self.subTest(skill=name):
                self.assertFalse((ROOT / "skills" / name).exists())
                self.assertNotIn(name, registered)


if __name__ == "__main__":
    unittest.main()
