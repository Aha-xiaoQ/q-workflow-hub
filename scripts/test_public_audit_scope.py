"""Explicit audit roots must not traverse the caller's profile roots."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'skills/q-skill-creation/scripts/skill_portfolio_audit.py'
spec = importlib.util.spec_from_file_location('portfolio_scope', SCRIPT)
audit = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = audit
spec.loader.exec_module(audit)


class ExplicitScopeTests(unittest.TestCase):
    def test_explicit_root_overrides_valid_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / 'audit.json'
            with patch.object(sys, 'argv', [str(SCRIPT), '--root', f'fixture={root}', '--json-out', str(output)]), \
                 patch.object(audit, 'profile_authority_errors', side_effect=AssertionError('personal profile accessed')), \
                 patch.object(audit, 'default_roots', side_effect=AssertionError('personal roots accessed')), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 0)
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(list(result['roots']), ['fixture'])
            self.assertEqual(result['authority']['mode'], 'explicit-roots')
            self.assertIsNone(result['authority']['profile'])


if __name__ == '__main__':
    unittest.main()
