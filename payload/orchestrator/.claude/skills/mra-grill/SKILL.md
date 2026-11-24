---
name: mra-grill
description: Use when starting a new feature or decision in an mra-flow orchestrator, before any OpenSpec change exists - phase 1 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <topic or idea to grill>
---

# mra-grill — phase 1: grill and record decisions

Stress-test the idea in `$ARGUMENTS` and record its outcomes as domain docs, before any spec is written.

## Steps

1. Ground yourself first: read the glossaries and ADRs of the domain-docs layout in use (`.mra-flow/docs/agents/domain.md`: `GLOSSARY.md` + `docs/adr/`, or the contexts listed in `docs/GLOSSARY-MAP.md`), the capability list (`openspec list --specs`), the registered repos (`.mra-flow/bin/mra-repo list`), and the roadmaps (`docs/roadmap/*.md`). Skip silently whatever does not exist yet. If no repos are registered, recommend `.mra-flow/bin/mra-repo add <key> <remote> --description "..."` before grilling: step 5 needs them to ask which repos a decision binds. Proceed if the user declines.
2. **Roadmap.** Rules: `.mra-flow/docs/agents/roadmap.md`.
   - If `$ARGUMENTS` is a slice of a roadmap (its change id, or its goal), grill that slice: start from its goal, its open points and the initiative's Decisions and constraints, and keep its change id. A *UI preview* cell naming a `docs/prototypes/<slug>.md` note means the prototype is done: in step 7, reuse its verdict for the screens it covers (`preview: prototype docs/prototypes/<slug>.md`) instead of recommending a new one.
   - If no roadmap covers it and the topic looks too large for one change (several capabilities, several screens, or more than one contract change), recommend `/mra-roadmap <topic>` before grilling. Proceed if the user declines.
3. **Spec drift check.** If `$ARGUMENTS` extends or touches a capability already in that list, recommend `/mra-drift <capability>` before grilling: decisions should account for the code's real current behaviour, not a possibly stale spec. Proceed if the user declines.
4. Call the Skill tool with `mattpocock-skills:grilling`, then with `mattpocock-skills:domain-modeling`. Run the grilling session with both active: resolved terms go to `GLOSSARY.md`, ADR-worthy decisions go to `docs/adr/NNNN-slug.md` (multi-context: those of the narrowest context the term or decision binds, `docs/<repo-key>/` or the root; see `.mra-flow/docs/agents/domain.md`). Override grilling's rounds: ask **one question per message**, each with your recommended answer, and wait for the reply before the next.
5. Keep the repo boundaries in view (`.mra-flow/bin/mra-repo list`, and each repo's `description` in `mra-flow.toml`): for every decision, ask which code repos it binds, and when it binds a repo and one of its `depends_on`, grill the contract between them.
6. **Stuck questions.** Proceed without either if the user declines.
   - A decision that depends on an external fact nobody here can confirm (a library's capability, an API's limits, a standard, a version difference) → recommend `/mra-research <question>`; grill other questions while it runs, then resume this one from its note.
   - A question about a state model or logic, or about what a UI should look like, still open after two rounds → recommend `/mra-prototype <question>`: a throwaway prototype settles it faster than more talk. Resume the grilling from its verdict.
7. **UI preview.** Before closing, check every screen the decisions add or change against `.mra-flow/docs/agents/ui-preview.md`. A screen that needs a prototype → recommend `/mra-prototype <question>`, with the question already written (the new screens and patterns it covers); resume from the note in `docs/prototypes/`. A screen that needs a sketch → show it in a question with a `preview` and ask the user to accept or correct it. Proceed if the user declines; record the outcome per screen as that file says.
8. Keep a running list of **carried decisions**: answers that bind the change but are not ADR-worthy (an API contract, a tool or version choice, a naming detail). They have no file yet; the close summary carries them to `/mra-propose`.
9. Close the session with a short summary:
   - ADRs created or changed, glossary terms added (a purely technical change may add none: that is expected)
   - Carried decisions, one line each
   - UI previews, one `preview:` line per new or changed screen (`.mra-flow/docs/agents/ui-preview.md`); prototype notes in `docs/prototypes/`; research notes in `docs/research/`
   - Open points that still need an answer
   - Roadmap impact, for a slice: one line per finding that changes the roadmap (slice larger than estimated, to split, a new slice, a dependency, a slice no longer needed), and then `/mra-roadmap <initiative>` among the next commands; nothing when the slice holds
   - A proposed kebab-case change id (e.g. `add-cook-session-log`); for a slice, its change id from the roadmap. If no roadmap covers the topic and the grill showed it is too large for one change (the step 2 signals, found only now), propose `/mra-roadmap <topic>` instead of a change id: it reads the ADRs and terms recorded here and does not ask again what this grill settled
   - The next command: `/mra-propose <change-id>`

## Rules

- Do not create an OpenSpec change or write code in this phase.
- Never edit a roadmap: report its impact; `/mra-roadmap` revises it.
- Do not commit; list the changed files and let the user decide.
