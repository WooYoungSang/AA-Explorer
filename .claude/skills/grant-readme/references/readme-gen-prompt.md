# README generation prompt reference

Source note: `obsidian://open?vault=WARVIS&file=02-Projects%2Fgrant-base-aa-explorer%2FSkills%2Freadme-gen-prompt`

Use this reference when generating or revising the repository `README.md`.

## Core intent
- Produce a grant-reviewer-optimized README for **Base AA Explorer**
- Help a reviewer understand the project in under 60 seconds
- Keep the tone professional and technical, not hype-heavy

## Project framing
- First dedicated ERC-4337 analytics dashboard for Base
- Focus on real-time visibility into UserOperations, Paymasters, and Smart Account adoption
- Target audience: Base Builder Grants reviewers

## Required emphasis
- Base
- ERC-4337
- Account Abstraction
- real-time analytics
- technical credibility

## Preferred README structure
1. Header with badges and one-line description
2. Screenshot placeholder
3. Why this matters
4. Features
5. Architecture
6. Quick start
7. API reference
8. Dashboard pages
9. Configuration
10. Development
11. Deployment
12. Roadmap
13. Contributing
14. License
15. Acknowledgments

## Style rules
- English only
- Concise
- Copy-paste ready commands
- Include `.env.example` style configuration examples only
- Mention Base throughout where relevant
- Link to Base docs, ERC-4337 spec, and Alchemy when useful

## Reference facts from the source prompt
- One-liner: first dedicated ERC-4337 analytics dashboard for Base
- Problem: Base AA has no dedicated analytics tooling
- Solution flow: WSS indexing → UserOp decode → Paymaster/Smart Account classification → stats aggregation → REST API → Next.js dashboard
- Suggested stack:
  - Backend: Python 3.11+, FastAPI, web3.py, aiosqlite
  - Frontend: Next.js 14, TypeScript, Recharts, SWR, Tailwind CSS
  - Database: SQLite MVP → TimescaleDB later
- Suggested SLOs:
  - data freshness ≤ 5 minutes
  - API response < 1 second
  - dashboard LCP < 2 seconds

## Important usage note
Treat the prompt as a target shape, not absolute truth. Prefer the repository's current implementation, commands, and architecture when they differ.
