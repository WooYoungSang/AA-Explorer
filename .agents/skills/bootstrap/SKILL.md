---
name: bootstrap
description: "Bootstrap the AA Explorer repo, run S0 preflight, and verify the environment is ready for Sprint work"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"bootstrap", "setup", "init", "environment setup", "preflight", "s0", "환경설정"

## Purpose
Initialize or re-verify the local AA Explorer workspace so Sprint work can start from a green baseline.

## Process
1. Confirm required docs and lock-in facts exist: Pitch, Bet, ADR, FR, NFR, UOWs, BOOTSTRAP, harness docs.
2. Re-check the 4 lock-in conditions and the kill condition before changing code.
3. Verify the toolchain: Python >= 3.11, Node >= 18, optional `uv`/`pnpm`.
4. Confirm or create the expected project structure for `backend/`, `frontend/`, `docs/bets/`, `.claude/`, and `.codex/`.
5. Install backend dependencies with the repo-standard command and verify imports.
6. Install frontend dependencies and confirm a clean production build.
7. Confirm the baseline skeleton tests and lint/build commands pass.
8. Confirm harness files are present so the repo is ready for Build phase work.
9. Record the preflight result in `BET-LOG.md` when this is part of a bet kickoff.

## Commands
- `python --version`
- `node --version`
- `cd backend && poetry env use python3.11 && poetry install --with dev && poetry run ruff check . && poetry run pytest -q`
- `cd frontend && npm install && npm run build && npm test -- --watchAll=false`

## Exit criteria
- Backend + frontend install cleanly
- Baseline verification is green
- Kill condition is not triggered
- Workspace is ready for Sprint / UOW execution
