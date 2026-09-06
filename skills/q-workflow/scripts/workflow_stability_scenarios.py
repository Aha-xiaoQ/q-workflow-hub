#!/usr/bin/env python3
"""Deterministic, no-network regression scenarios for workflow stability.

Remote endpoint freshness is deliberately excluded: without a successful fetch it
is reported as unproven, never simulated as verified.
"""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try: _stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError: pass

ROOT=Path(__file__).resolve().parents[1]
def run(cmd: list[str]) -> tuple[int, dict]:
    p=subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    try: return p.returncode, json.loads(p.stdout)
    except json.JSONDecodeError: return p.returncode, {"raw":p.stdout[-400:]}
def main() -> int:
    cases=[]
    planner=ROOT.parent / "q-agent-roster" / "scripts" / "task_role_plan.py"
    for name, expected in {"research":"source-scout","workflow":"workflow-distiller","install":"main-or-assigned-installer","interface":"pagewright","tiny":"main-agent"}.items():
        rc, data=run([sys.executable,str(planner),"--task-class",name,"--format","json"])
        cases.append({"id":f"expert-route-{name}","pass":rc==0 and data.get("primary_owner")==expected,"evidence":data})
    rc,data=run([sys.executable,str(planner),"--self-test"])
    cases.append({"id":"expert-router-self-test","pass":rc==0 and data.get("status")=="pass","evidence":data})
    routing_reference=ROOT.parent / "q-agent-roster" / "references" / "model-routing.md"
    routing_scenarios=ROOT.parent / "q-agent-roster" / "references" / "validation-scenarios.md"
    routing_text=(routing_reference.read_text(encoding="utf-8") + "\n" + routing_scenarios.read_text(encoding="utf-8")).lower()
    routing_anchors={
        "safety and authority hard gate",
        "protocol_conformance",
        "promotion_eligible: false",
        "fresh per-invocation",
        "scenario 19: routing benchmark promotion gate",
    }
    missing_routing=sorted(anchor for anchor in routing_anchors if anchor not in routing_text)
    cases.append({"id":"model-routing-promotion-gate","pass":not missing_routing,"evidence":{"missing":missing_routing}})
    contract=json.loads((ROOT / "references" / "lifecycle-contract.json").read_text(encoding="utf-8"))
    required={"work","integrity","release"}.issubset(contract.get("axes",{})) and contract.get("format_version")==1
    cases.append({"id":"lifecycle-contract-schema","pass":required,"evidence":{"format_version":contract.get("format_version")}})
    transitions=contract.get("transitions", [])
    names={row.get("event") for row in transitions if isinstance(row,dict)}
    cases.append({"id":"transition-contract-covers-start-pause-block-resume-close","pass":{"start","pause","block","resume","close"}.issubset(names),"evidence":{"events":sorted(names)}})
    cases.append({"id":"offline-release-is-rejected","pass":"remote_status=proven" in " ".join(contract.get("transition_rules", [])),"evidence":{"rule":"ready/released needs remote proof"}})
    lifecycle=ROOT / "scripts" / "workflow_lifecycle.py"
    transition_cases=[("paused","briefing",True,["--old-epoch","1","--new-epoch","2","--old-revision","r1","--new-revision","r2"]),("paused","briefing",False,["--old-epoch","1","--new-epoch","1","--old-revision","r1","--new-revision","r1"]),("closed","active",False,[]),("active","paused",True,[]),("active","blocked",True,["--blocked-on","remote-fetch","--error-code","REMOTE_UNPROVEN"]),("active","blocked",False,[]),("briefing","active",False,[]),("briefing","active",True,["--role-plan","p1","--primary-status","planned"])]
    for source, target, expect, extra in transition_cases:
        rc,data=run([sys.executable,str(lifecycle),"--check-transition",source,target,"--format","json",*extra])
        cases.append({"id":f"transition-{source}-to-{target}","pass":(rc==0)==expect and data.get("allowed")==expect,"evidence":data})

    # Visual-imitation gates are deliberately a documentation/ordering replay,
    # not an automatic visual-fidelity judge.  It proves that every saved VIG
    # case resolves to an existing rule/reference and that its required anchors
    # remain discoverable after future edits.
    feedback_cases=json.loads((ROOT / "references" / "workflow-feedback-regression-cases.json").read_text(encoding="utf-8")).get("cases", [])
    reference_roots={
        "references/q-standard-contract.md": ROOT / "references" / "q-standard-contract.md",
        "q-html-interface-design/references/html-visual-review-gate.md": ROOT.parent / "q-html-interface-design" / "references" / "html-visual-review-gate.md",
    }
    expected_vig={
        "VIG-01-scale-is-not-optimization",
        "VIG-02-inspection-layer-missing",
        "VIG-03-live-before-review",
        "VIG-04-review-after-integration",
        "VIG-05-clean-before-inspection-approval",
    }
    vig_rows={row.get("id"): row for row in feedback_cases if str(row.get("id", "")).startswith("VIG-")}
    cases.append({"id":"visual-imitation-case-set","pass":set(vig_rows)==expected_vig,"evidence":{"found":sorted(vig_rows),"expected":sorted(expected_vig)}})
    for case_id, row in sorted(vig_rows.items()):
        reference=reference_roots.get(row.get("expected_reference"))
        text=reference.read_text(encoding="utf-8").lower() if reference and reference.exists() else ""
        required=[row.get("expected_route", ""), *row.get("must_have_terms", [])]
        missing=[term for term in required if not term or term.lower() not in text]
        cases.append({
            "id":f"visual-imitation-{case_id}",
            "pass":bool(reference) and not missing,
            "evidence":{"reference":str(reference) if reference else None,"missing":missing},
        })
    # A mutation-free failure oracle: missing profile cannot silently pass lifecycle inspection.
    with tempfile.TemporaryDirectory() as temp:
        env_script=ROOT / "scripts" / "workflow_lifecycle.py"
        p=subprocess.run([sys.executable,str(env_script),"--strict","--format","json"],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30, env={"CODEX_HOME":temp})
        cases.append({"id":"cold-start-missing-authority-fails-closed","pass":p.returncode!=0,"evidence":{"rc":p.returncode}})
    failed=[case for case in cases if not case["pass"]]
    print(json.dumps({"status":"pass" if not failed else "blocked","cases":cases,"failures":len(failed),"remote_status":"unproven-by-design"},ensure_ascii=False,indent=2))
    return 0 if not failed else 1
if __name__=="__main__": raise SystemExit(main())
