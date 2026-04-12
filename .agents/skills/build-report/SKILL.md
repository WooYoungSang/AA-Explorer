---
name: build-report
description: "Generate a Base AA Explorer Build phase progress/completion report"
allowed-tools: Read Grep Glob Bash
---

## Trigger
At 50% of Build, or when Build completes

## Input
- Scope list and Hill Position
- List of changed files
- Verification results: build(`cd backend && pip install -e ".[dev]" && cd ../frontend && npm run build`), test(`cd backend && pytest && cd ../frontend && npm test`), lint(`cd backend && ruff check . && cd ../frontend && npx eslint .`)

## Process
1. Collect the current Hill Chart state
2. Classify completed and in-progress work
3. Run the verification gates
4. Decide whether Acceptance is met
5. Alert when Position ≤ 4
6. Recommend Ship-or-Cut when complete

## Output
📋 BUILD PROGRESS/COMPLETION REPORT → append to `BET-LOG.md`
