"""Regression checks for child-host isolation and real rollback evidence."""
import os
import subprocess
import unittest
from unittest.mock import patch

import workflow_stability_suite as suite


class InstallerEnvironmentTests(unittest.TestCase):
    def test_windows_child_only_isolation(self):
        original = {"PsModulePath": "foreign-modules", "PATH": "keep", "CUSTOM": "keep"}
        with patch.dict(os.environ, original, clear=True), patch.object(suite.os, "name", "nt"):
            before = dict(os.environ)
            child = suite.windows_powershell_test_env()
            self.assertFalse(any(key.casefold() == "psmodulepath" for key in child))
            self.assertEqual(child["PATH"], "keep")
            self.assertEqual(child["CUSTOM"], "keep")
            self.assertEqual(dict(os.environ), before)

    def test_other_hosts_preserve_environment(self):
        with patch.dict(os.environ, {"PSModulePath": "keep"}, clear=True), patch.object(suite.os, "name", "posix"):
            self.assertEqual(suite.windows_powershell_test_env(), dict(os.environ))

    def test_only_intended_failure_qualifies(self):
        marker = "Injected transaction failure."
        for code, stdout, stderr, expected in (
            (1, marker, "", True), (1, "", marker, True),
            (1, "", "Get-FileHash unavailable", False),
            (0, marker, "", False), (1, None, None, False),
        ):
            with self.subTest(code=code, stdout=stdout, stderr=stderr):
                result = subprocess.CompletedProcess([], code, stdout, stderr)
                self.assertEqual(suite.injected_failure_reached(result, marker), expected)


if __name__ == "__main__":
    unittest.main()
