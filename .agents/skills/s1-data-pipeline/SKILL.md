---
name: s1-data-pipeline
description: "Execute UOW-001 for the Base AA Explorer data pipeline: schema, EntryPoint v0.7 indexing, decoding, classification, and aggregation"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"s1", "data pipeline", "indexer", "decoder"

## Goal
Deliver the Base EntryPoint v0.7 ingestion pipeline through SQLite persistence and daily stats aggregation.

## Main workstream
1. Define or verify the SQLite schema for `user_ops` and `daily_stats` plus supporting indexes.
2. Implement the minimal ABI/event definitions required for EntryPoint v0.7.
3. Build the WSS indexer with bounded reconnect logic and an HTTP fallback path.
4. Decode `UserOperationEvent` logs into normalized records.
5. Classify known paymasters and smart-account factories.
6. Aggregate daily stats from stored UserOps.
7. Lock behavior with focused backend tests before expanding scope.

## Verification
- `cd backend && pytest tests/test_indexer.py tests/test_decoder.py tests/test_classifier.py tests/test_aggregator.py tests/test_schema.py -q`

## Guardrails
- Respect the kill condition if EntryPoint access or both WSS/HTTP ingestion paths fail persistently.
- Stay within Base mainnet + EntryPoint v0.7 only.
