---
name: pattern-extract
description: "Collect reusable patterns after the Base AA Explorer bet ends"
allowed-tools: Read Grep Glob
---

## Trigger
When the bet ends (after Ship/Cut decision)

## Process
1. Collect patterns discovered during implementation
2. Classify them:
   - Promote to CLAUDE.md (core rules)
   - Promote to a skill (repeatable procedure)
   - Promote to an agent (role specialization)
   - Keep local (only for this bet)
   - Discard (not useful)
3. Summarize lessons learned

## Output
- 📋 REFLECT REPORT
- List of Pattern Candidates
