#!/usr/bin/env python3
"""Advisory context telemetry; never changes model limits or native compaction."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _run_token_usage() -> dict[str, Any]:
    script = Path(__file__).with_name("token_usage.py")
    if not script.exists():
        raise SystemExit(f"token_usage.py not found beside {Path(__file__).name}")
    proc = subprocess.run(
        [sys.executable, str(script), "--format", "json"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or f"token_usage.py failed with {proc.returncode}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"token_usage.py returned invalid JSON: {exc}") from exc


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _classify(data: dict[str, Any], max_safe: float, critical: float) -> dict[str, Any]:
    latest = data.get("latest_turn") or {}
    latest_metrics = latest.get("metrics") or {}
    trend = data.get("efficiency_trend") or {}
    pressure = _num(latest.get("context_pressure"))
    cache_ratio = _num(latest_metrics.get("cached_input_ratio"))
    uncached = _num(latest_metrics.get("uncached_input_tokens"))
    spread = _num(trend.get("cache_ratio_spread"))
    growth = _num(trend.get("input_growth_tokens"))
    growth_ratio = _num(trend.get("input_growth_ratio"))
    pressure_delta = _num(trend.get("context_pressure_delta"))

    flags: list[str] = []
    if pressure >= critical:
        level = "critical"
        flags.append(f"context pressure {pressure:.1f}% >= critical gate {critical:.1f}%")
    elif pressure >= max_safe:
        level = "throttle"
        flags.append(f"context pressure {pressure:.1f}% >= max-safe gate {max_safe:.1f}%")
    elif pressure >= 60.0:
        level = "watch"
        flags.append(f"context pressure {pressure:.1f}% is in watch range")
    else:
        level = "ok"

    if spread > 50.0:
        flags.append(f"cache ratio spread {spread:.1f} pp is unstable")
        if level == "ok":
            level = "watch"
    if growth > 0:
        flags.append(f"recent input grew by {growth:.0f} tokens")
        if level == "ok":
            level = "watch"
    if growth_ratio >= 0.30 and pressure >= 60.0 and level == "watch":
        level = "throttle"
        flags.append(f"input growth ratio {growth_ratio:.2f} with elevated pressure")
    if pressure_delta > 15.0 and pressure >= 60.0 and level == "watch":
        level = "throttle"
        flags.append(f"context pressure rose by {pressure_delta:.1f} percentage points")

    if not flags:
        flags.append("no pressure gate tripped")

    action_by_level = {
        "ok": "Continue with targeted reads; avoid loading large files unless decision-critical.",
        "watch": "Checkpoint before broad work; keep dynamic outputs in files and pass paths forward. For workflow-rule, release, or handoff work, suggest workflow-health / 体检 before expanding further.",
        "throttle": "Prefer targeted reads and a checkpoint at the next meaningful boundary. Continue authorized work; do not split tasks or run health suites solely because of this advisory level.",
        "critical": "Checkpoint material state and let native compaction handle context. Continue the authorized task with targeted reads; this telemetry is advisory, not a stop or model-limit override.",
    }
    return {
        "level": level,
        "pressure": pressure,
        "cache_ratio": cache_ratio,
        "uncached_input_tokens": uncached,
        "cache_ratio_spread": spread,
        "input_growth_tokens": growth,
        "input_growth_ratio": growth_ratio,
        "context_pressure_delta": pressure_delta,
        "flags": flags,
        "recommended_action": action_by_level[level],
    }


def _clip(text: str, max_chars: int = 600) -> str:
    text = str(text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 18].rstrip() + " ... [truncated]"


def _lines(values: list[str] | None, fallback: str, max_items: int = 8, max_chars: int = 240) -> str:
    if not values:
        return fallback
    clipped = [f"- {_clip(item, max_chars)}" for item in values[:max_items]]
    if len(values) > max_items:
        clipped.append(f"- ... [{len(values) - max_items} more omitted; put details in handoff_paths]")
    return "\n".join(clipped)


def _write_packet(path: Path, args: argparse.Namespace, data: dict[str, Any], result: dict[str, Any]) -> None:
    now = _dt.datetime.now().astimezone().isoformat(timespec="seconds")
    latest_session = (data.get("current") or {}).get("latest_session", "unknown")
    project = data.get("project_label") or data.get("project_path") or "unknown"
    packet = f"""TASK-PACKET v1
packet_type: compact-entry
created_at: {now}
context_governor:
- level: {result['level']}
- latest_context_pressure: {result['pressure']:.1f}%
- latest_cache_ratio: {result['cache_ratio']:.1f}%
- cache_ratio_spread: {result['cache_ratio_spread']:.1f} pp
- input_growth_tokens: {result['input_growth_tokens']:.0f}
- recommended_action: {result['recommended_action']}
session:
- latest_session: {latest_session}
- inferred_project: {project}
objective:
{_clip(args.objective or 'TBD')}
source_of_truth:
{_lines(args.source_of_truth, 'TBD')}
current_state:
{_clip(args.current_state or 'TBD')}
changed_files:
{_lines(args.changed_files, 'TBD')}
constraints:
{_lines(args.constraints, 'TBD')}
no_edit_zones:
{_lines(args.no_edit_zones, 'TBD')}
next_actions:
{_lines(args.next_action, 'TBD')}
evidence_chain:
{_lines(args.evidence_anchor, 'TBD')}
validation:
{_lines(args.validation, 'TBD')}
handoff_paths:
{_lines(args.handoff_path, 'TBD')}
residual_risks:
{_lines(args.residual_risk, 'TBD')}
read_rule:
- Read this entry first. Open handoff_paths or source_of_truth details only when the next action is ambiguous, risky, or validation fails.
- Do not paste long logs, reports, diffs, or sub-agent output into this packet; store them as files and link their paths here.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_suffix(path.suffix + ".tmp")
    with staged.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(packet)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(staged, path)
    if path.read_text(encoding="utf-8") != packet:
        raise RuntimeError("task packet readback mismatch after atomic replacement")


def _validate_packet_inputs(args: argparse.Namespace) -> None:
    if not args.packet_out:
        return
    missing = []
    if not (args.objective or "").strip(): missing.append("--objective")
    if not (args.current_state or "").strip(): missing.append("--current-state")
    if not args.source_of_truth: missing.append("--source-of-truth")
    if not args.next_action: missing.append("--next-action")
    if not (args.validation or args.evidence_anchor): missing.append("--validation or --evidence-anchor")
    if missing:
        raise SystemExit("packet-out requires durable recovery fields: " + ", ".join(missing))


def _print_text(result: dict[str, Any], data: dict[str, Any], packet_out: str | None) -> None:
    latest = data.get("latest_turn") or {}
    tokens = latest.get("tokens") or {}
    print(f"Context Governor: {result['level'].upper()}")
    print(f"Latest context pressure: {result['pressure']:.1f}%")
    print(f"Latest cache ratio: {result['cache_ratio']:.1f}%")
    print(f"Uncached input tokens: {result['uncached_input_tokens']:.0f}")
    print(f"Cache ratio spread: {result['cache_ratio_spread']:.1f} pp")
    print(f"Input growth tokens: {result['input_growth_tokens']:.0f}")
    print(f"Latest total tokens: {_num(tokens.get('total_tokens')):.0f}")
    print("Flags:")
    for flag in result["flags"]:
        print(f"- {flag}")
    print(f"Recommended action: {result['recommended_action']}")
    if packet_out:
        print(f"Task packet: {packet_out}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--max-safe", type=float, default=70.0)
    parser.add_argument("--critical", type=float, default=85.0)
    parser.add_argument("--strict", action="store_true", help="exit 2 on throttle or critical")
    parser.add_argument("--packet-out", help="write a compact task packet to this path")
    parser.add_argument("--objective")
    parser.add_argument("--current-state")
    parser.add_argument("--source-of-truth", action="append")
    parser.add_argument("--changed-files", action="append")
    parser.add_argument("--constraints", action="append")
    parser.add_argument("--no-edit-zones", action="append")
    parser.add_argument("--next-action", action="append")
    parser.add_argument("--validation", action="append")
    parser.add_argument("--evidence-anchor", action="append")
    parser.add_argument("--handoff-path", action="append")
    parser.add_argument("--residual-risk", action="append")
    args = parser.parse_args(argv)
    _validate_packet_inputs(args)

    data = _run_token_usage()
    result = _classify(data, args.max_safe, args.critical)

    if args.packet_out:
        _write_packet(Path(args.packet_out), args, data, result)

    if args.format == "json":
        payload = {"result": result, "packet_out": args.packet_out, "token_usage": data}
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        _print_text(result, data, args.packet_out)

    if args.strict and result["level"] in {"throttle", "critical"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
