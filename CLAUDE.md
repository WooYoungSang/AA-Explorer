# CLAUDE.md — Base AA Explorer

> **Micro-Bet based. Structured reporting is required at every phase transition.**
> Claude Code Native Harness — follow the official format (`.claude/skills/`, `.claude/agents/`)

## Project Context
- **Project ID**: `grant-base-aa-explorer`
- **Size / Appetite**: Small (1 Sprint)
- **Tech Stack**: Python (FastAPI), TypeScript (Next.js 14), SQLite (MVP)
- **Language**: Python + TypeScript

---

## Build / Test / Lint

```bash
# Build
cd backend && pip install -e ".[dev]" && cd ../frontend && npm run build

# Test
cd backend && pytest && cd ../frontend && npm test

# Lint
cd backend && ruff check . && cd ../frontend && npx eslint .
```

## Constraints

### No-Touch Files
```json
["node_modules/", ".env", "*.key"]
```

### No-Gos (strictly out of scope for this bet)
- transaction execution or signing
- private key management
- multichain support (Base only)
- historical backfill (forward-only)
- direct bundler/mempool integration
- user authentication/login
- EntryPoint v0.6 compatibility

### Acceptance Criteria
- Confirm real-time UserOp collection within 5 minutes
- Dashboard load time < 2 seconds

### Kill Condition
> Base EntryPoint ABI becomes inaccessible, or the WSS connection keeps failing for more than 1 hour.

---

## Micro-Bet Execution Rules

### Phase-Based Execution
```
[Phase 0: Preflight] → [Phase 1: Shape] → [Phase 2: Build] → [Phase 3: Ship] → [Phase 4: Reflect]
```

#### Phase 0: Preflight (required before entering Shape)
1. Confirm that PITCH, BET, UOW, FR, NFR, and ADR documents exist
2. Verify Lock-in 4/4 (Problem ✓, Appetite ✓, No-Go ✓, Acceptance ✓)
3. Check the kill condition — stop immediately if triggered
4. Run bootstrap → confirm build/test are green
5. Record a Phase 0 entry in `BET-LOG.md`

- **Appetite is sprint-sized**: Small (1 Sprint)
- **Adjust scope instead of extending appetite**
- **At 50%**: review Hill Position → alert if Position ≤ 4
- **At 75%**: force a Ship-or-Cut decision
- **No carry-over**: stop automatically when appetite is exhausted

### Required Order: Spec → Contract → Test → Code
1. confirm or update the spec
2. confirm or update the contract
3. add or update a failing test
4. make the smallest safe code diff
5. run targeted verification → then broader verification

### SSOT Priority
1. Pitch → 2. Bet → 3. UoW → 4. ADR/FR/NFR → 5. existing patterns → 6. tests → 7. implementation details

---

## Claude Code Native Harness Layout

- `CLAUDE.md` = **constitution** (this file)
- `.claude/skills/` = **procedures** (repeatable workflows)
  - `bootstrap` — initialize the project, install dependencies, and verify
  - `build-verify` — integrated build/test/lint verification
  - `bet-kickoff` — automate Preflight + Shape
  - `build-report` — build progress/completion report
  - `pattern-extract` — extract patterns during Reflect
  - `grant-submit` — submission prep and release procedure
- `.claude/agents/` = **role separation**
  - `spec-auditor` — spec/contract gap review (read-only)
  - `small-diff-implementer` — minimal-diff implementation (write)
  - `work-reporter` — professional work reporting (read-only)
- hooks / settings = **enforcement mechanisms** (deterministic only)

---

## Absolute Rules

```
❌ Implement No-Go items        ❌ Modify no_touch files
❌ Start implementation without AC
❌ Declare completion without verification
❌ Break the baseline           ❌ Extend appetite
❌ Ignore the kill condition    ❌ Add features outside the Pitch
❌ Carry work over              ❌ Skip phase reports
```
