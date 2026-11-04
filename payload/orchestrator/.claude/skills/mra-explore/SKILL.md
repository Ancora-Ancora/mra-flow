---
name: mra-explore
description: Use when the user wants to think through an idea, investigate a problem, or clarify requirements in the low-and-slow orchestrator without committing to a decision yet - optional step before /mra-grill in the mra-flow workflow.
disable-model-invocation: true
argument-hint: [idea, problem or change-id]
---

# mra-explore — think before grilling

Open-ended exploration of `$ARGUMENTS`, grounded in this orchestrator's domain docs.

## Steps

1. Read `GLOSSARY.md`, the ADRs in `docs/adr/` related to the topic, and `openspec list --specs`. Skip silently what does not exist. Use glossary terms in the discussion.
2. Call the Skill tool with `openspec-explore` and follow it. When investigating code, look in `low-and-slow-cooking-lab-be/` and `low-and-slow-cooking-lab-fe/` (or the change's `.worktrees/<change-id>/` if it is being built).
3. When the exploration converges, end with what was learned and the next command:
   - decisions still need to be made → `/mra-grill <topic>`
   - decisions are made and recorded → `/mra-propose <change-id>`
   - an existing change needs revising → `/mra-update <change-id>`

## Rules

- Exploration writes no code, no ADRs, no beads issues. Decisions are recorded in `/mra-grill`.
