#!/usr/bin/env python3
"""Bounded real-use telemetry pilot for q-workflow.

The pilot is deliberately separate from ``q_workflow_manager.py``.  It invokes
only read-only manager commands, records compact operational metrics, and owns
only files inside an explicit pilot directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from workflow_file_ops import (
        WorkflowFileLockError,
        acquire_lock,
        atomic_replace_bytes,
        release_lock,
    )
except ModuleNotFoundError as exc:
    if exc.name == "workflow_file_ops":
        print(
            "workflow_pilot.py must stay beside workflow_file_ops.py; use the installed q-workflow scripts directory.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    raise


STATE_NAME = "PILOT_STATE.json"
SAMPLES_NAME = "samples.jsonl"
SUMMARY_JSON_NAME = "SUMMARY.json"
SUMMARY_MARKDOWN_NAME = "SUMMARY.md"
LOCK_NAME = ".pilot.lock"
ACTIVE = "ACTIVE"
TERMINAL_STATES = {"COMPLETE", "STOPPED"}
PAUSED_STATES = {"PAUSED_USER", "PAUSED_RESOURCE", "PAUSED_AUTOMATION_CLEANUP"}


class PilotError(RuntimeError):
    """Raised for a bounded pilot contract failure."""


def now_iso() -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def local_date() -> str:
    return datetime.now().astimezone().date().isoformat()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PilotError(f"missing required pilot file: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PilotError(f"invalid UTF-8 JSON pilot file: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PilotError(f"pilot JSON root must be an object: {path}")
    return value


def validate_state(state: dict[str, Any], path: Path) -> None:
    required = (
        "format_version",
        "pilot_id",
        "trace_id",
        "run_state",
        "system_volume",
        "system_volume_band",
        "automation",
        "sampling",
        "authority",
        "preserved_focus",
        "resume_condition",
    )
    missing = [key for key in required if key not in state]
    if missing:
        raise PilotError(f"pilot state missing fields {missing}: {path}")
    if state.get("format_version") != 1:
        raise PilotError(f"unsupported pilot format_version: {state.get('format_version')!r}")
    if not isinstance(state.get("sampling"), dict) or not isinstance(state.get("automation"), dict):
        raise PilotError("pilot sampling and automation fields must be objects")


def load_samples(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not raw.strip():
                continue
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise PilotError(f"sample line {line_number} is not an object: {path}")
            rows.append(value)
    except UnicodeDecodeError as exc:
        raise PilotError(f"invalid UTF-8 samples file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PilotError(f"invalid JSONL sample at line {exc.lineno}: {path}") from exc
    return rows


def write_samples(path: Path, rows: list[dict[str, Any]]) -> None:
    data = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)
    atomic_replace_bytes(path, data.encode("utf-8"))


def volume_root(volume: str) -> Path:
    if os.name == "nt":
        cleaned = volume.rstrip("\\/")
        return Path(cleaned + "\\")
    return Path(volume)


def classify_volume_band(free_gib: float, green_minimum: float = 3, yellow_minimum: float = 1) -> str:
    if free_gib >= green_minimum:
        return "GREEN"
    if free_gib >= yellow_minimum:
        return "YELLOW"
    if free_gib > 0:
        return "RED"
    return "CRITICAL"


def volume_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    root = volume_root(str(state["system_volume"]))
    try:
        usage = shutil.disk_usage(root)
    except OSError as exc:
        raise PilotError(f"cannot inspect system volume {root}: {exc}") from exc
    free_gib = round(usage.free / (1024**3), 2)
    thresholds = state.get("resource_thresholds_gib", {})
    green_minimum = float(thresholds.get("green_minimum", 3))
    yellow_minimum = float(thresholds.get("yellow_minimum", 1))
    band = classify_volume_band(free_gib, green_minimum, yellow_minimum)
    return {
        "volume": str(state["system_volume"]),
        "free_bytes": usage.free,
        "free_gib": free_gib,
        "band": band,
    }


def apply_volume_snapshot(state: dict[str, Any], snapshot: dict[str, Any]) -> None:
    state["system_volume_free_bytes"] = snapshot["free_bytes"]
    state["system_volume_free_gib"] = snapshot["free_gib"]
    state["system_volume_band"] = snapshot["band"]


def parse_json_output(output: str) -> Any:
    stripped = output.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        for raw in reversed(stripped.splitlines()):
            candidate = raw.strip()
            if not candidate.startswith(("{", "[")):
                continue
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue
    return None


def payload_status(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    direct = payload.get("status")
    if isinstance(direct, str):
        return direct
    summary = payload.get("summary")
    if isinstance(summary, dict) and isinstance(summary.get("status"), str):
        return str(summary["status"])
    return None


def failure_from_payload(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    direct = payload.get("failure_class")
    if isinstance(direct, str) and direct:
        return direct
    probes = payload.get("probes")
    if isinstance(probes, list):
        classes = sorted(
            {
                str(row.get("failure_class"))
                for row in probes
                if isinstance(row, dict) and row.get("status") != "pass" and row.get("failure_class")
            }
        )
        if len(classes) == 1:
            return classes[0]
        if len(classes) > 1:
            return "multiple-probe-failures"
    return None


def compact_evidence(name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    if name == "doctor":
        probes = []
        for row in payload.get("probes", []):
            if not isinstance(row, dict):
                continue
            probes.append(
                {
                    "name": row.get("name"),
                    "status": row.get("status"),
                    "failure_class": row.get("failure_class"),
                    "exit_code": row.get("returncode"),
                    "elapsed_ms": row.get("elapsed_ms"),
                }
            )
        return {"scope": payload.get("scope"), "failures": payload.get("failures", []), "probes": probes}
    if name == "status":
        active = payload.get("active") if isinstance(payload.get("active"), dict) else {}
        pointer = active.get("recovery_pointer") if isinstance(active.get("recovery_pointer"), dict) else {}
        return {
            "task_id": pointer.get("task_id"),
            "trace_id": pointer.get("trace_id"),
            "state_revision": pointer.get("state_revision"),
            "work_state": pointer.get("work_state"),
            "task_count": payload.get("task_count"),
            "core_surfaces": payload.get("core_surfaces"),
            "remote_status": payload.get("remote_status"),
        }
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    if name == "task-list":
        return {
            "count": summary.get("count"),
            "failures": summary.get("failures"),
            "focus_task_id": summary.get("focus_task_id"),
        }
    if name == "core-surfaces":
        return {
            "skills": summary.get("skills"),
            "failures": summary.get("failures"),
            "status": summary.get("status"),
        }
    return {}


def run_manager_probe(
    name: str,
    arguments: list[str],
    *,
    manager: Path,
    profile: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(manager),
        "--profile",
        str(profile),
        "--format",
        "json",
        *arguments,
    ]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env={**os.environ, "Q_PROFILE_PATH": str(profile)},
        )
        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        output = completed.stdout or completed.stderr or ""
        payload = parse_json_output(output)
        observed_status = payload_status(payload)
        passed = completed.returncode == 0 and observed_status == "pass"
        if passed:
            failure_class = None
        elif payload is None:
            failure_class = "invalid-json" if output.strip() else "empty-output"
        elif observed_status is None or observed_status not in {"pass", "blocked", "attention", "failed"}:
            failure_class = "invalid-status"
        else:
            failure_class = failure_from_payload(payload) or "nonzero-exit"
        result = {
            "name": name,
            "status": "pass" if passed else "blocked",
            "failure_class": failure_class,
            "exit_code": completed.returncode,
            "elapsed_ms": elapsed_ms,
            "observed_status": observed_status,
            "evidence": compact_evidence(name, payload),
        }
        if payload is None:
            result["output_length"] = len(output)
            result["output_sha256"] = hashlib.sha256(output.encode("utf-8", errors="replace")).hexdigest()
        return result
    except subprocess.TimeoutExpired as exc:
        return {
            "name": name,
            "status": "blocked",
            "failure_class": "timeout",
            "exit_code": 124,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "observed_status": None,
            "evidence": {"timeout_seconds": exc.timeout},
        }
    except OSError as exc:
        return {
            "name": name,
            "status": "blocked",
            "failure_class": "spawn-error",
            "exit_code": 127,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "observed_status": None,
            "evidence": {"error_type": type(exc).__name__},
        }


def probe_specs(
    command_timeout: int,
    doctor_timeout: int,
    doctor_mode: str,
    rounds: int,
) -> list[tuple[str, list[str], int]]:
    doctor_arguments = ["doctor"]
    if doctor_mode == "full":
        doctor_arguments.extend(["--full", "--rounds", str(rounds)])
    return [
        ("status", ["status"], command_timeout),
        ("doctor", doctor_arguments, doctor_timeout),
        ("task-list", ["task", "list"], command_timeout),
        ("core-surfaces", ["surfaces", "--tier", "core", "--strict"], command_timeout),
    ]


def sample_key(source: str, run_key: str | None) -> str:
    if run_key:
        return f"{source}:{run_key}"
    if source in {"baseline", "scheduled"}:
        return f"{source}:{local_date()}"
    return f"manual:{datetime.now().astimezone().strftime('%Y%m%dT%H%M%S%z')}"


def has_sample_key(rows: list[dict[str, Any]], key: str) -> bool:
    return any(row.get("sample_key") == key for row in rows)


def sync_counts(state: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    sampling = state["sampling"]
    sampling["samples_completed"] = len(rows)
    sampling["baseline_samples_completed"] = sum(row.get("source") == "baseline" for row in rows)
    sampling["scheduled_samples_completed"] = sum(row.get("source") == "scheduled" for row in rows)
    sampling["manual_samples_completed"] = sum(row.get("source") == "manual" for row in rows)
    sampling["pass_samples"] = sum(row.get("status") == "pass" for row in rows)
    sampling["blocked_samples"] = sum(row.get("status") != "pass" for row in rows)


def focus_observation(state: dict[str, Any], probes: list[dict[str, Any]]) -> dict[str, bool | None]:
    status_probe = next((row for row in probes if row.get("name") == "status"), None)
    if not status_probe or status_probe.get("status") != "pass":
        return {"identity_matches_pilot_start": None, "revision_changed_from_start": None}
    evidence = status_probe.get("evidence", {})
    expected = state.get("preserved_focus", {})
    identity_matches = (
        evidence.get("task_id") == expected.get("task_id")
        and evidence.get("trace_id") == expected.get("trace_id")
    )
    return {
        "identity_matches_pilot_start": identity_matches,
        "revision_changed_from_start": evidence.get("state_revision") != expected.get("state_revision"),
    }


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return round(ordered[index], 3)


def metric_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "p50": None, "max": None, "mean": None}
    return {
        "count": len(values),
        "min": round(min(values), 3),
        "p50": percentile(values, 0.50),
        "max": round(max(values), 3),
        "mean": round(sum(values) / len(values), 3),
    }


def build_summary(state: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    probes = [probe for row in rows for probe in row.get("probes", []) if isinstance(probe, dict)]
    sample_failures = Counter(
        str(row.get("failure_class")) for row in rows if row.get("failure_class")
    )
    probe_failures = Counter(
        str(row.get("failure_class")) for row in probes if row.get("failure_class")
    )
    by_probe: dict[str, Any] = {}
    for name in sorted({str(row.get("name")) for row in probes if row.get("name")}):
        selected = [row for row in probes if row.get("name") == name]
        values = [float(row["elapsed_ms"]) for row in selected if isinstance(row.get("elapsed_ms"), (int, float))]
        by_probe[name] = {
            "runs": len(selected),
            "passes": sum(row.get("status") == "pass" for row in selected),
            "blocked": sum(row.get("status") != "pass" for row in selected),
            "elapsed_ms": metric_summary(values),
            "failure_classes": dict(sorted(Counter(str(row.get("failure_class")) for row in selected if row.get("failure_class")).items())),
        }
    sample_elapsed = [float(row["elapsed_ms"]) for row in rows if isinstance(row.get("elapsed_ms"), (int, float))]
    free_values = [float(row["resource_after"]["free_gib"]) for row in rows if isinstance(row.get("resource_after"), dict) and isinstance(row["resource_after"].get("free_gib"), (int, float))]
    return {
        "format_version": 1,
        "pilot_id": state.get("pilot_id"),
        "trace_id": state.get("trace_id"),
        "generated_at": now_iso(),
        "run_state": state.get("run_state"),
        "planned_end_at": state.get("planned_end_at"),
        "samples": {
            "total": len(rows),
            "expected": state.get("sampling", {}).get("expected_total_samples"),
            "baseline": sum(row.get("source") == "baseline" for row in rows),
            "scheduled": sum(row.get("source") == "scheduled" for row in rows),
            "manual": sum(row.get("source") == "manual" for row in rows),
            "passes": sum(row.get("status") == "pass" for row in rows),
            "blocked": sum(row.get("status") != "pass" for row in rows),
            "pass_rate": round(sum(row.get("status") == "pass" for row in rows) / len(rows), 4) if rows else None,
        },
        "sample_elapsed_ms": metric_summary(sample_elapsed),
        "probes": by_probe,
        "sample_failure_classes": dict(sorted(sample_failures.items())),
        "probe_failure_classes": dict(sorted(probe_failures.items())),
        "focus_identity_mismatch_count": sum(row.get("focus_identity_matches_pilot_start") is False for row in rows),
        "focus_revision_changed_count": sum(row.get("focus_revision_changed_from_start") is True for row in rows),
        "resource_free_gib": metric_summary(free_values),
        "latest_sample": rows[-1] if rows else None,
        "release_state": "local-only",
        "remote_status": "unproven",
    }


def markdown_summary(summary: dict[str, Any]) -> str:
    samples = summary["samples"]
    elapsed = summary["sample_elapsed_ms"]
    lines = [
        "# q-workflow real-use pilot summary",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- State: `{summary['run_state']}`",
        f"- Samples: `{samples['total']}/{samples.get('expected')}` (baseline {samples['baseline']}, scheduled {samples['scheduled']}, manual {samples['manual']})",
        f"- Pass rate: `{samples['pass_rate'] if samples['pass_rate'] is not None else 'n/a'}`",
        f"- Sample elapsed min/median/max: `{elapsed['min']}/{elapsed['p50']}/{elapsed['max']} ms`",
        f"- Focus identity mismatches / revision changes: `{summary['focus_identity_mismatch_count']} / {summary['focus_revision_changed_count']}`",
        "",
        "## Probe baseline",
        "",
        "| Probe | Runs | Pass | Blocked | Min ms | Median ms | Max ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for name, row in summary["probes"].items():
        metric = row["elapsed_ms"]
        lines.append(
            f"| {name} | {row['runs']} | {row['passes']} | {row['blocked']} | {metric['min']} | {metric['p50']} | {metric['max']} |"
        )
    lines.extend(
        [
            "",
            "## Failure classes",
            "",
            f"- Sample: `{json.dumps(summary['sample_failure_classes'], ensure_ascii=False, sort_keys=True)}`",
            f"- Probe: `{json.dumps(summary['probe_failure_classes'], ensure_ascii=False, sort_keys=True)}`",
            "",
            "Local-only telemetry; remote state remains unproven.",
            "",
        ]
    )
    return "\n".join(lines)


def write_summary(pilot_dir: Path, state: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = build_summary(state, rows)
    atomic_replace_bytes(pilot_dir / SUMMARY_JSON_NAME, json_bytes(summary))
    atomic_replace_bytes(pilot_dir / SUMMARY_MARKDOWN_NAME, markdown_summary(summary).encode("utf-8"))
    state["sampling"]["summary_updated_at"] = summary["generated_at"]
    return summary


def state_paths(pilot_dir: Path) -> tuple[Path, Path, Path]:
    return pilot_dir / STATE_NAME, pilot_dir / SAMPLES_NAME, pilot_dir / LOCK_NAME


def scheduled_target(state: dict[str, Any]) -> int:
    return int(state.get("automation", {}).get("scheduled_runs", 0))


def reconcile_after_sample(state: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    sync_counts(state, rows)
    target = scheduled_target(state)
    completed = int(state["sampling"].get("scheduled_samples_completed", 0))
    if target > 0 and completed >= target and state["run_state"] not in TERMINAL_STATES:
        state["run_state"] = "STOPPING"
        state["automation"]["automation_delete"] = "pending"


def sample_pilot(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    pilot_dir = args.pilot_dir.resolve()
    state_path, samples_path, lock_path = state_paths(pilot_dir)
    descriptor = acquire_lock(lock_path)
    try:
        state = load_json(state_path)
        validate_state(state, state_path)
        rows = load_samples(samples_path)
        reconcile_after_sample(state, rows)
        key = sample_key(args.source, args.run_key)
        duplicate = next((row for row in rows if row.get("sample_key") == key), None)
        if has_sample_key(rows, key):
            state["updated_at"] = now_iso()
            write_summary(pilot_dir, state, rows)
            atomic_replace_bytes(state_path, json_bytes(state))
            return {"status": "skipped", "reason": "duplicate-sample-key-reconciled", "sample_key": key, "sample": duplicate, "run_state": state["run_state"]}, 0
        if state["run_state"] == "STOPPING":
            state["updated_at"] = now_iso()
            write_summary(pilot_dir, state, rows)
            atomic_replace_bytes(state_path, json_bytes(state))
            return {"status": "skipped", "reason": "awaiting-automation-cleanup", "sample_key": key, "run_state": state["run_state"]}, 0
        if state["run_state"] in TERMINAL_STATES | PAUSED_STATES:
            return {"status": "skipped", "reason": f"run-state-{state['run_state'].lower()}", "sample_key": key}, 0
        if state["run_state"] != ACTIVE:
            raise PilotError(f"unsupported run_state: {state['run_state']!r}")

        resource_before = volume_snapshot(state)
        apply_volume_snapshot(state, resource_before)
        started_at = now_iso()
        started = time.perf_counter()
        if resource_before["band"] != "GREEN":
            state["run_state"] = "PAUSED_RESOURCE"
            sample = {
                "format_version": 1,
                "pilot_id": state["pilot_id"],
                "trace_id": state["trace_id"],
                "sample_key": key,
                "source": args.source,
                "started_at": started_at,
                "finished_at": now_iso(),
                "status": "blocked",
                "failure_class": f"resource-{resource_before['band'].lower()}",
                "exit_code": 2,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "resource_before": resource_before,
                "resource_after": resource_before,
                "focus_identity_matches_pilot_start": None,
                "focus_revision_changed_from_start": None,
                "doctor_mode": "not-run",
                "probes": [],
            }
            rows.append(sample)
            write_samples(samples_path, rows)
            reconcile_after_sample(state, rows)
            state["updated_at"] = now_iso()
            write_summary(pilot_dir, state, rows)
            atomic_replace_bytes(state_path, json_bytes(state))
            return sample, 2

        manager = (args.manager or Path(__file__).with_name("q_workflow_manager.py")).resolve()
        profile = Path(str(state["authority"]["profile"])).resolve()
        if not manager.is_file():
            raise PilotError(f"manager script is missing: {manager}")
        if not profile.is_file():
            raise PilotError(f"profile is missing: {profile}")
        doctor_mode = args.doctor_mode
        if doctor_mode == "auto":
            scheduled_done = int(state["sampling"].get("scheduled_samples_completed", 0))
            doctor_mode = "full" if args.source == "scheduled" and scheduled_done + 1 >= scheduled_target(state) else "quick"
        doctor_timeout = args.doctor_timeout or (600 if doctor_mode == "full" else 180)
        probes = [
            run_manager_probe(
                name,
                command,
                manager=manager,
                profile=profile,
                timeout_seconds=timeout_seconds,
            )
            for name, command, timeout_seconds in probe_specs(
                args.command_timeout, doctor_timeout, doctor_mode, args.rounds
            )
        ]
        resource_after = volume_snapshot(state)
        apply_volume_snapshot(state, resource_after)
        focus = focus_observation(state, probes)
        blocked = [row for row in probes if row["status"] != "pass"]
        classes = sorted({str(row["failure_class"]) for row in blocked if row.get("failure_class")})
        failure_class: str | None = None
        if resource_after["band"] != "GREEN":
            failure_class = f"resource-{resource_after['band'].lower()}"
            state["run_state"] = "PAUSED_RESOURCE"
        elif len(classes) == 1:
            failure_class = classes[0]
        elif len(classes) > 1:
            failure_class = "multiple-probe-failures"
        status = "pass" if not blocked and resource_after["band"] == "GREEN" else "blocked"
        sample = {
            "format_version": 1,
            "pilot_id": state["pilot_id"],
            "trace_id": state["trace_id"],
            "sample_key": key,
            "source": args.source,
            "started_at": started_at,
            "finished_at": now_iso(),
            "status": status,
            "failure_class": failure_class,
            "exit_code": 0 if status == "pass" else 1,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
            "resource_before": resource_before,
            "resource_after": resource_after,
            "focus_identity_matches_pilot_start": focus["identity_matches_pilot_start"],
            "focus_revision_changed_from_start": focus["revision_changed_from_start"],
            "doctor_mode": doctor_mode,
            "probes": probes,
        }
        rows.append(sample)
        write_samples(samples_path, rows)
        reconcile_after_sample(state, rows)
        state["updated_at"] = now_iso()
        summary = write_summary(pilot_dir, state, rows)
        atomic_replace_bytes(state_path, json_bytes(state))
        return {"status": status, "sample": sample, "summary": summary["samples"], "run_state": state["run_state"]}, sample["exit_code"]
    finally:
        release_lock(lock_path, descriptor)


def init_pilot(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if not args.yes:
        raise PilotError("init creates pilot state; rerun with --yes")
    if args.scheduled_runs < 1:
        raise PilotError("--scheduled-runs must be an integer >= 1")
    try:
        first = datetime.fromisoformat(args.first_at)
    except ValueError as exc:
        raise PilotError("--first-at must be an ISO-8601 timestamp with UTC offset") from exc
    if first.tzinfo is None:
        raise PilotError("--first-at must include a UTC offset")
    pilot_dir = args.pilot_dir.resolve()
    state_path, _, lock_path = state_paths(pilot_dir)
    if state_path.exists():
        raise PilotError(f"pilot state already exists: {state_path}")
    descriptor = acquire_lock(lock_path)
    try:
        if state_path.exists():
            raise PilotError(f"pilot state already exists: {state_path}")
        profile = args.profile.resolve()
        if not profile.is_file():
            raise PilotError(f"profile is missing: {profile}")
        planned_end = first + timedelta(days=args.scheduled_runs - 1)
        state: dict[str, Any] = {
            "format_version": 1,
            "pilot_id": args.pilot_id,
            "trace_id": args.trace_id,
            "started_at": now_iso(),
            "planned_first_scheduled_at": first.isoformat(),
            "planned_end_at": planned_end.isoformat(),
            "timezone": str(first.tzinfo),
            "run_state": ACTIVE,
            "release_state": "local-only",
            "remote_status": "unproven",
            "system_volume": args.system_volume,
            "system_volume_band": "UNKNOWN",
            "resource_thresholds_gib": {"green_minimum": 3, "yellow_minimum": 1},
            "automation": {
                "automation_id": None,
                "create_state": "pending",
                "automation_delete": "not_requested",
                "kind": "heartbeat",
                "scheduled_runs": args.scheduled_runs,
            },
            "sampling": {
                "baseline_runs": 1,
                "scheduled_runs": args.scheduled_runs,
                "expected_total_samples": args.scheduled_runs + 1,
                "commands": ["status", "doctor", "task list", "surfaces --tier core --strict"],
                "metrics": ["elapsed_ms", "exit_code", "status", "failure_class", "system_volume_free_gib"],
                "samples_path": str(pilot_dir / SAMPLES_NAME),
                "summary_json_path": str(pilot_dir / SUMMARY_JSON_NAME),
                "summary_markdown_path": str(pilot_dir / SUMMARY_MARKDOWN_NAME),
            },
            "authority": {"profile": str(profile)},
            "preserved_focus": {
                "task_id": args.focus_task_id,
                "trace_id": args.focus_trace_id,
                "state_revision": args.focus_state_revision,
            },
            "resume_condition": "Resume only when run_state is ACTIVE and system_volume_band is GREEN; otherwise record one bounded failure and stop without retry or project-task mutation.",
            "updated_at": now_iso(),
        }
        resource = volume_snapshot(state)
        apply_volume_snapshot(state, resource)
        if resource["band"] != "GREEN":
            state["run_state"] = "PAUSED_RESOURCE"
        validate_state(state, state_path)
        atomic_replace_bytes(state_path, json_bytes(state))
        return {"status": "initialized", "state_path": str(state_path), "run_state": state["run_state"], "resource": resource}, 0
    finally:
        release_lock(lock_path, descriptor)


def report_pilot(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    pilot_dir = args.pilot_dir.resolve()
    state_path, samples_path, lock_path = state_paths(pilot_dir)
    descriptor = acquire_lock(lock_path)
    try:
        state = load_json(state_path)
        validate_state(state, state_path)
        rows = load_samples(samples_path)
        sync_counts(state, rows)
        summary = write_summary(pilot_dir, state, rows)
        state["updated_at"] = now_iso()
        atomic_replace_bytes(state_path, json_bytes(state))
        return summary, 0
    finally:
        release_lock(lock_path, descriptor)


def status_pilot(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    pilot_dir = args.pilot_dir.resolve()
    state_path, samples_path, lock_path = state_paths(pilot_dir)
    descriptor = acquire_lock(lock_path)
    try:
        state = load_json(state_path)
        validate_state(state, state_path)
        rows = load_samples(samples_path)
        sync_counts(state, rows)
        live_resource = volume_snapshot(state)
        latest = rows[-1] if rows else None
        payload = {
            "format_version": 1,
            "pilot_id": state["pilot_id"],
            "trace_id": state["trace_id"],
            "run_state": state["run_state"],
            "planned_end_at": state.get("planned_end_at"),
            "resource": live_resource,
            "samples": {
                "total": len(rows),
                "expected": state["sampling"].get("expected_total_samples"),
                "scheduled": state["sampling"].get("scheduled_samples_completed", 0),
                "scheduled_target": scheduled_target(state),
                "passes": state["sampling"].get("pass_samples", 0),
                "blocked": state["sampling"].get("blocked_samples", 0),
            },
            "automation": state.get("automation"),
            "latest": {
                "sample_key": latest.get("sample_key"),
                "status": latest.get("status"),
                "failure_class": latest.get("failure_class"),
                "finished_at": latest.get("finished_at"),
            }
            if latest
            else None,
        }
        return payload, 0
    finally:
        release_lock(lock_path, descriptor)


def apply_automation_cleanup_result(state: dict[str, Any], result: str) -> None:
    current = state.get("run_state")
    if current not in {"STOPPING", "PAUSED_AUTOMATION_CLEANUP"}:
        raise PilotError(f"automation cleanup requires STOPPING or PAUSED_AUTOMATION_CLEANUP, got {current!r}")
    if result == "verified":
        state["automation"]["automation_delete"] = "verified"
        state["run_state"] = "COMPLETE"
    elif result == "failed":
        state["automation"]["automation_delete"] = "failed"
        state["run_state"] = "PAUSED_AUTOMATION_CLEANUP"
    else:
        raise PilotError(f"unsupported automation cleanup result: {result!r}")


def mutate_state(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    if not args.yes:
        raise PilotError(f"{args.command} changes pilot state; rerun with --yes")
    pilot_dir = args.pilot_dir.resolve()
    state_path, samples_path, lock_path = state_paths(pilot_dir)
    descriptor = acquire_lock(lock_path)
    try:
        state = load_json(state_path)
        validate_state(state, state_path)
        rows = load_samples(samples_path)
        before = state["run_state"]
        if args.command == "pause":
            if before in TERMINAL_STATES:
                raise PilotError(f"cannot pause terminal pilot state {before}")
            if before in {"STOPPING", "PAUSED_AUTOMATION_CLEANUP"}:
                raise PilotError(f"cannot pause while automation cleanup is pending: {before}")
            state["run_state"] = "PAUSED_USER"
        elif args.command == "resume":
            if before not in {"PAUSED_USER", "PAUSED_RESOURCE"}:
                raise PilotError(f"cannot resume pilot state {before}; only user/resource pauses are resumable")
            resource = volume_snapshot(state)
            apply_volume_snapshot(state, resource)
            if resource["band"] != "GREEN":
                raise PilotError(f"cannot resume while system volume is {resource['band']}")
            sync_counts(state, rows)
            if state["sampling"].get("scheduled_samples_completed", 0) >= scheduled_target(state):
                raise PilotError("cannot resume because the scheduled sample target is complete")
            state["run_state"] = ACTIVE
        elif args.command == "stop":
            if before in TERMINAL_STATES:
                raise PilotError(f"cannot stop terminal pilot state {before}")
            state["run_state"] = "STOPPING"
            state["automation"]["automation_delete"] = "pending"
        elif args.command == "finalize":
            apply_automation_cleanup_result(state, args.automation_delete)
        else:
            raise PilotError(f"unsupported pilot mutation: {args.command}")
        state["last_transition"] = {
            "at": now_iso(),
            "from": before,
            "to": state["run_state"],
            "reason": args.reason,
        }
        state["updated_at"] = state["last_transition"]["at"]
        atomic_replace_bytes(state_path, json_bytes(state))
        return {"status": "applied", "transition": state["last_transition"]}, 0
    finally:
        release_lock(lock_path, descriptor)


def self_test() -> dict[str, Any]:
    failures: list[str] = []
    cases = 0

    cases += 1
    if percentile([1, 2, 3, 4], 0.50) != 2:
        failures.append("nearest-rank percentile is incorrect")

    cases += 1
    if sample_key("baseline", "fixed") != "baseline:fixed":
        failures.append("explicit sample key is not stable")

    cases += 1
    parsed = parse_json_output("notice\n{\"status\":\"pass\"}")
    if parsed != {"status": "pass"}:
        failures.append("trailing JSON recovery failed")

    cases += 1
    if failure_from_payload({"probes": [{"status": "blocked", "failure_class": "timeout"}]}) != "timeout":
        failures.append("nested failure class was not preserved")

    with tempfile.TemporaryDirectory(prefix="q-workflow-pilot-selftest-") as raw:
        root = Path(raw)
        state = {
            "format_version": 1,
            "pilot_id": "self-test",
            "trace_id": "SELF-TEST",
            "run_state": ACTIVE,
            "system_volume": str(Path(raw).anchor or "/"),
            "system_volume_band": "GREEN",
            "automation": {"scheduled_runs": 1},
            "sampling": {"expected_total_samples": 2},
            "authority": {"profile": str(root / "profile.json")},
            "preserved_focus": {"task_id": "t", "trace_id": "x", "state_revision": "r"},
            "resume_condition": "test",
        }
        rows = [
            {
                "source": "baseline",
                "status": "pass",
                "elapsed_ms": 10,
                "focus_identity_matches_pilot_start": True,
                "focus_revision_changed_from_start": False,
                "resource_after": {"free_gib": 5},
                "probes": [{"name": "status", "status": "pass", "elapsed_ms": 5, "failure_class": None}],
            },
            {
                "source": "scheduled",
                "status": "blocked",
                "failure_class": "timeout",
                "elapsed_ms": 20,
                "focus_identity_matches_pilot_start": True,
                "focus_revision_changed_from_start": False,
                "resource_after": {"free_gib": 4},
                "probes": [{"name": "status", "status": "blocked", "elapsed_ms": 20, "failure_class": "timeout"}],
            },
        ]
        cases += 1
        summary = build_summary(state, rows)
        if summary["samples"]["total"] != 2 or summary["probe_failure_classes"] != {"timeout": 1}:
            failures.append("summary aggregation failed")

        cases += 1
        write_samples(root / SAMPLES_NAME, rows)
        if load_samples(root / SAMPLES_NAME) != rows:
            failures.append("atomic JSONL round trip failed")

        cases += 1
        atomic_replace_bytes(root / STATE_NAME, json_bytes(state))
        loaded = load_json(root / STATE_NAME)
        try:
            validate_state(loaded, root / STATE_NAME)
        except PilotError as exc:
            failures.append(f"valid self-test state was rejected: {exc}")

        cases += 1
        if not has_sample_key([{"sample_key": "scheduled:2026-08-10"}], "scheduled:2026-08-10"):
            failures.append("duplicate wake detection failed")
        recovery_state = {"run_state": "PAUSED_RESOURCE", "automation": {"scheduled_runs": 1, "automation_delete": "not_requested"}, "sampling": {}}
        reconcile_after_sample(recovery_state, [{"source": "scheduled", "status": "blocked"}])
        if recovery_state["run_state"] != "STOPPING" or recovery_state["automation"]["automation_delete"] != "pending":
            failures.append("final resource failure cannot reconcile to STOPPING")

        cases += 1
        if [classify_volume_band(value) for value in (4, 2, 0.5, 0)] != ["GREEN", "YELLOW", "RED", "CRITICAL"]:
            failures.append("resource band classification failed")

        cases += 1
        cleanup_state = {"run_state": "STOPPING", "automation": {"automation_delete": "pending"}}
        apply_automation_cleanup_result(cleanup_state, "failed")
        if cleanup_state != {"run_state": "PAUSED_AUTOMATION_CLEANUP", "automation": {"automation_delete": "failed"}}:
            failures.append("automation cleanup failure state is not durable")
        apply_automation_cleanup_result(cleanup_state, "verified")
        if cleanup_state != {"run_state": "COMPLETE", "automation": {"automation_delete": "verified"}}:
            failures.append("automation cleanup retry cannot reach COMPLETE")

        cases += 1
        active_state = load_json(root / STATE_NAME)
        active_state["run_state"] = ACTIVE
        active_state["automation"]["automation_delete"] = "not_requested"
        atomic_replace_bytes(root / STATE_NAME, json_bytes(active_state))
        mutate_state(argparse.Namespace(pilot_dir=root, yes=True, command="stop", reason="self-test"))
        stopped = load_json(root / STATE_NAME)
        if stopped["run_state"] != "STOPPING" or stopped["automation"]["automation_delete"] != "pending":
            failures.append("stop did not enter cleanup-pending state")
        stopped["run_state"] = "COMPLETE"
        atomic_replace_bytes(root / STATE_NAME, json_bytes(stopped))
        try:
            mutate_state(argparse.Namespace(pilot_dir=root, yes=True, command="stop", reason="invalid-regression"))
            failures.append("stop allowed terminal-state regression")
        except PilotError:
            pass

    return {"status": "pass" if not failures else "blocked", "cases": cases, "failures": failures}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage a bounded q-workflow real-use telemetry pilot without changing project task state."
    )
    parser.add_argument("--pilot-dir", type=Path, help="Directory containing PILOT_STATE.json.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--self-test", action="store_true", help="Run isolated deterministic tests.")
    commands = parser.add_subparsers(dest="command")

    sample = commands.add_parser("sample", help="Run one idempotent read-only telemetry sample.")
    sample.add_argument("--source", choices=("baseline", "scheduled", "manual"), default="manual")
    sample.add_argument("--run-key", help="Optional idempotency key; scheduled and baseline default to the local date.")
    sample.add_argument("--manager", type=Path, help="Override q_workflow_manager.py for validation or recovery.")
    sample.add_argument("--command-timeout", type=int, default=60, help="Seconds for status/list/surface probes.")
    sample.add_argument("--doctor-timeout", type=int, help="Override doctor timeout; defaults to 180s quick or 600s full.")
    sample.add_argument("--doctor-mode", choices=("auto", "quick", "full"), default="auto", help="Auto uses quick daily and full on the final scheduled sample.")
    sample.add_argument("--rounds", type=int, default=2, help="Positive stability rounds when full doctor runs.")

    init = commands.add_parser("init", help="Create a validated pilot state in an empty pilot directory.")
    init.add_argument("--pilot-id", required=True)
    init.add_argument("--trace-id", required=True)
    init.add_argument("--profile", type=Path, default=Path.home() / ".codex" / "q-profile.json")
    init.add_argument("--scheduled-runs", type=int, default=7)
    init.add_argument("--first-at", required=True, help="ISO-8601 first scheduled timestamp including UTC offset.")
    init.add_argument("--system-volume", default="C:")
    init.add_argument("--focus-task-id")
    init.add_argument("--focus-trace-id")
    init.add_argument("--focus-state-revision")
    init.add_argument("--yes", action="store_true", help="Confirm pilot-state creation.")

    commands.add_parser("status", help="Show live resource, sample, automation, and latest-run status.")
    commands.add_parser("report", help="Regenerate JSON and Markdown aggregate reports.")
    for name in ("pause", "resume", "stop"):
        command = commands.add_parser(name, help=f"{name.title()} pilot execution state.")
        command.add_argument("--reason", required=True, help="Durable reason stored with the transition.")
        command.add_argument("--yes", action="store_true", help="Confirm the state mutation.")
    finalize = commands.add_parser("finalize", help="Record verified or failed cleanup of the bounded automation.")
    finalize.add_argument("--automation-delete", choices=("verified", "failed"), required=True)
    finalize.add_argument("--reason", required=True, help="Durable cleanup result stored with the transition.")
    finalize.add_argument("--yes", action="store_true", help="Confirm the state mutation.")
    return parser


def render_text(payload: dict[str, Any]) -> str:
    if payload.get("status") == "initialized":
        return f"q-workflow pilot: initialized {payload['run_state']} at {payload['state_path']}"
    if "transition" in payload:
        row = payload["transition"]
        return f"q-workflow pilot: {payload['status']} {row['from']} -> {row['to']} ({row['reason']})"
    if "samples" in payload and "run_state" in payload and "resource" in payload:
        samples = payload["samples"]
        lines = [
            f"q-workflow pilot: {payload['run_state']}",
            f"samples: {samples['total']}/{samples['expected']} scheduled={samples['scheduled']}/{samples['scheduled_target']}",
            f"pass/blocked: {samples['passes']}/{samples['blocked']}",
            f"system volume: {payload['resource']['band']} {payload['resource']['free_gib']} GiB free",
            f"automation: {payload['automation'].get('automation_id') or 'pending'} delete={payload['automation'].get('automation_delete', 'not_requested')}",
        ]
        if payload["run_state"] == "STOPPING":
            lines.append("next: delete the automation, then run finalize --automation-delete verified --reason <reason> --yes")
        elif payload["run_state"] == "PAUSED_AUTOMATION_CLEANUP":
            lines.append("next: retry automation deletion once, then finalize with verified or failed")
        elif payload["run_state"] == "PAUSED_RESOURCE":
            lines.append("next: restore GREEN resources before resume --reason <reason> --yes")
        return "\n".join(lines)
    if "samples" in payload and "sample_elapsed_ms" in payload:
        samples = payload["samples"]
        elapsed = payload["sample_elapsed_ms"]
        pass_rate = "n/a" if samples["pass_rate"] is None else str(samples["pass_rate"])
        median = "n/a" if elapsed["p50"] is None else f"{elapsed['p50']}ms"
        maximum = "n/a" if elapsed["max"] is None else f"{elapsed['max']}ms"
        return (
            f"q-workflow pilot report: {payload['run_state']} samples={samples['total']}/{samples.get('expected')} "
            f"pass_rate={pass_rate} median={median} max={maximum}"
        )
    if payload.get("status") == "blocked" and payload.get("error"):
        return f"q-workflow pilot: blocked [{payload.get('failure_class', 'unknown')}] {payload['error']}"
    if payload.get("status") == "skipped":
        return f"q-workflow pilot: skipped ({payload.get('reason')}) key={payload.get('sample_key')}"
    if "sample" in payload:
        sample = payload["sample"]
        return (
            f"q-workflow pilot sample: {sample['status']} key={sample['sample_key']} "
            f"elapsed={sample['elapsed_ms']}ms failure={sample.get('failure_class') or 'none'}"
        )
    if "cases" in payload:
        return f"q-workflow pilot self-test: {payload['status']} cases={payload['cases']} failures={len(payload['failures'])}"
    return json.dumps(payload, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        payload = self_test()
        code = 0 if payload["status"] == "pass" else 1
    else:
        if not args.command:
            parser.error("a command is required unless --self-test is used")
        if not args.pilot_dir:
            parser.error("--pilot-dir is required")
        try:
            if args.command == "init":
                payload, code = init_pilot(args)
            elif args.command == "sample":
                if args.command_timeout < 1 or (args.doctor_timeout is not None and args.doctor_timeout < 1) or args.rounds < 1:
                    raise PilotError("timeouts and rounds must be positive integers")
                payload, code = sample_pilot(args)
            elif args.command == "status":
                payload, code = status_pilot(args)
            elif args.command == "report":
                payload, code = report_pilot(args)
            else:
                payload, code = mutate_state(args)
        except (PilotError, WorkflowFileLockError) as exc:
            payload = {"status": "blocked", "failure_class": "contract", "error": str(exc)}
            code = 2
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.format == "json" else render_text(payload))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
