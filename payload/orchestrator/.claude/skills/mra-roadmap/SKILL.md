---
name: mra-roadmap
description: Use when an effort in an mra-flow orchestrator is too large for one change and needs to be cut into estimated slices before the first change - the optional initiative level above phase 1 of the mra-flow workflow.
disable-model-invocation: true
argument-hint: <topic> | <initiative> (revise) | --from <wayfinder-map-epic> | --retro [<initiative>, default go-live]
---

# mra-roadmap — initiative: breadth grill, slices and estimates

Cut the effort in `$ARGUMENTS` into slices, one change each, estimate them and record the result as `docs/roadmap/<initiative>.md` plus an initiative epic with one slice epic per slice. The project has **one** initiative, `go-live` unless the user names it otherwise, and every change is a slice of it (*One initiative per project*). The file format, the size scale, the totals, the actuals and the beads conventions are in `.mra-flow/docs/agents/roadmap.md`: read it first and follow it exactly.

## Modes

Pick the mode from `$ARGUMENTS`:

The initiative is the one roadmap in `docs/roadmap/`, whatever its name. When there is none yet, it is named by the argument (`--retro <name>`, `/mra-roadmap <name>`), and `go-live` when the command gives none: propose `go-live` as that argument, and use the name typed instead when the user gives another. Once a roadmap exists, an argument naming another initiative is read as a topic.

- **new** — a topic, no roadmap yet and no change yet (nothing archived, in flight or tracked);
- **revise** — the project's roadmap exists: a topic adds its slices to it; any other `docs/roadmap/*.md` is merged into it and a roadmap in days is converted (step 2);
- **from** — `--from <map-epic>`: a `/mattpocock-skills:wayfinder` map (an epic labelled `wayfinder`) whose decisions seed the roadmap, or the slices they add to it;
- **retro** — `--retro`, or **new** when changes already exist: builds the project's whole roadmap at once, every slice done and not done, each with an estimate, and the actuals in hours of the done ones.

## Steps

1. **Ground yourself.** Read the glossaries and ADRs of the domain-docs layout in use (`.mra-flow/docs/agents/domain.md`), the capability list (`openspec list --specs`), the registered repos (`.mra-flow/bin/mra-repo list`, with each repo's `description` and `depends_on` in `mra-flow.toml`), the changes (`openspec list`, `openspec/changes/archive/`) and the other roadmaps (`docs/roadmap/*.md`). Skip silently whatever does not exist yet. If no repos are registered, recommend `.mra-flow/bin/mra-repo add` first: slices name their repos. Proceed if the user declines.
2. **Seed** (by mode):
   - **from**: `bd show <map-epic>` and its closed children (`bd list --parent <map-epic> --all`): Destination, Decisions so far, Not yet specified and Out of scope become the starting point; the grill covers only what they leave open.
   - **retro**: collect every piece of work, done and not done:
     - archived changes (folder `openspec/changes/archive/<YYYY-MM-DD>-<change-id>`) → `done` slices;
     - in-flight changes (`openspec/changes/<change-id>`) → `in progress` (tracked: an epic `openspec:<change-id>`) or `proposed` (no epic yet);
     - every other `docs/roadmap/*.md` → its slices, merged (*One initiative per project*), converted to hours if in days (*A roadmap in days*);
     - open epics in beads that are no change yet (`bd list -t epic --all`, not `openspec:`-labelled, not closed) → `planned` slices, keeping their epic.

     Show the list and ask, in one question, only which to **leave out** (default: none). For each done change, collect what it built (proposal Why, specs touched, repos) and its actual hours per phase with `.mra-flow/bin/mra-effort measure <change-id> --json`, whose `inferred` stretches already cover the commands that named no change (*Actuals* in `.mra-flow/docs/agents/roadmap.md`); settle what is left as that section says; propose one figure per change, with the assignments and its start and end, and ask the user to confirm or correct the whole list in one question. For an in-progress change, measure it too and show the hours so far in the close summary (its actual is recorded at `/mra-archive`).
   - **revise**: read the roadmap; only rows with status `planned` or `proposed` are open to change. First merge any other `docs/roadmap/*.md` and convert a roadmap in days (both in `.mra-flow/docs/agents/roadmap.md`), showing the result in one question. Then ask what triggered the revision (a new topic, a `/mra-grill` roadmap impact, a new requirement, a slice found too large) and grill only that.
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
7. **Estimates.** Every slice gets one: in retro mode the done slices too, as *Retro estimates* in `.mra-flow/docs/agents/roadmap.md` says (confidence `retro`, sized from their drivers without looking at their actuals). For each slice not done, size it with the scale of `.mra-flow/docs/agents/roadmap.md` (or the roadmap's own scale, if it overrides it):
   - start from the size drivers: repos touched, contract change, new capabilities or requirements, new or changed screens, data migration, open points;
   - compare with the **reference class**: done slices with actuals in this and every other `docs/roadmap/*.md`; when the actuals of similar slices sit outside the scale's range, use them and say so;
   - give a range in effective hours and a confidence; low confidence widens the range.
   Show the estimates with their drivers in one question and let the user correct them. Then write the **Assumptions** the figures rely on; the **Total** lines come from `mra-effort report` in step 8.
8. **Write the roadmap** `docs/roadmap/<initiative>.md` in the format of `.mra-flow/docs/agents/roadmap.md`, with a first Log line (`created`, `created from wayfinder map <id>`, `reconstructed (retro)` or the revision and its trigger). In revise mode, change only open rows: never rewrite a done row or an original estimate; a dropped slice keeps its row with status `dropped`. Never write the `## Actuals by phase` heading by hand. In retro mode, write each done slice's confirmed hours, start and end with `.mra-flow/bin/mra-effort record <initiative> <change-id> --phase <phase>=<hours> ... --start "<start>" --end "<end>"`, and the start of each in-progress slice with `record <initiative> <change-id> --start "<start>"`. Then run `.mra-flow/bin/mra-effort report <initiative>`: it writes the Total lines and `docs/roadmap/<initiative>-effort.md`.
9. **Beads**, sequentially, following *Beads* in `.mra-flow/docs/agents/roadmap.md`:
   - the initiative epic (new, or the wayfinder map in from mode, or reuse it in revise mode); write its id into the front matter;
   - one slice epic per slice not done and without an epic, with `--estimate` = the upper bound of its range × 60 (minutes); in retro mode, reparent every existing change epic under the initiative epic, archived ones included (and set the estimate of those not done the same way); when merging another roadmap, reparent and relabel its epics and close its initiative epic;
   - dependencies between slice epics; `bd dep cycles` must report none;
   - revise mode: close the epics of dropped slices; create the epics of new ones; update the `--estimate` of every open slice whose range changed.
   Write each epic id into its row.
10. **Close** with a short summary:
   - ADRs created or changed, glossary terms added;
   - the slices table (change id, size, estimate, status) and the three Total lines;
   - open points per slice, and Risks;
   - prototype notes in `docs/prototypes/` and research notes in `docs/research/` written during the session;
   - `bd epic status` for the initiative epic (every change epic is its child);
   - in retro mode, the actual hours per done slice and the hours so far of the in-progress ones;
   - the next command: `/mra-grill <change-id of the first slice with no open dependency>`.

## Rules

- Show the model at work: `Model: <model> (<role>)` at the phase start, with every subagent dispatch and whenever it changes; see `.mra-flow/docs/agents/model-display.md`.
- Do not create an OpenSpec change, task issues or code in this skill: only the roadmap file, ADRs, glossary terms and epics.
- Never rewrite an original estimate or a done row; the log keeps every revision.
- Do not commit; list the changed files and let the user decide.
