# Spec Index — grant-base-aa-explorer

> WARVIS SSOT: Obsidian `02-Projects/grant-base-aa-explorer/`
> Indexed: Neo4j + Qdrant + MinIO via `devos_index_project`

## ADR (Architecture Decision Records)
| ID | Title | Path |
|----|-------|------|
| ADR-AA-Explorer-001 | AA Explorer tech stack and architecture decision | ADR/ADR-AA-Explorer-001.md |

**Decision**: Python (FastAPI) + TypeScript (Next.js 14) + PostgreSQL/TimescaleDB. WSS-based EntryPoint indexer.

## FR (Functional Requirements)
| ID | Title | Path |
|----|-------|------|
| FR-AA-Explorer-001 | Core data collection pipeline | FR/FR-AA-Explorer-001.md |
| FR-AA-Explorer-002 | Dashboard and API | FR/FR-AA-Explorer-002.md |

## NFR (Non-Functional Requirements)
| ID | Title | Quality Attribute | Thresholds |
|----|-------|-------------------|------------|
| NFR-AA-Explorer-001 | Response time and performance SLO | performance | data_freshness ≤ 5 minutes / dashboard_lcp ≤ 2 seconds |

## UOW (Units of Work)
| ID | Title | Risk | Status |
|----|-------|------|--------|
| UOW-001 | S1-Data: Build the EntryPoint WSS-based UserOp collection pipeline | R1 | initialized |
| UOW-002 | S2-API: Build FastAPI endpoints | R1 | initialized |
| UOW-003 | S3-UI: Build the Next.js dashboard | R1 | initialized |

## Acceptance Criteria
- Confirm real-time UserOp collection within 5 minutes
- Dashboard load time < 2 seconds

## Kill Condition
> Base EntryPoint ABI becomes inaccessible, or the WSS connection keeps failing.

## WARVIS Context Query
```
devos_retrieve_context(project_id="grant-base-aa-explorer", query="UoW list ADR decisions")
```
