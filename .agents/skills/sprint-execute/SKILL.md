---
name: sprint-execute
description: "Run the AA Explorer SCTCV execution loop for each task: spec, contract, test, code, verify"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"execute", "build", "실행", "구현", "다음 태스크"

## Core contract
Always follow `Spec -> Contract -> Test -> Code -> Verify` for each task.

## Procedure
1. Pick the next unstarted task from `BET-LOG.md` or the active UOW.
2. Re-read the governing FR/NFR/ADR/UOW material for that task.
3. Confirm the interface contract before writing code.
4. Write or update a failing test that proves the task is incomplete.
5. Implement the smallest safe diff that makes the test pass.
6. Run the relevant verification commands.
7. Update task status and hill position in `BET-LOG.md`.

## Rules
- Prefer small diffs and bounded file counts.
- Stop and scope-hammer if requirements become ambiguous, blockers compound, or No-Go boundaries are threatened.
- Do not claim completion without green verification evidence.
