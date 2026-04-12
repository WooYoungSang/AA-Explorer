# Spec Index — grant-base-aa-explorer

> WARVIS SSOT: Obsidian `02-Projects/grant-base-aa-explorer/`
> Repo status: bootstrap baseline scaffold + harness mirror

## Canonical SSOT location

The authoritative pitch, bet, ADR, FR, NFR, and UOW documents currently live in the WARVIS Obsidian vault:

- `02-Projects/grant-base-aa-explorer/PITCH-Base-AA-Explorer.md`
- `01-GTD/Bets/BET-SMALL-GRANT-aa-explorer.md`
- `02-Projects/grant-base-aa-explorer/ADR/ADR-AA-Explorer-001.md`
- `02-Projects/grant-base-aa-explorer/FR/FR-AA-Explorer-001.md`
- `02-Projects/grant-base-aa-explorer/FR/FR-AA-Explorer-002.md`
- `02-Projects/grant-base-aa-explorer/NFR/NFR-AA-Explorer-001.md`
- `02-Projects/grant-base-aa-explorer/UOW/`
- `02-Projects/grant-base-aa-explorer/BOOTSTRAP.md`

## Accepted lock-in facts

- Problem: Base AA ecosystem visibility is missing for UserOps, paymasters, and smart accounts.
- Appetite: Small, one sprint.
- No-Go: no signing, key management, multichain, historical backfill, bundler integration, auth, or EntryPoint v0.6.
- Acceptance: reflect UserOps within 5 minutes and keep dashboard load under 2 seconds.

## Architecture direction

- MVP stack: Python (FastAPI) + TypeScript (Next.js 14) + SQLite
- Data flow: Base EntryPoint v0.7 → indexer → decoder → classifier → aggregates → API → dashboard
- Reliability: reconnect-first with HTTP fallback when WSS degrades

## Local repo mirror

This repository now contains the runnable bootstrap baseline used for S0 preflight:

- `backend/` — FastAPI baseline scaffold
- `frontend/` — Next.js baseline scaffold
- `BOOTSTRAP.md` — local setup and verification guide
- `.agents/`, `.claude/`, `.codex/` — agent harness artifacts
