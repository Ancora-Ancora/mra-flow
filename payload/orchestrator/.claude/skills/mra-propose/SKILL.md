---
name: mra-propose
description: Use when a grilled idea is ready to become an OpenSpec change in an mra-flow orchestrator - phase 2 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <change-id or short description>
---

# mra-propose — phase 2: OpenSpec change and artifacts

Create the OpenSpec change for `$ARGUMENTS` with all artifacts of the `mra-flow` schema (proposal, specs, design, tasks).

## Steps

1. **Grilling check.** Look for ADRs in `docs/adr/` and glossary terms in `GLOSSARY.md` that cover this topic. If none do, tell the user and ask: run `/mra-grill` first, or proceed anyway. Wait for the answer.
   Also check whether `$ARGUMENTS` matches a capability already in `openspec list --specs`. If so, recommend `/mra-drift <capability>` before proceeding and resolving any DRIFT-SPEC it finds first: the proposal must build on the code's real current behaviour, not a possibly stale spec. Proceed if the user declines.
2. Call the Skill tool with `openspec-propose`, passing the change id/description and the carried decisions from the `/mra-grill` close summary. Follow it up to its closing prompt; the schema instructions carry the project rules (ADR citations, `## Contract:` sections, `[<key>]` tasks with `Depends on:` / `Covers:`).
3. **Check the result:**
   - `openspec validate <change-id> --strict` passes.
   - For every repo the proposal Impact names together with one of its `depends_on` (`.mra-flow/bin/mra-repo list`), `design.md` has a filled `## Contract: <repo> -> <dependency>`.
   - Every task in `tasks.md` has a `[<key>]` tag naming a repo declared in `mra-flow.toml`.
   - Every spec scenario appears in at least one task's `Covers:` line.
   Fix any gap via the `openspec-update-change` skill (Skill tool) before going on.
4. If `design.md` lists **ADR candidates**, offer to record them now (Skill tool: `mattpocock-skills:domain-modeling`). If its open questions include external facts (a library's capability, an API's behaviour, a version difference), offer `/mra-research <question> --change <change-id>` and fold the answers in through `openspec-update-change`.
5. End with the change id and the next command: `/mra-track <change-id>`. This replaces the next step that `openspec-propose` suggests and that `openspec status` prints (`/opsx:apply`, `openspec instructions apply`): in mra-flow, tasks go to beads before any code.

## Rules

- Never write code or create beads issues in this phase.
- Do not commit; list the changed files and let the user decide.
