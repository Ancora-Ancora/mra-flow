---
name: mra-roadmap
description: Use when an effort in an mra-flow orchestrator is too large for one change and needs to be cut into estimated slices before the first change - the optional initiative level above phase 1 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <topic> | <initiative> (revise) | --from <wayfinder-map-epic> | --retro <initiative>
---

# mra-roadmap — initiative: breadth grill, slices and estimates

Cut the effort in `$ARGUMENTS` into slices, one future change each, estimate them and record the result as `docs/roadmap/<initiative>.md` plus an initiative epic with one slice epic per slice. The file format, the size scale, the totals, the actuals and the beads conventions are in `.mra-flow/docs/agents/roadmap.md`: read it first and follow it exactly.

## Modes

Pick the mode from `$ARGUMENTS`:

- **new** — a topic, and no `docs/roadmap/<initiative>.md` matches it;
- **revise** — an initiative whose roadmap exists;
- **from** — `--from <map-epic>`: a `/mattpocock-skills:wayfinder` map (an epic labelled `wayfinder`) whose decisions seed the roadmap;
- **retro** — `--retro <initiative>`: the orchestrator already has archived or in-flight changes that belong to this initiative.

## Steps

1. **Ground yourself.** Read the glossaries and ADRs of the domain-docs layout in use (`.mra-flow/docs/agents/domain.md`), the capability list (`openspec list --specs`), the registered repos (`.mra-flow/bin/mra-repo list`, with each repo's `description` and `depends_on` in `mra-flow.toml`), the changes (`openspec list`, `openspec/changes/archive/`) and the other roadmaps (`docs/roadmap/*.md`). Skip silently whatever does not exist yet. If no repos are registered, recommend `.mra-flow/bin/mra-repo add` first: slices name their repos. Proceed if the user declines.
2. **Seed** (by mode):
   - **from**: `bd show <map-epic>` and its closed children (`bd list --parent <map-epic> --all`): Destination, Decisions so far, Not yet specified and Out of scope become the starting point; the grill covers only what they leave open.
   - **retro**: list archived changes (folder `openspec/changes/archive/<YYYY-MM-DD>-<change-id>`), in-flight changes (`openspec/changes/<change-id>`) and their epics (`bd list -t epic -l openspec:<change-id> --all`). Ask the user which belong to the initiative, in one question with the list. For each chosen change, collect what it built (proposal Why, specs touched, repos) and its actual effort as `.mra-flow/docs/agents/roadmap.md` *Actuals* says for `--retro`; propose one figure per change and ask the user to confirm or correct the whole list in one question. These become `done` slices (archived) and `in progress` slices (tracked, not archived) or `proposed` (no epic yet).
   - **revise**: read the roadmap; only rows with status `planned` or `proposed` are open to change. Ask what triggered the revision (a `/mra-grill` roadmap impact, a new requirement, a slice found too large) and grill only that.
3. **Breadth grill.** Call the Skill tool with `mattpocock-skills:grilling`, then with `mattpocock-skills:domain-modeling`. Run the session with both active: resolved terms go to the glossary, ADR-worthy cross-cutting decisions go to the ADRs (narrowest context, per `.mra-flow/docs/agents/domain.md`). Override grilling's rounds: ask **one question per message**, each with your recommended answer, and wait for the reply. Go **wide, not deep**, through this agenda, skipping what the seed already settled:
   1. destination: what is true when the initiative is done;
   2. scope and out of scope;
   3. actors and roles;
   4. constraints binding every slice: contracts and compatibility, environments, non-functional requirements, deadlines;
   5. repo and contract boundaries: which repos the effort touches, and for each repo with one of its `depends_on`, whether the contract changes;
   6. cross-cutting decisions (architecture, contract strategy, data migration) → ADRs;
   7. the screens the effort adds or changes, each with the preview it needs per `.mra-flow/docs/agents/ui-preview.md`: named, not drawn, unless step 4 asks for a prototype now;
   8. the slicing rule (default: vertical slices with observable value, each shippable alone; a contract change ships in the dependency first).
   A detail question (one requirement, one screen's layout, one edge case) is not answered here: write it down as an open point of the slice it belongs to.
4. **Stuck questions.** A question is worth settling here only when its answer changes the cut (one slice or two, which repo, what depends on what) or a size; any other question becomes an open point of its slice, for its `/mra-grill`. For a question that does:
   - an external fact nobody here can confirm (a library's capability, an API's limits, a standard, a version difference) → recommend `/mra-research <question>`; grill other agenda items while it runs, then resume from its note in `docs/research/`;
   - a UI or state-model question still open after two rounds (a single screen or a wizard, one flow for every role or one per role, a new interaction pattern whose cost is unclear) → recommend `/mra-prototype <question>`, with the question already written; resume from its verdict in `docs/prototypes/<slug>.md` and write that note into the slice's *UI preview* cell;
   - the user declines → mark the affected slices `low` confidence and list the question under Risks.
   Both commands are run by the user: recommend them, never run their steps yourself.
5. **Fog check.** If more than a few cross-cutting decisions stay open after two rounds, or the destination itself is unclear, the effort is mostly fog: recommend `/mattpocock-skills:wayfinder <idea>` and, once its map is clear, `/mra-roadmap --from <map-epic>`. Proceed only if the user prefers a rough roadmap now; then mark every affected slice `low` confidence and list the open decisions under Risks.
6. **Slices.** Cut the remaining work by the slicing rule. Per slice: change id, one-line goal, repos, contract yes/no, dependencies, UI preview, open points. No slice may be XL: split it. Show the whole table in one question (with a `preview`) and let the user correct it; iterate until accepted.
7. **Estimates.** For each slice not done, size it with the scale of `.mra-flow/docs/agents/roadmap.md` (or the roadmap's own scale, if it overrides it):
   - start from the size drivers: repos touched, contract change, new capabilities or requirements, new or changed screens, data migration, open points;
   - compare with the **reference class**: done slices with actuals in this and every other `docs/roadmap/*.md`; when the actuals of similar slices sit outside the scale's range, use them and say so;
   - give a range in person-days and a confidence; low confidence widens the range.
   Show the estimates with their drivers in one question and let the user correct them. Then compute the **Total** lines and write the **Assumptions** the figures rely on.
8. **Write the roadmap** `docs/roadmap/<initiative>.md` in the format of `.mra-flow/docs/agents/roadmap.md`, with a first Log line (`created`, `created from wayfinder map <id>`, `reconstructed (retro)` or the revision and its trigger). In revise mode, change only open rows: never rewrite a done row or an original estimate; a dropped slice keeps its row with status `dropped`.
9. **Beads**, sequentially, following *Beads* in `.mra-flow/docs/agents/roadmap.md`:
   - the initiative epic (new, or the wayfinder map in from mode, or reuse it in revise mode); write its id into the front matter;
   - one slice epic per slice not done and without an epic; in retro mode, reparent the in-flight change epics instead;
   - dependencies between slice epics; `bd dep cycles` must report none;
   - revise mode: close the epics of dropped slices; create the epics of new ones.
   Write each epic id into its row.
10. **Close** with a short summary:
   - ADRs created or changed, glossary terms added;
   - the slices table (change id, size, estimate, status) and the three Total lines;
   - open points per slice, and Risks;
   - prototype notes in `docs/prototypes/` and research notes in `docs/research/` written during the session;
   - `bd epic status` for the initiative epic;
   - the next command: `/mra-grill <change-id of the first slice with no open dependency>`.

## Rules

- Do not create an OpenSpec change, task issues or code in this skill: only the roadmap file, ADRs, glossary terms and epics.
- Never rewrite an original estimate or a done row; the log keeps every revision.
- Do not commit; list the changed files and let the user decide.
