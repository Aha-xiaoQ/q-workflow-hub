from __future__ import annotations

import argparse
import json
from collections import Counter
import os
from pathlib import Path
import re


CURRENT_SKILLS_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_ROOTS = {
    "runtime": Path.home() / ".codex" / "skills",
    "current_hub": CURRENT_SKILLS_ROOT,
    "public_hub": Path(os.environ.get("Q_WORKFLOW_PUBLIC_SKILLS", str(Path.home() / "q-workflow-hub-public" / "skills"))),
    "personal_bootstrap": Path(os.environ.get("Q_PERSONAL_BOOTSTRAP_SKILLS", str(Path.home() / "q-personal-github-bootstrap" / "q-personal-hub" / "bootstrap" / "skills"))),
}

EXTERNAL_SUFFIXES = ("-main",)
GENERIC_DRIFT_WORDS = {"workflow", "system", "manager", "helper", "tool"}
LIFECYCLE_TERMS = ("create", "update", "review", "stabilize", "release", "rename")
Q_SKILL_NAME_RE = re.compile(r"^q-[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_candidate_name(name: str, kind: str) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not name or name != name.strip() or len(name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        issues.append({"severity": "P1", "code": "invalid-candidate-name", "detail": "name must be lowercase hyphen-case and no longer than 64 characters"})
        return issues
    if kind == "q-owned" and not Q_SKILL_NAME_RE.fullmatch(name):
        issues.append({"severity": "P1", "code": "q-prefix-required", "detail": "q-workflow-owned reusable skills must start with `q-`"})
    return issues


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return {}, text
    end = normalized.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = normalized[4:end]
    body = normalized[end + 5:]
    meta: dict[str, str] = {}
    current = None
    for line in raw.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            current = key.strip()
            meta[current] = value.strip().strip("'\"")
        elif current and line.startswith((" ", "\t")):
            meta[current] += " " + line.strip().strip("'\"")
    return meta, body


def classify(root: str, skill_dir: Path) -> dict:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    name = meta.get("name", skill_dir.name)
    desc = meta.get("description", "")
    lower = (name + " " + desc + " " + body[:2000]).lower()
    tokens = set(name.split("-"))
    issues = []
    recommendations = []
    decision = "keep"

    folder = skill_dir.name
    external_folder_suffix = next((suffix for suffix in EXTERNAL_SUFFIXES if folder.endswith(suffix)), "")
    external_folder_base = folder[:-len(external_folder_suffix)] if external_folder_suffix else folder

    if name != folder:
        if external_folder_suffix and external_folder_base == name:
            issues.append({"severity": "info", "code": "external-repo-folder-suffix", "detail": f"folder `{folder}` keeps external repository suffix `{external_folder_suffix}` while frontmatter uses `{name}`"})
            recommendations.append("Keep if this is an external installed skill; wrap or canonicalize only before q-workflow publication.")
            decision = "keep-external"
        else:
            issues.append({"severity": "P2", "code": "folder-name-mismatch", "detail": f"folder `{folder}` differs from frontmatter `{name}`"})
            recommendations.append("Align folder, frontmatter, and install/runtime name before release.")
            decision = "migration-candidate"

    if not name.startswith("q-") and "compatibility alias for q-" in lower:
        issues.append({"severity": "P1", "code": "published-non-q-alias", "detail": "non-q compatibility folders must not remain in a published q-workflow skill root"})
        recommendations.append("Delete the alias folder and keep the old phrase in canonical metadata or migration notes.")
        decision = "migration-candidate"

    if any(folder.endswith(suffix) for suffix in EXTERNAL_SUFFIXES) and not external_folder_suffix:
        issues.append({"severity": "info", "code": "external-repo-suffix", "detail": "`-main` looks like an external repository suffix, not q-workflow naming"})
        recommendations.append("Keep if external; add a q-workflow wrapper only if users need a polished Xiao Q trigger.")

    if name in {"q-skill-creation"} and all(term in lower for term in LIFECYCLE_TERMS):
        issues.append({"severity": "P3", "code": "name-understates-lifecycle", "detail": "`creation` now covers creation, update, review, release, and rename lifecycle work"})
        recommendations.append("Keep current name for compatibility; consider `q-skill-lifecycle` only if users misroute lifecycle/release work.")
        decision = "watch"

    if tokens & GENERIC_DRIFT_WORDS and name not in {"q-workflow"}:
        if "review gate" not in lower and "pipeline" not in lower and "root workflow" not in lower:
            issues.append({"severity": "P3", "code": "generic-token-review", "detail": f"name includes generic token(s): {', '.join(sorted(tokens & GENERIC_DRIFT_WORDS))}"})
            recommendations.append("Keep only if the generic token is the user-facing job; otherwise consider a domain-job name.")
            decision = "watch"

    if "create" in lower and "review" in lower and "visual" in lower and "ppt" in lower:
        issues.append({"severity": "info", "code": "creator-reviewer-boundary-check", "detail": "PPT creation/review boundary should remain separate unless triggers duplicate"})
        recommendations.append("Keep creation and visual review separate; compose with a review gate.")

    if not issues:
        recommendations.append("Name matches current function at this audit depth.")

    return {
        "root": root,
        "skill_id": skill_dir.name,
        "name": name,
        "path": str(skill_dir / "SKILL.md"),
        "decision": decision,
        "issues": issues,
        "recommendations": recommendations,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit skill naming drift, rename candidates, and split/merge signals.")
    parser.add_argument("--root", action="append", default=[], help="Add/override root as label=path")
    parser.add_argument("--json-out", default="")
    parser.add_argument("--markdown-out", default="")
    parser.add_argument("--fail-on-p1", action="store_true")
    parser.add_argument("--candidate-name", default="", help="Validate one proposed skill name before scaffolding")
    parser.add_argument("--candidate-kind", choices=("q-owned", "external", "project-local"), default="q-owned")
    return parser.parse_args()


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Skill Naming Drift Audit",
        "",
        f"Skills checked: {report['summary']['skill_count']}",
        f"P1/P2 findings: {report['summary']['p1_p2_count']}",
        f"Watch candidates: {report['summary']['watch_count']}",
        "",
        "## Findings",
        "",
    ]
    for item in report["skills"]:
        if not item["issues"]:
            continue
        lines.append(f"### {item['root']} / {item['skill_id']} / {item['decision']}")
        lines.append("")
        for issue in item["issues"]:
            lines.append(f"- {issue['severity']} `{issue['code']}`: {issue['detail']}")
        for rec in item["recommendations"]:
            lines.append(f"- recommendation: {rec}")
        lines.append("")
    if not any(item["issues"] for item in report["skills"]):
        lines.append("No naming drift findings.")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.candidate_name:
        issues = validate_candidate_name(args.candidate_name, args.candidate_kind)
        result = {
            "candidate_name": args.candidate_name,
            "candidate_kind": args.candidate_kind,
            "status": "blocked" if issues else "pass",
            "issues": issues,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if issues else 0

    roots = dict(DEFAULT_ROOTS)
    for item in args.root:
        if "=" not in item:
            raise SystemExit("--root must be label=path")
        label, raw = item.split("=", 1)
        roots[label] = Path(raw)

    skills = []
    for label, root in roots.items():
        if not root.exists():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            skills.append(classify(label, skill_md.parent))

    names_by_root: dict[str, set[str]] = {}
    for item in skills:
        names_by_root.setdefault(item["root"], set()).add(item["name"])
    for item in skills:
        name = item["name"]
        if name.startswith("q-") or f"q-{name}" not in names_by_root[item["root"]]:
            continue
        if not any(issue["code"] == "duplicate-non-q-q-counterpart" for issue in item["issues"]):
            item["issues"].append({"severity": "P1", "code": "duplicate-non-q-q-counterpart", "detail": f"published root contains both `{name}` and canonical `q-{name}`"})
            item["recommendations"].append("Retire the non-q folder; preserve compatibility as canonical text metadata or a migration note.")
            item["decision"] = "migration-candidate"

    issue_counts = Counter(issue["code"] for item in skills for issue in item["issues"])
    p1_p2 = sum(1 for item in skills for issue in item["issues"] if issue["severity"] in {"P1", "P2"})
    watch = sum(1 for item in skills if item["decision"] == "watch")
    report = {
        "summary": {
            "skill_count": len(skills),
            "issue_counts": dict(issue_counts),
            "p1_p2_count": p1_p2,
            "watch_count": watch,
        },
        "skills": skills,
    }
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_out:
        write_markdown(report, Path(args.markdown_out))
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 1 if args.fail_on_p1 and p1_p2 else 0


if __name__ == "__main__":
    raise SystemExit(main())
