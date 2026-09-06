from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path


CURRENT_SKILLS_ROOT = Path(__file__).resolve().parents[2]

def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()


def read_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def profile_authority_errors() -> tuple[Path, list[str]]:
    profile_path = Path(os.environ.get("Q_PROFILE_PATH", str(codex_home() / "q-profile.json"))).expanduser()
    errors: list[str] = []
    if not profile_path.is_file():
        return profile_path, [f"authoritative q-profile is missing: {profile_path}"]
    profile = read_json_object(profile_path)
    if not profile:
        return profile_path, [f"authoritative q-profile is unreadable or invalid: {profile_path}"]
    hub_value = profile.get("hub")
    if not isinstance(hub_value, str) or not hub_value or not Path(hub_value).expanduser().is_dir():
        errors.append("q-profile hub is missing or is not an existing directory")
    repositories = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    workflow_row = repositories.get("q-workflow-hub") if isinstance(repositories.get("q-workflow-hub"), dict) else {}
    workflow_value = workflow_row.get("path") or workflow_row.get("local_path") or workflow_row.get("registry_path")
    if not isinstance(workflow_value, str) or not workflow_value or not (Path(workflow_value).expanduser() / "skills").is_dir():
        errors.append("q-profile q-workflow-hub skills root is missing or invalid")
    return profile_path, errors


def default_roots() -> dict[str, Path]:
    profile_path = Path(os.environ.get("Q_PROFILE_PATH", str(codex_home() / "q-profile.json")))
    profile = read_json_object(profile_path)
    hub_value = profile.get("hub")
    hub = Path(hub_value).expanduser() if isinstance(hub_value, str) and hub_value else None
    repositories = profile.get("repositories") if isinstance(profile.get("repositories"), dict) else {}
    workflow_row = repositories.get("q-workflow-hub") if isinstance(repositories.get("q-workflow-hub"), dict) else {}
    workflow_value = workflow_row.get("path") or workflow_row.get("local_path") or workflow_row.get("registry_path")
    source = Path(workflow_value).expanduser() / "skills" if isinstance(workflow_value, str) and workflow_value else CURRENT_SKILLS_ROOT
    bootstrap_default = hub / "bootstrap" / "skills" if hub is not None else Path.home() / "q-personal-hub" / "bootstrap" / "skills"
    return {
        "runtime": codex_home() / "skills",
        "current_hub": source,
        "public_hub": Path(os.environ.get("Q_WORKFLOW_PUBLIC_SKILLS", str(Path.home() / "q-workflow-hub-public" / "skills"))),
        "personal_bootstrap": Path(os.environ.get("Q_PERSONAL_BOOTSTRAP_SKILLS", str(bootstrap_default))),
    }


def normalized_root_key(path: Path) -> str:
    return str(path.expanduser().resolve()).casefold()

TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".yaml", ".yml", ".py", ".ps1", ".html",
    ".htm", ".css", ".js", ".csv", ".toml", ".ini", ".xml", ".svg",
    ".template",
}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "archive", ".tmp"}

VAGUE_PHRASES = [
    "as needed", "when appropriate", "where practical", "if useful",
    "be careful", "ensure", "make sure", "should usually",
]
HARD_WORDS = ["must", "must not", "required", "blocks", "hard gate", "fatal"]
OUTPUT_WORDS = ["output", "handoff", "deliverable", "report", "summary"]
VALIDATION_WORDS = ["validate", "validation", "test", "smoke", "check", "gate", "pass"]
DEPENDENCY_WORDS = ["use q-", "compose", "downstream", "review gate", "pipeline", "depends"]


def is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.endswith(".md.template")


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        base = Path(dirpath)
        for name in filenames:
            path = base / name
            if is_text(path):
                yield path


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        return {}, text
    end = normalized.find("\n---\n", 4)
    if end == -1:
        return {}, text
    raw = normalized[4:end]
    body = normalized[end + 5 :]
    meta: dict[str, str] = {}
    current = None
    for line in raw.splitlines():
        if re.match(r"^[A-Za-z0-9_-]+:", line):
            key, value = line.split(":", 1)
            current = key.strip()
            meta[current] = value.strip().strip("'\"")
        elif current and line.startswith((" ", "\t")):
            meta[current] += " " + line.strip().strip("'\"")
    return meta, body


def skill_root_from_skill_dir(skill_dir: Path) -> Path:
    return skill_dir.parent


def hub_root_from_skill_dir(skill_dir: Path) -> Path:
    return skill_dir.parent.parent


def context_for(text: str, start: int, end: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    before = max(0, start - 100)
    after = min(len(text), end + 100)
    return text[before:after] + "\n" + text[line_start:line_end]


def classify_reference(skill_dir: Path, text: str, match: re.Match[str]) -> dict:
    raw = match.group(1).strip()
    clean = raw.rstrip(".,;:")
    result = {"ref": clean, "owner": "local", "exists": False, "status": "missing"}
    if any(ch in clean for ch in [" ", "\n", "\r", "\t"]):
        result.update({"owner": "unknown", "status": "ignored-composite"})
        return result

    local = skill_dir / clean
    if local.exists():
        result.update({"owner": "local", "exists": True, "status": "ok"})
        return result

    ctx = context_for(text, match.start(), match.end())
    skill_root = skill_root_from_skill_dir(skill_dir)
    for sibling in sorted(skill_root.glob("q-*")):
        candidate = sibling / clean
        if sibling.name in ctx and candidate.exists():
            result.update({"owner": f"cross-skill:{sibling.name}", "exists": True, "status": "ok"})
            return result

    hub_candidate = hub_root_from_skill_dir(skill_dir) / clean
    if hub_candidate.exists() and any(token in ctx.lower() for token in ["hub", "repo", "repository", "when available"]):
        result.update({"owner": "hub", "exists": True, "status": "ok"})
        return result

    if "when available" in ctx.lower() or "if available" in ctx.lower():
        result.update({"owner": "optional", "exists": False, "status": "optional-missing"})
        return result

    return result


def referenced_paths(skill_dir: Path, text: str) -> list[dict]:
    refs: list[dict] = []
    for match in re.finditer(r"`((?:workflows|references|scripts|agents|assets)/[^`]+)`", text):
        refs.append(classify_reference(skill_dir, text, match))
    return refs


def line_ending_issue(data: bytes) -> str | None:
    has_crlf = b"\r\n" in data
    has_bare_lf = bool(re.search(rb"(?<!\r)\n", data))
    has_bare_cr = bool(re.search(rb"\r(?!\n)", data))
    if has_crlf and has_bare_lf:
        return "mixed-crlf-lf"
    if has_bare_cr:
        return "bare-cr"
    return None


def audit_skill(root_label: str, skill_md: Path) -> dict:
    skill_dir = skill_md.parent
    data = skill_md.read_bytes()
    text = data.decode("utf-8")
    meta, body = parse_frontmatter(text)
    lines = text.splitlines()
    lower = text.lower()
    desc = meta.get("description", "")
    name = meta.get("name", "")
    refs = referenced_paths(skill_dir, text)
    missing_required = [r for r in refs if r["status"] == "missing"]

    files = list(iter_files(skill_dir))
    dirs = {p.parent.relative_to(skill_dir).parts[0] for p in files if p.parent != skill_dir}

    issues = []
    metrics = {
        "lines": len(lines),
        "body_lines": len(body.splitlines()),
        "desc_chars": len(desc),
        "text_files": len(files),
        "refs": len(refs),
        "missing_required_refs": len(missing_required),
        "optional_missing_refs": sum(1 for r in refs if r["status"] == "optional-missing"),
        "cross_skill_refs": sum(1 for r in refs if r["owner"].startswith("cross-skill:")),
        "hub_refs": sum(1 for r in refs if r["owner"] == "hub"),
        "workflow_files": sum(1 for p in files if "workflows" in p.relative_to(skill_dir).parts),
        "reference_files": sum(1 for p in files if "references" in p.relative_to(skill_dir).parts),
        "script_files": sum(1 for p in files if "scripts" in p.relative_to(skill_dir).parts),
    }

    if not meta:
        issues.append(("blocker", "frontmatter_missing", "SKILL.md lacks YAML frontmatter"))
    if not name:
        issues.append(("blocker", "name_missing", "frontmatter name missing"))
    if not desc:
        issues.append(("blocker", "description_missing", "frontmatter description missing"))
    elif "use when" not in desc.lower() and len(desc) < 90:
        issues.append(("warning", "description_trigger_weak", "description may not state concrete trigger/use-when"))
    if len(desc) > 900:
        issues.append(("warning", "description_too_long", f"description is long ({len(desc)} chars)"))
    if metrics["lines"] > 180:
        issues.append(("warning", "skill_md_large", f"SKILL.md first-read surface is large ({metrics['lines']} lines)"))
    if metrics["lines"] > 260:
        issues.append(("blocker", "skill_md_too_large", f"SKILL.md is very large ({metrics['lines']} lines)"))
    if missing_required:
        issues.append(("blocker", "missing_referenced_file", f"{len(missing_required)} required referenced paths missing"))
    if "workflow" not in lower and "default" not in lower and "steps" not in lower:
        issues.append(("warning", "default_path_weak", "default path/routing is not obvious"))
    if not any(word in lower for word in OUTPUT_WORDS):
        issues.append(("warning", "output_contract_weak", "output or handoff contract is not obvious"))
    if not any(word in lower for word in VALIDATION_WORDS):
        issues.append(("warning", "validation_contract_weak", "validation/check behavior is not obvious"))
    if any(w in lower for w in HARD_WORDS) and not any(w in lower for w in ["blocks", "check:", "validation", "gate"]):
        issues.append(("warning", "hard_rule_without_check", "hard/required language appears without clear check or blocked outcome"))
    if len([p for p in VAGUE_PHRASES if p in lower]) >= 4:
        issues.append(("info", "many_soft_phrases", "many soft phrases; check whether rules are too loose"))
    if line_ending_issue(data):
        issues.append(("blocker", "mixed_line_endings", "SKILL.md has mixed or bare line endings"))
    if data and not data.endswith(b"\n"):
        issues.append(("warning", "missing_final_newline", "SKILL.md lacks final newline"))
    for i, raw in enumerate(data.splitlines(), start=1):
        if raw.rstrip(b" \t") != raw:
            issues.append(("warning", "trailing_whitespace", f"line {i} has trailing whitespace"))
            break

    has_router = "router" in lower or "read next" in lower or "| user intent |" in lower
    has_modularity = bool({"workflows", "references", "scripts"} & dirs)
    has_composition = any(w in lower for w in DEPENDENCY_WORDS) or metrics["cross_skill_refs"] > 0
    score = 100
    for sev, _, _ in issues:
        score -= {"blocker": 18, "warning": 7, "info": 2}[sev]
    if has_router:
        score += 4
    if has_modularity:
        score += 4
    if has_composition:
        score += 2
    score = max(0, min(100, score))

    return {
        "root": root_label,
        "skill_id": skill_dir.name,
        "path": str(skill_md),
        "name": name,
        "description": desc,
        "metrics": metrics,
        "dirs": sorted(dirs),
        "refs": refs,
        "issues": [{"severity": s, "code": c, "detail": d} for s, c, d in issues],
        "signals": {
            "router": has_router,
            "modularity": has_modularity,
            "composition": has_composition,
            "output_contract": any(word in lower for word in OUTPUT_WORDS),
            "validation_contract": any(word in lower for word in VALIDATION_WORDS),
        },
        "score": score,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit q-workflow skill portfolio structure, contracts, references, and hygiene.")
    parser.add_argument("--root", action="append", default=[], help="Override/add a root as label=path.")
    parser.add_argument("--json-out", default="", help="Write full JSON report to this path.")
    parser.add_argument("--fail-on-blocker", action="store_true", help="Exit nonzero when blockers are found.")
    parser.add_argument("--markdown-out", default="", help="Write a compact Markdown report to this path.")
    return parser.parse_args()


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Skill Portfolio Audit",
        "",
        f"Skill surfaces checked: {report['summary']['skill_count']}",
        f"Blockers: {report['summary']['severity_counts'].get('blocker', 0)}",
        f"Warnings: {report['summary']['severity_counts'].get('warning', 0)}",
        "",
        "## Root Scores",
        "",
    ]
    for root, score in report["summary"]["root_average_scores"].items():
        lines.append(f"- {root}: {score}")
    lines += ["", "## Findings", ""]
    for item in report["skills"]:
        visible = [i for i in item["issues"] if i["severity"] in {"blocker", "warning"}]
        if not visible:
            continue
        lines.append(f"### {item['root']} / {item['skill_id']} / score {item['score']}")
        lines.append("")
        for issue in visible:
            lines.append(f"- {issue['severity']} `{issue['code']}`: {issue['detail']}")
        for ref in item["refs"]:
            if ref["status"] in {"missing", "optional-missing"}:
                lines.append(f"- ref `{ref['ref']}`: {ref['status']} ({ref['owner']})")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    profile_path, authority_errors = profile_authority_errors()
    if authority_errors and not args.root:
        blocked = {
            "status": "blocked",
            "failure_class": "profile-authority",
            "profile": str(profile_path),
            "errors": authority_errors,
            "repair": "Restore Q_PROFILE_PATH authority or provide one or more explicit --root label=path values.",
        }
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(blocked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(blocked, ensure_ascii=False, indent=2))
        return 2
    roots = {} if authority_errors else default_roots()
    for item in args.root:
        if "=" not in item:
            raise SystemExit("--root must be label=path")
        label, raw = item.split("=", 1)
        roots[label] = Path(raw)

    report = {
        "authority": {
            "mode": "profile" if not authority_errors else "explicit-roots",
            "profile": str(profile_path),
            "warnings": authority_errors,
        },
        "roots": {},
        "skills": [],
    }
    seen_roots: dict[str, str] = {}
    for label, root in roots.items():
        root = root.expanduser().resolve()
        root_key = normalized_root_key(root)
        duplicate_of = seen_roots.get(root_key)
        if duplicate_of:
            report["roots"][label] = {
                "path": str(root),
                "skill_count": 0,
                "exists": root.exists(),
                "duplicate_of": duplicate_of,
            }
            continue
        seen_roots[root_key] = label
        skill_files = sorted(root.glob("*/SKILL.md")) if root.exists() else []
        report["roots"][label] = {
            "path": str(root),
            "skill_count": len(skill_files),
            "exists": root.exists(),
            "duplicate_of": None,
        }
        for skill_md in skill_files:
            report["skills"].append(audit_skill(label, skill_md))

    issue_counts = Counter()
    severity_counts = Counter()
    root_scores = defaultdict(list)
    for item in report["skills"]:
        root_scores[item["root"]].append(item["score"])
        for issue in item["issues"]:
            issue_counts[issue["code"]] += 1
            severity_counts[issue["severity"]] += 1
    report["summary"] = {
        "skill_count": len(report["skills"]),
        "issue_counts": dict(issue_counts),
        "severity_counts": dict(severity_counts),
        "root_average_scores": {
            root: round(sum(scores) / len(scores), 1) if scores else 0
            for root, scores in root_scores.items()
        },
    }

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_out:
        write_markdown(report, Path(args.markdown_out))
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    return 1 if args.fail_on_blocker and severity_counts.get("blocker", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
