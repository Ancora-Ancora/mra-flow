# An initiative roadmap sits above the changes, optional and backward compatible

The workflow worked one change at a time: `/mra-grill` closed with a single change id, and the first epic appeared at `/mra-track`. Nothing showed how much work a large effort held, how it was cut, or in what order, so a rough evaluation before the first change was impossible, and the cut, when made by hand, left no record. We add an **initiative** level above the changes: `/mra-roadmap` grills the whole effort breadth-first, records its cross-cutting decisions as ADRs and glossary terms as `/mra-grill` does, and writes `docs/roadmap/<initiative>.md`: the **slices** (one future change each, with its change id), their repos, contract impact, dependencies, UI previews needed, a **size with a person-day range** and a confidence, and a total range with its assumptions. In beads it creates one initiative epic (`roadmap:<initiative>`) with one child epic per slice; `/mra-track` promotes the slice epic into the change epic instead of creating a new one, so `bd epic status` shows the whole initiative. The rules of the file and of the epics live in one place, `.mra-flow/docs/agents/roadmap.md`, which every skill that reads or writes a roadmap points to.

The initiative grill differs from `/mra-grill` in breadth, not in method: same primitives (`grilling` + `domain-modeling`, one question per message with a recommended answer), but its agenda is destination, scope and out of scope, actors, constraints, repo and contract boundaries, cross-cutting decisions, the list of screens and the slicing rule. Detail questions are not answered there: they become open points of the slice they belong to, and the per-change `/mra-grill` starts from them.

Estimates are part of the roadmap and are checked against reality: each slice keeps its original estimate, `/mra-propose` adds a revised one from `tasks.md`, and `/mra-archive` records the actual effort (active days from the change's commits, confirmed or corrected by the user). Done slices of every roadmap are the reference class for sizing new ones.

Three entry modes:

- `/mra-roadmap <topic>`: a new initiative, from a breadth grill.
- `/mra-roadmap --from <map-epic>`: an initiative whose decisions were first worked out with `/mattpocock-skills:wayfinder`. The map's Destination, Decisions so far, Not yet specified and Out of scope seed the grill, which then covers only the gaps, and the map epic becomes the initiative epic.
- `/mra-roadmap --retro <initiative>`: an orchestrator that already has archived or in-flight changes. Their changes become done or in-progress slices (actuals from archive dates, epics and commits, confirmed by the user), their epics are reparented under the new initiative epic, and the breadth grill covers only the remaining work, sized against the done slices.

Re-running `/mra-roadmap <initiative>` on an existing roadmap revises it: it re-grills only the slices not yet tracked and never rewrites a done row or an original estimate.

## Considered Options

- **Use `/mattpocock-skills:wayfinder` as the roadmap.** Rejected as the only tool: its tickets are decisions, not slices of work, it gives no estimate, and it resolves one ticket per session. It stays the recommended step *before* `/mra-roadmap` when an effort is mostly fog, and `--from` consumes its map.
- **A breadth mode of `/mra-grill`.** Rejected: one skill with two agendas and two outputs (a change id, or a roadmap) is harder to follow than two skills; `/mra-grill` stays the per-change depth grill.
- **The roadmap only in beads (epic descriptions).** Rejected: the table of slices, sizes and totals is read and corrected as a whole, and it must exist before any epic does in `--retro`; the file is the plan, beads holds the status, as `tasks.md` and the change epic already do.
- **No beads placeholders.** Rejected: without slice epics, `bd epic status` cannot show the initiative's progress, and change epics have nothing to hang from.

## Consequences

- Optional: an orchestrator without `docs/roadmap/` behaves exactly as before. `/mra-grill`, `/mra-propose`, `/mra-track` and `/mra-archive` look for a roadmap slice matching the change id and skip every roadmap step when there is none; `/mra-grill` only *suggests* `/mra-roadmap` when a topic is too large for one change.
- `/mra-roadmap` joins the skills allowed to create issues (initiative and slice epics only, never tasks).
- Only `/mra-roadmap` changes the structure of a roadmap (slices added, split, merged, dropped, reordered); the phase skills write only their own slice's status, revised estimate, epic and actual. `/mra-grill` reports roadmap impact and recommends a revision instead of editing the slices.
- `/mra-roadmap` recommends `/mra-prototype` or `/mra-research` only when the answer changes the cut or a size; every other question waits for the slice's `/mra-grill`. A prototype done at roadmap time is recorded in the slice's *UI preview* cell, and the slice's `/mra-grill` reuses it instead of prototyping again.
- A roadmap found missing late is recommended, not imposed: `/mra-propose` (an XL change, or several capabilities with a contract change) and `/mra-archive` (follow-ups left, or related archived changes) recommend `/mra-roadmap --retro` once per change, and a decline is recorded on the epic. An orchestrator updated to the version that brings `/mra-roadmap`, with changes but no roadmap, gets a one-time note in the update report pointing at `--retro`.
- Estimates are in person-days of one developer working with the agent, across the whole cycle from grill to archive; the size scale is a default the roadmap may override.
