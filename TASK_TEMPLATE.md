# Child Coverage Analysis Task

## Target
- Target ID: {{target_id}}

## Inputs
### Source files
{{source_files}}

### Test files
{{test_files}}

### Coverage evidence
{{coverage_evidence}}

## Goal

Analyze whether the current tests cover the important scenarios for this target.

## Required output files

- `artifacts/report.json`
- `artifacts/report.md`

## Output requirements

### report.json
Must follow the normalized schema and include:
- target id
- status
- source files
- test files
- coverage evidence
- missing scenarios
- untested branches
- edge cases
- recommended tests
- confidence
- risk score
- summary

### report.md
Must explain:
- what was analyzed
- what evidence was available
- the biggest likely gaps
- whether the findings are measured or heuristic
- the most important next tests to add

## Important rules

- Prefer measured coverage evidence when available.
- If coverage artifacts are missing, label findings as heuristic.
- Be specific about missing conditions, branches, error paths, and edge cases.
- Do not modify any repository files.
