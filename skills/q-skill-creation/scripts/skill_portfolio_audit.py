from __future__ import annotations

import argparse
import json
import os
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.parse import unquote


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
        "personal_generated": hub / "generated-skills" if hub is not None else Path.home() / "q-personal-hub" / "generated-skills",
    }


def normalized_root_key(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


# These installation surfaces are optional unless explicitly supplied by --root.
OPTIONAL_DEFAULT_ROOTS = {"public_hub", "nxp_hub", "personal_bootstrap", "personal_generated"}
REFERENCE_SCAN_LIMIT = 256
REFERENCE_SCOPE = (
    "Reachable local Markdown from each selected entry; Markdown links and inline "
    "resource paths/commands only. Fenced code, arbitrary prose/code strings, "
    "external URLs, link anchors, executable behavior and semantic quality are not certified. "
    "Markdown links resolve relative to the containing file; inline resource-directory "
    "paths and the SKILL.md basename resolve from the owning skill; explicit ./ "
    "and ../ use the containing file. Bare output/directory mentions are uncertain."
)

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
    return skill_dir.parent.parent if skill_dir.parent.name == ".system" else skill_dir.parent


def hub_root_from_skill_dir(skill_dir: Path) -> Path:
    return skill_root_from_skill_dir(skill_dir).parent


def context_for(text: str, start: int, end: int) -> str:
    # A qualification cannot cross a sentence, line, table cell or semicolon.
    # Only inspect outside the current reference span, so dots inside its path
    # do not split the reference's own context.
    separator = re.compile(r"[\n;|\u3002\uff01\uff1f]|[.!?](?=\s|$)")
    before = list(separator.finditer(text, 0, start))
    after = separator.search(text, end)
    begin = before[-1].end() if before else 0
    finish = after.start() if after else len(text)
    return text[begin:finish]


RESOURCE_PREFIX = re.compile(r"^(?:workflows|references|scripts|agents|assets|schemas|templates|tools)/", re.I)
SCRIPT_END = re.compile(r"^(.+?\.(?:py|ps1|sh|js|mjs|cjs|exe))(?:\s+.*)?$", re.I)
OPTIONAL_REFERENCE = re.compile(r"\b(?:optional|(?:when|if) (?:available|installed))\b", re.I)


def markdown_surface(text: str) -> tuple[str, int]:
    """Mask code blocks/comments without moving source offsets or line numbers."""
    fence = None
    excluded = 0
    output = []
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if fence:
            output.append(re.sub(r"[^\r\n]", " ", line))
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
        elif marker:
            fence = marker.group(1)
            excluded += 1
            output.append(re.sub(r"[^\r\n]", " ", line))
        else:
            output.append(line)
    surface = "".join(output)
    surface = re.sub(r"<!--[\s\S]*?-->", lambda m: re.sub(r"[^\r\n]", " ", m.group()), surface)
    return surface, excluded


def inline_path(value: str) -> str | None:
    """Recognize a path or command position, never search arbitrary code strings."""
    value = value.strip().replace("\\", "/")
    command = re.match(r"^(?:python(?:\d+(?:\.\d+)*)?|py|pwsh|powershell|bash|sh|node)\s+(.*)$", value, re.I)
    if command:
        value = command.group(1)
        value = re.sub(r"^(?:-(?:B|u|3|NoProfile|File)\s+)+", "", value, flags=re.I)
    if value.startswith(('"', "'")):
        quote = value[0]
        end = value.find(quote, 1)
        if end < 0:
            return None
        value = value[1:end]
    else:
        script = SCRIPT_END.match(value)
        if script:
            value = script.group(1)
    if any(token in value for token in (" = ", " == ", " -> ", "\n")):
        return None
    if (RESOURCE_PREFIX.match(value) or value.startswith(("./", "../", "/", "~/"))
            or re.match(r"^[A-Za-z]:/", value)
            or re.match(r"^(?:q-[\w-]+|[\w-]+)/(?:references|workflows|scripts|agents|assets|schemas|templates)/", value)
            or re.match(r"^<[^>]+>/", value)
            or re.match(r"^(?:\$\{?\w+\}?|%\w+%)/", value)
            or value.lower().endswith((".md", ".md.template"))
            or (command and SCRIPT_END.match(value))):
        return value
    return None


def reference_candidates(text: str) -> tuple[list[dict], int]:
    surface, excluded = markdown_surface(text)
    candidates = []
    link_spans = []
    # Covers inline links including angle-bracket paths with spaces and titles.
    link_pattern = r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|((?:\\.|[^)\n])+?))\s*\)"
    for match in re.finditer(link_pattern, surface):
        raw = match.group(1) or match.group(2)
        raw = re.sub(r'\s+["\'][^"\']*["\']\s*$', '', raw).strip()
        candidates.append({"raw": raw, "start": match.start(), "end": match.end(), "syntax": "markdown-link"})
        link_spans.append((match.start(), match.end()))
    # Reference-style link definitions are explicit references, even when the
    # lightweight parser cannot prove which prose branch activates each one.
    for match in re.finditer(r"^\s{0,3}\[[^\]\n]+\]:\s*(?:<([^>\n]+)>|(\S+))", surface, re.M):
        candidates.append({"raw": match.group(1) or match.group(2), "start": match.start(), "end": match.end(), "syntax": "markdown-link"})
    for match in re.finditer(r"(?<!`)`([^`\n]+)`(?!`)", surface):
        if any(begin <= match.start() < end for begin, end in link_spans):
            continue
        raw = inline_path(match.group(1))
        if raw:
            candidates.append({"raw": raw, "start": match.start(), "end": match.end(), "syntax": "inline"})
    return sorted(candidates, key=lambda c: c["start"]), excluded


def owner_for(path: Path, fallback: Path) -> Path:
    for parent in path.parents:
        if (parent / "SKILL.md").is_file():
            return parent
    return fallback


def resolve_reference(skill_dir: Path, source: Path, text: str, candidate: dict) -> dict:
    clean = unquote(candidate["raw"].strip()).replace("\\", "/")
    ctx = context_for(text, candidate["start"], candidate["end"])
    # File names such as references/optional.md are not optionality declarations.
    prose = re.sub(r"`[^`\n]*`", "", ctx)
    prose = re.sub(r"\]\([^\n)]*\)", "]", prose)
    optional = bool(OPTIONAL_REFERENCE.search(prose))
    ambiguous_optional = optional and len(reference_candidates(ctx)[0]) > 1
    optional = optional and not ambiguous_optional
    result = {"ref": clean, "owner": "local", "exists": False, "status": "missing",
              "source": str(source), "line": text.count("\n", 0, candidate["start"]) + 1,
              "syntax": candidate["syntax"], "optional": optional, "target": None}
    if clean.startswith(("#", "//")) or re.match(r"^(?:https?|mailto|data):", clean, re.I):
        result.update(status="external-or-anchor", exists=None, owner="external")
        return result
    # Known root placeholders are statically resolvable, unlike project/user variables.
    alias = re.match(r"^<(?:skill-root|skill-dir|skill-directory)>/", clean, re.I)
    if alias:
        clean = clean[alias.end():]
    if re.search(r"[<>{}*$%]", clean) or (candidate["syntax"] == "inline" and "?" in clean):
        result.update(status="dynamic", exists=None, owner="unresolved")
        return result
    if any(token in clean for token in ("(", ")", " and ", " or ", " | ")):
        result.update(status="unsupported-path-syntax", exists=None, owner="unresolved")
        return result
    if re.match(r"^[a-z][\w+.-]*:", clean, re.I) and not re.match(r"^[A-Za-z]:/", clean):
        result.update(status="unsupported-scheme", exists=None, owner="unresolved")
        return result
    clean = clean.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        result.update(status="external-or-anchor", exists=None)
        return result
    # Output declarations are not evidence that a generated file must already
    # exist. This is deliberately a narrow lexical distinction, not NLP QA.
    if candidate["syntax"] == "inline" and re.search(r"\b(?:write|writes|generate|generates|create|creates|save|output|outputs)\b", ctx, re.I):
        if not re.search(r"\b(?:read|load|consult|follow|run|execute)\b", ctx, re.I):
            result.update(status="role-uncertain", exists=None, owner="unresolved")
            return result
    collection = skill_root_from_skill_dir(skill_dir)
    parts = Path(clean).parts
    cross = (len(parts) > 1 and not RESOURCE_PREFIX.match(clean)
             and not clean.startswith(("./", "../", "/", "~/"))
             and not re.match(r"^[A-Za-z]:/", clean)
             and (parts[0].startswith("q-")
                  or RESOURCE_PREFIX.match("/".join(parts[1:]))
                  or (collection / parts[0] / "SKILL.md").is_file()))
    if cross:
        target = collection / clean
        if not (collection / parts[0]).exists() and (collection / ".system" / parts[0] / "SKILL.md").is_file():
            target = collection / ".system" / clean
        result.update(owner=f"cross-skill:{parts[0]}", resolution="explicit-owner")
    elif Path(clean).is_absolute() or clean.startswith("~/"):
        target = Path(clean).expanduser()
        result["resolution"] = "absolute"
    elif alias or (candidate["syntax"] == "inline" and (RESOURCE_PREFIX.match(clean) or clean == "SKILL.md")):
        target = skill_dir / clean
        result["resolution"] = "skill-root"
    else:
        target = source.parent / clean
        result["resolution"] = "containing-file"
    # Preserve the old owner-qualified inline form without guessing a sibling
    # merely because its file happens to exist somewhere in the portfolio.
    if not target.exists() and result.get("resolution") == "skill-root":
        owners = set(re.findall(r"(?<![\w-])q-[a-z0-9-]+(?![\w-])", ctx)) - {skill_dir.name}
        if len(owners) == 1:
            owner = owners.pop()
            target = collection / owner / clean
            result.update(owner=f"cross-skill:{owner}", resolution="context-owner")
        elif len(owners) > 1:
            result.update(status="ambiguous-owner", exists=None, owner="unresolved")
            return result
    target = target.resolve()
    result.update(target=str(target), exists=target.exists())
    if clean.endswith("/"):
        result["status"] = "directory-mention"
        return result
    if result["exists"] and Path(clean).suffix and not target.is_file():
        result["status"] = "not-a-file"
        return result
    if not result["exists"] and ambiguous_optional:
        result.update(status="qualification-uncertain", exists=None)
        return result
    if (candidate["syntax"] == "inline" and not result["exists"] and "/" not in clean
            and not re.search(r"\b(?:read|load|consult|follow|run|execute|see|open)\b", ctx, re.I)):
        result.update(status="role-uncertain", exists=None, owner="unresolved")
        return result
    result["status"] = "ok" if result["exists"] else "optional-missing" if optional else "missing"
    return result


def classify_reference(skill_dir: Path, text: str, match: re.Match[str]) -> dict:
    """Compatibility wrapper for callers using the original inline regex API."""
    raw = inline_path(match.group(1)) or match.group(1)
    return resolve_reference(skill_dir, skill_dir / "SKILL.md", text,
                             {"raw": raw, "start": match.start(), "end": match.end(), "syntax": "inline"})


def referenced_paths(skill_dir: Path, text: str, source_file: Path | None = None) -> list[dict]:
    candidates, _ = reference_candidates(text)
    return [resolve_reference(skill_dir, source_file or skill_dir / "SKILL.md", text, candidate)
            for candidate in candidates]


def scan_instruction_references(skill_dir: Path, entry: Path, max_files: int = REFERENCE_SCAN_LIMIT) -> dict:
    queue = deque([(entry.resolve(), skill_dir.resolve())])
    scheduled = {normalized_root_key(entry)}
    visited, refs, skipped = [], [], []
    excluded_blocks = 0
    while queue:
        if len(visited) >= max_files:
            skipped.extend({"path": str(path), "reason": "traversal-limit"} for path, _ in queue)
            break
        source, owner = queue.popleft()
        try:
            text = source.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            skipped.append({"path": str(source), "reason": "unreadable", "detail": str(error)})
            continue
        visited.append(str(source))
        candidates, excluded = reference_candidates(text)
        excluded_blocks += excluded
        for candidate in candidates:
            ref = resolve_reference(owner, source, text, candidate)
            refs.append(ref)
            if ref["status"] != "ok" or not ref["target"]:
                continue
            target = Path(ref["target"])
            if not target.is_file() or not target.name.lower().endswith((".md", ".md.template")):
                continue
            key = normalized_root_key(target)
            if key not in scheduled:
                scheduled.add(key)
                queue.append((target, owner_for(target, owner)))
    uncertain = [r for r in refs if r["status"] not in {"ok", "missing", "external-or-anchor"}]
    return {"scope": REFERENCE_SCOPE, "status": "partial" if skipped or uncertain else "complete",
            "visited_files": visited, "skipped_files": skipped, "max_files": max_files,
            "excluded_fenced_blocks": excluded_blocks, "uncertain_count": len(uncertain), "refs": refs}


def line_ending_issue(data: bytes) -> str | None:
    has_crlf = b"\r\n" in data
    has_bare_lf = bool(re.search(rb"(?<!\r)\n", data))
    has_bare_cr = bool(re.search(rb"\r(?!\n)", data))
    if has_bare_cr:
        return "bare-cr"
    if has_crlf and has_bare_lf:
        return "mixed-crlf-lf"
    return None


def audit_skill(root_label: str, skill_md: Path, max_reference_files: int = REFERENCE_SCAN_LIMIT) -> dict:
    skill_dir = skill_md.parent
    data = skill_md.read_bytes()
    text = data.decode("utf-8-sig")
    meta, body = parse_frontmatter(text)
    lines = text.splitlines()
    lower = text.lower()
    desc = meta.get("description", "")
    name = meta.get("name", "")
    reference_scan = scan_instruction_references(skill_dir, skill_md, max_reference_files)
    refs = reference_scan["refs"]
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
        "instruction_files_visited": len(reference_scan["visited_files"]),
        "uncertain_refs": reference_scan["uncertain_count"],
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
        issues.append(("warning", "skill_md_too_large", f"Review loading cost ({metrics['lines']} lines); length alone is not a correctness failure"))
    if missing_required:
        issues.append(("blocker", "missing_referenced_file", f"{len(missing_required)} required referenced paths missing"))
    if reference_scan["status"] == "partial":
        issues.append(("warning", "reference_scan_partial", "Optional, dynamic, unsupported, unreadable or bounded references remain; inspect reference_scan"))
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
    ending_issue = line_ending_issue(data)
    if ending_issue:
        severity = "blocker" if ending_issue == "bare-cr" else "warning"
        issues.append((severity, "mixed_line_endings", f"SKILL.md line ending issue: {ending_issue}"))
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
        "reference_scan": {key: value for key, value in reference_scan.items() if key != "refs"},
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


def audit_agents(path: Path, max_reference_files: int = REFERENCE_SCAN_LIMIT) -> dict:
    """AGENTS is an instruction document, not a skill/frontmatter instance."""
    scan = scan_instruction_references(path.parent, path, max_reference_files)
    missing = sum(ref["status"] == "missing" for ref in scan["refs"])
    issues = []
    if missing:
        issues.append({"severity": "blocker", "code": "missing_referenced_file", "detail": f"{missing} required referenced paths missing"})
    if scan["status"] == "partial":
        issues.append({"severity": "warning", "code": "reference_scan_partial", "detail": "Some instruction references were not resolved or visited"})
    return {"path": str(path), "kind": "agents", "refs": scan.pop("refs"), "reference_scan": scan,
            "issues": issues, "checks": ["readability", "reachable-markdown-references"],
            "not_checked": ["skill-frontmatter", "policy-semantics", "instruction-precedence"]}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit declared skill/AGENTS surfaces and reachable Markdown references; not semantic or executable certification.")
    parser.add_argument("--root", action="append", default=[], help="Isolated audit root as label=path; repeat for multiple roots.")
    parser.add_argument("--optional-root", action="append", default=[], help="Add an optional label=path root; absence is reported as a skip.")
    parser.add_argument("--only-roots", action="store_true", help="Audit only explicit roots/AGENTS, without profile defaults.")
    parser.add_argument("--include-system", action="store_true", help="Also discover .system/*/SKILL.md under selected roots.")
    parser.add_argument("--agents", action="append", default=[], metavar="PATH", help="Explicit AGENTS instruction file, checked separately from SKILL frontmatter.")
    parser.add_argument("--max-reference-files", type=int, default=REFERENCE_SCAN_LIMIT, help="Per-entry reachable Markdown limit; remaining files are reported partial.")
    parser.add_argument("--json-out", default="", help="Write full JSON report to this path.")
    parser.add_argument("--fail-on-blocker", action="store_true", help="Exit nonzero when blockers are found.")
    parser.add_argument("--markdown-out", default="", help="Write a compact Markdown report to this path.")
    args = parser.parse_args()
    if args.only_roots and not (args.root or args.optional_root or args.agents):
        parser.error("--only-roots requires --root, --optional-root or --agents")
    if args.max_reference_files < 1:
        parser.error("--max-reference-files must be positive")
    for option in (args.root, args.optional_root):
        for item in option:
            if "=" not in item or not all(part.strip() for part in item.split("=", 1)):
                parser.error("root inputs require a nonempty label=path")
    return args


def write_markdown(report: dict, path: Path) -> None:
    lines = [
        "# Skill Portfolio Audit",
        "",
        f"Skill surfaces checked: {report['summary']['skill_count']}",
        f"Blockers: {report['summary']['severity_counts'].get('blocker', 0)}",
        f"Warnings: {report['summary']['severity_counts'].get('warning', 0)}",
        f"Status: {report.get('status', 'unknown')}",
        f"AGENTS files checked: {report['summary'].get('agents_count', 0)}",
        "",
        "## Declared Scope",
        "",
        report["scope"]["discovery"],
        REFERENCE_SCOPE,
        "",
    ]
    for label, root in report["roots"].items():
        lines.append(f"- {label}: {root['status']}, required={root['required']}, {root['path']} ({root['skill_count']} entries)")
    for row in report["scope"]["skipped"] + report["scope"]["missing"]:
        lines.append(f"- {row['reason']}: {row['path']}")
    lines += [
        "",
        "## Structural Heuristic Scores (not capability or quality measurements)",
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
                lines.append(f"- ref `{ref['ref']}`: {ref['status']} ({ref['owner']}) at {ref['source']}:{ref['line']}")
        lines.append("")
    for item in report.get("agents", []):
        lines += [f"### AGENTS / {item['path']}", ""]
        for issue in item["issues"]:
            lines.append(f"- {issue['severity']} `{issue['code']}`: {issue['detail']}")
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    explicit_scope = bool(args.root or args.optional_root or args.agents)
    profile_path, authority_errors = (None, []) if explicit_scope else profile_authority_errors()
    if authority_errors and not explicit_scope:
        blocked = {
            "status": "blocked",
            "failure_class": "profile-authority",
            "profile": str(profile_path),
            "errors": authority_errors,
            "scope": {"selected": [], "visited": [], "skipped": [], "missing": [],
                      "unresolved": ["Profile defaults could not be selected because profile authority is invalid."]},
            "repair": "Restore Q_PROFILE_PATH authority or provide one or more explicit --root label=path values.",
        }
        if args.json_out:
            Path(args.json_out).write_text(json.dumps(blocked, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(blocked, ensure_ascii=False, indent=2))
        return 2
    # Public explicit inputs define an isolated audit and never read a personal profile.
    roots = {} if explicit_scope or authority_errors else default_roots()
    required = {label: label not in OPTIONAL_DEFAULT_ROOTS for label in roots}
    requests = [{"label": label, "path": str(path), "required": required[label], "origin": "profile"}
                for label, path in roots.items()]
    seen_explicit = {}
    for values, is_required in ((args.root, True), (args.optional_root, False)):
        for item in values:
            label, raw = (part.strip() for part in item.split("=", 1))
            root = Path(raw).expanduser()
            identity = (normalized_root_key(root), is_required)
            if label in seen_explicit and seen_explicit[label] != identity:
                raise SystemExit(f"conflicting repeated root label: {label}")
            seen_explicit[label] = identity
            roots[label] = root
            required[label] = is_required
            requests.append({"label": label, "path": str(root), "required": is_required, "origin": "explicit"})

    report = {
        "authority": {
            "mode": "explicit-roots" if explicit_scope else "profile",
            "profile": str(profile_path) if profile_path is not None else None,
            "warnings": authority_errors,
        },
        "roots": {},
        "skills": [],
        "agents": [],
        "scope": {"requests": requests, "selected": [], "visited": [], "skipped": [], "missing": [],
                  "discovery": "Immediate */SKILL.md entries; .system/*/SKILL.md is opt-in. Other nested layouts are not searched. AGENTS requires explicit input.",
                  "include_system": args.include_system, "reference_scope": REFERENCE_SCOPE},
        "issues": [],
    }
    seen_roots: dict[str, str] = {}
    for label, root in roots.items():
        root = root.expanduser().resolve()
        root_key = normalized_root_key(root)
        report["scope"]["selected"].append({"kind": "root", "label": label, "path": str(root), "required": required[label]})
        duplicate_of = seen_roots.get(root_key)
        if duplicate_of:
            report["roots"][label] = {
                "path": str(root),
                "skill_count": 0,
                "exists": root.exists(),
                "duplicate_of": duplicate_of,
                "required": required[label], "status": "duplicate",
            }
            report["scope"]["skipped"].append({"path": str(root), "reason": "duplicate-root", "label": label, "duplicate_of": duplicate_of})
            if required[label] and not root.is_dir():
                report["scope"]["missing"].append({"path": str(root), "reason": "required-root-missing", "label": label})
            continue
        seen_roots[root_key] = label
        skill_files = sorted(root.glob("*/SKILL.md")) if root.is_dir() else []
        system_files = sorted((root / ".system").glob("*/SKILL.md")) if root.is_dir() else []
        if args.include_system:
            skill_files += system_files
        elif (root / ".system").is_dir():
            report["scope"]["skipped"].append({"path": str(root / ".system"), "reason": "system-not-selected", "entries": [str(path) for path in system_files]})
        status = "visited" if root.is_dir() else "missing" if required[label] else "optional-missing"
        report["roots"][label] = {
            "path": str(root),
            "skill_count": len(skill_files),
            "exists": root.exists(),
            "duplicate_of": None,
            "required": required[label], "status": status,
            "selected_entries": [str(path) for path in skill_files], "visited_entries": [],
        }
        if not root.is_dir():
            bucket = "missing" if required[label] else "skipped"
            report["scope"][bucket].append({"path": str(root), "label": label, "reason": "required-root-missing" if required[label] else "optional-root-missing"})
            continue
        report["scope"]["visited"].append({"path": str(root), "kind": "root", "label": label})
        for skill_md in skill_files:
            try:
                item = audit_skill(label, skill_md, args.max_reference_files)
            except (OSError, UnicodeError) as error:
                report["scope"]["missing"].append({"path": str(skill_md), "reason": "skill-unreadable", "detail": str(error)})
                continue
            report["skills"].append(item)
            report["roots"][label]["visited_entries"].append(str(skill_md))
            report["scope"]["visited"].append({"path": str(skill_md), "kind": "skill", "label": label})

    seen_agents = set()
    for raw in args.agents:
        path = Path(raw).expanduser().resolve()
        key = normalized_root_key(path)
        report["scope"]["selected"].append({"path": str(path), "kind": "agents", "required": True})
        if key in seen_agents:
            report["scope"]["skipped"].append({"path": str(path), "reason": "duplicate-agents"})
            continue
        seen_agents.add(key)
        if not path.is_file():
            report["scope"]["missing"].append({"path": str(path), "reason": "required-agents-missing"})
            continue
        item = audit_agents(path, args.max_reference_files)
        report["agents"].append(item)
        if str(path) in item["reference_scan"]["visited_files"]:
            report["scope"]["visited"].append({"path": str(path), "kind": "agents"})
        else:
            report["scope"]["missing"].append({"path": str(path), "reason": "agents-unreadable"})

    for missing in report["scope"]["missing"]:
        report["issues"].append({"severity": "blocker", "code": "scope_incomplete", "detail": f"{missing['reason']}: {missing['path']}"})

    issue_counts = Counter()
    severity_counts = Counter()
    root_scores = defaultdict(list)
    for item in report["skills"]:
        root_scores[item["root"]].append(item["score"])
    for item in report["skills"] + report["agents"] + [{"issues": report["issues"]}]:
        for issue in item["issues"]:
            issue_counts[issue["code"]] += 1
            severity_counts[issue["severity"]] += 1
    report["summary"] = {
        "score_meaning": "Structural heuristics only; not capability, semantic quality, full YAML validation, or behavioral coverage.",
        "skill_count": len(report["skills"]),
        "agents_count": len(report["agents"]),
        "selected_root_count": len(report["roots"]),
        "visited_root_count": sum(r["status"] == "visited" for r in report["roots"].values()),
        "missing_required_scope_count": len(report["scope"]["missing"]),
        "skipped_scope_count": len(report["scope"]["skipped"]),
        "partial_reference_scan_count": sum(item["reference_scan"]["status"] == "partial" for item in report["skills"] + report["agents"]),
        "issue_counts": dict(issue_counts),
        "severity_counts": dict(severity_counts),
        "root_average_scores": {
            root: round(sum(scores) / len(scores), 1) if scores else 0
            for root, scores in root_scores.items()
        },
    }
    report["status"] = ("blocked" if report["scope"]["missing"] else
                        "findings" if severity_counts.get("blocker") else
                        "partial" if report["summary"]["partial_reference_scan_count"] else
                        "completed-with-skips" if report["scope"]["skipped"] else "completed")
    report["summary"]["status"] = report["status"]

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown_out:
        write_markdown(report, Path(args.markdown_out))
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    if report["scope"]["missing"]:
        return 2
    return 1 if args.fail_on_blocker and severity_counts.get("blocker", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
