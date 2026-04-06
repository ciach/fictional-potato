# Requirements: VS Code Folder-Level Test Coverage Harness

## 1. Objective

Build a VS Code-compatible harness that runs an existing per-file coverage analysis agent across a folder or repository section and produces:

- per-target missing-coverage reports
- a folder-level summary
- resumable state and stable artifacts

## 2. Problem Statement

The current coverage agent must be triggered manually for each file. This does not scale, makes results inconsistent, and prevents folder-level prioritization. The harness should orchestrate repeated child analysis runs, validate outputs, and aggregate the results into one reliable review.

## 3. Product Scope

### In scope

- folder traversal
- include and exclude glob support
- source-to-test mapping
- optional coverage artifact input
- one child analysis per target
- normalized report schema
- validation and aggregation
- resumable execution state

### Out of scope for v1

- generating or editing tests automatically
- committing code changes
- deep whole-program dataflow analysis
- perfect mapping for every framework without adapters

## 4. Users

- QA / automation engineers
- developers working in VS Code
- reviewers who want a ranked coverage-gap summary

## 5. User Stories

- As a developer, I want to run coverage-gap analysis on a folder so I do not need to trigger the agent file by file.
- As a reviewer, I want a normalized report per target so outputs are comparable.
- As a team lead, I want a folder summary that ranks the most important missing scenarios first.
- As an engineer, I want interrupted runs to resume without redoing successful work.

## 6. Functional Requirements

### FR-1 Discovery
The harness shall accept a root folder and discover candidate source files and test files based on language/framework-specific rules and glob filters.

### FR-2 Mapping
The harness shall map source files to relevant test files using configurable strategies:
- by file name
- by colocated conventions
- by import references
- hybrid fallback

### FR-3 Task Packet Creation
For each discovered target, the harness shall create a child task packet containing:
- target id
- source file list
- mapped test file list
- optional coverage artifact references
- expected output locations
- analysis instructions

### FR-4 Child Invocation
The harness shall invoke the existing coverage agent once per target.

### FR-5 Normalized Output
Each child run shall write:
- `artifacts/report.json`
- `artifacts/report.md`

### FR-6 Validation
The harness shall validate each `report.json` against a required schema before accepting it into the aggregate result set.

### FR-7 Aggregation
The harness shall produce folder-level outputs:
- `summary.json`
- `summary.md`
- optional `top_gaps.md`

### FR-8 Resume
The harness shall persist state and skip already completed targets unless forced to rerun.

### FR-9 Changed-only Mode
The harness should support analyzing only changed files derived from git diff or a supplied file list.

### FR-10 Read-only Default
The harness shall be read-only by default and must not modify source code or test code.

## 7. Non-Functional Requirements

### NFR-1 Inspectability
All child and aggregate artifacts shall be stored on disk in stable paths.

### NFR-2 Deterministic Adapters
Discovery, validation, and aggregation logic shall be deterministic and scriptable.

### NFR-3 Bounded Execution
The harness should support per-target timeout, retry limit, and optional concurrency control.

### NFR-4 Minimal Context Bleed
Each child analysis should receive isolated per-target context rather than a single giant shared prompt.

### NFR-5 Explainability
Outputs shall explain whether a gap was inferred from measured coverage or from static/heuristic analysis.

## 8. Inputs

- root folder
- include globs
- exclude globs
- language
- framework
- mapping strategy
- optional coverage artifact paths
- timeout
- retry limit
- mode: sequential or parallel
- changed-only switch

## 9. Per-target Output Schema

Required top-level fields:

- `target_id`
- `status`
- `source_files`
- `test_files`
- `coverage_evidence`
- `missing_scenarios`
- `untested_branches`
- `edge_cases`
- `recommended_tests`
- `confidence`
- `risk_score`
- `summary`

## 10. Failure Taxonomy

The harness shall classify failures using explicit categories:

- `discovery_error`
- `mapping_error`
- `missing_artifact`
- `invalid_report_schema`
- `coverage_parser_error`
- `agent_timeout`
- `tool_error`
- `low_confidence_analysis`
- `partial_success`

## 11. Acceptance Criteria

The feature is accepted when:

1. Running the harness on a folder creates one child work item per discovered target.
2. Every successful child emits a valid `report.json`.
3. Invalid reports are rejected and surfaced in the summary.
4. Aggregation produces a ranked summary across all valid child reports.
5. Restarting the harness can resume without repeating successful targets.
6. The harness can operate without modifying repository files.

## 12. Recommended v1 Prioritization

1. discovery
2. mapping
3. per-target invocation
4. validation
5. aggregation
6. resume support
7. changed-only mode
