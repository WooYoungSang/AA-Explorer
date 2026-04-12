---
name: build-verify
description: "Run integrated build + test + lint verification for the full AA Explorer project"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"verify", "check", "test", "build", "validation"

## Process
1. Run backend lint + test
2. Run frontend lint + build + test
3. Check `/health` if possible
4. Review Acceptance/NFR criteria

## Commands
- `cd backend && ruff check . && pytest -q`
- `cd frontend && npx eslint . --quiet && npm run build && npm test -- --watchAll=false`
