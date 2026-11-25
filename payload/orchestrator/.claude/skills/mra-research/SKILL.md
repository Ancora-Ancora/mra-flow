---
name: mra-research
description: Use when a decision in an mra-flow orchestrator depends on an external fact nobody in the conversation can confirm - a library's capability, an API's behaviour or limits, a standard, a version difference - usually from /mra-grill, /mra-propose or /mra-update.
disable-model-invocation: true
argument-hint: <question> [--change <change-id>]
---

# mra-research — settle an external fact from primary sources

Answer the factual question in `$ARGUMENTS` from **primary sources**, and save the findings as a cited note that later decisions can point at. Research produces evidence, not decisions: the decision is taken afterwards, in the phase that asked.

## Steps

1. **Frame the question.** Restate it as one or more factual questions ending in `?`, each with the decision it feeds (e.g. "Does library X support Y in version Z? → which auth library ADR"). Note the versions in use: read them from the owning code repos (`.mra-flow/bin/mra-repo list`; lockfiles, `package.json`, `pyproject.toml`, etc.). Done when the user confirms the questions.
2. **Pick the file.** `docs/research/YYYY-MM-DD-<slug>.md` at the orchestrator root (today's date, kebab-case `<slug>`). If a note on the same topic exists already, read it first and research only what it leaves open.
3. **Research.** Call the Skill tool with `mattpocock-skills:research` and follow it, with these inputs for its agent:
   - the framed questions and the versions from step 1;
   - the file path from step 2, which replaces its "where the repo keeps such notes" choice;
   - the note's layout: one section per question with a direct **answer**, each claim cited (URL or `file:line` in a dependency's source, at the version in use), then **Open points** for what the sources could not settle.
   While its background agent reads, carry on with the calling phase on other questions.
4. **Review the note** when the agent finishes: every question answered or listed under Open points, every claim cited, versions matching the ones in use. Fix gaps before going on.
5. **Hand the facts back.** Summarize the answers for the user in two or three lines each and say which decision each one unblocks. If `--change` names a change tracked in beads (`bd list -t epic -l openspec:<change-id>`), also `bd update <epic> --append-notes "research: docs/research/<file> - <one-line answer>"`.
6. End with the note's path and the command to resume: back to `/mra-grill`, `/mra-propose <change-id>` or `/mra-update <change-id>`. The ADR, carried decision or `design.md` that uses a finding cites the note's path.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Write only the research note (and the epic note in step 5); create no ADR, spec or beads issue here.
- Do not commit; list the note and let the user decide.
- Write the note in English; report to the user in their language.
