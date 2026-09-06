#!/usr/bin/env python3
"""Regression checks for deterministic Bilibili multipart page selection."""

from __future__ import annotations

import importlib.util
import argparse
import json
import tempfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("q_video_intake.py")
SPEC = importlib.util.spec_from_file_location("q_video_intake", SCRIPT_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Could not load q_video_intake.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def probe_args() -> argparse.Namespace:
    return argparse.Namespace(
        cookies_file=None,
        cookies_browser="none",
        subtitle_timeout=30,
        ffmpeg_location=None,
    )


def direct_probe_regression() -> None:
    """An explicit P4 request must never consume P1 HTML subtitles."""
    original_fetch = MODULE.fetch_text_url
    original_state = MODULE.extract_initial_state
    original_items = MODULE.subtitle_items_from_video_data
    original_run = MODULE.run_cmd
    try:
        page_one_html_data = {
            "aid": 1,
            "pages": [{"cid": 101}],
            "subtitle_items": [{"lan": "p1", "subtitle_url": "https://example.test/p1.json"}],
        }
        view_data = {"data": {"aid": 1, "cid": 101, "pages": [
            {"page": 1, "cid": 101, "part": "P1"},
            {"page": 4, "cid": 404, "part": "P4"},
        ]}}

        def fake_fetch(url: str, **_kwargs):
            if "x/web-interface/view" in url:
                return 200, json.dumps(view_data)
            if "x/player/wbi/v2" in url:
                assert "cid=404" in url
                return 200, json.dumps({"data": {"subtitle_items": []}})
            if url == "https://example.test/p1.json":
                raise AssertionError("explicit P4 probe attempted to download P1 subtitle")
            return 200, "<html></html>"

        MODULE.fetch_text_url = fake_fetch
        MODULE.extract_initial_state = lambda _html: {"videoData": page_one_html_data}
        MODULE.subtitle_items_from_video_data = lambda data: list(data.get("subtitle_items", []))
        with tempfile.TemporaryDirectory() as directory:
            transcript, debug = MODULE.direct_bilibili_subtitle_probe(
                "https://www.bilibili.com/video/BV1example/?p=4", Path(directory), probe_args(),
            )
        assert transcript is None
        assert debug["status"] == "no_subtitle_for_requested_page"
        assert debug["selected_page"]["cid"] == 404

        # fetch_subtitles is the outer fallback layer. It must terminate on the
        # direct probe's definitive explicit-page result rather than invoking
        # yt-dlp, which would otherwise choose P1 for some malformed URLs.
        MODULE.run_cmd = lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("yt-dlp fallback ran"))
        with tempfile.TemporaryDirectory() as directory:
            transcript, debug = MODULE.fetch_subtitles(
                "https://www.bilibili.com/video/BV1example/?p=4", Path(directory), probe_args(),
            )
        assert transcript is None
        assert debug["status"] == "no_subtitle_for_requested_page"
    finally:
        MODULE.fetch_text_url = original_fetch
        MODULE.extract_initial_state = original_state
        MODULE.subtitle_items_from_video_data = original_items
        MODULE.run_cmd = original_run


def browser_route_regression() -> None:
    """Browser routes must lock yt-dlp to the requested multipart item."""
    original_direct = MODULE.direct_bilibili_subtitle_probe
    original_run = MODULE.run_cmd
    try:
        MODULE.direct_bilibili_subtitle_probe = lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("browser route must not perform an anonymous direct probe")
        )

        def fake_run(command, **_kwargs):
            assert "--yes-playlist" in command
            assert "--playlist-items" in command
            assert command[command.index("--playlist-items") + 1] == "4"
            assert "--no-playlist" not in command
            return MODULE.subprocess.CompletedProcess(command, 1, "", "no subtitles for selected item")

        MODULE.run_cmd = fake_run
        browser_args = probe_args()
        browser_args.cookies_browser = "edge"
        browser_args.sub_langs = "ai-zh"
        with tempfile.TemporaryDirectory() as directory:
            transcript, debug = MODULE.fetch_subtitles(
                "https://www.bilibili.com/video/BV1example/?p=4", Path(directory), browser_args,
            )
        assert transcript is None
        assert debug["attempts"]
    finally:
        MODULE.direct_bilibili_subtitle_probe = original_direct
        MODULE.run_cmd = original_run


def main() -> int:
    assert MODULE.bilibili_page_number("https://www.bilibili.com/video/BV1abc/?p=4") == 4
    assert MODULE.bilibili_page_number("https://www.bilibili.com/video/BV1abc/?p=0") is None
    assert MODULE.bilibili_page_number("BV1abc") is None
    assert MODULE.bilibili_page_number("https://www.bilibili.com/video/BV1abc/?p=nope") is None
    assert MODULE.bilibili_page_request("https://www.bilibili.com/video/BV1abc/?p=0") == (None, "invalid_requested_page")
    assert MODULE.bilibili_page_request("https://www.bilibili.com/video/BV1abc/?p=nope") == (None, "invalid_requested_page")
    assert MODULE.subtitle_failure_status(
        "https://www.bilibili.com/video/BV1abc/?p=0",
        probe_args(),
        {"bilibili_direct_probe": {"status": "invalid_requested_page"}},
    ) == "invalid_requested_page"

    view = {"pages": [
        {"page": 1, "cid": 101, "part": "intro", "duration": 10},
        {"page": 4, "cid": 404, "part": "outline", "duration": 20},
    ]}
    selected, error = MODULE.select_bilibili_page(view, 4)
    assert error is None
    assert selected and selected["cid"] == 404
    missing, missing_error = MODULE.select_bilibili_page(view, 3)
    assert missing is None
    assert missing_error == "requested_page_not_found"
    default, default_error = MODULE.select_bilibili_page(view, None)
    assert default is None
    assert default_error is None
    direct_probe_regression()
    browser_route_regression()
    print("PASS: URL page parsing and multipart cid selection are deterministic")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
