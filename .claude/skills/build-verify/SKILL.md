---
name: build-verify
description: "Run integrated build + test + lint verification for the full AA Explorer project"
allowed-tools: Read Grep Glob Bash
---

# Skill: Build & Verify — AA Explorer

> **Trigger**: "verify", "check", "test", "build", "validation"
> **Scope**: integrated build + test + lint verification

## Quick Verify
```bash
cd backend && poetry run ruff check . && poetry run pytest -q
cd ../frontend && npx eslint . --quiet && npm run build && npm test -- --watchAll=false
```

## Full Verify
```bash
cd backend && poetry run ruff check . --fix
poetry run pytest -q --tb=short
cd ../frontend
npx eslint . --quiet
npm run build 2>&1 | tail -5
npm test -- --watchAll=false --silent
curl -s http://localhost:8000/health | python -m json.tool
```
