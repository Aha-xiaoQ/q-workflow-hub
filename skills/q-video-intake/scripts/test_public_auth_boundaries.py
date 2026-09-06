"""Offline public-route privacy and failure classification regressions."""
import argparse
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("intake_under_test", Path(__file__).with_name("q_video_intake.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PublicAuthBoundaries(unittest.TestCase):
    def classify(self, probe=None, browser="none", cookie=None, stderr=""):
        return module.subtitle_failure_status(
            "https://www.bilibili.com/video/BV1example/?p=2",
            argparse.Namespace(cookies_file=cookie, cookies_browser=browser),
            {"bilibili_direct_probe": probe, "stderr_tail": stderr},
        )

    def test_multipart_login_rejection_precedes_empty_subtitles(self):
        probe = {"status": "no_subtitle_for_requested_page", "auth": "cookies_file",
                 "cookies_file_loaded": True, "player_api_data": {"need_login_subtitle": True}}
        self.assertEqual(self.classify(probe, cookie="fixture-only.txt"), "auth_route_expired_or_rejected")

    def test_browser_login_rejection_without_direct_probe(self):
        self.assertEqual(self.classify(browser="edge", stderr="Subtitles are only available when logged in"),
                         "auth_route_expired_or_rejected")

    def test_anonymous_login_not_missing_captions(self):
        self.assertEqual(self.classify(stderr="Subtitles are only available when logged in"), "auth_route_unavailable")

    def test_unreadable_cookie_precedes_empty_subtitles(self):
        self.assertEqual(self.classify({"status": "no_subtitle_for_requested_page", "cookies_file_loaded": False}),
                         "auth_route_unreadable")

    def test_empty_subtitles_without_reported_auth_failure(self):
        self.assertEqual(self.classify({"status": "no_subtitle_for_requested_page"}), "no_subtitle_for_requested_page")

    def test_invalid_page_keeps_specific_error(self):
        self.assertEqual(self.classify({"status": "invalid_requested_page"}), "invalid_requested_page")

    def test_explicit_missing_registry_never_reads_default(self):
        with tempfile.TemporaryDirectory() as folder:
            registry = Path(folder) / "missing.json"
            with patch.dict(os.environ, {module.Q_VIDEO_AUTH_ROUTES_ENV: str(registry)}):
                self.assertEqual(module.q_video_auth_route_paths(), [registry])
                self.assertEqual(module.load_auth_routes(), ([], registry))

    def test_opt_out_never_looks_up_saved_route(self):
        args = argparse.Namespace(input="https://www.bilibili.com/video/BV1example", cookies_file=None, cookies_browser="none", no_saved_auth_route=True)
        with patch.object(module, "choose_auth_route", side_effect=AssertionError("lookup forbidden")):
            self.assertEqual(module.apply_known_bilibili_auth_route(args)["source"], "saved_route_disabled")

    def test_relative_file_is_recorded_as_absolute(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            cookie = Path(folder) / "fixture-cookies.txt"
            cookie.touch()
            relative = os.path.relpath(cookie, Path.cwd())
            registry = Path(folder) / "registry.json"
            with patch.dict(os.environ, {module.Q_VIDEO_AUTH_ROUTES_ENV: str(registry)}):
                module.remember_auth_route("bilibili", cookies_file=relative)
                routes, _ = module.load_auth_routes()
                self.assertEqual(routes[0]["cookies_file"], str(cookie.resolve()))

    def test_legacy_relative_route_is_not_reused_from_another_directory(self):
        routes = [{"provider": "bilibili", "cookies_file": "cookies.txt", "status": "validated"}]
        with patch.object(module, "load_auth_routes", return_value=(routes, Path("unused"))):
            self.assertIsNone(module.choose_auth_route("bilibili"))

    def test_explicit_cookie_overrides_opt_out(self):
        args = argparse.Namespace(input="https://www.bilibili.com/video/BV1example", cookies_file="fixture-only.txt", cookies_browser="none", no_saved_auth_route=True)
        self.assertEqual(module.apply_known_bilibili_auth_route(args)["source"], "explicit_cookies_file")


if __name__ == "__main__":
    unittest.main()
