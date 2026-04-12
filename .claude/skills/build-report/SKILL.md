---
name: build-report
description: "Generate a Base AA Explorer Build phase progress/completion report"
allowed-tools: Read Grep Glob Bash
---

## Trigger
At the 50% point of the Build phase, or when Build completes

## Process
1. Collect Hill Chart status (each scope position 0~10)
2. Classify completed and in-progress work
3. Run the verification gates:
   - Build: `cd backend && poetry install --with dev && cd ../frontend && npm run build`
   - Test: `cd backend && poetry run pytest && cd ../frontend && npm test`
   - Lint: `cd backend && poetry run ruff check . && cd ../frontend && npx eslint .`
4. Decide whether Acceptance is met
5. Check for scope alerts when Position ≤ 4

## Output
- 📋 BUILD PROGRESS REPORT (50%) or 📋 BUILD COMPLETION REPORT
- Ship-or-Cut recommendation when complete
