#!/usr/bin/env python3
"""q-video-intake: subtitle-first video/audio intake for coding agents."""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_SUB_LANGS = "zh-Hans,zh,zh-Hant,ai-zh,ai-en,en"
DEFAULT_OUTPUT_ROOT = Path("local-state") / "q-video-intake"
DEFAULT_CHUNK_CHARS = 6000
FFMPEG_ENV_VARS = ("Q_VIDEO_INTAKE_FFMPEG", "FFMPEG_LOCATION", "IMAGEIO_FFMPEG_EXE")
Q_VIDEO_CONFIG_DIR_NAME = "q-video-intake"
Q_VIDEO_AUTH_ROUTES_ENV = "Q_VIDEO_INTAKE_AUTH_ROUTES"
VISUAL_PACK_PRESETS = {
    "manual": {"interval": 10.0, "max_frames": 24, "width": 960},
    "economy": {"base_interval": 60.0, "min_frames": 5, "max_frames": 12, "width": 640},
    "balanced": {"base_interval": 30.0, "min_frames": 8, "max_frames": 18, "width": 800},
    "deep": {"base_interval": 12.0, "min_frames": 24, "max_frames": 72, "width": 480},
}
VISUAL_ANALYZE_PRESETS = {
    "manual": {"max_frames": 8, "max_output_tokens": 1800, "image_detail": "auto"},
    "economy": {"max_frames": 8, "max_output_tokens": 1000, "image_detail": "low"},
    "balanced": {"max_frames": 14, "max_output_tokens": 1800, "image_detail": "low"},
}
VISUAL_KIND_INTERVAL_MULTIPLIERS = {
    "general": 1.0,
    "talking-head": 1.2,
    "slides": 0.8,
    "ui-demo": 0.55,
    "fast-action": 0.4,
}
SMART_THUMB_WIDTH = 16
SMART_THUMB_HEIGHT = 16
SMART_THUMB_CHANNELS = 3
DEFAULT_SUBTITLE_HINT_KEYWORDS = (
    "首先,然后,最后,总结,结论,注意,重点,问题,步骤,演示,打开,点击,选择,输入,"
    "first,next,finally,summary,conclusion,important,step,demo,click,open,select,type"
)
SMART_SELECTION_POLICIES = {
    "balanced": {
        "budget_frames": 24,
        "baseline_seconds": 45.0,
        "min_gap_seconds": 2.0,
        "event_neighbor_frames": 0,
        "coverage_fraction": 0.6,
    },
    "summary": {
        "budget_frames": 12,
        "baseline_seconds": 90.0,
        "min_gap_seconds": 4.0,
        "event_neighbor_frames": 0,
        "coverage_fraction": 0.8,
    },
    "lecture": {
        "budget_frames": 24,
        "baseline_seconds": 45.0,
        "min_gap_seconds": 2.0,
        "event_neighbor_frames": 0,
        "coverage_fraction": 0.8,
    },
    "ui": {
        "budget_frames": 32,
        "baseline_seconds": 20.0,
        "min_gap_seconds": 2.0,
        "event_neighbor_frames": 1,
        "coverage_fraction": 0.35,
    },
    "style": {
        "budget_frames": 36,
        "baseline_seconds": 15.0,
        "min_gap_seconds": 1.5,
        "event_neighbor_frames": 1,
        "coverage_fraction": 0.8,
    },
    "deep": {
        "budget_frames": 72,
        "baseline_seconds": 10.0,
        "min_gap_seconds": 0.5,
        "event_neighbor_frames": 1,
        "coverage_fraction": 0.45,
    },
}
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "www."))


def is_azure_v1_base_url(value: str) -> bool:
    return "/openai/v1" in value.lower()


def normalize_azure_v1_base_url(value: str) -> str:
    """Accept a v1 base URL or full /responses URL and return SDK base_url."""
    cleaned = value.strip().split("?", 1)[0].rstrip("/")
    lowered = cleaned.lower()
    for suffix in ("/responses", "/chat/completions"):
        if lowered.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            lowered = cleaned.lower()
            break
    marker = "/openai/v1"
    marker_index = lowered.find(marker)
    if marker_index >= 0:
        cleaned = cleaned[: marker_index + len(marker)]
    elif lowered.endswith("/openai"):
        cleaned = cleaned + "/v1"
    return cleaned.rstrip("/") + "/"


def describe_azure_openai_mode() -> dict[str, str] | None:
    base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    if base_url:
        return {"azure_mode": "v1_base_url", "azure_url_source": "AZURE_OPENAI_BASE_URL"}
    if endpoint and is_azure_v1_base_url(endpoint):
        return {"azure_mode": "v1_base_url", "azure_url_source": "AZURE_OPENAI_ENDPOINT"}
    if endpoint:
        return {"azure_mode": "legacy_endpoint", "azure_url_source": "AZURE_OPENAI_ENDPOINT"}
    return None


def is_bilibili(value: str) -> bool:
    return "bilibili.com" in value or "b23.tv" in value


def extract_bvid(value: str) -> str | None:
    match = re.search(r"(BV[0-9A-Za-z]+)", value)
    return match.group(1) if match else None


def bilibili_page_request(value: str) -> tuple[int | None, str | None]:
    """Parse an explicit multipart page request without downgrading invalid input."""
    if not is_url(value):
        return None, None
    query = urllib.parse.parse_qs(urllib.parse.urlparse(value).query, keep_blank_values=True)
    if "p" not in query:
        return None, None
    raw_page = query.get("p", [None])[0]
    if raw_page is None:
        return None, "invalid_requested_page"
    try:
        page = int(raw_page)
    except (TypeError, ValueError):
        return None, "invalid_requested_page"
    return (page, None) if page > 0 else (None, "invalid_requested_page")


def bilibili_page_number(value: str) -> int | None:
    """Compatibility helper returning a valid explicit multipart page or None."""
    page, _error = bilibili_page_request(value)
    return page


def select_bilibili_page(view: dict[str, Any], page_number: int | None) -> tuple[dict[str, Any] | None, str | None]:
    """Select one multipart page from view API data without silently falling back."""
    if page_number is None:
        return None, None
    pages = view.get("pages") if isinstance(view.get("pages"), list) else []
    for item in pages:
        if isinstance(item, dict) and item.get("page") == page_number:
            return item, None
    return None, "requested_page_not_found"


def bilibili_headers(*, referer: str | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": DEFAULT_UA,
        "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    headers["Referer"] = referer or "https://www.bilibili.com/"
    return headers


def netscape_cookie_header(path: Path, *, domains: tuple[str, ...]) -> tuple[str, int]:
    cookie_jar = http.cookiejar.MozillaCookieJar(str(path))
    cookie_jar.load(ignore_discard=True, ignore_expires=True)
    pairs: list[str] = []
    for cookie in cookie_jar:
        cookie_domain = str(cookie.domain or "").lstrip(".").lower()
        if not cookie_domain:
            continue
        if not any(cookie_domain == domain or cookie_domain.endswith("." + domain) for domain in domains):
            continue
        if cookie.value is None:
            continue
        pairs.append(f"{cookie.name}={cookie.value}")
    return "; ".join(pairs), len(pairs)


def fetch_text_url(url: str, *, headers: dict[str, str], timeout: int = 30) -> tuple[int, str]:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            encoding = response.headers.get_content_charset() or "utf-8"
            return int(response.status), response.read().decode(encoding, errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return int(exc.code), body


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def sanitize_error_text(text: str) -> str:
    sanitized = text
    for name in (
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_BASE_URL",
    ):
        value = os.environ.get(name)
        if value and len(value) >= 6:
            sanitized = sanitized.replace(value, f"<{name}>")
            sanitized = sanitized.replace(value.rstrip("/"), f"<{name}>")
    return sanitized


def parse_ffmpeg_duration(output: str) -> float | None:
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", output)
    if not match:
        return None
    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = float(match.group(3))
    return hours * 3600 + minutes * 60 + seconds


def probe_video_duration(ffmpeg_command: str, source: Path, timeout: int = 30) -> float | None:
    try:
        result = run_cmd([ffmpeg_command, "-i", str(source)], timeout=timeout)
    except Exception:
        return None
    return parse_ffmpeg_duration(result.stdout + "\n" + result.stderr)


def choose_visual_frame_count(
    *,
    duration: float | None,
    base_interval: float,
    min_frames: int,
    max_frames: int,
) -> int:
    if duration is None or duration <= 0:
        return max_frames
    estimated = int((duration + base_interval - 0.001) // base_interval) + 1
    return max(min_frames, min(max_frames, estimated))


def visual_pack_settings(
    args: argparse.Namespace,
    *,
    source_duration: float | None = None,
) -> dict[str, Any]:
    preset = VISUAL_PACK_PRESETS[args.visual_preset]
    width = args.width if args.width is not None else preset["width"]
    if args.visual_preset == "manual":
        return {
            "preset": args.visual_preset,
            "visual_kind": args.visual_kind,
            "source_duration": source_duration,
            "sample_duration": args.duration,
            "interval": args.interval if args.interval is not None else preset["interval"],
            "max_frames": args.max_frames if args.max_frames is not None else preset["max_frames"],
            "width": width,
        }

    start = float(args.start or 0)
    sample_duration = args.duration
    if sample_duration is None and source_duration is not None:
        sample_duration = max(0.0, source_duration - start)
    multiplier = VISUAL_KIND_INTERVAL_MULTIPLIERS[args.visual_kind]
    base_interval = float(preset["base_interval"]) * multiplier
    max_frames = int(args.max_frames) if args.max_frames is not None else choose_visual_frame_count(
        duration=sample_duration,
        base_interval=base_interval,
        min_frames=int(preset["min_frames"]),
        max_frames=int(preset["max_frames"]),
    )
    if args.interval is not None:
        interval = args.interval
    elif sample_duration is not None and sample_duration > 0:
        interval = max(1.0, sample_duration / max_frames)
    else:
        interval = base_interval
    return {
        "preset": args.visual_preset,
        "visual_kind": args.visual_kind,
        "source_duration": source_duration,
        "sample_duration": sample_duration,
        "interval": interval,
        "max_frames": max_frames,
        "width": width,
    }


def visual_analyze_settings(args: argparse.Namespace) -> dict[str, Any]:
    preset = VISUAL_ANALYZE_PRESETS[args.visual_preset]
    return {
        "preset": args.visual_preset,
        "max_frames": args.max_frames if args.max_frames is not None else preset["max_frames"],
        "max_output_tokens": (
            args.max_output_tokens
            if args.max_output_tokens is not None
            else preset["max_output_tokens"]
        ),
        "image_detail": args.image_detail if args.image_detail is not None else preset["image_detail"],
    }


def default_output_dir() -> Path:
    return DEFAULT_OUTPUT_ROOT / now_stamp()


def run_cmd(
    cmd: list[str],
    *,
    timeout: int,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env["PYTHONIOENCODING"] = "utf-8"
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def module_available(module_name: str) -> bool:
    result = run_cmd(
        [sys.executable, "-c", f"import {module_name}"],
        timeout=20,
    )
    return result.returncode == 0


def command_available(command: str) -> bool:
    return resolve_command(command) is not None


def resolve_command(command: str) -> str | None:
    found = shutil.which(command)
    if found:
        return found
    if os.name != "nt":
        return None

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Command {command} -ErrorAction SilentlyContinue).Source",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except Exception:
        return None
    candidate = result.stdout.strip()
    if result.returncode == 0 and candidate:
        return candidate
    return None


def q_video_config_paths() -> list[Path]:
    paths: list[Path] = []
    configured = os.environ.get("Q_VIDEO_INTAKE_CONFIG")
    if configured:
        paths.append(Path(configured).expanduser())
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        paths.append(Path(local_app_data) / Q_VIDEO_CONFIG_DIR_NAME / "config.json")
    paths.append(Path.home() / f".{Q_VIDEO_CONFIG_DIR_NAME}" / "config.json")
    return paths


def q_video_auth_route_paths() -> list[Path]:
    """Return private, machine-local route registries; never store cookie values here."""
    paths: list[Path] = []
    configured = os.environ.get(Q_VIDEO_AUTH_ROUTES_ENV)
    if configured:
        # An explicit registry is an isolation boundary, not a search hint.
        return [Path(configured).expanduser()]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        paths.append(Path(local_app_data) / Q_VIDEO_CONFIG_DIR_NAME / "auth-routes.json")
    paths.append(Path.home() / f".{Q_VIDEO_CONFIG_DIR_NAME}" / "auth-routes.json")
    return paths


def load_auth_routes() -> tuple[list[dict[str, Any]], Path]:
    """Load route metadata only. Cookie files remain private local inputs."""
    paths = q_video_auth_route_paths()
    for path in paths:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        routes = data.get("routes", []) if isinstance(data, dict) else []
        if isinstance(routes, list):
            return [dict(route) for route in routes if isinstance(route, dict)], path
    return [], paths[0]


def save_auth_routes(routes: list[dict[str, Any]], path: Path) -> None:
    """Persist route pointers and health, never browser cookies or their contents."""
    write_json(path, {"version": 1, "routes": routes})


def choose_auth_route(provider: str) -> dict[str, Any] | None:
    routes, _ = load_auth_routes()
    candidates: list[dict[str, Any]] = []
    for route in routes:
        if str(route.get("provider", "")).lower() != provider.lower():
            continue
        kind = str(route.get("kind", "cookies_file"))
        if kind == "cookies_file":
            cookie_file = route.get("cookies_file")
            if not isinstance(cookie_file, str) or not cookie_file.strip():
                continue
            cookie_path = Path(cookie_file).expanduser()
            if not cookie_path.is_absolute() or not cookie_path.is_file():
                continue
        elif kind == "cookies_browser":
            if str(route.get("browser", "")) not in {"chrome", "edge", "firefox"}:
                continue
        else:
            continue
        if route.get("status", "validated") not in {"validated", "active"}:
            continue
        candidates.append(route)
    # A file route is independent of a running browser and therefore more
    # reproducible than a browser adapter. Use recency only within a kind.
    candidates.sort(
        key=lambda route: (
            1 if str(route.get("kind", "cookies_file")) == "cookies_file" else 0,
            str(route.get("last_success_at", "")),
        ),
        reverse=True,
    )
    return dict(candidates[0]) if candidates else None


def apply_known_bilibili_auth_route(args: argparse.Namespace) -> dict[str, str]:
    """Use an explicit route first, otherwise reuse the last proven local route."""
    if not is_bilibili(args.input):
        return {"source": "not_applicable"}
    if args.cookies_file:
        return {"source": "explicit_cookies_file"}
    if args.cookies_browser != "none":
        return {"source": "explicit_browser_route", "browser": args.cookies_browser}
    if getattr(args, "no_saved_auth_route", False):
        return {"source": "saved_route_disabled"}
    route = choose_auth_route("bilibili")
    if route is None:
        return {"source": "no_validated_route"}
    selected = {
        "source": "validated_local_route",
        "route_id": str(route.get("id", "bilibili-local")),
    }
    if str(route.get("kind", "cookies_file")) == "cookies_browser":
        args.cookies_browser = str(route["browser"])
        selected["kind"] = "cookies_browser"
        selected["browser"] = args.cookies_browser
        return selected
    args.cookies_file = str(Path(str(route["cookies_file"])).expanduser())
    selected["kind"] = "cookies_file"
    return selected


def remember_auth_route(
    provider: str,
    *,
    cookies_file: str | None = None,
    cookies_browser: str = "none",
    route_id: str | None = None,
) -> None:
    """Refresh a successful local route without exposing or copying cookie data."""
    kind = "cookies_file" if cookies_file else "cookies_browser"
    if kind == "cookies_file":
        cookie_path = Path(str(cookies_file)).expanduser().resolve()
        if not cookie_path.is_file():
            return
        normalized = str(cookie_path)
    else:
        if cookies_browser not in {"chrome", "edge", "firefox"}:
            return
        normalized = cookies_browser
    routes, registry_path = load_auth_routes()
    retained = [
        route for route in routes
        if not (
            str(route.get("provider", "")).lower() == provider.lower()
            and str(route.get("kind", "cookies_file")) == kind
            and str(route.get("cookies_file" if kind == "cookies_file" else "browser", "")) == normalized
        )
    ]
    route_identity = hashlib.sha256(f"{provider}|{kind}|{normalized}".encode("utf-8")).hexdigest()[:12]
    route: dict[str, Any] = {
        "id": route_id or f"{provider}-{kind}-{route_identity}",
        "provider": provider,
        "kind": kind,
        "status": "validated",
        "last_success_at": datetime.now().isoformat(timespec="seconds"),
    }
    route["cookies_file" if kind == "cookies_file" else "browser"] = normalized
    retained.append(route)
    save_auth_routes(retained, registry_path)


def mark_auth_route_rejected(provider: str, route_id: str | None) -> None:
    """Disable only a route rejected by an authenticated subtitle response."""
    if not route_id:
        return
    routes, registry_path = load_auth_routes()
    changed = False
    for route in routes:
        if (
            str(route.get("provider", "")).lower() == provider.lower()
            and str(route.get("id", "")) == route_id
        ):
            route["status"] = "rejected"
            route["last_failure_at"] = datetime.now().isoformat(timespec="seconds")
            route["last_failure"] = "authenticated_subtitle_login_required"
            changed = True
    if changed:
        save_auth_routes(routes, registry_path)


def configured_ffmpeg_locations() -> list[str]:
    locations: list[str] = []
    for env_var in FFMPEG_ENV_VARS:
        value = os.environ.get(env_var)
        if value:
            locations.append(value)
    for config_path in q_video_config_paths():
        if not config_path.exists():
            continue
        try:
            data = json.loads(config_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        value = data.get("ffmpeg") if isinstance(data, dict) else None
        if isinstance(value, str) and value.strip():
            locations.append(value.strip())
    return locations


def resolve_ffmpeg(location: str | None = None) -> str | None:
    def usable(candidate: str) -> bool:
        try:
            result = subprocess.run(
                [candidate, "-version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
        except Exception:
            return False
        return result.returncode == 0

    if location:
        path = Path(location).expanduser()
        if path.is_dir():
            candidate = path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if candidate.exists() and usable(str(candidate)):
                return str(candidate)
        if path.exists() and usable(str(path)):
            return str(path)
    for configured_location in configured_ffmpeg_locations():
        path = Path(configured_location).expanduser()
        if path.is_dir():
            candidate = path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if candidate.exists() and usable(str(candidate)):
                return str(candidate)
        if path.exists() and usable(str(path)):
            return str(path)
    candidate = resolve_command("ffmpeg")
    if candidate and usable(candidate):
        return candidate
    return None


def ffmpeg_location_arg(location: str | None = None) -> str | None:
    ffmpeg_path = resolve_ffmpeg(location)
    if not ffmpeg_path:
        return None
    return str(Path(ffmpeg_path).parent)


def check_env(_args: argparse.Namespace) -> int:
    checks = {
        "python": {
            "ok": True,
            "detail": sys.version.split()[0],
            "fix": "",
        },
        "yt_dlp": {
            "ok": module_available("yt_dlp"),
            "detail": "python module yt_dlp",
            "fix": f"{sys.executable} -m pip install -r skills/q-video-intake/scripts/requirements.txt",
        },
        "ffmpeg": {
            "ok": resolve_ffmpeg() is not None,
            "detail": resolve_ffmpeg() or "ffmpeg command",
            "fix": "Install ffmpeg if you need audio fallback.",
        },
        "openai_key": {
            "ok": bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")),
            "detail": "OPENAI_API_KEY",
            "fix": "Set OPENAI_API_KEY, or AZURE_OPENAI_API_KEY plus AZURE_OPENAI_ENDPOINT/AZURE_OPENAI_BASE_URL for Azure OpenAI.",
        },
    }

    print("q-video-intake environment check")
    for name, data in checks.items():
        mark = "OK" if data["ok"] else "MISSING"
        print(f"- {name}: {mark} ({data['detail']})")
        if not data["ok"] and data["fix"]:
            print(f"  next: {data['fix']}")

    print("RESULT_JSON:" + json.dumps(checks, ensure_ascii=False))
    return 0


def print_diagnosis(error_text: str) -> None:
    lowered = error_text.lower()
    print("Useful next checks:")
    if "could not copy chrome cookie database" in lowered:
        print("- Browser cookies could not be copied.")
        print("- Close Chrome/Edge completely and retry, or try another browser profile.")
        print("- If that still fails, export cookies to a file and add cookie-file support.")
        return
    if "unsupported_country_region_territory" in lowered:
        print("- OpenAI API rejected the current country/region/network route.")
        print("- Try a supported network route or use --engine none to prepare local notes.")
        return
    if "invalid_api_key" in lowered or "incorrect api key" in lowered:
        print("- OpenAI API rejected the configured key.")
        print("- Replace OPENAI_API_KEY in the local environment with a valid active key.")
        print("- If using Azure OpenAI, use --openai-provider azure with AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL, plus AZURE_OPENAI_API_KEY.")
        return
    if "api_key" in lowered or "api key" in lowered:
        print("- Configure the selected engine API key locally.")
        print("- Use OPENAI_API_KEY for --engine openai.")
        print("- For Azure OpenAI, use AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL.")
        return
    if "azure_openai_endpoint" in lowered or "azure endpoint" in lowered:
        print("- Configure AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL for Azure OpenAI.")
        return
    if "ffmpeg" in lowered:
        print("- Install ffmpeg before audio fallback.")
        return
    if "cookies" in lowered or "login" in lowered:
        print("- For Bilibili subtitles, try --cookies-browser chrome or edge.")
        return
    print("- run check-env")
    print("- for Bilibili subtitles, try --cookies-browser chrome or edge")
    print("- for audio fallback, install ffmpeg and configure an API key")


def subtitle_next_options(
    subtitle_debug: dict[str, Any] | None,
    *,
    status: str | None = None,
    auth_route: dict[str, str] | None = None,
) -> list[str]:
    stderr_tail = ""
    direct_probe = None
    if subtitle_debug:
        stderr_tail = str(subtitle_debug.get("stderr_tail", ""))
        candidate_probe = subtitle_debug.get("bilibili_direct_probe")
        if isinstance(candidate_probe, dict):
            direct_probe = candidate_probe
    lowered = stderr_tail.lower()
    selected_browser = str((auth_route or {}).get("browser", "the selected browser"))
    if status == "browser_cookie_locked" or re.search(r"could not copy .*cookie database", lowered):
        return [
            f"close {selected_browser}, then retry the same validated authorization route once",
            "do not retry anonymous, alternate browsers, or manual export before the known route has been retried",
        ]
    if status == "browser_cookie_decrypt_failed" or "failed to decrypt with dpapi" in lowered:
        return [
            "the selected browser authorization route cannot be decrypted on this machine; recover a different already-validated local route",
            "do not classify this authorization failure as missing subtitles",
        ]
    if status == "auth_route_unavailable":
        return [
            "no validated automatic Bilibili authorization route is registered; establish one through the confirmed logged-in browser flow",
            "do not repeat anonymous subtitle attempts before an authorization route exists",
        ]
    if status == "auth_route_unreadable":
        return [
            "the selected local cookie file could not be loaded; verify that explicit file's format and permissions locally",
            "do not paste cookie contents into chat or classify this as missing subtitles",
        ]
    if status == "auth_route_expired_or_rejected":
        return [
            "the selected authorization route was rejected by the authenticated subtitle endpoint; recover a different known route or refresh this route once",
            "do not classify this authorization result as missing subtitles",
        ]
    if status == "invalid_requested_page":
        return [
            "use a positive integer in the Bilibili URL, for example ?p=4; this request was not allowed to fall back to P1",
        ]
    if status == "requested_page_not_found":
        return [
            "choose one of the available multipart page numbers recorded in metadata; this request was not allowed to fall back to P1",
        ]
    if status == "no_subtitle_for_requested_page":
        return [
            "the requested multipart page has no usable subtitles on the selected authenticated route; choose another chapter or use an explicit audio/visual fallback for this page",
        ]
    if direct_probe and direct_probe.get("status") == "no_subtitle_items":
        auth = str(direct_probe.get("auth") or "none")
        if auth == "none":
            return [
                "Bilibili unauthenticated page/API probe found zero subtitle items; retry with an exported Netscape cookies file via --cookies-file before concluding the source has no subtitles",
                "if a cookies-file path was previously validated on this machine, use it before audio or visual fallback",
                "record this as login-gated direct-probe evidence, not as proof that Bilibili has no subtitles",
            ]
        return [
            "Bilibili page/API probe found zero subtitle items even with the selected auth path; try yt-dlp --cookies-file before falling back",
            "if yt-dlp with cookies also reports no subtitles, use audio transcription or visual analysis fallback",
            "record this source as authenticated no-page-subtitle-list only after the cookies path is tested",
        ]
    if "subtitles are only available when logged in" in lowered or "login" in lowered:
        return [
            "retry with --cookies-browser chrome or --cookies-browser edge after logging in to Bilibili",
            "use audio fallback with --engine openai",
        ]
    if "too many requests" in lowered or "http error 429" in lowered:
        return [
            "retry with a narrower subtitle language such as --sub-langs en",
            "retry later or with browser cookies if the platform is rate limiting subtitles",
            "use audio fallback with --engine openai",
        ]
    return [
        "retry with --cookies-browser chrome or --cookies-browser edge",
        "use audio fallback with --engine openai",
    ]


def subtitle_failure_status(source: str, args: argparse.Namespace, subtitle_debug: dict[str, Any] | None) -> str:
    """Keep recoverable authorization failures distinct from genuine no-subtitle results."""
    if not is_bilibili(source):
        return "no_subtitles_engine_none"
    debug = subtitle_debug or {}
    stderr_tail = str(debug.get("stderr_tail", "")).lower()
    if re.search(r"could not copy .*cookie database", stderr_tail):
        return "browser_cookie_locked"
    if "failed to decrypt with dpapi" in stderr_tail:
        return "browser_cookie_decrypt_failed"
    direct_probe = debug.get("bilibili_direct_probe")
    direct_status = direct_probe.get("status") if isinstance(direct_probe, dict) else None
    if direct_status in {"invalid_requested_page", "requested_page_not_found"}:
        return str(direct_status)
    player_data = direct_probe.get("player_api_data", {}) if isinstance(direct_probe, dict) else {}
    requires_login = (
        isinstance(player_data, dict) and player_data.get("need_login_subtitle") is True
    ) or "subtitles are only available when logged in" in stderr_tail
    if isinstance(direct_probe, dict) and direct_probe.get("cookies_file_loaded") is False:
        return "auth_route_unreadable"
    authenticated_route = bool(args.cookies_file) or args.cookies_browser != "none"
    if requires_login and authenticated_route:
        return "auth_route_expired_or_rejected"
    if requires_login and not authenticated_route:
        return "auth_route_unavailable"
    if direct_status == "no_subtitle_for_requested_page":
        return str(direct_status)
    return "no_subtitles_engine_none"


def ytdlp_base_cmd(url: str, args: argparse.Namespace) -> list[str]:
    cmd = [sys.executable, "-m", "yt_dlp"]
    ffmpeg_location = ffmpeg_location_arg(args.ffmpeg_location)
    if ffmpeg_location:
        cmd.extend(["--ffmpeg-location", ffmpeg_location])
    if is_bilibili(url):
        cmd.extend([
            "--add-header",
            "Referer:https://www.bilibili.com/",
            "--add-header",
            "Origin:https://www.bilibili.com",
            "--user-agent",
            DEFAULT_UA,
        ])
    if args.cookies_browser and args.cookies_browser != "none":
        cmd.extend(["--cookies-from-browser", args.cookies_browser])
    if args.cookies_file:
        cmd.extend(["--cookies", str(Path(args.cookies_file).expanduser())])
    return cmd


def extract_initial_state(html: str) -> dict[str, Any]:
    match = re.search(r"<script>window\.__INITIAL_STATE__=(.*?);\(function\(", html)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def subtitle_items_from_video_data(video_data: dict[str, Any]) -> list[dict[str, Any]]:
    subtitle = video_data.get("subtitle") if isinstance(video_data, dict) else None
    if not isinstance(subtitle, dict):
        return []
    raw_items = subtitle.get("list") or subtitle.get("subtitles") or []
    if not isinstance(raw_items, list):
        return []
    return [dict(item) for item in raw_items if isinstance(item, dict)]


def normalize_bilibili_subtitle_url(value: str) -> str:
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("/"):
        return "https://www.bilibili.com" + value
    return value


def parse_bilibili_subtitle_json(text: str) -> tuple[str, str]:
    data = json.loads(text)
    body = data.get("body", []) if isinstance(data, dict) else []
    if not isinstance(body, list):
        return "", ""
    transcript_lines = []
    srt_lines = []
    for index, item in enumerate(body, start=1):
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        start = float(item.get("from", 0.0))
        end = float(item.get("to", start))
        transcript_lines.append(content)
        srt_lines.extend([
            str(index),
            f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
            content,
            "",
        ])
    return "\n".join(transcript_lines).strip(), "\n".join(srt_lines).strip()


def format_srt_timestamp(seconds: float) -> str:
    total_ms = max(0, int(round(float(seconds) * 1000)))
    ms = total_ms % 1000
    total_seconds = total_ms // 1000
    secs = total_seconds % 60
    minutes_total = total_seconds // 60
    minutes = minutes_total % 60
    hours = minutes_total // 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def direct_bilibili_subtitle_probe(url: str, output_dir: Path, args: argparse.Namespace) -> tuple[str | None, dict[str, Any]]:
    logs_dir = output_dir / "logs"
    ensure_dir(logs_dir)
    bvid = extract_bvid(url)
    requested_page, requested_page_error = bilibili_page_request(url)
    debug: dict[str, Any] = {
        "method": "bilibili_page_api_probe",
        "bvid": bvid,
        "requested_page": requested_page,
        "status": "started",
        "auth": "none",
        "subtitle_count": 0,
        "downloaded": [],
    }
    if not bvid:
        debug["status"] = "not_bvid"
        return None, debug
    if requested_page_error:
        debug["status"] = requested_page_error
        return None, debug

    page_url = url if is_url(url) else f"https://www.bilibili.com/video/{bvid}"
    headers = bilibili_headers(referer=page_url)
    cookies_file = getattr(args, "cookies_file", None)
    if cookies_file:
        debug["auth"] = "cookies_file"
        cookies_path = Path(cookies_file).expanduser()
        debug["cookies_file_present"] = cookies_path.exists()
        if cookies_path.exists():
            try:
                cookie_header, cookie_count = netscape_cookie_header(cookies_path, domains=("bilibili.com",))
                debug["cookies_file_loaded"] = bool(cookie_header)
                debug["cookie_count"] = cookie_count
                if cookie_header:
                    headers["Cookie"] = cookie_header
            except Exception as exc:
                debug["cookies_file_loaded"] = False
                debug["cookies_file_error"] = str(exc)
    try:
        page_status, html = fetch_text_url(page_url, headers=headers, timeout=max(10, min(args.subtitle_timeout, 60)))
        debug["page_status"] = page_status
        write_text(logs_dir / "bilibili_page.html", html)
        state = extract_initial_state(html)
        video_data = state.get("videoData") if isinstance(state.get("videoData"), dict) else {}
        cid = None
        aid = None
        if video_data:
            cid = (video_data.get("pages") or [{}])[0].get("cid") if isinstance(video_data.get("pages"), list) else video_data.get("cid")
            aid = video_data.get("aid")
            debug["page_video_data"] = {
                "title": video_data.get("title"),
                "aid": aid,
                "bvid": video_data.get("bvid"),
                "cid": cid,
                "duration": video_data.get("duration"),
                "owner": (video_data.get("owner") or {}).get("name") if isinstance(video_data.get("owner"), dict) else None,
            }
        page_subtitles = subtitle_items_from_video_data(video_data)
        debug["page_subtitle_count"] = len(page_subtitles)

        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        api_status, api_text = fetch_text_url(api_url, headers=headers, timeout=max(10, min(args.subtitle_timeout, 60)))
        write_text(logs_dir / "bilibili_view_api.json", api_text)
        debug["view_api_status"] = api_status
        try:
            api_data = json.loads(api_text)
        except json.JSONDecodeError:
            api_data = {}
        view = api_data.get("data", {}) if isinstance(api_data, dict) else {}
        if isinstance(view, dict):
            aid = aid or view.get("aid")
            selected_page, page_error = select_bilibili_page(view, requested_page)
            if page_error:
                debug["status"] = page_error
                debug["available_pages"] = [item.get("page") for item in view.get("pages", []) if isinstance(item, dict)]
                return None, debug
            if selected_page:
                cid = selected_page.get("cid")
                debug["selected_page"] = {
                    "page": selected_page.get("page"),
                    "cid": cid,
                    "part": selected_page.get("part"),
                    "duration": selected_page.get("duration"),
                }
            else:
                cid = cid or view.get("cid")
            debug["view_api_data"] = {
                "code": api_data.get("code") if isinstance(api_data, dict) else None,
                "title": view.get("title"),
                "aid": view.get("aid"),
                "bvid": view.get("bvid"),
                "cid": view.get("cid"),
                "duration": view.get("duration"),
                "owner": (view.get("owner") or {}).get("name") if isinstance(view.get("owner"), dict) else None,
            }
        api_subtitles = subtitle_items_from_video_data(view)
        debug["view_api_subtitle_count"] = len(api_subtitles)

        player_subtitles: list[dict[str, Any]] = []
        if cid and (bvid or aid):
            player_query = {"cid": cid}
            if bvid:
                player_query["bvid"] = bvid
            elif aid:
                player_query["aid"] = aid
            player_url = "https://api.bilibili.com/x/player/wbi/v2?" + urllib.parse.urlencode(player_query)
            player_status, player_text = fetch_text_url(player_url, headers=headers, timeout=max(10, min(args.subtitle_timeout, 60)))
            write_text(logs_dir / "bilibili_player_wbi_v2.json", player_text)
            debug["player_api_status"] = player_status
            try:
                player_data = json.loads(player_text)
            except json.JSONDecodeError:
                player_data = {}
            player_view = player_data.get("data", {}) if isinstance(player_data, dict) else {}
            if isinstance(player_view, dict):
                debug["player_api_data"] = {
                    "code": player_data.get("code") if isinstance(player_data, dict) else None,
                    "need_login_subtitle": player_view.get("need_login_subtitle"),
                }
            player_subtitles = subtitle_items_from_video_data(player_view)
        debug["player_api_subtitle_count"] = len(player_subtitles)

        # A multipart URL may render stale first-page state in HTML. For an
        # explicit ?p=N request, the player API queried with that page's cid is
        # authoritative; never allow first-page HTML subtitles to win.
        subtitle_items = player_subtitles if requested_page else (page_subtitles or player_subtitles or api_subtitles)
        debug["subtitle_count"] = len(subtitle_items)

        for item in subtitle_items:
            subtitle_url = item.get("subtitle_url") or item.get("url")
            if not subtitle_url:
                continue
            subtitle_url = normalize_bilibili_subtitle_url(str(subtitle_url))
            label = str(item.get("lan") or item.get("lan_doc") or item.get("id") or "subtitle")
            safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", label).strip("_") or "subtitle"
            subtitle_status, subtitle_text = fetch_text_url(subtitle_url, headers=headers, timeout=max(10, min(args.subtitle_timeout, 60)))
            parsed_subtitle_url = urllib.parse.urlparse(subtitle_url)
            debug.setdefault("downloaded", []).append({
                "label": label,
                "status": subtitle_status,
                "url_host": parsed_subtitle_url.netloc,
                "has_url": bool(subtitle_url),
            })
            if subtitle_status != 200:
                continue
            json_path = output_dir / f"bilibili_subtitle_{safe_label}.json"
            srt_path = output_dir / f"bilibili_subtitle_{safe_label}.srt"
            write_text(json_path, subtitle_text)
            transcript, srt_text = parse_bilibili_subtitle_json(subtitle_text)
            if transcript:
                write_text(srt_path, srt_text + "\n")
                debug["selected_file"] = str(json_path)
                debug["selected_srt"] = str(srt_path)
                debug["status"] = "subtitle_downloaded"
                return transcript, debug

        if requested_page and not subtitle_items:
            debug["status"] = "no_subtitle_for_requested_page"
        else:
            debug["status"] = "no_subtitle_items" if not subtitle_items else "subtitle_items_unusable"
        return None, debug
    except Exception as exc:
        debug["status"] = "probe_failed"
        debug["error"] = str(exc)
        return None, debug


def parse_subtitle_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8", errors="ignore")
    content = re.sub(r"^\ufeff", "", content)
    content = re.sub(r"WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    content = re.sub(
        r"\d{1,2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*"
        r"\d{1,2}:\d{2}:\d{2}[\.,]\d{3}.*?\n",
        "",
        content,
    )
    content = re.sub(r"^\d+\s*$", "", content, flags=re.MULTILINE)
    content = re.sub(r"<[^>]+>", "", content)
    content = re.sub(r"\{\\.*?\}", "", content)

    result: list[str] = []
    previous = ""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == previous:
            continue
        previous = line
        result.append(line)
    return "\n".join(result).strip()


def parse_subtitle_timestamp(value: str) -> float | None:
    cleaned = value.strip().replace(",", ".")
    match = re.match(
        r"^(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?$",
        cleaned,
    )
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    milliseconds = int((match.group(4) or "0").ljust(3, "0")[:3])
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0


def parse_subtitle_cues(path: Path) -> list[dict[str, Any]]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    content = re.sub(r"^\ufeff", "", content)
    lines = content.splitlines()
    cues: list[dict[str, Any]] = []
    index = 0
    cue_counter = 0
    while index < len(lines):
        line = lines[index].strip()
        if not line or line.upper().startswith("WEBVTT"):
            index += 1
            continue
        if "-->" not in line and index + 1 < len(lines) and "-->" in lines[index + 1]:
            index += 1
            line = lines[index].strip()
        if "-->" not in line:
            index += 1
            continue
        start_raw, end_raw = [part.strip().split()[0] for part in line.split("-->", 1)]
        start = parse_subtitle_timestamp(start_raw)
        end = parse_subtitle_timestamp(end_raw)
        index += 1
        text_lines = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index].strip())
            index += 1
        text = re.sub(r"<[^>]+>", "", " ".join(text_lines))
        text = re.sub(r"\{\\.*?\}", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if start is None or end is None or not text:
            continue
        cue_counter += 1
        cues.append({
            "id": f"subtitle_{cue_counter:04d}",
            "start_seconds": start,
            "end_seconds": end,
            "duration_seconds": max(0.0, end - start),
            "text": text,
        })
    return cues


def normalize_for_score(text: str, metric: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(
        r"\d{1,2}:\d{2}:\d{2}[\.,]\d{3}\s*-->\s*"
        r"\d{1,2}:\d{2}:\d{2}[\.,]\d{3}.*",
        "",
        text,
    )
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.lower()

    result: list[str] = []
    for char in text:
        category = unicodedata.category(char)
        if category.startswith(("P", "S")):
            result.append(" " if metric == "wer" else "")
        elif char.isspace():
            result.append(" " if metric == "wer" else "")
        else:
            result.append(char)
    return re.sub(r"\s+", " ", "".join(result)).strip()


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))


def normalize_match_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    return re.sub(r"\s+", "", normalized)


def contains_normalized(haystack: str, needle: str) -> bool:
    return normalize_match_text(needle) in normalize_match_text(haystack)


def edit_distance(left: list[str], right: list[str]) -> int:
    if len(left) < len(right):
        left, right = right, left
    previous = list(range(len(right) + 1))
    for i, left_item in enumerate(left, start=1):
        current = [i]
        for j, right_item in enumerate(right, start=1):
            current.append(
                min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (0 if left_item == right_item else 1),
                )
            )
        previous = current
    return previous[-1]


def score_transcripts(args: argparse.Namespace) -> int:
    reference_path = Path(args.reference).expanduser()
    candidate_path = Path(args.candidate).expanduser()
    if not reference_path.exists():
        raise RuntimeError(f"Reference transcript does not exist: {reference_path}")
    if not candidate_path.exists():
        raise RuntimeError(f"Candidate transcript does not exist: {candidate_path}")

    reference_raw = reference_path.read_text(encoding="utf-8", errors="ignore")
    candidate_raw = candidate_path.read_text(encoding="utf-8", errors="ignore")
    metric = args.metric
    if metric == "auto":
        metric = "cer" if contains_cjk(reference_raw + candidate_raw) else "wer"

    reference_text = normalize_for_score(reference_raw, metric)
    candidate_text = normalize_for_score(candidate_raw, metric)
    reference_units = list(reference_text) if metric == "cer" else reference_text.split()
    candidate_units = list(candidate_text) if metric == "cer" else candidate_text.split()
    distance = edit_distance(reference_units, candidate_units)
    denominator = max(1, len(reference_units))
    error_rate = distance / denominator
    result = {
        "status": "scored",
        "metric": metric,
        "reference": str(reference_path),
        "candidate": str(candidate_path),
        "distance": distance,
        "reference_units": len(reference_units),
        "candidate_units": len(candidate_units),
        "error_rate": round(error_rate, 6),
        "similarity": round(max(0.0, 1.0 - error_rate), 6),
        "normalization": [
            "NFKC",
            "lowercase",
            "remove subtitle timing and sequence lines",
            "remove punctuation/symbols",
            "remove whitespace for CER or collapse whitespace for WER",
        ],
    }

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser()
        ensure_dir(output_dir)
        write_json(output_dir / "score.json", result)

    print("RESULT_JSON:" + json.dumps(result, ensure_ascii=False))
    return 0


def check_terms(text: str, terms: list[Any]) -> tuple[list[str], list[str]]:
    expected = [str(term) for term in terms]
    found = [term for term in expected if contains_normalized(text, term)]
    missing = [term for term in expected if term not in found]
    return found, missing


def score_visual_notes(args: argparse.Namespace) -> int:
    notes_path = Path(args.notes).expanduser()
    gold_path = Path(args.gold).expanduser()
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else notes_path.parent
    if not notes_path.exists():
        raise RuntimeError(f"Visual notes file does not exist: {notes_path}")
    if not gold_path.exists():
        raise RuntimeError(f"Gold checklist file does not exist: {gold_path}")

    notes_text = notes_path.read_text(encoding="utf-8", errors="ignore")
    gold = json.loads(gold_path.read_text(encoding="utf-8"))
    weights = {"labels": 0.30, "facts": 0.45, "frames": 0.25}
    if isinstance(gold.get("weights"), dict):
        for key, value in gold["weights"].items():
            if key in weights:
                weights[key] = float(value)

    labels = gold.get("labels", [])
    label_found, label_missing = check_terms(notes_text, labels)
    label_score = len(label_found) / max(1, len(labels))

    fact_results = []
    fact_scores = []
    forbidden_hits: list[dict[str, str]] = []
    for fact in gold.get("facts", []):
        if not isinstance(fact, dict):
            continue
        fact_id = str(fact.get("id", f"fact_{len(fact_results) + 1}"))
        must_include = fact.get("must_include", [])
        found, missing = check_terms(notes_text, must_include)
        forbidden = [str(term) for term in fact.get("forbidden", [])]
        fact_forbidden_hits = [term for term in forbidden if contains_normalized(notes_text, term)]
        for term in fact_forbidden_hits:
            forbidden_hits.append({"scope": fact_id, "term": term})
        score = len(found) / max(1, len(must_include))
        if fact_forbidden_hits:
            score = max(0.0, score - 0.25 * len(fact_forbidden_hits))
        fact_scores.append(score)
        fact_results.append({
            "id": fact_id,
            "score": score,
            "found": found,
            "missing": missing,
            "forbidden_hits": fact_forbidden_hits,
        })
    fact_score = sum(fact_scores) / max(1, len(fact_scores))

    frame_results = []
    frame_scores = []
    for frame in gold.get("frames", []):
        if not isinstance(frame, dict):
            continue
        frame_id = str(frame.get("id") or frame.get("frame") or f"frame_{len(frame_results) + 1}")
        must_include = frame.get("must_include", [])
        found, missing = check_terms(notes_text, must_include)
        forbidden = [str(term) for term in frame.get("forbidden", [])]
        frame_forbidden_hits = [term for term in forbidden if contains_normalized(notes_text, term)]
        for term in frame_forbidden_hits:
            forbidden_hits.append({"scope": frame_id, "term": term})
        score = len(found) / max(1, len(must_include))
        if frame_forbidden_hits:
            score = max(0.0, score - 0.25 * len(frame_forbidden_hits))
        frame_scores.append(score)
        frame_results.append({
            "id": frame_id,
            "score": score,
            "found": found,
            "missing": missing,
            "forbidden_hits": frame_forbidden_hits,
        })
    frame_score = sum(frame_scores) / max(1, len(frame_scores))

    weighted_total = (
        label_score * weights["labels"]
        + fact_score * weights["facts"]
        + frame_score * weights["frames"]
    )
    total_weight = max(0.0001, weights["labels"] + weights["facts"] + weights["frames"])
    overall = max(0.0, min(1.0, weighted_total / total_weight))
    result = {
        "status": "scored",
        "method": "gold_checklist",
        "notes": str(notes_path),
        "gold": str(gold_path),
        "overall": round(overall, 6),
        "scores": {
            "label_recall": round(label_score, 6),
            "fact_coverage": round(fact_score, 6),
            "frame_coverage": round(frame_score, 6),
        },
        "weights": weights,
        "labels": {
            "expected": [str(term) for term in labels],
            "found": label_found,
            "missing": label_missing,
        },
        "facts": fact_results,
        "frames": frame_results,
        "forbidden_hits": forbidden_hits,
        "interpretation": (
            ">=0.85 strong, 0.70-0.85 usable with review, "
            "<0.70 needs correction or better sampling"
        ),
    }

    ensure_dir(output_dir)
    score_json = output_dir / "visual_score.json"
    score_md = output_dir / "visual_score.md"
    write_json(score_json, result)
    lines = [
        "# Visual Score",
        "",
        f"- Overall: `{overall:.3f}`",
        f"- Label recall: `{label_score:.3f}`",
        f"- Fact coverage: `{fact_score:.3f}`",
        f"- Frame coverage: `{frame_score:.3f}`",
        f"- Forbidden hits: `{len(forbidden_hits)}`",
        "",
        "## Missing Labels",
        "",
    ]
    lines.extend([f"- `{term}`" for term in label_missing] or ["- None"])
    lines.extend(["", "## Weak Facts", ""])
    weak_facts = [fact for fact in fact_results if fact["score"] < 1.0]
    if weak_facts:
        for fact in weak_facts:
            lines.append(f"- `{fact['id']}` score `{fact['score']:.3f}`, missing: {fact['missing']}")
    else:
        lines.append("- None")
    lines.extend(["", "## Weak Frames", ""])
    weak_frames = [frame for frame in frame_results if frame["score"] < 1.0]
    if weak_frames:
        for frame in weak_frames:
            lines.append(f"- `{frame['id']}` score `{frame['score']:.3f}`, missing: {frame['missing']}")
    else:
        lines.append("- None")
    write_text(score_md, "\n".join(lines).strip() + "\n")
    print(f"Done. Visual score: {score_json}")
    print("RESULT_JSON:" + json.dumps(result, ensure_ascii=False))
    return 0


def subtitle_priority(path: Path, sub_langs: str) -> tuple[int, str]:
    name = path.name.lower()
    languages = [item.strip().lower() for item in sub_langs.split(",") if item.strip()]
    for index, language in enumerate(languages):
        if f".{language}." in name or name.endswith(f".{language}{path.suffix.lower()}"):
            return index, name
    return len(languages), name


def chunk_text(text: str, max_chars: int) -> list[str]:
    if max_chars < 1000:
        raise RuntimeError("--chunk-chars must be at least 1000.")

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append("\n\n".join(current).strip())
                current = []
                current_len = 0
            for index in range(0, len(paragraph), max_chars):
                chunks.append(paragraph[index:index + max_chars].strip())
            continue

        next_len = current_len + len(paragraph) + (2 if current else 0)
        if current and next_len > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [paragraph]
            current_len = len(paragraph)
        else:
            current.append(paragraph)
            current_len = next_len

    if current:
        chunks.append("\n\n".join(current).strip())

    return [chunk for chunk in chunks if chunk]


def analysis_instructions(mode: str) -> list[str]:
    common = [
        "Read transcript chunks in order.",
        "Ground every claim in the transcript; do not invent details.",
        "Keep useful original phrasing when it helps future writing.",
        "Call out unclear or missing context instead of guessing.",
    ]
    if mode == "summary":
        return common + [
            "Extract 5-8 key ideas in priority order.",
            "List concrete examples, data points, names, tools, and links mentioned.",
            "End with action items or follow-up questions.",
        ]
    if mode == "workflow":
        return common + [
            "Map the process as ordered steps and checkpoints.",
            "Identify failure points, prerequisites, and fallback paths.",
            "Suggest documentation or product changes that reduce user friction.",
        ]
    if mode == "learning":
        return common + [
            "Turn the transcript into study notes grouped by concept.",
            "Preserve definitions, examples, and contrasts.",
            "End with questions a learner should be able to answer.",
        ]
    return common + [
        "Analyze how the tutorial opens and lowers beginner anxiety.",
        "Extract setup steps, checkpoints, and troubleshooting moments.",
        "Identify phrases or structures worth adapting into our documentation.",
        "List missing pieces in our own onboarding or workflow.",
    ]


def write_analysis_pack(
    output_dir: Path,
    metadata: dict[str, Any],
    transcript: str,
    *,
    mode: str,
    chunk_chars: int,
) -> None:
    analysis_dir = output_dir / "analysis"
    chunks_dir = analysis_dir / "chunks"
    ensure_dir(chunks_dir)

    chunks = chunk_text(transcript, chunk_chars)
    chunk_paths: list[str] = []
    width = max(2, len(str(len(chunks))))
    for index, chunk in enumerate(chunks, start=1):
        chunk_path = chunks_dir / f"chunk_{index:0{width}d}.txt"
        write_text(chunk_path, chunk + "\n")
        chunk_paths.append(str(chunk_path))

    prompt_lines = [
        "# Video Analysis Prompt",
        "",
        f"Source: `{metadata.get('source')}`",
        f"Mode: `{mode}`",
        f"Chunk count: {len(chunks)}",
        "",
        "## Task",
        "",
        "Use the transcript chunks in `analysis/chunks/` to produce a clear, useful analysis.",
        "",
        "## Instructions",
        "",
    ]
    prompt_lines.extend([f"- {item}" for item in analysis_instructions(mode)])
    prompt_lines.extend([
        "",
        "## Output Shape",
        "",
        "1. One-paragraph executive summary.",
        "2. Structured notes with headings.",
        "3. Key quotes or original phrasings worth preserving.",
        "4. Actionable documentation/workflow improvements.",
        "5. Open questions or validation gaps.",
    ])
    prompt_path = analysis_dir / "analysis_prompt.md"
    write_text(prompt_path, "\n".join(prompt_lines).strip() + "\n")

    metadata["analysis"] = {
        "mode": mode,
        "chunk_chars": chunk_chars,
        "chunk_count": len(chunks),
    }
    metadata.setdefault("files", {})
    metadata["files"]["analysis_prompt"] = str(prompt_path)
    metadata["files"]["analysis_chunks"] = chunk_paths


def write_visual_prompt(
    output_dir: Path,
    metadata: dict[str, Any],
    *,
    mode: str,
) -> None:
    visual_dir = output_dir / "visual"
    frame_paths = [Path(path) for path in metadata.get("frames", [])]
    lines = [
        "# Visual Video Analysis Prompt",
        "",
        f"Source: `{metadata.get('source')}`",
        f"Mode: `{mode}`",
        f"Frame count: {len(frame_paths)}",
        "",
        "## Task",
        "",
        "Inspect the sampled frames in order and describe what visual information adds beyond the transcript.",
        "",
        "## Instructions",
        "",
        "- Treat frames as sparse samples, not a complete reconstruction.",
        "- Note visible UI state, cursor/action hints, diagrams, slides, gestures, facial expressions, and scene changes.",
        "- Extract on-screen text only when legible; mark uncertain OCR instead of guessing.",
        "- Align observations to frame timestamps when available.",
        "- Call out missing intervals where more frames or clips are needed.",
        "",
        "## Output Shape",
        "",
        "1. One-paragraph visual summary.",
        "2. Timeline bullets with timestamp, frame file, and observation.",
        "3. UI/actions/OCR/gesture notes grouped by category.",
        "4. What this visual pass adds to transcript-only analysis.",
        "5. Follow-up frame ranges or clips worth sampling.",
    ]
    if mode == "reverse":
        lines.extend([
            "",
            "## Reverse-Parsing Focus",
            "",
            "- Infer the likely tutorial action or editing intent for each visual change.",
            "- Identify reusable structure: setup, demonstration, verification, correction, and result.",
            "- Do not claim exact source project files, prompts, or edits unless visible evidence supports it.",
        ])
    prompt_path = visual_dir / "visual_prompt.md"
    write_text(prompt_path, "\n".join(lines).strip() + "\n")
    metadata.setdefault("files", {})
    metadata["files"]["visual_prompt"] = str(prompt_path)


def format_timestamp(seconds: float | int | None) -> str:
    if seconds is None:
        return "unknown"
    total = max(0, int(round(float(seconds))))
    minutes, secs = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def load_visual_frame_index(input_dir: Path, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    frame_index = metadata.get("frame_index")
    if isinstance(frame_index, list) and frame_index:
        return [dict(item) for item in frame_index if isinstance(item, dict)]

    frames_json = metadata.get("files", {}).get("frames_json") if isinstance(metadata.get("files"), dict) else None
    candidates = []
    if frames_json:
        candidates.append(Path(frames_json))
    candidates.append(input_dir / "visual" / "frames.json")

    for candidate in candidates:
        resolved = candidate
        if not resolved.exists() and not candidate.is_absolute():
            resolved = input_dir / candidate
        if resolved.exists():
            data = json.loads(resolved.read_text(encoding="utf-8"))
            frames = data.get("frames", [])
            if isinstance(frames, list):
                return [dict(item) for item in frames if isinstance(item, dict)]
    return []


def resolve_visual_frame_path(input_dir: Path, frame_file: str) -> Path:
    frame_path = Path(frame_file).expanduser()
    if frame_path.exists():
        return frame_path
    if not frame_path.is_absolute():
        candidate = input_dir / frame_path
        if candidate.exists():
            return candidate
        candidate = input_dir / "visual" / "frames" / frame_path.name
        if candidate.exists():
            return candidate
    return frame_path


def image_mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "application/octet-stream"


def select_visual_frames(
    input_dir: Path,
    frame_index: list[dict[str, Any]],
    max_frames: int,
) -> list[dict[str, Any]]:
    if max_frames >= len(frame_index):
        items = frame_index
    elif max_frames == 1:
        items = [frame_index[0]]
    else:
        positions = [
            round(index * (len(frame_index) - 1) / (max_frames - 1))
            for index in range(max_frames)
        ]
        items = [frame_index[position] for position in positions]

    selected: list[dict[str, Any]] = []
    for item in items:
        frame_file = str(item.get("file", ""))
        frame_path = resolve_visual_frame_path(input_dir, frame_file)
        selected.append({
            "index": item.get("index"),
            "timestamp_seconds": item.get("timestamp_seconds"),
            "timestamp": format_timestamp(item.get("timestamp_seconds")),
            "file": frame_file,
            "resolved_file": str(frame_path),
            "exists": frame_path.exists(),
            "mime_type": image_mime_type(frame_path),
        })
    return selected


def load_visual_selected_frame_index(
    input_dir: Path,
    metadata: dict[str, Any],
    *,
    selection_file: str | None = None,
) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    if selection_file:
        candidates.append(Path(selection_file).expanduser())
    files = metadata.get("files", {})
    if isinstance(files, dict) and files.get("selected_frames_json"):
        candidates.append(Path(str(files["selected_frames_json"])))
    candidates.append(input_dir / "visual" / "selected_frames.json")

    for candidate in candidates:
        resolved = candidate
        if not resolved.exists() and not candidate.is_absolute():
            resolved = input_dir / candidate
        if resolved.exists():
            data = json.loads(resolved.read_text(encoding="utf-8"))
            frames = data.get("selected_frames", data.get("frames", []))
            if isinstance(frames, list) and frames:
                return [dict(item) for item in frames if isinstance(item, dict)]
    return []


def visual_request_frame_index(
    input_dir: Path,
    metadata: dict[str, Any],
    *,
    frame_selection: str,
    selection_file: str | None = None,
) -> tuple[list[dict[str, Any]], str]:
    if frame_selection == "smart":
        selected = load_visual_selected_frame_index(
            input_dir,
            metadata,
            selection_file=selection_file,
        )
        if selected:
            return selected, "smart"
    return load_visual_frame_index(input_dir, metadata), "even"


def run_ffmpeg_thumbnails(
    ffmpeg_command: str,
    frame_paths: list[Path],
    *,
    timeout: int,
) -> list[bytes | None]:
    frame_size = SMART_THUMB_WIDTH * SMART_THUMB_HEIGHT * SMART_THUMB_CHANNELS
    if not frame_paths:
        return []

    pattern_match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", frame_paths[0].name)
    can_use_pattern = bool(pattern_match)
    if pattern_match:
        prefix, digits, suffix = pattern_match.groups()
        first_number = int(digits)
        width = len(digits)
        parent = frame_paths[0].parent
        for offset, path in enumerate(frame_paths):
            expected = f"{prefix}{first_number + offset:0{width}d}{suffix}"
            if path.parent != parent or path.name != expected:
                can_use_pattern = False
                break
    if can_use_pattern and pattern_match:
        prefix, digits, suffix = pattern_match.groups()
        pattern = frame_paths[0].parent / f"{prefix}%0{len(digits)}d{suffix}"
        cmd = [
            ffmpeg_command,
            "-hide_banner",
            "-loglevel",
            "error",
            "-start_number",
            str(int(digits)),
            "-i",
            str(pattern),
            "-vf",
            f"scale={SMART_THUMB_WIDTH}:{SMART_THUMB_HEIGHT},format=rgb24",
            "-frames:v",
            str(len(frame_paths)),
            "-f",
            "rawvideo",
            "-",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode == 0 and len(result.stdout) >= frame_size:
            thumbnails: list[bytes | None] = []
            for offset in range(len(frame_paths)):
                start = offset * frame_size
                end = start + frame_size
                if end <= len(result.stdout):
                    thumbnails.append(result.stdout[start:end])
                else:
                    thumbnails.append(None)
            return thumbnails

    thumbnails = []
    deadline = time.monotonic() + max(1, timeout)
    for path in frame_paths:
        remaining = max(1, int(deadline - time.monotonic()))
        cmd = [
            ffmpeg_command,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(path),
            "-vf",
            f"scale={SMART_THUMB_WIDTH}:{SMART_THUMB_HEIGHT},format=rgb24",
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=remaining,
                check=False,
            )
        except subprocess.TimeoutExpired:
            thumbnails.append(None)
            continue
        if result.returncode == 0 and len(result.stdout) >= frame_size:
            thumbnails.append(result.stdout[:frame_size])
        else:
            thumbnails.append(None)
    return thumbnails


def frame_delta(previous: bytes | None, current: bytes | None) -> float:
    if previous is None or current is None:
        return 0.0
    if len(previous) != len(current) or not previous:
        return 0.0
    total = sum(abs(a - b) for a, b in zip(previous, current))
    return total / (255.0 * len(previous))


def nearest_frame_position(frame_index: list[dict[str, Any]], timestamp: float) -> int:
    best_position = 0
    best_distance = float("inf")
    for position, item in enumerate(frame_index):
        value = item.get("timestamp_seconds")
        if value is None:
            continue
        distance = abs(float(value) - timestamp)
        if distance < best_distance:
            best_position = position
            best_distance = distance
    return best_position


def load_visual_event_hints(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_events = data.get("events", data) if isinstance(data, dict) else data
    if not isinstance(raw_events, list):
        raise RuntimeError("Event hints must be a JSON list or an object with an `events` list.")
    events = []
    for index, item in enumerate(raw_events, start=1):
        if not isinstance(item, dict) or "timestamp_seconds" not in item:
            continue
        timestamp = float(item["timestamp_seconds"])
        events.append({
            "id": str(item.get("id", f"hint_{index:04d}")),
            "timestamp_seconds": timestamp,
            "timestamp": format_timestamp(timestamp),
            "tolerance_seconds": float(item.get("tolerance_seconds", 1.0)),
            "weight": float(item.get("weight", 1.0)),
            "source": str(item.get("source", "event_hint")),
            "description": str(item.get("description", "")),
        })
    events.sort(
        key=lambda item: (
            -float(item.get("weight", 1.0)),
            float(item.get("timestamp_seconds", 0.0)),
        )
    )
    return events


def event_hints_by_position(
    frame_index: list[dict[str, Any]],
    event_hints: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    by_position: dict[int, list[dict[str, Any]]] = {}
    for hint in event_hints:
        position = nearest_frame_position(frame_index, float(hint["timestamp_seconds"]))
        by_position.setdefault(position, []).append(hint)
    return by_position


def resolve_smart_selection_policy(args: argparse.Namespace) -> dict[str, Any]:
    values = dict(SMART_SELECTION_POLICIES[args.policy])
    for key, attr in (
        ("budget_frames", "budget_frames"),
        ("baseline_seconds", "baseline_seconds"),
        ("min_gap_seconds", "min_gap_seconds"),
        ("event_neighbor_frames", "event_neighbor_frames"),
        ("coverage_fraction", "coverage_fraction"),
    ):
        override = getattr(args, attr)
        if override is not None:
            values[key] = override
    values["policy"] = args.policy
    values["signal_version"] = "rgb_delta_v2"
    return values


def write_smart_sampling_report(
    path: Path,
    *,
    metadata: dict[str, Any],
    policy: dict[str, Any],
    frame_scores: list[dict[str, Any]],
    selected_frames: list[dict[str, Any]],
    event_hints: list[dict[str, Any]],
) -> None:
    deltas = [float(item.get("visual_delta", 0.0)) for item in frame_scores]
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    max_delta = max(deltas) if deltas else 0.0
    lines = [
        "# Smart Visual Sampling Report",
        "",
        f"Source: `{metadata.get('source', '')}`",
        f"Candidate frames: {len(frame_scores)}",
        f"Selected frames: {len(selected_frames)}",
        "",
        "## Policy",
        "",
        f"- Budget frames: {policy.get('budget_frames')}",
        f"- Baseline seconds: {policy.get('baseline_seconds')}",
        f"- Effective baseline seconds: {policy.get('effective_baseline_seconds')}",
        f"- Minimum gap seconds: {policy.get('min_gap_seconds')}",
        f"- Event neighbor frames: {policy.get('event_neighbor_frames')}",
        f"- Coverage fraction: {policy.get('coverage_fraction')}",
        f"- Event hints: {policy.get('event_hint_count', 0)}",
        "",
        "## Signals",
        "",
        "- `visual_delta`: normalized RGB thumbnail difference from the previous candidate frame.",
        "- `event_hint`: externally supplied semantic timestamp from subtitles, chapters, OCR, or manual review.",
        "- Anchors and periodic baseline frames keep timeline coverage even when changes are subtle.",
        "- OCR, chapter, and audio-density signals can use the same event-hint interface as they become available.",
        f"- Mean visual delta: {mean_delta:.6f}",
        f"- Max visual delta: {max_delta:.6f}",
        "",
        "## Selected Frames",
        "",
        "| Rank | Frame | Time | Score | Reasons | File |",
        "|---:|---:|---:|---:|---|---|",
    ]
    for rank, frame in enumerate(selected_frames, start=1):
        reasons = ", ".join(str(item) for item in frame.get("reasons", []))
        lines.append(
            "| {rank} | {index} | {timestamp} | {score:.6f} | {reasons} | `{file}` |".format(
                rank=rank,
                index=frame.get("index", ""),
                timestamp=frame.get("timestamp", ""),
                score=float(frame.get("smart_score", 0.0)),
                reasons=reasons,
                file=frame.get("file", ""),
            )
        )
    if event_hints:
        lines.extend([
            "",
            "## Event Hints",
            "",
            "| Hint | Time | Weight | Source | Description |",
            "|---|---:|---:|---|---|",
        ])
        for hint in event_hints[:50]:
            description = str(hint.get("description", "")).replace("|", "\\|")
            lines.append(
                "| {id} | {time} | {weight:.3f} | {source} | {description} |".format(
                    id=hint.get("id", ""),
                    time=hint.get("timestamp", format_timestamp(hint.get("timestamp_seconds"))),
                    weight=float(hint.get("weight", 1.0)),
                    source=str(hint.get("source", "")).replace("|", "\\|"),
                    description=description,
                )
            )
        if len(event_hints) > 50:
            lines.append(f"| ... | ... | ... | ... | {len(event_hints) - 50} more hints omitted |")
    lines.extend([
        "",
        "## Use",
        "",
        "Run `visual-agent-task` or `visual-analyze` after this command. Those commands prefer `visual/selected_frames.json` when `--frame-selection smart` is used.",
        "For high-risk UI/action intervals, re-run dense extraction on the relevant time range with a smaller interval such as 0.5s.",
    ])
    write_text(path, "\n".join(lines).strip() + "\n")


def create_visual_smart_select(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir).expanduser()
    metadata_path = input_dir / "metadata.json"
    visual_dir = input_dir / "visual"
    ensure_dir(visual_dir)
    policy_values = resolve_smart_selection_policy(args)
    budget_frames = int(policy_values["budget_frames"])
    baseline_seconds = float(policy_values["baseline_seconds"])
    min_gap_seconds = float(policy_values["min_gap_seconds"])
    event_neighbor_frames = int(policy_values["event_neighbor_frames"])
    coverage_fraction = float(policy_values["coverage_fraction"])
    if not metadata_path.exists():
        raise RuntimeError(f"metadata.json does not exist: {metadata_path}")
    if budget_frames <= 0:
        raise RuntimeError("--budget-frames must be greater than 0.")
    if baseline_seconds <= 0:
        raise RuntimeError("--baseline-seconds must be greater than 0.")
    if min_gap_seconds < 0:
        raise RuntimeError("--min-gap-seconds must be greater than or equal to 0.")
    if event_neighbor_frames < 0:
        raise RuntimeError("--event-neighbor-frames must be greater than or equal to 0.")
    if coverage_fraction < 0 or coverage_fraction > 1:
        raise RuntimeError("--coverage-fraction must be between 0 and 1.")
    if args.timeout <= 0:
        raise RuntimeError("--timeout must be greater than 0.")

    metadata = load_metadata(metadata_path)
    frame_index = load_visual_frame_index(input_dir, metadata)
    if not frame_index:
        raise RuntimeError("No frames found in metadata or visual/frames.json.")
    event_hints_path = getattr(args, "event_hints", None)
    event_hints: list[dict[str, Any]] = []
    if event_hints_path:
        resolved_event_hints_path = Path(event_hints_path).expanduser()
        if not resolved_event_hints_path.exists():
            raise RuntimeError(f"Event hints file does not exist: {resolved_event_hints_path}")
        event_hints = load_visual_event_hints(resolved_event_hints_path)
    event_hints_by_frame = event_hints_by_position(frame_index, event_hints) if event_hints else {}
    hint_scores = [
        max((float(hint.get("weight", 1.0)) for hint in event_hints_by_frame.get(position, [])), default=0.0)
        for position in range(len(frame_index))
    ]
    ffmpeg_command = resolve_ffmpeg(args.ffmpeg_location)
    if not ffmpeg_command:
        raise RuntimeError("ffmpeg is required for smart visual selection.")

    frame_paths = [
        resolve_visual_frame_path(input_dir, str(item.get("file", "")))
        for item in frame_index
    ]
    thumbnails = run_ffmpeg_thumbnails(ffmpeg_command, frame_paths, timeout=args.timeout)
    deltas = [0.0]
    for previous, current in zip(thumbnails, thumbnails[1:]):
        deltas.append(frame_delta(previous, current))
    while len(deltas) < len(frame_index):
        deltas.append(0.0)

    selected_reasons: dict[int, set[str]] = {}

    def add_position(position: int, reason: str, *, enforce_gap: bool = False) -> bool:
        if position < 0 or position >= len(frame_index):
            return False
        if position not in selected_reasons and len(selected_reasons) >= budget_frames:
            return False
        if enforce_gap and position not in selected_reasons and min_gap_seconds:
            timestamp = frame_index[position].get("timestamp_seconds")
            if timestamp is not None:
                timestamp_value = float(timestamp)
                for selected_position in selected_reasons:
                    other = frame_index[selected_position].get("timestamp_seconds")
                    if other is not None and abs(float(other) - timestamp_value) < min_gap_seconds:
                        return False
        selected_reasons.setdefault(position, set()).add(reason)
        return True

    add_position(0, "anchor_start")
    add_position(len(frame_index) - 1, "anchor_end")

    first_ts = float(frame_index[0].get("timestamp_seconds") or 0.0)
    last_ts = float(frame_index[-1].get("timestamp_seconds") or first_ts)
    span = max(0.0, last_ts - first_ts)
    baseline_budget = min(
        max(0, int(round(budget_frames * coverage_fraction))),
        max(0, budget_frames - 2),
    )
    effective_baseline_seconds = baseline_seconds
    if baseline_budget > 1 and span > 0:
        effective_baseline_seconds = min(baseline_seconds, span / max(1, baseline_budget))

    event_candidates = sorted(
        range(len(frame_index)),
        key=lambda position: deltas[position],
        reverse=True,
    )
    reserved_for_baseline = baseline_budget if span > 0 else 0
    hint_centers: list[int] = []
    for hint in event_hints:
        if len(selected_reasons) >= budget_frames:
            break
        position = nearest_frame_position(frame_index, float(hint["timestamp_seconds"]))
        added = add_position(position, "event_hint", enforce_gap=True)
        if added:
            hint_centers.append(position)

    event_centers: list[int] = []
    for position in event_candidates:
        if len(selected_reasons) >= max(0, budget_frames - reserved_for_baseline):
            break
        if deltas[position] <= 0:
            continue
        added = add_position(position, "visual_delta", enforce_gap=True)
        if added:
            event_centers.append(position)

    if baseline_budget > 0 and span > 0:
        target = first_ts
        while target <= last_ts and len(selected_reasons) < budget_frames:
            add_position(nearest_frame_position(frame_index, target), "periodic_baseline")
            target += effective_baseline_seconds

    for position in event_candidates:
        if len(selected_reasons) >= budget_frames:
            break
        if position in selected_reasons or deltas[position] <= 0:
            continue
        add_position(position, "visual_delta", enforce_gap=True)

    if event_neighbor_frames:
        for position in sorted(set(hint_centers + event_centers)):
            if len(selected_reasons) >= budget_frames:
                break
            for neighbor_offset in range(1, event_neighbor_frames + 1):
                if len(selected_reasons) >= budget_frames:
                    break
                add_position(position - neighbor_offset, "event_neighbor", enforce_gap=False)
                if len(selected_reasons) >= budget_frames:
                    break
                add_position(position + neighbor_offset, "event_neighbor", enforce_gap=False)

    selected_positions = sorted(selected_reasons)
    selected_frames: list[dict[str, Any]] = []
    for position in selected_positions:
        item = dict(frame_index[position])
        frame_file = str(item.get("file", ""))
        frame_path = resolve_visual_frame_path(input_dir, frame_file)
        item.update({
            "timestamp": format_timestamp(item.get("timestamp_seconds")),
            "resolved_file": str(frame_path),
            "exists": frame_path.exists(),
            "mime_type": image_mime_type(frame_path),
            "visual_delta": round(float(deltas[position]), 6),
            "event_hint_score": round(float(hint_scores[position]), 6),
            "event_hints": event_hints_by_frame.get(position, []),
            "smart_score": round(float(deltas[position]) + float(hint_scores[position]), 6),
            "reasons": sorted(selected_reasons[position]),
        })
        selected_frames.append(item)

    selected_lookup = set(selected_positions)
    frame_scores = []
    for position, item in enumerate(frame_index):
        frame_scores.append({
            "position": position,
            "index": item.get("index"),
            "timestamp_seconds": item.get("timestamp_seconds"),
            "timestamp": format_timestamp(item.get("timestamp_seconds")),
            "file": item.get("file"),
            "visual_delta": round(float(deltas[position]), 6),
            "event_hint_score": round(float(hint_scores[position]), 6),
            "event_hints": event_hints_by_frame.get(position, []),
            "smart_score": round(float(deltas[position]) + float(hint_scores[position]), 6),
            "selected": position in selected_lookup,
            "reasons": sorted(selected_reasons.get(position, set())),
        })

    selection_path = Path(args.selection_file).expanduser() if args.selection_file else visual_dir / "selected_frames.json"
    scores_path = visual_dir / "frame_scores.json"
    report_path = Path(args.report_file).expanduser() if args.report_file else visual_dir / "smart_sampling_report.md"
    policy = {
        "policy": policy_values["policy"],
        "budget_frames": budget_frames,
        "baseline_seconds": baseline_seconds,
        "effective_baseline_seconds": round(float(effective_baseline_seconds), 3),
        "min_gap_seconds": min_gap_seconds,
        "event_neighbor_frames": event_neighbor_frames,
        "coverage_fraction": coverage_fraction,
        "event_hints": str(Path(event_hints_path).expanduser()) if event_hints_path else None,
        "event_hint_count": len(event_hints),
        "signal_version": policy_values["signal_version"],
    }
    write_json(scores_path, {
        "policy": policy,
        "candidate_count": len(frame_scores),
        "selected_count": len(selected_frames),
        "event_hints": event_hints,
        "frames": frame_scores,
    })
    write_json(selection_path, {
        "policy": policy,
        "candidate_count": len(frame_scores),
        "selected_count": len(selected_frames),
        "event_hints": event_hints,
        "selected_frames": selected_frames,
    })
    write_smart_sampling_report(
        report_path,
        metadata=metadata,
        policy=policy,
        frame_scores=frame_scores,
        selected_frames=selected_frames,
        event_hints=event_hints,
    )

    metadata.setdefault("files", {})
    metadata["files"]["frame_scores_json"] = str(scores_path)
    metadata["files"]["selected_frames_json"] = str(selection_path)
    metadata["files"]["smart_sampling_report"] = str(report_path)
    metadata["visual_smart_selection"] = {
        "status": "selected",
        "candidate_count": len(frame_scores),
        "selected_count": len(selected_frames),
        "policy": policy,
    }
    write_json(metadata_path, metadata)
    print(f"Done. Smart selection: {selection_path}")
    print("RESULT_JSON:" + json.dumps(metadata["visual_smart_selection"], ensure_ascii=False))
    return 0


def load_smart_selection_file(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    frames = data.get("selected_frames", data.get("frames", []))
    if not isinstance(frames, list):
        return []
    return [dict(item) for item in frames if isinstance(item, dict)]


def load_gold_events(path: Path, *, default_tolerance: float) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    raw_events = data.get("events", data) if isinstance(data, dict) else data
    if not isinstance(raw_events, list):
        raise RuntimeError("Gold events must be a JSON list or an object with an `events` list.")
    events = []
    for index, item in enumerate(raw_events, start=1):
        if not isinstance(item, dict):
            continue
        if "timestamp_seconds" not in item:
            continue
        tolerance = item.get("tolerance_seconds", default_tolerance)
        events.append({
            "id": str(item.get("id", f"event_{index:02d}")),
            "timestamp_seconds": float(item["timestamp_seconds"]),
            "tolerance_seconds": float(tolerance),
            "description": str(item.get("description", "")),
        })
    return events


def score_visual_smart_selection(args: argparse.Namespace) -> int:
    selection_path = Path(args.selection).expanduser()
    gold_path = Path(args.gold_events).expanduser()
    if not selection_path.exists():
        raise RuntimeError(f"Selection file does not exist: {selection_path}")
    if not gold_path.exists():
        raise RuntimeError(f"Gold events file does not exist: {gold_path}")
    if args.default_tolerance < 0:
        raise RuntimeError("--default-tolerance must be greater than or equal to 0.")

    selected_frames = load_smart_selection_file(selection_path)
    if not selected_frames:
        raise RuntimeError("No selected frames found in selection file.")
    gold_events = load_gold_events(gold_path, default_tolerance=args.default_tolerance)
    if not gold_events:
        raise RuntimeError("No gold events found in gold-events file.")

    selected_times = []
    for frame in selected_frames:
        timestamp = frame.get("timestamp_seconds")
        if timestamp is not None:
            selected_times.append(float(timestamp))

    event_results = []
    covered_count = 0
    for event in gold_events:
        timestamp = float(event["timestamp_seconds"])
        tolerance = float(event["tolerance_seconds"])
        nearest_time = None
        nearest_distance = None
        for selected_time in selected_times:
            distance = abs(selected_time - timestamp)
            if nearest_distance is None or distance < nearest_distance:
                nearest_time = selected_time
                nearest_distance = distance
        covered = nearest_distance is not None and nearest_distance <= tolerance
        if covered:
            covered_count += 1
        event_results.append({
            "id": event["id"],
            "timestamp_seconds": timestamp,
            "tolerance_seconds": tolerance,
            "description": event.get("description", ""),
            "covered": covered,
            "nearest_selected_seconds": nearest_time,
            "nearest_distance_seconds": None if nearest_distance is None else round(float(nearest_distance), 3),
        })

    recall = covered_count / max(1, len(gold_events))
    result = {
        "status": "scored",
        "method": "gold_event_recall",
        "selection": str(selection_path),
        "gold_events": str(gold_path),
        "selected_count": len(selected_frames),
        "gold_event_count": len(gold_events),
        "covered_event_count": covered_count,
        "event_recall": round(recall, 6),
        "events": event_results,
    }

    output_dir = Path(args.output_dir).expanduser() if args.output_dir else selection_path.parent
    ensure_dir(output_dir)
    score_json = output_dir / "visual_smart_score.json"
    score_md = output_dir / "visual_smart_score.md"
    write_json(score_json, result)

    lines = [
        "# Visual Smart Selection Score",
        "",
        f"- Selection: `{selection_path}`",
        f"- Gold events: `{gold_path}`",
        f"- Selected frames: `{len(selected_frames)}`",
        f"- Gold events: `{len(gold_events)}`",
        f"- Covered events: `{covered_count}`",
        f"- Event recall: `{recall:.3f}`",
        "",
        "## Events",
        "",
        "| Event | Time | Tolerance | Covered | Nearest selected | Distance |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for event in event_results:
        nearest = event["nearest_selected_seconds"]
        distance = event["nearest_distance_seconds"]
        lines.append(
            "| {id} | {time:.3f} | {tol:.3f} | {covered} | {nearest} | {distance} |".format(
                id=event["id"],
                time=float(event["timestamp_seconds"]),
                tol=float(event["tolerance_seconds"]),
                covered="yes" if event["covered"] else "no",
                nearest="" if nearest is None else f"{float(nearest):.3f}",
                distance="" if distance is None else f"{float(distance):.3f}",
            )
        )
    write_text(score_md, "\n".join(lines).strip() + "\n")
    print(f"Done. Visual smart score: {score_json}")
    print("RESULT_JSON:" + json.dumps(result, ensure_ascii=False))
    return 0


def parse_keyword_list(value: str) -> list[str]:
    keywords = []
    for raw in re.split(r"[,，]", value or ""):
        cleaned = raw.strip()
        if cleaned:
            keywords.append(cleaned)
    return keywords


def create_visual_subtitle_hints(args: argparse.Namespace) -> int:
    subtitle_path = Path(args.subtitle).expanduser()
    if not subtitle_path.exists():
        raise RuntimeError(f"Subtitle file does not exist: {subtitle_path}")
    if args.min_gap_seconds < 0:
        raise RuntimeError("--min-gap-seconds must be greater than or equal to 0.")
    if args.max_events <= 0:
        raise RuntimeError("--max-events must be greater than 0.")
    if args.default_tolerance < 0:
        raise RuntimeError("--default-tolerance must be greater than or equal to 0.")

    cues = parse_subtitle_cues(subtitle_path)
    keywords = parse_keyword_list(args.keywords)
    normalized_keywords = [(keyword, normalize_match_text(keyword)) for keyword in keywords]
    events = []
    last_kept_time: float | None = None
    for cue in cues:
        text = str(cue.get("text", ""))
        timestamp = float(cue["start_seconds"])
        normalized_text = normalize_match_text(text)
        matched_keywords = [
            keyword for keyword, normalized in normalized_keywords
            if normalized and normalized in normalized_text
        ]
        reason = "subtitle_keyword" if matched_keywords else "subtitle_boundary"
        min_gap = float(args.keyword_min_gap_seconds) if matched_keywords else float(args.min_gap_seconds)
        if last_kept_time is not None and timestamp - last_kept_time < min_gap:
            continue
        weight = float(args.keyword_weight) if matched_keywords else float(args.boundary_weight)
        events.append({
            "id": str(cue.get("id", f"subtitle_{len(events) + 1:04d}")),
            "timestamp_seconds": round(timestamp, 3),
            "timestamp": format_timestamp(timestamp),
            "tolerance_seconds": float(args.default_tolerance),
            "weight": weight,
            "source": reason,
            "description": text[:240],
            "matched_keywords": matched_keywords,
        })
        last_kept_time = timestamp
        if len(events) >= int(args.max_events):
            break

    output_file = Path(args.output_file).expanduser() if args.output_file else subtitle_path.with_suffix(".visual_event_hints.json")
    result = {
        "status": "created",
        "method": "subtitle_boundary_keyword_hints",
        "subtitle": str(subtitle_path),
        "cue_count": len(cues),
        "event_count": len(events),
        "min_gap_seconds": float(args.min_gap_seconds),
        "keyword_min_gap_seconds": float(args.keyword_min_gap_seconds),
        "keywords": keywords,
        "events": events,
    }
    write_json(output_file, result)
    print(f"Done. Visual subtitle hints: {output_file}")
    print("RESULT_JSON:" + json.dumps({
        "status": "created",
        "output_file": str(output_file),
        "cue_count": len(cues),
        "event_count": len(events),
    }, ensure_ascii=False))
    return 0


def parse_float_list(value: str) -> list[float]:
    items = []
    for raw in value.split(","):
        raw = raw.strip()
        if raw:
            items.append(float(raw))
    if not items:
        raise RuntimeError("Expected at least one numeric value.")
    return items


def parse_int_list(value: str) -> list[int]:
    items = []
    for raw in value.split(","):
        raw = raw.strip()
        if raw:
            items.append(int(raw))
    if not items:
        raise RuntimeError("Expected at least one integer value.")
    return items


def safe_grid_tag(*, coverage: float, min_gap: float, neighbors: int) -> str:
    coverage_part = f"{coverage:.3f}".rstrip("0").rstrip(".").replace(".", "p")
    gap_part = f"{min_gap:.3f}".rstrip("0").rstrip(".").replace(".", "p")
    return f"cov{coverage_part}_gap{gap_part}_n{neighbors}"


def create_visual_smart_grid(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir).expanduser()
    metadata_path = input_dir / "metadata.json"
    visual_dir = input_dir / "visual"
    grid_dir = Path(args.output_dir).expanduser() if args.output_dir else visual_dir / "smart_grid"
    ensure_dir(grid_dir)
    if not metadata_path.exists():
        raise RuntimeError(f"metadata.json does not exist: {metadata_path}")
    gold_path = Path(args.gold_events).expanduser()
    if not gold_path.exists():
        raise RuntimeError(f"Gold events file does not exist: {gold_path}")

    coverages = parse_float_list(args.coverage_fractions)
    gaps = parse_float_list(args.min_gap_seconds_values)
    neighbor_values = parse_int_list(args.event_neighbor_values)
    results = []

    for coverage in coverages:
        for min_gap in gaps:
            for neighbors in neighbor_values:
                tag = safe_grid_tag(
                    coverage=coverage,
                    min_gap=min_gap,
                    neighbors=neighbors,
                )
                selection_file = grid_dir / f"selected_{tag}.json"
                report_file = grid_dir / f"smart_report_{tag}.md"
                score_dir = grid_dir / f"score_{tag}"

                select_args = argparse.Namespace(
                    input_dir=str(input_dir),
                    policy=args.policy,
                    budget_frames=args.budget_frames,
                    baseline_seconds=args.baseline_seconds,
                    min_gap_seconds=min_gap,
                    event_neighbor_frames=neighbors,
                    coverage_fraction=coverage,
                    timeout=args.timeout,
                    ffmpeg_location=args.ffmpeg_location,
                    event_hints=args.event_hints,
                    selection_file=str(selection_file),
                    report_file=str(report_file),
                )
                create_visual_smart_select(select_args)

                score_args = argparse.Namespace(
                    selection=str(selection_file),
                    gold_events=str(gold_path),
                    default_tolerance=args.default_tolerance,
                    output_dir=str(score_dir),
                )
                score_visual_smart_selection(score_args)
                score_json = score_dir / "visual_smart_score.json"
                score_data = json.loads(score_json.read_text(encoding="utf-8-sig"))
                selection_data = json.loads(selection_file.read_text(encoding="utf-8-sig"))
                selection_policy = selection_data.get("policy", {})
                if not isinstance(selection_policy, dict):
                    selection_policy = {}
                results.append({
                    "tag": tag,
                    "policy": selection_policy.get("policy", args.policy),
                    "budget_frames": selection_policy.get("budget_frames", args.budget_frames),
                    "baseline_seconds": selection_policy.get("baseline_seconds", args.baseline_seconds),
                    "effective_baseline_seconds": selection_policy.get("effective_baseline_seconds"),
                    "coverage_fraction": selection_policy.get("coverage_fraction", coverage),
                    "min_gap_seconds": selection_policy.get("min_gap_seconds", min_gap),
                    "event_neighbor_frames": selection_policy.get("event_neighbor_frames", neighbors),
                    "selected_count": score_data.get("selected_count"),
                    "gold_event_count": score_data.get("gold_event_count"),
                    "covered_event_count": score_data.get("covered_event_count"),
                    "event_recall": score_data.get("event_recall"),
                    "selection_file": str(selection_file),
                    "report_file": str(report_file),
                    "score_file": str(score_json),
                })

    results.sort(
        key=lambda item: (
            float(item.get("event_recall") or 0.0),
            int(item.get("covered_event_count") or 0),
            -float(item.get("coverage_fraction") or 0.0),
        ),
        reverse=True,
    )
    summary = {
        "status": "scored",
        "method": "smart_selection_grid",
        "input_dir": str(input_dir),
        "gold_events": str(gold_path),
        "policy": args.policy,
        "budget_frames": args.budget_frames,
        "candidate_count": len(results),
        "best": results[0] if results else None,
        "results": results,
    }
    summary_json = grid_dir / "visual_smart_grid.json"
    summary_md = grid_dir / "visual_smart_grid.md"
    write_json(summary_json, summary)

    lines = [
        "# Visual Smart Grid",
        "",
        f"- Input: `{input_dir}`",
        f"- Gold events: `{gold_path}`",
        f"- Policy: `{args.policy}`",
        f"- Budget frames: `{args.budget_frames}`",
        f"- Candidates: `{len(results)}`",
        "",
        "## Ranked Results",
        "",
        "| Rank | Recall | Covered | Coverage | Gap | Neighbors | Selection |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rank, item in enumerate(results, start=1):
        lines.append(
            "| {rank} | {recall:.3f} | {covered}/{gold} | {coverage:.3f} | {gap:.3f} | {neighbors} | `{selection}` |".format(
                rank=rank,
                recall=float(item.get("event_recall") or 0.0),
                covered=int(item.get("covered_event_count") or 0),
                gold=int(item.get("gold_event_count") or 0),
                coverage=float(item.get("coverage_fraction") or 0.0),
                gap=float(item.get("min_gap_seconds") or 0.0),
                neighbors=int(item.get("event_neighbor_frames") or 0),
                selection=item.get("selection_file", ""),
            )
        )
    write_text(summary_md, "\n".join(lines).strip() + "\n")

    metadata = load_metadata(metadata_path)
    metadata.setdefault("files", {})
    metadata["files"]["visual_smart_grid_json"] = str(summary_json)
    metadata["files"]["visual_smart_grid_md"] = str(summary_md)
    metadata["visual_smart_grid"] = {
        "status": "scored",
        "policy": args.policy,
        "candidate_count": len(results),
        "best": results[0] if results else None,
    }
    write_json(metadata_path, metadata)
    print(f"Done. Visual smart grid: {summary_json}")
    print("RESULT_JSON:" + json.dumps(metadata["visual_smart_grid"], ensure_ascii=False))
    return 0


def build_visual_model_prompt(
    metadata: dict[str, Any],
    selected_frames: list[dict[str, Any]],
    *,
    mode: str,
) -> str:
    lines = [
        "# Visual Notes Generation",
        "",
        f"Source: `{metadata.get('source', '')}`",
        f"Mode: `{mode}`",
        f"Frame count in request: {len(selected_frames)}",
        "",
        "You are analyzing sparse video frames for tutorial/workflow understanding.",
        "Use only visible evidence in the attached frames. Keep uncertainty explicit.",
        "Do not identify or describe blurred faces; ignore face identity and focus on UI, actions, text, diagrams, gestures, and scene changes.",
        "",
        "## Frames",
        "",
    ]
    for frame in selected_frames:
        lines.append(
            f"- Frame {frame.get('index')} at {frame.get('timestamp')}: `{frame.get('file')}`"
        )
    lines.extend([
        "",
        "## Output",
        "",
        "Write Markdown using this exact structure:",
        "",
        "# Visual Notes",
        "",
        "## Visual Summary",
        "",
        "- Main visible flow:",
        "- Most important UI/action evidence:",
        "- What this adds beyond transcript-only analysis:",
        "",
        "## Frame Timeline",
        "",
        "For each frame, include:",
        "",
        "- Visible state:",
        "- On-screen text/OCR:",
        "- Action or transition evidence:",
        "- Tutorial/workflow value:",
        "- Confidence: high | medium | low",
        "- Needs denser sampling: no | yes, range:",
        "",
        "## Cross-Modal Alignment",
        "",
        "- Visual evidence that clarifies transcript/audio notes:",
        "- Visual evidence missing from transcript/audio notes:",
        "- Conflicts or uncertain points:",
        "",
        "## Follow-Up Sampling",
        "",
        "| Range | Why sample denser? | Suggested interval |",
        "|---|---|---|",
        "",
        "## Reusable Documentation Notes",
        "",
        "- UI labels or exact visible terms worth preserving:",
        "- Steps that should become docs/tutorial instructions:",
        "- Screenshots or frames worth using as references:",
    ])
    if mode == "reverse":
        lines.extend([
            "",
            "## Reverse-Parsing Emphasis",
            "",
            "Infer likely tutorial actions and intent only when the frame evidence supports it.",
            "Prefer concrete UI state and visible text over broad speculation.",
        ])
    return "\n".join(lines).strip() + "\n"


def image_data_url(path: Path) -> str:
    mime_type = image_mime_type(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def analyze_visual_openai(
    prompt: str,
    selected_frames: list[dict[str, Any]],
    args: argparse.Namespace,
) -> str:
    try:
        from openai import AzureOpenAI, OpenAI
    except ImportError as exc:
        raise RuntimeError("Python package 'openai' is not installed.") from exc

    content: list[dict[str, Any]] = [{"type": "input_text", "text": prompt}]
    for frame in selected_frames:
        path = Path(str(frame["resolved_file"]))
        if not path.exists():
            raise RuntimeError(f"Frame file does not exist: {path}")
        if path.stat().st_size > args.max_image_bytes:
            raise RuntimeError(f"Frame exceeds --max-image-bytes: {path}")
        content.append({
            "type": "input_image",
            "image_url": image_data_url(path),
            "detail": args.image_detail,
        })

    if args.openai_provider == "azure":
        api_key = os.environ.get("AZURE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        if not api_key:
            raise RuntimeError("AZURE_OPENAI_API_KEY is not set.")
        if base_url:
            client = OpenAI(api_key=api_key, base_url=normalize_azure_v1_base_url(base_url))
        elif endpoint and is_azure_v1_base_url(endpoint):
            client = OpenAI(api_key=api_key, base_url=normalize_azure_v1_base_url(endpoint))
        elif endpoint:
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version=args.azure_api_version,
            )
        else:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BASE_URL is not set.")
    else:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set.")
        client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=args.openai_model,
        input=[{"role": "user", "content": content}],
        max_output_tokens=args.max_output_tokens,
    )
    output_text = getattr(response, "output_text", "")
    return str(output_text or response).strip()


def write_visual_notes_template(
    output_dir: Path,
    metadata: dict[str, Any],
    *,
    mode: str,
    output_file: Path | None = None,
    metadata_key: str = "visual_notes_template",
) -> Path:
    visual_dir = output_dir / "visual"
    frame_index = load_visual_frame_index(output_dir, metadata)
    notes_path = output_file or visual_dir / "visual_notes_template.md"
    lines = [
        "# Visual Notes",
        "",
        f"Source: `{metadata.get('source', '')}`",
        f"Mode: `{mode}`",
        f"Frame count: {len(frame_index)}",
        "",
        "## Use",
        "",
        "- Fill this from visible evidence only.",
        "- Keep uncertainty explicit; use `unclear` instead of guessing.",
        "- Record what the visual pass adds beyond transcript/audio notes.",
        "- Mark intervals that need denser sampling or a short clip.",
        "",
        "## Visual Summary",
        "",
        "- Main visible flow:",
        "- Most important UI/action evidence:",
        "- What this adds beyond transcript-only analysis:",
        "",
        "## Frame Timeline",
        "",
    ]

    if not frame_index:
        lines.extend([
            "- No frames found. Regenerate the visual pack or check `visual/frames.json`.",
            "",
        ])

    for item in frame_index:
        index = item.get("index", "?")
        timestamp = item.get("timestamp_seconds")
        frame_file = item.get("file", "")
        lines.extend([
            f"### Frame {index} - {format_timestamp(timestamp)}",
            "",
            f"- File: `{frame_file}`",
            "- Visible state:",
            "- On-screen text/OCR:",
            "- Action or transition evidence:",
            "- Tutorial/workflow value:",
            "- Confidence: high | medium | low",
            "- Needs denser sampling: no | yes, range:",
            "",
        ])

    lines.extend([
        "## Cross-Modal Alignment",
        "",
        "- Matching transcript/audio range:",
        "- Visual evidence that clarifies the transcript:",
        "- Visual evidence missing from the transcript:",
        "- Conflicts or uncertain points:",
        "",
        "## Follow-Up Sampling",
        "",
        "| Range | Why sample denser? | Suggested interval |",
        "|---|---|---|",
        "|  |  |  |",
        "",
        "## Reusable Documentation Notes",
        "",
        "- UI labels or exact visible terms worth preserving:",
        "- Steps that should become docs/tutorial instructions:",
        "- Screenshots or frames worth using as references:",
    ])
    write_text(notes_path, "\n".join(lines).strip() + "\n")
    metadata.setdefault("files", {})
    metadata["files"][metadata_key] = str(notes_path)
    return notes_path


def create_visual_notes(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir).expanduser()
    metadata_path = input_dir / "metadata.json"
    if not metadata_path.exists():
        raise RuntimeError(f"metadata.json does not exist: {metadata_path}")
    metadata = load_metadata(metadata_path)
    output_file = Path(args.output_file).expanduser() if args.output_file else input_dir / "visual" / "visual_notes.md"
    if output_file.exists() and not args.force:
        raise RuntimeError(f"Output file already exists. Use --force to overwrite: {output_file}")
    notes_path = write_visual_notes_template(
        input_dir,
        metadata,
        mode=str(metadata.get("mode", args.visual_mode)),
        output_file=output_file,
        metadata_key="visual_notes",
    )
    metadata.setdefault("files", {})
    if metadata["files"].get("visual_notes_template") == str(notes_path):
        del metadata["files"]["visual_notes_template"]
    write_json(metadata_path, metadata)
    print(f"Done. Visual notes: {notes_path}")
    print("RESULT_JSON:" + json.dumps({"visual_notes": str(notes_path)}, ensure_ascii=False))
    return 0


def create_visual_analysis(args: argparse.Namespace) -> int:
    settings = visual_analyze_settings(args)
    args.max_frames = int(settings["max_frames"])
    args.max_output_tokens = int(settings["max_output_tokens"])
    args.image_detail = str(settings["image_detail"])
    input_dir = Path(args.input_dir).expanduser()
    metadata_path = input_dir / "metadata.json"
    visual_dir = input_dir / "visual"
    logs_dir = input_dir / "logs"
    ensure_dir(visual_dir)
    ensure_dir(logs_dir)
    if not metadata_path.exists():
        raise RuntimeError(f"metadata.json does not exist: {metadata_path}")
    if args.max_frames <= 0:
        raise RuntimeError("--max-frames must be greater than 0.")
    if args.max_image_bytes <= 0:
        raise RuntimeError("--max-image-bytes must be greater than 0.")
    if args.max_output_tokens <= 0:
        raise RuntimeError("--max-output-tokens must be greater than 0.")

    metadata = load_metadata(metadata_path)
    frame_index, frame_selection_source = visual_request_frame_index(
        input_dir,
        metadata,
        frame_selection=getattr(args, "frame_selection", "smart"),
        selection_file=getattr(args, "selection_file", None),
    )
    if not frame_index:
        raise RuntimeError("No frames found in metadata or visual/frames.json.")
    selected_frames = select_visual_frames(input_dir, frame_index, args.max_frames)
    missing = [frame["resolved_file"] for frame in selected_frames if not frame.get("exists")]
    if missing:
        raise RuntimeError("Frame file(s) missing: " + ", ".join(str(item) for item in missing))

    mode = str(metadata.get("mode", args.visual_mode))
    prompt = build_visual_model_prompt(metadata, selected_frames, mode=mode)
    prompt_path = visual_dir / "visual_model_prompt.md"
    request_path = visual_dir / "visual_model_request.json"
    output_file = Path(args.output_file).expanduser() if args.output_file else visual_dir / "visual_notes_model.md"
    write_text(prompt_path, prompt)
    request_data = {
        "engine": args.engine,
        "mode": mode,
        "visual_preset": settings["preset"],
        "frame_selection": frame_selection_source,
        "frame_count": len(selected_frames),
        "max_frames": args.max_frames,
        "image_detail": args.image_detail,
        "max_output_tokens": args.max_output_tokens,
        "frames": selected_frames,
        "prompt_file": str(prompt_path),
        "output_file": str(output_file),
    }
    if args.engine == "openai":
        request_data["model"] = args.openai_model
        request_data["openai_provider"] = args.openai_provider
        if args.openai_provider == "azure":
            request_data.update(describe_azure_openai_mode() or {})
            if request_data.get("azure_mode") != "v1_base_url":
                request_data["azure_api_version"] = args.azure_api_version
    write_json(request_path, request_data)

    metadata.setdefault("files", {})
    metadata["files"]["visual_model_prompt"] = str(prompt_path)
    metadata["files"]["visual_model_request"] = str(request_path)
    metadata["visual_analysis"] = {
        "engine": args.engine,
        "mode": mode,
        "visual_preset": settings["preset"],
        "frame_selection": frame_selection_source,
        "frame_count": len(selected_frames),
        "status": "prompt_ready" if args.engine == "none" else "started",
    }
    write_json(metadata_path, metadata)

    if args.engine == "none":
        print(f"Done. Visual model prompt: {prompt_path}")
        print("RESULT_JSON:" + json.dumps(metadata["visual_analysis"], ensure_ascii=False))
        return 0

    try:
        if args.engine == "openai":
            notes = analyze_visual_openai(prompt, selected_frames, args)
        else:
            raise RuntimeError(f"Unsupported visual analysis engine: {args.engine}")

        if not notes:
            raise RuntimeError("Provider returned an empty visual analysis.")
        write_text(output_file, notes.rstrip() + "\n")
        metadata["files"]["visual_notes_model"] = str(output_file)
        metadata["visual_analysis"]["status"] = "completed"
        metadata["visual_analysis"]["output_file"] = str(output_file)
        write_json(metadata_path, metadata)
        print(f"Done. Visual analysis: {output_file}")
        print("RESULT_JSON:" + json.dumps(metadata["visual_analysis"], ensure_ascii=False))
        return 0
    except Exception as exc:
        raw_error_text = str(exc)
        error_text = sanitize_error_text(raw_error_text)
        write_text(logs_dir / "visual_analyze_error.txt", error_text + "\n")
        metadata["visual_analysis"]["status"] = "failed"
        metadata["visual_analysis"]["error"] = error_text
        metadata["files"]["visual_analyze_error"] = str(logs_dir / "visual_analyze_error.txt")
        write_json(metadata_path, metadata)
        print(f"ERROR: {error_text}", file=sys.stderr)
        print_diagnosis(raw_error_text)
        print("RESULT_JSON:" + json.dumps(metadata["visual_analysis"], ensure_ascii=False))
        return 1


def create_visual_agent_task(args: argparse.Namespace) -> int:
    input_dir = Path(args.input_dir).expanduser()
    metadata_path = input_dir / "metadata.json"
    visual_dir = input_dir / "visual"
    ensure_dir(visual_dir)
    if not metadata_path.exists():
        raise RuntimeError(f"metadata.json does not exist: {metadata_path}")
    if args.max_frames <= 0:
        raise RuntimeError("--max-frames must be greater than 0.")

    metadata = load_metadata(metadata_path)
    frame_index, frame_selection_source = visual_request_frame_index(
        input_dir,
        metadata,
        frame_selection=getattr(args, "frame_selection", "smart"),
        selection_file=getattr(args, "selection_file", None),
    )
    if not frame_index:
        raise RuntimeError("No frames found in metadata or visual/frames.json.")
    selected_frames = select_visual_frames(input_dir, frame_index, args.max_frames)
    missing = [frame["resolved_file"] for frame in selected_frames if not frame.get("exists")]
    if missing:
        raise RuntimeError("Frame file(s) missing: " + ", ".join(str(item) for item in missing))

    mode = str(metadata.get("mode", args.visual_mode))
    output_file = Path(args.output_file).expanduser() if args.output_file else visual_dir / "visual_notes_agent.md"
    task_path = visual_dir / "visual_agent_task.md"
    lines = [
        "# Visual Agent Task",
        "",
        f"Source: `{metadata.get('source', '')}`",
        f"Mode: `{mode}`",
        f"Frame count: {len(selected_frames)}",
        f"Output file: `{output_file}`",
        "",
        "## Instructions",
        "",
        "- Open each frame with the local image viewer/tool available to the agent.",
        "- Ignore blurred faces and do not identify people.",
        "- Use only visible evidence; mark uncertainty as `unclear`.",
        "- Write structured notes to the output file using the Visual Notes shape.",
        "- After writing notes, update `metadata.json` with `visual_analysis.status = agent_completed`.",
        "",
        "## Frames",
        "",
    ]
    for frame in selected_frames:
        lines.append(
            f"- Frame {frame.get('index')} at {frame.get('timestamp')}: `{frame.get('resolved_file')}`"
        )
    lines.extend([
        "",
        "## Required Output Shape",
        "",
        "- Visual Summary",
        "- Frame Timeline",
        "- Cross-Modal Alignment",
        "- Follow-Up Sampling",
        "- Reusable Documentation Notes",
    ])
    write_text(task_path, "\n".join(lines).strip() + "\n")

    metadata.setdefault("files", {})
    metadata["files"]["visual_agent_task"] = str(task_path)
    metadata["files"]["visual_notes_agent"] = str(output_file)
    metadata["visual_analysis"] = {
        "engine": "agent",
        "mode": mode,
        "frame_selection": frame_selection_source,
        "frame_count": len(selected_frames),
        "status": "agent_ready",
        "task_file": str(task_path),
        "output_file": str(output_file),
    }
    write_json(metadata_path, metadata)
    print(f"Done. Visual agent task: {task_path}")
    print("RESULT_JSON:" + json.dumps(metadata["visual_analysis"], ensure_ascii=False))
    return 0


def create_visual_pack(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
    visual_dir = output_dir / "visual"
    frames_dir = visual_dir / "frames"
    logs_dir = output_dir / "logs"
    ensure_dir(frames_dir)
    ensure_dir(logs_dir)

    source = Path(args.input).expanduser()
    metadata: dict[str, Any] = {
        "source": str(source),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strategy": "visual-pack",
        "status": "started",
        "mode": args.visual_mode,
        "sampling": {
            "preset": args.visual_preset,
            "visual_kind": args.visual_kind,
            "start": args.start,
            "duration": args.duration,
            "interval": args.interval,
            "max_frames": args.max_frames,
            "width": args.width,
        },
        "files": {},
    }

    try:
        if not source.exists():
            raise RuntimeError(f"Input video does not exist: {source}")
        if args.start is not None and args.start < 0:
            raise RuntimeError("--start must be greater than or equal to 0.")
        if args.duration is not None and args.duration <= 0:
            raise RuntimeError("--duration must be greater than 0.")
        ffmpeg_command = resolve_ffmpeg(args.ffmpeg_location)
        if not ffmpeg_command:
            if args.ffmpeg_location:
                raise RuntimeError(
                    "ffmpeg could not run from --ffmpeg-location. If this is a "
                    "Windows app execution alias or WinGet Links shim, pass the "
                    "real ffmpeg.exe path or its containing directory."
                )
            raise RuntimeError(
                "ffmpeg is required to sample video frames. If Windows points "
                "ffmpeg to a WinGet Links shim, pass a real ffmpeg.exe with "
                "--ffmpeg-location."
            )
        source_duration = probe_video_duration(ffmpeg_command, source)
        settings = visual_pack_settings(args, source_duration=source_duration)
        args.interval = float(settings["interval"])
        args.max_frames = int(settings["max_frames"])
        args.width = int(settings["width"])
        metadata["sampling"].update(settings)
        if args.interval <= 0:
            raise RuntimeError("--interval must be greater than 0.")
        if args.max_frames <= 0:
            raise RuntimeError("--max-frames must be greater than 0.")
        if args.width < 0:
            raise RuntimeError("--width must be greater than or equal to 0.")
        if args.jpeg_quality < 2 or args.jpeg_quality > 31:
            raise RuntimeError("--jpeg-quality must be between 2 and 31.")
        if args.timeout <= 0:
            raise RuntimeError("--timeout must be greater than 0.")

        frame_pattern = frames_dir / "frame_%04d.jpg"
        fps = 1 / float(args.interval)
        cmd = [ffmpeg_command]
        if args.start is not None:
            cmd.extend(["-ss", str(args.start)])
        cmd.extend(["-i", str(source)])
        if args.duration is not None:
            cmd.extend(["-t", str(args.duration)])
        filters = [f"fps={fps}"]
        if args.width:
            filters.append(f"scale={args.width}:-1")
        cmd.extend([
            "-vf",
            ",".join(filters),
            "-frames:v",
            str(args.max_frames),
            "-q:v",
            str(args.jpeg_quality),
            str(frame_pattern),
            "-y",
        ])

        result = run_cmd(cmd, timeout=args.timeout)
        write_text(logs_dir / "ffmpeg_visual.stdout.txt", result.stdout)
        write_text(logs_dir / "ffmpeg_visual.stderr.txt", result.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg frame sampling failed: {result.stderr[-800:]}")

        frames = sorted(frames_dir.glob("frame_*.jpg"))
        if not frames:
            raise RuntimeError("Frame sampling completed but no frames were written.")

        frame_index: list[dict[str, Any]] = []
        start = float(args.start or 0)
        interval = float(args.interval)
        for index, frame in enumerate(frames):
            timestamp = start + index * interval
            frame_index.append({
                "index": index + 1,
                "timestamp_seconds": round(timestamp, 3),
                "file": str(frame),
            })

        write_json(visual_dir / "frames.json", {"frames": frame_index})
        metadata["status"] = "visual_pack_ready"
        metadata["frames"] = [item["file"] for item in frame_index]
        metadata["frame_index"] = frame_index
        metadata["files"]["frames_json"] = str(visual_dir / "frames.json")
        write_visual_prompt(output_dir, metadata, mode=args.visual_mode)
        write_visual_notes_template(output_dir, metadata, mode=args.visual_mode)
        write_json(output_dir / "metadata.json", metadata)
        print(f"Done. Output directory: {output_dir}")
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 0
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = str(exc)
        write_json(output_dir / "metadata.json", metadata)
        print(f"ERROR: {exc}", file=sys.stderr)
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 1


def create_visual_local(args: argparse.Namespace) -> int:
    """Create a local-only visual pack and agent task without provider calls."""
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
    args.output_dir = str(output_dir)
    pack_status = create_visual_pack(args)
    if pack_status != 0:
        return pack_status

    agent_args = argparse.Namespace(
        input_dir=str(output_dir),
        output_file=args.agent_output_file,
        visual_mode=args.visual_mode,
        max_frames=args.agent_max_frames,
    )
    return create_visual_agent_task(agent_args)


def fetch_subtitles(url: str, output_dir: Path, args: argparse.Namespace) -> tuple[str | None, dict[str, Any]]:
    logs_dir = output_dir / "logs"
    ensure_dir(logs_dir)
    attempts: list[dict[str, Any]] = []
    direct_probe: dict[str, Any] | None = None

    def with_attempts(debug: dict[str, Any]) -> dict[str, Any]:
        result = dict(debug)
        result["attempts"] = [dict(attempt) for attempt in attempts]
        if direct_probe is not None:
            result["bilibili_direct_probe"] = direct_probe
        return result

    def try_subtitle_languages(sub_langs: str, log_label: str) -> tuple[str | None, dict[str, Any]]:
        safe_label = re.sub(r"[^A-Za-z0-9_.-]+", "_", log_label).strip("_") or "default"
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            cmd = ytdlp_base_cmd(url, args)
            requested_page = bilibili_page_number(url) if is_bilibili(url) else None
            cmd.extend([
                "--write-auto-sub",
                "--write-sub",
                "--sub-langs",
                sub_langs,
                "--sub-format",
                "vtt/srt/best",
                "--skip-download",
                "-o",
                str(tmpdir / "subtitle.%(ext)s"),
                url,
            ])
            # Browser-cookie routes cannot safely expose cookies to the direct
            # HTTP probe. Scope yt-dlp itself to the requested multipart item
            # so it cannot reinterpret ?p=N as P1.
            if requested_page:
                cmd.extend(["--yes-playlist", "--playlist-items", str(requested_page)])
            else:
                cmd.append("--no-playlist")
            result = run_cmd(cmd, timeout=args.subtitle_timeout)
            write_text(logs_dir / f"yt_dlp_subtitles_{safe_label}.stdout.txt", result.stdout)
            write_text(logs_dir / f"yt_dlp_subtitles_{safe_label}.stderr.txt", result.stderr)

            files = sorted(list(tmpdir.glob("subtitle*.*")))
            subtitle_files = sorted(
                [p for p in files if p.suffix.lower() in {".vtt", ".srt"}],
                key=lambda path: subtitle_priority(path, sub_langs),
            )
            debug = {
                "sub_langs": sub_langs,
                "returncode": result.returncode,
                "files": [p.name for p in files],
                "stdout_tail": result.stdout[-1000:],
                "stderr_tail": result.stderr[-1000:],
            }
            if not subtitle_files:
                return None, debug

            copied: list[str] = []
            selected_transcript: str | None = None
            selected_file = ""
            for subtitle in subtitle_files:
                text = parse_subtitle_file(subtitle)
                if text:
                    target = output_dir / subtitle.name
                    shutil.copy2(subtitle, target)
                    copied.append(str(target))
                    if selected_transcript is None:
                        selected_transcript = text
                        selected_file = subtitle.name
            debug["copied"] = copied
            if selected_file:
                debug["selected_file"] = selected_file
            return selected_transcript, debug

    # Reject malformed explicit page selectors before any route can reinterpret
    # them as the default (P1) selection.
    if is_bilibili(url):
        _requested_page, page_request_error = bilibili_page_request(url)
        if page_request_error:
            direct_probe = {
                "method": "bilibili_page_api_probe",
                "bvid": extract_bvid(url),
                "requested_page": None,
                "status": page_request_error,
                "auth": "none",
                "subtitle_count": 0,
                "downloaded": [],
            }
            return None, with_attempts({
                "sub_langs": "bilibili-direct",
                "returncode": 1,
                "files": [],
                "stdout_tail": "",
                "stderr_tail": "",
                "status": page_request_error,
            })

    # A selected browser route is authenticated only inside yt-dlp. Running the
    # direct HTTP probe first would be anonymous and would violate route replay.
    if is_bilibili(url) and args.cookies_browser == "none":
        transcript, direct_probe = direct_bilibili_subtitle_probe(url, output_dir, args)
        if transcript:
            return transcript, with_attempts({
                "sub_langs": "bilibili-direct",
                "returncode": 0,
                "files": [direct_probe.get("selected_file", "")],
                "stdout_tail": "",
                "stderr_tail": "",
            })
        # An explicit multipart request has a stronger correctness contract
        # than yt-dlp's generic URL fallback. Continuing here could download
        # P1 after the direct API has already established that P=N is invalid,
        # missing, or has no subtitles.
        if direct_probe.get("status") in {
            "invalid_requested_page",
            "requested_page_not_found",
            "no_subtitle_for_requested_page",
        }:
            return None, with_attempts({
                "sub_langs": "bilibili-direct",
                "returncode": 1,
                "files": [],
                "stdout_tail": "",
                "stderr_tail": "",
                "status": direct_probe.get("status"),
            })

    transcript, debug = try_subtitle_languages(args.sub_langs, "all")
    attempts.append(debug)
    if transcript:
        write_text(logs_dir / "yt_dlp_subtitles.stdout.txt", debug.get("stdout_tail", ""))
        write_text(logs_dir / "yt_dlp_subtitles.stderr.txt", debug.get("stderr_tail", ""))
        return transcript, with_attempts(debug)

    languages = [
        item.strip()
        for item in args.sub_langs.split(",")
        if item.strip()
    ]
    if len(languages) > 1:
        for language in languages:
            transcript, debug = try_subtitle_languages(language, language)
            attempts.append(debug)
            if transcript:
                write_text(logs_dir / "yt_dlp_subtitles.stdout.txt", debug.get("stdout_tail", ""))
                write_text(logs_dir / "yt_dlp_subtitles.stderr.txt", debug.get("stderr_tail", ""))
                return transcript, with_attempts(debug)

    debug = attempts[-1] if attempts else {
        "returncode": 1,
        "files": [],
        "stdout_tail": "",
        "stderr_tail": "",
    }
    write_text(logs_dir / "yt_dlp_subtitles.stdout.txt", debug.get("stdout_tail", ""))
    write_text(logs_dir / "yt_dlp_subtitles.stderr.txt", debug.get("stderr_tail", ""))
    return None, with_attempts(debug)


def create_bilibili_subtitle_probe(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
    ensure_dir(output_dir)
    metadata = {
        "source": args.input,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "strategy": "bilibili-subtitle-probe",
        "status": "started",
        "files": {},
    }
    try:
        transcript, debug = direct_bilibili_subtitle_probe(args.input, output_dir, args)
        metadata["probe"] = debug
        if transcript:
            transcript_path = output_dir / "transcript.txt"
            write_text(transcript_path, transcript + "\n")
            metadata["status"] = "transcript_from_bilibili_direct"
            metadata["files"]["transcript"] = str(transcript_path)
        else:
            metadata["status"] = "no_direct_bilibili_subtitles"
        write_json(output_dir / "metadata.json", metadata)
        print(f"Done. Output directory: {output_dir}")
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 0
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = str(exc)
        write_json(output_dir / "metadata.json", metadata)
        print(f"ERROR: {exc}", file=sys.stderr)
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 1


def download_audio(source: str, output_dir: Path, args: argparse.Namespace) -> Path:
    logs_dir = output_dir / "logs"
    ensure_dir(logs_dir)
    if is_url(source):
        cmd = ytdlp_base_cmd(source, args)
        cmd.extend([
            "-x",
            "--audio-format",
            "mp3",
            "--audio-quality",
            "32K",
            "--no-playlist",
            "-o",
            str(output_dir / "audio.%(ext)s"),
            source,
        ])
        result = run_cmd(cmd, timeout=args.audio_timeout)
        write_text(logs_dir / "yt_dlp_audio.stdout.txt", result.stdout)
        write_text(logs_dir / "yt_dlp_audio.stderr.txt", result.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp audio download failed: {result.stderr[-800:]}")
        audio_files = sorted(output_dir.glob("audio.*"))
        if not audio_files:
            raise RuntimeError("Audio download completed but no audio file was found.")
        return audio_files[0]

    input_path = Path(source).expanduser()
    if not input_path.exists():
        raise RuntimeError(f"Input file does not exist: {input_path}")
    if input_path.suffix.lower() in {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg"}:
        target = output_dir / input_path.name
        shutil.copy2(input_path, target)
        return target

    ffmpeg_command = resolve_ffmpeg(args.ffmpeg_location)
    if not ffmpeg_command:
        raise RuntimeError("ffmpeg is required to extract audio from local video files.")
    audio_path = output_dir / "audio.mp3"
    cmd = [
        ffmpeg_command,
        "-i",
        str(input_path),
        "-vn",
        "-ar",
        "16000",
        "-ac",
        "1",
        "-ab",
        "32k",
        "-f",
        "mp3",
        str(audio_path),
        "-y",
    ]
    result = run_cmd(cmd, timeout=args.audio_timeout)
    write_text(logs_dir / "ffmpeg.stdout.txt", result.stdout)
    write_text(logs_dir / "ffmpeg.stderr.txt", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr[-800:]}")
    return audio_path


def transcribe_openai(audio_path: Path, args: argparse.Namespace) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Python package 'openai' is not installed.") from exc
    client = OpenAI(api_key=api_key, timeout=max(30, int(args.audio_timeout)), max_retries=2)
    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=args.openai_model,
            file=audio_file,
            response_format="text",
        )
    return str(result).strip()


def write_notes(output_dir: Path, metadata: dict[str, Any], transcript: str | None) -> None:
    lines = [
        "# Video Intake Notes",
        "",
        f"- Source: `{metadata.get('source')}`",
        f"- Status: `{metadata.get('status')}`",
        f"- Strategy: `{metadata.get('strategy')}`",
        "",
        "## Use This Transcript To Analyze",
        "",
        "- How the tutorial opens and lowers beginner anxiety.",
        "- The setup path and checkpoints.",
        "- Common issues surfaced by the author.",
        "- Phrases or structures worth adapting into project documentation.",
        "- Missing pieces in our own onboarding.",
    ]
    if transcript:
        lines.extend([
            "",
            "## Transcript Preview",
            "",
            transcript[:1200],
        ])
    write_text(output_dir / "notes.md", "\n".join(lines).strip() + "\n")


def intake(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
    ensure_dir(output_dir)

    metadata: dict[str, Any] = {
        "source": args.input,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "engine": args.engine,
        "cookies_browser": args.cookies_browser,
        "cookies_file": str(Path(args.cookies_file).expanduser()) if args.cookies_file else "",
        "strategy": "subtitle-first",
        "status": "started",
        "files": {},
    }

    auth_route = apply_known_bilibili_auth_route(args)
    metadata["auth_route"] = auth_route
    metadata["cookies_browser"] = args.cookies_browser
    if args.cookies_file:
        metadata["cookies_file"] = str(Path(args.cookies_file).expanduser())

    transcript: str | None = None
    subtitle_debug: dict[str, Any] | None = None

    try:
        if is_url(args.input) and not args.no_subtitles:
            print("Step 1: trying existing subtitles")
            transcript, subtitle_debug = fetch_subtitles(args.input, output_dir, args)
            metadata["subtitle_debug"] = subtitle_debug
            if transcript:
                metadata["status"] = "transcript_from_subtitles"
                metadata["files"]["transcript"] = str(output_dir / "transcript.txt")
                write_text(output_dir / "transcript.txt", transcript + "\n")
                if is_bilibili(args.input) and not getattr(args, "no_saved_auth_route", False):
                    remember_auth_route(
                        "bilibili",
                        cookies_file=args.cookies_file,
                        cookies_browser=args.cookies_browser,
                        route_id=auth_route.get("route_id"),
                    )
                print("Subtitles found. Transcript saved.")

        if not transcript:
            if args.engine == "none":
                metadata["status"] = subtitle_failure_status(args.input, args, subtitle_debug)
                if metadata["status"] == "auth_route_expired_or_rejected":
                    mark_auth_route_rejected("bilibili", auth_route.get("route_id"))
                write_notes(output_dir, metadata, None)
                write_json(output_dir / "metadata.json", metadata)
                print("No usable subtitles were found.")
                print("Next options:")
                for option in subtitle_next_options(
                    subtitle_debug,
                    status=metadata["status"],
                    auth_route=auth_route,
                ):
                    print(f"- {option}")
                print(f"Output directory: {output_dir}")
                print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
                return 0

            print("Step 2: downloading or extracting audio")
            audio_path = download_audio(args.input, output_dir, args)
            metadata["files"]["audio"] = str(audio_path)
            print(f"Audio ready: {audio_path}")

            print(f"Step 3: transcribing with {args.engine}")
            if args.engine == "openai":
                transcript = transcribe_openai(audio_path, args)
            else:
                raise RuntimeError(f"Unsupported engine: {args.engine}")
            metadata["status"] = f"transcript_from_{args.engine}"
            metadata["files"]["transcript"] = str(output_dir / "transcript.txt")
            write_text(output_dir / "transcript.txt", transcript + "\n")

        if transcript and not args.no_analysis_pack:
            write_analysis_pack(
                output_dir,
                metadata,
                transcript,
                mode=args.analysis_mode,
                chunk_chars=args.chunk_chars,
            )

        write_notes(output_dir, metadata, transcript)
        write_json(output_dir / "metadata.json", metadata)
        print(f"Done. Output directory: {output_dir}")
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 0
    except Exception as exc:
        metadata["status"] = "failed"
        metadata["error"] = str(exc)
        write_json(output_dir / "metadata.json", metadata)
        print(f"ERROR: {exc}", file=sys.stderr)
        print_diagnosis(str(exc))
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 1


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def analyze(args: argparse.Namespace) -> int:
    try:
        if args.input_dir:
            input_dir = Path(args.input_dir).expanduser()
            transcript_path = input_dir / "transcript.txt"
            source_metadata = load_metadata(input_dir / "metadata.json")
        elif args.transcript:
            transcript_path = Path(args.transcript).expanduser()
            source_metadata = {}
        else:
            raise RuntimeError("Use --input-dir or --transcript.")

        if not transcript_path.exists():
            raise RuntimeError(f"Transcript file does not exist: {transcript_path}")

        output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
        ensure_dir(output_dir)
        transcript = transcript_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not transcript:
            raise RuntimeError(f"Transcript file is empty: {transcript_path}")

        metadata: dict[str, Any] = {
            "source": args.source or source_metadata.get("source") or str(transcript_path),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "strategy": "analysis-pack",
            "status": "analysis_pack_ready",
            "files": {
                "source_transcript": str(transcript_path),
                "transcript": str(output_dir / "transcript.txt"),
            },
        }
        write_text(output_dir / "transcript.txt", transcript + "\n")
        write_analysis_pack(
            output_dir,
            metadata,
            transcript,
            mode=args.analysis_mode,
            chunk_chars=args.chunk_chars,
        )
        write_notes(output_dir, metadata, transcript)
        write_json(output_dir / "metadata.json", metadata)
        print(f"Analysis pack ready. Output directory: {output_dir}")
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 0
    except Exception as exc:
        metadata = {
            "status": "failed",
            "strategy": "analysis-pack",
            "error": str(exc),
        }
        print(f"ERROR: {exc}", file=sys.stderr)
        print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="q-video-intake")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-env", help="Check local dependencies")
    check.set_defaults(func=check_env)

    intake_parser = sub.add_parser("intake", help="Create transcript/notes from a URL or file")
    intake_parser.add_argument("--input", "-i", required=True, help="Video/audio URL or local file")
    intake_parser.add_argument("--output-dir", "-o", help="Output directory")
    intake_parser.add_argument("--engine", choices=["none", "openai"], default="none")
    intake_parser.add_argument("--cookies-browser", choices=["none", "chrome", "edge", "firefox"], default="none")
    intake_parser.add_argument("--cookies-file", help="Netscape-format cookies.txt file for yt-dlp --cookies")
    intake_parser.add_argument("--no-saved-auth-route", action="store_true", help="Do not reuse or save authorization routes; explicit cookie flags still apply")
    intake_parser.add_argument("--sub-langs", default=DEFAULT_SUB_LANGS)
    intake_parser.add_argument("--no-subtitles", action="store_true")
    intake_parser.add_argument("--subtitle-timeout", type=int, default=120)
    intake_parser.add_argument("--audio-timeout", type=int, default=900)
    intake_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    intake_parser.add_argument("--openai-model", default="gpt-4o-mini-transcribe")
    intake_parser.add_argument("--analysis-mode", choices=["tutorial", "summary", "workflow", "learning"], default="tutorial")
    intake_parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    intake_parser.add_argument("--no-analysis-pack", action="store_true")
    intake_parser.set_defaults(func=intake)

    bili_probe_parser = sub.add_parser(
        "bilibili-subtitle-probe",
        help="Probe Bilibili page/API subtitle metadata without yt-dlp",
    )
    bili_probe_parser.add_argument("--input", "-i", required=True, help="Bilibili URL or BV id")
    bili_probe_parser.add_argument("--output-dir", "-o", help="Output directory")
    bili_probe_parser.add_argument("--cookies-file", help="Netscape-format cookies.txt file for authenticated direct probe")
    bili_probe_parser.add_argument("--subtitle-timeout", type=int, default=120)
    bili_probe_parser.set_defaults(func=create_bilibili_subtitle_probe)

    analyze_parser = sub.add_parser("analyze", help="Create an analysis pack from an existing transcript")
    analyze_parser.add_argument("--input-dir", help="Existing intake output directory containing transcript.txt")
    analyze_parser.add_argument("--transcript", help="Transcript file to analyze")
    analyze_parser.add_argument("--source", help="Optional source label or URL")
    analyze_parser.add_argument("--output-dir", "-o", help="Output directory")
    analyze_parser.add_argument("--analysis-mode", choices=["tutorial", "summary", "workflow", "learning"], default="tutorial")
    analyze_parser.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    analyze_parser.set_defaults(func=analyze)

    score_parser = sub.add_parser("score", help="Score a transcript against a reference transcript")
    score_parser.add_argument("--reference", required=True, help="Reference transcript, usually downloaded subtitles")
    score_parser.add_argument("--candidate", required=True, help="Candidate transcript, usually STT output")
    score_parser.add_argument("--metric", choices=["auto", "cer", "wer"], default="auto")
    score_parser.add_argument("--output-dir", "-o", help="Optional directory for score.json")
    score_parser.set_defaults(func=score_transcripts)

    visual_score_parser = sub.add_parser("visual-score", help="Score visual notes against a gold checklist")
    visual_score_parser.add_argument("--notes", required=True, help="Visual notes markdown file to score")
    visual_score_parser.add_argument("--gold", required=True, help="Gold checklist JSON file")
    visual_score_parser.add_argument("--output-dir", "-o", help="Directory for visual_score.json and visual_score.md")
    visual_score_parser.set_defaults(func=score_visual_notes)

    visual_parser = sub.add_parser("visual-pack", help="Sample video frames and create a visual analysis pack")
    visual_parser.add_argument("--input", "-i", required=True, help="Local video file")
    visual_parser.add_argument("--output-dir", "-o", help="Output directory")
    visual_parser.add_argument("--start", type=float, help="Start offset in seconds")
    visual_parser.add_argument("--duration", type=float, help="Duration in seconds to sample")
    visual_parser.add_argument("--visual-preset", choices=["manual", "economy", "balanced", "deep"], default="manual")
    visual_parser.add_argument("--visual-kind", choices=["general", "talking-head", "slides", "ui-demo", "fast-action"], default="general")
    visual_parser.add_argument("--interval", type=float, help="Seconds between sampled frames")
    visual_parser.add_argument("--max-frames", type=int)
    visual_parser.add_argument("--width", type=int, help="Output frame width; use 0 to keep source width")
    visual_parser.add_argument("--jpeg-quality", type=int, default=3)
    visual_parser.add_argument("--timeout", type=int, default=300)
    visual_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    visual_parser.add_argument("--visual-mode", choices=["summary", "tutorial", "reverse"], default="reverse")
    visual_parser.set_defaults(func=create_visual_pack)

    visual_local_parser = sub.add_parser(
        "visual-local",
        help="Local-only frame sampling plus Codex/agent handoff; never calls a vision provider",
    )
    visual_local_parser.add_argument("--input", "-i", required=True, help="Local video file")
    visual_local_parser.add_argument("--output-dir", "-o", help="Output directory")
    visual_local_parser.add_argument("--start", type=float, help="Start offset in seconds")
    visual_local_parser.add_argument("--duration", type=float, help="Duration in seconds to sample")
    visual_local_parser.add_argument("--visual-preset", choices=["manual", "economy", "balanced", "deep"], default="economy")
    visual_local_parser.add_argument("--visual-kind", choices=["general", "talking-head", "slides", "ui-demo", "fast-action"], default="general")
    visual_local_parser.add_argument("--interval", type=float, help="Seconds between sampled frames")
    visual_local_parser.add_argument("--max-frames", type=int)
    visual_local_parser.add_argument("--width", type=int, help="Output frame width; use 0 to keep source width")
    visual_local_parser.add_argument("--jpeg-quality", type=int, default=3)
    visual_local_parser.add_argument("--timeout", type=int, default=300)
    visual_local_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    visual_local_parser.add_argument("--visual-mode", choices=["summary", "tutorial", "reverse"], default="reverse")
    visual_local_parser.add_argument("--agent-max-frames", type=int, default=4, help="Frames listed in the local agent task")
    visual_local_parser.add_argument("--agent-output-file", help="Output markdown file for the local agent notes")
    visual_local_parser.set_defaults(func=create_visual_local)

    visual_smart_parser = sub.add_parser(
        "visual-smart-select",
        help="Select high-value frames from an existing dense visual pack",
    )
    visual_smart_parser.add_argument("--input-dir", required=True, help="Existing visual-pack output directory")
    visual_smart_parser.add_argument("--policy", choices=sorted(SMART_SELECTION_POLICIES), default="balanced", help="Smart selection policy defaults")
    visual_smart_parser.add_argument("--budget-frames", type=int, help="Maximum frames to keep; overrides --policy")
    visual_smart_parser.add_argument("--baseline-seconds", type=float, help="Minimum periodic coverage interval; overrides --policy")
    visual_smart_parser.add_argument("--min-gap-seconds", type=float, help="Minimum gap between event-selected frames; overrides --policy")
    visual_smart_parser.add_argument("--event-neighbor-frames", type=int, help="Also keep nearby frames around high-delta events; overrides --policy")
    visual_smart_parser.add_argument("--coverage-fraction", type=float, help="0-1 share of frame budget reserved for periodic coverage; overrides --policy")
    visual_smart_parser.add_argument("--timeout", type=int, default=300)
    visual_smart_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    visual_smart_parser.add_argument("--event-hints", help="JSON event hints from subtitles, chapters, OCR, or manual review")
    visual_smart_parser.add_argument("--selection-file", help="Output selected-frames JSON; defaults to visual/selected_frames.json")
    visual_smart_parser.add_argument("--report-file", help="Output Markdown report; defaults to visual/smart_sampling_report.md")
    visual_smart_parser.set_defaults(func=create_visual_smart_select)

    visual_subtitle_hints_parser = sub.add_parser(
        "visual-subtitle-hints",
        help="Convert SRT/VTT subtitle cues into smart-selection event hints",
    )
    visual_subtitle_hints_parser.add_argument("--subtitle", required=True, help="SRT or WebVTT subtitle file")
    visual_subtitle_hints_parser.add_argument("--output-file", "-o", help="Output visual event hints JSON")
    visual_subtitle_hints_parser.add_argument("--min-gap-seconds", type=float, default=8.0, help="Minimum gap for regular subtitle boundary hints")
    visual_subtitle_hints_parser.add_argument("--keyword-min-gap-seconds", type=float, default=3.0, help="Minimum gap for keyword-matched hints")
    visual_subtitle_hints_parser.add_argument("--max-events", type=int, default=80)
    visual_subtitle_hints_parser.add_argument("--default-tolerance", type=float, default=1.0)
    visual_subtitle_hints_parser.add_argument("--boundary-weight", type=float, default=0.6)
    visual_subtitle_hints_parser.add_argument("--keyword-weight", type=float, default=1.0)
    visual_subtitle_hints_parser.add_argument("--keywords", default=DEFAULT_SUBTITLE_HINT_KEYWORDS)
    visual_subtitle_hints_parser.set_defaults(func=create_visual_subtitle_hints)

    visual_smart_score_parser = sub.add_parser(
        "visual-smart-score",
        help="Score smart selected frames against gold event timestamps",
    )
    visual_smart_score_parser.add_argument("--selection", required=True, help="visual/selected_frames.json from visual-smart-select")
    visual_smart_score_parser.add_argument("--gold-events", required=True, help="Gold event JSON with timestamps and optional tolerances")
    visual_smart_score_parser.add_argument("--default-tolerance", type=float, default=0.75, help="Default timestamp tolerance in seconds")
    visual_smart_score_parser.add_argument("--output-dir", "-o", help="Directory for visual_smart_score.json and .md")
    visual_smart_score_parser.set_defaults(func=score_visual_smart_selection)

    visual_smart_grid_parser = sub.add_parser(
        "visual-smart-grid",
        help="Run a closed-loop grid search for smart selection policy parameters",
    )
    visual_smart_grid_parser.add_argument("--input-dir", required=True, help="Existing visual-pack output directory")
    visual_smart_grid_parser.add_argument("--gold-events", required=True, help="Gold event JSON for event-recall scoring")
    visual_smart_grid_parser.add_argument("--policy", choices=sorted(SMART_SELECTION_POLICIES), default="balanced")
    visual_smart_grid_parser.add_argument("--budget-frames", type=int, default=16)
    visual_smart_grid_parser.add_argument("--baseline-seconds", type=float)
    visual_smart_grid_parser.add_argument("--coverage-fractions", default="0.35,0.5,0.65,0.8,0.95")
    visual_smart_grid_parser.add_argument("--min-gap-seconds-values", default="1,2")
    visual_smart_grid_parser.add_argument("--event-neighbor-values", default="0,1")
    visual_smart_grid_parser.add_argument("--default-tolerance", type=float, default=0.75)
    visual_smart_grid_parser.add_argument("--timeout", type=int, default=300)
    visual_smart_grid_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    visual_smart_grid_parser.add_argument("--event-hints", help="JSON event hints to include in every grid selection")
    visual_smart_grid_parser.add_argument("--output-dir", "-o", help="Directory for grid outputs; defaults to visual/smart_grid")
    visual_smart_grid_parser.set_defaults(func=create_visual_smart_grid)

    visual_notes_parser = sub.add_parser("visual-notes", help="Create fillable visual notes from an existing frame pack")
    visual_notes_parser.add_argument("--input-dir", required=True, help="Existing visual-pack output directory")
    visual_notes_parser.add_argument("--output-file", help="Output markdown file; defaults to visual/visual_notes.md")
    visual_notes_parser.add_argument("--visual-mode", choices=["summary", "tutorial", "reverse"], default="reverse")
    visual_notes_parser.add_argument("--force", action="store_true", help="Overwrite an existing notes file")
    visual_notes_parser.set_defaults(func=create_visual_notes)

    visual_analyze_parser = sub.add_parser("visual-analyze", help="Analyze a frame pack with a vision provider")
    visual_analyze_parser.add_argument("--input-dir", required=True, help="Existing visual-pack output directory")
    visual_analyze_parser.add_argument("--engine", choices=["none", "openai"], default="none")
    visual_analyze_parser.add_argument("--output-file", help="Output markdown file; defaults to visual/visual_notes_model.md")
    visual_analyze_parser.add_argument("--visual-mode", choices=["summary", "tutorial", "reverse"], default="reverse")
    visual_analyze_parser.add_argument("--visual-preset", choices=["manual", "economy", "balanced"], default="manual")
    visual_analyze_parser.add_argument("--frame-selection", choices=["smart", "even"], default="smart", help="Prefer smart selected frames when available")
    visual_analyze_parser.add_argument("--selection-file", help="Explicit selected-frames JSON from visual-smart-select")
    visual_analyze_parser.add_argument("--max-frames", type=int)
    visual_analyze_parser.add_argument("--max-image-bytes", type=int, default=5_000_000)
    visual_analyze_parser.add_argument("--max-output-tokens", type=int)
    visual_analyze_parser.add_argument("--openai-provider", choices=["openai", "azure"], default=os.environ.get("OPENAI_PROVIDER", "openai"))
    visual_analyze_parser.add_argument("--openai-model", default=os.environ.get("OPENAI_VISUAL_MODEL", "gpt-4.1-mini"))
    visual_analyze_parser.add_argument("--azure-api-version", default=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"))
    visual_analyze_parser.add_argument("--image-detail", choices=["auto", "low", "high"])
    visual_analyze_parser.set_defaults(func=create_visual_analysis)

    visual_agent_parser = sub.add_parser("visual-agent-task", help="Create a Codex/agent handoff task from a frame pack")
    visual_agent_parser.add_argument("--input-dir", required=True, help="Existing visual-pack output directory")
    visual_agent_parser.add_argument("--output-file", help="Output markdown file; defaults to visual/visual_notes_agent.md")
    visual_agent_parser.add_argument("--visual-mode", choices=["summary", "tutorial", "reverse"], default="reverse")
    visual_agent_parser.add_argument("--frame-selection", choices=["smart", "even"], default="smart", help="Prefer smart selected frames when available")
    visual_agent_parser.add_argument("--selection-file", help="Explicit selected-frames JSON from visual-smart-select")
    visual_agent_parser.add_argument("--max-frames", type=int, default=8)
    visual_agent_parser.set_defaults(func=create_visual_agent_task)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
