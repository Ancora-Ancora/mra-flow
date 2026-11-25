---
name: mra-explore
description: Use when the user wants to think through an idea, investigate a problem, or clarify requirements in an mra-flow orchestrator without committing to a decision yet - optional step before /mra-grill in the mra-flow workflow.
disable-model-invocation: true
argument-hint: [idea, problem or change-id]
---

# mra-explore — think before grilling

Open-ended exploration of `$ARGUMENTS`, grounded in this orchestrator's domain docs.

## Steps

1. Read the glossaries and the ADRs related to the topic, per the domain-docs layout in use (`.mra-flow/docs/agents/domain.md`), and `openspec list --specs`. Skip silently what does not exist. Use glossary terms in the discussion.
2. Call the Skill tool with `openspec-explore` and follow it. When investigating code, look in the code repos listed by `.mra-flow/bin/mra-repo list` (or the change's `.worktrees/<change-id>/<key>` if it is being built); each repo's `description` in `mra-flow.toml` says what it owns.
3. When the exploration converges, end with what was learned and the next command:
   - decisions still need to be made → `/mra-grill <topic>`
   - decisions are made and recorded → `/mra-propose <change-id>`
   - an existing change needs revising → `/mra-update <change-id>`

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Exploration writes no code, no ADRs, no beads issues. Decisions are recorded in `/mra-grill`.
