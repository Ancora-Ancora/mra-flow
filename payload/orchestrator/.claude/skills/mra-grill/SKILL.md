---
name: mra-grill
description: Use when starting a new feature or decision in the low-and-slow orchestrator, before any OpenSpec change exists - phase 1 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <topic or idea to grill>
---

# mra-grill — phase 1: grill and record decisions

Stress-test the idea in `$ARGUMENTS` and record its outcomes as domain docs, before any spec is written.

## Steps

1. Ground yourself first: read `GLOSSARY.md`, the ADRs in `docs/adr/`, and the capability list (`openspec list --specs`). Skip silently whatever does not exist yet.
2. Call the Skill tool with `mattpocock-skills:grilling`, then with `mattpocock-skills:domain-modeling`. Run the grilling session with both active: resolved terms go to `GLOSSARY.md`, ADR-worthy decisions go to `docs/adr/NNNN-slug.md`. Override grilling's rounds: ask **one question per message**, each with your recommended answer, and wait for the reply before the next.
3. Keep the FE↔BE boundary in view: for every decision, ask which repo (`fe`, `be`, both) it binds, and grill the contract between them when both are involved.
4. Keep a running list of **carried decisions**: answers that bind the change but are not ADR-worthy (an API contract, a tool or version choice, a naming detail). They have no file yet; the close summary carries them to `/mra-propose`.
5. Close the session with a short summary:
   - ADRs created or changed, glossary terms added (a purely technical change may add none: that is expected)
   - Carried decisions, one line each
   - Open points that still need an answer
   - A proposed kebab-case change id (e.g. `add-cook-session-log`)
   - The next command: `/mra-propose <change-id>`

## Rules

- Do not create an OpenSpec change or write code in this phase.
- Do not commit; list the changed files and let the user decide.
