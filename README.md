# VS Code Test Coverage Harness

This scaffold wraps an existing per-file test coverage agent with a folder-level harness.

## What is included

- `REQUIREMENTS.md` - product and engineering requirements
- `SKILL.md` - harness behavior and runtime contract
- `TASK_TEMPLATE.md` - per-child task packet template
- `schemas/report.schema.json` - normalized child report schema
- `scripts/discover_targets.py` - folder discovery and source/test mapping
- `scripts/validate_report.py` - report validation
- `scripts/aggregate_reports.py` - repo/folder summary aggregation
- `examples/config.sample.json` - sample harness configuration

## Intended workflow

1. Run `discover_targets.py` on a folder.
2. For each discovered target, create a child workspace and fill `TASK.md` from `TASK_TEMPLATE.md`.
3. Invoke your existing coverage agent once per target.
4. Store the child output as `artifacts/report.json` and `artifacts/report.md`.
5. Run `validate_report.py` on each report or on the whole children folder.
6. Run `aggregate_reports.py` to build `summary.json` and `summary.md`.

## Example

```bash
python scripts/discover_targets.py   --root /path/to/repo   --config examples/config.sample.json   --output /tmp/discovery.json

python scripts/validate_report.py   --report /path/to/child/artifacts/report.json

python scripts/aggregate_reports.py   --children-root /path/to/run/children   --output-dir /path/to/run/artifacts
```

## Notes

- The scripts are read-only.
- Discovery is heuristic by default.
- Real coverage artifacts such as `lcov.info` should be preferred when available.
- Reports distinguish between measured gaps and heuristic gaps when the child agent follows the schema.
