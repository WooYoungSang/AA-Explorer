---
name: grant-readme
description: "Generate or improve a grant-reviewer-optimized README.md for Base AA Explorer"
allowed-tools: Read Grep Glob Bash
---

## Trigger
"readme", "grant readme", "README", "README.md", "grant README"

## Purpose
Write the GitHub `README.md` for Base AA Explorer so that Base Builder Grants reviewers can understand the project quickly and confidently.

## When to use
- When the user asks to create or improve the README
- When a grant submission README is needed
- When Base / ERC-4337 / Account Abstraction context must be strongly reflected in the README

## Process
1. Check whether the current repository already has a `README.md`
2. Read the following sources first when they exist and are relevant
   - `references/readme-gen-prompt.md`
   - `AGENTS.md`
   - `CLAUDE.md`
   - actual implementation, commands, and endpoints under `docs/`, `backend/`, and `frontend/`
3. Write a grant-oriented README without conflicting with confirmed implementation facts
4. Use this structure by default
   - Header + badges
   - one-line description
   - screenshot placeholder
   - why this matters
   - features
   - architecture
   - quick start
   - API reference
   - dashboard/pages
   - configuration
   - development
   - deployment
   - roadmap
   - contributing
   - license
   - acknowledgments
5. Keep the writing short and technical
6. Prefer the repository's real commands and paths, and do not guess when something is unverified

## Output rules
- English only
- Include only copy-paste-ready commands
- Make `Built for Base`, `ERC-4337`, and `Account Abstraction` explicit
- Never include real keys or secrets; use `.env.example`-style examples only
- If the user asks for a direct edit, update `README.md`; otherwise provide a complete draft

## Quality checklist
- Is the project value obvious within the first 30–60 seconds?
- Is the Base AA problem/solution clear?
- Are architecture, endpoints, and performance targets included?
- Is Quick Start aligned with the actual repository state?
- Does the writing feel technically credible without hype?
