#!/usr/bin/env python3
"""q-audio-intake: audio-first STT intake and benchmark scoring."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = Path("local-state") / "q-audio-intake"
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg", ".opus"}
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def is_url(value: str) -> bool:
    return value.startswith(("http://", "https://", "www."))


def is_bilibili(value: str) -> bool:
    return "bilibili.com" in value or "b23.tv" in value


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, data: dict[str, Any]) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


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
    result = run_cmd([sys.executable, "-c", f"import {module_name}"], timeout=20)
    return result.returncode == 0


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


def executable_works(candidate: str) -> bool:
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


def executable_help_works(candidate: str) -> bool:
    try:
        result = subprocess.run(
            [candidate, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except Exception:
        return False
    return result.returncode == 0


def resolve_ffmpeg(location: str | None = None) -> str | None:
    if location:
        path = Path(location).expanduser()
        if path.is_dir():
            candidate = path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
            if candidate.exists() and executable_works(str(candidate)):
                return str(candidate)
        if path.exists() and executable_works(str(path)):
            return str(path)

    candidate = resolve_command("ffmpeg")
    if candidate and executable_works(candidate):
        return candidate
    return None


def resolve_whisper_cpp_cli(location: str | None = None) -> str | None:
    names = ["whisper-cli.exe", "whisper-cli"] if os.name == "nt" else ["whisper-cli"]
    candidates: list[Path] = []

    for value in [location, os.environ.get("WHISPER_CPP_CLI")]:
        if not value:
            continue
        path = Path(value).expanduser()
        if path.is_dir():
            candidates.extend(path / name for name in names)
        else:
            candidates.append(path)

    for candidate in candidates:
        if candidate.exists() and executable_help_works(str(candidate)):
            return str(candidate)

    for name in names:
        found = resolve_command(name)
        if found and executable_help_works(found):
            return found
    return None


def ffmpeg_location_arg(location: str | None = None) -> str | None:
    ffmpeg_path = resolve_ffmpeg(location)
    if not ffmpeg_path:
        return None
    return str(Path(ffmpeg_path).parent)


def clip_args(args: argparse.Namespace) -> list[str]:
    result: list[str] = []
    if args.start is not None:
        result.extend(["-ss", str(args.start)])
    if args.duration is not None:
        result.extend(["-t", str(args.duration)])
    return result


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
            "fix": f"{sys.executable} -m pip install -r skills/q-audio-intake/scripts/requirements.txt",
        },
        "ffmpeg": {
            "ok": resolve_ffmpeg() is not None,
            "detail": resolve_ffmpeg() or "ffmpeg command",
            "fix": "Install a real ffmpeg binary or pass --ffmpeg-location.",
        },
        "openai_key": {
            "ok": bool(os.environ.get("OPENAI_API_KEY")),
            "detail": "OPENAI_API_KEY",
            "fix": "Set OPENAI_API_KEY locally to use --engine openai.",
        },
        "gemini_key": {
            "ok": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
            "detail": "GEMINI_API_KEY or GOOGLE_API_KEY",
            "fix": "Set GEMINI_API_KEY locally to use --engine gemini.",
        },
        "faster_whisper": {
            "ok": module_available("faster_whisper"),
            "detail": "python module faster_whisper",
            "fix": f"{sys.executable} -m pip install faster-whisper",
        },
        "whisper_cpp_cli": {
            "ok": resolve_whisper_cpp_cli() is not None,
            "detail": resolve_whisper_cpp_cli() or "WHISPER_CPP_CLI or whisper-cli on PATH",
            "fix": "Set WHISPER_CPP_CLI or pass --whisper-cpp-cli.",
        },
        "whisper_cpp_model": {
            "ok": bool(os.environ.get("WHISPER_CPP_MODEL") and Path(os.environ["WHISPER_CPP_MODEL"]).expanduser().exists()),
            "detail": "WHISPER_CPP_MODEL",
            "fix": "Set WHISPER_CPP_MODEL or pass --whisper-cpp-model.",
        },
    }

    print("q-audio-intake environment check")
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
    if "unsupported_country_region_territory" in lowered:
        print("- Provider rejected the current country/region/network route.")
        print("- Try another configured provider or a supported network route.")
        return
    if "api_key" in lowered or "api key" in lowered:
        print("- Configure the selected provider API key locally.")
        print("- Use OPENAI_API_KEY for --engine openai.")
        print("- Use GEMINI_API_KEY or GOOGLE_API_KEY for --engine gemini.")
        return
    if "ffmpeg" in lowered:
        print("- Install a real ffmpeg binary or pass --ffmpeg-location.")
        return
    if "whisper.cpp" in lowered or "whisper-cpp" in lowered or "whisper_cpp" in lowered:
        print("- Set WHISPER_CPP_CLI or pass --whisper-cpp-cli.")
        print("- Set WHISPER_CPP_MODEL or pass --whisper-cpp-model.")
        return
    print("- run check-env")
    print("- retry with --engine none to isolate audio preparation from provider calls")


def ytdlp_audio_cmd(source: str, output_dir: Path, args: argparse.Namespace) -> list[str]:
    cmd = [sys.executable, "-m", "yt_dlp"]
    ffmpeg_location = ffmpeg_location_arg(args.ffmpeg_location)
    if ffmpeg_location:
        cmd.extend(["--ffmpeg-location", ffmpeg_location])
    if is_bilibili(source):
        cmd.extend([
            "--add-header",
            "Referer:https://www.bilibili.com/",
            "--user-agent",
            DEFAULT_UA,
        ])
    if args.cookies_browser and args.cookies_browser != "none":
        cmd.extend(["--cookies-from-browser", args.cookies_browser])
    if args.cookies_file:
        cmd.extend(["--cookies", str(Path(args.cookies_file).expanduser())])
    if args.start is not None or args.duration is not None:
        start = float(args.start or 0)
        if args.duration is None:
            section = f"*{start}-inf"
        else:
            section = f"*{start}-{start + float(args.duration)}"
        cmd.extend(["--download-sections", section])
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
    return cmd


def prepare_audio(source: str, output_dir: Path, args: argparse.Namespace) -> Path:
    logs_dir = output_dir / "logs"
    ensure_dir(logs_dir)

    if is_url(source):
        result = run_cmd(ytdlp_audio_cmd(source, output_dir, args), timeout=args.audio_timeout)
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

    if input_path.suffix.lower() in AUDIO_EXTENSIONS:
        if args.start is None and args.duration is None:
            target = output_dir / input_path.name
            shutil.copy2(input_path, target)
            return target

        ffmpeg_command = resolve_ffmpeg(args.ffmpeg_location)
        if not ffmpeg_command:
            raise RuntimeError("ffmpeg is required to clip local audio files.")
        audio_path = output_dir / "audio.mp3"
        cmd = [ffmpeg_command]
        cmd.extend(clip_args(args))
        cmd.extend([
            "-i",
            str(input_path),
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
        ])
        result = run_cmd(cmd, timeout=args.audio_timeout)
        write_text(logs_dir / "ffmpeg_clip.stdout.txt", result.stdout)
        write_text(logs_dir / "ffmpeg_clip.stderr.txt", result.stderr)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg audio clipping failed: {result.stderr[-800:]}")
        return audio_path

    ffmpeg_command = resolve_ffmpeg(args.ffmpeg_location)
    if not ffmpeg_command:
        raise RuntimeError("ffmpeg is required to extract audio from local video files.")
    audio_path = output_dir / "audio.mp3"
    cmd = [ffmpeg_command]
    cmd.extend(clip_args(args))
    cmd.extend([
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
    ])
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
    client = OpenAI(api_key=api_key)
    with audio_path.open("rb") as audio_file:
        result = client.audio.transcriptions.create(
            model=args.openai_model,
            file=audio_file,
            response_format="text",
        )
    return str(result).strip()


def transcribe_gemini(audio_path: Path, args: argparse.Namespace) -> str:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not set.")
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Python package 'google-genai' is not installed.") from exc
    client = genai.Client(api_key=api_key)
    uploaded = client.files.upload(file=audio_path)
    response = client.models.generate_content(
        model=args.gemini_model,
        contents=[
            uploaded,
            (
                "Please transcribe this audio fully. Preserve the original "
                "language, wording, and structure. Do not summarize."
            ),
        ],
    )
    return (response.text or "").strip()


def transcribe_faster_whisper(audio_path: Path, args: argparse.Namespace) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("Python package 'faster-whisper' is not installed.") from exc

    model = WhisperModel(
        args.faster_whisper_model,
        device=args.faster_whisper_device,
        compute_type=args.faster_whisper_compute_type,
        download_root=args.faster_whisper_model_dir,
    )
    language = None if args.language == "auto" else args.language
    segments, info = model.transcribe(
        str(audio_path),
        language=language,
        vad_filter=True,
        beam_size=args.faster_whisper_beam_size,
    )

    lines: list[str] = []
    segment_data: list[dict[str, Any]] = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        lines.append(text)
        segment_data.append({
            "start": round(float(segment.start), 3),
            "end": round(float(segment.end), 3),
            "text": text,
        })

    metadata_path = audio_path.parent / "faster_whisper.json"
    write_json(
        metadata_path,
        {
            "model": args.faster_whisper_model,
            "device": args.faster_whisper_device,
            "compute_type": args.faster_whisper_compute_type,
            "language": getattr(info, "language", None),
            "language_probability": getattr(info, "language_probability", None),
            "duration": getattr(info, "duration", None),
            "segments": segment_data,
        },
    )
    if not lines:
        raise RuntimeError("faster-whisper completed but returned no transcript.")
    return "\n".join(lines).strip()


def transcribe_whisper_cpp(audio_path: Path, args: argparse.Namespace) -> str:
    cli = resolve_whisper_cpp_cli(args.whisper_cpp_cli)
    if not cli:
        raise RuntimeError("whisper.cpp CLI was not found.")
    if not args.whisper_cpp_model:
        raise RuntimeError("whisper.cpp model path is required.")
    model_path = Path(args.whisper_cpp_model).expanduser()
    if not model_path.exists():
        raise RuntimeError(f"whisper.cpp model does not exist: {model_path}")

    output_base = audio_path.parent / "whisper_cpp_output"
    cmd = [
        cli,
        "--model",
        str(model_path),
        "--file",
        str(audio_path),
        "--language",
        "auto" if args.language == "auto" else args.language,
        "--output-txt",
        "--output-json",
        "--output-file",
        str(output_base),
        "--no-timestamps",
    ]
    if args.whisper_cpp_no_gpu:
        cmd.append("--no-gpu")
    if args.whisper_cpp_device is not None:
        cmd.extend(["--device", str(args.whisper_cpp_device)])
    if args.whisper_cpp_threads is not None:
        cmd.extend(["--threads", str(args.whisper_cpp_threads)])
    if args.whisper_cpp_beam_size is not None:
        cmd.extend(["--beam-size", str(args.whisper_cpp_beam_size)])

    result = run_cmd(cmd, timeout=args.transcribe_timeout)
    logs_dir = audio_path.parent / "logs"
    write_text(logs_dir / "whisper_cpp.stdout.txt", result.stdout)
    write_text(logs_dir / "whisper_cpp.stderr.txt", result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"whisper.cpp transcription failed: {result.stderr[-800:]}")

    transcript_path = output_base.with_suffix(".txt")
    transcript = transcript_path.read_text(encoding="utf-8", errors="ignore").strip() if transcript_path.exists() else ""
    if not transcript:
        transcript = result.stdout.strip()
    if not transcript:
        raise RuntimeError("whisper.cpp completed but returned no transcript.")

    write_json(
        audio_path.parent / "whisper_cpp.json",
        {
            "cli": cli,
            "model": str(model_path),
            "language": args.language,
            "gpu": not args.whisper_cpp_no_gpu,
            "device": args.whisper_cpp_device,
            "threads": args.whisper_cpp_threads,
            "beam_size": args.whisper_cpp_beam_size,
            "files": {
                "text": str(transcript_path) if transcript_path.exists() else "",
                "json": str(output_base.with_suffix(".json")) if output_base.with_suffix(".json").exists() else "",
            },
        },
    )
    return transcript


def transcribe(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).expanduser() if args.output_dir else default_output_dir()
    ensure_dir(output_dir)
    metadata: dict[str, Any] = {
        "source": args.input,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "engine": args.engine,
        "cookies_browser": args.cookies_browser,
        "cookies_file": str(Path(args.cookies_file).expanduser()) if args.cookies_file else "",
        "clip": {
            "start": args.start,
            "duration": args.duration,
        },
        "strategy": "audio-first",
        "status": "started",
        "files": {},
    }
    if args.engine == "faster-whisper":
        metadata["provider_options"] = {
            "model": args.faster_whisper_model,
            "device": args.faster_whisper_device,
            "compute_type": args.faster_whisper_compute_type,
            "language": args.language,
            "beam_size": args.faster_whisper_beam_size,
        }
    if args.engine == "whisper-cpp":
        metadata["provider_options"] = {
            "cli": args.whisper_cpp_cli or os.environ.get("WHISPER_CPP_CLI", ""),
            "model": args.whisper_cpp_model or os.environ.get("WHISPER_CPP_MODEL", ""),
            "language": args.language,
            "gpu": not args.whisper_cpp_no_gpu,
            "device": args.whisper_cpp_device,
            "threads": args.whisper_cpp_threads,
            "beam_size": args.whisper_cpp_beam_size,
        }

    try:
        started_at = time.perf_counter()
        print("Step 1: preparing audio")
        audio_path = prepare_audio(args.input, output_dir, args)
        metadata["runtime_seconds_audio_prepare"] = round(time.perf_counter() - started_at, 3)
        metadata["files"]["audio"] = str(audio_path)
        metadata["status"] = "audio_prepared"
        print(f"Audio ready: {audio_path}")

        if args.engine == "none":
            write_json(output_dir / "metadata.json", metadata)
            print(f"Done. Output directory: {output_dir}")
            print("RESULT_JSON:" + json.dumps(metadata, ensure_ascii=False))
            return 0

        print(f"Step 2: transcribing with {args.engine}")
        transcribe_started_at = time.perf_counter()
        if args.engine == "openai":
            transcript = transcribe_openai(audio_path, args)
        elif args.engine == "gemini":
            transcript = transcribe_gemini(audio_path, args)
        elif args.engine == "faster-whisper":
            transcript = transcribe_faster_whisper(audio_path, args)
            metadata["files"]["faster_whisper"] = str(output_dir / "faster_whisper.json")
        elif args.engine == "whisper-cpp":
            transcript = transcribe_whisper_cpp(audio_path, args)
            metadata["files"]["whisper_cpp"] = str(output_dir / "whisper_cpp.json")
        else:
            raise RuntimeError(f"Unsupported engine: {args.engine}")
        metadata["runtime_seconds_transcribe"] = round(time.perf_counter() - transcribe_started_at, 3)
        metadata["runtime_seconds_total"] = round(time.perf_counter() - started_at, 3)

        transcript_path = output_dir / "transcript.txt"
        write_text(transcript_path, transcript + "\n")
        metadata["status"] = f"transcript_from_{args.engine}"
        metadata["files"]["transcript"] = str(transcript_path)
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


def score(args: argparse.Namespace) -> int:
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


def parse_subtitle_time(value: str) -> float:
    match = re.match(r"(\d{1,2}):(\d{2}):(\d{2})[\.,](\d{3})", value.strip())
    if not match:
        raise RuntimeError(f"Unsupported subtitle timestamp: {value}")
    hours, minutes, seconds, millis = [int(item) for item in match.groups()]
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def subtitle_segment(args: argparse.Namespace) -> int:
    subtitle_path = Path(args.subtitle).expanduser()
    if not subtitle_path.exists():
        raise RuntimeError(f"Subtitle file does not exist: {subtitle_path}")

    start = float(args.start)
    end = start + float(args.duration)
    content = subtitle_path.read_text(encoding="utf-8", errors="ignore")
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").replace("\r", "\n"))
    lines: list[str] = []
    segment_count = 0

    for block in blocks:
        block_lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not block_lines:
            continue
        timing_index = next((i for i, line in enumerate(block_lines) if "-->" in line), None)
        if timing_index is None:
            continue
        left, right = block_lines[timing_index].split("-->", 1)
        segment_start = parse_subtitle_time(left)
        segment_end = parse_subtitle_time(right.split()[0])
        if segment_end < start or segment_start > end:
            continue
        text_lines = [
            re.sub(r"<[^>]+>", "", line).strip()
            for line in block_lines[timing_index + 1:]
        ]
        text = "\n".join(line for line in text_lines if line)
        if not text:
            continue
        if not lines or lines[-1] != text:
            lines.append(text)
        segment_count += 1

    transcript = "\n".join(lines).strip()
    if not transcript:
        raise RuntimeError("No subtitle text found for the requested segment.")

    output_path = Path(args.output).expanduser()
    write_text(output_path, transcript + "\n")
    result = {
        "status": "subtitle_segment_written",
        "subtitle": str(subtitle_path),
        "output": str(output_path),
        "start": start,
        "duration": float(args.duration),
        "end": end,
        "segments": segment_count,
        "chars": len(transcript),
    }
    print("RESULT_JSON:" + json.dumps(result, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="q-audio-intake")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-env", help="Check local dependencies")
    check.set_defaults(func=check_env)

    transcribe_parser = sub.add_parser("transcribe", help="Prepare audio and optionally transcribe it")
    transcribe_parser.add_argument("--input", "-i", required=True, help="Audio/video URL or local file")
    transcribe_parser.add_argument("--output-dir", "-o", help="Output directory")
    transcribe_parser.add_argument("--engine", choices=["none", "openai", "gemini", "faster-whisper", "whisper-cpp"], default="none")
    transcribe_parser.add_argument("--cookies-browser", choices=["none", "chrome", "edge", "firefox"], default="none")
    transcribe_parser.add_argument("--cookies-file", help="Netscape-format cookies.txt file for yt-dlp --cookies")
    transcribe_parser.add_argument("--start", type=float, help="Start offset in seconds for a benchmark clip")
    transcribe_parser.add_argument("--duration", type=float, help="Clip duration in seconds for a benchmark clip")
    transcribe_parser.add_argument("--audio-timeout", type=int, default=900)
    transcribe_parser.add_argument("--transcribe-timeout", type=int, default=3600)
    transcribe_parser.add_argument("--ffmpeg-location", help="Path to ffmpeg executable or directory")
    transcribe_parser.add_argument("--openai-model", default="gpt-4o-mini-transcribe")
    transcribe_parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    transcribe_parser.add_argument("--language", default="auto", help="Speech language hint such as zh, en, or auto")
    transcribe_parser.add_argument("--faster-whisper-model", default="base", help="faster-whisper model name or path")
    transcribe_parser.add_argument("--faster-whisper-model-dir", help="Optional model download/cache directory")
    transcribe_parser.add_argument("--faster-whisper-device", default="cpu")
    transcribe_parser.add_argument("--faster-whisper-compute-type", default="int8")
    transcribe_parser.add_argument("--faster-whisper-beam-size", type=int, default=5)
    transcribe_parser.add_argument("--whisper-cpp-cli", default=os.environ.get("WHISPER_CPP_CLI"), help="Path to whisper.cpp whisper-cli executable")
    transcribe_parser.add_argument("--whisper-cpp-model", default=os.environ.get("WHISPER_CPP_MODEL"), help="Path to whisper.cpp ggml model")
    transcribe_parser.add_argument("--whisper-cpp-no-gpu", action="store_true", help="Disable whisper.cpp GPU acceleration")
    transcribe_parser.add_argument("--whisper-cpp-device", type=int, help="whisper.cpp GPU device index")
    transcribe_parser.add_argument("--whisper-cpp-threads", type=int, help="whisper.cpp CPU thread count")
    transcribe_parser.add_argument("--whisper-cpp-beam-size", type=int, help="whisper.cpp beam size")
    transcribe_parser.set_defaults(func=transcribe)

    score_parser = sub.add_parser("score", help="Score a transcript against a reference transcript")
    score_parser.add_argument("--reference", required=True, help="Reference transcript, usually downloaded subtitles")
    score_parser.add_argument("--candidate", required=True, help="Candidate transcript, usually STT output")
    score_parser.add_argument("--metric", choices=["auto", "cer", "wer"], default="auto")
    score_parser.add_argument("--output-dir", "-o", help="Optional directory for score.json")
    score_parser.set_defaults(func=score)

    subtitle_parser = sub.add_parser("subtitle-segment", help="Extract a timed transcript segment from an SRT/VTT file")
    subtitle_parser.add_argument("--subtitle", required=True, help="Subtitle file with timestamps")
    subtitle_parser.add_argument("--start", type=float, required=True, help="Start offset in seconds")
    subtitle_parser.add_argument("--duration", type=float, required=True, help="Segment duration in seconds")
    subtitle_parser.add_argument("--output", required=True, help="Output transcript path")
    subtitle_parser.set_defaults(func=subtitle_segment)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
