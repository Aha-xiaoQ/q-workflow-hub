#!/usr/bin/env python3
"""Optional, side-effect-free execution advice. Never grants action authority.

Use for policy regression or ambiguous planning, not as a mandatory per-turn
gate. Inputs are caller assertions; this module does not verify permissions,
evidence, model availability or completion. Existing gates always prevail.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ENUMS = {
    "intent": {"answer", "diagnose", "change", "monitor"},
    "risk": {"low", "material", "high"},
    "claim": {"local", "mirror", "remote-rebuild", "release"},
    "authority": {"in-scope", "missing", "denied"},
    "evidence": {"not-run", "pass", "fail", "stale"},
}
FLAGS = {"decision_missing", "pending_tools", "unresolved_concerns",
         "independent_work", "useful_main_work", "delegation_permitted",
         "delegation_available", "review_required", "monitor_available"}
REQUIRED = set(ENUMS) | FLAGS


def advise(facts: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic advice only; missing/invalid inputs fail closed."""
    base: dict[str, Any] = {"advisory_only": True, "grants_authority": False,
                            "promotion_eligible": False}
    if not isinstance(facts, dict):
        return {**base, "status": "needs-context", "errors": ["input must be an object"]}
    errors = [f"missing {k}" for k in sorted(REQUIRED - facts.keys())]
    errors += [f"unknown {k}" for k in sorted(facts.keys() - REQUIRED)]
    for key, values in ENUMS.items():
        if key in facts and (not isinstance(facts[key], str) or facts[key] not in values):
            errors.append(f"invalid {key}")
    errors += [f"invalid boolean {k}" for k in sorted(FLAGS & facts.keys())
               if type(facts[k]) is not bool]
    if errors:
        return {**base, "status": "needs-context", "errors": errors}

    tier = {"local": "T1", "mirror": "T2", "remote-rebuild": "T3", "release": "T4"}[facts["claim"]]
    # Risk changes test depth within the affected surface, not the surface itself.
    # A high-risk application fix does not acquire workflow/bootstrap mirrors.
    if facts["intent"] in {"answer", "diagnose"} and facts["claim"] == "local" and facts["risk"] == "low":
        tier = "T0"
    delegation = "main"
    if (facts["authority"] == "in-scope" and not facts["decision_missing"]
            and facts["independent_work"] and facts["useful_main_work"]
            and facts["delegation_permitted"] and facts["delegation_available"]):
        delegation = "bounded-child"
    elif facts["review_required"]:
        delegation = "review-needed"  # Do not silently substitute self-review.

    # Revoked authority and material choices dominate successful tests.
    if facts["authority"] == "denied":
        action = "stop-out-of-scope"
    elif facts["authority"] == "missing" or facts["decision_missing"]:
        action = "ask-focused-question"
    elif facts["pending_tools"]:
        action = "reconcile-pending-tools"
    elif facts["intent"] == "monitor":
        action = "use-native-monitor" if facts["monitor_available"] else "report-capability-gap"
    elif facts["evidence"] in {"fail", "stale"} or facts["unresolved_concerns"]:
        action = ("targeted-read-only-validation" if facts["intent"] in {"answer", "diagnose"}
                  else "targeted-validation-or-repair")
    elif facts["review_required"]:
        action = "complete-independent-review"
    elif facts["evidence"] == "pass":
        action = "handoff-with-evidence"  # Not permission to publish or close task state.
    else:
        action = "inspect-read-only" if facts["intent"] in {"answer", "diagnose"} else "implement-in-scope"
    return {**base, "status": "advice", "next_action": action, "test_tier": tier,
            "delegation": delegation,
            "requested_mode": "change" if facts["intent"] == "change" else "no-artifact-mutation",
            "repeat_checks": facts["evidence"] in {"fail", "stale"} or facts["unresolved_concerns"],
            "model_policy": "inherit-observed-host-default; no automatic override"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Explicit JSON facts; no state is written")
    args = parser.parse_args()
    try:
        result = advise(json.loads(args.input.read_text(encoding="utf-8-sig")))
    except (OSError, ValueError) as exc:
        result = {"status": "needs-context", "advisory_only": True,
                  "grants_authority": False, "errors": [str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "advice" else 2


if __name__ == "__main__":
    raise SystemExit(main())
