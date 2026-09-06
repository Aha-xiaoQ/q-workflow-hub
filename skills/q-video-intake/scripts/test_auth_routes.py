#!/usr/bin/env python3
"""Focused regression checks for q-video-intake's Bilibili auth-route recovery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("q_video_intake.py")
SPEC = importlib.util.spec_from_file_location("q_video_intake", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load q_video_intake.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def args(*, cookies_file: str | None = None, cookies_browser: str = "none") -> argparse.Namespace:
    return argparse.Namespace(
        input="https://www.bilibili.com/video/BV1example",
        cookies_file=cookies_file,
        cookies_browser=cookies_browser,
        output_dir=None,
        engine="none",
        no_subtitles=False,
        no_analysis_pack=True,
        sub_langs=MODULE.DEFAULT_SUB_LANGS,
        subtitle_timeout=30,
        ffmpeg_location=None,
    )


def main() -> int:
    previous = os.environ.get(MODULE.Q_VIDEO_AUTH_ROUTES_ENV)
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cookie = root / "validated-cookies.txt"
            cookie.write_text("# Netscape HTTP Cookie File\nCOOKIE_CONTENT_SENTINEL\n", encoding="utf-8")
            registry = root / "auth-routes.json"
            registry.write_text(json.dumps({
                "version": 1,
                "routes": [{
                    "id": "bilibili-regression",
                    "provider": "bilibili",
                    "cookies_file": str(cookie),
                    "status": "validated",
                    "last_success_at": "2026-07-15T00:00:00",
                }],
            }), encoding="utf-8")
            os.environ[MODULE.Q_VIDEO_AUTH_ROUTES_ENV] = str(registry)

            automatic = args()
            selected = MODULE.apply_known_bilibili_auth_route(automatic)
            assert selected["source"] == "validated_local_route"
            assert automatic.cookies_file == str(cookie)

            explicit_cookie = root / "explicit-cookies.txt"
            explicit_cookie.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
            explicit = args(cookies_file=str(explicit_cookie))
            selected_explicit = MODULE.apply_known_bilibili_auth_route(explicit)
            assert selected_explicit["source"] == "explicit_cookies_file"
            assert explicit.cookies_file == str(explicit_cookie)

            registry.write_text(json.dumps({
                "version": 1,
                "routes": [{
                    "id": "edge-regression",
                    "provider": "bilibili",
                    "kind": "cookies_browser",
                    "browser": "edge",
                    "status": "validated",
                    "last_success_at": "2026-07-15T00:01:00",
                }],
            }), encoding="utf-8")
            browser_route = args()
            selected_browser = MODULE.apply_known_bilibili_auth_route(browser_route)
            assert selected_browser == {
                "source": "validated_local_route",
                "route_id": "edge-regression",
                "kind": "cookies_browser",
                "browser": "edge",
            }
            assert browser_route.cookies_browser == "edge"

            cookie.unlink()
            registry.write_text(json.dumps({"version": 1, "routes": []}), encoding="utf-8")
            unavailable = args()
            selected_unavailable = MODULE.apply_known_bilibili_auth_route(unavailable)
            assert selected_unavailable["source"] == "no_validated_route"

            for browser_name in ("chrome", "edge", "firefox"):
                locked = MODULE.subtitle_failure_status(
                    automatic.input,
                    args(cookies_browser=browser_name),
                    {"stderr_tail": f"ERROR: Could not copy {browser_name.title()} cookie database"},
                )
                assert locked == "browser_cookie_locked"

            unavailable_status = MODULE.subtitle_failure_status(
                automatic.input,
                args(),
                {"bilibili_direct_probe": {"player_api_data": {"need_login_subtitle": True}}},
            )
            assert unavailable_status == "auth_route_unavailable"

            cookie.write_text("# Netscape HTTP Cookie File\n", encoding="utf-8")
            original_fetch = MODULE.fetch_subtitles
            MODULE.fetch_subtitles = lambda *_args, **_kwargs: ("字幕验证", {"returncode": 0})
            try:
                first_run = args(cookies_file=str(cookie))
                first_run.output_dir = str(root / "first-run")
                assert MODULE.intake(first_run) == 0
                automatic_run = args()
                automatic_run.output_dir = str(root / "automatic-run")
                assert MODULE.intake(automatic_run) == 0
                metadata = json.loads((root / "automatic-run" / "metadata.json").read_text(encoding="utf-8"))
                assert metadata["auth_route"]["source"] == "validated_local_route"
                assert metadata["status"] == "transcript_from_subtitles"

                registry.write_text(json.dumps({"version": 1, "routes": []}), encoding="utf-8")
                browser_first = args(cookies_browser="edge")
                browser_first.output_dir = str(root / "browser-first-run")
                assert MODULE.intake(browser_first) == 0
                browser_auto = args()
                browser_auto.output_dir = str(root / "browser-automatic-run")
                assert MODULE.intake(browser_auto) == 0
                browser_metadata = json.loads((root / "browser-automatic-run" / "metadata.json").read_text(encoding="utf-8"))
                assert browser_metadata["auth_route"]["kind"] == "cookies_browser"
                assert browser_metadata["auth_route"]["browser"] == "edge"
                assert "COOKIE_CONTENT_SENTINEL" not in registry.read_text(encoding="utf-8")

                MODULE.remember_auth_route("bilibili", cookies_file=str(cookie))
                routes, _ = MODULE.load_auth_routes()
                browser_saved = next(route for route in routes if route.get("kind") == "cookies_browser")
                file_saved = next(route for route in routes if route.get("kind") == "cookies_file")
                assert browser_saved["id"] != file_saved["id"]
                preferred = args()
                preferred_route = MODULE.apply_known_bilibili_auth_route(preferred)
                assert preferred_route["kind"] == "cookies_file"
                assert preferred.cookies_file == str(cookie)
                MODULE.mark_auth_route_rejected("bilibili", str(browser_saved["id"]))
                routes_after_reject, _ = MODULE.load_auth_routes()
                assert next(route for route in routes_after_reject if route.get("id") == browser_saved["id"])["status"] == "rejected"
                assert next(route for route in routes_after_reject if route.get("id") == file_saved["id"])["status"] == "validated"
            finally:
                MODULE.fetch_subtitles = original_fetch

            original_direct = MODULE.direct_bilibili_subtitle_probe
            original_run = MODULE.run_cmd
            try:
                MODULE.direct_bilibili_subtitle_probe = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("anonymous probe ran"))

                def fake_run(command, **_kwargs):
                    output = Path(command[command.index("-o") + 1].replace("%(ext)s", "ai-zh.srt"))
                    output.write_text("1\n00:00:00,000 --> 00:00:01,000\n验证\n", encoding="utf-8")
                    return subprocess.CompletedProcess(command, 0, "", "")

                MODULE.run_cmd = fake_run
                transcript, _debug = MODULE.fetch_subtitles(
                    automatic.input,
                    root / "browser-probe-skip",
                    args(cookies_browser="edge"),
                )
                assert transcript == "验证"
            finally:
                MODULE.direct_bilibili_subtitle_probe = original_direct
                MODULE.run_cmd = original_run
    finally:
        if previous is None:
            os.environ.pop(MODULE.Q_VIDEO_AUTH_ROUTES_ENV, None)
        else:
            os.environ[MODULE.Q_VIDEO_AUTH_ROUTES_ENV] = previous

    print("PASS: file/browser route persistence, unique rejection, browser-lock classification, and probe-free auto-reuse")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
