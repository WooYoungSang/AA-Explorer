---
name: s2-api-layer
description: "Execute UOW-002 for the Base AA Explorer API layer: response schemas, query layer, FastAPI routers, errors, and API performance checks"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"s2", "api layer", "endpoints"

## Goal
Expose the indexed AA data through FastAPI endpoints that match the documented FR contracts and stay under the API performance target.

## Main workstream
1. Define Pydantic response models that match the API contract.
2. Build the database query layer for userops, stats, paymasters, and smart accounts.
3. Connect the routers to real database reads with pagination and not-found handling.
4. Add error handling consistent with the contract.
5. Add or extend endpoint, schema, query, and performance tests.

## Verification
- `cd backend && pytest tests/test_api.py tests/test_schemas.py tests/test_queries.py tests/test_api_perf.py -q`

## Guardrails
- Treat `docs/FR` as the API SSOT.
- Keep changes aligned with the dashboard's expected response shapes.
