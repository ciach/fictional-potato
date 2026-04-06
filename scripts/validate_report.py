#!/usr/bin/env python3
"""
Validate child report JSON files for the coverage harness.

This script tries jsonschema if available. If not, it performs a strict fallback validation
for the required top-level structure.

Examples:
  python validate_report.py --report /path/report.json
  python validate_report.py --children-root /path/run/children
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REQUIRED_FIELDS = {
    "target_id": str,
    "status": str,
    "source_files": list,
    "test_files": list,
    "coverage_evidence": list,
    "missing_scenarios": list,
    "untested_branches": list,
    "edge_cases": list,
    "recommended_tests": list,
    "confidence": (int, float),
    "risk_score": (int, float),
    "summary": str,
}
VALID_STATUS = {"success", "partial_success", "failed"}


def load_schema(schema_path: Path) -> dict | None:
    if not schema_path.exists():
        return None
    return json.loads(schema_path.read_text(encoding="utf-8"))


def fallback_validate(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in data:
            errors.append(f"missing field: {field}")
            continue
        if not isinstance(data[field], expected_type):
            errors.append(f"wrong type for {field}: expected {expected_type}, got {type(data[field])}")
    if "status" in data and data["status"] not in VALID_STATUS:
        errors.append(f"invalid status: {data['status']}")
    if "confidence" in data:
        try:
            val = float(data["confidence"])
            if not 0 <= val <= 1:
                errors.append("confidence must be between 0 and 1")
        except Exception:
            errors.append("confidence must be numeric")
    if "risk_score" in data:
        try:
            val = float(data["risk_score"])
            if not 0 <= val <= 100:
                errors.append("risk_score must be between 0 and 100")
        except Exception:
            errors.append("risk_score must be numeric")
    return errors


def validate_with_jsonschema(data: dict, schema: dict) -> List[str]:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return ["jsonschema package not available"]
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(x) for x in err.absolute_path) or '<root>'}: {err.message}" for err in validator.iter_errors(data)]


def validate_report(report_path: Path, schema_path: Path | None) -> dict:
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"report": report_path.as_posix(), "valid": False, "errors": [f"json parse error: {e}"]}

    errors: List[str] = []
    if schema_path and schema_path.exists():
        schema = load_schema(schema_path)
        schema_errors = validate_with_jsonschema(data, schema) if schema else []
        if schema_errors and schema_errors != ["jsonschema package not available"]:
            errors.extend(schema_errors)
        else:
            errors.extend(fallback_validate(data))
    else:
        errors.extend(fallback_validate(data))

    return {
        "report": report_path.as_posix(),
        "valid": len(errors) == 0,
        "errors": errors,
    }


def discover_reports(children_root: Path) -> List[Path]:
    return sorted(children_root.glob("**/artifacts/report.json"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", help="Single report.json path")
    parser.add_argument("--children-root", help="Root containing child folders")
    parser.add_argument("--schema", help="Path to schema JSON")
    parser.add_argument("--output", help="Optional path to write validation results JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    schema_path = Path(args.schema).resolve() if args.schema else None

    report_paths: List[Path] = []
    if args.report:
        report_paths = [Path(args.report).resolve()]
    elif args.children_root:
        report_paths = discover_reports(Path(args.children_root).resolve())
    else:
        raise SystemExit("Provide --report or --children-root")

    results = [validate_report(path, schema_path) for path in report_paths]
    payload = {
        "report_count": len(results),
        "valid_count": sum(1 for r in results if r["valid"]),
        "invalid_count": sum(1 for r in results if not r["valid"]),
        "results": results,
    }

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2))
    return 0 if payload["invalid_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
