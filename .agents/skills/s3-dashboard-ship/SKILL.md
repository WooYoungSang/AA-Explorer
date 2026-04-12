---
name: s3-dashboard-ship
description: "Execute UOW-003 for the Base AA Explorer dashboard, deployment readiness, and grant-facing ship preparation"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"s3", "dashboard", "ship"

## Goal
Build the Next.js dashboard, verify the key UX/performance targets, and prepare the project for deployment and grant-facing shipping.

## Main workstream
1. Implement layout/navigation and the main dashboard pages.
2. Wire SWR hooks to the AA Explorer API.
3. Add KPI cards, trend, paymaster, and smart-account charts.
4. Build the recent UserOps feed with pagination/refresh cues.
5. Add frontend tests for the major pages/components.
6. Verify a clean frontend build, deployment readiness, and dashboard performance.
7. Prepare screenshots, live URL placeholders, and ship evidence for grant submission.

## Verification
- `cd frontend && npm run build && npm test`
- Run Lighthouse or equivalent when the deployed or local app is available and confirm LCP stays below the target when possible.

## Handoff
If the dashboard is ship-ready, hand off to `grant-submit` for final submission packaging.
