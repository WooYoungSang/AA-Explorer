---
name: bootstrap
description: "Initialize the AA Explorer project, install dependencies, and verify the setup"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"bootstrap", "setup", "init", "environment setup"

## Process
1. Check required tools: node/python/uv
2. Create the directory structure
3. Install backend dependencies (`uv pip install -e ".[dev]"`)
4. Install the frontend (`create-next-app@14`, `recharts`, `swr`, `clsx`)
5. Run skeleton tests
6. place the harness files

## Output
✅ Bootstrap Complete
