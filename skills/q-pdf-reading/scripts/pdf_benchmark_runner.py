#!/usr/bin/env python3
"""Run PDF reading benchmark manifests against local samples."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import pdf_to_reading_pack  # noqa: E402


GRADE_RANK = {"missing": 0, "low": 1, "medium": 2, "high": 3}
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]{2,}|[\u4e00-\u9fff]{2,}")


def configure_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def token_set(text: str, limit: int = 300) -> set[str]:
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    stop = {"the", "and", "for", "with", "from", "this", "that", "page"}
    seen: list[str] = []
    for token in tokens:
        if token in stop or token in seen:
            continue
        seen.append(token)
        if len(seen) >= limit:
            break
    return set(seen)


def slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return value.strip("-") or "sample"


def resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


def resolve_ground_truth(manifest_base: Path, pack_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    pack_path = pack_dir / path
    return pack_path if pack_path.exists() else manifest_base / path


def merge_options(defaults: dict[str, Any], sample: dict[str, Any], mode: str) -> dict[str, Any]:
    options = dict(defaults)
    options.update(sample.get("options", {}))
    options["mode"] = mode
    return options


def run_sample(pdf: Path, pack_dir: Path, options: dict[str, Any]) -> int:
    args = [
        str(pdf),
        "--out",
        str(pack_dir),
        "--mode",
        str(options.get("mode", "robust")),
        "--max-render-pages",
        str(options.get("max_render_pages", 30)),
        "--render-dpi",
        str(options.get("render_dpi", 144)),
        "--max-table-pages",
        str(options.get("max_table_pages", 80)),
        "--max-table-probe-pages",
        str(options.get("max_table_probe_pages", 5)),
    ]
    if options.get("ocr_pages"):
        args.append("--ocr-pages")
    if options.get("render_pages"):
        args.append("--render-pages")
    if options.get("table_structure_probe"):
        args.append("--table-structure-probe")
    return pdf_to_reading_pack.main(args)


def collect_pack(pack_dir: Path) -> dict[str, Any]:
    strategy = read_json(pack_dir / "strategy_comparison.json")
    confidence = read_json(pack_dir / "confidence_report.json")
    extraction = read_json(pack_dir / "extraction_metadata.json")
    tables = read_json(pack_dir / "tables" / "tables_manifest.json")
    table_probe = read_json(pack_dir / "tables" / "table_structure_probe.json")
    routing = strategy.get("routing", {})
    selection = strategy.get("selection", {})
    grade = confidence.get("grade", {})
    artifacts = {}
    for rel in [
        "extracted_text.md",
        "strategy_comparison.md",
        "strategy_comparison.json",
        "confidence_report.md",
        "confidence_report.json",
        "reading_notes.md",
        "deep_backend_report.md",
        "tables/table_extraction_report.md",
        "tables/tables_manifest.json",
        "tables/table_structure_probe_report.md",
        "tables/table_structure_probe.json",
    ]:
        artifacts[rel] = (pack_dir / rel).exists()
    pages_dir = pack_dir / "pages"
    artifacts["pages"] = pages_dir.exists() and any(pages_dir.glob("page_*.png"))
    ocr_dir = pack_dir / "ocr"
    artifacts["ocr/ocr_text.md"] = (ocr_dir / "ocr_text.md").exists()
    return {
        "strategy": strategy,
        "confidence": confidence,
        "extraction": extraction,
        "tables": tables,
        "table_structure_probe": table_probe,
        "pdf_type": routing.get("pdf_type") or extraction.get("pdf_type"),
        "recommended_strategy": routing.get("recommended_strategy"),
        "selected_strategy": selection.get("selected") or extraction.get("extractor"),
        "confidence_grade": grade.get("grade", "missing"),
        "confidence_score": grade.get("score"),
        "tables_found": tables.get("tables_found", 0) if tables else 0,
        "table_structure_regions": table_probe.get("candidate_table_regions", 0) if table_probe else 0,
        "table_structure_cells": table_probe.get("estimated_grid_cells", 0) if table_probe else 0,
        "artifacts": artifacts,
    }


def check_expectations(observed: dict[str, Any], expected: dict[str, Any], pack_dir: Path, manifest_base: Path) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    if "pdf_type" in expected:
        wanted = expected["pdf_type"]
        allowed = wanted if isinstance(wanted, list) else [wanted]
        add("pdf_type", observed.get("pdf_type") in allowed, f"observed={observed.get('pdf_type')} expected={allowed}")
    if "selected_strategy" in expected:
        wanted = expected["selected_strategy"]
        allowed = wanted if isinstance(wanted, list) else [wanted]
        add("selected_strategy", observed.get("selected_strategy") in allowed, f"observed={observed.get('selected_strategy')} expected={allowed}")
    if "min_confidence_grade" in expected:
        observed_grade = str(observed.get("confidence_grade", "missing"))
        wanted_grade = str(expected["min_confidence_grade"])
        passed = GRADE_RANK.get(observed_grade, 0) >= GRADE_RANK.get(wanted_grade, 0)
        add("min_confidence_grade", passed, f"observed={observed_grade} expected>={wanted_grade}")
    if "min_confidence_score" in expected:
        score = observed.get("confidence_score")
        minimum = int(expected["min_confidence_score"])
        add("min_confidence_score", score is not None and int(score) >= minimum, f"observed={score} expected>={minimum}")
    if "min_tables" in expected:
        found = int(observed.get("tables_found", 0) or 0)
        minimum = int(expected["min_tables"])
        add("min_tables", found >= minimum, f"observed={found} expected>={minimum}")
    if "min_table_structure_regions" in expected:
        found = int(observed.get("table_structure_regions", 0) or 0)
        minimum = int(expected["min_table_structure_regions"])
        add("min_table_structure_regions", found >= minimum, f"observed={found} expected>={minimum}")
    if "min_table_structure_cells" in expected:
        found = int(observed.get("table_structure_cells", 0) or 0)
        minimum = int(expected["min_table_structure_cells"])
        add("min_table_structure_cells", found >= minimum, f"observed={found} expected>={minimum}")
    ground_truth = expected.get("ground_truth", {})
    for kind, rel in ground_truth.items():
        gt_path = resolve_ground_truth(manifest_base, pack_dir, str(rel))
        add(f"ground_truth:{kind}", gt_path.exists(), str(gt_path))
        if kind == "text" and gt_path.exists():
            extracted_path = pack_dir / "extracted_text.md"
            if extracted_path.exists():
                expected_tokens = token_set(read_text(gt_path))
                observed_tokens = token_set(read_text(extracted_path))
                coverage = len(expected_tokens & observed_tokens) / len(expected_tokens) if expected_tokens else 1.0
                minimum = float(expected.get("min_text_token_coverage", 0.35))
                add("text_token_coverage", coverage >= minimum, f"observed={coverage:.3f} expected>={minimum:.3f}")
        if kind == "tables" and gt_path.exists():
            gt_tables = read_json(gt_path)
            expected_count = int(gt_tables.get("table_count", 0) or len(gt_tables.get("tables", [])))
            if expected_count and ("min_tables" in expected or expected.get("check_table_count")):
                found = int(observed.get("tables_found", 0) or 0)
                minimum = int(expected.get("min_tables", min(expected_count, 1)))
                add("ground_truth_table_count", found >= minimum, f"observed={found} expected_ground_truth={expected_count} minimum={minimum}")
        if kind == "ocr" and gt_path.exists():
            gt_ocr = read_json(gt_path)
            summary = []
            if "word_count" in gt_ocr:
                summary.append(f"words={gt_ocr.get('word_count')}")
            if "entity_labels" in gt_ocr:
                summary.append(f"labels={gt_ocr.get('entity_labels')}")
            if "link_count" in gt_ocr:
                summary.append(f"links={gt_ocr.get('link_count')}")
            if summary:
                add("ground_truth_ocr_summary", True, ", ".join(summary))
    for rel in expected.get("require_artifacts", []):
        rel_path = str(rel)
        if rel_path in observed["artifacts"]:
            exists = bool(observed["artifacts"][rel_path])
        else:
            exists = (pack_dir / rel_path).exists()
        add(f"artifact:{rel_path}", exists, "present" if exists else "missing")
    if not checks:
        add("pack_created", bool(observed.get("extraction") or observed.get("strategy")), "no explicit expectations")
    return all(item["passed"] for item in checks), checks


def write_reports(out_dir: Path, manifest: dict[str, Any], results: list[dict[str, Any]]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    passed = sum(1 for item in results if item["passed"])
    payload = {
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_name": manifest.get("name"),
        "sample_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
    (out_dir / "benchmark_results.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8-sig")
    lines = [
        "# PDF Benchmark Results",
        "",
        f"Created UTC: `{payload['created_utc']}`",
        f"Manifest: `{manifest.get('name', '')}`",
        f"Passed: {passed}/{len(results)}",
        "",
        "## Samples",
        "",
    ]
    for item in results:
        state = "PASS" if item["passed"] else "FAIL"
        observed = item["observed"]
        lines.extend(
            [
                f"### {item['id']} - {state}",
                "",
                f"- PDF type: `{observed.get('pdf_type')}`",
                f"- Selected strategy: `{observed.get('selected_strategy')}`",
                f"- Confidence: `{observed.get('confidence_grade')}` ({observed.get('confidence_score')})",
                f"- Tables found: {observed.get('tables_found')}",
                f"- Table-structure regions: {observed.get('table_structure_regions')}",
                f"- Table-structure cells: {observed.get('table_structure_cells')}",
                f"- Pack: `{item['pack_dir']}`",
                "",
                "Checks:",
            ]
        )
        for check in item["checks"]:
            mark = "PASS" if check["passed"] else "FAIL"
            lines.append(f"- {mark} {check['name']}: {check['detail']}")
        lines.append("")
    (out_dir / "benchmark_results.md").write_text("\n".join(lines), encoding="utf-8-sig")


def main(argv: list[str]) -> int:
    configure_stdout()
    parser = argparse.ArgumentParser(description="Run q-pdf-reading benchmark manifests.")
    parser.add_argument("manifest", help="Benchmark manifest JSON")
    parser.add_argument("--out", required=True, help="Output root for reading packs and benchmark reports")
    parser.add_argument("--sample", action="append", default=[], help="Run only matching sample id; can be repeated")
    parser.add_argument("--skip-existing", action="store_true", help="Reuse existing pack folders when possible")
    parser.add_argument("--max-samples", type=int, help="Maximum samples to run")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest_base = manifest_path.parent
    manifest = read_json(manifest_path)
    if int(manifest.get("version", 0)) != 0:
        raise SystemExit("Unsupported manifest version; expected 0")

    out_dir = Path(args.out)
    defaults = manifest.get("defaults", {})
    selected_ids = set(args.sample)
    samples = manifest.get("samples", [])
    if selected_ids:
        samples = [sample for sample in samples if sample.get("id") in selected_ids]
    if args.max_samples is not None:
        samples = samples[: args.max_samples]
    if not samples:
        raise SystemExit("No samples selected")

    results = []
    for sample in samples:
        sample_id = slug(str(sample.get("id") or Path(sample["pdf"]).stem))
        pdf = resolve_path(manifest_base, sample["pdf"])
        if not pdf.exists():
            results.append(
                {
                    "id": sample_id,
                    "pdf": str(pdf),
                    "mode": None,
                    "pack_dir": "",
                    "passed": False,
                    "observed": {},
                    "checks": [{"name": "pdf_exists", "passed": False, "detail": str(pdf)}],
                }
            )
            continue
        modes = sample.get("modes") or [defaults.get("mode", "robust")]
        for mode in modes:
            pack_dir = out_dir / "packs" / sample_id / str(mode)
            pack_dir.mkdir(parents=True, exist_ok=True)
            if not args.skip_existing or not (pack_dir / "extracted_text.md").exists():
                exit_code = run_sample(pdf, pack_dir, merge_options(defaults, sample, str(mode)))
                if exit_code != 0:
                    results.append(
                        {
                            "id": sample_id,
                            "pdf": str(pdf),
                            "mode": mode,
                            "pack_dir": str(pack_dir.resolve()),
                            "passed": False,
                            "observed": {},
                            "checks": [{"name": "runner_exit", "passed": False, "detail": str(exit_code)}],
                        }
                    )
                    continue
            observed = collect_pack(pack_dir)
            expected = sample.get("expected", {})
            passed, checks = check_expectations(observed, expected, pack_dir, manifest_base)
            results.append(
                {
                    "id": sample_id,
                    "pdf": str(pdf),
                    "mode": mode,
                    "pack_dir": str(pack_dir.resolve()),
                    "passed": passed,
                    "observed": observed,
                    "checks": checks,
                }
            )
    write_reports(out_dir, manifest, results)
    failed = [item for item in results if not item["passed"]]
    print(f"Benchmark passed: {len(results) - len(failed)}/{len(results)}")
    print(f"Wrote: {out_dir / 'benchmark_results.md'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
