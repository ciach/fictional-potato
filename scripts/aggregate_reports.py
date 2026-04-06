#!/usr/bin/env python3
"""
Aggregate child coverage analysis reports into summary JSON and Markdown.

Example:
  python aggregate_reports.py --children-root /path/run/children --output-dir /path/run/artifacts
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


SEVERITY_WEIGHT = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


def load_reports(children_root: Path) -> List[dict]:
    reports = []
    for report_path in sorted(children_root.glob("**/artifacts/report.json")):
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            report["_report_path"] = report_path.as_posix()
            reports.append(report)
        except Exception:
            reports.append({
                "target_id": report_path.parent.parent.name,
                "status": "failed",
                "source_files": [],
                "test_files": [],
                "coverage_evidence": [],
                "missing_scenarios": [],
                "untested_branches": [],
                "edge_cases": [],
                "recommended_tests": [],
                "confidence": 0,
                "risk_score": 0,
                "summary": "Failed to parse report JSON",
                "failures": ["invalid_json"],
                "_report_path": report_path.as_posix(),
            })
    return reports


def severity_score(report: dict) -> int:
    scenarios = report.get("missing_scenarios", [])
    return sum(SEVERITY_WEIGHT.get(item.get("severity", "low"), 1) for item in scenarios if isinstance(item, dict))


def compute_priority(report: dict) -> float:
    risk = float(report.get("risk_score", 0) or 0)
    confidence = float(report.get("confidence", 0) or 0)
    sev = severity_score(report)
    measured_bonus = 0.0
    for ev in report.get("coverage_evidence", []):
        if isinstance(ev, dict) and ev.get("kind") != "heuristic" and ev.get("used"):
            measured_bonus += 2.0
    # Higher risk and severity bubble up. Lower confidence also increases priority.
    return round(risk + (sev * 5) + ((1 - confidence) * 15) + measured_bonus, 2)


def build_summary(reports: List[dict]) -> dict:
    enriched = []
    for report in reports:
        item = dict(report)
        item["priority_score"] = compute_priority(report)
        enriched.append(item)

    valid_reports = [r for r in enriched if r.get("status") in {"success", "partial_success"}]
    ranked = sorted(enriched, key=lambda r: r["priority_score"], reverse=True)

    total_missing = sum(len(r.get("missing_scenarios", [])) for r in enriched)
    total_branches = sum(len(r.get("untested_branches", [])) for r in enriched)

    return {
        "report_count": len(enriched),
        "valid_report_count": len(valid_reports),
        "failed_report_count": len(enriched) - len(valid_reports),
        "total_missing_scenarios": total_missing,
        "total_untested_branches": total_branches,
        "ranked_targets": [
            {
                "target_id": r.get("target_id"),
                "priority_score": r.get("priority_score"),
                "risk_score": r.get("risk_score"),
                "confidence": r.get("confidence"),
                "missing_scenarios": len(r.get("missing_scenarios", [])),
                "untested_branches": len(r.get("untested_branches", [])),
                "status": r.get("status"),
                "summary": r.get("summary"),
                "report_path": r.get("_report_path"),
            }
            for r in ranked
        ],
    }


def render_markdown(summary: dict) -> str:
    lines = []
    lines.append("# Coverage Harness Summary")
    lines.append("")
    lines.append(f"- Reports processed: **{summary['report_count']}**")
    lines.append(f"- Valid reports: **{summary['valid_report_count']}**")
    lines.append(f"- Failed reports: **{summary['failed_report_count']}**")
    lines.append(f"- Total missing scenarios: **{summary['total_missing_scenarios']}**")
    lines.append(f"- Total untested branches: **{summary['total_untested_branches']}**")
    lines.append("")
    lines.append("## Ranked Targets")
    lines.append("")
    lines.append("| Rank | Target | Priority | Risk | Confidence | Missing | Branches | Status |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---|")
    for idx, item in enumerate(summary["ranked_targets"], start=1):
        lines.append(
            f"| {idx} | `{item['target_id']}` | {item['priority_score']} | {item['risk_score']} | "
            f"{item['confidence']} | {item['missing_scenarios']} | {item['untested_branches']} | {item['status']} |"
        )
    lines.append("")
    lines.append("## Top Findings")
    lines.append("")
    for idx, item in enumerate(summary["ranked_targets"][:10], start=1):
        lines.append(f"### {idx}. `{item['target_id']}`")
        lines.append(item["summary"] or "_No summary provided._")
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--children-root", required=True, help="Root containing child folders")
    parser.add_argument("--output-dir", required=True, help="Directory for summary outputs")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    children_root = Path(args.children_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    reports = load_reports(children_root)
    summary = build_summary(reports)
    summary_md = render_markdown(summary)

    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_md, encoding="utf-8")
    print(f"Wrote {output_dir / 'summary.json'}")
    print(f"Wrote {output_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
