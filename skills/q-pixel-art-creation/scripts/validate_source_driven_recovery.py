#!/usr/bin/env python3
"""Validate a generic source-driven pixel-training recovery receipt."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED = (
    "active_packet", "mode", "status", "primary_visual_source",
    "cross_visual_source", "primary_tutorial", "capability",
    "observation_units", "current_stage", "last_decision",
    "next_allowed_action", "blocked_actions", "private_shipping_status",
)
STAGES = {"recover", "source_packet", "observation", "mask_unit", "same_unit", "original_transfer"}
DECISIONS_BY_STAGE = {
    "recover": {"RECOVERED", "RECOVER"},
    "source_packet": {"RECOVERED", "PASS_RECOVERY"},
    "observation": {"PASS_SOURCE_PACKET"},
    "mask_unit": {"PASS_OBSERVATION"},
    "same_unit": {"PASS_MASK_UNIT"},
    "original_transfer": {"PASS_SAME_UNIT_REVIEW"},
}


def fail(errors: list[str]) -> int:
    print(json.dumps({"status": "RECOVER", "restart": "REBUILD_FROM_STAGE(recover)", "errors": errors}))
    return 1


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_source_driven_recovery.py RECOVERY.json", file=sys.stderr)
        return 2
    try:
        data = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return fail([f"unreadable receipt: {exc}"])
    if not isinstance(data, dict):
        return fail(["receipt must be a JSON object"])

    errors = [f"missing or empty: {key}" for key in REQUIRED if not data.get(key)]
    if data.get("primary_visual_source") == data.get("cross_visual_source"):
        errors.append("visual sources must be distinct")
    if data.get("current_stage") not in STAGES:
        errors.append("current_stage must be a registered source-driven stage")
    units = data.get("observation_units")
    if not isinstance(units, dict):
        errors.append("observation_units must be an object")
    else:
        for source_key in ("primary_visual_source", "cross_visual_source"):
            source = data.get(source_key)
            if source and not units.get(source):
                errors.append(f"observation_units missing registered source: {source}")
    stage = data.get("current_stage")
    decision = data.get("last_decision")
    if stage in DECISIONS_BY_STAGE and decision not in DECISIONS_BY_STAGE[stage]:
        errors.append("last_decision is incompatible with current_stage")
    if not isinstance(data.get("blocked_actions"), list) or not data.get("blocked_actions"):
        errors.append("blocked_actions must be a non-empty list")
    if data.get("status") == "READY / NO_DRAWING":
        next_action = str(data.get("next_allowed_action", "")).lower()
        blocked = " ".join(str(item).lower() for item in data.get("blocked_actions", []))
        if "draw" in next_action:
            errors.append("READY / NO_DRAWING cannot authorize drawing")
        if "draw" not in blocked:
            errors.append("READY / NO_DRAWING must explicitly block drawing")
    if errors:
        return fail(errors)

    print(json.dumps({"status": "PASS_RECOVERY", "active_packet": data["active_packet"], "next_allowed_action": data["next_allowed_action"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
