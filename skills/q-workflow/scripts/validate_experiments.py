#!/usr/bin/env python3
r"""Validate draft q-workflow experiment YAML files.

The experiment layer is intentionally small: it describes a manual/agent
execution contract, not a runtime engine. This validator catches structural
drift before a draft starts depending on implicit chat behavior again.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on lean Python installs
    yaml = None


REQUIRED_TOP_LEVEL = {
    "version",
    "kind",
    "name",
    "status",
    "description",
    "compatibility",
    "inputs",
    "policies",
    "artifacts",
    "stages",
    "finish",
}
EXPECTED_STAGE_ORDER = ("route", "plan", "edit", "validate", "review", "checkpoint")
ALLOWED_STAGE_TYPES = {"agent", "context", "deterministic", "state"}
REQUIRED_ASK_BEFORE = {
    "destructive_changes",
    "remote_push",
    "public_sync",
    "credential_handling",
    "broad_dependency_install",
}
REQUIRED_ARTIFACTS = {"plan", "validation_log", "review_notes", "checkpoint"}
REQUIRED_FINISH_FIELDS = {"changed_files", "validation", "next_action_or_done_state"}


def configure_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass


def as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def default_experiment_files() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    return sorted((root / "experiments").glob("*.yaml"))


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if value in {"true", "True"}:
        return True
    if value in {"false", "False"}:
        return False
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    try:
        return int(value)
    except ValueError:
        return value


def prepared_yaml_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append((indent, raw.strip()))
    return lines


def parse_block_scalar(lines: list[tuple[int, str]], index: int, parent_indent: int) -> tuple[str, int]:
    parts: list[str] = []
    while index < len(lines):
        indent, content = lines[index]
        if indent <= parent_indent:
            break
        parts.append(content)
        index += 1
    return " ".join(parts).strip(), index


def parse_mapping_entry(content: str) -> tuple[str, str]:
    if ":" not in content:
        raise ValueError(f"expected mapping entry, got {content!r}")
    key, value = content.split(":", 1)
    key = key.strip()
    if not key:
        raise ValueError(f"empty mapping key in {content!r}")
    return key, value.strip()


def parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, content = lines[index]
    if current_indent < indent:
        return {}, index
    if content.startswith("- "):
        return parse_yaml_list(lines, index, current_indent)
    return parse_yaml_map(lines, index, current_indent)


def parse_yaml_map(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    data: dict[str, Any] = {}
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"unexpected indent before {content!r}")
        if content.startswith("- "):
            break
        key, value = parse_mapping_entry(content)
        index += 1
        if value == ">":
            data[key], index = parse_block_scalar(lines, index, current_indent)
        elif value:
            data[key] = parse_scalar(value)
        else:
            if index < len(lines) and lines[index][0] > current_indent:
                data[key], index = parse_yaml_block(lines, index, lines[index][0])
            else:
                data[key] = None
    return data, index


def parse_yaml_list(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    while index < len(lines):
        current_indent, content = lines[index]
        if current_indent < indent:
            break
        if current_indent != indent or not content.startswith("- "):
            break
        item = content[2:].strip()
        index += 1
        if not item:
            if index < len(lines) and lines[index][0] > current_indent:
                value, index = parse_yaml_block(lines, index, lines[index][0])
                items.append(value)
            else:
                items.append(None)
            continue
        if not ((item.startswith('"') and item.endswith('"')) or (item.startswith("'") and item.endswith("'"))) and ":" in item:
            key, value = parse_mapping_entry(item)
            mapping: dict[str, Any] = {}
            if value == ">":
                mapping[key], index = parse_block_scalar(lines, index, current_indent)
            elif value:
                mapping[key] = parse_scalar(value)
            else:
                if index < len(lines) and lines[index][0] > current_indent:
                    mapping[key], index = parse_yaml_block(lines, index, lines[index][0])
                else:
                    mapping[key] = None
            if index < len(lines) and lines[index][0] > current_indent:
                extra, index = parse_yaml_map(lines, index, lines[index][0])
                mapping.update(extra)
            items.append(mapping)
        else:
            items.append(parse_scalar(item))
    return items, index


def parse_yaml_subset(text: str) -> Any:
    lines = prepared_yaml_lines(text)
    if not lines:
        return {}
    data, index = parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError(f"unparsed YAML content near {lines[index][1]!r}")
    return data


def load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"YAML read failed: {exc}")
        return None
    if yaml is not None:
        try:
            return yaml.safe_load(text)
        except Exception as exc:  # noqa: BLE001 - show concise validation failure
            errors.append(f"YAML parse failed: {exc}")
            return None
    try:
        return parse_yaml_subset(text)
    except Exception as exc:  # noqa: BLE001 - keep dependency-free fallback transparent
        errors.append(f"YAML subset parse failed without PyYAML: {exc}")
        return None

def validate_top_level(data: Any, errors: list[str]) -> None:
    if not isinstance(data, dict):
        errors.append("top-level document must be a mapping")
        return

    missing = sorted(REQUIRED_TOP_LEVEL.difference(data))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")

    if data.get("version") != 0:
        errors.append("version must be 0 for the current experiment schema")
    if data.get("kind") != "q-workflow-experiment":
        errors.append("kind must be q-workflow-experiment")
    if not isinstance(data.get("name"), str) or not data.get("name"):
        errors.append("name must be a non-empty string")
    if data.get("status") not in {"draft", "active", "deprecated"}:
        errors.append("status must be draft, active, or deprecated")


def validate_compatibility(data: dict[str, Any], errors: list[str]) -> None:
    compatibility = data.get("compatibility")
    if not isinstance(compatibility, dict):
        errors.append("compatibility must be a mapping")
        return

    if compatibility.get("archon_install_required") is not False:
        errors.append("compatibility.archon_install_required must be false")

    executable_by = set(as_str_list(compatibility.get("executable_by")))
    if not executable_by.intersection({"codex", "human"}):
        errors.append("compatibility.executable_by must include codex or human")


def validate_policies(data: dict[str, Any], errors: list[str]) -> None:
    policies = data.get("policies")
    if not isinstance(policies, dict):
        errors.append("policies must be a mapping")
        return

    for key in ("preserve_user_changes", "prefer_repo_native_commands", "avoid_unrelated_refactors"):
        if policies.get(key) is not True:
            errors.append(f"policies.{key} must be true")

    ask_before = set(as_str_list(policies.get("ask_before")))
    missing = sorted(REQUIRED_ASK_BEFORE.difference(ask_before))
    if missing:
        errors.append(f"policies.ask_before missing gates: {', '.join(missing)}")


def validate_artifacts(data: dict[str, Any], errors: list[str]) -> None:
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be a mapping")
        return

    missing = sorted(REQUIRED_ARTIFACTS.difference(artifacts))
    if missing:
        errors.append(f"artifacts missing required entries: {', '.join(missing)}")


def validate_stages(data: dict[str, Any], errors: list[str]) -> None:
    stages = data.get("stages")
    if not isinstance(stages, list) or not stages:
        errors.append("stages must be a non-empty list")
        return

    stage_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            errors.append(f"stages[{index}] must be a mapping")
            continue

        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or not stage_id:
            errors.append(f"stages[{index}].id must be a non-empty string")
            continue
        if stage_id in stage_by_id:
            errors.append(f"duplicate stage id: {stage_id}")
            continue

        stage_by_id[stage_id] = stage
        ordered_ids.append(stage_id)

        if stage.get("type") not in ALLOWED_STAGE_TYPES:
            errors.append(f"stage {stage_id}: unsupported type {stage.get('type')!r}")
        if not isinstance(stage.get("goal"), str) or not stage.get("goal"):
            errors.append(f"stage {stage_id}: goal must be a non-empty string")
        if not as_str_list(stage.get("actions")):
            errors.append(f"stage {stage_id}: actions must be a non-empty string list")
        if not as_str_list(stage.get("outputs")):
            errors.append(f"stage {stage_id}: outputs must be a non-empty string list")

    if tuple(ordered_ids) != EXPECTED_STAGE_ORDER:
        errors.append(
            "stage order must be "
            + " -> ".join(EXPECTED_STAGE_ORDER)
            + f"; found {' -> '.join(ordered_ids)}"
        )

    for stage_id, stage in stage_by_id.items():
        deps = as_str_list(stage.get("depends_on", []))
        for dep in deps:
            if dep not in stage_by_id:
                errors.append(f"stage {stage_id}: unknown dependency {dep}")
            elif ordered_ids.index(dep) >= ordered_ids.index(stage_id):
                errors.append(f"stage {stage_id}: dependency {dep} must appear before dependent stage")

    validate_no_cycles(stage_by_id, errors)

    validate_stage_specific_rules(stage_by_id, errors)


def validate_no_cycles(stage_by_id: dict[str, dict[str, Any]], errors: list[str]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(stage_id: str, stack: list[str]) -> None:
        if stage_id in visited:
            return
        if stage_id in visiting:
            errors.append("stage dependency cycle: " + " -> ".join(stack + [stage_id]))
            return
        visiting.add(stage_id)
        for dep in as_str_list(stage_by_id[stage_id].get("depends_on", [])):
            if dep in stage_by_id:
                visit(dep, stack + [stage_id])
        visiting.remove(stage_id)
        visited.add(stage_id)

    for stage_id in stage_by_id:
        visit(stage_id, [])


def validate_stage_specific_rules(stage_by_id: dict[str, dict[str, Any]], errors: list[str]) -> None:
    validate = stage_by_id.get("validate")
    if validate is not None and not as_str_list(validate.get("success_when")):
        errors.append("stage validate: success_when must be a non-empty string list")

    checkpoint = stage_by_id.get("checkpoint")
    if checkpoint is not None:
        outputs = set(as_str_list(checkpoint.get("outputs")))
        missing = {"checkpoint", "handoff_summary"}.difference(outputs)
        if missing:
            errors.append(f"stage checkpoint: missing outputs {', '.join(sorted(missing))}")


def validate_finish(data: dict[str, Any], errors: list[str]) -> None:
    finish = data.get("finish")
    if not isinstance(finish, dict):
        errors.append("finish must be a mapping")
        return

    fields = set(as_str_list(finish.get("response_must_include")))
    missing = sorted(REQUIRED_FINISH_FIELDS.difference(fields))
    if missing:
        errors.append(f"finish.response_must_include missing fields: {', '.join(missing)}")


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_yaml(path, errors)
    if errors or data is None:
        return errors

    validate_top_level(data, errors)
    if isinstance(data, dict):
        validate_compatibility(data, errors)
        validate_policies(data, errors)
        validate_artifacts(data, errors)
        validate_stages(data, errors)
        validate_finish(data, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", type=Path, help="Experiment YAML files to validate")
    args = parser.parse_args(argv)

    files = args.files or default_experiment_files()
    if not files:
        print("No experiment YAML files found.", file=sys.stderr)
        return 1

    failed = False
    for path in files:
        errors = validate_file(path)
        if errors:
            failed = True
            print(f"FAIL {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"OK   {path}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
