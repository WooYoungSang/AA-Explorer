---
name: bet-kickoff
description: "Automate Preflight + Shape at the start of a Base AA Explorer bet"
allowed-tools: Read Grep Glob Bash
---

## Trigger
Auto-run when the bet starts

## Process
1. Scan the codebase structure (Python + TypeScript)
2. Confirm the build/test baseline: `cd backend && pip install -e ".[dev]" && cd ../frontend && npm run build`
3. Confirm the no_touch file list: ["node_modules/", ".env", "*.key"]
4. Verify whether Acceptance items are testable
5. Break the scope into S1-Data, S2-API, and S3-UI
6. Generate 📋 PREFLIGHT REPORT + SHAPE REPORT

## Output
- Preflight Report (connectivity, Lock-in, baseline)
- Shape Report (scope breakdown, impact analysis, implementation plan)
