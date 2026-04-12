# AA Explorer — Bootstrap Guide

This repository now includes a runnable S0 baseline scaffold for the Base AA Explorer MVP.

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm 10+
- Poetry 2.2+

## Backend verification

```bash
cd backend
poetry env use python3.11
poetry install --with dev
poetry run ruff check .
poetry run pytest -q
```

## Frontend verification

```bash
cd frontend
npm install
npm run build
npm run lint
npm test -- --watchAll=false
```

## Scope

- Base mainnet only
- EntryPoint v0.7 only
- Read-only analytics only
- SQLite for the MVP baseline scaffold
