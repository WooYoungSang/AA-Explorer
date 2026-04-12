---
name: build-verify
description: "Run quick or full integrated verification for the AA Explorer backend, frontend, API health, and core acceptance checks"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"verify", "check", "test", "build", "validation", "검증"

## Quick verify
- `cd backend && poetry run ruff check . && poetry run pytest -q`
- `cd frontend && npx eslint . --quiet && npm run build && npm test -- --watchAll=false`

## Full verify
1. Backend lint and tests
2. Frontend lint, build, and tests
3. `/health` check when the backend is running
4. Acceptance review when the relevant services are live:
   - data freshness within 5 minutes
   - dashboard performance target (LCP < 2s)
   - API responses remain within the expected performance envelope

## Reporting format
Summarize backend, frontend, API, and acceptance status separately, then end with a single verdict.
