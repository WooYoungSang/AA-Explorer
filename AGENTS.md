# AGENTS.md — Base AA Explorer

> **Autonomous Codex operating constitution. Micro-Bet phase based. Reporting required.**

## CONFIG
```yaml
project_id: "grant-base-aa-explorer"
project_type: "dev"
repo_root: "."

lang: "Python + TypeScript"
tech_stack: "Python (FastAPI) + TypeScript (Next.js 14) + SQLite (MVP)"
build_cmd: "cd backend && pip install -e '.[dev]' && cd ../frontend && npm run build"
test_cmd: "cd backend && pytest && cd ../frontend && npm test"
lint_cmd: "cd backend && ruff check . && cd ../frontend && npx eslint ."

no_touch: ["node_modules/", ".env", "*.key"]
max_new_files_per_task: 5
appetite: "1 Sprint (Small)"

bet_dir: "docs/bets"
log_file: "BET-LOG.md"
```

## Phase-Based Execution

```
[PHASE 0: Preflight] → [PHASE 1: Shape] → [PHASE 2: Build] → [PHASE 3: Ship] → [PHASE 4: Reflect]
```

### Execution Order
1. confirm the spec → 2. confirm the contract → 3. write a failing test → 4. make the smallest safe diff → 5. verify

### Checkpoints
- **50%**: review Hill Position → alert if Position ≤ 4
- **75%**: force a Ship-or-Cut decision
- **Appetite exhausted**: stop automatically, no rollover

---

## SSOT Priority
1. Pitch → 2. Bet → 3. UoW → 4. ADR/FR/NFR → 5. existing patterns → 6. tests → 7. implementation details

## Acceptance
- "Confirm real-time UserOp collection within 5 minutes"
- "Dashboard load time < 2 seconds"

## No-Gos
- transaction execution or signing
- private key management
- multichain support (Base only)
- historical backfill (forward-only)
- direct bundler/mempool integration
- user authentication/login
- EntryPoint v0.6 compatibility

## Kill Condition
> Base EntryPoint ABI becomes inaccessible, or the WSS connection keeps failing for more than 1 hour.

---

## Autonomous Decision Protocol

### Green Zone — Execute Autonomously
Choose an existing pattern that satisfies the AC, make minor build fixes, or add edge-case tests.

### Yellow Zone — Scope Hammer
Acceptance is ambiguous, no matching pattern exists, scope grows 3×, 3 failures occur, or 50% checkpoint position is ≤ 4.

### Red Zone — Hard Stop
Kill condition triggered, a No-Go becomes mandatory, `no_touch` must be violated, 50%+ gets deferred, or a security vulnerability appears.

---

## Codex Native Harness Layout

- `AGENTS.md` = **constitution** (this file)
- `.agents/skills/` = **procedures**
  - `bootstrap` — initialize the project, install dependencies, and verify
  - `build-verify` — integrated build/test/lint verification
  - `bet-kickoff` — Preflight + Shape
  - `build-report` — Build report
  - `pattern-extract` — Reflect pattern extraction
  - `grant-submit` — submission prep and release procedure
- `.codex/agents/` = **role separation**
  - `spec_guardian` — spec review (read-only)
  - `bet_implementer` — minimal-diff implementation (write)
  - `work_reporter` — work reporting (read-only)
- `.codex/config.toml` = **execution constraints**

---

## Absolute Rules

```
❌ Implement No-Go scope        ❌ Modify no_touch files
❌ Start without AC             ❌ Declare completion without verification
❌ Break the baseline           ❌ Extend appetite
❌ Ignore the kill condition    ❌ Add features outside the Pitch
❌ Carry work over              ❌ Skip phase reports
❌ Create a task without a UoW  ❌ Override harness rules
```
