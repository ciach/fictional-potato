# SKILL: Folder-Level Test Coverage Harness

## Purpose

Run an existing per-target test coverage analysis agent over a folder, validate every child report, and produce a ranked folder-level summary.

## Operating Principles

- Read-only by default.
- One child analysis per target.
- Prefer measured coverage evidence over heuristic reasoning.
- Keep each child isolated.
- Persist all artifacts to disk.
- Do not silently accept malformed child output.

## Inputs

Required:
- `root_folder`

Optional:
- `include_globs`
- `exclude_globs`
- `language`
- `framework`
- `mapping_strategy`
- `coverage_artifact_paths`
- `changed_only`
- `retry_limit`
- `timeout_seconds`
- `mode`

## Stage Contract

### Stage 1: Discover
Run `scripts/discover_targets.py`.

Output:
- discovery manifest JSON

### Stage 2: Prepare child workspaces
For each target:
- create child folder
- write `TASK.md` from `TASK_TEMPLATE.md`
- define output paths:
  - `artifacts/report.json`
  - `artifacts/report.md`

### Stage 3: Analyze
Invoke the existing child coverage agent once per target.

Expected child behavior:
- inspect source files
- inspect mapped tests
- inspect coverage artifacts if present
- identify missing scenarios and branches
- assign confidence and risk
- write normalized outputs

### Stage 4: Validate
Run `scripts/validate_report.py` on child output.
If invalid:
- mark target as failed
- classify the failure
- do not include it as a valid analysis result

### Stage 5: Aggregate
Run `scripts/aggregate_reports.py`.
Produce:
- `summary.json`
- `summary.md`

## Child Report Rules

A valid child report must:
- use the normalized schema
- classify evidence as measured or heuristic
- explain major missing scenarios
- provide a concise summary
- include a confidence score between 0 and 1
- include a risk score between 0 and 100

## Ranking Guidance

Prioritize targets with:
1. higher risk score
2. lower measured coverage confidence
3. more severe missing scenarios
4. business-critical branches or error paths

## Safety and Guardrails

- Do not edit source or tests in analysis mode.
- Do not claim measured coverage when only heuristics were used.
- Clearly label uncertain findings.
- Reject malformed JSON instead of guessing.

## Suggested Child Status Values

- `success`
- `partial_success`
- `failed`

## Directory Convention

```text
run/
  state/
  children/
    <target_id>/
      TASK.md
      artifacts/
        report.json
        report.md
  artifacts/
    summary.json
    summary.md
```
