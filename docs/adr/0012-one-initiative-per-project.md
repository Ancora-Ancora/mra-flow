# One initiative per project, with every change as a slice

ADR-0010 let an orchestrator hold any number of initiatives, each its own roadmap and effort file, and `--retro` brought in only the changes the user picked, as done slices without estimates. In use this split the project's work in two: a retro initiative with the archived changes and no 🔴/🟢 (no estimate to compare), and a second roadmap, written before ADR-0011 and still in days, that `mra-effort` refused, so the planned slices appeared in no effort file at all. Reaching one complete picture took a second `/mra-roadmap`, a hand merge of the two roadmaps, retro estimates written by hand and a manual reattribution of the session hours.

We make the initiative the project's: one per orchestrator, named after the orchestrator repo's directory, `docs/roadmap/<project>.md`, `roadmap:<project>`. Every change is one of its slices, done, in progress or planned, and the initiative epic is the parent of every change epic, archived ones included. A new effort adds slices to it (revise mode); there is no second roadmap.

`/mra-roadmap --retro` builds that roadmap in one pass: archived changes as done slices, in-flight ones, open epics that are no change yet and every other roadmap (merged, converted to hours) as open slices. Every slice gets an estimate: the done ones a retro estimate (confidence `retro`, sized from their drivers without looking at the actual), so the effort file shows a variance for each of them. The actuals in hours come from the session logs with the aliases and the commands without a change id gathered automatically and confirmed by the user once.

The SessionStart drift hook and the installer recommend the command, every session and every update until done: `/mra-roadmap --retro` when there are changes but no roadmap, `/mra-roadmap <project>` when another roadmap exists or the project's is in days.

## Considered Options

- **Several initiatives, one effort file each (ADR-0010).** Rejected by the user: the planned work and the done work belong to the same project and must read as one table with one total.
- **One effort file summing several roadmaps.** Rejected: two sources of the same totals, and a change could still sit in no roadmap.
- **Name the initiative from `mra-flow.toml`.** Rejected for now: the directory name is always there and is what the user calls the project; a field can be added if a project ever needs a different name.
- **No estimate for done retro slices.** Rejected: the effort file then shows no indicator for most of the project, and the retro actuals cannot calibrate the scale.

## Consequences

- Amends ADR-0010: the initiative is no longer an optional effort above some changes but the project's one plan; ADR-0010's modes stay, with **new** limited to a project with no change yet.
- A roadmap from an older version (another name, or in days) is merged and converted by `/mra-roadmap <project>`; its day ranges stay in the Log.
- `retro` is a fourth confidence value; its estimates calibrate the scale and are not forecasts.
- The installer's one-time `--retro` note (ADR-0010) becomes a note on every update until a roadmap exists.
