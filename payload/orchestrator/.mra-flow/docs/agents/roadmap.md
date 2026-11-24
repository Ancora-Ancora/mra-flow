# Initiative roadmaps

An **initiative** is an effort too large for one change. Its **roadmap**, `docs/roadmap/<initiative>.md`, cuts it into **slices**, one future change each, with an estimate per slice and a total. `/mra-roadmap` writes and revises it (ADR-0010 of mra-flow). It is optional: when `docs/roadmap/` does not exist, or no slice matches a change id, every roadmap step in the other skills is skipped silently.

## Finding the slice of a change

A change belongs to a roadmap when a row of the **Slices** table of some `docs/roadmap/*.md` has that change id in its *Change id* column. A change id appears in at most one roadmap.

## A roadmap found missing late

A change that belongs to no roadmap may turn out, once proposed or archived, to be part of a larger effort. Two phases look for it and recommend `/mra-roadmap --retro <initiative>` (never the plain mode: there is already work to bring in as slices):

- `/mra-propose`: the change, estimated from `tasks.md` with the default size scale, is XL, or it touches more than one capability with a contract change; the change then enters the roadmap as a `proposed` slice and the rest becomes new slices.
- `/mra-archive`: the proposal or design names work left for later (follow-ups, a next change, out-of-scope items meant to be done), or other archived changes modify the same capabilities; list those changes as candidate done slices.

The recommendation is made **once per change** and never blocks the phase. When the user declines, record `bd update <epic> --append-notes "roadmap: declined (<reason>)"` when the epic exists (else say it in the close summary), and never ask again for that change; neither phase asks when a `roadmap: declined` note is on the epic.

## The file

```markdown
---
initiative: <initiative>          # kebab-case, also the beads label roadmap:<initiative>
title: <title>
status: active                    # active | done | dropped
epic: <initiative epic id>        # filled once the epic exists
created: <YYYY-MM-DD>
---

# <title>

## Destination

<one or two lines: what the world looks like when the initiative is done>

## Scope

- In: <...>
- Out: <... (why)>

## Actors and constraints

<roles involved; contracts, compatibility, environments, non-functional requirements that bind every slice>

## Decisions

<!-- pointers only: ADRs and glossary terms of this initiative, one line each -->
- ADR-NNNN <title>: <gist>

## Slicing rule

<how the work was cut, e.g. vertical slices, each with observable value and shippable on its own; hub before gens on a contract change>

## Size scale

| Size | Person-days | Meaning |
|---|---|---|
| S | 1–2 | one repo, no contract change, no new screen |
| M | 3–5 | one or two repos, or one new screen, or a small optional contract addition |
| L | 6–10 | several repos with a contract change, or several screens, or a new capability |
| XL | > 10 | too large for one change: split it |

## Slices

| # | Change id | Goal | Repos | Contract | Depends on | UI preview | Size | Estimate (d) | Confidence | Revised (d) | Status | Epic | Actual (d) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | add-foo | <one line> | hub | yes | – | prototype docs/prototypes/foo-screen.md | M | 3–5 | medium | | planned | bd-12 | |

## Total

<computed, see Totals below>

## Assumptions

- <what the estimates rely on>

## Risks and open points

- [slice <#>] <open point the per-change /mra-grill must settle>
- [all] <cross-cutting risk>

## Log

- <YYYY-MM-DD> <what changed in the roadmap and why>
```

Column rules:

- **Change id**: kebab-case, the id `/mra-propose` will use. Stable once written: a renamed slice keeps its row and logs the rename.
- **Contract**: `yes` when the slice changes an interface between a repo and one of its `depends_on`.
- **Depends on**: slice numbers that must be archived first.
- **UI preview**: what the slice's screens need, per `.mra-flow/docs/agents/ui-preview.md`; one value per slice, the strongest when its screens differ:
  - `prototype` — needed, to be done in the slice's `/mra-grill`;
  - `prototype docs/prototypes/<slug>.md` — already done (in `/mra-roadmap` or a previous slice): the slice's `/mra-grill` reuses the verdict instead of prototyping again;
  - `sketch` — only changes to existing screens: a sketch in the slice's `/mra-grill`;
  - `–` — no screen in a repo's `ui_paths`.
  The final `preview:` line of each screen (`.mra-flow/docs/agents/ui-preview.md`, *How it is recorded*) is still written by the slice's `/mra-grill` and lands in `design.md`, not here.
- **Estimate (d)**: the original range in person-days (one developer working with the agent, from `/mra-grill` to `/mra-archive`). Written once; never rewritten, so it stays comparable with the actual.
- **Confidence**: `high` (similar done slices exist, no open points), `medium`, `low` (open points or unknown technology; widen the range).
- **Revised (d)**: the range after `/mra-propose`, from `tasks.md`. Empty until then.
- **Status**: `planned` → `proposed` (`/mra-propose`) → `in progress` (`/mra-track`) → `done` (`/mra-archive`); or `dropped` (by `/mra-roadmap` only, with a log line).
- **Actual (d)**: person-days spent, written by `/mra-archive` (see Actuals).

## Totals

The **Total** section holds three lines; whoever changes a size, estimate, status or actual recomputes them:

- `Estimate: <min>–<max> d` — the sum of the original estimates of all slices not dropped.
- `Forecast: <min>–<max> d` — the sum, over slices not dropped, of the actual for done slices, else the revised range, else the original one.
- `Progress: <done>/<total> slices; actual <sum of actuals> d vs. estimated <sum of the original ranges of the done slices> d`.

## Actuals

`/mra-archive` measures, before integrating:

- **active days**: the distinct commit dates on `change/<change-id>` in every repo's worktree (`git -C .worktrees/<change-id>/<key> log --format=%ad --date=short <merge-base>..HEAD`), joined with the dates of the orchestrator commits touching `openspec/changes/<change-id>` (`git log --format=%ad --date=short -- openspec/changes/<change-id>`), counted once;
- **calendar span**: from the epic's creation date to today.

It proposes the active days as the actual and asks the user to confirm or correct it (part-time days, work without commits). `--retro` does the same from what still exists (archive folder date, epic created and closed dates, commits on the default branch that mention the change id) and always asks.

## Beads

- **Initiative epic**: `bd create "<initiative>: <title>" -t epic -l roadmap:<initiative> --spec-id docs/roadmap/<initiative>.md -d "<Destination>"`. From `--from <map-epic>`, the wayfinder map epic is reused instead: `bd update <map-epic> --add-label roadmap:<initiative> --spec-id docs/roadmap/<initiative>.md`.
- **Slice epic**: one child per slice not done, `bd create "<change-id>: <goal>" -t epic --parent <initiative epic> -d "<goal; open points of the slice>" --metadata '{"slice":"<change-id>"}'`; it inherits `roadmap:<initiative>`. Find it with `bd list --parent <initiative epic> -t epic --metadata-field slice=<change-id> --all`.
- **Promotion**: `/mra-track` turns the slice epic into the change epic (`bd update <slice epic> --add-label openspec:<change-id> --spec-id openspec/changes/<change-id> --title "<change-id>: <proposal title>" -d "<proposal Why>"`) instead of creating a new one; tasks become its children as usual.
- **Order**: for each `Depends on`, `bd dep add <slice epic> <slice epic it depends on>`.
- **Existing change epics** (`--retro`): `bd update <change epic> --parent <initiative epic> --add-label roadmap:<initiative> --metadata '{"slice":"<change-id>"}'`; archived changes get no new epic: their row records the old epic id, if any.
- **Dropped slice**: `bd close <slice epic> --reason "dropped from roadmap <initiative>: <why>"`.
- **Done initiative**: when every slice is done or dropped, `/mra-archive` offers `bd close <initiative epic>` and sets the front matter `status: done`.

## Who writes what

| Skill | Writes |
|---|---|
| `/mra-roadmap` | everything: rows, sizes, original estimates, scale, assumptions, risks, epics, log |
| `/mra-grill` | nothing; reports **roadmap impact** in its close summary and recommends `/mra-roadmap <initiative>` when slices must change |
| `/mra-propose` | its row: Revised, Status `proposed`; Total; a log line when the revised range leaves the original one |
| `/mra-track` | its row: Status `in progress`, Epic; promotes the slice epic |
| `/mra-archive` | its row: Status `done`, Actual; Total; a log line; closes the initiative when done |
