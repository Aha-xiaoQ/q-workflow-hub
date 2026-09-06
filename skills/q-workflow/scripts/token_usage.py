#!/usr/bin/env python3
r"""Summarize local Codex token usage from session JSONL files.

This is intentionally read-only and dependency-free. It scans
%USERPROFILE%\.codex\sessions by default and aggregates the latest cumulative
token_count event per session file.
"""

from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
import os
import sys
import tempfile
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
)

DEFAULT_INPUT_RATE = 5.00
DEFAULT_CACHED_INPUT_RATE = 0.50
DEFAULT_OUTPUT_RATE = 30.00
ANSI = {
    "reset": "\033[0m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "dim": "\033[2m",
}


@dataclass
class TokenTotals:
    input_tokens: int = 0
    cached_input_tokens: int = 0
    output_tokens: int = 0
    reasoning_output_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "TokenTotals":
        data = data or {}
        return cls(**{name: int(data.get(name) or 0) for name in TOKEN_FIELDS})

    def add(self, other: "TokenTotals") -> None:
        for name in TOKEN_FIELDS:
            setattr(self, name, getattr(self, name) + getattr(other, name))

    def as_dict(self) -> dict[str, int]:
        return {name: getattr(self, name) for name in TOKEN_FIELDS}


@dataclass
class TokenEvent:
    timestamp: str = ""
    totals: TokenTotals = field(default_factory=TokenTotals)
    last_turn: TokenTotals = field(default_factory=TokenTotals)
    context_window: int = 0


@dataclass
class SessionUsage:
    path: Path
    session_id: str = ""
    cwd: str = ""
    started_at: str = ""
    updated_at: float = 0.0
    model: str = ""
    provider: str = ""
    totals: TokenTotals = field(default_factory=TokenTotals)
    last_turn: TokenTotals = field(default_factory=TokenTotals)
    context_window: int = 0
    token_events: int = 0
    parse_errors: int = 0
    match_texts: list[str] = field(default_factory=list)
    token_history: list[TokenEvent] = field(default_factory=list)
    project_hint: str = ""


@dataclass
class ProjectRoot:
    name: str
    path: Path


@dataclass
class CostRates:
    input_per_million: float = DEFAULT_INPUT_RATE
    cached_input_per_million: float = DEFAULT_CACHED_INPUT_RATE
    output_per_million: float = DEFAULT_OUTPUT_RATE


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def default_codex_home() -> Path:
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"

def default_projects_root() -> Path:
    if os.environ.get("Q_WORKFLOW_PROJECTS_ROOT"):
        return Path(os.environ["Q_WORKFLOW_PROJECTS_ROOT"]).expanduser()
    profile_path = default_codex_home() / "q-profile.json"
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    for key in ("projects", "projects_root", "project_root"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value).expanduser()
    return Path.home() / "Q_projects"


def normalize_path(value: str) -> str:
    if not value:
        return ""
    return os.path.normcase(os.path.abspath(os.path.expanduser(value)))


def is_under(path_value: str, root_value: str) -> bool:
    path_norm = normalize_path(path_value)
    root_norm = normalize_path(root_value)
    if not path_norm or not root_norm:
        return False
    return path_norm == root_norm or path_norm.startswith(root_norm.rstrip("\\/") + os.sep)


def path_patterns(path: Path) -> tuple[str, str]:
    raw = str(path)
    return raw.lower(), raw.replace("\\", "\\\\").lower()


def discover_project_roots(projects_root: Path) -> list[ProjectRoot]:
    if not projects_root.exists():
        return []
    roots: list[ProjectRoot] = []
    for child in sorted(projects_root.iterdir(), key=lambda item: item.name.lower()):
        if child.is_dir():
            roots.append(ProjectRoot(name=child.name, path=child))
    return roots


def score_project_session(session: SessionUsage, project: ProjectRoot) -> int:
    score = 0
    if session.cwd and is_under(session.cwd, str(project.path)):
        score += 1000
    path_text, escaped_path_text = path_patterns(project.path)
    name_text = project.name.lower()
    for text in session.match_texts:
        lowered = text.lower()
        score += lowered.count(path_text) * 20
        score += lowered.count(escaped_path_text) * 20
        score += lowered.count(name_text) * 3
    return score


def infer_project(session: SessionUsage, project_roots: list[ProjectRoot]) -> str:
    if session.project_hint:
        return session.project_hint
    best_name = ""
    best_score = 0
    for project in project_roots:
        score = score_project_session(session, project)
        if score > best_score:
            best_name = project.name
            best_score = score
    return best_name if best_score > 0 else "(unassigned)"


def project_by_name(project_roots: list[ProjectRoot]) -> dict[str, ProjectRoot]:
    return {project.name: project for project in project_roots}


def extract_model(obj: dict[str, Any]) -> str:
    payload = obj.get("payload")
    if isinstance(payload, dict):
        for key in ("model", "model_slug"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        nested = payload.get("payload")
        if isinstance(nested, dict):
            value = nested.get("model")
            if isinstance(value, str) and value:
                return value
    return ""


def append_text_value(texts: list[str], value: Any) -> None:
    if isinstance(value, str) and value:
        texts.append(value)


def extract_match_texts(obj: dict[str, Any]) -> list[str]:
    texts: list[str] = []
    payload = obj.get("payload")
    if not isinstance(payload, dict):
        return texts

    if obj.get("type") == "session_meta":
        append_text_value(texts, payload.get("cwd"))
        return texts

    append_text_value(texts, payload.get("message"))
    append_text_value(texts, payload.get("arguments"))
    append_text_value(texts, payload.get("output"))

    content = payload.get("content")
    if isinstance(content, list):
        for part in content:
            if isinstance(part, dict):
                append_text_value(texts, part.get("text"))
    return texts


def apply_session_object(usage: SessionUsage, obj: dict[str, Any]) -> None:
    usage.match_texts.extend(extract_match_texts(obj))

    if obj.get("type") == "session_meta":
        payload = obj.get("payload") or {}
        usage.session_id = str(payload.get("id") or usage.session_id)
        usage.cwd = str(payload.get("cwd") or usage.cwd)
        usage.started_at = str(payload.get("timestamp") or usage.started_at)
        usage.provider = str(payload.get("model_provider") or usage.provider)
        model = payload.get("model")
        if isinstance(model, str) and model:
            usage.model = model

    model = extract_model(obj)
    if model:
        usage.model = model

    payload = obj.get("payload") or {}
    if obj.get("type") == "event_msg" and payload.get("type") == "token_count":
        info = payload.get("info") or {}
        totals = TokenTotals.from_mapping(info.get("total_token_usage"))
        last_turn = TokenTotals.from_mapping(info.get("last_token_usage"))
        context_window = int(info.get("model_context_window") or usage.context_window or 0)
        usage.totals = totals
        usage.last_turn = last_turn
        usage.context_window = context_window
        usage.token_events += 1
        usage.token_history.append(
            TokenEvent(
                timestamp=str(obj.get("timestamp") or ""),
                totals=totals,
                last_turn=last_turn,
                context_window=context_window,
            )
        )


def parse_session(path: Path, usage: SessionUsage | None = None, start_offset: int = 0) -> SessionUsage:
    usage = usage or SessionUsage(path=path)
    usage.updated_at = path.stat().st_mtime
    try:
        with path.open("rb") as handle:
            if start_offset:
                handle.seek(start_offset)
            for raw_line in handle:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    usage.parse_errors += 1
                    continue
                if isinstance(obj, dict):
                    apply_session_object(usage, obj)
    except OSError:
        usage.parse_errors += 1
    return usage


def append_guard(path: Path, size: int, window: int = 256) -> str:
    if size <= 0:
        return ""
    try:
        with path.open("rb") as handle:
            handle.seek(max(0, size - window))
            return hashlib.sha256(handle.read(min(window, size))).hexdigest()
    except OSError:
        return ""


def is_safe_append(path: Path, cached: dict[str, Any], current_size: int) -> bool:
    cached_size = cached.get("size")
    cached_guard = cached.get("append_guard")
    if not isinstance(cached_size, int) or cached_size <= 0 or cached_size >= current_size or not isinstance(cached_guard, str) or not cached_guard:
        return False
    try:
        with path.open("rb") as handle:
            handle.seek(cached_size - 1)
            if handle.read(1) not in {b"\n", b"\r"}:
                return False
    except OSError:
        return False
    return append_guard(path, cached_size) == cached_guard


def session_to_cache(session: SessionUsage, size: int, mtime_ns: int) -> dict[str, Any]:
    return {
        "size": size,
        "mtime_ns": mtime_ns,
        "append_guard": append_guard(session.path, size),
        "session_id": session.session_id,
        "cwd": session.cwd,
        "started_at": session.started_at,
        "updated_at": session.updated_at,
        "model": session.model,
        "provider": session.provider,
        "totals": session.totals.as_dict(),
        "last_turn": session.last_turn.as_dict(),
        "context_window": session.context_window,
        "token_events": session.token_events,
        "parse_errors": session.parse_errors,
        "project_hint": session.project_hint,
        "token_history": [
            {
                "timestamp": event.timestamp,
                "totals": event.totals.as_dict(),
                "last_turn": event.last_turn.as_dict(),
                "context_window": event.context_window,
            }
            for event in session.token_history[-32:]
        ],
    }


def session_from_cache(path: Path, row: dict[str, Any]) -> SessionUsage:
    history = [
        TokenEvent(
            timestamp=str(event.get("timestamp") or ""),
            totals=TokenTotals.from_mapping(event.get("totals")),
            last_turn=TokenTotals.from_mapping(event.get("last_turn")),
            context_window=int(event.get("context_window") or 0),
        )
        for event in row.get("token_history", [])
        if isinstance(event, dict)
    ]
    return SessionUsage(
        path=path,
        session_id=str(row.get("session_id") or ""),
        cwd=str(row.get("cwd") or ""),
        started_at=str(row.get("started_at") or ""),
        updated_at=float(row.get("updated_at") or 0.0),
        model=str(row.get("model") or ""),
        provider=str(row.get("provider") or ""),
        totals=TokenTotals.from_mapping(row.get("totals")),
        last_turn=TokenTotals.from_mapping(row.get("last_turn")),
        context_window=int(row.get("context_window") or 0),
        token_events=int(row.get("token_events") or 0),
        parse_errors=int(row.get("parse_errors") or 0),
        token_history=history,
        project_hint=str(row.get("project_hint") or ""),
    )


def scan_sessions(codex_home: Path, project_roots: list[ProjectRoot]) -> list[SessionUsage]:
    sessions_dir = codex_home / "sessions"
    if not sessions_dir.exists():
        return []
    cache_path = codex_home / "cache" / "q-token-usage-v1.json"
    root_signature = [{"name": root.name, "path": str(root.path.resolve())} for root in project_roots]
    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cache = {}
    cache_rows = cache.get("sessions", {}) if cache.get("version") == 1 and cache.get("project_roots") == root_signature else {}
    if not isinstance(cache_rows, dict):
        cache_rows = {}
    sessions = []
    next_rows: dict[str, Any] = {}
    for path in sessions_dir.rglob("*.jsonl"):
        try:
            stat = path.stat()
        except OSError:
            continue
        key = str(path.resolve())
        cached = cache_rows.get(key)
        if (
            isinstance(cached, dict)
            and cached.get("size") == stat.st_size
            and cached.get("mtime_ns") == stat.st_mtime_ns
        ):
            parsed = session_from_cache(path, cached)
        elif isinstance(cached, dict) and is_safe_append(path, cached, stat.st_size):
            parsed = parse_session(path, session_from_cache(path, cached), int(cached["size"]))
            if not parsed.project_hint:
                parsed.project_hint = infer_project(parsed, project_roots)
        else:
            parsed = parse_session(path)
            parsed.project_hint = infer_project(parsed, project_roots)
        next_rows[key] = session_to_cache(parsed, stat.st_size, stat.st_mtime_ns)
        if parsed.token_events > 0:
            sessions.append(parsed)
    sessions.sort(key=lambda item: item.updated_at)
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"version": 1, "project_roots": root_signature, "sessions": next_rows}, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(cache_path)
    except OSError:
        pass
    return sessions


def incremental_cache_self_test() -> dict[str, Any]:
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="q-token-incremental-") as temp_dir:
        home = Path(temp_dir)
        session_path = home / "sessions" / "2026" / "08" / "03" / "rollout-test.jsonl"
        session_path.parent.mkdir(parents=True)

        meta = {
            "type": "session_meta",
            "payload": {"id": "incremental-test", "cwd": str(home / "work"), "timestamp": "2026-08-03T00:00:00Z"},
        }

        def token_event(total: int) -> dict[str, Any]:
            usage = {
                "input_tokens": total,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "reasoning_output_tokens": 0,
                "total_tokens": total,
            }
            return {
                "type": "event_msg",
                "timestamp": "2026-08-03T00:00:01Z",
                "payload": {"type": "token_count", "info": {"total_token_usage": usage, "last_token_usage": usage, "model_context_window": 1000}},
            }

        initial_lines = [meta, token_event(10)]
        session_path.write_text("".join(json.dumps(row) + "\n" for row in initial_lines), encoding="utf-8")
        first = scan_sessions(home, [])
        if len(first) != 1 or first[0].totals.total_tokens != 10 or first[0].token_events != 1:
            failures.append("initial cache scan did not capture the first token event")

        cache = json.loads((home / "cache" / "q-token-usage-v1.json").read_text(encoding="utf-8"))
        cached = cache.get("sessions", {}).get(str(session_path.resolve()), {})
        with session_path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(json.dumps(token_event(25)) + "\n")
        if not is_safe_append(session_path, cached, session_path.stat().st_size):
            failures.append("append-only growth did not pass the tail guard")

        second = scan_sessions(home, [])
        if len(second) != 1 or second[0].totals.total_tokens != 25 or second[0].token_events != 2:
            failures.append("incremental scan did not merge the appended token event")

        refreshed_cache = json.loads((home / "cache" / "q-token-usage-v1.json").read_text(encoding="utf-8"))
        refreshed = refreshed_cache.get("sessions", {}).get(str(session_path.resolve()), {})
        with session_path.open("r+b") as handle:
            handle.seek(max(0, int(refreshed.get("size", 0)) - 8))
            original = handle.read(1)
            handle.seek(-1, 1)
            handle.write(b"X" if original != b"X" else b"Y")
        with session_path.open("ab") as handle:
            handle.write((json.dumps(token_event(30)) + "\n").encode("utf-8"))
        if is_safe_append(session_path, refreshed, session_path.stat().st_size):
            failures.append("tail mutation was incorrectly accepted as append-only growth")

    return {"status": "pass" if not failures else "fail", "cases": 3, "failures": failures}


def sum_sessions(sessions: list[SessionUsage]) -> TokenTotals:
    totals = TokenTotals()
    for session in sessions:
        totals.add(session.totals)
    return totals


def iso_from_mtime(mtime: float) -> str:
    return datetime.fromtimestamp(mtime, timezone.utc).astimezone().isoformat(timespec="seconds")


def fmt_int(value: int) -> str:
    return f"{value:,}"


def fmt_compact(value: int) -> str:
    value_f = float(value)
    for suffix in ("", "K", "M", "B", "T"):
        if abs(value_f) < 1000 or suffix == "T":
            if suffix == "":
                return str(int(value_f))
            if abs(value_f) >= 100:
                return f"{value_f:.0f}{suffix}"
            if abs(value_f) >= 10:
                return f"{value_f:.1f}{suffix}"
            return f"{value_f:.2f}{suffix}"
        value_f /= 1000.0


def fmt_money(value: float) -> str:
    return f"${value:,.2f}"


def fmt_money_columns(value: float) -> str:
    return f"{('$' + format(value, ',.2f')):<8}"


def estimate_cost(tokens: dict[str, int], rates: CostRates) -> float:
    cached = int(tokens.get("cached_input_tokens") or 0)
    input_total = int(tokens.get("input_tokens") or 0)
    uncached_input = max(0, input_total - cached)
    output = int(tokens.get("output_tokens") or 0)
    reasoning = int(tokens.get("reasoning_output_tokens") or 0)
    return (
        (uncached_input / 1_000_000.0 * rates.input_per_million)
        + (cached / 1_000_000.0 * rates.cached_input_per_million)
        + ((output + reasoning) / 1_000_000.0 * rates.output_per_million)
    )


def token_metrics(tokens: dict[str, int], rates: CostRates) -> dict[str, Any]:
    cached = int(tokens.get("cached_input_tokens") or 0)
    input_total = int(tokens.get("input_tokens") or 0)
    uncached_input = max(0, input_total - cached)
    output = int(tokens.get("output_tokens") or 0)
    reasoning = int(tokens.get("reasoning_output_tokens") or 0)
    output_total = output + reasoning
    effective_total = uncached_input + cached + output_total

    uncached_cost = uncached_input / 1_000_000.0 * rates.input_per_million
    cached_cost = cached / 1_000_000.0 * rates.cached_input_per_million
    output_cost = output_total / 1_000_000.0 * rates.output_per_million
    estimated_cost = uncached_cost + cached_cost + output_cost
    no_cache_cost = (
        (input_total / 1_000_000.0 * rates.input_per_million)
        + (output_total / 1_000_000.0 * rates.output_per_million)
    )
    cache_savings = max(0.0, no_cache_cost - estimated_cost)

    return {
        "uncached_input_tokens": uncached_input,
        "output_plus_reasoning_tokens": output_total,
        "effective_total_tokens": effective_total,
        "cached_input_ratio": pct_float(cached, input_total),
        "uncached_input_ratio": pct_float(uncached_input, input_total),
        "output_token_share": pct_float(output_total, effective_total),
        "uncached_cost_usd": uncached_cost,
        "cached_cost_usd": cached_cost,
        "output_cost_usd": output_cost,
        "output_cost_share": pct_float(output_cost, estimated_cost),
        "no_cache_cost_usd": no_cache_cost,
        "cache_savings_usd": cache_savings,
        "cache_savings_ratio": pct_float(cache_savings, no_cache_cost),
        "effective_cost_per_million_usd": (estimated_cost / effective_total * 1_000_000.0) if effective_total else 0.0,
    }


def health_item(level: str, title: str, detail: str, action: str) -> dict[str, str]:
    return {"level": level, "title": title, "detail": detail, "action": action}


def avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def session_efficiency_trend(session: SessionUsage | None, rates: CostRates, limit: int = 8) -> dict[str, Any]:
    events = (session.token_history if session else [])[-limit:]
    if not events:
        return {
            "event_count": 0,
            "window": limit,
            "input_growth_tokens": 0,
            "input_growth_ratio": 0.0,
            "context_pressure_delta": 0.0,
            "avg_cache_ratio": 0.0,
            "min_cache_ratio": 0.0,
            "max_cache_ratio": 0.0,
            "cache_ratio_spread": 0.0,
            "latest_cache_savings_ratio": 0.0,
            "latest_effective_cost_per_million_usd": 0.0,
        }

    first = events[0]
    latest = events[-1]
    first_tokens = first.last_turn.as_dict()
    latest_tokens = latest.last_turn.as_dict()
    first_input = int(first_tokens.get("input_tokens") or 0)
    latest_input = int(latest_tokens.get("input_tokens") or 0)
    first_total = int(first_tokens.get("total_tokens") or 0)
    latest_total = int(latest_tokens.get("total_tokens") or 0)
    first_window = int(first.context_window or latest.context_window or 0)
    latest_window = int(latest.context_window or first.context_window or 0)
    cache_ratios = [
        float(token_metrics(event.last_turn.as_dict(), rates)["cached_input_ratio"])
        for event in events
        if int(event.last_turn.input_tokens or 0) > 0
    ]
    latest_metrics = token_metrics(latest_tokens, rates)
    return {
        "event_count": len(events),
        "window": limit,
        "first_timestamp": first.timestamp,
        "latest_timestamp": latest.timestamp,
        "first_input_tokens": first_input,
        "latest_input_tokens": latest_input,
        "input_growth_tokens": max(0, latest_input - first_input),
        "input_growth_ratio": pct_float(max(0, latest_input - first_input), first_input),
        "first_context_pressure": pct_float(first_total, first_window),
        "latest_context_pressure": pct_float(latest_total, latest_window),
        "context_pressure_delta": pct_float(latest_total, latest_window) - pct_float(first_total, first_window),
        "avg_cache_ratio": avg(cache_ratios),
        "min_cache_ratio": min(cache_ratios) if cache_ratios else 0.0,
        "max_cache_ratio": max(cache_ratios) if cache_ratios else 0.0,
        "cache_ratio_spread": (max(cache_ratios) - min(cache_ratios)) if cache_ratios else 0.0,
        "latest_cache_savings_ratio": float(latest_metrics["cache_savings_ratio"]),
        "latest_cache_savings_usd": float(latest_metrics["cache_savings_usd"]),
        "latest_effective_cost_per_million_usd": float(latest_metrics["effective_cost_per_million_usd"]),
    }


def token_health(current: dict[str, Any], rates: CostRates, trend: dict[str, Any] | None = None) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    trend = trend or {}
    last_turn = current.get("latest_last_turn") or {}
    metrics = token_metrics(last_turn, rates)
    input_total = int(last_turn.get("input_tokens") or 0)
    uncached_input = int(metrics["uncached_input_tokens"])
    output_total = int(metrics["output_plus_reasoning_tokens"])
    cache_ratio = float(metrics["cached_input_ratio"])
    output_cost_share = float(metrics["output_cost_share"])
    context_window = int(current.get("latest_context_window") or 0)
    last_total = int(last_turn.get("total_tokens") or 0)
    context_pct = pct_float(last_total, context_window)
    input_growth = int(trend.get("input_growth_tokens") or 0)
    input_growth_ratio = float(trend.get("input_growth_ratio") or 0.0)
    cache_spread = float(trend.get("cache_ratio_spread") or 0.0)
    savings_ratio = float(trend.get("latest_cache_savings_ratio") or metrics.get("cache_savings_ratio") or 0.0)

    if context_pct >= 85.0:
        items.append(
            health_item(
                "danger",
                "Context pressure is high",
                f"Latest turn used {context_pct:.1f}% of the context window.",
                "Checkpoint durable state, narrow the next task, and consider starting a fresh session from the saved state. If workflow rules, release, or colleague/customer handoff are in scope, suggest workflow-health / 体检 before expanding further.",
            )
        )
    elif context_pct >= 65.0:
        items.append(
            health_item(
                "warn",
                "Context pressure is rising",
                f"Latest turn used {context_pct:.1f}% of the context window.",
                "Before another broad task, write the current objective, changed files, validation, and next action to durable memory. If the task is workflow-rule, release, or handoff related, suggest workflow-health / 体检.",
            )
        )
    else:
        items.append(
            health_item(
                "ok",
                "Context pressure is manageable",
                f"Latest turn used {context_pct:.1f}% of the context window.",
                "Continue with targeted reads and avoid loading large files unless they are decision-critical.",
            )
        )

    if input_total <= 0:
        items.append(
            health_item(
                "warn",
                "No input-token sample for the latest turn",
                "The latest token event did not include input usage.",
                "Use the dashboard as a historical view and re-run after the next model turn.",
            )
        )
    elif cache_ratio >= 80.0 and uncached_input < 40_000:
        items.append(
            health_item(
                "ok",
                "Prompt cache is healthy",
                f"{cache_ratio:.1f}% of latest input tokens were cached; uncached input was {fmt_int(uncached_input)}.",
                "Keep static instructions and skill routers stable; optimize total size only when context pressure rises.",
            )
        )
    elif cache_ratio < 50.0 and input_total >= 8_000:
        items.append(
            health_item(
                "warn",
                "Prompt cache looks weak",
                f"Only {cache_ratio:.1f}% of latest input tokens were cached.",
                "Check whether the static prefix changed, too many full files were loaded, or dynamic content moved ahead of stable instructions.",
            )
        )
    elif uncached_input >= 80_000:
        items.append(
            health_item(
                "warn",
                "Uncached input is expensive",
                f"Latest uncached input was {fmt_int(uncached_input)} tokens.",
                "Prefer heading searches, file excerpts, and durable summaries before opening broad source or log files.",
            )
        )

    if output_total >= 20_000 or output_cost_share >= 60.0:
        items.append(
            health_item(
                "warn",
                "Output is dominating cost",
                f"Latest output plus reasoning was {fmt_int(output_total)} tokens and {output_cost_share:.1f}% of estimated turn cost.",
                "Use concise final replies by default; expand only for reviews, designs, or requested documentation.",
            )
        )

    if cache_ratio >= 80.0 and (input_growth >= 40_000 or input_growth_ratio >= 30.0):
        items.append(
            health_item(
                "warn",
                "High cache may be hiding context growth",
                f"Latest input grew by {fmt_int(input_growth)} tokens over the recent trend window while cache stayed high.",
                "Checkpoint durable state, summarize decisions, and consider a fresh session if the next task is broad. If this is a workflow/release/handoff task, suggest workflow-health / 体检.",
            )
        )

    if cache_spread >= 35.0 and input_total >= 8_000:
        items.append(
            health_item(
                "warn",
                "Cache hit rate is unstable",
                f"Recent cache ratio spread was {cache_spread:.1f} percentage points.",
                "Keep stable instructions and reusable context at the beginning; avoid changing the prompt prefix with dynamic details. If the spread recurs during workflow work, suggest workflow-health / 体检.",
            )
        )

    if cache_ratio >= 80.0 and savings_ratio < 40.0 and input_total >= 8_000:
        items.append(
            health_item(
                "warn",
                "Cache savings are weaker than the ratio suggests",
                f"Estimated cache savings for the latest turn were {savings_ratio:.1f}%.",
                "Check output/reasoning share and uncached input; high cached tokens alone is not enough. If this affects workflow or release decisions, suggest workflow-health / 体检.",
            )
        )

    return items


def scope_dict(label: str, sessions: list[SessionUsage], totals: TokenTotals, rates: CostRates) -> dict[str, Any]:
    latest = sessions[-1] if sessions else None
    tokens = totals.as_dict()
    return {
        "label": label,
        "sessions": len(sessions),
        "latest_session": latest.session_id if latest else "",
        "latest_cwd": latest.cwd if latest else "",
        "latest_updated_at": iso_from_mtime(latest.updated_at) if latest else "",
        "latest_last_turn": latest.last_turn.as_dict() if latest else TokenTotals().as_dict(),
        "latest_context_window": latest.context_window if latest else 0,
        "tokens": tokens,
        "metrics": token_metrics(tokens, rates),
        "estimated_cost_usd": estimate_cost(tokens, rates),
    }


def latest_turn_dict(current_scope: dict[str, Any], rates: CostRates) -> dict[str, Any]:
    tokens = dict(current_scope.get("latest_last_turn") or TokenTotals().as_dict())
    context_window = int(current_scope.get("latest_context_window") or 0)
    total = int(tokens.get("total_tokens") or 0)
    return {
        "label": "latest turn",
        "sessions": 1 if total else 0,
        "tokens": tokens,
        "metrics": token_metrics(tokens, rates),
        "estimated_cost_usd": estimate_cost(tokens, rates),
        "context_window": context_window,
        "context_pressure": pct_float(total, context_window),
    }


def project_breakdown_dict(sessions: list[SessionUsage], project_roots: list[ProjectRoot], rates: CostRates) -> list[dict[str, Any]]:
    grouped: dict[str, list[SessionUsage]] = {}
    for session in sessions:
        name = infer_project(session, project_roots) if project_roots else "(unassigned)"
        grouped.setdefault(name, []).append(session)

    rows: list[dict[str, Any]] = []
    for name, group_sessions in grouped.items():
        rows.append(scope_dict(name, group_sessions, sum_sessions(group_sessions), rates))
    rows.sort(key=lambda row: row["tokens"]["total_tokens"], reverse=True)
    return rows


def recent_sessions_dict(sessions: list[SessionUsage], rates: CostRates, limit: int = 20) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for session in sorted(sessions, key=lambda item: item.updated_at, reverse=True)[:limit]:
        tokens = session.totals.as_dict()
        rows.append(
            {
                "session_id": session.session_id,
                "session_short": session.session_id[:8] if session.session_id else "",
                "cwd": session.cwd,
                "cwd_name": Path(session.cwd).name if session.cwd else "",
                "updated_at": iso_from_mtime(session.updated_at),
                "model": session.model,
                "provider": session.provider,
                "tokens": tokens,
                "context_window": session.context_window,
                "last_turn": session.last_turn.as_dict(),
                "estimated_cost_usd": estimate_cost(tokens, rates),
            }
        )
    return rows


def select_project_scope(
    explicit_project: str,
    latest: SessionUsage | None,
    sessions: list[SessionUsage],
    project_roots: list[ProjectRoot],
) -> tuple[str, str, list[SessionUsage], str]:
    if explicit_project:
        project_path = explicit_project
        return (
            project_path,
            Path(project_path).name or project_path,
            [session for session in sessions if is_under(session.cwd, project_path)],
            "explicit project path",
        )

    if latest and project_roots:
        active_name = infer_project(latest, project_roots)
        roots_by_name = project_by_name(project_roots)
        active_root = roots_by_name.get(active_name)
        if active_root:
            inferred_sessions = [
                session
                for session in sessions
                if infer_project(session, project_roots) == active_name
            ]
            return (
                str(active_root.path),
                active_name,
                inferred_sessions,
                "inferred from latest session transcript",
            )

    project_path = latest.cwd if latest and latest.cwd else os.getcwd()
    return (
        project_path,
        Path(project_path).name or project_path,
        [session for session in sessions if is_under(session.cwd, project_path)],
        "latest session cwd",
    )


def print_text(result: dict[str, Any]) -> None:
    print("Codex token usage")
    print(f"Codex home: {result['codex_home']}")
    print(f"Active project: {result['project_label']} ({result['project_scope_method']})")
    print(f"Project path: {result['project_path']}")
    print(f"Session files with token events: {result['session_files_with_tokens']}")
    if result.get("warnings"):
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    print()

    rows = [
        ("latest", result["latest_turn"]),
        ("current", result["current"]),
        ("project", result["project"]),
        ("total", result["total"]),
    ]
    header = (
        f"{'Scope':<10} {'Sessions':>8} {'Total':>14} {'Input':>14} "
        f"{'Uncached':>14} {'Cached':>14} {'Cache%':>8} {'Output':>14}"
    )
    print(header)
    print("-" * len(header))
    for label, scope in rows:
        tokens = scope["tokens"]
        metrics = scope["metrics"]
        print(
            f"{label:<10} {scope['sessions']:>8} {fmt_int(tokens['total_tokens']):>14} "
            f"{fmt_int(tokens['input_tokens']):>14} {fmt_int(metrics['uncached_input_tokens']):>14} "
            f"{fmt_int(tokens['cached_input_tokens']):>14} {metrics['cached_input_ratio']:>7.1f}% "
            f"{fmt_int(tokens['output_tokens'] + tokens['reasoning_output_tokens']):>14}"
        )
    print()
    current = result["current"]
    print(f"Current session: {current['latest_session'] or '(none)'}")
    if current.get("latest_cwd"):
        print(f"Current cwd: {current['latest_cwd']}")
    if current.get("latest_updated_at"):
        print(f"Current updated: {current['latest_updated_at']}")
    trend = result.get("efficiency_trend") or {}
    if trend.get("event_count"):
        print()
        print("Efficiency trend")
        print(
            f"Recent events: {trend['event_count']} | "
            f"input growth: {fmt_int(int(trend['input_growth_tokens']))} "
            f"({trend['input_growth_ratio']:.1f}%) | "
            f"cache spread: {trend['cache_ratio_spread']:.1f} pp | "
            f"cache savings: {trend['latest_cache_savings_ratio']:.1f}% | "
            f"effective cost: ${trend['latest_effective_cost_per_million_usd']:.2f}/M"
        )
    if result.get("health"):
        print()
        print("Health")
        for item in result["health"]:
            print(f"- {item['level'].upper()}: {item['title']} - {item['action']}")


def bar(value: int, maximum: int, width: int = 24) -> str:
    if maximum <= 0:
        return "░" * width
    filled = round(width * min(max(value / maximum, 0.0), 1.0))
    if value > 0 and filled == 0:
        filled = 1
    return ("█" * filled) + ("░" * (width - filled))


def pct(value: int, maximum: int) -> str:
    if maximum <= 0:
        return "n/a"
    return f"{(value / maximum * 100):.1f}%"


def status_for_context(percent: float) -> str:
    if percent >= 85:
        return "HIGH"
    if percent >= 65:
        return "WATCH"
    return "OK"


def status_for_share(percent: float) -> str:
    if percent >= 25:
        return "HIGH"
    if percent >= 8:
        return "MED"
    return "LOW"


def colorize(text: str, status: str, enabled: bool) -> str:
    if not enabled:
        return text
    color = {
        "OK": "green",
        "LOW": "green",
        "WATCH": "yellow",
        "MED": "yellow",
        "HIGH": "red",
        "WARN": "yellow",
        "DANGER": "red",
    }.get(status, "reset")
    return f"{ANSI[color]}{text}{ANSI['reset']}"


def print_metric(label: str, value: int, maximum: int, suffix: str = "tok") -> None:
    print(f"{label:<14} {bar(value, maximum)}  {fmt_compact(value):>8} {suffix:<3} {pct(value, maximum):>6}")


def print_visual(result: dict[str, Any], color: bool = False) -> None:
    print("Codex token dashboard")
    print(f"Project  {result['project_label']} ({result['project_scope_method']})")
    print(f"Path     {result['project_path']}")
    print(f"Sessions {result['session_files_with_tokens']} with token events")
    rates = result["cost_rates"]
    print(
        "Cost     estimate only, API-equivalent "
        f"(${rates['input_per_million']}/M input, "
        f"${rates['cached_input_per_million']}/M cached, "
        f"${rates['output_per_million']}/M output+reasoning)"
    )
    if result.get("warnings"):
        for warning in result["warnings"]:
            print(f"Warning: {warning}")
    print()

    current_scope = result["current"]
    project_scope = result["project"]
    total_scope = result["total"]
    latest_turn = result["latest_turn"]
    current_total = current_scope["tokens"]["total_tokens"]
    project_total = project_scope["tokens"]["total_tokens"]
    total_total = total_scope["tokens"]["total_tokens"]
    outside_total = max(0, total_total - project_total)
    outside_sessions = max(0, total_scope["sessions"] - project_scope["sessions"])
    max_total = max(total_total, 0)
    print("Now")
    rows = [
        ("latest", int(latest_turn["tokens"]["total_tokens"]), 1),
        ("current", current_total, current_scope["sessions"]),
        ("project", project_total, project_scope["sessions"]),
        ("outside", outside_total, outside_sessions),
        ("total", total_total, total_scope["sessions"]),
    ]
    for label, total, sessions_count in rows:
        sessions = f"{sessions_count} session" if sessions_count == 1 else f"{sessions_count} sessions"
        share = (total / total_total * 100.0) if total_total else 0.0
        status = status_for_share(share)
        status_text = colorize(f"{status:<4}", status, color)
        row_cost = {
            "latest": latest_turn,
            "current": current_scope,
            "project": project_scope,
            "outside": {"estimated_cost_usd": max(0.0, total_scope["estimated_cost_usd"] - project_scope["estimated_cost_usd"])},
            "total": total_scope,
        }[label]["estimated_cost_usd"]
        print(
            f"{label:<8} {bar(total, max_total)}  {fmt_compact(total):>8} tok  "
            f"{pct(total, total_total):>6}  {fmt_money_columns(row_cost)}  {status_text}  {sessions}"
        )

    project_rows = result.get("project_breakdown") or []
    if project_rows:
        print()
        print("Projects inferred (bars relative to largest project)")
        max_project_total = max((row["tokens"]["total_tokens"] for row in project_rows), default=total_total)
        for row in project_rows[:8]:
            value = row["tokens"]["total_tokens"]
            sessions = f"{row['sessions']} session" if row["sessions"] == 1 else f"{row['sessions']} sessions"
            share = (value / total_total * 100.0) if total_total else 0.0
            status = status_for_share(share)
            status_text = colorize(f"{status:<4}", status, color)
            print(
                f"{row['label']:<24} {bar(value, max_project_total, width=18)}  "
                f"{fmt_compact(value):>8} tok  {pct(value, total_total):>6}  "
                f"{fmt_money_columns(row['estimated_cost_usd'])}  {status_text}  {sessions}"
            )

    current = current_scope
    current_tokens = current["tokens"]
    current_metrics = current["metrics"]
    print()
    print("Latest turn mix")
    latest_tokens = latest_turn["tokens"]
    latest_metrics = latest_turn["metrics"]
    trend = result.get("efficiency_trend") or {}
    latest_total = max(1, int(latest_metrics["effective_total_tokens"]))
    latest_rows = [
        ("uncached", latest_metrics["uncached_input_tokens"], latest_total),
        ("cached", latest_tokens["cached_input_tokens"], latest_total),
        ("output", latest_tokens["output_tokens"] + latest_tokens["reasoning_output_tokens"], latest_total),
    ]
    for label, value, maximum in latest_rows:
        print_metric(label, value, maximum)

    print()
    print("Current session mix")
    total = max(1, int(current_metrics["effective_total_tokens"]))
    rows = [
        ("uncached", current_metrics["uncached_input_tokens"], total),
        ("cached", current_tokens["cached_input_tokens"], total),
        ("output", current_tokens["output_tokens"] + current_tokens["reasoning_output_tokens"], total),
    ]
    for label, value, maximum in rows:
        print_metric(label, value, maximum)

    trend = result.get("efficiency_trend") or {}
    if trend.get("event_count"):
        print()
        print("Efficiency trend")
        print(
            f"events         {int(trend['event_count'])} recent token events"
        )
        print(
            f"input growth   {fmt_compact(int(trend['input_growth_tokens']))}  "
            f"{trend['input_growth_ratio']:.1f}% over window"
        )
        print(
            f"cache spread   {trend['cache_ratio_spread']:.1f} pp  "
            f"avg {trend['avg_cache_ratio']:.1f}%"
        )
        print(
            f"cache savings  {trend['latest_cache_savings_ratio']:.1f}%  "
            f"{fmt_money(trend.get('latest_cache_savings_usd') or 0.0)} latest turn"
        )
        print(
            f"eff cost       ${trend['latest_effective_cost_per_million_usd']:.2f}/M effective tokens"
        )

    last_turn = current["latest_last_turn"]
    window = int(current.get("latest_context_window") or 0)
    last_total = int(last_turn.get("total_tokens") or 0)
    context_percent = (last_total / window * 100.0) if window else 0.0
    print()
    print("Context pressure")
    context_status = status_for_context(context_percent)
    print(
        f"{bar(last_total, window)}  {fmt_compact(last_total)} / {fmt_compact(window)}  "
        f"{context_percent:.1f}%  {colorize(context_status, context_status, color)}"
    )
    print(f"latest  {current['latest_session'] or '(none)'}")
    if current.get("latest_updated_at"):
        print(f"updated {current['latest_updated_at']}")
    if result.get("health"):
        print()
        print("Health")
        for item in result["health"]:
            status = colorize(f"{item['level'].upper():<6}", item["level"].upper(), color)
            print(f"{status} {item['title']}: {item['action']}")


def pct_float(value: int | float, maximum: int | float) -> float:
    if maximum <= 0:
        return 0.0
    return max(0.0, min(100.0, float(value) / float(maximum) * 100.0))


def html_num(value: int) -> str:
    return escape(fmt_int(int(value or 0)))


def html_money(value: float) -> str:
    return escape(fmt_money(float(value or 0.0)))


def css_width(percent: float) -> str:
    return f"{max(0.0, min(100.0, percent)):.3f}%"


def mix_segments(tokens: dict[str, int]) -> str:
    uncached = max(0, int(tokens.get("input_tokens") or 0) - int(tokens.get("cached_input_tokens") or 0))
    cached = int(tokens.get("cached_input_tokens") or 0)
    output = int(tokens.get("output_tokens") or 0)
    reasoning = int(tokens.get("reasoning_output_tokens") or 0)
    total = max(1, uncached + cached + output + reasoning)
    fields = [
        ("uncached", "Uncached input", uncached),
        ("cached", "Cached input", cached),
        ("output", "Output", output),
        ("reasoning", "Reasoning", reasoning),
    ]
    return "\n".join(
        f'<span class="seg {cls}" style="width:{css_width(pct_float(value, total))};flex-basis:{css_width(pct_float(value, total))}" title="{label}: {fmt_int(value)}"></span>'
        for cls, label, value in fields
        if value > 0
    )


def write_html_dashboard(result: dict[str, Any], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    latest_turn = result["latest_turn"]
    current = result["current"]
    project = result["project"]
    total = result["total"]
    latest_tokens = latest_turn["tokens"]
    latest_metrics = latest_turn["metrics"]
    trend = result.get("efficiency_trend") or {}
    current_tokens = current["tokens"]
    project_tokens = project["tokens"]
    total_tokens = total["tokens"]
    context_window = int(current.get("latest_context_window") or 0)
    last_turn_total = int(current.get("latest_last_turn", {}).get("total_tokens") or 0)
    context_pct = pct_float(last_turn_total, context_window)
    context_class = "danger" if context_pct >= 85 else "warn" if context_pct >= 65 else "ok"
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    status_label = "临界" if context_class == "danger" else "关注" if context_class == "warn" else "稳定"
    latest_updated = current.get("latest_updated_at") or "(unknown)"
    latest_session = current.get("latest_session") or "(none)"

    if context_class == "danger":
        action_title = "先保存状态，再开新会话"
        action_detail = "上下文压力已经接近上限，建议先 checkpoint，再从恢复点继续。"
    elif context_class == "warn":
        action_title = "先收束任务，再继续扩展"
        action_detail = "上下文开始变重，建议写下当前目标、改动和下一步，再进入新分支任务。"
    else:
        action_title = "可以继续当前任务"
        action_detail = "上下文压力可控，继续保持精准读取和小步验证。"

    mix_items = [
        ("未缓存输入", int(latest_metrics["uncached_input_tokens"]), "uncached"),
        ("缓存输入", int(latest_tokens.get("cached_input_tokens") or 0), "cached"),
        ("输出", int(latest_tokens.get("output_tokens") or 0), "output"),
        ("推理输出", int(latest_tokens.get("reasoning_output_tokens") or 0), "reasoning"),
    ]
    mix_colors = {
        "uncached": "#3b82f6",
        "cached": "#14b8a6",
        "output": "#f59e0b",
        "reasoning": "#ef476f",
    }
    mix_total = max(1, sum(value for _, value, _ in mix_items))
    cursor = 0.0
    stops = []
    for _, value, cls in mix_items:
        start = cursor
        cursor += (value / mix_total) * 100.0
        color = mix_colors[cls]
        stops.append(f"{color} {start:.2f}% {cursor:.2f}%")
    donut_style = "conic-gradient(" + ", ".join(stops) + ")"
    donut_legend = "".join(
        f"""
        <div class="legend-item">
          <span class="legend-dot {escape(cls)}"></span>
          <span>{escape(label)}</span>
          <strong>{pct(value, mix_total)}</strong>
        </div>
        """
        for label, value, cls in mix_items
    )
    mix_stat_cards = "".join(
        f"""
        <div class="mini-stat">
          <span>{escape(label)}</span>
          <strong>{html_num(value)}</strong>
        </div>
        """
        for label, value, _ in mix_items
    )

    headline_cards = [
        ("总 Token", html_num(int(total_tokens["total_tokens"])), "全部本地 session", "violet"),
        ("最近一轮", html_num(int(latest_tokens["total_tokens"])), "当前对话最新 token 事件", "blue"),
        ("上下文压力", f"{context_pct:.1f}%", f"{fmt_compact(last_turn_total)} / {fmt_compact(context_window)}", context_class),
        ("估算成本", html_money(total["estimated_cost_usd"]), "API 等价估算，非账单", "amber"),
    ]
    headline_html = "".join(
        f"""
        <section class="headline-card {escape(cls)}">
          <span>{escape(label)}</span>
          <strong>{value}</strong>
          <em>{escape(detail)}</em>
        </section>
        """
        for label, value, detail, cls in headline_cards
    )

    scope_rows = [
        ("当前会话", current, current_tokens),
        (f"当前项目 / {result['project_label']}", project, project_tokens),
        ("全部会话", total, total_tokens),
    ]
    max_scope = max(1, int(total_tokens["total_tokens"]))
    scope_html = "".join(
        f"""
        <div class="scope-row">
          <div>
            <strong>{escape(label)}</strong>
            <span>{scope['sessions']} {'session' if scope['sessions'] == 1 else 'sessions'} · {html_money(scope['estimated_cost_usd'])}</span>
          </div>
          <div class="scope-meter"><span style="width:{css_width(pct_float(int(tokens['total_tokens']), max_scope))}"></span></div>
          <b>{pct(int(tokens['total_tokens']), int(total_tokens['total_tokens']))}</b>
        </div>
        """
        for label, scope, tokens in scope_rows
    )

    trend_items = [
        ("事件窗口", str(int(trend.get("event_count") or 0))),
        ("输入增长", f"{fmt_compact(int(trend.get('input_growth_tokens') or 0))} / {float(trend.get('input_growth_ratio') or 0.0):.1f}%"),
        ("缓存波动", f"{float(trend.get('cache_ratio_spread') or 0.0):.1f} pp"),
        ("缓存节省", f"{float(trend.get('latest_cache_savings_ratio') or 0.0):.1f}%"),
    ]
    trend_html = "".join(
        f"<div class=\"trend-pill\"><span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
        for label, value in trend_items
    )

    warnings_html = "".join(f"<li>{escape(w)}</li>" for w in result.get("warnings", []))
    if warnings_html:
        warnings_html = f"<section class=\"warning-band\"><strong>Warnings</strong><ul>{warnings_html}</ul></section>"

    cached_ratio = float(latest_metrics.get("cached_input_ratio", 0.0) or 0.0)
    output_share = float(latest_metrics.get("output_cost_share", 0.0) or 0.0)
    input_growth = int(trend.get("input_growth_tokens") or 0)
    cache_spread = float(trend.get("cache_ratio_spread") or 0.0)
    cache_savings_ratio = float(trend.get("latest_cache_savings_ratio") or 0.0)
    effective_cpm = float(latest_metrics.get("effective_cost_per_million_usd", 0.0) or 0.0)
    cache_level = "ok" if cached_ratio >= 60.0 else "warn"
    output_level = "warn" if output_share >= 65.0 else "ok"
    trend_level = "warn" if input_growth >= 20000 or cache_spread >= 30.0 else "ok"
    health_cards = [
        (
            context_class,
            "上下文状态",
            f"最近一轮上下文压力 {context_pct:.1f}%，使用 {fmt_compact(last_turn_total)} / {fmt_compact(context_window)}。",
            action_detail,
        ),
        (
            cache_level,
            "输入缓存效率",
            f"缓存输入占比 {cached_ratio:.1f}%，未缓存输入 {html_num(int(latest_metrics['uncached_input_tokens']))}。",
            "保持稳定的系统提示和 skill 路由，减少大段上下文反复送入。",
        ),
        (
            output_level,
            "输出与推理占比",
            f"输出/推理 token 为 {html_num(int(latest_metrics['output_plus_reasoning_tokens']))}，成本占比 {output_share:.1f}%。",
            "如果输出占比过高，优先收敛问题范围，分批生成长文档或大段代码。",
        ),
        (
            trend_level,
            "最近趋势",
            f"输入增长 {fmt_compact(input_growth)}，缓存波动 {cache_spread:.1f} pp，缓存节省 {cache_savings_ratio:.1f}%。",
            "增长过快时先沉淀当前状态，再进入新任务或新会话。",
        ),
        (
            "ok" if float(latest_metrics.get("cache_savings_usd", 0.0) or 0.0) > 0.0 else "warn",
            "成本参考",
            f"本轮缓存估算节省 {html_money(latest_metrics['cache_savings_usd'])}，有效成本约 ${effective_cpm:.2f}/M token。",
            "这是本地估算值，用来辅助判断上下文和输出结构，不等同于最终账单。",
        ),
    ]

    health_html = "".join(
        f"""
        <li class="{escape(level)}">
          <strong>{escape(title)}</strong>
          <span>{detail}</span>
          <em>{escape(action)}</em>
        </li>
        """
        for level, title, detail, action in health_cards
    )

    project_rows = []
    project_breakdown = result.get("project_breakdown") or []
    max_project = max((row["tokens"]["total_tokens"] for row in project_breakdown), default=1)
    for row in project_breakdown[:10]:
        value = int(row["tokens"]["total_tokens"])
        project_rows.append(
            f"""
            <tr>
              <td><strong>{escape(row['label'])}</strong></td>
              <td class="num">{row['sessions']}</td>
              <td class="num">{html_num(value)}</td>
              <td><div class="row-meter"><span style="width:{css_width(pct_float(value, max_project))}"></span></div></td>
              <td class="num">{pct(value, int(total_tokens['total_tokens']))}</td>
            </tr>
            """
        )

    recent_rows = []
    for row in result.get("recent_sessions", [])[:12]:
        tokens = row["tokens"]
        total_value = int(tokens["total_tokens"])
        recent_rows.append(
            f"""
            <tr>
              <td><code>{escape(row['session_short'] or '(none)')}</code></td>
              <td>{escape(row['cwd_name'] or row['cwd'] or '(unknown)')}</td>
              <td>{escape(row['updated_at'])}</td>
              <td class="num">{html_num(total_value)}</td>
              <td><div class="token-stack mini">{mix_segments(tokens)}</div></td>
            </tr>
            """
        )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>小Q Token Dashboard</title>
  <style>
    :root {{
      --bg: #f7f4ff;
      --ink: #171321;
      --muted: #6d647a;
      --panel: rgba(255, 255, 255, 0.86);
      --panel-solid: #ffffff;
      --line: rgba(42, 31, 75, 0.14);
      --purple: #6d4aff;
      --cyan: #12b8c8;
      --mint: #14b8a6;
      --amber: #f59e0b;
      --pink: #ef476f;
      --ok: #12a66a;
      --warn: #c76b00;
      --danger: #cf274c;
      --shadow: 0 22px 70px rgba(44, 31, 84, 0.16);
    }}
    * {{ box-sizing: border-box; }}
    html {{ min-width: 320px; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 10% 8%, rgba(109, 74, 255, 0.22), transparent 28%),
        radial-gradient(circle at 92% 0%, rgba(18, 184, 200, 0.18), transparent 26%),
        linear-gradient(135deg, #fffdf7 0%, #f2ecff 48%, #eefbff 100%);
      min-height: 100vh;
    }}
    .shell {{ width: min(1280px, calc(100% - 36px)); margin: 0 auto; padding: 24px 0 30px; }}
    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
      gap: 18px;
      min-height: 430px;
      padding: 22px;
      border: 1px solid rgba(255, 255, 255, 0.72);
      border-radius: 8px;
      background:
        linear-gradient(130deg, rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.58)),
        linear-gradient(135deg, rgba(109, 74, 255, 0.10), rgba(20, 184, 166, 0.08));
      box-shadow: var(--shadow);
      overflow: hidden;
      position: relative;
    }}
    .hero::after {{
      content: "";
      position: absolute;
      left: 22px;
      right: 22px;
      bottom: 0;
      height: 5px;
      background: linear-gradient(90deg, var(--purple), var(--cyan), var(--amber), var(--pink));
      border-radius: 8px 8px 0 0;
    }}
    .hero-main, .hero-visual {{ position: relative; z-index: 1; min-width: 0; }}
    .brand-row {{ display: flex; align-items: center; justify-content: space-between; gap: 14px; }}
    .brand {{ display: flex; align-items: center; gap: 12px; min-width: 0; }}
    .logo {{
      width: 50px;
      height: 50px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: #009FE8;
      box-shadow: 0 14px 28px rgba(0, 159, 232, 0.28);
      overflow: hidden;
    }}
    .logo svg {{ width: 100%; height: 100%; display: block; }}
    .brand span {{ display: block; color: var(--muted); font-size: 12px; font-weight: 800; }}
    .brand strong {{ display: block; font-size: 17px; }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      min-height: 36px;
      padding: 7px 10px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.66);
      font-size: 13px;
      font-weight: 800;
      white-space: nowrap;
    }}
    .status-light {{ width: 9px; height: 9px; border-radius: 50%; background: var(--ok); }}
    .status-light.warn {{ background: var(--warn); }}
    .status-light.danger {{ background: var(--danger); }}
    h1 {{ margin: 32px 0 8px; font-size: 58px; line-height: 0.95; letter-spacing: 0; }}
    .hero-copy {{ max-width: 720px; color: var(--muted); font-size: 15px; line-height: 1.55; }}
    code {{ background: rgba(255,255,255,0.74); border: 1px solid var(--line); border-radius: 5px; padding: 2px 5px; overflow-wrap: anywhere; }}
    .headline-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin-top: 26px; }}
    .headline-card {{
      min-width: 0;
      padding: 13px;
      background: rgba(255, 255, 255, 0.72);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .headline-card span, .mini-stat span, .trend-pill span {{ display: block; color: var(--muted); font-size: 12px; }}
    .headline-card strong {{ display: block; margin-top: 8px; font-size: 24px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .headline-card em {{ display: block; margin-top: 5px; color: var(--muted); font-size: 12px; font-style: normal; overflow-wrap: anywhere; }}
    .hero-visual {{
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 12px;
      padding: 18px;
      background: rgba(18, 17, 31, 0.9);
      color: #f8fbff;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.14);
    }}
    .visual-title {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }}
    .visual-title strong {{ font-size: 17px; }}
    .visual-title span {{ color: #aeb6ca; font-size: 12px; }}
    .donut-wrap {{ display: grid; grid-template-columns: minmax(190px, 0.85fr) minmax(0, 1fr); gap: 16px; align-items: center; }}
    .donut {{
      width: min(260px, 100%);
      aspect-ratio: 1;
      border-radius: 50%;
      background: {donut_style};
      position: relative;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.22), 0 24px 42px rgba(0,0,0,0.24);
      margin: 0 auto;
    }}
    .donut::after {{
      content: "";
      position: absolute;
      inset: 20%;
      border-radius: 50%;
      background: #141424;
      box-shadow: inset 0 0 0 1px rgba(255,255,255,0.12);
    }}
    .donut-center {{
      position: absolute;
      inset: 30%;
      z-index: 1;
      display: grid;
      place-items: center;
      text-align: center;
      font-variant-numeric: tabular-nums;
    }}
    .donut-center strong {{ display: block; font-size: 25px; line-height: 1; }}
    .donut-center span {{ display: block; margin-top: 5px; color: #aeb6ca; font-size: 11px; }}
    .legend {{ display: grid; gap: 8px; }}
    .legend-item {{ display: grid; grid-template-columns: 12px minmax(0,1fr) auto; align-items: center; gap: 8px; color: #dce6f7; font-size: 13px; }}
    .legend-item strong {{ font-variant-numeric: tabular-nums; }}
    .legend-dot {{ width: 10px; height: 10px; border-radius: 3px; }}
    .legend-dot.uncached, .uncached {{ background: #3b82f6; }}
    .legend-dot.cached, .cached {{ background: #14b8a6; }}
    .legend-dot.output, .output {{ background: #f59e0b; }}
    .legend-dot.reasoning, .reasoning {{ background: #ef476f; }}
    .mini-stat-grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
    .mini-stat {{ min-width: 0; padding: 10px; border-radius: 8px; background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); }}
    .mini-stat strong {{ display: block; margin-top: 5px; font-size: 17px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .action-strip {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      margin: 14px 0;
      padding: 14px 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 12px 30px rgba(44, 31, 84, 0.10);
    }}
    .action-strip strong {{ display: block; font-size: 16px; }}
    .action-strip span {{ display: block; margin-top: 3px; color: var(--muted); }}
    .action-chip {{ padding: 8px 10px; border-radius: 8px; background: #171321; color: #fff; font-weight: 800; white-space: nowrap; }}
    .content-grid {{ display: grid; grid-template-columns: minmax(0, 0.9fr) minmax(360px, 1.1fr); gap: 14px; }}
    .panel {{
      min-width: 0;
      padding: 16px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 12px 30px rgba(44, 31, 84, 0.09);
    }}
    .panel-title {{ display: flex; justify-content: space-between; gap: 14px; align-items: baseline; margin-bottom: 12px; }}
    h2 {{ margin: 0; font-size: 17px; line-height: 1.2; }}
    .panel-title span {{ color: var(--muted); font-size: 12px; }}
    .scope-list {{ display: grid; gap: 10px; }}
    .scope-row {{ display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(120px, 1fr) auto; gap: 12px; align-items: center; }}
    .scope-row strong, .scope-row span {{ display: block; overflow-wrap: anywhere; }}
    .scope-row span {{ color: var(--muted); font-size: 12px; margin-top: 3px; }}
    .scope-row b {{ font-variant-numeric: tabular-nums; }}
    .scope-meter, .row-meter, .token-stack {{
      width: 100%;
      height: 10px;
      background: rgba(23, 19, 33, 0.10);
      border-radius: 6px;
      overflow: hidden;
      line-height: 0;
    }}
    .scope-meter span, .row-meter span {{
      display: block;
      height: 100%;
      min-width: 0;
      background: linear-gradient(90deg, var(--purple), var(--cyan));
      border-radius: 6px;
    }}
    .token-stack {{
      display: flex;
      align-items: stretch;
      gap: 0;
      padding: 0;
      height: 12px;
    }}
    .token-stack.mini {{ min-width: 160px; }}
    .seg {{
      display: block;
      flex: 0 0 auto;
      min-width: 0;
      height: 100%;
      border-radius: 0;
    }}
    .seg:first-child {{ border-radius: 6px 0 0 6px; }}
    .seg:last-child {{ border-radius: 0 6px 6px 0; }}
    .seg:first-child:last-child {{ border-radius: 6px; }}
    .trend-strip {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }}
    .trend-pill {{ min-width: 0; padding: 10px; border-radius: 8px; border: 1px solid var(--line); background: rgba(255,255,255,0.64); }}
    .trend-pill strong {{ display: block; margin-top: 5px; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }}
    .health-list {{ list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }}
    .health-list li {{ border-left: 4px solid var(--ok); background: rgba(20, 184, 166, 0.09); padding: 10px 12px; border-radius: 6px; }}
    .health-list li.warn {{ border-left-color: var(--warn); background: rgba(245, 158, 11, 0.12); }}
    .health-list li.danger {{ border-left-color: var(--danger); background: rgba(239, 71, 111, 0.10); }}
    .health-list strong, .health-list span, .health-list em {{ display: block; }}
    .health-list span {{ color: var(--muted); margin-top: 3px; }}
    .health-list em {{ color: var(--ink); font-style: normal; margin-top: 5px; }}
    details {{ margin-top: 14px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; box-shadow: 0 12px 30px rgba(44, 31, 84, 0.08); }}
    summary {{ cursor: pointer; padding: 14px 16px; font-weight: 850; }}
    .details-body {{ padding: 0 16px 16px; overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: middle; }}
    th {{ color: var(--muted); font-weight: 850; background: rgba(255,255,255,0.58); }}
    td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .warning-band {{ margin: 12px 0; padding: 12px 16px; color: #7a4a00; background: #fff7e8; border: 1px solid #f0d7a6; border-radius: 8px; }}
    .warning-band strong {{ display: block; margin-bottom: 6px; }}
    .warning-band ul {{ margin: 0; padding-left: 18px; }}
    @media (max-width: 980px) {{
      .hero, .content-grid, .donut-wrap, .action-strip {{ grid-template-columns: 1fr; }}
      .headline-grid, .mini-stat-grid, .trend-strip {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      h1 {{ font-size: 44px; }}
    }}
    @media (max-width: 560px) {{
      .shell {{ width: min(100% - 20px, 1280px); padding: 10px 0 20px; }}
      .hero, .hero-visual, .panel {{ padding: 14px; }}
      .brand-row, .visual-title, .panel-title {{ display: block; }}
      .status-pill {{ margin-top: 12px; }}
      .headline-grid, .mini-stat-grid, .trend-strip {{ grid-template-columns: 1fr; }}
      .scope-row {{ grid-template-columns: 1fr; gap: 6px; }}
      h1 {{ font-size: 34px; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-main">
        <div class="brand-row">
          <div class="brand">
            <div class="logo" aria-label="小Q Logo">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" role="img" aria-labelledby="q-logo-title q-logo-desc">
                <title id="q-logo-title">Q logo stable rounded icon</title>
                <desc id="q-logo-desc">Current Xiao Q logo: a rounded Q-blue tile with an organic yellow Q stroke selected from the V28 direction.</desc>
                <rect width="256" height="256" rx="42" fill="#009FE8"/>
                <g transform="translate(12 0)">
                  <path d="M190 116 C190 92 166 67 128 60 C88 52 52 72 41 113 C29 158 60 191 107 198 C139 203 166 188 176 165 C183 169 191 180 197 195" fill="none" stroke="#FFD84F" stroke-width="36" stroke-linecap="round" stroke-linejoin="round"/>
                </g>
              </svg>
            </div>
            <div><span>Token Console</span><strong>小Q 工作流仪表盘</strong></div>
          </div>
          <div class="status-pill"><span class="status-light {context_class}"></span>{escape(status_label)} · 上下文</div>
        </div>
        <h1>Token 总览</h1>
        <p class="hero-copy">突出总量、占比和上下文压力；明细已收进底部折叠区。生成时间 {escape(generated_at)}，活跃项目 <code>{escape(result['project_label'])}</code>。</p>
        <div class="headline-grid">{headline_html}</div>
      </div>
      <div class="hero-visual">
        <div class="visual-title">
          <strong>最近一轮 Token 占比</strong>
          <span>{html_money(latest_turn['estimated_cost_usd'])} estimated</span>
        </div>
        <div class="donut-wrap">
          <div class="donut">
            <div class="donut-center"><div><strong>{html_num(int(latest_tokens['total_tokens']))}</strong><span>latest turn</span></div></div>
          </div>
          <div class="legend">{donut_legend}</div>
        </div>
        <div class="mini-stat-grid">{mix_stat_cards}</div>
      </div>
    </section>
    {warnings_html}
    <section class="action-strip">
      <div>
        <strong>{escape(action_title)}</strong>
        <span>{escape(action_detail)}</span>
      </div>
      <div class="action-chip">{context_pct:.1f}% pressure</div>
    </section>
    <section class="content-grid">
      <div class="panel">
        <div class="panel-title"><h2>范围对比</h2><span>token share</span></div>
        <div class="scope-list">{scope_html}</div>
      </div>
      <div class="panel">
        <div class="panel-title"><h2>效率趋势</h2><span>latest event window</span></div>
        <div class="trend-strip">{trend_html}</div>
      </div>
    </section>
    <section class="panel" style="margin-top:14px">
      <div class="panel-title"><h2>健康建议</h2><span>{escape(status_label)} state</span></div>
      <ul class="health-list">{health_html}</ul>
    </section>
    <details>
      <summary>项目与会话明细</summary>
      <div class="details-body">
        <h2>Projects</h2>
        <table>
          <thead><tr><th>Project</th><th class="num">Sessions</th><th class="num">Tokens</th><th>Relative</th><th class="num">Share</th></tr></thead>
          <tbody>{''.join(project_rows)}</tbody>
        </table>
        <h2 style="margin-top:18px">Recent Sessions</h2>
        <table>
          <thead><tr><th>Session</th><th>CWD</th><th>Updated</th><th class="num">Tokens</th><th>Mix</th></tr></thead>
          <tbody>{''.join(recent_rows)}</tbody>
        </table>
      </div>
    </details>
  </main>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")
    return output_path


def print_html_result(path: Path, opened: bool) -> None:
    print("Codex token dashboard")
    print(f"HTML: {path}")
    print(f"Opened: {'yes' if opened else 'no'}")


def open_dashboard(path: Path) -> bool:
    try:
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            webbrowser.open(path.resolve().as_uri())
        return True
    except Exception:
        return False


def main() -> int:
    configure_output()
    parser = argparse.ArgumentParser(description="Summarize local Codex token usage.")
    parser.add_argument("--codex-home", default=str(default_codex_home()), help="Codex home directory.")
    parser.add_argument("--project", default="", help="Project path for project-token aggregation.")
    parser.add_argument("--projects-root", default=str(default_projects_root()), help="Root containing known project directories for breakdown.")
    parser.add_argument("--format", choices=("text", "json", "visual", "html", "dashboard"), default="text", help="Output format.")
    parser.add_argument("--html-out", default="", help="Output path for --format html/dashboard.")
    parser.add_argument("--open", action="store_true", help="Open the generated HTML dashboard. HTML/dashboard output opens by default; this flag is kept for compatibility.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the generated HTML dashboard.")
    parser.add_argument("--input-rate", type=float, default=DEFAULT_INPUT_RATE, help="Estimated uncached input USD per 1M tokens.")
    parser.add_argument("--cached-input-rate", type=float, default=DEFAULT_CACHED_INPUT_RATE, help="Estimated cached input USD per 1M tokens.")
    parser.add_argument("--output-rate", type=float, default=DEFAULT_OUTPUT_RATE, help="Estimated output/reasoning USD per 1M tokens.")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto", help="ANSI colors for visual output.")
    parser.add_argument("--self-test", action="store_true", help="Run the incremental cache regression without reading real sessions.")
    args = parser.parse_args()

    if args.self_test:
        result = incremental_cache_self_test()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "pass" else 1

    rates = CostRates(
        input_per_million=args.input_rate,
        cached_input_per_million=args.cached_input_rate,
        output_per_million=args.output_rate,
    )
    codex_home = Path(args.codex_home).expanduser()
    project_roots = discover_project_roots(Path(args.projects_root).expanduser())
    sessions = scan_sessions(codex_home, project_roots)
    current_sessions = sessions[-1:] if sessions else []
    latest = current_sessions[-1] if current_sessions else None
    project_path, project_label, project_sessions, project_scope_method = select_project_scope(
        args.project,
        latest,
        sessions,
        project_roots,
    )

    warnings: list[str] = []
    if not sessions:
        warnings.append("No token_count events found under the Codex sessions directory.")
    if not project_sessions and project_path:
        warnings.append("No token_count sessions matched the selected project path.")

    current_scope = scope_dict("current", current_sessions, sum_sessions(current_sessions), rates)
    project_scope = scope_dict("project", project_sessions, sum_sessions(project_sessions), rates)
    total_scope = scope_dict("total", sessions, sum_sessions(sessions), rates)
    efficiency_trend = session_efficiency_trend(latest, rates)
    result = {
        "codex_home": str(codex_home),
        "project_path": project_path,
        "project_label": project_label,
        "project_scope_method": project_scope_method,
        "session_files_with_tokens": len(sessions),
        "warnings": warnings,
        "cost_rates": {
            "input_per_million": rates.input_per_million,
            "cached_input_per_million": rates.cached_input_per_million,
            "output_per_million": rates.output_per_million,
        },
        "cost_estimate_note": "API-equivalent estimate from local logs; not an official Codex bill.",
        "current": current_scope,
        "project": project_scope,
        "total": total_scope,
        "latest_turn": latest_turn_dict(current_scope, rates),
        "efficiency_trend": efficiency_trend,
        "health": token_health(current_scope, rates, efficiency_trend),
        "project_roots": [{"name": root.name, "path": str(root.path)} for root in project_roots],
        "project_breakdown_method": "cwd path first, then project path/name mentions in each local session transcript",
        "project_breakdown": project_breakdown_dict(sessions, project_roots, rates),
        "recent_sessions": recent_sessions_dict(sessions, rates),
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.format in {"html", "dashboard"}:
        html_path = Path(args.html_out).expanduser() if args.html_out else codex_home / "reports" / "token_dashboard.html"
        html_path = write_html_dashboard(result, html_path)
        opened = False
        if not args.no_open:
            opened = open_dashboard(html_path)
            if not opened:
                warnings.append("Could not open dashboard with the OS default browser.")
        print_html_result(html_path, opened)
    elif args.format == "visual":
        use_color = args.color == "always" or (args.color == "auto" and sys.stdout.isatty())
        print_visual(result, color=use_color)
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
