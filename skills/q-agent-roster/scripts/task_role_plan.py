#!/usr/bin/env python3
"""Emit a deterministic expert role plan for a material task."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for _stream in (sys.stdout, sys.stderr):
    try: _stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError: pass
def load() -> dict: return json.loads((ROOT / "references" / "expert-routing-matrix.json").read_text(encoding="utf-8"))
def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--task-class", choices=("tiny","research","workflow","code","interface","standard","install","release")); p.add_argument("--format", choices=("json","text"), default="json"); p.add_argument("--self-test", action="store_true"); a=p.parse_args(); data=load()
    if a.self_test:
        expected={"research":"source-scout","workflow":"workflow-distiller","install":"main-or-assigned-installer","interface":"pagewright"}; actual={k:data["routes"][k]["primary_owner"] for k in expected}; ok=actual==expected; print(json.dumps({"status":"pass" if ok else "blocked","actual":actual},ensure_ascii=False)); return 0 if ok else 1
    if not a.task_class: p.error("--task-class is required unless --self-test is used")
    plan={"format_version":1,"task_class":a.task_class,"integration_owner":"main-agent","dispatch_required":a.task_class!="tiny","release_state_ceiling":"local-only"}
    if a.task_class=="tiny": plan.update({"reason":data["tiny_exemption"],"primary_owner":"main-agent","reviewer_gate":"none","validator_gate":"none","mode":"local-pass","independence_required":False})
    else: plan.update(data["routes"][a.task_class])
    print(json.dumps(plan,ensure_ascii=False,indent=2) if a.format=="json" else " | ".join(f"{k}={v}" for k,v in plan.items()))
    return 0
if __name__ == "__main__": raise SystemExit(main())
